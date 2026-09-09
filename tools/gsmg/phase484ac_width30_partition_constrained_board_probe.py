#!/usr/bin/env python3
"""Partition-constrained width-30 checkerboard fit on hard negatives.

The exact-profile and VIC-profile fixture generators both freeze the same
closed-training-corpus rule: the seven single-digit checkerboard slots encode
the seven most frequent training letters, while the 18 double-digit slots
encode the rest.  This development probe preserves that partition and searches
all permutations within each side.  It loads Phase 484AA's exact hard pool and
never imports FAED or holdout data.
"""
from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np

import phase484a_raw_symbol_vic_solver as base
import phase484j_constructive_prefix_beam_probe as prefix
import phase484x_exact_faed_profile_power_probe as exact
import phase484y_width30_feasibility_probe as width30
import phase484y_width30_blind_joint_solver as joint
import phase484z_width30_row_holdout_probe as rowcv
import phase484aa_width30_board_reliability_probe as reliability
import phase484ab_width30_null_margin_probe as margin_probe

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_SOURCE = SCRIPT_DIR / "phase484aa_width30_stability_i16_h400_r8_n2000.json"
GPU_BINARY = SCRIPT_DIR.parents[1] / "_work/phase484ac/constrained_board_server"
RESTARTS = 3
ITERATIONS = 2000
T0, T1 = 20.0, 1.0
SEED = 0x484AC101
SINGLE_SLOTS = tuple(range(7))
DOUBLE_SLOTS = tuple(range(7, 25))


def letter_groups() -> tuple[np.ndarray, np.ndarray]:
    common, other = exact.training_groups()
    index = {letter: value for value, letter in enumerate(base.LETTER_ALPHABET)}
    return (np.asarray([index[letter] for letter in common], dtype=np.int64),
            np.asarray([index[letter] for letter in other], dtype=np.int64))


def initial_board(rng: base.PCG32) -> np.ndarray:
    common, other = letter_groups()
    return np.concatenate([
        common[np.asarray(rng.permutation(len(common)), dtype=np.int64)],
        other[np.asarray(rng.permutation(len(other)), dtype=np.int64)],
    ])


def respects_partition(board) -> bool:
    common, other = letter_groups()
    board = np.asarray(board)
    return (set(board[:7].tolist()) == set(common.tolist()) and
            set(board[7:].tolist()) == set(other.tolist()))


def anneal(rows, quad, seed: int, iterations=ITERATIONS,
           t0=T0, t1=T1) -> tuple[np.ndarray, float, int]:
    rng = base.PCG32(seed)
    board = initial_board(rng)
    windows = sum(max(0, len(row) - 3) for row in rows)

    def score(candidate):
        return sum(base.score_indices(candidate[row], quad)
                   for row in rows if len(row) >= 4)

    current = score(board)
    best, best_board = current, board.copy()
    cooling = (t1 / t0) ** (1.0 / max(1, iterations))
    temperature = t0
    groups = (SINGLE_SLOTS, DOUBLE_SLOTS)
    for _ in range(iterations):
        # Equal group probability prevents the seven-slot side from receiving
        # only 12% of proposals merely because it contains fewer slot pairs.
        group = groups[rng.below(2)]
        left = group[rng.below(len(group))]
        right = group[rng.below(len(group))]
        if left != right:
            board[left], board[right] = board[right], board[left]
            proposed = score(board)
            delta = proposed - current
            if delta >= 0 or rng.random() < math.exp(delta / temperature):
                current = proposed
                if proposed > best:
                    best, best_board = proposed, board.copy()
            else:
                board[left], board[right] = board[right], board[left]
        temperature *= cooling
    return best_board, best / windows if windows else -1e9, windows


def multistart(rows, quad, path, restarts=RESTARTS,
               iterations=ITERATIONS, seed=SEED):
    path_seed = rowcv.path_seed(seed, path)
    best_score, best_board, best_restart = -math.inf, None, None
    for restart in range(restarts):
        board, score, _ = anneal(
            rows, quad, base.derive_seed(path_seed, restart), iterations)
        if score > best_score:
            best_score, best_board, best_restart = score, board, restart
    return best_score, best_board, best_restart


