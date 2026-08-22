#!/usr/bin/env python3
"""Brainstorm item 2 (2026-08-06 fresh pass, doc/GSMG_FRESH_BRAINSTORM does
NOT contain this list -- it was generated directly in-chat in response to
the creator's "two sloppy days... zero polish" retrospective and is logged
in FINDINGS.md Phase 164): "Try literal page text as key material with zero
transformation. Not hashed, not derived -- raw UTF-8 bytes of some already-
visible phrase, padded/truncated to key length."

Every prior sweep in this project (cb_common.aes_try_open,
EXTENDED_CIPHER_VARIANTS, AES Key Wrap, the nopad oracle) treats a candidate
string as a PASSPHRASE: something fed through EVP_BytesToKey, PBKDF2, or a
SHA-256 digest before it ever becomes cipher key bytes. cb_common already
has the other half of the machinery -- raw_key_try_open() tries a byte
string directly as an AES/3DES key with a zero IV, no derivation at all --
but every existing caller only ever feeds it EXACT-length byte strings
(SHA-256 digests, AES-Key-Wrap-unwrapped output). Nothing in this project
has ever taken an arbitrary-length literal string, padded or truncated it
to a valid key length, and tried it raw. That's a genuine, cheap, distinct
oracle axis this project's own "sloppy/naive build" prior (Phase 138/155)
predicts is worth checking: a rushed hobbyist script doing
`key = passphrase.encode()[:16].ljust(16, b'\\0')` is exactly the kind of
zero-thought shortcut the retrospective message argues for expecting.

Scope: the same 648-candidate curated tier extended_cipher_recheck.py
already uses (Path 1 discipline -- cheap, distilled, high-confidence
material first). answer_forms() case variants only; deliberately NOT
keystr_forms() (sha256/newline/whitespace) since those are hashing/
derivation steps this specific check exists to bypass.

Usage:
    python3 tools/gsmg/literal_raw_key_material_audit.py
    python3 tools/gsmg/literal_raw_key_material_audit.py --self-test
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cb_common import (  # noqa: E402
    BLOBS,
    QUARANTINED_BLOBS,
    RAW_KEY_LENS,
    answer_forms,
    raw_key_try_open,
)
from extended_cipher_recheck import (  # noqa: E402
    candidate_list_digest,
    load_curated_candidates,
)
from binary_key_material_backfill import load_candidates  # noqa: E402

# Union of every valid direct-key length raw_key_try_open() recognizes
# (AES: 16/24/32, 3DES: 8/16/24) -- one padded/truncated form per length.
KEY_LENS = sorted({n for lens in RAW_KEY_LENS.values() for n in lens})


def raw_key_forms(form: str):
    """Every length in KEY_LENS, built by the single most naive
    "buffer(keylen); write string into it" construction: truncate to the
    first N bytes if longer, zero-pad on the right if shorter. Returns a
    dict {length: bytes}, deduplicated by the caller across forms/lengths
    that happen to collide (e.g. two different case variants both shorter
    than 8 bytes zero-pad to the same thing only if they were already
    equal, which can't happen -- kept as a dict for clarity, not dedup)."""
    raw = form.encode("utf-8", errors="replace")
    return {n: raw[:n].ljust(n, b"\x00") for n in KEY_LENS}


def sweep(candidates, blobs=None):
    """Every candidate x answer_forms() case variant x KEY_LENS padded/
    truncated raw-byte form, through raw_key_try_open (zero-IV direct
    AES/3DES key, no KDF/hash at all). Returns (attempts, hits)."""
    attempts = 0
    hits = []
    seen_keys = set()
    for candidate in candidates:
        for form in answer_forms(candidate):
            for length, key_bytes in raw_key_forms(form).items():
                if key_bytes in seen_keys:
                    continue
                seen_keys.add(key_bytes)
                attempts += 1
                result = raw_key_try_open(key_bytes, blobs=blobs)
                for tag, cipher, body, z in result:
                    hits.append({
                        "candidate": candidate,
                        "form": form,
                        "key_len": length,
                        "key_bytes": key_bytes,
                        "blob": tag,
                        "cipher": cipher,
                        "z_score": z,
                        "plaintext": body[:500],
                    })
    return attempts, hits


def self_test():
    """Verify candidate loading + sweep plumbing against a synthetic
    known-positive vector. Extracted from main()'s former inline
    `--self-test` block so it can be called directly (e.g. from the test
    suite) without going through argparse."""
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    candidates = load_candidates(None)
    assert len(candidates) > 500, (
        f"self-test FAILED: expected >500 curated candidates, got {len(candidates)}"
    )
    # Known-positive synthetic vector: a candidate whose literal
    # (truncate/pad) 16-byte form is a real AES-128 key, matching
    # cb_common's own raw_key_try_open self-test pattern.
    synth_phrase = "sixteenbyteskey"  # 15 chars -> zero-padded to 16 bytes
    raw_key = synth_phrase.encode("utf-8").ljust(16, b"\x00")
    assert len(raw_key) == 16
    plaintext = b"literal raw key material self-test vector, zero KDF"
    block = 16
    pad_len = block - (len(plaintext) % block)
    padded = plaintext + bytes([pad_len]) * pad_len
    encryptor = Cipher(algorithms.AES(raw_key), modes.CBC(bytes(block))).encryptor()
    ct = encryptor.update(padded) + encryptor.finalize()
    synth_blobs = {"SYNTHLIT": (b"01234567", ct)}

    forms = raw_key_forms(synth_phrase)
    assert forms[16] == raw_key, (
        f"self-test FAILED: raw_key_forms() built {forms[16]!r}, expected {raw_key!r}"
    )
    attempts, hits = sweep([synth_phrase] + candidates[:5], blobs=synth_blobs)
    assert attempts > 0, "self-test FAILED: sweep() produced zero attempts"
    assert any(
        h["blob"] == "SYNTHLIT" and h["plaintext"] == plaintext for h in hits
    ), (
        "self-test FAILED: sweep() did not recover the known-positive "
        "synthetic literal-raw-key vector"
    )
    print(f"[*] self-test OK ({attempts} attempts on 6 candidates, "
          f"{len(hits)} hits, synthetic vector recovered)")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true",
                     help="verify candidate loading + sweep plumbing against a "
                          "synthetic known-positive vector, then exit")
    ap.add_argument("--include-quarantined", action="store_true",
                     help="also sweep cb_common.QUARANTINED_BLOBS (e.g. urlblob)")
    ap.add_argument("--candidate-file", type=str, default=None,
                     help="path to a newline-delimited candidate wordlist "
                          "(e.g. wordlists/gsmg/medium_curated_all.txt) instead "
                          "of the default 648-candidate curated tier -- same "
                          "convention as binary_key_material_backfill.py")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return

    candidates = load_candidates(args.candidate_file)
    print(f"[*] loaded {len(candidates)} candidates"
          + (f" from {args.candidate_file}" if args.candidate_file else " (default curated tier)"))
    print(f"[*] candidate-list digest: {candidate_list_digest(candidates)}")
    print(f"[*] raw key lengths tried per form: {KEY_LENS}")

    blobs = {**BLOBS, **QUARANTINED_BLOBS} if args.include_quarantined else None
    active_blobs = blobs if blobs is not None else BLOBS

    attempts, hits = sweep(candidates, blobs=blobs)
    print(f"[*] {attempts:,} attempts across {len(KEY_LENS)} raw key lengths "
          f"x {len(active_blobs)} blobs ({', '.join(active_blobs)})")
    if not hits:
        print("[*] no candidate opened any blob as a raw (unhashed, undeived) "
              "truncated/zero-padded AES/3DES key")
        return
    for hit in hits:
        print(f"\n[+++ HIT] candidate={hit['candidate']!r} form={hit['form']!r} "
              f"blob={hit['blob']} cipher={hit['cipher']} key_len={hit['key_len']} "
              f"z={hit['z_score']:.2f}")
        print(f"    key_bytes: {hit['key_bytes']!r}")
        print(f"    plaintext: {hit['plaintext']!r}")


if __name__ == "__main__":
    main()
