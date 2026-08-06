#!/usr/bin/env python3
"""AES Key Wrap (RFC 3394 / RFC 5649) hypothesis test, prioritized 2026-07-24
after Phase 25's provenance triage surfaced that an external, independently-
maintained fork's own attempt catalog flags "-id-aes256-wrap-pad" as an
untested cipher-mode hypothesis for the exact blob this project tracks as
P32TRAILING (see FINDINGS.md Phase 25). Every prior sweep in this project --
including path 1's broadened EXTENDED_CIPHER_VARIANTS -- still assumes CBC
mode. AES Key Wrap is a structurally different mode (no CBC IV; strict RFC
forms use a fixed AIV while OpenSSL `enc` derives a custom wrap IV, wraps *key
material* rather than arbitrary plaintext, and carries its own built-in
integrity check distinct from CBC's PKCS7-padding heuristic), so a correct
passphrase under CBC-only coverage would look identical to a wrong one if
the real cipher mode were Key Wrap all along.

Per the exact instructions for this path:
  - RFC 3394 and RFC 5649 (padded) are tested SEPARATELY, under both their
    strict RFC default AIVs and OpenSSL `enc`'s password-derived custom IVs.
  - KEKs are derived through the EXISTING EVP_BytesToKey/PBKDF2 machinery
    (cb_common.KEY_WRAP_KDF_VARIANTS), not a new derivation scheme.
  - Every branch (RFC 3394 unwrap, RFC 5649 unwrap, and the raw-key chaining
    step below) is validated against synthetic known-positive vectors before
    being trusted against the real blobs -- see cb_common._self_test_keywrap
    and this module's own --self-test.
  - A successful unwrap's output is treated as KEY MATERIAL FIRST, not
    assumed to be plaintext: cb_common.raw_key_try_open() tries it as a
    direct AES/3DES key (zero IV, no passphrase-based derivation) against
    all blobs, and separately its text/hex forms are tried as ordinary
    PASSPHRASES (through the normal EVP_BytesToKey/PBKDF2 path) against all
    blobs -- only after a real unwrap succeeds, never speculatively.
  - `urlblob` (the fourth blob surfaced by the same external research) was
    NOT added when this module was first written -- it needed its own
    exact-archived-byte-and-provenance verification first. That verification
    is now done (see data.URLBLOB_B64: independently re-fetched from the
    live Wayback CDX API, byte-exact match confirmed, a truncated-capture/
    timestamp error in the source fork's own citation caught and corrected).
    Its puzzle-authenticity is still weaker than SALPH/COSMIC/P32TRAILING
    (no official-README/solved-plaintext corroboration, source fork calls it
    "orphaned"), so it's tracked as a QUARANTINED target
    (cb_common.QUARANTINED_BLOBS) -- opt in with --include-quarantined
    rather than it silently joining the default sweep.

Bounded to the same CURATED candidate set path 1 already validated as a
reasonable-cost source (not the raw multi-megabyte mined corpora) -- AES Key
Wrap's per-attempt cost is a few block ops (cheaper than a full CBC decrypt
of the body), so this comfortably affords the same candidate breadth.

Usage:
    python3 tools/gsmg/aes_key_wrap_sweep.py
    python3 tools/gsmg/aes_key_wrap_sweep.py --self-test
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cb_common import (  # noqa: E402
    BLOBS,
    EXTENDED_CIPHER_VARIANTS,
    KDF_VARIANTS,
    KEY_WRAP_KDF_VARIANTS,
    QUARANTINED_BLOBS,
    aes_key_wrap,
    aes_keywrap_try_open,
    aes_keywrap_try_open_bytes,
    aes_try_open,
    answer_forms,
    derive_kek,
    keystr_forms,
    raw_key_try_open,
)
from extended_cipher_recheck import candidate_list_digest, load_curated_candidates  # noqa: E402

ALL_CBC_VARIANTS = list(KDF_VARIANTS) + list(EXTENDED_CIPHER_VARIANTS)


def chain_unwrapped(unwrapped: bytes, source_tag: str, blobs=None):
    """Given successfully-unwrapped bytes, test them two ways -- "key material
    first, not necessarily plaintext":

    1. As a direct cipher key (zero IV, cb_common.raw_key_try_open) against
       every blob, including the source blob itself (a key-wrap KEK unwrap
       could plausibly hand back the *same* blob's own CBC key, if the
       puzzle layers key-wrap around a second CBC-encrypted stage using the
       same container).
    2. As ordinary passphrase text/hex, through the normal EVP_BytesToKey/
       PBKDF2 + CBC path (aes_try_open), against every blob -- covering the
       case where the unwrapped material is itself a password string rather
       than raw key bytes.

    Returns (raw_key_hits, passphrase_hits).
    """
    raw_key_hits = raw_key_try_open(unwrapped, blobs=blobs)

    passphrase_hits = []
    text_forms = set()
    try:
        text_forms.add(unwrapped.decode("utf-8").strip())
    except UnicodeDecodeError:
        pass
    text_forms.add(unwrapped.hex())
    text_forms.discard("")
    for form in text_forms:
        for af in answer_forms(form):
            for keystr in keystr_forms(af):
                result = aes_try_open(keystr, kdf_variants=ALL_CBC_VARIANTS, blobs=blobs)
                if result:
                    tag, body, kdf_label, key_len = result
                    passphrase_hits.append((keystr, tag, body, kdf_label, key_len))
    return raw_key_hits, passphrase_hits


def sweep(candidates, newline_variants=True, blobs=None):
    """Every candidate line, through answer_forms() x keystr_forms(), as a
    KEK-deriving passphrase against every blob under both RFC 3394 and RFC
    5649. Returns (attempts, hits) where each hit is a dict with the wrap
    match plus chained raw-key/passphrase follow-up results."""
    attempts = 0
    hits = []
    for candidate in candidates:
        for form in answer_forms(candidate):
            for keystr in keystr_forms(form, newline_variants=newline_variants):
                attempts += 1
                for tag, wrap_kind, kdf_label, key_len, unwrapped in aes_keywrap_try_open_bytes(
                    keystr.encode(), blobs=blobs
                ):
                    raw_key_hits, passphrase_hits = chain_unwrapped(unwrapped, tag, blobs=blobs)
                    hits.append({
                        "candidate": candidate,
                        "form": form,
                        "keystr": keystr,
                        "blob": tag,
                        "wrap_kind": wrap_kind,
                        "kdf": kdf_label,
                        "key_bits": key_len * 8,
                        "unwrapped_hex": unwrapped.hex(),
                        "unwrapped_len": len(unwrapped),
                        "raw_key_hits": raw_key_hits,
                        "passphrase_hits": passphrase_hits,
                    })
    return attempts, hits


def _self_test():
    """End-to-end validation of THIS module's sweep()/chain_unwrapped()
    plumbing (cb_common's own primitives are separately validated by
    cb_common._self_test_keywrap(), imported and run automatically). Builds
    a synthetic scenario where a known candidate passphrase's derived KEK
    (via a KEY_WRAP_KDF_VARIANTS combo) wraps a raw AES key via RFC 3394,
    and that raw key is itself the zero-IV key to a SECOND synthetic
    AES-CBC blob -- confirming sweep() finds the unwrap hit AND
    chain_unwrapped() recovers the second-stage plaintext via
    raw_key_try_open(), without being told either answer directly."""
    import cb_common
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    known_answer = "keywrap-self-test-passphrase"
    salt = b"deadbeef"
    kdf_kind, kdf_param, key_len = KEY_WRAP_KDF_VARIANTS[0]
    keystr = keystr_forms(known_answer)[0]
    kek = derive_kek(kdf_kind, kdf_param, salt, keystr.encode(), key_len)

    second_stage_key = b"0123456789ABCDEF"  # 16 bytes: valid RFC 3394 payload
    # and a valid direct AES-128 key for the second stage.
    wrapped = aes_key_wrap(kek, second_stage_key)

    second_stage_plaintext = b"chained past the key-wrap unwrap successfully"
    block = 16
    pad_len = block - (len(second_stage_plaintext) % block)
    padded = second_stage_plaintext + bytes([pad_len]) * pad_len
    encryptor = Cipher(algorithms.AES(second_stage_key), modes.CBC(bytes(block))).encryptor()
    second_stage_ct = encryptor.update(padded) + encryptor.finalize()

    real_blobs_backup = dict(cb_common.BLOBS)
    cb_common.BLOBS.clear()
    cb_common.BLOBS.update({
        "SYNTHWRAP": (salt, wrapped),
        "SYNTHSTAGE2": (b"01234567", second_stage_ct),
    })
    try:
        attempts, hits = sweep([known_answer], newline_variants=False)
    finally:
        cb_common.BLOBS.clear()
        cb_common.BLOBS.update(real_blobs_backup)

    assert attempts > 0, "self-test FAILED: sweep() produced zero attempts"
    matching = [
        h for h in hits
        if h["blob"] == "SYNTHWRAP"
        and h["wrap_kind"] == "rfc3394-default"
    ]
    assert matching, (
        "self-test FAILED: sweep() did not find the synthetic RFC 3394 "
        "key-wrap hit"
    )
    hit = matching[0]
    assert bytes.fromhex(hit["unwrapped_hex"]) == second_stage_key, (
        "self-test FAILED: sweep() unwrapped to the wrong key material"
    )
    assert any(
        rh[0] == "SYNTHSTAGE2" and rh[2] == second_stage_plaintext
        for rh in hit["raw_key_hits"]
    ), (
        "self-test FAILED: chain_unwrapped() did not recover the second-stage "
        "plaintext via raw_key_try_open() from the unwrapped key material"
    )
    print(f"[*] self-test OK ({attempts} attempts, chained unwrap -> "
          f"second-stage plaintext recovered end-to-end)")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true",
                     help="verify sweep/chaining plumbing against a synthetic "
                          "two-stage vector, then exit")
    ap.add_argument("--include-quarantined", action="store_true",
                     help="also target cb_common.QUARANTINED_BLOBS (urlblob) "
                          "-- opt-in since its puzzle provenance is weaker "
                          "than the default BLOBS")
    args = ap.parse_args()

    if args.self_test:
        _self_test()
        return

    blobs = {**BLOBS, **QUARANTINED_BLOBS} if args.include_quarantined else None
    active_blobs = blobs if blobs is not None else BLOBS

    candidates = load_curated_candidates()
    print(f"[*] loaded {len(candidates)} curated candidates")
    print(f"[*] candidate-list digest: {candidate_list_digest(candidates)}")
    print(f"[*] {len(KEY_WRAP_KDF_VARIANTS)} KEK-derivation variants x "
          f"{len(active_blobs)} blobs ({', '.join(active_blobs)}) x "
          f"{{rfc3394, rfc5649}} x {{default-AIV, OpenSSL-IV}}")

    attempts, hits = sweep(candidates, blobs=blobs)
    print(f"[*] {attempts:,} KEK-deriving passphrase attempts")
    unwrap_operations = (
        attempts * len(KEY_WRAP_KDF_VARIANTS) * len(active_blobs) * 4
    )
    print(f"[*] {unwrap_operations:,} effective unwrap operations")
    if not hits:
        print("[*] no candidate's derived KEK unwrapped any blob under "
              "RFC 3394 or RFC 5649")
        return
    for hit in hits:
        print(f"\n[+++ UNWRAP HIT] candidate={hit['candidate']!r} "
              f"blob={hit['blob']} wrap={hit['wrap_kind']} "
              f"kdf={hit['kdf']}/{hit['key_bits']}bit")
        print(f"    unwrapped ({hit['unwrapped_len']} bytes): "
              f"{hit['unwrapped_hex']}")
        if hit["raw_key_hits"]:
            for tag, cipher, body, z in hit["raw_key_hits"]:
                print(f"    [+++ CHAINED RAW-KEY HIT] blob={tag} cipher={cipher} "
                      f"z={z:.1f}")
                print(f"        plaintext: {body[:500]!r}")
        if hit["passphrase_hits"]:
            for keystr, tag, body, kdf_label, key_len in hit["passphrase_hits"]:
                print(f"    [+++ CHAINED PASSPHRASE HIT] via {keystr!r} -> "
                      f"{tag} ({kdf_label}/{key_len * 8}bit)")
                print(f"        plaintext: {body[:500]!r}")
        if not hit["raw_key_hits"] and not hit["passphrase_hits"]:
            print("    [*] unwrap succeeded but no chained interpretation "
                  "opened any blob -- unwrapped bytes recorded above for "
                  "manual inspection")


if __name__ == "__main__":
    main()
