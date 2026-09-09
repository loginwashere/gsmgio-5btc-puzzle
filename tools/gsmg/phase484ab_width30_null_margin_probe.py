#!/usr/bin/env python3
"""Token-preserving null-calibrated board-fit margin on width-30 hard paths.

Development only.  Loads the exact hard-negative pool written by Phase 484AA,
fits a checkerboard to each real fragment and to deterministic within-row token
shuffles with the same optimization budget, then ranks the real-minus-null mean
margin.  No FAED or holdout data is imported.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np

import phase484a_raw_symbol_vic_solver as base
import phase484j_constructive_prefix_beam_probe as prefix
import phase484y_width30_feasibility_probe as width30
import phase484y_width30_blind_joint_solver as joint
import phase484z_width30_row_holdout_probe as rowcv
import phase484aa_width30_board_reliability_probe as reliability

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_SOURCE = SCRIPT_DIR / "phase484aa_width30_stability_i16_h400_r8_n2000.json"
NULL_CONTROLS = 2
RESTARTS = 3
ITERATIONS = 2000
SEED = 0x484AB101


def shuffle_rows(rows, seed: int) -> list[np.ndarray]:
    """Shuffle within each row, preserving every row's token multiset."""
    shuffled = []
    for row_index, row in enumerate(rows):
        row = np.asarray(row, dtype=np.int64)
        rng = base.PCG32(base.derive_seed(seed, row_index))
        order = rng.permutation(len(row)) if len(row) else []
        shuffled.append(row[np.asarray(order, dtype=np.int64)].copy())
    return shuffled


def optimized_score(rows, quad, seed: int, restarts: int,
                    iterations: int) -> float:
    rowcv.QUAD = quad
    all_rows = list(range(len(rows)))
    board = rowcv.fit_best(rows, all_rows, seed, restarts, iterations,
                           rowcv.DEFAULT_T0, rowcv.DEFAULT_T1)
    total, windows = rowcv.subset_score(board, rows, all_rows)
    return total / windows if windows else -1e9


def load_pool(path: Path, fixture_index: int):
    path = Path(path)
    source = json.loads(path.read_text())
    if source.get("fixture_index") != fixture_index:
        raise ValueError("source fixture does not match requested fixture")
    if source.get("faed_scored") is not False or source.get(
            "holdout_consumed") is not False:
        raise ValueError("source is not a synthetic development artifact")
    records = source.get("per_candidate", [])
    paths = [tuple(record["path"]) for record in records]
    if not paths or reliability.pool_sha256(paths) != source.get("pool_sha256"):
        raise ValueError("source candidate pool hash mismatch")
    return source, paths, hashlib.sha256(path.read_bytes()).hexdigest()


def run(source_path=DEFAULT_SOURCE, fixture_index=16,
        null_controls=NULL_CONTROLS, restarts=RESTARTS,
        iterations=ITERATIONS, seed=SEED) -> dict:
    if null_controls < 1:
        raise ValueError("at least one null control is required")
    source, paths, source_sha256 = load_pool(source_path, fixture_index)
    fixture = width30.width30_fixture(fixture_index, "dev")
    blocks = prefix.blocks_from_observed(fixture)
    pair = tuple(fixture["pair"])
    truth = prefix.order_to_sequence(fixture["order"])
    paths_array = np.asarray(paths, dtype=np.uint8)
    true_mask = width30.true_path_mask(paths_array, truth, reliability.DEPTH)
    source_true = np.asarray([record["is_true"]
                              for record in source["per_candidate"]])
    if not np.array_equal(true_mask, source_true):
        raise ValueError("source truth labels do not match regenerated fixture")
    quad, _ = base.load_language_model()
    began = time.monotonic()
    observed_scores = np.empty(len(paths), dtype=np.float64)
    margins = np.empty(len(paths), dtype=np.float64)
    per_candidate = []
    for index, path in enumerate(paths):
        rows = joint.canonical_token_rows(blocks, pair, path)
        path_seed = rowcv.path_seed(seed, path)
        observed_replicates = []
        null_scores = []
        for control in range(null_controls):
            anneal_seed = base.derive_seed(path_seed, control + 1, 1)
            observed_replicates.append(optimized_score(
                rows, quad, anneal_seed, restarts, iterations))
            shuffled = shuffle_rows(
                rows, base.derive_seed(path_seed, control + 1, 0))
            null_scores.append(optimized_score(
                shuffled, quad, anneal_seed,
                restarts, iterations))
        observed = float(np.mean(observed_replicates))
        paired_margins = [real - null for real, null in zip(
            observed_replicates, null_scores)]
        margin = float(np.mean(paired_margins))
        observed_scores[index] = observed
        margins[index] = margin
        per_candidate.append({
            "path": list(path), "is_true": bool(true_mask[index]),
            "observed_optimized_scores": observed_replicates,
            "observed_optimized_score_mean": observed,
            "null_optimized_scores": null_scores,
            "paired_real_minus_null": paired_margins,
            "real_minus_null_mean": margin,
        })
    return {
        "phase": "484AB",
        "status": "development_width30_null_margin_not_frozen",
        "faed_scored": False,
        "holdout_consumed": False,
        "fixture_index": fixture_index,
        "source_artifact": str(source_path),
        "source_artifact_sha256": source_sha256,
        "pool_sha256": reliability.pool_sha256(paths),
        "pool_size": len(paths),
        "true_count": int(true_mask.sum()),
        "hard_negative_count": int((~true_mask).sum()),
        "null_controls": null_controls,
        "restarts": restarts,
        "iterations": iterations,
        "seed": seed,
        "seed_scheme": "path_seed_v1; paired real/null anneal seed; per-row token shuffle",
        "observed_optimized_score": reliability.summarize(
            observed_scores, true_mask),
        "real_minus_null_mean": reliability.summarize(margins, true_mask),
        "per_candidate": per_candidate,
        "wall_seconds": time.monotonic() - began,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--fixture-index", type=int, default=16)
    parser.add_argument("--null-controls", type=int, default=NULL_CONTROLS)
    parser.add_argument("--restarts", type=int, default=RESTARTS)
    parser.add_argument("--iterations", type=int, default=ITERATIONS)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.run:
        parser.error("use --run")
    result = run(args.source, args.fixture_index, args.null_controls,
                 args.restarts, args.iterations)
    output = args.output or SCRIPT_DIR / (
        f"phase484ab_width30_null_margin_i{args.fixture_index}_"
        f"c{args.null_controls}_r{args.restarts}_n{args.iterations}.json")
    output.write_text(json.dumps(result, indent=2) + "\n")
    print("observed", result["observed_optimized_score"])
    print("margin", result["real_minus_null_mean"])
    print("wall", round(result["wall_seconds"], 3))
    print("wrote", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
