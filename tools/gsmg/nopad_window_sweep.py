#!/usr/bin/env python3
"""Sweep SALPH/P32TRAILING under `openssl enc -nopad` semantics.

Every prior sweep (Phase 25-83) requires a valid PKCS7 pad to accept a
decrypt, then either checks printability or -- for the binary64 hypothesis
(Phase 78-83) -- accepts a decrypt whose pad is exactly one full 16-byte
`0x10` block. `-nopad` does not change CBC decryption itself: it only means
OpenSSL retains all 80 decrypted bytes instead of requiring/removing PKCS7
padding. Under this interpretation, the 2**-128 padding-based signal this
project has otherwise relied on does not exist -- a wrong key produces 80
bytes that look exactly as "valid" as a right key's output. The only usable
filter is address-based: does a fixed window of those 80 bytes form a real
secp256k1 scalar whose derived address is the known prize/halving address,
or (secondary, weaker) a Bloom-filter-flagged funded address.

Pre-registered, bounded scope (not an open-ended search):

* four 16-byte-block-aligned 32-byte windows, offsets {0, 16, 32, 48} --
  covering the full 80 bytes with 50% overlap. No arbitrary sliding.
* known-address exact match checked first (cheap, zero false-accept);
  the funded-address Bloom filter is secondary discovery only, and any
  Bloom hit is queued for mandatory API verification, never treated as
  confirmed on its own.
* test exactly one clue-supported two-key pairing: offsets 0 and 32 (the
  non-overlapping pair spanning the first 64 bytes -- the same "two
  32-byte keys" shape Phase 78-83 established under the padded
  interpretation). Its bounded operation family is scalar sum, both
  directed scalar differences, each scalar's secp256k1 additive inverse,
  both ordered SHA-256 concatenations, and bytewise XOR. It also checks the
  exact pair relations `a + b == 0 (mod n)` and `a XOR b == FF..FF`, plus
  both X/Y coordinate orderings as one raw public point. No other window
  pairing or arithmetic/bitwise operation is tested.

Deliberately a new, self-contained script: it only *imports* from
cb_common.py and binary_key_material_backfill.py, never edits them, so
neither file's SHA-256 changes and any currently-running sweep's checkpoint
fingerprint (which hashes both files) stays valid.

Phase 87/91 speed optimization: profiling found `private_key_details()`
(unconditional here, since -nopad has no cheap structural pre-filter -- see
above) at ~75% of runtime, and redundant PBKDF2 derivation at most of the
rest. Two fixes, both provably output-preserving (parity-tested below, not
just benchmarked):

* `private_key_details` is overridden below to use `coincurve` (Bitcoin
  Core's own libsecp256k1) instead of the `cryptography` package's generic
  OpenSSL `EC_POINT_mul` -- ~9x faster for this one curve. This is a NEW
  external dependency this script alone needs (no apt package exists;
  installed via `pip3 install --user --break-system-packages coincurve`,
  version pinned and fingerprinted into the checkpoint below -- see
  tools/gsmg/requirements.txt). Note this contradicts cb_common.py's own
  docstring ("this environment has no pip") -- empirically false in the
  environment this was implemented in; pip works fine with
  --break-system-packages. Left that comment alone (out of scope, and
  editing shared files remains something this script deliberately avoids).
* PBKDF2 derivation is cached per (kdf_param, salt, passwd): every PBKDF2
  variant sharing a `kdf_param` produces a byte-for-byte prefix of the
  longest one (a property of the RFC 8018 construction, not an assumption --
  verified directly), so deriving once at the max `dklen` any variant needs
  and slicing replaces up to 9 redundant 10,000-iteration calls with 1.

Combined measured effect (Phase 87 benchmark): 4.63 -> 22.42 keystrings/sec
single-threaded, cutting the Tier-1-scope estimate from ~29h to ~6.5h.

Phase 92: multiprocessing (`--workers`/`--chunk-size`) is now built -- a
ProcessPoolExecutor with a bounded in-flight window, workers that only
compute (never write any file), and a single parent process that owns
every checkpoint/hits/queue write. See WorkerConfig, `_sweep_parallel`, and
FINDINGS.md Phase 92 for the design (explicit `spawn` everywhere, Bloom
identity verified per-worker, idempotent writes across resumes, structural
validation of every worker result before trusting it). Benchmarked at
~169 keystrings/sec at 16 workers (~7.4x over single-threaded), projecting
the Tier-1 scope to ~52 minutes.

Phase 94: real Tier-1 launch (`--workers 8`, `wordlists/gsmg/
medium_curated_tier1_primary.txt`, 24,554 candidates / 525,436 keystrings)
completed 0 errors, 6 Bloom hits, all confirmed `bloom_false_positive` by
live Blockstream lookup -- clean negative. Added a third, independent
classification, since the confirmed prize address
(1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe) is a deliberately vanity-mined address
(FINDINGS.md Phase 28) and, unlike the Bloom filter (which only covers
addresses with real on-chain history), a vanity-prefix check needs no
funding/usage to be visible -- catching a never-used vanity-mined target
Bloom can't. Queued for API verification exactly like a Bloom hit (neither
is definitive alone). Added after the Tier-1 launch completed, so it did
not retroactively rescan the already-finished 525,436 keystrings.

Phase 95: broader output-interpretation + reliability revision (FINDINGS.md
Phase 95 has the full review that motivated this):

* The vanity check from Phase 94 was replaced: it originally matched "gsmg"
  as an unanchored substring anywhere in the address, which at Tier-1 scale
  had a non-trivial coincidental false-accept rate. `VANITY_STRONG_RE`/
  `VANITY_WEAK_RE` now anchor to the start of the address (right after the
  fixed "1" version-byte character), exactly mirroring how the real prize
  address was actually vanity-mined, and split into two tiers
  ("vanity_strong" == "^1GSMG1" exactly, "vanity_weak" == "^1GSMG[1-9]").
* Two new encoded-key candidate sources, alongside the existing raw-binary
  windows: `hex_window_candidates` (a private key written out as 64 ASCII
  hex characters, at the two block-aligned offsets that fit) and
  `wif_window_candidates` (a Base58Check WIF string anywhere in the body,
  filtered by its own checksum -- ~2**-32 false-accept, not an open-ended
  scan). Both are genuine format gaps the raw-binary-only reading could
  never have caught.
* `combo_candidates` gained a fourth combination: bytewise XOR of the two
  windows -- a natural, free "duality" operation, more directly tied to
  this investigation's "half and better half" framing than scalar_sum or
  the concat hashes are.
* Reliability: `acquire_run_lock` (exclusive flock on a sibling `.lock`
  file, held for the run's duration) stops two accidental concurrent
  invocations from interleaving writes to the same output files;
  `load_checkpoint` now tolerates exactly one truncated final line (the
  only place a hard kill could ever leave a fragment) while still raising
  on corruption anywhere earlier; `audit_completion`/`classification_counts`
  plus a `sweep()`-level summary footer (fingerprint, elapsed time, resumed/
  session/missing/duplicate counts, classification tallies) close the gap
  where confirming a run's completeness required a separate manual check;
  progress reporting now reports resumed vs. session-new counts, percentage
  of total scope, throughput, and ETA instead of a bare running count.

A review pass on the above (before any of it ran against the real corpus)
caught three further real issues, all fixed and independently reproduced:
(1) the anchored vanity check's own base-rate estimate was wrong -- see the
corrected math above VANITY_STRONG_RE/VANITY_WEAK_RE, the real Tier-1
volume is ~605.3M address checks, not ~7.35M, so neither tier is
independently compelling and both remain candidate filters, not confirmed
hits; (2) a WIF candidate's compression flag was not restricted to its own
address_type -- a compressed WIF was matching a known UNCOMPRESSED
address of the same scalar, fixed via `_allowed_address_types`; (3) the
shared verify_pending_queue has no concept of "vanity" and would label an
unfunded vanity hit `bloom_false_positive` (misleading -- a vanity address
is expected to often be unfunded), fixed via a `classification` field on
the queue record plus `relabel_vanity_verifications`/`--relabel-vanity-queue`.
"""

import argparse
import atexit
import fcntl
import hashlib
import itertools
import json
import multiprocessing
import os
import re
import sys
import tempfile
import time
from concurrent.futures import CancelledError, ProcessPoolExecutor, wait, FIRST_COMPLETED
from concurrent.futures.process import BrokenProcessPool
from pathlib import Path
from typing import NamedTuple, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

import coincurve
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

import aes_key_wrap_sweep
import binary_key_material_backfill
import cb_common
from aes_key_wrap_sweep import ALL_CBC_VARIANTS
from cb_common import (
    BLOBS,
    CIPHER_BLOCK_SIZES,
    CIPHER_CLASSES,
    ECB_CIPHER_VARIANTS,
    answer_forms,
    evp_bytes_to_key,
    keystr_forms,
    pbkdf2_bytes_to_key,
)
from extended_cipher_recheck import candidate_list_digest, load_curated_candidates
from binary_key_material_backfill import (
    DEFAULT_BLOOM,
    KNOWN_GSMG_ADDRESSES,
    SECP256K1_ORDER,
    BloomCache,
    append_jsonl,
    load_candidates,
    normalized_keystrings,
    private_key_details as _reference_private_key_details,
)

SCRIPT_DIR = Path(__file__).resolve().parent
TARGET_BLOBS = {
    "SALPH": BLOBS["SALPH"],
    "P32TRAILING": BLOBS["P32TRAILING"],
}
DEFAULT_CHECKPOINT = SCRIPT_DIR / "nopad_window_checkpoint.jsonl"
DEFAULT_HITS = SCRIPT_DIR / "nopad_window_hits.jsonl"
DEFAULT_QUEUE = SCRIPT_DIR / "nopad_window_api_queue.jsonl"

WINDOW_OFFSETS = (0, 16, 32, 48)
WINDOW_SIZE = 32
COMBO_OFFSETS = (0, 32)  # the only clue-supported pairing; see module docstring.

# The confirmed prize address (1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe) is a
# deliberately vanity-mined address -- "GSMG1" right after the version byte
# (FINDINGS.md Phase 28). A derived address matching this same anchored
# prefix is a weaker, independent signal from known-address/Bloom: unlike
# Bloom, it needs no funding/on-chain history to be visible, so it can catch
# a never-used vanity-mined target that Bloom membership alone cannot.
#
# Anchored at the start (right after the fixed "1" P2PKH version-byte
# character), not an arbitrary embedded substring -- this mirrors how vanity
# mining actually works (targeting a prefix is what standard tools search
# for; an arbitrary embedded substring is a different, far more expensive
# search) and reduces (does NOT eliminate) the false-accept rate versus an
# unanchored scan. At full Tier-1 scale the real check volume is per
# DECRYPT, not per keystring: 525,436 keystrings x 72 decrypts/keystring x
# 12 always-present scalar candidates (4 windows + 8 combos) x 2 address
# formats = ~908.1M address checks (an earlier version of this comment used
# ~7.35M, omitting the x72 decrypts/keystring factor entirely -- caught on
# review). At that real volume: strong ("^1GSMG1", 5 fixed chars after the
# leading "1") expected coincidental hits = 908.1M x 58**-5 = ~1.38;
# weak-only ("^1GSMG[2-9]", same 4 chars + 1-of-8 digits) expected
# coincidental hits = 908.1M x 8/58**5 = ~11.07. Neither tier is
# independently compelling at this volume -- both
# remain candidate filters requiring passphrase/context corroboration, not
# confirmed hits, exactly like a Bloom match. An earlier, unanchored
# version of this check would have had a substantially higher rate still
# (never run against the real corpus) and was replaced before being run.
VANITY_STRONG_RE = re.compile(r"^1GSMG1")   # the exact confirmed pattern.
VANITY_WEAK_RE = re.compile(r"^1GSMG[1-9]")  # same vanity convention, any digit.


def private_key_details(private_key):
    """Drop-in replacement for binary_key_material_backfill.private_key_details
    (kept there as `_reference_private_key_details` for the permanent parity
    test in self_test()) using coincurve/libsecp256k1 instead of `cryptography`
    /OpenSSL's generic EC_POINT_mul -- ~9x faster per Phase 87's profiling.
    Overrides the name imported above for every use in this file (check_decrypt,
    self_test, etc.) via ordinary Python name shadowing: this definition runs
    after the import, so `private_key_details` means this function from here
    on, not the imported one."""
    value = int.from_bytes(private_key, "big")
    if not 1 <= value < SECP256K1_ORDER:
        return None
    pk = coincurve.PrivateKey(private_key)
    public_keys = {
        "compressed": pk.public_key.format(compressed=True),
        "uncompressed": pk.public_key.format(compressed=False),
    }
    addresses = {}
    for address_type, public_key in public_keys.items():
        digest = binary_key_material_backfill.hash160(public_key)
        addresses[address_type] = {
            "address": binary_key_material_backfill.base58check(b"\x00" + digest),
            "hash160": digest.hex(),
            "wif": binary_key_material_backfill.base58check(
                b"\x80" + private_key + (b"\x01" if address_type == "compressed" else b"")
            ),
        }
    return addresses


def _coincurve_fingerprint():
    """Version + compiled-backend hash, so a coincurve upgrade (or a rebuilt
    .so under the same version string) invalidates a stale checkpoint rather
    than silently reusing coverage computed under different EC-math code --
    the same principle Phase 86 already applied to cb_common.py/this driver/
    binary_key_material_backfill.py/aes_key_wrap_sweep.py."""
    backend_path = Path(coincurve._libsecp256k1.__file__)
    return {
        "version": coincurve.__version__,
        "backend_sha256": hashlib.sha256(backend_path.read_bytes()).hexdigest()[:16],
    }


def _normalize_variant(variant):
    """Same shorthand cb_common._normalize_variant accepts, reimplemented
    locally rather than importing a name prefixed `_` from another module."""
    if len(variant) == 2:
        digest_name, key_len = variant
        return "legacy", digest_name, "aes", key_len
    return variant


# Every PBKDF2-kind entry across ALL_CBC_VARIANTS and ECB_CIPHER_VARIANTS
# shares one kdf_param, ("sha256", 10000) at the time of writing -- only the
# requested dklen (key_len + block) differs. PBKDF2's output for a fixed
# (password, salt, iterations, digest) is a strict byte-prefix relationship
# across dklen values (verified directly against hashlib, not assumed: RFC
# 8018's T_i blocks are computed independently of the requested output
# length), so deriving once at the max dklen any variant with this kdf_param
# needs and slicing is exactly equivalent to calling pbkdf2_bytes_to_key
# separately for each -- just without repeating the expensive part. Grouped
# by kdf_param (not hardcoded to the single current one) so this keeps
# working correctly if a second PBKDF2 parameter set is ever added.
PBKDF2_MAX_DKLEN = {}
for _variant in ALL_CBC_VARIANTS:
    _kdf_kind, _kdf_param, _cipher_name, _key_len = _normalize_variant(_variant)
    if _kdf_kind == "pbkdf2":
        _needed = _key_len + CIPHER_BLOCK_SIZES[_cipher_name]
        PBKDF2_MAX_DKLEN[_kdf_param] = max(PBKDF2_MAX_DKLEN.get(_kdf_param, 0), _needed)
for _variant in ECB_CIPHER_VARIANTS:
    _kdf_kind, _kdf_param, _key_len = _variant
    if _kdf_kind == "pbkdf2":
        PBKDF2_MAX_DKLEN[_kdf_param] = max(PBKDF2_MAX_DKLEN.get(_kdf_param, 0), _key_len)
del _variant, _kdf_kind, _kdf_param, _cipher_name, _key_len
try:
    del _needed
except NameError:
    pass


