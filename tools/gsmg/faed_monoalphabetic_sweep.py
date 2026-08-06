#!/usr/bin/env python3
"""Ciphertext-only monoalphabetic checkerboard recovery against FAED under
a chosen ordered escape pair -- (h,e) by default, generalized (Phase 112) to
also run under (g,i).

Rationale for (h,e) (see doc/GSMG_CREATOR_AUTHORED_CLUE_LEDGER.md and
FINDINGS.md Phase 33-41): the reconstructed `574061 -> matrixsumlist
[23,16,7] -> BOTH/ULTIMATELY/THE -> BUT/HYE` chain, keyed by BUT, orders HYE
into HEY -- pointing at escape pair (h,e) with h first, not merely the
unordered {h,e} this project has tested since Phase 16. Phase 43 tested this
pair (and its 3 topology/order siblings) via this script and found real
FAED sitting at the shuffled-null median (empirical p=0.634) -- a clean
negative.

Rationale for (g,i) (FINDINGS.md Phase 112): a real bug in
`checkerboard_code_ic_oracle.py` (ranking by largest code-IC instead of
distance from English's 0.067) was corrected, and the corrected statistic
independently ranks `{g,i}` 1st of 36 possible pairs for FAED (rank-1 in
three separate 1000-trial calibrations against a control built from
UNIFORM RANDOM RAW SYMBOLS, not the token-preserving code-shuffle null this
script's own hillclimb is tested against below -- the two are separate,
complementary checks, not the same statistic) -- a pair this script has
never actually searched under before (Phase 43 tested only (h,e)/(e,h)).

Separately, FAED (570 raw symbols) is a far more favorable regime for blind
substitution-key recovery than DBBI ever was: under (h,e) it segments into
469 complete codes touching all 25 of 25 possible code types (368 in the 7
"top" single-symbol codes, 101 in the 18 escape-led codes) -- vs. DBBI's 63
codes / 19 of 25 types under {b,e}, which checkerboard_recovery_calibration.py
already showed is a hard regime for this technique. Under (g,i) it segments
into 436 codes (Phase 43's corrected exhaustive scan).

This module is a thin driver: hillclimb()/decode_with_key()/score()/
run_all_variants_parallel() are reused verbatim from quadgram_solver.py
(they already take seq/e1/e2/base_pair as parameters and are not
DBBI-specific -- only quadgram_solver.py's own __main__ and internal
`variants` lists are). Only the variant list and __main__ differ here.

Per the approved plan, AES escalation is gated on
checkerboard_recovery_calibration.py --target faed's holdout best-score-
per-char distribution, not run unconditionally -- see --escalate-if-above.

Usage:
    python3 tools/gsmg/faed_monoalphabetic_sweep.py [iters] [restarts] [topn] [workers] [--pair g,i]
    python3 tools/gsmg/faed_monoalphabetic_sweep.py --self-test
"""
import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from cb_common import (  # noqa: E402
    BLOBS,
    EXTENDED_CIPHER_VARIANTS,
    QUARANTINED_BLOBS,
    aes_keywrap_try_open_bytes,
    aes_try_open,
    answer_forms,
    keystr_forms,
)
from data import FAED  # noqa: E402
from quadgram_solver import (  # noqa: E402
    decode_with_key,
    hillclimb,
    run_all_variants_parallel,
    score,
)

# (h,e)/top_first is the pre-registered primary target for the default pair
# (BUT/HEY ordering argument + the already-validated 3.2.2 board layout).
# For (g,i), (g,i)/top_first is primary (matches the code-IC oracle's own
# canonical ordering). All 4 order/topology combos are still run per pair,
# same coverage pattern as quadgram_solver.py's DBBI variants -- nothing is
# silently dropped, but interpretation should treat the first entry as the
# hypothesis under test, not a result picked after seeing scores.
EXPECTED_CODE_COUNTS = {
    ("h", "e"): 469,  # Phase 43
    ("g", "i"): 436,  # Phase 43's corrected exhaustive scan
}


def variants_for_pair(pair):
    e1, e2 = pair
    return [
        (e1, e2, "top_first"),
        (e2, e1, "top_first"),
        (e1, e2, "escapes_first"),
        (e2, e1, "escapes_first"),
    ]


# Backward-compatible default -- existing callers/imports of VARIANTS see
# the same (h,e) list as before.
VARIANTS = variants_for_pair(("h", "e"))

