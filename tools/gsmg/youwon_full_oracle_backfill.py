#!/usr/bin/env python3
"""Close `GSMG_PHASE_VALIDATION_LOGIC_CONSISTENCY_AUDIT.md` Finding 2: Phase
75's `YOUWON`/`YOUWONX` sweep predates Phase 78's binary-plaintext oracle fix
(`aes_try_open_bytes()` previously discarded a correct AES decrypt whose
plaintext body is non-printable -- exactly the shape a raw private-key body
would have), and neither candidate is registered in
`curated_candidate_registry.py`'s tracked files, so they never received a
confirmed re-sweep under the corrected oracle.

Scope discipline (per this project's brainstorm-doc convention: closed
candidate universe, no expansion after the fact): this reuses
`youwon_partition_audit.py`'s own `candidate_forms()` output verbatim -- the
exact same DBBI-subtraction-derived strings Phase 75 already enumerated
(`YOUWON`, `YOUWONX`-row, the 21-char prefix, 64/63-char tails, the
row-removed/zeroed variants, and the full 91-char output) -- and
`cb_common.answer_forms()` for the same case variants Phase 75 already
tried. No new candidates, no sha256/newline pre-hash forms (that would be a
genuinely different oracle axis, not a "confirm this still holds" rerun).

The one deliberate widening: Phase 75 only ever ran the CBC-family oracle
(`aes_try_open`). This also runs ECB, stream-mode, and AES Key Wrap --
already this project's own standard bar for calling a candidate set "fully
covered" (Phase 256/257's `curated_v2_residual_oracle_backfill.py` sets that
precedent) -- against all four tracked blobs (SALPH, COSMIC, P32TRAILING,
URLBLOB, all now in `cb_common.BLOBS` by default).

Usage:
    python3 tools/gsmg/youwon_full_oracle_backfill.py
    python3 tools/gsmg/youwon_full_oracle_backfill.py --self-test
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cb_common import (  # noqa: E402
    BLOBS,
    ECB_CIPHER_VARIANTS,
    EXTENDED_CIPHER_VARIANTS,
    KDF_VARIANTS,
    KEY_WRAP_KDF_VARIANTS,
    STREAM_CIPHER_VARIANTS,
    aes_keywrap_try_open_bytes,
    aes_try_open_bytes,
    aes_try_open_ecb_bytes,
    aes_try_open_stream_bytes,
    answer_forms,
)
from youwon_partition_audit import audit as youwon_audit

CBC_VARIANTS = tuple(KDF_VARIANTS) + tuple(EXTENDED_CIPHER_VARIANTS)


def candidate_passphrases():
    """Every Phase-75 candidate label x its answer_forms() case variants,
    deduplicated by exact byte string (18 unique -- `youwon_partition_audit`'s
    own CBC-only sweep reports 20 because it dedupes by (label, form) pair,
    not by resulting byte string; two case-form pairs collide across labels).
    Returns a tuple of (label, form, bytes)."""
    result = youwon_audit(run_oracle=False)
    seen = set()
    out = []
    for label, candidate in result["candidates"].items():
        for form in sorted(answer_forms(candidate)):
            material = form.encode()
            if material in seen:
                continue
            seen.add(material)
            out.append((label, form, material))
    return tuple(out)


def run(blobs=None):
    active_blobs = BLOBS if blobs is None else blobs
    passphrases = candidate_passphrases()
    hits = {"cbc": [], "ecb": [], "stream": [], "keywrap": []}

    for label, form, material in passphrases:
        result = aes_try_open_bytes(material, kdf_variants=CBC_VARIANTS, blobs=active_blobs)
        if result:
            hits["cbc"].append((label, form, result))
        result = aes_try_open_ecb_bytes(material, blobs=active_blobs)
        if result:
            hits["ecb"].append((label, form, result))
        result = aes_try_open_stream_bytes(material, blobs=active_blobs)
        if result:
            hits["stream"].append((label, form, result))
        for result in aes_keywrap_try_open_bytes(material, blobs=active_blobs):
            hits["keywrap"].append((label, form, result))

    blob_count = len(active_blobs)
    n = len(passphrases)
    return {
        "passphrase_count": n,
        "blobs": tuple(active_blobs),
        "cbc_variants": len(CBC_VARIANTS),
        "ecb_variants": len(ECB_CIPHER_VARIANTS),
        "stream_variants": len(STREAM_CIPHER_VARIANTS),
        "keywrap_kdf_variants": len(KEY_WRAP_KDF_VARIANTS),
        "cbc_decryptions": n * len(CBC_VARIANTS) * blob_count,
        "ecb_decryptions": n * len(ECB_CIPHER_VARIANTS) * blob_count,
        "stream_decryptions": n * len(STREAM_CIPHER_VARIANTS) * blob_count,
        "keywrap_effective_unwrap_attempts": n * len(KEY_WRAP_KDF_VARIANTS) * blob_count * 4,
        "hits": hits,
        "total_hits": sum(len(v) for v in hits.values()),
    }


def self_test():
    passphrases = candidate_passphrases()
    assert len(passphrases) == 18, (
        f"self-test FAILED: expected 18 unique candidate forms, got "
        f"{len(passphrases)}"
    )
    labels = {label for label, _, _ in passphrases}
    assert {"word", "row"} <= labels, (
        f"self-test FAILED: expected 'word' (YOUWON) and 'row' (YOUWONX) "
        f"labels present, got {labels}"
    )
    assert tuple(BLOBS) == ("SALPH", "COSMIC", "P32TRAILING", "URLBLOB"), (
        f"self-test FAILED: expected all 4 tracked blobs in BLOBS by default, "
        f"got {tuple(BLOBS)}"
    )
    report = run()
    assert report["total_hits"] == 0, (
        f"self-test FAILED: expected 0 hits across CBC/ECB/stream/Key Wrap, "
        f"got {report['total_hits']}: {report['hits']}"
    )
    print(
        f"[*] self-test OK: {report['passphrase_count']} candidate forms "
        f"(Phase 75's YOUWON/YOUWONX set, unchanged) x current post-Phase-78 "
        f"oracle x CBC/ECB/stream/Key Wrap x {len(report['blobs'])} blobs, "
        f"{report['total_hits']} hits"
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return

    report = run()
    print(
        f"[*] {report['passphrase_count']} candidate forms x "
        f"{len(report['blobs'])} blobs ({', '.join(report['blobs'])})"
    )
    print(
        f"[*] CBC: {report['cbc_decryptions']:,} decryptions "
        f"({report['cbc_variants']} variants)"
    )
    print(
        f"[*] ECB: {report['ecb_decryptions']:,} decryptions "
        f"({report['ecb_variants']} variants)"
    )
    print(
        f"[*] stream: {report['stream_decryptions']:,} decryptions "
        f"({report['stream_variants']} variants)"
    )
    print(
        f"[*] Key Wrap: {report['keywrap_effective_unwrap_attempts']:,} "
        f"effective unwrap attempts ({report['keywrap_kdf_variants']} KDF variants)"
    )
    if report["total_hits"] == 0:
        print("[*] 0 hits across CBC, ECB, stream, and Key Wrap")
        return
    for family, entries in report["hits"].items():
        for label, form, result in entries:
            print(f"\n[+++ HIT] family={family} label={label} form={form!r}")
            print(f"    {result}")


if __name__ == "__main__":
    main()