def derive_key_iv(kdf_kind, kdf_param, key_len, block, salt, passwd, pbkdf2_cache=None):
    """`pbkdf2_cache`, when given, is a dict the caller scopes to one
    keystring (see sweep()) -- entries are keyed by (kdf_param, salt, passwd)
    so they're never reused across keystrings anyway; scoping it per-keystring
    just avoids the dict growing unboundedly over a long run. `None` (the
    default, used by self_test's direct calls) always derives fresh, matching
    the original unconditional behavior exactly."""
    if kdf_kind == "legacy":
        return evp_bytes_to_key(passwd, salt, kdf_param, key_len, block)
    digest_name, iterations = kdf_param
    if pbkdf2_cache is None:
        return pbkdf2_bytes_to_key(passwd, salt, iterations, digest_name, key_len, block)
    cache_key = (kdf_param, salt, passwd)
    buf = pbkdf2_cache.get(cache_key)
    if buf is None:
        buf = hashlib.pbkdf2_hmac(
            digest_name, passwd, salt, iterations, dklen=PBKDF2_MAX_DKLEN[kdf_param],
        )
        pbkdf2_cache[cache_key] = buf
    return buf[:key_len], buf[key_len:key_len + block]


def raw_cbc_decrypt(cipher_name, key, iv, ciphertext):
    """Decrypt without touching PKCS7 padding at all -- the `-nopad`
    semantics the module docstring describes."""
    decryptor = Cipher(CIPHER_CLASSES[cipher_name](key), modes.CBC(iv)).decryptor()
    return decryptor.update(ciphertext) + decryptor.finalize()


def raw_ecb_decrypt(cipher_name, key, ciphertext):
    decryptor = Cipher(CIPHER_CLASSES[cipher_name](key), modes.ECB()).decryptor()
    return decryptor.update(ciphertext) + decryptor.finalize()


def extract_windows(body):
    return {offset: body[offset : offset + WINDOW_SIZE] for offset in WINDOW_OFFSETS}


def known_address_matches(details, known_addresses):
    """Which address_type(s) in `details` exactly match a known GSMG address.
    `known_addresses` is passed explicitly (never read from the module-level
    `KNOWN_GSMG_ADDRESSES` global here) so this function behaves identically
    whether called from the sequential path or from inside a worker process
    -- see WorkerConfig/Phase 92 for why relying on a module global would be
    unsafe under `spawn`."""
    return tuple(
        address_type
        for address_type, address_data in details.items()
        if address_data["address"] in known_addresses
    )


def bloom_matches(details, bloom):
    """Which address_type(s) in `details` the Bloom filter flags. Does NOT
    check known-address status -- callers must only reach this after every
    candidate has already cleared the known-address pass (see check_decrypt),
    so a Bloom false positive on one candidate can never suppress checking
    the others."""
    if bloom is None:
        return ()
    return tuple(
        address_type
        for address_type, address_data in details.items()
        if bloom.contains(bytes.fromhex(address_data["hash160"]))
    )


def vanity_matches(details):
    """Which address_type(s) match the strong/weak GSMG vanity-prefix
    pattern (case-sensitive -- the real vanity-mined address is exactly
    "1GSMG1", not a case-insensitive variant), independent of
    known-address/Bloom status. Returns {address_type: tier} for every
    matching address_type ("strong" or "weak"); empty dict if none match.
    "strong" still is not treated as a confirmed hit anywhere downstream --
    both tiers are queued for the same mandatory API verification."""
    matches = {}
    for address_type, address_data in details.items():
        address = address_data["address"]
        if VANITY_STRONG_RE.match(address):
            matches[address_type] = "strong"
        elif VANITY_WEAK_RE.match(address):
            matches[address_type] = "weak"
    return matches


def combo_candidates(window_a, window_b):
    """Bounded operations on the clue-supported half/better-half pair.

    Besides the already-tested sum, ordered hashes, and XOR, cover the
    direct secp256k1 meanings of "opposite/complement": each scalar's
    additive inverse and both directed differences. These are order-complete
    without introducing another window pairing or open arithmetic family."""
    a = int.from_bytes(window_a, "big")
    b = int.from_bytes(window_b, "big")
    combos = {
        "scalar_sum": ((a + b) % SECP256K1_ORDER).to_bytes(32, "big"),
        "scalar_diff_ab": ((a - b) % SECP256K1_ORDER).to_bytes(32, "big"),
        "scalar_diff_ba": ((b - a) % SECP256K1_ORDER).to_bytes(32, "big"),
        "scalar_neg_a": ((-a) % SECP256K1_ORDER).to_bytes(32, "big"),
        "scalar_neg_b": ((-b) % SECP256K1_ORDER).to_bytes(32, "big"),
        "concat_hash_ab": hashlib.sha256(window_a + window_b).digest(),
        "concat_hash_ba": hashlib.sha256(window_b + window_a).digest(),
        "xor": bytes(x ^ y for x, y in zip(window_a, window_b)),
    }
    return combos


def pair_relation_hits(window_a, window_b):
    """Return exact, effectively self-authenticating half-pair relations."""
    a = int.from_bytes(window_a, "big")
    b = int.from_bytes(window_b, "big")
    hits = []
    if (
        1 <= a < SECP256K1_ORDER
        and 1 <= b < SECP256K1_ORDER
        and (a + b) % SECP256K1_ORDER == 0
    ):
        hits.append({
            "source": "relation:scalar_additive_inverse",
            "private_key": window_a + window_b,
            "classification": "pair_relation",
            "details": {
                "relation": "b == -a mod secp256k1_order",
                "half": private_key_details(window_a),
                "better_half": private_key_details(window_b),
            },
            "matched_address_types": (),
        })
    if bytes(x ^ y for x, y in zip(window_a, window_b)) == b"\xff" * 32:
        hits.append({
            "source": "relation:bitwise_complement",
            "private_key": window_a + window_b,
            "classification": "pair_relation",
            "details": {
                "relation": "a XOR b == FF" * 32,
                "half": private_key_details(window_a),
                "better_half": private_key_details(window_b),
            },
            "matched_address_types": (),
        })
    return hits


def public_point_candidates(window_a, window_b):
    """Interpret the two halves as X/Y coordinates, in both orderings."""
    candidates = []
    field = binary_key_material_backfill.SECP256K1_FIELD
    for label, x_bytes, y_bytes in (
        ("xy", window_a, window_b),
        ("yx", window_b, window_a),
    ):
        x = int.from_bytes(x_bytes, "big")
        y = int.from_bytes(y_bytes, "big")
        if x >= field or y >= field:
            continue
        if (y * y - (x * x * x + 7)) % field:
            continue
        public_keys = {
            "compressed": bytes([2 + (y & 1)]) + x_bytes,
            "uncompressed": b"\x04" + x_bytes + y_bytes,
        }
        details = {}
        for address_type, public_key in public_keys.items():
            digest = binary_key_material_backfill.hash160(public_key)
            details[address_type] = {
                "address": binary_key_material_backfill.base58check(b"\x00" + digest),
                "hash160": digest.hex(),
                "wif": None,
            }
        candidates.append((f"public_point:{label}", x_bytes + y_bytes, details))
    return candidates


HEX_WINDOW_OFFSETS = (0, 16)  # the only two 16-byte-block-aligned offsets a
                               # 64-ASCII-hex-char (32-byte) key can occupy
                               # within an 80-byte body -- not a slide.
HEX_CANDIDATE_LENGTH = 64      # 32 bytes represented as ASCII hex digits.

WIF_LENGTHS = (51, 52)  # uncompressed (37 raw bytes) / compressed (38 raw
                         # bytes) Base58Check WIF, their standard encoded
                         # lengths.
BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_BASE58_INDEX = {char: index for index, char in enumerate(BASE58_ALPHABET)}


def hex_window_candidates(body):
    """Recognize a private key written out as 64 ASCII hex characters,
    rather than assumed to always be 32 raw binary bytes -- a genuine
    format gap the raw-window-only reading could never catch. Bounded to
    the same two block-aligned offsets as HEX_WINDOW_OFFSETS (only two fit
    a 64-byte span in an 80-byte body), not a sliding scan: the ASCII-hex
    charset requirement is itself a strict structural filter (all 64 bytes
    must decode as hex digits, probability ~(22/256)**64 by chance -- far
    stricter than the Bloom filter's own false-accept rate), so this adds
    negligible false-accept surface for the cost of two extra decode
    attempts per body."""
    candidates = []
    for offset in HEX_WINDOW_OFFSETS:
        chunk = body[offset : offset + HEX_CANDIDATE_LENGTH]
        if len(chunk) < HEX_CANDIDATE_LENGTH:
            continue
        try:
            key = bytes.fromhex(chunk.decode("ascii"))
        except (UnicodeDecodeError, ValueError):
            continue
        candidates.append((f"hex@{offset}", key))
    return candidates


def base58check_decode(text):
    """Decode+verify a Base58Check string. Returns the payload (version
    byte + key material, with the 4-byte checksum stripped) or None if any
    character falls outside the alphabet or the checksum doesn't verify.
    This checksum is the actual bound on the WIF scan below (~2**-32
    false-accept rate) -- not the fixed-length scan itself, which is why
    scanning every offset for a fixed-length window is safe here in a way
    it would not be for a raw binary scalar (which has no comparable
    self-verifying structure)."""
    if not text or any(ch not in _BASE58_INDEX for ch in text):
        return None
    value = 0
    for ch in text:
        value = value * 58 + _BASE58_INDEX[ch]
    leading_ones = len(text) - len(text.lstrip("1"))
    body = value.to_bytes((value.bit_length() + 7) // 8, "big") if value else b""
    full = b"\x00" * leading_ones + body
    if len(full) < 5:
        return None
    payload, checksum = full[:-4], full[-4:]
    if hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4] != checksum:
        return None
    return payload


def wif_window_candidates(body):
    """Recognize a private key written out as a Base58Check WIF string,
    rather than assumed to always be 32 raw binary bytes. Scans every
    fixed-length (51- or 52-character) ASCII substring of the 80-byte body
    -- <=59 positions total, not open-ended -- and keeps only the ones
    whose Base58Check checksum actually verifies. That checksum (not the
    scan itself) is the real, self-terminating filter here: it plays
    exactly the role the removed PKCS7 pad used to play for the padded
    hypothesis, so this is a bounded, self-validating check rather than an
    arbitrary sliding search over raw bytes."""
    candidates = []
    for length in WIF_LENGTHS:
        for offset in range(0, len(body) - length + 1):
            chunk = body[offset : offset + length]
            try:
                text = chunk.decode("ascii")
            except UnicodeDecodeError:
                continue
            payload = base58check_decode(text)
            if payload is None:
                continue
            if len(payload) == 33 and payload[0] == 0x80:
                candidates.append((f"wif@{offset}:uncompressed", payload[1:33]))
            elif len(payload) == 34 and payload[0] == 0x80 and payload[33] == 0x01:
                candidates.append((f"wif@{offset}:compressed", payload[1:33]))
    return candidates


def _file_sha256(module):
    return hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()[:16]


def run_fingerprint(candidates, keystrings, bloom):
    """`bloom` is the live BloomCache (or None for --no-bloom) actually used
    for this run. Behavior depends on more than the driver + cb_common: it
    also depends on binary_key_material_backfill.py and aes_key_wrap_sweep.py
    (imported for private_key_details/ALL_CBC_VARIANTS), the known-address
    set, and whether/which Bloom cache is active -- all of those must be
    fingerprinted too, or a change to any of them could silently reuse a
    checkpoint produced under different behavior."""
    blob_digest = hashlib.sha256()
    for tag, (salt, ciphertext) in TARGET_BLOBS.items():
        blob_digest.update(tag.encode() + b"\0" + salt + ciphertext)
    known_addresses_sha256 = hashlib.sha256(
        "\0".join(sorted(KNOWN_GSMG_ADDRESSES)).encode()
    ).hexdigest()[:16]
    return {
        "version": 3,
        "candidate_digest": candidate_list_digest(candidates),
        "candidate_count": len(candidates),
        "keystring_count": len(keystrings),
        "blob_digest": blob_digest.hexdigest()[:16],
        "window_offsets": list(WINDOW_OFFSETS),
        "combo_offsets": list(COMBO_OFFSETS),
        "cbc_variants": len(ALL_CBC_VARIANTS),
        "ecb_variants": len(ECB_CIPHER_VARIANTS),
        "known_addresses_sha256": known_addresses_sha256,
        "bloom_enabled": bloom is not None,
        "bloom_identity": bloom.identity if bloom is not None else None,
        "oracle_sha256": _file_sha256(cb_common),
        "driver_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:16],
        "binary_key_material_sha256": _file_sha256(binary_key_material_backfill),
        "aes_key_wrap_sha256": _file_sha256(aes_key_wrap_sweep),
        # Phase 91: private_key_details now runs on coincurve, not
        # cryptography/OpenSSL -- a coincurve upgrade (or rebuilt backend
        # under the same version string) must invalidate a stale checkpoint
        # the same way an edit to any of the source files above already does.
        "coincurve": _coincurve_fingerprint(),
    }


def load_checkpoint(path, fingerprint):
    """Load the set of already-completed keystr_sha256 digests. Tolerates
    exactly one truncated/malformed line -- and only if it is the very LAST
    line in the file: a hard kill (OOM, power loss, `kill -9`) mid-write can
    only ever leave a fragment at the tail, since every earlier line was
    already a completed, flushed append_jsonl() call before that one
    started. Corruption anywhere else in the file is never expected from
    normal operation and still raises -- this is deliberately narrow
    resilience for one specific, well-understood failure mode, not a
    general tolerance for a corrupt checkpoint."""
    path = Path(path)
    if not path.exists() or path.stat().st_size == 0:
        return set()
    lines = [line for line in path.read_text().splitlines() if line.strip()]
    records = []
    for i, line in enumerate(lines):
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            if i == len(lines) - 1:
                print(
                    f"[!] {path}: quarantining truncated final line "
                    f"(likely an interrupted write): {line[:80]!r}"
                )
                continue
            raise ValueError(
                f"{path}: corrupt checkpoint line {i} (not the final line, so not "
                f"attributable to an interrupted write) -- refusing to guess: {line[:80]!r}"
            )
    expected_header = {"header": True, **fingerprint}
    if not records or records[0] != expected_header:
        raise ValueError(f"{path}: checkpoint header does not match this run; use a new checkpoint")
    return {record["keystr_sha256"] for record in records[1:] if "keystr_sha256" in record}


def ensure_checkpoint_header(path, fingerprint):
    path = Path(path)
    if not path.exists() or path.stat().st_size == 0:
        append_jsonl(path, {"header": True, **fingerprint})


class _RunLock:
    """Wraps however many distinct-path flocks acquire_run_lock ends up
    holding, so the caller releases all of them via a single .close()
    regardless of how many there were."""

    def __init__(self, lock_files):
        self._lock_files = lock_files

    def close(self):
        for lock_file in self._lock_files:
            lock_file.close()


def acquire_run_lock(*paths):
    """Exclusive, non-blocking flock on a dedicated sibling `.lock` file for
    EACH distinct path given (not the paths themselves, so this works even
    before those files exist). Nothing previously stopped two `sweep()`
    invocations against the same output files from running at once and
    interleaving writes -- this closes that gap.

    Locking only the checkpoint path is not enough: a checkpoint/hits/queue
    trio need not share a path prefix, so two runs using different
    checkpoints but the same hits or queue file could still interleave
    writes to that shared file undetected. `sweep()` passes all three paths
    so any single shared artifact is caught, not just an identical
    checkpoint path. Duplicate paths (e.g. two arguments that happen to be
    identical) are deduplicated -- locking the same file twice in one call
    would otherwise always "conflict" with itself.

    Held for the entire run via the returned object's open file handles;
    the OS releases each flock automatically whenever this process exits,
    however it exits (normal return, exception, signal), so the caller only
    needs to keep the returned handle alive for the run's duration (via
    `.close()`), not release explicitly on every exit path. If any one of
    the requested locks is unavailable, every lock already acquired in
    this same call is released before raising -- a partial lock set is
    never left held."""
    distinct_paths = sorted({str(path) for path in paths})
    acquired = []
    try:
        for path in distinct_paths:
            lock_path = Path(path + ".lock")
            lock_file = open(lock_path, "w")
            try:
                fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                lock_file.close()
                raise SystemExit(
                    f"another sweep is already running against {path} "
                    f"(lock held on {lock_path}) -- refusing to start a second one"
                )
            acquired.append(lock_file)
    except SystemExit:
        for lock_file in acquired:
            lock_file.close()
        raise
    return _RunLock(acquired)


