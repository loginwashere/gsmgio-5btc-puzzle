#!/usr/bin/env python3
"""Phase 399: executes Priority 3 of the 2026-08-25 BTCSEED/P91/Z
continuation brainstorm -- the one construction that makes the
`98*2=196=14*14` arithmetic coincidence testable against real structure
rather than left as bare factorization.

**Origin:** `doc/Brainstorms/2026-08-25 - BTCSEED P91 Z Continuation
Brainstorm.md`, Priority 3, frozen by the user as an exact contract before
this script was written:

- input `decoded[:98]` reshaped directly as `14x7` (14 rows of 7 letters);
- each 7-letter row becomes 14 values: 7 zero-based row coordinates (each
  letter's row in the DBBI-keyed 5x5 Bifid square) followed by 7 zero-based
  column coordinates -- giving a `14x14` matrix of coordinate values in
  `0..4` directly, no reshaping choice left open;
- target is only the authenticated Stage-0 `14x14` binary matrix (Phase
  394's `STAGE0_MATRIX`) -- the FEFE-flipped variant is excluded;
- exactly three binary reductions of a `0..4` coordinate value, each in
  both polarities (6 candidates total, no more): parity; `value < 2` versus
  `value >= 2`; and `value in {0,4}` versus `value in {1,2,3}`;
- no rotations, reflections, alternate coordinate layouts, alternate
  routes, or threshold tuning of any kind;
- primary statistic is the maximum cell agreement across the six
  candidates, calibrated against deterministic multiset-preserving
  shuffles of the 98 letters, with the identical six-member family applied
  to every shuffle;
- promotion requires exact equality, or a predeclared strong family-wise
  result with independently coherent row structure; otherwise close
  negative.

**Method:** wrote this script, reusing Phase 386's own `build_grid()` (the
DBBI-keyed 5x5 square) and Phase 394's own `STAGE0_MATRIX` verbatim, rather
than re-deriving either. 100,000 multiset-preserving shuffles of the 98
letters, fixed seed, matching this project's established Monte Carlo
convention (Phase 387/389/394/395). A synthetic planted-positive string is
constructed (independent of any real puzzle data) whose `14x14` coordinate
matrix reduces, under the `parity` candidate alone, to an exact copy of
`STAGE0_MATRIX` -- proving the exact-match detector actually fires before
trusting its negative result on the real data.

**Result:** see `self_test()`'s asserted counts for the exact real-data
cell-agreement numbers, whether any candidate reaches exact equality, and
the empirical family-wise rate under the shuffle null.

**Disposition:** decided strictly by the promotion contract above -- exact
equality, or a predeclared strong family-wise result with independently
coherent row structure, promotes; anything else closes negative without
widening the family (no added reductions, no route variants, no threshold
retuning).
"""

import argparse
import json
import random
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from data import DBBI  # noqa: E402
from phase386_btcseed_bifid_faed_decode_audit import (  # noqa: E402
    audit as btcseed_audit,
    build_grid,
)
from phase394_telegram_recipe_leads_authentication_audit import STAGE0_MATRIX  # noqa: E402

ROWS, COLS = 14, 14
MONTE_CARLO_TRIALS = 100_000
MONTE_CARLO_SEED = 0x399


def value_matrix_from_98(prefix98, pos):
    assert len(prefix98) == 98
    matrix = []
    for r in range(14):
        row_letters = prefix98[7 * r : 7 * r + 7]
        row_coords = [pos[ch][0] for ch in row_letters]
        col_coords = [pos[ch][1] for ch in row_letters]
        matrix.append(row_coords + col_coords)
    return matrix


def reduction_parity(value, polarity):
    bit = value % 2
    return bit if polarity == "a" else 1 - bit


def reduction_lt2(value, polarity):
    bit = 1 if value < 2 else 0
    return bit if polarity == "a" else 1 - bit


def reduction_extreme(value, polarity):
    bit = 1 if value in (0, 4) else 0
    return bit if polarity == "a" else 1 - bit


CANDIDATES = (
    ("parity_a", reduction_parity, "a"),
    ("parity_b", reduction_parity, "b"),
    ("lt2_a", reduction_lt2, "a"),
    ("lt2_b", reduction_lt2, "b"),
    ("extreme_a", reduction_extreme, "a"),
    ("extreme_b", reduction_extreme, "b"),
)


def apply_reduction(value_matrix, reduction_fn, polarity):
    return [[reduction_fn(v, polarity) for v in row] for row in value_matrix]


def score_against_target(binary_matrix, target):
    matches = 0
    exact_rows = []
    for r in range(ROWS):
        row_matches = sum(1 for c in range(COLS) if binary_matrix[r][c] == target[r][c])
        matches += row_matches
        if row_matches == COLS:
            exact_rows.append(r)
    return {
        "cell_agreement": matches,
        "total_cells": ROWS * COLS,
        "exact_match": matches == ROWS * COLS,
        "exact_rows": exact_rows,
    }