def gpu_parity(binary=GPU_BINARY) -> dict:
    fixture = width30.width30_fixture(16, "dev")
    blocks = prefix.blocks_from_observed(fixture)
    pair = tuple(fixture["pair"])
    truth = prefix.order_to_sequence(fixture["order"])
    paths = np.asarray(sorted(reliability.bidi.true_windows(
        truth, reliability.DEPTH))[:8], dtype=np.uint8)
    quad, _ = base.load_language_model()
    initial_scores, initial_windows, initial_boards = joint.gpu_coarse_screen(
        binary, blocks, pair, quad, paths, iterations=0, seed=SEED)
    actual_scores, actual_windows, actual_boards = joint.gpu_coarse_screen(
        binary, blocks, pair, quad, paths, iterations=37, seed=SEED)
    errors = []
    for index, path in enumerate(paths):
        rows = joint.canonical_token_rows(blocks, pair, path)
        board0, score0, windows = anneal(
            rows, quad, rowcv.path_seed(SEED, path), iterations=0)
        if not np.array_equal(board0, initial_boards[index]):
            raise AssertionError("CPU/GPU initial board mismatch")
        errors.append(abs(score0 - initial_scores[index]))
        # The wire format is uint8.  Cast before score_indices: its base-25
        # vector arithmetic must not wrap at 255.
        returned_board = actual_boards[index].astype(np.int64)
        recomputed = sum(base.score_indices(
            returned_board[row], quad) for row in rows if len(row) >= 4)
        recomputed = recomputed / windows if windows else -1e9
        errors.append(abs(recomputed - actual_scores[index]))
        if windows != initial_windows[index] or windows != actual_windows[index]:
            raise AssertionError("CPU/GPU window count mismatch")
        if not respects_partition(actual_boards[index]):
            raise AssertionError("GPU board escaped frozen partition")
    maximum = max(errors)
    if maximum > 1e-10:
        raise AssertionError(f"CPU/GPU constrained score mismatch: {maximum}")
    return {"paths": len(paths), "max_abs_error": maximum,
            "exact_initial_board_parity": True,
            "returned_boards_respect_partition": True}


def run(source_path=DEFAULT_SOURCE, fixture_index=16,
        restarts=RESTARTS, iterations=ITERATIONS, seed=SEED) -> dict:
    source, paths, source_sha256 = margin_probe.load_pool(
        source_path, fixture_index)
    fixture = width30.width30_fixture(fixture_index, "dev")
    blocks = prefix.blocks_from_observed(fixture)
    pair = tuple(fixture["pair"])
    truth = prefix.order_to_sequence(fixture["order"])
    paths_array = np.asarray(paths, dtype=np.uint8)
    true_mask = width30.true_path_mask(paths_array, truth, reliability.DEPTH)
    quad, _ = base.load_language_model()
    rowcv.QUAD = quad
    began = time.monotonic()
    scores = np.empty(len(paths), dtype=np.float64)
    matched_unconstrained = np.empty(len(paths), dtype=np.float64)
    per_candidate = []
    for index, path in enumerate(paths):
        rows = joint.canonical_token_rows(blocks, pair, path)
        path_seed = rowcv.path_seed(seed, path)
        matched = rowcv.baseline_score(
            rows, path_seed, restarts, iterations, T0, T1)["normalized"]
        score, board, best_restart = multistart(
            rows, quad, path, restarts, iterations, seed)
        if not respects_partition(board):
            raise AssertionError("annealed board escaped frozen partition")
        scores[index] = score
        matched_unconstrained[index] = matched
        per_candidate.append({
            "path": list(path), "is_true": bool(true_mask[index]),
            "normalized_score": float(score),
            "matched_unconstrained_score": float(matched),
            "best_restart": int(best_restart),
            "board": board.tolist(),
        })
    common, other = exact.training_groups()
    return {
        "phase": "484AC",
        "status": "development_width30_partition_constrained_board_not_frozen",
        "faed_scored": False,
        "holdout_consumed": False,
        "fixture_index": fixture_index,
        "source_artifact": str(source_path),
        "source_artifact_sha256": source_sha256,
        "pool_sha256": reliability.pool_sha256(paths),
        "pool_size": len(paths),
        "true_count": int(true_mask.sum()),
        "hard_negative_count": int((~true_mask).sum()),
        "single_slot_letters": list(common),
        "double_slot_letters": list(other),
        "proposal_group_probability": "1/2 single-slot; 1/2 double-slot",
        "restarts": restarts,
        "iterations": iterations,
        "seed": seed,
        "seed_scheme": "path_seed_v1",
        "constrained_score": reliability.summarize(scores, true_mask),
        "matched_unconstrained_score": reliability.summarize(
            matched_unconstrained, true_mask),
        "source_unconstrained_gpu_score": source["raw_full_row_score"],
        "per_candidate": per_candidate,
        "wall_seconds": time.monotonic() - began,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--fixture-index", type=int, default=16)
    parser.add_argument("--restarts", type=int, default=RESTARTS)
    parser.add_argument("--iterations", type=int, default=ITERATIONS)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(gpu_parity(), indent=2))
        return 0
    if not args.run:
        parser.error("use --run")
    result = run(args.source, args.fixture_index,
                 args.restarts, args.iterations)
    output = args.output or SCRIPT_DIR / (
        f"phase484ac_width30_partition_i{args.fixture_index}_"
        f"r{args.restarts}_n{args.iterations}.json")
    output.write_text(json.dumps(result, indent=2) + "\n")
    print("unconstrained", result["source_unconstrained_gpu_score"])
    print("matched unconstrained", result["matched_unconstrained_score"])
    print("constrained", result["constrained_score"])
    print("wall", round(result["wall_seconds"], 3))
    print("wrote", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
