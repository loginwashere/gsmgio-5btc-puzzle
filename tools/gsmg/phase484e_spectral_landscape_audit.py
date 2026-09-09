#!/usr/bin/env python3
"""Phase 484E: informal landscape audit of Phase 484A's code-level spectral
statistic at exact widths 10, 15, 19, 30, 38, with the escape pair held
fixed (known).

This is a quick development experiment: no holdout, no lock, no FAED. It
tests whether the planted order is a local optimum of the already-powered
spectral statistic at widths beyond the exhaustively-solved width <= 6/7
range, before any population/order search is built around it.
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path

import numpy as np

import phase484a_raw_symbol_vic_solver as base

SCRIPT_DIR = Path(__file__).resolve().parent
WIDTHS = (10, 15, 19, 30, 38)
BOARD_MODES = base.BOARD_MODES
PAIR_INDEX = 0
FIXTURES_PER_CELL = 5
SEED = 0x484E0DE
CORRUPTION_DEPTHS = (1, 2, 4, 8)
MAX_GREEDY_STEPS = 300


def kendall_tau(order_a, order_b) -> float:
    width = len(order_a)
    rank_a = np.empty(width, dtype=np.int64)
    rank_b = np.empty(width, dtype=np.int64)
    rank_a[np.asarray(order_a)] = np.arange(width)
    rank_b[np.asarray(order_b)] = np.arange(width)
    concordant = 0
    for i in range(width):
        for j in range(i + 1, width):
            concordant += 1 if (rank_a[i] - rank_a[j]) * (rank_b[i] - rank_b[j]) > 0 else -1
    denominator = width * (width - 1) / 2
    return concordant / denominator if denominator else 1.0


def one_swap_neighbors(order: list[int]):
    width = len(order)
    for i, j in itertools.combinations(range(width), 2):
        neighbor = list(order)
        neighbor[i], neighbor[j] = neighbor[j], neighbor[i]
        yield neighbor


def score(model: base.SpectralModel, observed: str, width: int, order, pair) -> float | None:
    return model.score_order(observed, width, order, pair)


def neighbor_survey(model, fixture) -> dict:
    width, observed, pair, truth = (
        fixture["width"], fixture["observed"], tuple(fixture["pair"]), list(fixture["order"])
    )
    planted = score(model, observed, width, truth, pair)
    improving, invalid, gains = 0, 0, []
    best_gain, best_neighbor = -float("inf"), None
    total = 0
    for neighbor in one_swap_neighbors(truth):
        total += 1
        s = score(model, observed, width, neighbor, pair)
        if s is None:
            invalid += 1
            continue
        gain = s - planted
        gains.append(gain)
        if gain > 0:
            improving += 1
        if gain > best_gain:
            best_gain, best_neighbor = gain, neighbor
    return {
        "planted_score": planted,
        "total_neighbors": total,
        "invalid_neighbors": invalid,
        "improving_neighbors": improving,
        "improving_fraction": improving / max(1, total - invalid),
        "best_neighbor_gain": best_gain if best_neighbor is not None else None,
        "mean_neighbor_gain": float(np.mean(gains)) if gains else None,
    }


def greedy_ascent(model, fixture, max_steps: int = MAX_GREEDY_STEPS) -> dict:
    width, observed, pair, truth = (
        fixture["width"], fixture["observed"], tuple(fixture["pair"]), list(fixture["order"])
    )
    current = list(truth)
    current_score = score(model, observed, width, current, pair)
    steps = 0
    for steps in range(1, max_steps + 1):
        best_gain, best_neighbor, best_score = 0.0, None, current_score
        for neighbor in one_swap_neighbors(current):
            s = score(model, observed, width, neighbor, pair)
            if s is None:
                continue
            gain = s - current_score
            if gain > best_gain:
                best_gain, best_neighbor, best_score = gain, neighbor, s
        if best_neighbor is None:
            break
        current, current_score = best_neighbor, best_score
    else:
        steps = max_steps
    return {
        "steps_taken": steps,
        "converged": best_neighbor is None,
        "final_score": current_score,
        "planted_score": score(model, observed, width, truth, pair),
        "kendall_tau_to_truth": kendall_tau(truth, current),
        "exact_order_recovery": current == truth,
    }


def corrupt_by_swaps(order: list[int], rng: base.PCG32, k: int) -> list[int]:
    result = list(order)
    width = len(result)
    for _ in range(k):
        i, j = rng.below(width), rng.below(width)
        while j == i:
            j = rng.below(width)
        result[i], result[j] = result[j], result[i]
    return result


def corruption_curve(model, fixture, seed: int, samples: int = 20) -> dict:
    width, observed, pair, truth = (
        fixture["width"], fixture["observed"], tuple(fixture["pair"]), list(fixture["order"])
    )
    planted = score(model, observed, width, truth, pair)
    curve = {}
    for depth in CORRUPTION_DEPTHS:
        rng = base.PCG32(base.derive_seed(seed, width, depth))
        scores = []
        for _ in range(samples):
            candidate = corrupt_by_swaps(truth, rng, depth)
            s = score(model, observed, width, candidate, pair)
            if s is not None:
                scores.append(s)
        curve[str(depth)] = {
            "samples": len(scores),
            "mean_score": float(np.mean(scores)) if scores else None,
            "median_score": float(np.median(scores)) if scores else None,
        }
    medians = [curve[str(d)]["median_score"] for d in CORRUPTION_DEPTHS]
    monotone_non_increasing = all(
        a is not None and b is not None and a >= b for a, b in zip(medians, medians[1:])
    )
    truth_beats_all_medians = all(m is not None and planted > m for m in medians)
    return {
        "planted_score": planted,
        "curve": curve,
        "monotone_non_increasing_medians": monotone_non_increasing,
        "truth_beats_all_corruption_medians": truth_beats_all_medians,
    }


def run_audit(widths=WIDTHS, board_modes=BOARD_MODES, fixtures_per_cell: int = FIXTURES_PER_CELL) -> dict:
    model = base.SpectralModel.from_training_corpus()
    pair = base.ESCAPE_PAIRS[PAIR_INDEX]
    cells = []
    for board_mode in board_modes:
        for width in widths:
            fixture_records = []
            for index in range(fixtures_per_cell):
                fixture = base.make_fixture(
                    width=width, pair_index=PAIR_INDEX, fixture_index=index,
                    seed=SEED, board_mode=board_mode, split="dev",
                )
                survey = neighbor_survey(model, fixture)
                ascent = greedy_ascent(model, fixture)
                corruption = corruption_curve(model, fixture, seed=SEED)
                fixture_records.append({
                    "fixture_index": index,
                    "neighbor_survey": survey,
                    "greedy_ascent": ascent,
                    "corruption": corruption,
                    "truth_is_local_optimum": survey["improving_neighbors"] == 0,
                })
            local_optimum_count = sum(r["truth_is_local_optimum"] for r in fixture_records)
            exact_after_ascent = sum(r["greedy_ascent"]["exact_order_recovery"] for r in fixture_records)
            cells.append({
                "board_mode": board_mode,
                "width": width,
                "fixture_count": fixtures_per_cell,
                "truth_is_local_optimum_count": local_optimum_count,
                "greedy_ascent_exact_recovery_count": exact_after_ascent,
                "mean_improving_fraction": float(np.mean(
                    [r["neighbor_survey"]["improving_fraction"] for r in fixture_records]
                )),
                "mean_final_kendall_tau": float(np.mean(
                    [r["greedy_ascent"]["kendall_tau_to_truth"] for r in fixture_records]
                )),
                "records": fixture_records,
            })
    return {
        "phase": "484E",
        "status": "informal_dev_scoping_not_frozen",
        "faed_scored": False,
        "pair_index": PAIR_INDEX,
        "pair": list(pair),
        "widths": list(widths),
        "board_modes": list(board_modes),
        "cells": cells,
    }


def self_test() -> bool:
    model = base.SpectralModel.from_training_corpus()
    fixture = base.make_fixture(width=10, pair_index=PAIR_INDEX, fixture_index=0,
                                seed=SEED, board_mode="vic_profile", split="dev")
    survey = neighbor_survey(model, fixture)
    assert survey["total_neighbors"] == 45
    ascent = greedy_ascent(model, fixture, max_steps=5)
    assert ascent["steps_taken"] <= 5
    corruption = corruption_curve(model, fixture, seed=SEED, samples=3)
    assert set(corruption["curve"]) == {str(d) for d in CORRUPTION_DEPTHS}
    return True


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
        print(json.dumps({"self_test": self_test()}))
        raise SystemExit(0)
    result = run_audit()
    out_path = SCRIPT_DIR / "phase484e_landscape_audit_result.json"
    out_path.write_text(json.dumps(result, indent=2))
    for cell in result["cells"]:
        print(f"board_mode={cell['board_mode']:12s} width={cell['width']:3d} "
              f"local_optimum={cell['truth_is_local_optimum_count']}/{cell['fixture_count']} "
              f"greedy_exact={cell['greedy_ascent_exact_recovery_count']}/{cell['fixture_count']} "
              f"mean_improving_frac={cell['mean_improving_fraction']:.3f} "
              f"mean_final_tau={cell['mean_final_kendall_tau']:.3f}")
    print(f"wrote {out_path}")
