#!/usr/bin/env python3
"""Shuffle-based null-model control for dbbi_faed_adfgvx_transposition_audit.py's
top result: DBBI e/b escapes_first scored -279.9 under key=lastwordsbeforearchichoice
(untranspose direction), a +22.4 improvement over that variant's real -302.3
baseline -- roughly 2x the noise-band margin Phase 310/311 established for the
Nihilist additive-shift mechanism (~7-8 points) at an equivalent trial count
(264 non-baseline searches in both). Per this project's own established
practice (matrixsum_permutation_sweep.py's shuffle-gate), that margin must be
checked against a null model before being treated as a lead: shuffle the
SAME multiset of DBBI e/b escapes_first slot values (same length, same value
distribution, order randomized), run the IDENTICAL 22-search transposition
pipeline (11 CORE_ALPHABET_SEEDS keywords x transpose/untranspose) against
each shuffled copy, and record each trial's own best-delta-over-its-own-
shuffled-baseline. If shuffled (definitionally meaningless) input reliably
produces deltas at or above the real +22.4/~+17-average result, the real
result is a multiple-comparisons artifact of searching 22 reorderings, not a
decode signal.

Reuses slot_sequence()/hillclimb_slots() (dbbi_faed_nihilist_additive_audit.py)
and transpose()/untranspose() (dbbi_faed_adfgvx_transposition_audit.py)
directly -- no reimplementation. Same hillclimb budget (800 iters/30
restarts) as the real run, so trial cost is directly comparable.

Reproduce with:
    python3 tools/gsmg/dbbi_adfgvx_shuffle_null_model.py --self-test
    python3 tools/gsmg/dbbi_adfgvx_shuffle_null_model.py --trials 20
"""
import argparse
import random
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from dbbi_faed_adfgvx_transposition_audit import (  # noqa: E402
    stable_seed,
    transpose,
    untranspose,
)
from dbbi_faed_nihilist_additive_audit import (  # noqa: E402
    TARGETS,
    hillclimb_slots,
    slot_sequence,
)
from matrixsum_permutation_sweep import CORE_ALPHABET_SEEDS  # noqa: E402

REAL_VARIANT = ("DBBI", "e", "b", "escapes_first")
REAL_TOP_DELTA = 22.4  # -279.9 vs -302.3 baseline, from the real sweep
REAL_TOP15_AVG_DELTA = 17.0  # approx average of the real sweep's top-15 deltas


def real_base_slots(target="DBBI", e1="e", e2="b", topology="escapes_first"):
    raw = TARGETS[target][0]
    return slot_sequence(raw, e1, e2, topology)


def trial_best_delta(shuffled_slots, iters, restarts, seed):
    baseline = hillclimb_slots(shuffled_slots, iters, restarts, seed=seed)
    best_transposed = None
    best_tag = None
    for kw in CORE_ALPHABET_SEEDS:
        for direction, fn in (("transpose", transpose), ("untranspose", untranspose)):
            reordered = fn(shuffled_slots, kw) if direction == "transpose" \
                else fn(shuffled_slots, kw, original_length=len(shuffled_slots))
            if reordered is None or sorted(reordered) != sorted(shuffled_slots):
                continue
            sub_seed = stable_seed(seed, kw, direction)
            result = hillclimb_slots(reordered, iters, restarts, seed=sub_seed)
            if best_transposed is None or result[0] > best_transposed:
                best_transposed = result[0]
                best_tag = f"{kw}/{direction}"
    return baseline[0], best_transposed, best_tag


def self_test():
    base = real_base_slots()
    assert len(base) == 63, len(base)
    rng = random.Random(0)
    shuffled = list(base)
    rng.shuffle(shuffled)
    assert sorted(shuffled) == sorted(base)
    assert shuffled != base  # extremely unlikely to coincide for 63 items
    # Cheap smoke test: tiny budget, just confirm the pipeline runs end to end.
    baseline, best, tag = trial_best_delta(shuffled, iters=50, restarts=3, seed=1)
    assert isinstance(baseline, float) and isinstance(best, float)
    assert tag is not None
    print(f"self-test OK: real base_slots reproduced (len=63), shuffle preserves "
          f"multiset, pipeline smoke test ran (baseline={baseline:.1f}, "
          f"best={best:.1f}, tag={tag})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--trials", type=int, default=20)
    ap.add_argument("--iters", type=int, default=800)
    ap.add_argument("--restarts", type=int, default=30)
    ap.add_argument("--seed-base", type=int, default=1000)
    ap.add_argument("--target", default="DBBI", choices=("DBBI", "FAED"))
    ap.add_argument("--e1", default="e")
    ap.add_argument("--e2", default="b")
    ap.add_argument("--topology", default="escapes_first",
                     choices=("top_first", "escapes_first"))
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return

    base = real_base_slots(args.target, args.e1, args.e2, args.topology)
    deltas = []
    t0 = time.time()
    for t in range(args.trials):
        rng = random.Random(args.seed_base + t)
        shuffled = list(base)
        rng.shuffle(shuffled)
        baseline, best, tag = trial_best_delta(
            shuffled, args.iters, args.restarts, seed=args.seed_base + t)
        delta = best - baseline
        deltas.append(delta)
        elapsed = time.time() - t0
        print(f"[trial {t+1}/{args.trials}] baseline={baseline:.1f} best={best:.1f} "
              f"delta={delta:+.1f} best_key={tag}  (elapsed {elapsed:.0f}s)")

    deltas.sort()
    n = len(deltas)
    mean_delta = sum(deltas) / n
    max_delta = deltas[-1]
    ge_top = sum(1 for d in deltas if d >= REAL_TOP_DELTA)
    ge_avg = sum(1 for d in deltas if d >= REAL_TOP15_AVG_DELTA)
    print(f"\n[*] {n} shuffle trials complete in {time.time()-t0:.0f}s")
    print(f"[*] delta distribution: mean={mean_delta:+.1f}  min={deltas[0]:+.1f}  "
          f"max={max_delta:+.1f}  median={deltas[n//2]:+.1f}")
    print(f"[*] real result comparison: {ge_top}/{n} shuffle trials had "
          f"delta >= real top ({REAL_TOP_DELTA:+.1f}); "
          f"{ge_avg}/{n} had delta >= real top-15 average ({REAL_TOP15_AVG_DELTA:+.1f})")


if __name__ == "__main__":
    main()