def record_hit(hits_path, queue_path, candidate, form, keystr, blob_tag, mode_label,
                kdf_label, source, private_key, classification, details,
                matched_address_types, bloom, seen_hit_ids=None, seen_queue_ids=None):
    """Sensitive key material always goes to the mode-0600 hits file. For
    scalar candidates this is a private key; for a pair-relation or public-
    point hit it is the complete 64-byte source pair. The API queue remains
    address-only and receives only the specific address type(s) that
    matched. Bloom and vanity classifications get queued for verification;
    exact known-address and structural-relation hits do not.

    `seen_hit_ids`/`seen_queue_ids`, when given, make each artifact write
    idempotent across resumes -- checked and updated INDEPENDENTLY of each
    other, not gated on one another: a prior crash could have written the
    sensitive hit record but crashed before writing its corresponding queue
    entry (or vice versa), so "hit_id already seen -> skip everything" would
    be wrong. `None` (the default -- used by check_decrypt/self_test's
    from-scratch temp files, where a duplicate can't arise) always writes,
    matching the original unconditional behavior exactly."""
    hit_id = hashlib.sha256(
        blob_tag.encode() + b"\0" + mode_label.encode() + b"\0" + kdf_label.encode()
        + b"\0" + source.encode() + b"\0" + keystr.encode() + b"\0" + private_key
    ).hexdigest()[:24]
    if seen_hit_ids is None or hit_id not in seen_hit_ids:
        record = {
            "hit_id": hit_id,
            "blob": blob_tag,
            "mode": mode_label,
            "kdf": kdf_label,
            "source": source,  # e.g. "window@0", "combo:scalar_sum"
            "candidate": candidate,
            "form": form,
            "passphrase_hex": keystr.encode().hex(),
            "key_material_hex": private_key.hex(),
            "private_key_hex": private_key.hex() if len(private_key) == 32 else None,
            "classification": classification,
            "matched_address_types": matched_address_types,
            "addresses": details,
            "created_at": int(time.time()),
        }
        append_jsonl(hits_path, record, sensitive=True)
        print(f"[+++ {classification.upper()} HIT] {blob_tag} {mode_label} {kdf_label} {source}")
        if seen_hit_ids is not None:
            seen_hit_ids.add(hit_id)
    if classification in (
        "bloom", "vanity_strong", "vanity_weak",
        "bloom_public_point", "vanity_strong_public_point",
        "vanity_weak_public_point",
    ):
        for address_type in matched_address_types:
            address_data = details[address_type]
            queue_id = hashlib.sha256(
                f"{hit_id}|{address_type}|{address_data['address']}".encode()
            ).hexdigest()[:24]
            if seen_queue_ids is not None and queue_id in seen_queue_ids:
                continue
            append_jsonl(queue_path, {
                "queue_id": queue_id,
                "hit_id": hit_id,
                "address_type": address_type,
                "address": address_data["address"],
                "hash160": address_data["hash160"],
                # Needed downstream to interpret an unfunded verification
                # result correctly: the shared verify_pending_queue (in
                # binary_key_material_backfill.py) has no concept of "vanity"
                # and would otherwise label an unfunded vanity address the
                # same as an unfunded Bloom coincidence -- see
                # relabel_vanity_verifications below.
                "classification": classification,
                "bloom": bloom.identity if bloom else None,
                "status": "pending",
                "attempt_count": 0,
                "created_at": int(time.time()),
            })
            if seen_queue_ids is not None:
                seen_queue_ids.add(queue_id)


def load_seen_ids(hits_path, queue_path):
    """Scan any existing hits/queue files for their hit_id/queue_id values,
    so record_hit's idempotency checks have something to check against on a
    resumed run. Malformed lines are skipped rather than raising -- this is
    a best-effort dedup aid, not a checkpoint-equivalent source of truth."""
    seen_hit_ids = set()
    hits_path = Path(hits_path)
    if hits_path.exists():
        for line in hits_path.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "hit_id" in record:
                seen_hit_ids.add(record["hit_id"])
    seen_queue_ids = set()
    queue_path = Path(queue_path)
    if queue_path.exists():
        for line in queue_path.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "queue_id" in record:
                seen_queue_ids.add(record["queue_id"])
    return seen_hit_ids, seen_queue_ids


def audit_completion(checkpoint_path, keystrings):
    """Post-run completeness check, independent of trusting the dispatch
    loop's own completed/error counters: reload the checkpoint fresh and
    verify every expected keystring digest appears in it, counting
    duplicates rather than collapsing them into a set (a plain-set load
    could never notice one). Returns (missing_digests, duplicate_digests) --
    `missing` is expected and fine when errors occurred this run (those
    keystrings are simply retryable on the next resume); `duplicate` is
    never expected and always worth surfacing loudly, since normal
    operation only ever appends one checkpoint line per newly-completed
    keystring."""
    checkpoint_path = Path(checkpoint_path)
    lines = [
        line for line in checkpoint_path.read_text().splitlines() if line.strip()
    ] if checkpoint_path.exists() else []
    digest_counts = {}
    for line in lines[1:]:  # skip the header line
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        digest = record.get("keystr_sha256")
        if digest is not None:
            digest_counts[digest] = digest_counts.get(digest, 0) + 1
    expected_digests = {
        hashlib.sha256(keystr.encode()).hexdigest() for _, _, keystr in keystrings
    }
    missing = expected_digests - set(digest_counts)
    duplicates = {digest: count for digest, count in digest_counts.items() if count > 1}
    return missing, duplicates


def classification_counts(hits_path):
    """Tally hits by `classification` for the final summary. Reads the
    (always small -- hits are rare by design) hits file directly rather
    than threading counters through both the sequential and parallel
    dispatch paths, which would mean invasive plumbing changes across
    _apply_chunk_results/_drain_interrupted/_sweep_sequential for a
    once-at-the-end reporting need. Malformed lines are skipped, matching
    load_seen_ids's existing tolerance."""
    counts = {}
    hits_path = Path(hits_path)
    if not hits_path.exists():
        return counts
    for line in hits_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        classification = record.get("classification")
        if classification is not None:
            counts[classification] = counts.get(classification, 0) + 1
    return counts


def relabel_vanity_verifications(queue_path):
    """The shared `binary_key_material_backfill.verify_pending_queue` has
    no concept of "vanity" -- it labels any address with no on-chain
    history `bloom_false_positive`, which is actively misleading for a
    vanity-tier hit: a vanity-mined address is *expected* to often be
    unfunded (mining it costs nothing; funding it is a separate, optional
    step), so "no transaction history" is not evidence the vanity match
    itself is wrong the way it is for an actual Bloom coincidence -- it
    remains weak evidence warranting passphrase/context review, not a
    dismissed false positive.

    Rewrites the *reported* status (not the underlying verification --
    real funded/used-empty findings are left untouched) for any
    vanity-classified queue entry currently showing `bloom_false_positive`
    to `unfunded` instead, via a new append (matching this file's
    append-only/latest-wins queue convention -- see
    binary_key_material_backfill.latest_queue_state). Must be run AFTER
    `verify_pending_queue`, not instead of it: this only relabels an
    already-recorded verification result and makes no API calls of its
    own. Returns the number of entries relabeled."""
    state = binary_key_material_backfill.latest_queue_state(queue_path)
    relabeled = 0
    for record in state.values():
        if (
            record.get("classification") in (
                "vanity_strong", "vanity_weak",
                "vanity_strong_public_point", "vanity_weak_public_point",
            )
            and record.get("status") == "bloom_false_positive"
        ):
            append_jsonl(queue_path, {**record, "status": "unfunded"})
            relabeled += 1
    return relabeled


def _allowed_address_types(source):
    """WIF-sourced candidates explicitly assert which pubkey format they
    are for (the WIF compression flag): a compressed WIF only ever
    produces the compressed address in real wallet software, so checking
    the OTHER (uncompressed) address derived from the same scalar would be
    testing an interpretation the ciphertext's own encoding never claimed.
    Raw window/combo/hex candidates carry no such assertion, so both
    address types stay in play for those -- `None` means "no restriction".
    A real bug this closes: a compressed WIF embedded in a body was
    matching against a known *uncompressed* address, and being reported as
    a "known" hit -- confirmed by direct reproduction before this fix."""
    if source.endswith(":compressed"):
        return frozenset({"compressed"})
    if source.endswith(":uncompressed"):
        return frozenset({"uncompressed"})
    return None


def evaluate_body(body, bloom, known_addresses):
    """Check one 80-byte nopad decrypt. Candidates come from the 4 raw
    windows, 8 bounded operations on the clue-supported (0, 32) pair, both
    possible X/Y public-point orderings, up to 2 ASCII-hex windows, and any
    self-checksum-validated WIF strings. Exact pair relations are retained
    as structural hits independently of address state. Every address-bearing
    candidate is checked in the same two passes --

    1. every candidate against the exact known-address set first, with no
       Bloom/vanity checks at all in this pass;
    2. only if pass 1 found nothing, every candidate against the anchored
       vanity-prefix check (VANITY_STRONG_RE/VANITY_WEAK_RE, unconditional)
       and, if a Bloom cache is active, the Bloom filter -- queuing only
       the specific address_type(s) that matched each.

    This ordering is required, not cosmetic: a Bloom/vanity false positive
    on any one candidate must never prevent checking the others, including
    one that is the actual known-address match.

    Pure -- returns a list of hit dicts (`source`, `private_key`,
    `classification`, `details`, `matched_address_types`) instead of writing
    anything, so this same function can run identically inside a worker
    process (Phase 92) or the sequential path. Deliberately takes only
    `bloom`/`known_addresses`, not blob/mode/kdf labels or the candidate/
    form/keystr bookkeeping fields -- those play no role in the
    classification math, only in labeling the eventual record, and are
    stitched on by the caller (`evaluate_keystring`/`check_decrypt`)."""
    windows = extract_windows(body)
    window_a, window_b = windows[COMBO_OFFSETS[0]], windows[COMBO_OFFSETS[1]]
    all_candidates = (
        [(f"window@{offset}", windows[offset]) for offset in WINDOW_OFFSETS]
        + [(f"combo:{name}", key) for name, key in combo_candidates(window_a, window_b).items()]
        + hex_window_candidates(body)
        + wif_window_candidates(body)
    )

    evaluated = []
    found_known = False
    hits = pair_relation_hits(window_a, window_b)
    for source, private_key in all_candidates:
        details = private_key_details(private_key)
        if details is None:
            evaluated.append((source, private_key, None, None))
            continue
        # A WIF-sourced candidate asserts which pubkey format it's for (the
        # WIF compression flag) -- restrict matching to only that
        # address_type; see _allowed_address_types. `details` (both types)
        # is still what gets stored in the eventual hit record, so it stays
        # available for context even though only `checkable` is matched
        # against.
        allowed_types = _allowed_address_types(source)
        checkable = (
            details if allowed_types is None
            else {t: d for t, d in details.items() if t in allowed_types}
        )
        matches = known_address_matches(checkable, known_addresses)
        evaluated.append((source, private_key, details, checkable))
        if matches:
            found_known = True
            hits.append({
                "source": source, "private_key": private_key,
                "classification": "known", "details": details,
                "matched_address_types": matches,
            })
    for source, material, details in public_point_candidates(window_a, window_b):
        matches = known_address_matches(details, known_addresses)
        evaluated.append((source, material, details, details))
        if matches:
            found_known = True
            hits.append({
                "source": source, "private_key": material,
                "classification": "known_public_point", "details": details,
                "matched_address_types": matches,
            })
    if found_known:
        return hits

    for source, private_key, details, checkable in evaluated:
        if details is None:
            continue
        public_point = source.startswith("public_point:")
        vanity = vanity_matches(checkable)
        if vanity:
            # Grouped by tier, not one hit per address_type: the common
            # case is both address_types (if either matches at all) landing
            # in the same tier, but a compressed/uncompressed split across
            # tiers is handled correctly rather than assumed away.
            for tier in set(vanity.values()):
                types_at_tier = tuple(t for t, tr in vanity.items() if tr == tier)
                hits.append({
                    "source": source, "private_key": private_key,
                    "classification": (
                        f"vanity_{tier}_public_point"
                        if public_point else f"vanity_{tier}"
                    ),
                    "details": details,
                    "matched_address_types": types_at_tier,
                })
        if bloom is not None:
            matches = bloom_matches(checkable, bloom)
            if matches:
                hits.append({
                    "source": source, "private_key": private_key,
                    "classification": (
                        "bloom_public_point" if public_point else "bloom"
                    ),
                    "details": details,
                    "matched_address_types": matches,
                })
    return hits


def evaluate_keystring(keystr, bloom, known_addresses, target_blobs, cbc_variants, ecb_variants):
    """The full 72-decrypt (36 variants x 2 blobs) inner loop for one
    keystring. Pure -- no candidate/form arguments, no file I/O, no implicit
    reliance on any module-level global (everything that could vary by run
    configuration is an explicit parameter) -- so the sequential path and a
    multiprocessing worker (Phase 92) call this identically and can never
    silently diverge. Returns a flat list of
    `(blob_tag, mode_label, kdf_label, hit_dict)` tuples.

    `pbkdf2_cache` is local to this one call: its key includes `passwd`, so
    it would never produce a cache hit across different keystrings anyway,
    and hoisting it to a wider scope (e.g. a worker-global reused across
    many keystrings in a long-lived process) would leak memory for zero
    benefit."""
    passwd = keystr.encode()
    pbkdf2_cache = {}
    results = []
    for tag, (salt, ciphertext) in target_blobs.items():
        for variant in cbc_variants:
            kdf_kind, kdf_param, cipher_name, key_len = _normalize_variant(variant)
            block = CIPHER_BLOCK_SIZES[cipher_name]
            if len(ciphertext) % block != 0:
                continue
            key, iv = derive_key_iv(
                kdf_kind, kdf_param, key_len, block, salt, passwd, pbkdf2_cache,
            )
            body = raw_cbc_decrypt(cipher_name, key, iv, ciphertext)
            kdf_label = cb_common._kdf_label(kdf_kind, kdf_param, cipher_name)
            mode_label = "cbc"
            for hit in evaluate_body(body, bloom, known_addresses):
                results.append((tag, mode_label, f"{kdf_label}/{key_len * 8}", hit))
        for variant in ecb_variants:
            # ecb_variants is AES-only: (kdf_kind, kdf_param, key_len), not
            # the CBC 4-tuple shape -- no _normalize_variant() here.
            kdf_kind, kdf_param, key_len = variant
            cipher_name = "aes"
            block = CIPHER_BLOCK_SIZES[cipher_name]
            if len(ciphertext) % block != 0:
                continue
            key, _ = derive_key_iv(
                kdf_kind, kdf_param, key_len, 0, salt, passwd, pbkdf2_cache,
            )
            body = raw_ecb_decrypt(cipher_name, key, ciphertext)
            kdf_label = cb_common._kdf_label(kdf_kind, kdf_param, cipher_name)
            mode_label = "ecb"
            for hit in evaluate_body(body, bloom, known_addresses):
                results.append((tag, mode_label, f"{kdf_label}/{key_len * 8}", hit))
    return results


