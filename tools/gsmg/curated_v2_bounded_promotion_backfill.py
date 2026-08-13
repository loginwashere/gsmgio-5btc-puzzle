#!/usr/bin/env python3
"""Oracle backfill for the 136 candidates the V2 registry promotes from
excluded to bounded (Fresco/SafeNet-Luna/Looking-Forward lines not in the
historical 648/650 corpus; see curated_candidate_registry.py).

The post-run Phase-257 review corrected this module's original historical
rationale. P32TRAILING was already added in Phase 25, not Phase 77, and the
recorded dedicated Fresco and SafeNet/Luna runs already covered newline-aware
CBC/ECB/stream/Key-Wrap against all four tracked blobs. Phase 44's Looking
Forward run also used all four blobs, but omitted newline forms and predated
the stream oracle. This 136-candidate CBC rerun is therefore valid but mostly
consolidating/repeated coverage; its net addition is the old AES/3DES CBC
families over Looking Forward's newline forms. Phase 255 separately covered
the Blowfish/Camellia/SEED family for all 136 against all four blobs.

This module closes the CBC-family part of that specific gap: legacy KDF_VARIANTS
(AES-128/256-CBC) + EXTENDED_CIPHER_VARIANTS (AES-192-CBC, 3DES-CBC) +
OPENSSL_MENU_GAP_CIPHER_VARIANTS (Blowfish/Camellia/SEED-CBC) = 44 CBC
cipher/KDF combinations, against the current 4-blob BLOBS default. Stream
ciphers (CFB/OFB/CTR) and AES Key Wrap are not covered by this module. Their
true residual scope was later narrowed and closed by
curated_v2_residual_oracle_backfill.py (Phase 257), rather than rerunning all
136 candidates.
"""

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from cb_common import BLOBS, EXTENDED_CIPHER_VARIANTS, KDF_VARIANTS, OPENSSL_MENU_GAP_CIPHER_VARIANTS  # noqa: E402
from curated_candidate_registry import build_registry  # noqa: E402
from extended_cipher_recheck import candidate_list_digest, sweep  # noqa: E402

CBC_FAMILY_VARIANTS = tuple(KDF_VARIANTS) + tuple(EXTENDED_CIPHER_VARIANTS) + tuple(OPENSSL_MENU_GAP_CIPHER_VARIANTS)

EXPECTED_CANDIDATE_COUNT = 136
EXPECTED_CANDIDATE_DIGEST = "8db6659bc547569a"
EXPECTED_CBC_FAMILY_VARIANTS = 44
EXPECTED_EVALUATIONS = 6327
EXPECTED_DECRYPTIONS = 1113552


def net_new_bounded_candidates():
    entries = build_registry()
    return tuple(
        e["candidate"] for e in entries
        if e["pool"] == "phase255-net-new" and e["class"] == "bounded"
    )


def run(blobs=None):
    candidates = net_new_bounded_candidates()
    attempts, hits = sweep(
        list(candidates),
        newline_variants=True,
        blobs=blobs if blobs is not None else BLOBS,
        kdf_variants=CBC_FAMILY_VARIANTS,
    )
    return {
        "candidate_count": len(candidates),
        "candidate_digest": candidate_list_digest(candidates),
        "cbc_family_variants": len(CBC_FAMILY_VARIANTS),
        "blobs": tuple(blobs if blobs is not None else BLOBS),
        "attempts": attempts,
        "concrete_decryptions": attempts * len(CBC_FAMILY_VARIANTS) * len(blobs if blobs is not None else BLOBS),
        "hits": hits,
    }


def self_test():
    """Fast, no-decryption check: candidate scope and digest only, matching
    this project's convention (self-test never runs the live sweep; --run
    does). The live result -- 6,327 evaluations, 1,113,552 decryptions, 0
    hits -- is independently reproducible via --run and recorded in
    FINDINGS.md, not re-executed on every test invocation."""
    candidates = net_new_bounded_candidates()
    assert len(candidates) == EXPECTED_CANDIDATE_COUNT
    assert candidate_list_digest(candidates) == EXPECTED_CANDIDATE_DIGEST
    assert len(CBC_FAMILY_VARIANTS) == EXPECTED_CBC_FAMILY_VARIANTS
    print(
        f"[*] self-test OK: {len(candidates)} net-new bounded candidates/"
        f"{EXPECTED_CANDIDATE_DIGEST}, {len(CBC_FAMILY_VARIANTS)} CBC-family variants staged"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="execute the live sweep")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.run:
        candidates = net_new_bounded_candidates()
        print(f"[*] {len(candidates)} net-new bounded candidates, digest {candidate_list_digest(candidates)}")
        print(f"[*] {len(CBC_FAMILY_VARIANTS)} CBC-family cipher/KDF variants staged (not yet run; pass --run)")
        return
    result = run()
    print(
        f"[*] {result['candidate_count']} candidates / {result['cbc_family_variants']} variants / "
        f"{len(result['blobs'])} blobs / {result['attempts']} evaluations / "
        f"{result['concrete_decryptions']} decryptions"
    )
    print(f"[*] hits: {len(result['hits'])}")
    for hit in result["hits"]:
        print(hit)


if __name__ == "__main__":
    main()