FAED_CODE_COUNT = EXPECTED_CODE_COUNTS[("h", "e")]  # kept for backward compatibility


def run_all_variants_faed(iters, restarts, workers=1, seed_base=2000, pair=("h", "e")):
    variants = variants_for_pair(pair)
    if workers > 1:
        return run_all_variants_parallel(
            FAED, "faed", iters, restarts, workers=workers, seed_base=seed_base,
            base_pair=pair,
        )
    all_results = []
    for vi, (e1, e2, topo) in enumerate(variants):
        best, results = hillclimb(
            FAED, e1, e2, topo, iters=iters, restarts=restarts, seed=seed_base + vi
        )
        print(f"[faed {e1}/{e2} {topo}] best score={best[0]:.1f} decode={best[1]!r}")
        for s_, d_, k_ in results:
            all_results.append((s_, d_, (e1, e2, topo), k_))
    all_results.sort(key=lambda x: -x[0])
    return all_results


def self_test():
    # decode_with_key/hillclimb/score are exercised by test_cb_common.py's
    # own reuse-path coverage of quadgram_solver.py already -- this self-test
    # only checks the FAED-specific wiring (variant list, code count, that a
    # tiny run completes without error), for BOTH pairs this module supports.
    from prefix_boundary_sweep import segment_codes

    assert VARIANTS[0] == ("h", "e", "top_first"), "primary target must be listed first"
    assert len({(e1, e2, topo) for e1, e2, topo in VARIANTS}) == 4

    for pair, expected_count in EXPECTED_CODE_COUNTS.items():
        variants = variants_for_pair(pair)
        assert len({(e1, e2, topo) for e1, e2, topo in variants}) == 4
        codes = segment_codes(FAED, pair[0], pair[1])
        assert len(codes) == expected_count, (
            f"self-test FAILED: expected {expected_count} codes under {pair}, got {len(codes)}"
        )
        assert len(set(codes)) == 25, f"self-test FAILED: expected all 25 code types under {pair}"

        results = run_all_variants_faed(iters=20, restarts=2, workers=1, seed_base=1, pair=pair)
        assert results, "self-test FAILED: hillclimb produced no results"
        best_score, best_decode, _, _ = results[0]
        assert isinstance(best_score, float) and len(best_decode) == expected_count

        # The workers>1 path calls run_all_variants_parallel() through a
        # DIFFERENT code path than the serial branch above (which builds
        # variants directly via hillclimb()) -- it must be checked
        # separately, or a missing base_pair=pair there would silently
        # default back to quadgram_solver.py's hardcoded ("b","e") and
        # search the wrong symbols (caught once already during this
        # session's implementation).
        parallel_results = run_all_variants_faed(
            iters=20, restarts=2, workers=2, seed_base=1, pair=pair
        )
        parallel_variants = {variant for _, _, variant, _ in parallel_results}
        assert parallel_variants == set(variants), (
            f"self-test FAILED: parallel path used wrong variants for {pair}: {parallel_variants}"
        )
    print(f"[*] self-test OK (both (h,e) and (g,i) pairs verified: code counts, "
          f"serial + parallel variant coverage)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("iters", type=int, nargs="?", default=400)
    ap.add_argument("restarts", type=int, nargs="?", default=20)
    ap.add_argument("topn", type=int, nargs="?", default=20)
    ap.add_argument("workers", type=int, nargs="?", default=1)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument(
        "--escalate-if-above",
        type=float,
        default=None,
        help="only run the AES escalation if best_score/len(decode) >= this "
             "threshold (set from checkerboard_recovery_calibration.py "
             "--target faed's holdout best-score-per-char distribution, per "
             "the approved plan's escalation gate). Omit to skip escalation "
             "and just report the hill-climb results.",
    )
    ap.add_argument(
        "--include-quarantined", action="store_true",
        help="also test cb_common.QUARANTINED_BLOBS (URLBLOB) on escalation",
    )
    ap.add_argument(
        "--pair", type=str, default="h,e",
        help="ordered escape pair to search under, as 'e1,e2' (default h,e; "
             "Phase 112 also supports g,i)",
    )
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return

    pair = tuple(args.pair.split(","))
    if len(pair) != 2 or any(len(c) != 1 for c in pair):
        raise SystemExit(f"--pair must be two single characters like 'g,i', got {args.pair!r}")
    if pair not in EXPECTED_CODE_COUNTS:
        raise SystemExit(
            f"--pair {pair} has no known expected code count -- add it to "
            f"EXPECTED_CODE_COUNTS after verifying via segment_codes() first"
        )
    code_count = EXPECTED_CODE_COUNTS[pair]

    print(
        f"[*] faed: {code_count} codes under {pair}/{pair[::-1]}, running "
        f"iters={args.iters} restarts={args.restarts} workers={args.workers}..."
    )
    results = run_all_variants_faed(args.iters, args.restarts, workers=args.workers, pair=pair)

    print(f"\nTop {min(10, len(results))} faed decodes by quadgram score:")
    per_char = []
    for s_, d_, variant, k_ in results[:10]:
        print(f"  {s_:9.1f}  ({s_/len(d_):.4f}/char)  {variant}  {d_!r}")
    best_score, best_decode, best_variant, _ = results[0]
    best_per_char = best_score / len(best_decode)
    print(f"\nBest overall: score={best_score:.1f} per_char={best_per_char:.4f} variant={best_variant}")

    if args.escalate_if_above is None:
        print(
            "\n[*] no --escalate-if-above threshold given -- skipping AES "
            "escalation (per the approved plan's gate). Compare "
            f"per_char={best_per_char:.4f} against "
            "checkerboard_recovery_calibration.py --target faed's holdout "
            "best-score-per-char distribution before deciding whether to "
            "escalate."
        )
        return

    if best_per_char < args.escalate_if_above:
        print(
            f"\n[*] best_per_char={best_per_char:.4f} < threshold="
            f"{args.escalate_if_above:.4f} -- gate CLOSED, not escalating. "
            "Treated as a genuine negative: faed likely isn't a plain "
            "checkerboard under (h,e)/(e,h) at this evidence level."
        )
        return

    print(
        f"\n[*] best_per_char={best_per_char:.4f} >= threshold="
        f"{args.escalate_if_above:.4f} -- gate OPEN, escalating top "
        f"{args.topn} unique decodes to the AES oracle..."
    )
    blobs = {**BLOBS, **QUARANTINED_BLOBS} if args.include_quarantined else None
    hits = []
    tested = set()
    attempts = 0
    # Dedup BEFORE taking the top N, not after: `results` is sorted
    # descending by score but not deduped, and with 4 provably-isomorphic
    # variants (see FINDINGS.md Phase 43) the top raw entries are heavily
    # duplicated -- slicing results[:topn] first and deduping second was
    # measured to leave only 15 unique decodes out of a nominal top 20 (real
    # FAED run, 2026-07-25). Iterating the full sorted list and stopping once
    # `topn` unique decodes are collected still keeps the highest-scoring
    # occurrence of each (first occurrence in sorted order), just without
    # losing slots to duplicates.
    escalation_set = []
    for s_, d_, variant, k_ in results:
        if d_ in tested:
            continue
        tested.add(d_)
        escalation_set.append((s_, d_, variant, k_))
        if len(escalation_set) >= args.topn:
            break
    for s_, d_, variant, k_ in escalation_set:
        # Per the approved plan: answer_forms() first (case variants -- the
        # hill-climb decode is uppercase-only, but real puzzle passphrases
        # have historically been lowercase), then keystr_forms(), then BOTH
        # the original legacy KDF_VARIANTS (kdf_variants=None) and the
        # broadened EXTENDED_CIPHER_VARIANTS as separate calls -- the two are
        # deliberately disjoint (cb_common.py's own comment), so testing only
        # one silently skips the other.
        for form in answer_forms(d_):
            for keystr in keystr_forms(form):
                attempts += 1
                for kdf_variants in (None, EXTENDED_CIPHER_VARIANTS):
                    r = aes_try_open(keystr, kdf_variants=kdf_variants, blobs=blobs)
                    if r:
                        hits.append(("cbc", d_, variant, keystr, kdf_variants, r))
                r2 = aes_keywrap_try_open_bytes(
                    keystr.encode() if isinstance(keystr, str) else keystr, blobs=blobs
                )
                if r2:
                    hits.append(("keywrap", d_, variant, keystr, None, r2))
    print(f"Tested {len(tested)} unique decodes ({attempts} keystring forms). Hits: {len(hits)}")
    for h in hits:
        print("  HIT:", h)


if __name__ == "__main__":
    main()
