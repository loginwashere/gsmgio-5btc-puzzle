#!/usr/bin/env python3
"""Phase 521: can DBBI and FAED share one board key after each keeps its
own separately-best escape pair?

Follow-up to Phase 520 (2026-09-17), which forced ONE shared escape pair on
the raw `DBBI+FAED` concatenation and found no coherence. The user's refined
question: escape-pair choice and board-key choice are logically separate
steps in a straddling checkerboard (the pair only decides which raw symbols
are "escapes" and therefore how the raw stream segments into codes; the
BOARD decides which letter sits in which of the 25 slots). What if each
stream keeps its own already-established, independently-best escape pair
(DBBI: `be`; FAED: `gi`) for segmentation, and only the BOARD KEY is
hypothesized to be shared between them?

This directly speaks to the tension Phase 371/G-ESC-001 already recorded
("each stream's own independently-best escape pair differs") -- that
observation was previously read as one piece of evidence against a
symmetric/joint construction. This phase tests whether it actually needs to
be: a real single-board construction could legitimately use different
escape pairs per segment while still sharing one underlying board.

Statistic: `cost_of_sharing = S_independent - S_shared`, where
`S_independent` is the sum of each stream's own independently-best-annealed
board score, and `S_shared` is the best score achievable by ONE board key
annealed jointly to fit both streams' own-pair-segmented code sequences at
once (each stream scored on its own contiguous quadgram windows only --
no spurious boundary window is created). `cost_of_sharing >= 0` always,
by construction (independent optimization is a strict superset of the
shared-key search space). Lower cost is more consistent with "these two
segments could share one real board"; the question is how the REAL streams'
cost compares to what unrelated streams -- each independently escape-pair-
optimized the same way -- would show.

Matched null: 20,000-scale-intended, but the joint annealer is not cheap,
so this reuses Phase 516's own established two-tier discipline: a CHEAP
budget (6,000 iters x 2 restarts, matching Phase 516's CHEAP_ITERS/
CHEAP_RESTARTS) for both the real primary statistic and every null
replicate (matched budget, so the comparison is apples-to-apples), plus a
separate, secondary EXPENSIVE-budget (60,000 x 30, Phase 516's REFINE_*)
confirmation of the real statistic only, reported as a robustness diagnostic
and never directly p-compared against the cheap null.

No plaintext, password, or key material is generated; no AES oracle. Any
positive result is corroboration_only and cannot itself select a board,
reconcile G-ESC-001, or reopen/close G-YIN-001.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from data import DBBI, FAED  # noqa: E402
from phase459_dual_stream_escape_pair_calibration import (  # noqa: E402
    PAIRS,
    endpoint_fixed_shuffle,
    euler_surrogate,
    pair_loss,
)
from phase484a_raw_symbol_vic_solver import (  # noqa: E402
    PCG32,
    derive_seed,
    load_language_model,
    score_indices,
    segment_raw,
    slot_codes,
)

SEED_BASE = 0x52100AB
CHEAP_ITERS, CHEAP_RESTARTS = 6_000, 2
EXPENSIVE_ITERS, EXPENSIVE_RESTARTS = 60_000, 30
BOARD_T0, BOARD_T1 = 20.0, 0.3
NULL_TRIALS = 300
PROMOTION_THRESHOLD = 0.005

_QUAD_CACHE = None


def quad_table():
    global _QUAD_CACHE
    if _QUAD_CACHE is None:
        _QUAD_CACHE, _ = load_language_model()
    return _QUAD_CACHE


def own_best_pair(stream: str):
    rows = [(pair_loss(stream, pair), pair) for pair in PAIRS]
    best_loss = min(loss for loss, _pair in rows)
    ties = sorted(pair for loss, pair in rows if loss == best_loss)
    return ties[0]


def token_slots_for(stream: str, pair: tuple[str, str]):
    codes = segment_raw(stream, pair)
    if codes is None:
        return None
    slots = slot_codes(pair)
    code_to_slot = {code: index for index, code in enumerate(slots)}
    return np.array([code_to_slot[code] for code in codes], dtype=np.int64)


def anneal_independent(token_slots: np.ndarray, quad, rng: PCG32, iters: int, t0: float, t1: float):
    """Mirrors phase484a_raw_symbol_vic_solver.anneal_board exactly (one
    segment, one key) -- reproduced locally so this module has a single
    self-contained annealing primitive shared by both the independent and
    joint searches below."""
    n = 25
    key = np.array(rng.permutation(n), dtype=np.int64)

    def score(candidate):
        return score_indices(candidate[token_slots], quad)

    current = score(key)
    best, best_key = current, key.copy()
    cool = (t1 / t0) ** (1.0 / max(1, iters))
    temperature = t0
    for _ in range(iters):
        i, j = rng.below(n), rng.below(n)
        if i != j:
            key[i], key[j] = key[j], key[i]
            proposed = score(key)
            delta = proposed - current
            if delta >= 0 or rng.random() < __import__("math").exp(delta / temperature):
                current = proposed
                if proposed > best:
                    best, best_key = proposed, key.copy()
            else:
                key[i], key[j] = key[j], key[i]
        temperature *= cool
    return best_key, best


def anneal_joint(slots_a: np.ndarray, slots_b: np.ndarray, quad, rng: PCG32,
                  iters: int, t0: float, t1: float):
    """One shared 25-slot key, scored as the SUM of both segments' own
    contiguous quadgram windows (no cross-boundary window is ever formed --
    slots_a and slots_b are scored independently and added, never
    concatenated into one array)."""
    n = 25
    key = np.array(rng.permutation(n), dtype=np.int64)

    def score(candidate):
        return score_indices(candidate[slots_a], quad) + score_indices(candidate[slots_b], quad)

    current = score(key)
    best, best_key = current, key.copy()
    cool = (t1 / t0) ** (1.0 / max(1, iters))
    temperature = t0
    for _ in range(iters):
        i, j = rng.below(n), rng.below(n)
        if i != j:
            key[i], key[j] = key[j], key[i]
            proposed = score(key)
            delta = proposed - current
            if delta >= 0 or rng.random() < __import__("math").exp(delta / temperature):
                current = proposed
                if proposed > best:
                    best, best_key = proposed, key.copy()
            else:
                key[i], key[j] = key[j], key[i]
        temperature *= cool
    return best_key, best


def best_independent(slots_a, slots_b, quad, seed_parts, iters, restarts):
    best_a, best_b = -1e18, -1e18
    for restart in range(restarts):
        _, score_a = anneal_independent(slots_a, quad, PCG32(derive_seed(SEED_BASE, *seed_parts, 1, restart)), iters, BOARD_T0, BOARD_T1)
        _, score_b = anneal_independent(slots_b, quad, PCG32(derive_seed(SEED_BASE, *seed_parts, 2, restart)), iters, BOARD_T0, BOARD_T1)
        best_a, best_b = max(best_a, score_a), max(best_b, score_b)
    return best_a, best_b


def best_shared(slots_a, slots_b, quad, seed_parts, iters, restarts):
    best = -1e18
    for restart in range(restarts):
        _, score = anneal_joint(slots_a, slots_b, quad, PCG32(derive_seed(SEED_BASE, *seed_parts, 3, restart)), iters, BOARD_T0, BOARD_T1)
        best = max(best, score)
    return best


def combined_normalized(score_sum: float, len_a: int, len_b: int) -> float:
    windows = max(1, (len_a - 3) + (len_b - 3))
    return score_sum / windows


def cost_of_sharing(stream_a: str, stream_b: str, seed_parts, iters, restarts, quad=None):
    quad = quad_table() if quad is None else quad
    pair_a, pair_b = own_best_pair(stream_a), own_best_pair(stream_b)
    slots_a, slots_b = token_slots_for(stream_a, pair_a), token_slots_for(stream_b, pair_b)
    if slots_a is None or slots_b is None:
        return None
    score_a, score_b = best_independent(slots_a, slots_b, quad, seed_parts, iters, restarts)
    s_independent = score_a + score_b
    s_shared = best_shared(slots_a, slots_b, quad, seed_parts, iters, restarts)
    cost = s_independent - s_shared
    return {
        "pair_a": "".join(pair_a), "pair_b": "".join(pair_b),
        "len_a": len(slots_a), "len_b": len(slots_b),
        "s_independent": s_independent, "s_shared": s_shared,
        "cost_raw": cost,
        "cost_normalized": combined_normalized(cost, len(slots_a), len(slots_b)),
    }


def null_population(kind: str, trials: int, seed: int, iters=CHEAP_ITERS, restarts=CHEAP_RESTARTS):
    rng = random.Random(seed)
    quad = quad_table()
    values = []
    for trial in range(trials):
        if kind == "euler":
            a, b = euler_surrogate(DBBI, rng), euler_surrogate(FAED, rng)
        elif kind == "endpoint_shuffle":
            a, b = endpoint_fixed_shuffle(DBBI, rng), endpoint_fixed_shuffle(FAED, rng)
        else:
            raise ValueError(kind)
        row = cost_of_sharing(a, b, (kind_tag(kind), trial), iters, restarts, quad=quad)
        if row is not None:
            values.append(row["cost_normalized"])
    return values


def kind_tag(kind: str) -> int:
    return 0 if kind == "euler" else 1


def summarize(values, observed):
    ordered = sorted(values)
    extreme = sum(value <= observed for value in values)
    return {
        "trials": len(values),
        "extreme_count": extreme,
        "empirical_p": (extreme + 1) / (len(values) + 1),
        "minimum": ordered[0],
        "median": ordered[len(ordered) // 2],
        "q95": ordered[int(0.95 * (len(ordered) - 1))],
        "maximum": ordered[-1],
    }


def run(trials: int = NULL_TRIALS, run_expensive: bool = True):
    real_cheap = cost_of_sharing(DBBI, FAED, (99, 0), CHEAP_ITERS, CHEAP_RESTARTS)

    primary_null = null_population("euler", trials, SEED_BASE + 1)
    sensitivity_null = null_population("endpoint_shuffle", trials, SEED_BASE + 2)
    primary_summary = summarize(primary_null, real_cheap["cost_normalized"])
    sensitivity_summary = summarize(sensitivity_null, real_cheap["cost_normalized"])

    passes = (
        primary_summary["empirical_p"] <= PROMOTION_THRESHOLD,
        sensitivity_summary["empirical_p"] <= PROMOTION_THRESHOLD,
    )
    if all(passes):
        decision = "robust_shared_board_consistency"
    elif any(passes):
        decision = "null_sensitive"
    else:
        decision = "no_calibrated_shared_board_consistency"

    result = {
        "phase": 521,
        "real_cheap_budget": real_cheap,
        "nulls_cheap_budget": {
            "primary_euler": primary_summary,
            "sensitivity_endpoint_shuffle": sensitivity_summary,
        },
        "promotion_threshold": PROMOTION_THRESHOLD,
        "decision": decision,
        "maximum_inference": "corroboration_only_no_gap_closure_no_board_selected",
        "password_materials_generated": 0,
        "oracle_calls": 0,
    }

    if run_expensive:
        result["real_expensive_budget_diagnostic"] = cost_of_sharing(
            DBBI, FAED, (199, 0), EXPENSIVE_ITERS, EXPENSIVE_RESTARTS,
        )

    return result


def self_test():
    pair = own_best_pair(DBBI)
    assert "".join(pair) == "be", pair
    pair = own_best_pair(FAED)
    assert "".join(pair) == "gi", pair

    slots = token_slots_for(DBBI, ("b", "e"))
    assert slots is not None and len(slots) == 63

    # cost_of_sharing is always >= 0 (independent search is a superset).
    row = cost_of_sharing(DBBI, FAED, (0, 0), 500, 1)
    assert row["cost_raw"] >= -1e-9, row

    # Determinism.
    a1 = cost_of_sharing(DBBI, FAED, (1, 1), 500, 1)
    a2 = cost_of_sharing(DBBI, FAED, (1, 1), 500, 1)
    assert a1["cost_raw"] == a2["cost_raw"]

    print("[*] Phase 521 self-test OK: own-best-pair reproduction (be/gi), "
          "token-slot lengths, cost_of_sharing non-negativity and "
          "determinism passed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--trials", type=int, default=NULL_TRIALS)
    parser.add_argument("--no-expensive", action="store_true")
    parser.add_argument("--json-out", type=Path, default=SCRIPT_DIR / "phase521_result.json")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    elif args.run:
        start = time.monotonic()
        result = run(trials=args.trials, run_expensive=not args.no_expensive)
        result["elapsed_seconds"] = time.monotonic() - start
        args.json_out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(f"[*] wrote {args.json_out} in {result['elapsed_seconds']:.1f}s")
        print(f"[*] decision: {result['decision']}")
    else:
        self_test()


if __name__ == "__main__":
    main()