class WorkerConfig(NamedTuple):
    """Everything a multiprocessing worker needs to reproduce the exact same
    computation as the parent -- passed explicitly as data (never read from
    a module-level global) so behavior can't silently differ under `spawn`
    (which re-imports this module fresh in every worker) versus however it
    happened to be initialized in the parent process. Stricter than strictly
    required for target_blobs/cbc_variants/ecb_variants (nothing mutates
    those after import today), included anyway so the worker's computation
    has zero implicit dependency on module-level state surviving any
    particular start method, and so a self-test can exercise a deliberately
    *different* known_addresses through the real worker path."""
    bloom_cache_path: Optional[str]
    bloom_identity: Optional[dict]   # the PARENT's BloomCache.identity, for
                                      # cross-checking against what the
                                      # worker itself opens -- see
                                      # _worker_init.
    known_addresses: frozenset
    target_blobs: tuple              # ((tag, salt, ciphertext), ...) -- a
                                      # plain dict field on a NamedTuple is
                                      # still a mutable dict; an ordered
                                      # tuple-of-tuples is what's actually
                                      # immutable.
    cbc_variants: tuple
    ecb_variants: tuple


# Worker-process globals: set exactly once by _worker_init when the worker
# process starts, never mutated afterward. Not the "config mutated before
# pool creation" bug class this project has already hit once
# (test_9ary_config_survives_spawn) -- these are set correctly, from
# explicit data, inside the child process itself, by the initializer
# mechanism `ProcessPoolExecutor` provides for exactly this purpose.
_worker_config = None
_worker_bloom = None
_worker_target_blobs = None  # dict form of config.target_blobs, precomputed
                              # once in _worker_init rather than reconverting
                              # config.target_blobs on every _process_chunk
                              # call (each worker processes many chunks).


def _worker_init(config):
    """Runs once per worker process, via ProcessPoolExecutor's
    initializer/initargs. Opens this worker's own BloomCache (mmap'd
    read-only -- safe for many processes to map the same file
    simultaneously, since `contains()` never writes and the OS page cache
    shares the underlying physical pages across all of them) and verifies
    its identity matches what the parent fingerprinted before the pool was
    created, closing a race where the Bloom file could otherwise be
    replaced/rebuilt in the window between parent-side fingerprinting and
    this worker actually starting up."""
    global _worker_config, _worker_bloom, _worker_target_blobs
    _worker_config = config
    _worker_target_blobs = {tag: (salt, ct) for tag, salt, ct in config.target_blobs}
    if config.bloom_cache_path is not None:
        _worker_bloom = BloomCache(config.bloom_cache_path)
        if _worker_bloom.identity != config.bloom_identity:
            raise ValueError(
                f"worker Bloom cache identity mismatch: expected "
                f"{config.bloom_identity}, got {_worker_bloom.identity} -- "
                f"the Bloom file may have changed since the parent "
                f"fingerprinted it"
            )
        atexit.register(_worker_bloom.close)
    else:
        _worker_bloom = None


def _process_chunk(chunk):
    """Runs in a worker process. `chunk` is a list of
    `(index, candidate, form, keystr, keystr_digest)` tuples (the parent
    already computed keystr_digest and retains the full tuples itself, so
    the worker doesn't need to return keystr/candidate/form back -- see
    _iter_chunks). Returns one `(index, keystr_digest, hits, error)` entry
    per input item, always -- never lets one bad keystring discard its
    chunk-mates' results by letting an exception propagate out of the
    per-item loop.

    Reads config/Bloom from the worker-globals _worker_init already set;
    does NOT take a config argument itself -- passing it again on every
    call would waste IPC/pickling and could let a later chunk silently
    carry a different config than the Bloom cache this worker actually
    initialized with. Never writes to any file -- workers only compute."""
    config = _worker_config
    results = []
    for index, candidate, form, keystr, keystr_digest in chunk:
        try:
            hits = evaluate_keystring(
                keystr, _worker_bloom, config.known_addresses, _worker_target_blobs,
                config.cbc_variants, config.ecb_variants,
            )
            results.append((index, keystr_digest, hits, None))
        except Exception as exc:
            # Never return exception text (str(exc)) -- some library call
            # could in principle echo input data (a password candidate).
            # Class name only.
            results.append((index, keystr_digest, None, type(exc).__name__))
    return results


def _process_chunk_test_always_fail(chunk):
    """Test-only, module-level (so it's picklable under `spawn`): simulates
    something escaping `_process_chunk`'s own per-item try/except entirely
    -- used by self_test() to exercise the whole-future-failure path in
    `_handle_future_result` for real, via an actual worker process."""
    raise RuntimeError("deliberate whole-future failure for testing")


def _worker_init_test_always_fail(config):
    """Test-only: an initializer that always fails, for self_test() to
    exercise the BrokenProcessPool path for real."""
    raise RuntimeError("deliberate initializer failure for testing")


def _process_chunk_test_slow(chunk, started_event):
    """Test-only: signals `started_event` the instant it actually begins
    executing (so a test can deterministically wait until this task is
    genuinely running, rather than guessing based on wall-clock timing --
    worker startup time under `spawn` is not fast enough, or consistent
    enough, to assume any fixed delay is "surely long enough"), sleeps
    briefly, then returns a normal, validly-shaped, empty-hits result.
    Occupies a single-worker pool long enough for a KeyboardInterrupt-
    draining test to reliably submit and cancel a second, still-queued
    chunk before this one finishes. Returns realistic `_process_chunk`-
    shaped output (unlike submitting bare `time.sleep` directly, whose
    `None` return value isn't chunk-result-shaped and would be misread as
    a failure)."""
    started_event.set()
    time.sleep(0.5)
    return [
        (index, keystr_digest, [], None)
        for index, candidate, form, keystr, keystr_digest in chunk
    ]


def _process_chunk_test_intermittent(chunk):
    """Test-only: raises for the ENTIRE chunk if any of its keystrings is
    exactly "POISON" -- a whole-future failure (the ordinary,
    non-pool-breaking kind `_handle_future_result` turns into
    `chunk_results is None`), not a per-item one. This distinction matters:
    a per-item failure (one item's own `error` field set, chunk otherwise
    returned normally) flows entirely through `_apply_chunk_results`, which
    was never the buggy code path. The missing-replenishment bug
    specifically lived in the `if chunk_results is None: ... continue`
    branch -- reachable only by a WHOLE chunk failing outright, which is
    what this function simulates. (An earlier version of this test function
    returned per-item error markers instead and, despite looking like it
    was testing failure handling, never actually exercised the buggy
    branch at all -- caught by deliberately reintroducing the bug in a
    scratch copy and confirming the test still passed; only failed once
    this function was corrected to raise for the whole chunk.)"""
    for index, candidate, form, keystr, keystr_digest in chunk:
        if keystr == "POISON":
            raise RuntimeError("deliberate whole-chunk test failure")
    return [
        (index, keystr_digest, [], None)
        for index, candidate, form, keystr, keystr_digest in chunk
    ]


def _iter_chunks(keystrings, completed, chunk_size):
    """Lazy: never materializes a second ~525K-item list alongside the
    already-loaded `keystrings` list. Skips already-checkpointed items on
    the fly and yields chunk_size-sized lists on demand. Each yielded item
    is a 5-tuple `(index, candidate, form, keystr, keystr_digest)` -- the
    parent computes and keeps keystr_digest here (not inside a worker's
    try/except) since it's part of the same atomic per-item unit the rest
    of the pipeline already treats that way, not something split across the
    process boundary."""
    chunk = []
    for index, (candidate, form, keystr) in enumerate(keystrings):
        keystr_digest = hashlib.sha256(keystr.encode()).hexdigest()
        if keystr_digest in completed:
            continue
        chunk.append((index, candidate, form, keystr, keystr_digest))
        if len(chunk) >= chunk_size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def check_decrypt(body, blob_tag, mode_label, kdf_label, candidate, form, keystr,
                   hits_path, queue_path, bloom, known_addresses=None):
    """Sequential-path/self-test wrapper: evaluate, then write immediately
    (today's exact observable behavior). `known_addresses` defaults to the
    live module-level `KNOWN_GSMG_ADDRESSES` (so pre-Phase-92 call sites,
    including self_test's synthetic-known-key override via a `global`
    reassignment, keep working unchanged) but can be overridden explicitly."""
    if known_addresses is None:
        known_addresses = KNOWN_GSMG_ADDRESSES
    hits = evaluate_body(body, bloom, known_addresses)
    for hit in hits:
        record_hit(
            hits_path, queue_path, candidate, form, keystr, blob_tag, mode_label,
            kdf_label, hit["source"], hit["private_key"], hit["classification"],
            hit["details"], hit["matched_address_types"], bloom,
        )
    return hits


def _apply_chunk_results(original_chunk, chunk_results, hits_path, queue_path,
                          checkpoint_path, bloom, seen_hit_ids, seen_queue_ids):
    """Validate `chunk_results` against `original_chunk` as a structural
    sanity check independent of trusting `_process_chunk`'s implementation
    to always behave correctly (a future bug there -- a refactor that
    accidentally drops or double-emits an item without raising -- would
    otherwise silently corrupt the checkpoint rather than getting caught):
    the set of `(index, keystr_digest)` pairs returned must exactly match
    what was submitted, same count, no missing/duplicate/unexpected
    entries. On mismatch, the entire chunk is treated as failed -- none of
    it checkpointed, every original digest logged -- rather than trying to
    partially trust an already-inconsistent result.

    Otherwise, for every successfully-processed keystring: write each hit
    via `record_hit` (idempotent across resumes) and append one checkpoint
    line. This -- along with the sequential path in `sweep()` -- is the
    ONLY place any file write happens; satisfies "workers only compute,
    single parent writes" by construction.

    Factored out from the dispatch loop specifically so it's directly
    unit-testable without needing a real process pool.

    Returns (num_completed, num_errors)."""
    chunk_by_index = {
        index: (candidate, form, keystr)
        for index, candidate, form, keystr, _ in original_chunk
    }
    expected = [(index, digest) for index, _, _, _, digest in original_chunk]
    actual = [(index, digest) for index, digest, _hits, _error in chunk_results]
    if len(actual) != len(expected) or set(actual) != set(expected):
        for index, _, _, _, digest in original_chunk:
            print(f"[!] malformed chunk result (set mismatch) keystr_digest={digest}")
        return 0, len(original_chunk)

    num_completed = 0
    num_errors = 0
    for index, digest, hits, error in chunk_results:
        candidate, form, keystr = chunk_by_index[index]
        if error is not None:
            print(f"[!] keystring failure keystr_digest={digest} error={error}")
            num_errors += 1
            continue
        for tag, mode_label, kdf_label, hit in hits:
            record_hit(
                hits_path, queue_path, candidate, form, keystr, tag, mode_label,
                kdf_label, hit["source"], hit["private_key"], hit["classification"],
                hit["details"], hit["matched_address_types"], bloom,
                seen_hit_ids, seen_queue_ids,
            )
        append_jsonl(checkpoint_path, {"index": index, "keystr_sha256": digest})
        num_completed += 1
    return num_completed, num_errors


def _handle_future_result(fut, original_chunk):
    """Resolve one completed future. Two distinct failure classes:

    - `BrokenProcessPool` (the executor itself can no longer run anything,
      e.g. an initializer failed for every worker): re-raised for the
      caller to handle specially -- stop submitting entirely, do not treat
      it as an ordinary per-chunk failure.
    - any other exception (something escaped `_process_chunk`'s own
      per-item try/except -- e.g. the worker process itself died mid-chunk):
      an ordinary, if unexpected, failure. Log every keystr_digest in the
      lost chunk and return `None` -- the pool may continue with other
      chunks.

    Returns the raw `chunk_results` list on success, `None` on an ordinary
    whole-future failure."""
    try:
        return fut.result()
    except BrokenProcessPool:
        raise
    except Exception as exc:
        for index, _, _, _, digest in original_chunk:
            print(f"[!] chunk failure keystr_digest={digest} error={type(exc).__name__}")
        return None


def _drain_interrupted(pending, future_to_chunk, hits_path, queue_path, checkpoint_path,
                        bloom, seen_hit_ids, seen_queue_ids):
    """`KeyboardInterrupt` handling, factored out for direct testability.
    `fut.cancel()` returns `True` only for futures that hadn't started yet
    -- those are simply dropped: never run, nothing to process, and NOT a
    computation failure (a `CancelledError` from a future *we* intentionally
    cancelled is an expected outcome of shutting down, not an error, so it
    must never be logged/counted as one -- this is why cancellation is
    checked and filtered BEFORE anything is ever passed to
    `_handle_future_result`, rather than relying on that function to somehow
    distinguish a cancellation from a real failure after the fact). Futures
    still running (`cancel()` returns `False`) are drained -- waited on and
    processed through the normal writer path exactly like any other
    completed chunk -- not discarded just because the interrupt fired while
    they were in flight. Returns (total_completed, total_errors)."""
    still_running = [fut for fut in pending if not fut.cancel()]
    total_completed = 0
    total_errors = 0
    for fut in still_running:
        original_chunk = future_to_chunk.pop(fut)
        try:
            chunk_results = _handle_future_result(fut, original_chunk)
        except BrokenProcessPool:
            total_errors += len(original_chunk)
            continue
        if chunk_results is None:
            total_errors += len(original_chunk)
            continue
        completed_n, errors_n = _apply_chunk_results(
            original_chunk, chunk_results, hits_path, queue_path, checkpoint_path,
            bloom, seen_hit_ids, seen_queue_ids,
        )
        total_completed += completed_n
        total_errors += errors_n
    return total_completed, total_errors


def _format_progress(session_completed, resumed_count, total, error_count, start_time):
    """Shared by both dispatch paths: total-scope percentage (resumed +
    session, not just this session's slice), session-only throughput (rate/
    ETA exclude resumed items -- they were never redone this run, so
    counting them would inflate the rate), and an explicit resumed/session
    split so a resumed run's progress output doesn't read as if the whole
    run started from zero."""
    elapsed = time.monotonic() - start_time
    rate = session_completed / elapsed if elapsed > 0 else 0.0
    done = resumed_count + session_completed
    pct = 100.0 * done / total if total else 100.0
    remaining = max(total - done, 0)
    eta_str = f"{remaining / rate / 60:.1f}m" if rate > 0 else "?"
    return (
        f"[*] progress {done:,}/{total:,} ({pct:.1f}%) session={session_completed:,} "
        f"resumed={resumed_count:,} errors={error_count} rate={rate:.1f}/s eta={eta_str}"
    )


def _sweep_sequential(args, keystrings, completed, bloom, seen_hit_ids, seen_queue_ids):
    """--workers 1 (default): today's exact code path, no pool created at
    all. Shares evaluate_keystring with the parallel path below -- the
    sequential and parallel paths can never silently diverge, since there
    is only one implementation of "what does the -nopad oracle check for a
    given keystring." """
    resumed_count = len(completed)
    total = len(keystrings)
    session_completed = 0
    start_time = time.monotonic()
    for index, (candidate, form, keystr) in enumerate(keystrings):
        keystr_digest = hashlib.sha256(keystr.encode()).hexdigest()
        if keystr_digest in completed:
            continue
        results = evaluate_keystring(
            keystr, bloom, KNOWN_GSMG_ADDRESSES, TARGET_BLOBS,
            ALL_CBC_VARIANTS, ECB_CIPHER_VARIANTS,
        )
        for tag, mode_label, kdf_label, hit in results:
            record_hit(
                args.hits, args.queue, candidate, form, keystr, tag, mode_label,
                kdf_label, hit["source"], hit["private_key"], hit["classification"],
                hit["details"], hit["matched_address_types"], bloom,
                seen_hit_ids, seen_queue_ids,
            )
        append_jsonl(args.checkpoint, {"index": index, "keystr_sha256": keystr_digest})
        session_completed += 1
        if session_completed % 250 == 0 or index + 1 == total:
            print(_format_progress(session_completed, resumed_count, total, 0, start_time))


