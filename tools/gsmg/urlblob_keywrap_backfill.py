#!/usr/bin/env python3
"""URLBLOB-only AES Key Wrap backfill against the current curated corpus.

The 2026-07-24 quarantine-era Key Wrap recheck (FINDINGS.md, `python3
tools/gsmg/aes_key_wrap_sweep.py --include-quarantined`) covered SALPH,
COSMIC, P32TRAILING, and URLBLOB together, but against the corpus as it
stood then (568 candidates). `extended_cipher_recheck.load_curated_candidates`
now returns 648 -- CURATED_FILES grew after that run. Phase 192 promoted
URLBLOB into the default `cb_common.BLOBS`, so ordinary reruns of
`aes_key_wrap_sweep.py` already cover it going forward; this module closes
the one remaining gap that promotion does not: URLBLOB specifically was
never checked under Key Wrap against the corpus's current 648 candidates.

Deliberately scoped to URLBLOB alone rather than re-running all four blobs:
SALPH/COSMIC/P32TRAILING's own Key-Wrap coverage against the growing corpus
is tracked by `aes_key_wrap_sweep.py`'s own history and is not what this
backfill exists to redo. Reuses `aes_key_wrap_sweep.sweep()` and
`chain_unwrapped()` unmodified -- no new cipher/KDF/wrap logic is
introduced here, only a narrower blob scope over the current corpus.
"""

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from aes_key_wrap_sweep import KEY_WRAP_KDF_VARIANTS, sweep  # noqa: E402
from cb_common import BLOBS  # noqa: E402
from extended_cipher_recheck import (  # noqa: E402
    candidate_list_digest,
    load_curated_candidates,
)

TARGET_BLOBS = {"URLBLOB": BLOBS["URLBLOB"]}


def audit():
    candidates = load_curated_candidates()
    attempts, hits = sweep(candidates, blobs=TARGET_BLOBS)
    unwrap_operations = attempts * len(KEY_WRAP_KDF_VARIANTS) * len(TARGET_BLOBS) * 4
    return {
        "candidate_count": len(candidates),
        "candidate_digest": candidate_list_digest(candidates),
        "kdf_variant_count": len(KEY_WRAP_KDF_VARIANTS),
        "attempts": attempts,
        "unwrap_operations": unwrap_operations,
        "hits": hits,
    }


def self_test():
    candidates = load_curated_candidates()
    assert len(candidates) >= 568, (
        f"self-test FAILED: curated corpus shrank below the last documented "
        f"Key-Wrap/URLBLOB run's 568 candidates: {len(candidates)}"
    )
    probe_attempts, probe_hits = sweep(candidates[:3], blobs=TARGET_BLOBS)
    assert probe_attempts > 0, "self-test FAILED: sweep() produced zero attempts"
    print(
        f"[*] self-test OK ({len(candidates)} candidates available, "
        f"3-candidate probe ran cleanly against URLBLOB, {len(probe_hits)} hits)"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    self_test()
    if args.self_test:
        return

    report = audit()
    print(f"[*] loaded {report['candidate_count']} curated candidates")
    print(f"[*] candidate-list digest: {report['candidate_digest']}")
    print(
        f"[*] {report['kdf_variant_count']} KEK-derivation variants x "
        "1 blob (URLBLOB) x {rfc3394, rfc5649} x {default-AIV, OpenSSL-IV}"
    )
    print(f"[*] {report['attempts']:,} KEK-deriving passphrase attempts")
    print(f"[*] {report['unwrap_operations']:,} effective unwrap operations")
    if not report["hits"]:
        print(
            "[*] no candidate's derived KEK unwrapped URLBLOB under RFC 3394 "
            "or RFC 5649"
        )
        return
    for hit in report["hits"]:
        print(
            f"\n[+++ UNWRAP HIT] candidate={hit['candidate']!r} "
            f"blob={hit['blob']} wrap={hit['wrap_kind']} "
            f"kdf={hit['kdf']}/{hit['key_bits']}bit"
        )
        print(
            f"    unwrapped ({hit['unwrapped_len']} bytes): "
            f"{hit['unwrapped_hex']}"
        )


if __name__ == "__main__":
    main()