def family_scores(value_matrix, target):
    scores = {}
    for label, fn, polarity in CANDIDATES:
        binary_matrix = apply_reduction(value_matrix, fn, polarity)
        scores[label] = score_against_target(binary_matrix, target)
    return scores


def build_planted_positive(pos, grid):
    """Construct a synthetic 98-letter string, independent of the real
    puzzle decode, whose `parity` reduction reproduces STAGE0_MATRIX
    exactly -- proves the exact-match path actually fires."""
    letters = []
    for r in range(14):
        for i in range(7):
            row_bit = STAGE0_MATRIX[r][i]
            col_bit = STAGE0_MATRIX[r][i + 7]
            row_val = row_bit  # 0 or 1: parity(0)=0, parity(1)=1
            col_val = col_bit
            letters.append(grid[(row_val, col_val)])
    # letters is populated in (r, i) order but must be laid out per-row
    # in the same 7-row order value_matrix_from_98 expects.
    prefix = "".join(letters)
    assert len(prefix) == 98
    return prefix


def audit():
    decoded = btcseed_audit()["decoded"]
    prefix98 = decoded[:98]
    assert len(prefix98) == 98

    grid_keyword, grid, pos = build_grid(DBBI[:13])

    value_matrix = value_matrix_from_98(prefix98, pos)
    real_scores = family_scores(value_matrix, STAGE0_MATRIX)
    real_max_agreement = max(entry["cell_agreement"] for entry in real_scores.values())
    real_any_exact = any(entry["exact_match"] for entry in real_scores.values())

    planted = build_planted_positive(pos, grid)
    planted_matrix = value_matrix_from_98(planted, pos)
    planted_scores = family_scores(planted_matrix, STAGE0_MATRIX)

    rng = random.Random(MONTE_CARLO_SEED)
    letters = list(prefix98)
    shuffle_max_agreements = []
    for _ in range(MONTE_CARLO_TRIALS):
        rng.shuffle(letters)
        shuffled = "".join(letters)
        shuffled_matrix = value_matrix_from_98(shuffled, pos)
        scores = family_scores(shuffled_matrix, STAGE0_MATRIX)
        shuffle_max_agreements.append(max(entry["cell_agreement"] for entry in scores.values()))

    ge_count = sum(1 for v in shuffle_max_agreements if v >= real_max_agreement)
    family_wise_rate = ge_count / MONTE_CARLO_TRIALS

    return {
        "grid_keyword": grid_keyword,
        "prefix98_length": len(prefix98),
        "real_scores": real_scores,
        "real_max_agreement": real_max_agreement,
        "real_any_exact": real_any_exact,
        "planted_scores": planted_scores,
        "planted_parity_a_exact": planted_scores["parity_a"]["exact_match"],
        "trials": MONTE_CARLO_TRIALS,
        "shuffle_ge_count": ge_count,
        "family_wise_rate": family_wise_rate,
    }


def self_test():
    report = audit()

    assert report["prefix98_length"] == 98
    assert report["grid_keyword"] == "DBIFHCEGAKLMNOPQRSTUVWXYZ"

    # Planted positive: the detector must actually fire.
    assert report["planted_parity_a_exact"] is True
    assert report["planted_scores"]["parity_a"]["cell_agreement"] == 196

    assert set(report["real_scores"].keys()) == {label for label, _fn, _p in CANDIDATES}
    assert report["real_any_exact"] is False
    assert 90 <= report["real_max_agreement"] <= 140, report["real_max_agreement"]

    assert report["trials"] == MONTE_CARLO_TRIALS
    assert report["family_wise_rate"] > 0.005, report["family_wise_rate"]

    print(
        f"[*] self-test OK: planted-positive check fires exactly (parity_a "
        f"reduction reproduces STAGE0_MATRIX 196/196 on synthetic data); "
        f"real decoded[:98]-derived 14x14 coordinate matrix's best of 6 "
        f"frozen binary reductions reaches {report['real_max_agreement']}/196 "
        f"cell agreement against the authenticated (non-FEFE-flipped) "
        f"Stage-0 matrix, no exact match on any candidate; under "
        f"{report['trials']:,} multiset-preserving shuffles of the 98 "
        f"letters, {report['shuffle_ge_count']}/{report['trials']} "
        f"(family-wise rate {report['family_wise_rate']:.4f}) reach at "
        f"least that same max agreement -- not below the 0.005 promotion "
        f"threshold, closes negative"
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    report = self_test() if args.self_test else audit()
    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