def _sweep_parallel(args, keystrings, completed, bloom, seen_hit_ids, seen_queue_ids,
                     worker_fn=None):
    """--workers N, N>1: ProcessPoolExecutor with a bounded in-flight window
    (mirroring cosmic_sweep_9ary.py), explicit `spawn` context (not just in
    tests -- see WorkerConfig), and a single parent process that is the only
    thing that ever writes checkpoint/hits/queue files.

    `worker_fn` defaults to the real `_process_chunk`; self_test() overrides
    it with a test-only function that deliberately fails a subset of items,
    so the exact real dispatch/replenishment/draining control flow gets
    exercised end-to-end with real interspersed failures -- not just the
    individual helper functions in isolation (which is how the missing-
    replenishment bug escaped the first review pass)."""
    if worker_fn is None:
        worker_fn = _process_chunk
    chunk_iter = _iter_chunks(keystrings, completed, args.chunk_size)
    try:
        first_chunk = next(chunk_iter)
    except StopIteration:
        print("[*] no unfinished work remains -- skipping pool creation")
        return
    chunk_iter = itertools.chain([first_chunk], chunk_iter)

    config = WorkerConfig(
        bloom_cache_path=str(args.bloom_cache) if bloom is not None else None,
        bloom_identity=bloom.identity if bloom is not None else None,
        known_addresses=frozenset(KNOWN_GSMG_ADDRESSES),
        target_blobs=tuple((tag, salt, ct) for tag, (salt, ct) in TARGET_BLOBS.items()),
        cbc_variants=tuple(ALL_CBC_VARIANTS),
        ecb_variants=tuple(ECB_CIPHER_VARIANTS),
    )
    max_in_flight = max(args.workers * 4, 8)
    resumed_count = len(completed)
    total = len(keystrings)
    total_completed = 0
    last_reported = 0
    error_count = 0
    start_time = time.monotonic()

    mp_context = multiprocessing.get_context("spawn")
    try:
        with ProcessPoolExecutor(
            max_workers=args.workers, mp_context=mp_context,
            initializer=_worker_init, initargs=(config,),
        ) as executor:
            future_to_chunk = {}
            pending = set()

            def submit_next():
                chunk = next(chunk_iter, None)
                if chunk is None:
                    return False
                fut = executor.submit(worker_fn, chunk)
                future_to_chunk[fut] = chunk
                pending.add(fut)
                return True

            for _ in range(max_in_flight):
                if not submit_next():
                    break

            try:
                while pending:
                    done, pending = wait(pending, return_when=FIRST_COMPLETED)
                    for fut in done:
                        original_chunk = future_to_chunk.pop(fut)
                        try:
                            chunk_results = _handle_future_result(fut, original_chunk)
                        except BrokenProcessPool:
                            print("[!] process pool broken -- stopping, not dispatching further work")
                            error_count += len(original_chunk)
                            for remaining_chunk in future_to_chunk.values():
                                for _, _, _, _, digest in remaining_chunk:
                                    print(f"[!] unresolved due to broken pool keystr_digest={digest}")
                                    error_count += 1
                            # Propagate out of the `with` block deliberately,
                            # rather than calling shutdown()+sys.exit() here:
                            # the `with` block's own __exit__ already performs
                            # one clean shutdown on the way out (the pool is
                            # dead either way), so doing it again here -- then
                            # calling sys.exit() from *inside* the block, which
                            # would trigger yet another shutdown via __exit__
                            # on the way out of that exit -- is exactly the
                            # kind of double-shutdown-through-SystemExit
                            # ambiguity worth avoiding, caught on review.
                            raise
                        if chunk_results is None:
                            error_count += len(original_chunk)
                        else:
                            completed_n, errors_n = _apply_chunk_results(
                                original_chunk, chunk_results, args.hits, args.queue,
                                args.checkpoint, bloom, seen_hit_ids, seen_queue_ids,
                            )
                            total_completed += completed_n
                            error_count += errors_n
                            if total_completed - last_reported >= 250:
                                print(_format_progress(
                                    total_completed, resumed_count, total, error_count, start_time,
                                ))
                                last_reported = total_completed
                        # Always replenish -- for both success and an ordinary
                        # (non-pool-breaking) failure. An earlier version only
                        # called this after the success branch (inside a
                        # `continue`d-past `if chunk_results is None` check),
                        # which skipped replenishment on every ordinary
                        # failure -- shrinking the in-flight window each time
                        # one occurred, and, given enough failures, emptying
                        # `pending` (ending the `while pending:` loop) while
                        # chunks remained undispatched in chunk_iter. Caught on
                        # review, confirmed by reading the control flow
                        # directly.
                        submit_next()
            except KeyboardInterrupt:
                print("[!] interrupted -- cancelling queued work, draining in-flight chunks...")
                # Drain every future still unresolved -- `set(future_to_chunk)`,
                # not just `pending`. KeyboardInterrupt can land at any bytecode
                # boundary, including mid-iteration over `done`: if it arrives
                # after some futures in the current `done` batch were already
                # popped and processed but before others were, those remaining
                # ones are still keys in `future_to_chunk` yet are NOT in
                # `pending` (which only reflects the not-yet-done set from the
                # last wait() call) -- using `pending` alone would silently lose
                # their already-computed results. Caught on review.
                completed_n, errors_n = _drain_interrupted(
                    set(future_to_chunk), future_to_chunk, args.hits, args.queue,
                    args.checkpoint, bloom, seen_hit_ids, seen_queue_ids,
                )
                total_completed += completed_n
                error_count += errors_n
                # Propagate out of the `with` block rather than calling
                # shutdown(wait=True) here and then sys.exit() while still
                # inside it -- the `with` block's own __exit__ already
                # performs exactly that shutdown on the way out. Doing both
                # would be the same redundant-double-shutdown-through-
                # SystemExit pattern already fixed for the broken-pool path
                # just below (caught on review there; applied here too for
                # consistency even though this specific case -- a healthy
                # pool asked to wait -- is lower-risk than the broken-pool
                # one).
                raise
    except BrokenProcessPool:
        print(f"[*] final: {total_completed:,} completed, {error_count} errors")
        sys.exit(1)
    except KeyboardInterrupt:
        print(f"[*] interrupted: {total_completed:,} completed, {error_count} errors")
        sys.exit(130)

    print(f"[*] final: {total_completed:,} completed, {error_count} errors")
    if error_count:
        sys.exit(1)


def sweep(args):
    if args.workers < 1:
        raise SystemExit(f"--workers must be >= 1, got {args.workers}")
    if args.chunk_size < 1:
        raise SystemExit(f"--chunk-size must be >= 1, got {args.chunk_size}")

    # Held for the entire run (released automatically at process exit,
    # however it exits) -- guards against a second accidental `sweep()`
    # invocation against any of these three output files interleaving
    # writes, even if it uses a different checkpoint path but shares the
    # hits or queue file.
    lock_file = acquire_run_lock(args.checkpoint, args.hits, args.queue)
    try:
        candidates = load_candidates(args.candidate_file)
        keystrings = normalized_keystrings(candidates)
        if args.limit is not None:
            keystrings = keystrings[: args.limit]
        # Bloom must exist before fingerprinting: which cache (or none, under
        # --no-bloom) is active changes sweep behavior and is part of the
        # fingerprint below, so a checkpoint from one Bloom state is never
        # silently reused under a different one.
        bloom = None if args.no_bloom else BloomCache(args.bloom_cache)
        try:
            fingerprint = run_fingerprint(candidates, keystrings, bloom)
            completed = load_checkpoint(args.checkpoint, fingerprint)
            ensure_checkpoint_header(args.checkpoint, fingerprint)
            # Idempotency across resumes: a crash between writing a hit and
            # writing its checkpoint line (pre-existing risk, not introduced
            # by multiprocessing, but easier to hit once many keystrings can
            # be "in flight" at once) would otherwise produce an exact
            # duplicate hit/queue record on the next resume (deterministic
            # hit_id/queue_id, not a fresh UUID).
            seen_hit_ids, seen_queue_ids = load_seen_ids(args.hits, args.queue)
            operations_per_key = len(TARGET_BLOBS) * (len(ALL_CBC_VARIANTS) + len(ECB_CIPHER_VARIANTS))
            print(
                f"[*] candidates={len(candidates):,} digest={fingerprint['candidate_digest']} "
                f"keystrings={len(keystrings):,} operations/key={operations_per_key} "
                f"windows={list(WINDOW_OFFSETS)} combo_pair={list(COMBO_OFFSETS)} "
                f"hex_offsets={list(HEX_WINDOW_OFFSETS)} wif_lengths={list(WIF_LENGTHS)} "
                f"workers={args.workers} chunk_size={args.chunk_size}"
            )
            start_time = time.monotonic()
            exit_code = None
            try:
                if args.workers == 1:
                    _sweep_sequential(args, keystrings, completed, bloom, seen_hit_ids, seen_queue_ids)
                else:
                    _sweep_parallel(args, keystrings, completed, bloom, seen_hit_ids, seen_queue_ids)
            except SystemExit as exc:
                # Still run the completion audit/summary below rather than
                # unwinding immediately -- this is exactly the situation
                # (errors, an interrupt) where seeing what actually
                # completed is most useful. The exit code is re-raised
                # unchanged once the summary has been printed.
                exit_code = exc.code
            elapsed = time.monotonic() - start_time

            missing, duplicates = audit_completion(args.checkpoint, keystrings)
            if duplicates:
                sample = list(duplicates)[:5]
                print(
                    f"[!] duplicate checkpoint digests detected (data integrity "
                    f"bug -- normal operation never produces these): "
                    f"count={len(duplicates)} sample={sample}"
                )
            counts = classification_counts(args.hits)
            counts_str = ", ".join(f"{k}={v}" for k, v in sorted(counts.items())) or "none"
            print(
                f"[*] summary: fingerprint={fingerprint['candidate_digest']} "
                f"elapsed={elapsed:.1f}s resumed={len(completed):,} "
                f"total={len(keystrings):,} missing={len(missing):,} "
                f"duplicate_digests={len(duplicates):,} classifications: {counts_str}"
            )
            if exit_code is not None:
                raise SystemExit(exit_code)
        finally:
            if bloom:
                bloom.close()
    finally:
        lock_file.close()


