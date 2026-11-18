#!/usr/bin/env python3
"""Rabbit stream cipher (RFC 4503) as implemented by CryptoJS 4.1.1, batched with numpy.

Ported line for line from crypto-js `rabbit.js` (`Rabbit`) and `rabbit-legacy.js` (`RabbitLegacy`).
The only difference between the two is the key byte swap in `_doReset`. CryptoJS reads bytes into
big-endian 32-bit words; the port reproduces that. Verified against vectors produced by the real
library (see `test_rabbit_cryptojs.py`).

CryptoJS passphrase mode (`Rabbit.encrypt(msg, "passphrase")`) emits an OpenSSL `Salted__` envelope.
Key and IV come from `EVP_BytesToKey` with MD5 (the CryptoJS default): a 16-byte key and an 8-byte IV.
"""
from __future__ import annotations

import hashlib

import numpy as np

M32 = np.uint64(0xFFFFFFFF)
A_CONST = [0x4D34D34D, 0xD34D34D3, 0x34D34D34, 0x4D34D34D, 0xD34D34D3, 0x34D34D34, 0x4D34D34D, 0xD34D34D3]


def _u(x):
    return np.asarray(x, dtype=np.uint64) & M32


def _rotl(x, n):
    return ((x << np.uint64(n)) | (x >> np.uint64(32 - n))) & M32


def _swap(x):
    """CryptoJS endian swap of a 32-bit word."""
    return (((_rotl(x, 8)) & np.uint64(0x00FF00FF)) | ((_rotl(x, 24)) & np.uint64(0xFF00FF00))) & M32


def _words_be(b):
    """(N, 4k) uint8 -> (N, k) big-endian uint64 words."""
    b = b.astype(np.uint64)
    return (b[:, 0::4] << np.uint64(24)) | (b[:, 1::4] << np.uint64(16)) | (b[:, 2::4] << np.uint64(8)) | b[:, 3::4]


def _next_state(X, C, b):
    old = [c.copy() for c in C]
    carry = b
    for i in range(8):
        C[i] = (C[i] + np.uint64(A_CONST[i]) + carry) & M32
        carry = (C[i] < old[i]).astype(np.uint64)
    b = carry
    G = []
    for i in range(8):
        gx = (X[i] + C[i]) & M32
        sq = gx * gx  # < 2**64, exact in uint64
        G.append(((sq & M32) ^ (sq >> np.uint64(32))) & M32)
    X[0] = (G[0] + _rotl(G[7], 16) + _rotl(G[6], 16)) & M32
    X[1] = (G[1] + _rotl(G[0], 8) + G[7]) & M32
    X[2] = (G[2] + _rotl(G[1], 16) + _rotl(G[0], 16)) & M32
    X[3] = (G[3] + _rotl(G[2], 8) + G[1]) & M32
    X[4] = (G[4] + _rotl(G[3], 16) + _rotl(G[2], 16)) & M32
    X[5] = (G[5] + _rotl(G[4], 8) + G[3]) & M32
    X[6] = (G[6] + _rotl(G[5], 16) + _rotl(G[4], 16)) & M32
    X[7] = (G[7] + _rotl(G[6], 8) + G[5]) & M32
    return b


def keystream(keys, ivs, nbytes, legacy=False):
    """keys (N,16) uint8, ivs (N,8) uint8 -> (N, nbytes) uint8 keystream, CryptoJS byte order."""
    keys = np.asarray(keys, dtype=np.uint8)
    ivs = np.asarray(ivs, dtype=np.uint8)
    K = [w for w in _words_be(keys).T]
    if not legacy:
        K = [_swap(k) for k in K]
    sl = lambda x: (x << np.uint64(16)) & M32  # noqa: E731
    sr = lambda x: x >> np.uint64(16)  # noqa: E731
    X = [K[0], sl(K[3]) | sr(K[2]), K[1], sl(K[0]) | sr(K[3]), K[2], sl(K[1]) | sr(K[0]), K[3], sl(K[2]) | sr(K[1])]
    hi, lo = np.uint64(0xFFFF0000), np.uint64(0x0000FFFF)
    C = [sl(K[2]) | sr(K[2]), (K[0] & hi) | (K[1] & lo), sl(K[3]) | sr(K[3]), (K[1] & hi) | (K[2] & lo),
         sl(K[0]) | sr(K[0]), (K[2] & hi) | (K[3] & lo), sl(K[1]) | sr(K[1]), (K[3] & hi) | (K[0] & lo)]
    X = [x.copy() for x in X]
    b = np.zeros(keys.shape[0], dtype=np.uint64)
    for _ in range(4):
        b = _next_state(X, C, b)
    for i in range(8):
        C[i] = C[i] ^ X[(i + 4) & 7]
    IV = _words_be(ivs).T
    i0, i2 = _swap(IV[0]), _swap(IV[1])
    i1 = (i0 >> np.uint64(16)) | (i2 & hi)
    i3 = ((i2 << np.uint64(16)) & M32) | (i0 & lo)
    for i, v in enumerate((i0, i1, i2, i3, i0, i1, i2, i3)):
        C[i] = C[i] ^ v
    for _ in range(4):
        b = _next_state(X, C, b)
    blocks = []
    for _ in range((nbytes + 15) // 16):
        b = _next_state(X, C, b)
        S = [X[0] ^ (X[5] >> np.uint64(16)) ^ ((X[3] << np.uint64(16)) & M32),
             X[2] ^ (X[7] >> np.uint64(16)) ^ ((X[5] << np.uint64(16)) & M32),
             X[4] ^ (X[1] >> np.uint64(16)) ^ ((X[7] << np.uint64(16)) & M32),
             X[6] ^ (X[3] >> np.uint64(16)) ^ ((X[1] << np.uint64(16)) & M32)]
        for s in S:
            s = _swap(s & M32)  # CryptoJS swaps, then XORs into big-endian message words
            for shift in (24, 16, 8, 0):
                blocks.append(((s >> np.uint64(shift)) & np.uint64(0xFF)).astype(np.uint8))
    return np.stack(blocks, axis=1)[:, :nbytes]


def evp_key_iv(passphrase: bytes, salt: bytes, digest="md5"):
    """OpenSSL EVP_BytesToKey (one iteration) -> (16-byte key, 8-byte IV), as CryptoJS uses for Rabbit."""
    d, prev = b"", b""
    while len(d) < 24:
        prev = hashlib.new(digest, prev + passphrase + salt).digest()
        d += prev
    return d[:16], d[16:24]
