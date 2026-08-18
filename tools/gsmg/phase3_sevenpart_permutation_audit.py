#!/usr/bin/env python3
"""Bounded, disclosed brute-force of all orderings of Phase 3's seven known
password parts against the still-open blobs, prompted by the Phase 3.2
monologue's "seven intertwined passwords" line.

Distinct from prior coverage, not a rephrasing of it:
- Phase 266 (`phase3_sevenpart_p32_reuse_audit.py`) tested only the one
  canonical solve-order concatenation (and its SHA-256) -- 0 hits. It never
  tested any other ordering of the same seven parts.
- "Intertwined" is read here as a claim about *order*, not content: the
  seven values are already fixed and canonical (the only exactly-seven
  password-level item set uniquely identified anywhere in the solved
  chain -- see that script's docstring for why no other seven-item set is
  adopted). What's untested is whether they concatenate in some order other
  than the one the solved Phase 3 chain happens to use.

Closed, pre-declared candidate set: all 7! = 5040 permutations of the same
seven Phase 3 parts, each tested as (a) raw concatenation and (b) that
concatenation's SHA-256 hex digest -- the exact two forms Phase 266 already
used for the single canonical order, now extended to every order. No other
form (case variants, separators, partial subsets) is introduced -- that
would reopen the arbitrary-construction problem already closed for idea 4
in `2026-08-17 - Architect Monologue vs Film Substitution Table.md`.

Exact-match bar: a successful AES decrypt (valid PKCS#7 padding, no OpenSSL
error) against any tracked blob via the standard `passphrase_hits` oracle.
Stop rule: 0 hits across all 5040 orderings closes this exact hypothesis
negative; no further variant invention (separators, subsets, case forms)
without a new, separately-justified reason.
"""

import argparse
import hashlib
import itertools
import json
import time

from cb_common import BLOBS
from color_mask_full_stream_audit import passphrase_hits

PHASE3_PARTS = (
    "causality",
    "Safenet",
    "Luna",
    "HSM",
    "11110",
    "0x736B6E616220726F662074756F6C69616220646E6F63657320666F206B6E697262"
    "206E6F20726F6C6C65636E61684320393030322F6E614A2F33302073656D695420656854",
    "B5KR/1r5B/2R5/2b1p1p1/2P1k1P1/1p2P2p/1P2P2P/3N1N2 b - - 0 1",
)
CANONICAL_ORDER_SHA256 = (
    "1a57c572caf3cf722e41f5f9cf99ffacff06728a43032dd44c481c77d2ec30d5"
)
EXPECTED_PERMUTATION_COUNT = 5040  # 7!


def all_orderings():
    return list(itertools.permutations(PHASE3_PARTS))


def materials_for_ordering(ordering):
    concat = "".join(ordering)
    digest_hex = hashlib.sha256(concat.encode()).hexdigest()
    return concat.encode("utf-8"), digest_hex.encode("utf-8")


def sweep(orderings, blobs, progress_every=None):
    hits = []
    materials_tested = 0
    for i, ordering in enumerate(orderings):
        for material in materials_for_ordering(ordering):
            materials_tested += 1
            for hit in passphrase_hits(material, blobs):
                hits.append({
                    "ordering_index": i,
                    "ordering": ordering,
                    "material_hex": material.hex(),
                    **hit,
                })
        if progress_every and (i + 1) % progress_every == 0:
            print(f"[*] {i + 1}/{len(orderings)} orderings checked, "
                  f"{materials_tested} materials, {len(hits)} hits so far")
    return {
        "ordering_count": len(orderings),
        "materials_tested": materials_tested,
        "hits": hits,
    }


def audit(progress=False):
    orderings = all_orderings()
    report = sweep(orderings, BLOBS, progress_every=500 if progress else None)
    return {
        "blob_names": tuple(sorted(BLOBS)),
        **report,
    }


def self_test():
    orderings = all_orderings()
    assert len(orderings) == EXPECTED_PERMUTATION_COUNT

    # Regression check: the canonical solved order must reproduce the
    # already-known Phase 3 hash exactly, confirming the seven parts/their
    # exact text are correct before brute-forcing every other order of them.
    canonical_concat = "".join(PHASE3_PARTS)
    assert hashlib.sha256(canonical_concat.encode()).hexdigest() == CANONICAL_ORDER_SHA256

    # Cheap oracle smoke test on a tiny subset (not a full claim).
    subset_report = sweep(orderings[:3], BLOBS)
    assert subset_report["materials_tested"] == 6
    assert subset_report["hits"] == []

    print(
        f"[*] self-test OK: {EXPECTED_PERMUTATION_COUNT} permutations "
        f"confirmed (7! of 7 known parts), canonical order hash matches "
        f"known Phase 3 SHA-256, 3-ordering oracle smoke test clean"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--progress", action="store_true",
                         help="print progress every 500 orderings")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    t0 = time.time()
    report = audit(progress=args.progress)
    elapsed = time.time() - t0
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"[*] done in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