def self_test():
    global KNOWN_GSMG_ADDRESSES, private_key_details
    real_known_addresses = KNOWN_GSMG_ADDRESSES
    real_private_key_details = private_key_details
    passwd = b"correct horse battery staple"
    salt = b"01234567"

    # 0) Permanent parity tests for the Phase 91 speed optimizations --
    # promoted from a one-off benchmark script into this suite, per review.
    #
    # 0a) private_key_details (coincurve) vs _reference_private_key_details
    # (cryptography/OpenSSL) must agree exactly. Edge cases (0 and
    # SECP256K1_ORDER and beyond are invalid; 1 and SECP256K1_ORDER-1 are the
    # valid boundary) plus 200 deterministic pseudorandom keys (a SHA-256
    # hash chain, not os.urandom, for reproducibility -- matching this file's
    # established preference, see the FILLER comment below).
    _edge_case_keys = [
        (0).to_bytes(32, "big"),
        SECP256K1_ORDER.to_bytes(32, "big"),
        (SECP256K1_ORDER + 1).to_bytes(32, "big"),
        (1).to_bytes(32, "big"),
        (SECP256K1_ORDER - 1).to_bytes(32, "big"),
    ]
    _chain_block = b"nopad-window-sweep-parity-seed"
    _random_keys = []
    for _ in range(200):
        _chain_block = hashlib.sha256(_chain_block).digest()
        _random_keys.append(_chain_block)
    for _key in _edge_case_keys + _random_keys:
        assert private_key_details(_key) == _reference_private_key_details(_key), _key.hex()

    # 0b) PBKDF2 caching parity: every (kdf_kind, kdf_param, key_len, block)
    # combination actually used by ALL_CBC_VARIANTS/ECB_CIPHER_VARIANTS must
    # produce IDENTICAL (key, iv) output whether derived directly (cache=None)
    # or through a shared cache -- not just the single spot-check the Phase 87
    # benchmark ran, every real variant.
    _pbkdf2_parity_cache = {}
    for _variant in ALL_CBC_VARIANTS:
        _kdf_kind, _kdf_param, _cipher_name, _key_len = _normalize_variant(_variant)
        _block = CIPHER_BLOCK_SIZES[_cipher_name]
        _direct = derive_key_iv(_kdf_kind, _kdf_param, _key_len, _block, salt, passwd)
        _cached = derive_key_iv(
            _kdf_kind, _kdf_param, _key_len, _block, salt, passwd, _pbkdf2_parity_cache,
        )
        assert _direct == _cached, (_kdf_kind, _kdf_param, _key_len, _block)
    for _variant in ECB_CIPHER_VARIANTS:
        _kdf_kind, _kdf_param, _key_len = _variant
        _direct = derive_key_iv(_kdf_kind, _kdf_param, _key_len, 0, salt, passwd)
        _cached = derive_key_iv(
            _kdf_kind, _kdf_param, _key_len, 0, salt, passwd, _pbkdf2_parity_cache,
        )
        assert _direct == _cached, (_kdf_kind, _kdf_param, _key_len, 0)
    # Deterministic 80-byte filler for test bodies -- NOT os.urandom(), which
    # risks an occasional spurious Bloom false positive on unrelated noise
    # (the Bloom filter's ~0.01%-per-lookup false-accept rate applies to any
    # 20-byte hash160, including ones derived from filler that was never
    # meant to test anything) and would make these tests flaky.
    FILLER = bytes(range(1, 81))

    # A key we control, so we can test the "known" classification without the
    # real (unknown) puzzle private key: temporarily treat this key's own
    # compressed address as if it were a "known GSMG address" for the
    # duration of this test only, restored in `finally` below.
    known_key = (1).to_bytes(32, "big")
    known_details = private_key_details(known_key)
    known_address = known_details["compressed"]["address"]
    KNOWN_GSMG_ADDRESSES = {known_address}

    try:
        with tempfile.TemporaryDirectory() as directory:
            bloom_path = Path(directory) / "test.bloom"
            # A DIFFERENT key's hash160 populates the Bloom filter, so "known"
            # (exact address-set match) and "bloom" (Bloom-only) stay distinct.
            bloom_key = (12345).to_bytes(32, "big")
            bloom_details = private_key_details(bloom_key)
            _make_test_bloom(bloom_path, [bytes.fromhex(bloom_details["uncompressed"]["hash160"])])

            with BloomCache(bloom_path) as bloom:
                # 1) known_address_matches / bloom_matches: invalid scalar, known
                # address (and only the specific matching address_type), bloom-only,
                # none.
                assert private_key_details(bytes(32)) is None
                known_key_details = private_key_details(known_key)
                assert known_address_matches(known_key_details, KNOWN_GSMG_ADDRESSES) == ("compressed",)
                assert bloom_matches(known_key_details, bloom) == ()

                bloom_key_details = private_key_details(bloom_key)
                assert known_address_matches(bloom_key_details, KNOWN_GSMG_ADDRESSES) == ()
                assert bloom_matches(bloom_key_details, bloom) == ("uncompressed",)

                other_key = (999999).to_bytes(32, "big")
                other_details = private_key_details(other_key)
                assert known_address_matches(other_details, KNOWN_GSMG_ADDRESSES) == ()
                assert bloom_matches(other_details, bloom) == ()

                # 2) Synthetic positives for every offset x cipher/KDF x address format.
                for offset in WINDOW_OFFSETS:
                    for variant, mode_label in (
                        (("sha256", 32), "cbc"),
                        (("pbkdf2", ("sha256", 10000), "aes", 24), "cbc"),
                        (("legacy", "md5", "aes", 32), "ecb"),
                    ):
                        kdf_kind, kdf_param, cipher_name, key_len = _normalize_variant(variant)
                        block = CIPHER_BLOCK_SIZES[cipher_name]
                        body = bytearray(FILLER)
                        body[offset : offset + WINDOW_SIZE] = known_key
                        body = bytes(body)
                        if mode_label == "cbc":
                            key, iv = derive_key_iv(kdf_kind, kdf_param, key_len, block, salt, passwd)
                            encryptor = Cipher(
                                CIPHER_CLASSES[cipher_name](key), modes.CBC(iv)
                            ).encryptor()
                            ciphertext = encryptor.update(body) + encryptor.finalize()
                            decrypted = raw_cbc_decrypt(cipher_name, key, iv, ciphertext)
                        else:
                            key, _ = derive_key_iv(kdf_kind, kdf_param, key_len, 0, salt, passwd)
                            encryptor = Cipher(CIPHER_CLASSES[cipher_name](key), modes.ECB()).encryptor()
                            ciphertext = encryptor.update(body) + encryptor.finalize()
                            decrypted = raw_ecb_decrypt(cipher_name, key, ciphertext)
                        assert decrypted == body, (offset, variant, mode_label)
                        windows = extract_windows(decrypted)
                        assert windows[offset] == known_key
                        details = private_key_details(windows[offset])
                        assert known_address_matches(details, KNOWN_GSMG_ADDRESSES) == ("compressed",), (
                            offset, variant, mode_label,
                        )
                        assert details["compressed"]["address"] == known_address
                        assert "uncompressed" in details

                # 3) Combo path: neither individual window at offsets (0, 32) is a
                # known/Bloom key, but their scalar sum is.
                key_a = (7).to_bytes(32, "big")
                key_b_int = (int.from_bytes(known_key, "big") - 7) % SECP256K1_ORDER
                key_b = key_b_int.to_bytes(32, "big")
                assert known_address_matches(private_key_details(key_a), KNOWN_GSMG_ADDRESSES) == ()
                assert known_address_matches(private_key_details(key_b), KNOWN_GSMG_ADDRESSES) == ()
                combos = combo_candidates(key_a, key_b)
                assert combos["scalar_sum"] == known_key
                assert known_address_matches(private_key_details(combos["scalar_sum"]), KNOWN_GSMG_ADDRESSES) == (
                    "compressed",
                )

                # 3b) XOR combo path: neither individual window is known, but
                # their bytewise XOR recovers the known key -- covers the
                # newly-added "duality" combo the same way section 3 above
                # already covers scalar_sum.
                xor_key_a = (11).to_bytes(32, "big")
                xor_key_b = bytes(x ^ y for x, y in zip(xor_key_a, known_key))
                assert known_address_matches(private_key_details(xor_key_a), KNOWN_GSMG_ADDRESSES) == ()
                assert known_address_matches(private_key_details(xor_key_b), KNOWN_GSMG_ADDRESSES) == ()
                xor_combos = combo_candidates(xor_key_a, xor_key_b)
                assert xor_combos["xor"] == known_key
                assert known_address_matches(
                    private_key_details(xor_combos["xor"]), KNOWN_GSMG_ADDRESSES
                ) == ("compressed",)

                # 3c) Complete complementary-scalar operation family.
                assert set(combos) == {
                    "scalar_sum",
                    "scalar_diff_ab",
                    "scalar_diff_ba",
                    "scalar_neg_a",
                    "scalar_neg_b",
                    "concat_hash_ab",
                    "concat_hash_ba",
                    "xor",
                }
                diff_a = (8).to_bytes(32, "big")
                diff_b = (7).to_bytes(32, "big")
                diff_combos = combo_candidates(diff_a, diff_b)
                assert diff_combos["scalar_diff_ab"] == known_key
                assert combo_candidates(diff_b, diff_a)["scalar_diff_ba"] == known_key
                negated_known = (SECP256K1_ORDER - 1).to_bytes(32, "big")
                neg_combos = combo_candidates(negated_known, diff_b)
                assert neg_combos["scalar_neg_a"] == known_key

                relation_a = (7).to_bytes(32, "big")
                relation_b = (SECP256K1_ORDER - 7).to_bytes(32, "big")
                relation_hits = pair_relation_hits(relation_a, relation_b)
                assert [hit["source"] for hit in relation_hits] == [
                    "relation:scalar_additive_inverse"
                ]
                complement_a = hashlib.sha256(b"half").digest()
                complement_b = bytes(value ^ 0xff for value in complement_a)
                complement_hits = pair_relation_hits(complement_a, complement_b)
                assert [hit["source"] for hit in complement_hits] == [
                    "relation:bitwise_complement"
                ]

                # 3d) The same 64 bytes may be public X/Y coordinates rather
                # than two private scalars. Both orderings must identify the
                # known synthetic address.
                public = coincurve.PrivateKey(known_key).public_key.format(compressed=False)
                x_bytes, y_bytes = public[1:33], public[33:65]
                xy_body = bytearray(FILLER)
                xy_body[0:32], xy_body[32:64] = x_bytes, y_bytes
                xy_hits = evaluate_body(bytes(xy_body), bloom, KNOWN_GSMG_ADDRESSES)
                assert any(
                    hit["source"] == "public_point:xy"
                    and hit["classification"] == "known_public_point"
                    for hit in xy_hits
                ), xy_hits
                yx_body = bytearray(FILLER)
                yx_body[0:32], yx_body[32:64] = y_bytes, x_bytes
                yx_hits = evaluate_body(bytes(yx_body), bloom, KNOWN_GSMG_ADDRESSES)
                assert any(
                    hit["source"] == "public_point:yx"
                    and hit["classification"] == "known_public_point"
                    for hit in yx_hits
                ), yx_hits

                # 3e) Encoded-key recognition: the known key written out as
                # 64 ASCII hex characters, and as a Base58Check WIF string,
                # both recovered from a body that is otherwise unrelated
                # filler -- a genuine format gap the raw-binary-window-only
                # reading could never catch on its own.
                hex_body = bytearray(FILLER)
                hex_body[16 : 16 + HEX_CANDIDATE_LENGTH] = known_key.hex().encode()
                hex_body = bytes(hex_body)
                hex_candidates = hex_window_candidates(hex_body)
                assert ("hex@16", known_key) in hex_candidates, hex_candidates
                hex_hits = evaluate_body(hex_body, bloom, KNOWN_GSMG_ADDRESSES)
                known_hex_hits = [h for h in hex_hits if h["source"] == "hex@16"]
                assert len(known_hex_hits) == 1, hex_hits
                assert known_hex_hits[0]["classification"] == "known"

                known_wif_compressed = known_details["compressed"]["wif"]
                wif_offset = 10
                wif_body = bytearray(FILLER)
                wif_body[wif_offset : wif_offset + len(known_wif_compressed)] = (
                    known_wif_compressed.encode()
                )
                wif_body = bytes(wif_body)
                wif_candidates = wif_window_candidates(wif_body)
                assert (f"wif@{wif_offset}:compressed", known_key) in wif_candidates, wif_candidates
                wif_hits = evaluate_body(wif_body, bloom, KNOWN_GSMG_ADDRESSES)
                known_wif_hits = [
                    h for h in wif_hits if h["source"] == f"wif@{wif_offset}:compressed"
                ]
                assert len(known_wif_hits) == 1, wif_hits
                assert known_wif_hits[0]["classification"] == "known"

                # 3d) WIF compression-type restriction: a compressed WIF
                # must only ever be checked against the compressed address
                # of that same scalar, never the uncompressed one (and vice
                # versa) -- a real bug found on review: a compressed WIF was
                # incorrectly matching a known UNCOMPRESSED address of the
                # same underlying key and being reported as a "known" hit,
                # even though no real wallet holding that literal WIF text
                # would ever derive that address. Reproduced directly before
                # this fix (a standalone repro, not just this suite).
                known_uncompressed_address = known_details["uncompressed"]["address"]
                KNOWN_GSMG_ADDRESSES = {known_uncompressed_address}
                try:
                    negative_hits = evaluate_body(wif_body, bloom, KNOWN_GSMG_ADDRESSES)
                    negative_wif_hits = [
                        h for h in negative_hits if h["source"] == f"wif@{wif_offset}:compressed"
                    ]
                    assert negative_wif_hits == [], (
                        "a compressed WIF incorrectly matched the uncompressed "
                        "address of the same key", negative_wif_hits,
                    )
                finally:
                    KNOWN_GSMG_ADDRESSES = {known_address}

                known_wif_uncompressed = known_details["uncompressed"]["wif"]
                wif_u_offset = 10
                wif_u_body = bytearray(FILLER)
                wif_u_body[wif_u_offset : wif_u_offset + len(known_wif_uncompressed)] = (
                    known_wif_uncompressed.encode()
                )
                wif_u_body = bytes(wif_u_body)
                wif_u_candidates = wif_window_candidates(wif_u_body)
                assert (f"wif@{wif_u_offset}:uncompressed", known_key) in wif_u_candidates, wif_u_candidates
                # Positive case needs the UNCOMPRESSED address known -- the
                # module-level KNOWN_GSMG_ADDRESSES is the compressed one.
                KNOWN_GSMG_ADDRESSES = {known_uncompressed_address}
                try:
                    wif_u_hits = evaluate_body(wif_u_body, bloom, KNOWN_GSMG_ADDRESSES)
                    known_wif_u_hits = [
                        h for h in wif_u_hits if h["source"] == f"wif@{wif_u_offset}:uncompressed"
                    ]
                    assert len(known_wif_u_hits) == 1, wif_u_hits
                    assert known_wif_u_hits[0]["classification"] == "known"
                    assert known_wif_u_hits[0]["matched_address_types"] == ("uncompressed",)
                finally:
                    KNOWN_GSMG_ADDRESSES = {known_address}

                # Mirror negative: an uncompressed WIF must not match a
                # known COMPRESSED address of the same key.
                KNOWN_GSMG_ADDRESSES = {known_address}  # known_address is the compressed one
                negative_hits_u = evaluate_body(wif_u_body, bloom, KNOWN_GSMG_ADDRESSES)
                negative_wif_u_hits = [
                    h for h in negative_hits_u if h["source"] == f"wif@{wif_u_offset}:uncompressed"
                ]
                assert negative_wif_u_hits == [], (
                    "an uncompressed WIF incorrectly matched the compressed "
                    "address of the same key", negative_wif_u_hits,
                )

                # 4) End-to-end via check_decrypt + record_hit, using temp files.
                hits_path = Path(directory) / "hits.jsonl"
                queue_path = Path(directory) / "queue.jsonl"
                body = bytearray(FILLER)
                body[0:32] = key_a
                body[32:64] = key_b
                check_decrypt(
                    bytes(body), "SYNTH", "cbc", "sha256/256", "cand", "form", "keystr",
                    hits_path, queue_path, bloom,
                )
                hit_lines = hits_path.read_text().splitlines()
                assert len(hit_lines) == 1, hit_lines
                hit_record = json.loads(hit_lines[0])
                assert hit_record["classification"] == "known"
                assert hit_record["source"] == "combo:scalar_sum"
                assert hit_record["matched_address_types"] == ["compressed"]
                assert hits_path.stat().st_mode & 0o777 == 0o600

                # A Bloom-only hit (not a known address) must reach the queue file
                # for mandatory verification, AND must queue only the specific
                # address_type that actually matched Bloom (bloom_key's hash160
                # was built from its uncompressed form only).
                body2 = bytearray(FILLER)
                body2[0:32] = bloom_key
                check_decrypt(
                    bytes(body2), "SYNTH", "cbc", "sha256/256", "cand", "form", "keystr2",
                    hits_path, queue_path, bloom,
                )
                queue_records = [json.loads(line) for line in queue_path.read_text().splitlines()]
                assert len(queue_records) == 1, queue_records
                assert queue_records[0]["address_type"] == "uncompressed", queue_records
                assert queue_records[0]["address"] == bloom_key_details["uncompressed"]["address"]
                queue_text = queue_path.read_text()
                assert "private_key_hex" not in queue_text and "passphrase" not in queue_text

                # 4b) Vanity-prefix classification (strong/weak tiers):
                # independent of known/Bloom, and both tiers must reach the
                # API queue since neither is conclusive on its own (mirrors
                # "bloom" handling above). There is no way to derive a
                # *real* key whose address genuinely starts with "1GSMG..."
                # without actual vanity mining, so this temporarily patches
                # private_key_details (module-global shadowing, restored
                # below and again in the shared `finally` as a safety net)
                # to graft synthetic vanity-looking addresses onto three
                # specific test keys' real derivations -- exercising the
                # classification/queuing logic itself, not a mining search.
                vanity_key_strong = (777).to_bytes(32, "big")
                vanity_key_weak = (778).to_bytes(32, "big")
                vanity_key_none = (779).to_bytes(32, "big")
                _vanity_test_addresses = {
                    vanity_key_strong: "1GSMG1TestOnlyFakeAddressXXXXXXXXX",
                    vanity_key_weak: "1GSMG7TestOnlyFakeAddressXXXXXXXXX",
                    vanity_key_none: "1XXXXXTestOnlyFakeAddressXXXXXXXXX",
                }

                def _vanity_patched_details(private_key, _real=real_private_key_details):
                    details = _real(private_key)
                    if details is not None and private_key in _vanity_test_addresses:
                        details = {k: dict(v) for k, v in details.items()}
                        details["compressed"]["address"] = _vanity_test_addresses[private_key]
                    return details

                private_key_details = _vanity_patched_details
                strong_details = private_key_details(vanity_key_strong)
                weak_details = private_key_details(vanity_key_weak)
                none_details = private_key_details(vanity_key_none)
                assert vanity_matches(strong_details) == {"compressed": "strong"}
                assert vanity_matches(weak_details) == {"compressed": "weak"}
                assert vanity_matches(none_details) == {}
                assert known_address_matches(strong_details, KNOWN_GSMG_ADDRESSES) == ()
                assert bloom_matches(strong_details, bloom) == ()

                body_vanity_strong = bytearray(FILLER)
                body_vanity_strong[0:32] = vanity_key_strong
                strong_hits = evaluate_body(bytes(body_vanity_strong), bloom, KNOWN_GSMG_ADDRESSES)
                assert len(strong_hits) == 1, strong_hits
                assert strong_hits[0]["classification"] == "vanity_strong"
                assert strong_hits[0]["matched_address_types"] == ("compressed",)

                body_vanity_weak = bytearray(FILLER)
                body_vanity_weak[0:32] = vanity_key_weak
                weak_hits = evaluate_body(bytes(body_vanity_weak), bloom, KNOWN_GSMG_ADDRESSES)
                assert len(weak_hits) == 1, weak_hits
                assert weak_hits[0]["classification"] == "vanity_weak"
                assert weak_hits[0]["matched_address_types"] == ("compressed",)

                body_vanity_none = bytearray(FILLER)
                body_vanity_none[0:32] = vanity_key_none
                none_hits = evaluate_body(bytes(body_vanity_none), bloom, KNOWN_GSMG_ADDRESSES)
                assert none_hits == [], none_hits

                hits_path4 = Path(directory) / "hits4.jsonl"
                queue_path4 = Path(directory) / "queue4.jsonl"
                check_decrypt(
                    bytes(body_vanity_strong), "SYNTH", "cbc", "sha256/256", "cand", "form",
                    "keystr4", hits_path4, queue_path4, bloom,
                )
                vanity_hit_records = [
                    json.loads(line) for line in hits_path4.read_text().splitlines()
                ]
                assert len(vanity_hit_records) == 1, vanity_hit_records
                assert vanity_hit_records[0]["classification"] == "vanity_strong"
                vanity_queue_records = [
                    json.loads(line) for line in queue_path4.read_text().splitlines()
                ]
                assert len(vanity_queue_records) == 1, vanity_queue_records
                assert vanity_queue_records[0]["address_type"] == "compressed"
                assert vanity_queue_records[0]["address"] == "1GSMG1TestOnlyFakeAddressXXXXXXXXX"
                private_key_details = real_private_key_details

                # 5) Regression test for the reported bug: window@0 is a
                # simulated Bloom hit -- bloom_key's hash160 was deliberately
                # inserted into the test Bloom filter above, standing in for
                # whatever key produces a real algorithmic false-positive
                # collision (the real Bloom filter's own false-positive rate
                # is a separate, much rarer, unforced event -- this test
                # exercises the code path, not that probability). Meanwhile
                # the clue-supported combo of two OTHER windows is the actual
                # known key. The provisional Bloom match on window@0 must NOT
                # suppress finding the combo hit -- both must be recorded,
                # and via the known-address path found in pass 1, not
                # swallowed by an early return.
                hits_path3 = Path(directory) / "hits3.jsonl"
                queue_path3 = Path(directory) / "queue3.jsonl"
                # window@32 must pair with bloom_key (not key_a/key_b, which pair
                # with each other) so their scalar sum equals known_key exactly.
                paired_with_bloom_key_int = (
                    int.from_bytes(known_key, "big") - int.from_bytes(bloom_key, "big")
                ) % SECP256K1_ORDER
                paired_with_bloom_key = paired_with_bloom_key_int.to_bytes(32, "big")
                assert known_address_matches(private_key_details(paired_with_bloom_key), KNOWN_GSMG_ADDRESSES) == ()
                assert bloom_matches(private_key_details(paired_with_bloom_key), bloom) == ()
                body3 = bytearray(FILLER)
                body3[0:32] = bloom_key  # window@0: Bloom-flagged, not known.
                body3[32:64] = paired_with_bloom_key  # window@32: completes the combo.
                combo_check = combo_candidates(bloom_key, paired_with_bloom_key)
                assert combo_check["scalar_sum"] == known_key
                check_decrypt(
                    bytes(body3), "SYNTH", "cbc", "sha256/256", "cand", "form", "keystr3",
                    hits_path3, queue_path3, bloom,
                )
                hit_lines3 = hits_path3.read_text().splitlines()
                hit_records3 = [json.loads(line) for line in hit_lines3]
                combo_hits = [r for r in hit_records3 if r["source"] == "combo:scalar_sum"]
                assert len(combo_hits) == 1, hit_records3
                assert combo_hits[0]["classification"] == "known", hit_records3
                assert combo_hits[0]["private_key_hex"] == known_key.hex()
                # Because a known-address match was found in pass 1, the Bloom
                # pass never runs at all -- window@0's Bloom-positive status is
                # correctly never recorded (checking known addresses across all
                # 7 candidates always takes priority over any Bloom lookup).
                window_hits = [r for r in hit_records3 if r["source"] == "window@0"]
                assert window_hits == [], hit_records3

                # 6) Negative control: a random 80-byte body with no known-address
                # key anywhere (Bloom disabled, to keep this deterministic) produces
                # no hit record.
                hits_path2 = Path(directory) / "hits2.jsonl"
                queue_path2 = Path(directory) / "queue2.jsonl"
                check_decrypt(
                    FILLER, "SYNTH", "cbc", "sha256/256", "cand", "form",
                    "wrong-keystr", hits_path2, queue_path2, None,
                )
                assert not hits_path2.exists()

            # 7) Checkpoint fingerprint/resume guard, mirroring the other
            # drivers -- and, unlike them, covering every dependency this
            # driver's behavior actually pulls in: not just this file and
            # cb_common.py, but binary_key_material_backfill.py (source of
            # private_key_details/append_jsonl/etc.), aes_key_wrap_sweep.py
            # (source of ALL_CBC_VARIANTS), the known-address set, and
            # whether a Bloom cache is active at all.
            checkpoint_path = Path(directory) / "checkpoint.jsonl"
            candidates = ["alpha"]
            keystrings = normalized_keystrings(candidates)
            fp = run_fingerprint(candidates, keystrings, None)
            ensure_checkpoint_header(checkpoint_path, fp)
            assert load_checkpoint(checkpoint_path, fp) == set()
            for changed_field in (
                "oracle_sha256",
                "binary_key_material_sha256",
                "aes_key_wrap_sha256",
                "known_addresses_sha256",
                "bloom_enabled",
                "coincurve",
            ):
                changed = {**fp, changed_field: "changed"}
                try:
                    load_checkpoint(checkpoint_path, changed)
                except ValueError:
                    pass
                else:
                    raise AssertionError(
                        f"mismatched {changed_field} fingerprint was accepted"
                    )

            # 8) Crash-tolerant checkpoint loading: exactly one truncated
            # final line (simulating a hard kill mid-write) is quarantined,
            # not fatal; the same kind of corruption anywhere earlier in
            # the file still raises -- it is never expected there and must
            # not be silently swallowed.
            truncated_checkpoint = Path(directory) / "checkpoint_truncated.jsonl"
            ensure_checkpoint_header(truncated_checkpoint, fp)
            good_digest = "a" * 64
            append_jsonl(truncated_checkpoint, {"index": 0, "keystr_sha256": good_digest})
            with open(truncated_checkpoint, "a") as f:
                f.write('{"index": 1, "keystr_sha256": "trun')  # deliberately cut off
            assert load_checkpoint(truncated_checkpoint, fp) == {good_digest}, (
                "a truncated final line should be quarantined, not fatal, and "
                "must not affect any earlier valid entry"
            )

            corrupt_middle_checkpoint = Path(directory) / "checkpoint_corrupt_middle.jsonl"
            ensure_checkpoint_header(corrupt_middle_checkpoint, fp)
            with open(corrupt_middle_checkpoint, "a") as f:
                f.write('{"index": 0, "keystr_sha256": "broken\n')  # malformed, NOT the final line
            append_jsonl(corrupt_middle_checkpoint, {"index": 1, "keystr_sha256": "b" * 64})
            try:
                load_checkpoint(corrupt_middle_checkpoint, fp)
                raise AssertionError("corruption in a non-final line was silently tolerated")
            except ValueError:
                pass

            # 9) Single-instance run locking: a second acquire against the
            # same checkpoint path while the first is still held must be
            # refused (SystemExit, not a hang or silent double-run); once
            # released, a subsequent acquire must succeed normally.
            lock_target = Path(directory) / "lock_target.jsonl"
            lock1 = acquire_run_lock(lock_target)
            try:
                try:
                    acquire_run_lock(lock_target)
                    raise AssertionError("acquire_run_lock allowed two concurrent locks")
                except SystemExit:
                    pass
            finally:
                lock1.close()
            lock2 = acquire_run_lock(lock_target)  # must succeed now that lock1 released
            lock2.close()

            # 9b) Multi-path locking: two runs with DIFFERENT checkpoint
            # paths but a SHARED hits path must still conflict -- locking
            # only the checkpoint path would miss exactly this collision.
            checkpoint_a = Path(directory) / "checkpoint_a.jsonl"
            checkpoint_b = Path(directory) / "checkpoint_b.jsonl"
            shared_hits = Path(directory) / "shared_hits.jsonl"
            lock_a = acquire_run_lock(checkpoint_a, shared_hits)
            try:
                try:
                    acquire_run_lock(checkpoint_b, shared_hits)
                    raise AssertionError(
                        "acquire_run_lock allowed two concurrent locks sharing "
                        "only a hits path, with different checkpoint paths"
                    )
                except SystemExit:
                    pass
                # A DIFFERENT hits path (no overlap at all) must succeed even
                # while lock_a is still held.
                lock_c = acquire_run_lock(checkpoint_b, Path(directory) / "unrelated_hits.jsonl")
                lock_c.close()
            finally:
                lock_a.close()
            # Duplicate paths in one call must not conflict with themselves.
            lock_dup = acquire_run_lock(checkpoint_a, checkpoint_a, shared_hits)
            lock_dup.close()

            # 10) Completion audit + classification counts: a duplicate
            # digest is detected (not silently collapsed by a set), a
            # missing one is reported, and classification tallies match a
            # small synthetic hits file exactly.
            audit_checkpoint = Path(directory) / "checkpoint_audit.jsonl"
            audit_keystrings = [("c0", "f", "k0"), ("c1", "f", "k1"), ("c2", "f", "k2")]
            audit_fp = run_fingerprint(["c0", "c1", "c2"], audit_keystrings, None)
            ensure_checkpoint_header(audit_checkpoint, audit_fp)
            digest0 = hashlib.sha256(b"k0").hexdigest()
            digest1 = hashlib.sha256(b"k1").hexdigest()
            digest2 = hashlib.sha256(b"k2").hexdigest()
            append_jsonl(audit_checkpoint, {"index": 0, "keystr_sha256": digest0})
            append_jsonl(audit_checkpoint, {"index": 0, "keystr_sha256": digest0})  # duplicate
            missing, duplicates = audit_completion(audit_checkpoint, audit_keystrings)
            assert missing == {digest1, digest2}, missing
            assert duplicates == {digest0: 2}, duplicates

            counts_hits_path = Path(directory) / "counts_hits.jsonl"
            append_jsonl(counts_hits_path, {"classification": "known"}, sensitive=True)
            append_jsonl(counts_hits_path, {"classification": "bloom"}, sensitive=True)
            append_jsonl(counts_hits_path, {"classification": "bloom"}, sensitive=True)
            append_jsonl(counts_hits_path, {"classification": "vanity_strong"}, sensitive=True)
            counts = classification_counts(counts_hits_path)
            assert counts == {"known": 1, "bloom": 2, "vanity_strong": 1}, counts
            assert classification_counts(Path(directory) / "does_not_exist.jsonl") == {}

            # 11) Vanity queue relabeling: only vanity-classified entries
            # currently showing bloom_false_positive are rewritten to
            # unfunded -- a real Bloom false positive, a vanity entry that
            # was actually confirmed funded, and one already relabeled must
            # all be left alone.
            relabel_queue = Path(directory) / "relabel_queue.jsonl"
            append_jsonl(relabel_queue, {
                "queue_id": "q_vanity_unfunded", "classification": "vanity_strong",
                "status": "bloom_false_positive", "address": "1vanity_unfunded",
            })
            append_jsonl(relabel_queue, {
                "queue_id": "q_vanity_weak_unfunded", "classification": "vanity_weak",
                "status": "bloom_false_positive", "address": "1vanity_weak_unfunded",
            })
            append_jsonl(relabel_queue, {
                "queue_id": "q_bloom_fp", "classification": "bloom",
                "status": "bloom_false_positive", "address": "1bloom_fp",
            })
            append_jsonl(relabel_queue, {
                "queue_id": "q_vanity_funded", "classification": "vanity_strong",
                "status": "confirmed_funded", "address": "1vanity_funded",
            })
            relabeled_count = relabel_vanity_verifications(relabel_queue)
            assert relabeled_count == 2, relabeled_count
            final_state = binary_key_material_backfill.latest_queue_state(relabel_queue)
            assert final_state["q_vanity_unfunded"]["status"] == "unfunded"
            assert final_state["q_vanity_weak_unfunded"]["status"] == "unfunded"
            assert final_state["q_bloom_fp"]["status"] == "bloom_false_positive", (
                "a real Bloom false positive must not be relabeled"
            )
            assert final_state["q_vanity_funded"]["status"] == "confirmed_funded", (
                "a vanity entry that was actually confirmed funded must not be touched"
            )
            # Running it again must be a no-op (the entries are now
            # "unfunded", not "bloom_false_positive").
            assert relabel_vanity_verifications(relabel_queue) == 0
    finally:
        KNOWN_GSMG_ADDRESSES = real_known_addresses
        private_key_details = real_private_key_details

    _self_test_multiprocessing()

    print(
        "[*] self-test OK: coincurve/reference private_key_details parity "
        "(edge cases + 200 keys), PBKDF2 cache/direct parity (every real "
        "CBC/ECB variant), window extraction, known/Bloom/vanity(strong+weak)/"
        "none classification (with specific matched address_type), synthetic "
        "positives at all 4 offsets x 3 cipher/KDF variants x both address "
        "formats, clue-supported combo recovery (scalar_sum + xor), hex/WIF "
        "encoded-key recognition, mandatory-queue routing scoped to only the "
        "matched address form (bloom and both vanity tiers alike), a "
        "simulated Bloom hit on one window never suppressing a real "
        "known-address combo hit, sensitive-file mode, negative control, "
        "checkpoint source guard over every real dependency (driver, "
        "cb_common, binary_key_material_backfill, aes_key_wrap_sweep, "
        "known-address set, bloom enabled/disabled, coincurve version+backend), "
        "crash-tolerant checkpoint loading (truncated-final-line quarantine "
        "vs earlier corruption still raising), single-instance run locking "
        "(single-path and multi-path/shared-artifact collisions alike), "
        "completion audit (duplicate/missing digest detection), "
        "classification-count tallying, WIF compression-type restriction "
        "(a compressed/uncompressed WIF only matches its own address_type), "
        "and vanity queue relabeling (bloom_false_positive -> unfunded, "
        "real Bloom false positives and confirmed-funded entries left alone)"
    )


