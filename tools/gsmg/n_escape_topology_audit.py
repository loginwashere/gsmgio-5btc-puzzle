#!/usr/bin/env python3
"""Cheap pre-check for a non-standard N-escape straddling-checkerboard topology
(N=3 or N=4 escape leaders out of the 9 raw a-i symbols, instead of the
validated N=2 model) on dbbi/faed.

Generalizes checkerboard_code_ic_oracle.py's segment_codes()/code_ic()
(Phase 106/112's alphabet-independent escape-pair oracle) from escape PAIRS
to escape SETS of any size, using the same classical, UNRESTRICTED
construction: any of the 9 raw symbols -- including another escape leader --
may follow an escape leader as the second digit of a two-symbol code. (A
"restricted" variant that forbids escape-following-escape, discussed in
conversation as a way to force a tidier total code count, has no precedent in
real straddling-checkerboard design or in this puzzle's own validated N=2
construction; this script also reports, per candidate escape set, how many
codes in the real ciphertext would actually be escape-following-escape --
which is exactly the count that would make that specific restricted
construction structurally impossible for this ciphertext, i.e. a cheap
falsifiability check for that variant without writing any decode code.)

Self-tests first: must reproduce checkerboard_code_ic_oracle.py's established
N=2 result (dbbi {b,e} and faed {g,i}, both rank 1st/36) using this script's
own generalized segmenter, before trusting any N=3/N=4 output.

Usage: python3 tools/gsmg/n_escape_topology_audit.py
"""
import itertools
import random
from collections import Counter

from cb_common import NINE_SYMS
from data import DBBI, FAED

ENGLISH_PROSE_IC = 0.067  # same reference used by checkerboard_code_ic_oracle.py


def segment_codes(stream, escapes):
    """escapes: any non-empty set/tuple of raw a-i symbols acting as escape
    leaders. Returns None on a dangling final escape (this escape set cannot
    validly segment this stream at all)."""
    escapes = set(escapes)
    codes = []
    i, n = 0, len(stream)
    while i < n:
        ch = stream[i]
        if ch in escapes:
            if i + 1 >= n:
                return None
            codes.append(stream[i:i + 2])
            i += 2
        else:
            codes.append(ch)
            i += 1
    return codes


def code_ic(codes):
    n = len(codes)
    if n < 2:
        return 0.0
    counts = Counter(codes)
    numerator = sum(c * (c - 1) for c in counts.values())
    return numerator / (n * (n - 1))


def escape_follows_escape_count(stream, escapes):
    """Count of two-symbol codes in the real segmentation whose SECOND digit
    is itself an escape leader -- these are exactly the codes a "restricted"
    (escape can't follow escape) topology could not construct."""
    escapes = set(escapes)
    codes = segment_codes(stream, escapes)
    if codes is None:
        return None
    return sum(1 for c in codes if len(c) == 2 and c[1] in escapes)


def rank_all(stream, n_escapes):
    results = {}
    for combo in itertools.combinations(NINE_SYMS, n_escapes):
        codes = segment_codes(stream, combo)
        if codes is not None:
            results[combo] = code_ic(codes)
    return sorted(results.items(), key=lambda kv: abs(kv[1] - ENGLISH_PROSE_IC))


def self_test():
    checks = [
        ("dbbi", DBBI, ("b", "e"), 0.06708),
        ("faed", FAED, ("g", "i"), 0.07429),
    ]
    for name, stream, expected_pair, expected_ic in checks:
        ranked = rank_all(stream, 2)
        top_combo, top_ic = ranked[0]
        assert set(top_combo) == set(expected_pair), (
            f"self-test FAILED: {name} top N=2 pair is {top_combo}, "
            f"expected {expected_pair}"
        )
        assert abs(top_ic - expected_ic) < 1e-3, (
            f"self-test FAILED: {name} {expected_pair} IC={top_ic:.5f}, "
            f"expected ~{expected_ic:.5f}"
        )
    print("[*] self-test passed: N=2 reproduces checkerboard_code_ic_oracle.py's "
          "Phase 106/112 result exactly (dbbi->{b,e}, faed->{g,i}, both rank 1/36)")


def best_distance(stream, n_escapes):
    ranked = rank_all(stream, n_escapes)
    if not ranked:
        return None
    _, ic = ranked[0]
    return abs(ic - ENGLISH_PROSE_IC)


def null_calibration(stream, n_escapes, trials=1000, seed=20260806):
    """Shuffles the REAL stream's own symbol multiset (preserves exact raw
    symbol-frequency profile, destroys any real checkerboard structure) and
    re-runs the same "best of C(9,n_escapes) combos" search on each shuffle.
    This answers: how close to English does the MULTIPLE-TESTING effect alone
    (trying many combos, keeping the best) get you on pure noise of the same
    length/profile? The real stream's own best distance is only meaningful if
    it beats this null distribution, not just in isolation."""
    rng = random.Random(seed)
    symbols = list(stream)
    null_bests = []
    for _ in range(trials):
        rng.shuffle(symbols)
        shuffled = "".join(symbols)
        d = best_distance(shuffled, n_escapes)
        if d is not None:
            null_bests.append(d)
    null_bests.sort()
    return null_bests


def percentile_rank(value, sorted_null):
    """Fraction of null trials at least as close to English as `value` (i.e.
    the one-sided p-value: P(null best-distance <= real best-distance))."""
    count_as_close_or_closer = sum(1 for d in sorted_null if d <= value)
    return count_as_close_or_closer / len(sorted_null)


def main():
    self_test()
    for name, stream in [("dbbi", DBBI), ("faed", FAED)]:
        print(f"\n=== {name} (raw len={len(stream)}) ===")
        for n_escapes in (2, 3, 4):
            ranked = rank_all(stream, n_escapes)
            total_combos = len(list(itertools.combinations(NINE_SYMS, n_escapes)))
            valid = len(ranked)
            print(f"-- N={n_escapes} escapes ({valid}/{total_combos} combos segment "
                  f"validly; top-row width={9 - n_escapes}, per-escape-row width=9, "
                  f"total code slots={9 - n_escapes + n_escapes * 9}) --")
            for rank, (combo, ic) in enumerate(ranked[:3], 1):
                ef = escape_follows_escape_count(stream, combo)
                flag = " <-- IMPOSSIBLE under a restricted (no escape-follows-" \
                       "escape) topology" if ef else ""
                print(f"   #{rank}: escapes={combo}  IC={ic:.5f}  "
                      f"dist-from-English={abs(ic - ENGLISH_PROSE_IC):.5f}  "
                      f"escape-follows-escape-codes={ef}{flag}")
            real_best = best_distance(stream, n_escapes)
            null = null_calibration(stream, n_escapes, trials=1000)
            p = percentile_rank(real_best, null)
            print(f"   null calibration (1000 shuffles of {name}'s own symbol "
                  f"multiset, best-of-{total_combos} each): "
                  f"null median dist={null[len(null)//2]:.5f}, "
                  f"null 5th-pct dist={null[len(null)//20]:.5f}, "
                  f"real dist={real_best:.5f}  ==>  p={p:.4f} "
                  f"({'REAL beats the null -- worth a closer look' if p < 0.05 else 'NOT exceptional vs. multiple-testing noise'})")


if __name__ == "__main__":
    main()