def _self_test_multiprocessing():
    """Phase 92 multiprocessing coverage. Every parallel-path test here runs
    under `spawn` for real (via a real ProcessPoolExecutor) -- production
    never forces a start method other than spawn either (see WorkerConfig),
    so there is no separate "does this survive spawn" question: spawn is
    the only mode that exists."""
    known_key = (1).to_bytes(32, "big")
    known_details = private_key_details(known_key)
    known_address = known_details["compressed"]["address"]
    bloom_key = (12345).to_bytes(32, "big")
    bloom_details = private_key_details(bloom_key)

    with tempfile.TemporaryDirectory() as directory:
        # 1) _apply_chunk_results: normal case, per-item error isolation,
        # and structural result-set validation (missing/duplicate/extra
        # entries), all without needing a real pool.
        original_chunk = [
            (0, "candA", "form", "keystrA", "digestA"),
            (1, "candB", "form", "keystrB", "digestB"),
        ]

        checkpoint_ok = Path(directory) / "checkpoint_ok.jsonl"
        completed_n, errors_n = _apply_chunk_results(
            original_chunk,
            [(0, "digestA", [], None), (1, "digestB", [], None)],
            Path(directory) / "hits_unused.jsonl", Path(directory) / "queue_unused.jsonl",
            checkpoint_ok, None, set(), set(),
        )
        assert (completed_n, errors_n) == (2, 0), (completed_n, errors_n)
        recorded = {json.loads(l)["keystr_sha256"] for l in checkpoint_ok.read_text().splitlines()}
        assert recorded == {"digestA", "digestB"}

        checkpoint_partial = Path(directory) / "checkpoint_partial.jsonl"
        completed_n, errors_n = _apply_chunk_results(
            original_chunk,
            [(0, "digestA", [], None), (1, "digestB", None, "ValueError")],
            Path(directory) / "hits_unused.jsonl", Path(directory) / "queue_unused.jsonl",
            checkpoint_partial, None, set(), set(),
        )
        assert (completed_n, errors_n) == (1, 1), (completed_n, errors_n)
        recorded = {json.loads(l)["keystr_sha256"] for l in checkpoint_partial.read_text().splitlines()}
        assert recorded == {"digestA"}, "sibling of a failed keystring must still be checkpointed"

        for label, malformed in (
            ("missing", [(0, "digestA", [], None)]),
            ("duplicate", [(0, "digestA", [], None), (0, "digestA", [], None)]),
            ("extra", [(0, "digestA", [], None), (1, "digestB", [], None), (2, "digestC", [], None)]),
        ):
            checkpoint_bad = Path(directory) / f"checkpoint_{label}.jsonl"
            completed_n, errors_n = _apply_chunk_results(
                original_chunk, malformed,
                Path(directory) / "hits_unused.jsonl", Path(directory) / "queue_unused.jsonl",
                checkpoint_bad, None, set(), set(),
            )
            assert (completed_n, errors_n) == (0, 2), (label, completed_n, errors_n)
            assert not checkpoint_bad.exists(), f"{label}: malformed chunk must not be checkpointed at all"

        # 2) Idempotent writes: a hit already recorded is not duplicated; a
        # queue entry independently missing (simulating a crash between the
        # two writes) still gets written on a rerun.
        hits_path = Path(directory) / "idem_hits.jsonl"
        queue_path = Path(directory) / "idem_queue.jsonl"
        record_hit(
            hits_path, queue_path, "cand", "form", "keystr", "SALPH", "cbc", "sha256/256",
            "window@0", known_key, "known", known_details, ("compressed",), None,
        )
        assert len(hits_path.read_text().splitlines()) == 1
        seen_hit_ids, seen_queue_ids = load_seen_ids(hits_path, queue_path)
        assert len(seen_hit_ids) == 1
        record_hit(
            hits_path, queue_path, "cand", "form", "keystr", "SALPH", "cbc", "sha256/256",
            "window@0", known_key, "known", known_details, ("compressed",), None,
            seen_hit_ids, seen_queue_ids,
        )
        assert len(hits_path.read_text().splitlines()) == 1, "duplicate hit was written on rerun"

        hits_path2 = Path(directory) / "idem_hits2.jsonl"
        queue_path2 = Path(directory) / "idem_queue2.jsonl"
        record_hit(
            hits_path2, queue_path2, "cand", "form", "keystr", "SALPH", "cbc", "sha256/256",
            "window@0", bloom_key, "bloom", bloom_details, ("uncompressed",), None,
        )
        assert len(hits_path2.read_text().splitlines()) == 1
        assert len(queue_path2.read_text().splitlines()) == 1
        queue_path2.write_text("")  # simulate a crash: hit written, queue entry lost
        seen_hit_ids2, seen_queue_ids2 = load_seen_ids(hits_path2, queue_path2)
        assert len(seen_hit_ids2) == 1 and len(seen_queue_ids2) == 0
        record_hit(
            hits_path2, queue_path2, "cand", "form", "keystr", "SALPH", "cbc", "sha256/256",
            "window@0", bloom_key, "bloom", bloom_details, ("uncompressed",), None,
            seen_hit_ids2, seen_queue_ids2,
        )
        assert len(hits_path2.read_text().splitlines()) == 1, "hit was duplicated on rerun"
        assert len(queue_path2.read_text().splitlines()) == 1, "missing queue entry was not restored"

        # 3) Sequential-vs-parallel parity, via a REAL spawned worker
        # process: a synthetic candidate/blob engineered so a known key
        # appears at window@0, computed once directly (sequential
        # reference) and once through an actual ProcessPoolExecutor running
        # _process_chunk under `spawn`. Compares full hit dicts, not just
        # counts -- including the coincurve-derived address itself.
        parity_salt = b"parity01"
        parity_passwd = "parity-test-passphrase"
        filler = bytes(range(1, 81))
        body = bytearray(filler)
        body[0:32] = known_key
        key, iv = derive_key_iv("legacy", "sha256", 32, 16, parity_salt, parity_passwd.encode())
        encryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
        parity_ciphertext = encryptor.update(bytes(body)) + encryptor.finalize()

        parity_known_addresses = frozenset({known_address})
        parity_target_blobs_tuple = (("PARITYTEST", parity_salt, parity_ciphertext),)
        parity_cbc_variants = (("sha256", 32),)

        sequential_result = evaluate_keystring(
            parity_passwd, None, parity_known_addresses,
            {"PARITYTEST": (parity_salt, parity_ciphertext)}, parity_cbc_variants, (),
        )
        assert len(sequential_result) == 1, sequential_result
        assert sequential_result[0][3]["classification"] == "known"

        parity_config = WorkerConfig(
            bloom_cache_path=None, bloom_identity=None,
            known_addresses=parity_known_addresses, target_blobs=parity_target_blobs_tuple,
            cbc_variants=parity_cbc_variants, ecb_variants=(),
        )
        spawn_ctx = multiprocessing.get_context("spawn")
        with ProcessPoolExecutor(
            max_workers=1, mp_context=spawn_ctx,
            initializer=_worker_init, initargs=(parity_config,),
        ) as executor:
            test_chunk = [(0, "cand", "form", parity_passwd, "digest0")]
            fut = executor.submit(_process_chunk, test_chunk)
            worker_results = fut.result()
        assert len(worker_results) == 1, worker_results
        _, _, worker_hits, worker_error = worker_results[0]
        assert worker_error is None, worker_error
        assert worker_hits == sequential_result, (
            "worker-computed result (under spawn) must match the sequential "
            "reference exactly, including the coincurve-derived address"
        )

        # 4) Whole-future-failure: a function that raises before returning
        # anything at all -- _handle_future_result must treat this as an
        # ordinary (if unexpected) failure, log every digest, and return
        # None rather than raising or crashing the dispatch loop.
        with ProcessPoolExecutor(max_workers=1, mp_context=spawn_ctx) as executor:
            fail_chunk = [(0, "c", "f", "k", "digestFail")]
            fut = executor.submit(_process_chunk_test_always_fail, fail_chunk)
            wait([fut])
            result = _handle_future_result(fut, fail_chunk)
            assert result is None, "whole-future failure must return None, not raise"

        # 5) Broken pool: an initializer that always fails must surface as
        # BrokenProcessPool -- re-raised by _handle_future_result, not
        # swallowed as an ordinary per-chunk failure (the pool itself is no
        # longer usable, a categorically different situation).
        with ProcessPoolExecutor(
            max_workers=1, mp_context=spawn_ctx, initializer=_worker_init_test_always_fail,
            initargs=(None,),
        ) as executor:
            broken_chunk = [(0, "c", "f", "k", "digestBroken")]
            fut = executor.submit(_process_chunk, broken_chunk)
            try:
                _handle_future_result(fut, broken_chunk)
                raise AssertionError("expected BrokenProcessPool")
            except BrokenProcessPool:
                pass

        # 6) Bloom-identity mismatch: a real worker whose WorkerConfig
        # claims a Bloom identity that doesn't match the file it actually
        # points to (simulating the file having changed between parent-side
        # fingerprinting and this worker starting up) must refuse to
        # proceed -- surfacing as a broken pool, not a silent continuation
        # with a mismatched cache mapped.
        bloom_path = Path(directory) / "identity_test.bloom"
        _make_test_bloom(bloom_path, [bytes.fromhex(bloom_details["uncompressed"]["hash160"])])
        with BloomCache(bloom_path) as bc:
            real_identity = bc.identity
        fake_identity = {**real_identity, "size": real_identity["size"] + 1}
        mismatched_config = WorkerConfig(
            bloom_cache_path=str(bloom_path), bloom_identity=fake_identity,
            known_addresses=frozenset(), target_blobs=(), cbc_variants=(), ecb_variants=(),
        )
        with ProcessPoolExecutor(
            max_workers=1, mp_context=spawn_ctx, initializer=_worker_init,
            initargs=(mismatched_config,),
        ) as executor:
            id_chunk = [(0, "c", "f", "k", "digestIdentity")]
            fut = executor.submit(_process_chunk, id_chunk)
            try:
                _handle_future_result(fut, id_chunk)
                raise AssertionError("expected BrokenProcessPool from bloom identity mismatch")
            except BrokenProcessPool:
                pass

        # 7) Cancellation vs. failure: a future successfully cancelled via
        # KeyboardInterrupt handling must never be logged/counted as an
        # error; a genuine, already-running future must be drained and
        # processed through the normal writer path, not discarded. A
        # single-worker pool guarantees the second submission stays queued
        # (unstarted) until the first finishes, so cancel() is deterministic
        # here, not a race: `_process_chunk_test_slow` occupies the only
        # worker for 0.5s, comfortably longer than the near-instant time
        # between submitting the second chunk and attempting to cancel it.
        checkpoint_interrupt = Path(directory) / "checkpoint_interrupt.jsonl"
        with ProcessPoolExecutor(max_workers=1, mp_context=spawn_ctx) as executor:
            running_chunk = [(0, "c", "f", "k", "digestRunning")]
            queued_chunk = [(1, "c", "f", "k", "digestQueued")]
            # A plain `spawn_ctx.Event()` cannot be passed through
            # `submit()` -- multiprocessing.synchronize objects can only be
            # shared via inheritance (fork), not via the ordinary pickling
            # path ProcessPoolExecutor uses to hand arguments to an
            # already-spawned worker (confirmed directly: raises
            # "Condition objects should only be shared between processes
            # through inheritance"). A Manager-backed Event is a proxy
            # object designed for exactly this.
            started_event = multiprocessing.Manager().Event()
            running_fut = executor.submit(_process_chunk_test_slow, running_chunk, started_event)
            # Block until the running task is GENUINELY executing (not a
            # guessed delay -- spawn worker startup time isn't fast or
            # consistent enough to assume any fixed sleep is long enough;
            # an earlier version of this test used a fixed sleep and was
            # observed to flake, with the pool racing ahead and starting
            # both chunks before cancellation was attempted).
            assert started_event.wait(timeout=10), "running task never started"
            queued_fut = executor.submit(_process_chunk_test_slow, queued_chunk, started_event)
            future_to_chunk = {running_fut: running_chunk, queued_fut: queued_chunk}
            pending = {running_fut, queued_fut}
            completed_n, errors_n = _drain_interrupted(
                pending, future_to_chunk,
                Path(directory) / "hits_unused.jsonl", Path(directory) / "queue_unused.jsonl",
                checkpoint_interrupt, None, set(), set(),
            )
            assert errors_n == 0, (completed_n, errors_n)
            assert completed_n == 1, (completed_n, errors_n)
            recorded = {
                json.loads(l)["keystr_sha256"]
                for l in checkpoint_interrupt.read_text().splitlines()
            }
            assert recorded == {"digestRunning"}, (
                "cancelled (never-started) chunk must not be checkpointed; "
                f"got {recorded}"
            )

        # 8) Full dispatch-loop integration test: calls the REAL
        # _sweep_parallel (not just its extracted helpers in isolation --
        # this is exactly the level at which a real review caught a missing
        # `submit_next()` replenishment bug that unit tests of the helpers
        # alone could not: an earlier version only replenished the
        # in-flight window after a success, silently shrinking it on every
        # ordinary failure and, given enough of them, ending the dispatch
        # loop early with chunks still undispatched). Many small chunks
        # (chunk_size=3) force several wait()/while-pending rounds; three
        # in four chunks deliberately fail via _process_chunk_test_
        # intermittent -- a low success ratio is required, not just handy
        # for a bigger failure count, see the assertion below.
        #
        # n_total is deliberately large enough that the number of chunks
        # EXCEEDS max_in_flight (workers*4 = 16 here) -- with fewer chunks
        # than that, every chunk gets dispatched in the initial priming
        # loop before any results come back, and the replenishment path
        # inside the main dispatch loop never runs at all, making the test
        # unable to catch the exact bug it exists to catch. Confirmed by
        # deliberately reintroducing the bug in a scratch copy and
        # re-running this test against it: with n_total=40 (14 chunks,
        # under max_in_flight=16) it passed even with the bug present; with
        # n_total=90 (30 chunks, over max_in_flight) it correctly failed.
        n_total = 90
        chunk_size_test = 3
        workers_test = 4
        # Poison whole CHUNKS (aligned to chunk_size_test), not scattered
        # individual items -- _process_chunk_test_intermittent raises for
        # the entire chunk if it contains a "POISON" item, so every item in
        # a poisoned chunk must be "POISON" together for this to actually
        # simulate one whole-future failure per poisoned chunk.
        #
        # The success ratio (1 in 4 chunks) is deliberately low enough that
        # successful_chunks < remaining_after_priming -- under the buggy
        # version (replenishment skipped after an ordinary failure), the
        # total number of chunks EVER dispatched is bounded by
        # max_in_flight + successful_chunks regardless of completion
        # order, since only a success ever triggers another submit_next().
        # With a higher success ratio there are enough successes to
        # "accidentally" pull in every remaining chunk anyway, masking the
        # bug entirely -- confirmed the hard way: an earlier version of
        # this test used a 2-in-3 success ratio, which passed even with the
        # bug reintroduced in a scratch copy, for exactly this reason.
        keystrings_test = []
        for i in range(n_total):
            chunk_index = i // chunk_size_test
            keystr = f"keystr{i}" if chunk_index % 4 == 0 else "POISON"
            keystrings_test.append((f"cand{i}", "form", keystr))
        total_chunks = -(-n_total // chunk_size_test)  # ceil division
        successful_chunks = len(range(0, total_chunks, 4))
        max_in_flight_test = max(workers_test * 4, 8)
        assert successful_chunks < total_chunks - max_in_flight_test, (
            "test parameters no longer guarantee the bug would manifest -- "
            "increase n_total or lower the success ratio"
        )
        expected_ok_count = successful_chunks * chunk_size_test

        class _DispatchTestArgs:
            pass

        dispatch_args = _DispatchTestArgs()
        dispatch_args.hits = Path(directory) / "hits_dispatch.jsonl"
        dispatch_args.queue = Path(directory) / "queue_dispatch.jsonl"
        dispatch_args.checkpoint = Path(directory) / "checkpoint_dispatch.jsonl"
        dispatch_args.bloom_cache = None
        dispatch_args.workers = workers_test
        dispatch_args.chunk_size = chunk_size_test

        try:
            _sweep_parallel(
                dispatch_args, keystrings_test, set(), None, set(), set(),
                worker_fn=_process_chunk_test_intermittent,
            )
            raise AssertionError(
                "expected _sweep_parallel to exit non-zero given intentional failures"
            )
        except SystemExit as exc:
            assert exc.code == 1, exc.code

        recorded_dispatch = {
            json.loads(l)["keystr_sha256"]
            for l in dispatch_args.checkpoint.read_text().splitlines()
        }
        assert len(recorded_dispatch) == expected_ok_count, (
            len(recorded_dispatch), expected_ok_count,
            "fewer non-poisoned keystrings were checkpointed than expected -- "
            "this is exactly the missing-replenishment bug class caught on review",
        )
        poison_digest = hashlib.sha256(b"POISON").hexdigest()
        assert poison_digest not in recorded_dispatch, (
            "a poisoned (deliberately-failed) chunk was checkpointed"
        )


def _make_test_bloom(path, entries):
    import math
    import struct

    from binary_key_material_backfill import MURMUR_SEED, murmur3_x86_32_20

    n = max(1, len(entries))
    probability = 0.0001
    m_raw = math.ceil((-n * math.log(probability)) / (math.log(2) ** 2))
    m = ((m_raw + 63) // 64) * 64
    k = math.ceil((m / n) * math.log(2))
    words = [0] * (m // 64)
    for entry in entries:
        h1 = murmur3_x86_32_20(entry, MURMUR_SEED)
        h2 = murmur3_x86_32_20(entry, h1)
        for index in range(k):
            bit = (h1 + index * h2) % m
            words[bit // 64] |= 1 << (bit % 64)
    with open(path, "wb") as output:
        output.write(b"BLMCACHE" + bytes([1]))
        output.write(struct.pack("<QI", m, k))
        output.write(b"".join(struct.pack("<Q", word) for word in words))


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-file", type=Path)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--hits", type=Path, default=DEFAULT_HITS)
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--bloom-cache", type=Path, default=DEFAULT_BLOOM)
    parser.add_argument("--no-bloom", action="store_true")
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--workers", type=int, default=1,
        help="1 (default) = sequential, no process pool created at all",
    )
    parser.add_argument(
        "--chunk-size", type=int, default=100,
        help="keystrings per worker task, only relevant when --workers > 1",
    )
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument(
        "--relabel-vanity-queue", action="store_true",
        help=(
            "run after binary_key_material_backfill.py --verify-queue: "
            "relabels vanity-classified entries currently showing "
            "bloom_false_positive to unfunded (see relabel_vanity_verifications). "
            "Makes no API calls; only rewrites already-recorded results."
        ),
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.self_test:
        self_test()
    elif args.relabel_vanity_queue:
        # Same queue-write collision `sweep()` guards against: without this,
        # relabeling could interleave with an active sweep (or a second
        # concurrent relabel invocation) writing to the same queue file.
        lock_file = acquire_run_lock(args.queue)
        try:
            relabeled = relabel_vanity_verifications(args.queue)
        finally:
            lock_file.close()
        print(f"[*] relabeled {relabeled} vanity queue entries from bloom_false_positive to unfunded")
    else:
        sweep(args)


if __name__ == "__main__":
    main()
