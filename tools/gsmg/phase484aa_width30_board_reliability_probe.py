#!/usr/bin/env python3
"""Width-30 board-reliability diagnostic on actual shortlist hard negatives.

Development only: build the existing depth-8 invariant shortlist, select the
highest-scoring false fragments under an independent one-restart board screen,
then test whether boards recovered from independent restarts agree more strongly
for genuine order windows.  Truth labels are used only after candidate generation
for recovery measurement.  FAED and holdout fixtures are never imported.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import time
from pathlib import Path

import numpy as np

import phase484a_raw_symbol_vic_solver as base
import phase484j_constructive_prefix_beam_probe as prefix
import phase484k_bidirectional_segment_assembly_probe as bidi
import phase484y_width30_feasibility_probe as width30
import phase484y_width30_blind_joint_solver as joint

SCRIPT_DIR = Path(__file__).resolve().parent
DEPTH = 8
HARD_COUNT = 400
HARD_RESTARTS = 1
HARD_ITERATIONS = 2000
STABILITY_RESTARTS = 8
STABILITY_ITERATIONS = 2000
HARD_SEED = 0x484AA101
STABILITY_SEED = 0x484AA201


def pool_sha256(paths) -> str:
    payload = json.dumps([list(map(int, path)) for path in paths],
                         separators=(",", ":")).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def weighted_board_agreement(boards: np.ndarray,
                             token_slots: np.ndarray) -> float:
    """Mean pairwise decoded-letter agreement, token-frequency weighted."""
    boards = np.asarray(boards, dtype=np.uint8)
    token_slots = np.asarray(token_slots, dtype=np.int64)
    if boards.ndim != 2 or boards.shape[1] != 25:
        raise ValueError("boards must be R x 25")
    if len(boards) < 2:
        raise ValueError("at least two boards are required")
    if not len(token_slots):
        return 0.0
    decoded = boards[:, token_slots]
    agreements = [float(np.mean(decoded[left] == decoded[right]))
                  for left, right in itertools.combinations(
                      range(len(boards)), 2)]
    return float(np.mean(agreements))


def summarize(scores: np.ndarray, true_mask: np.ndarray) -> dict:
    scores = np.asarray(scores, dtype=np.float64)
    true = scores[true_mask]
    background = scores[~true_mask]
    order = np.lexsort((np.arange(len(scores)), -scores))
    ranks = np.empty(len(scores), dtype=np.int64)
    ranks[order] = np.arange(1, len(scores) + 1)
    beaten = np.asarray([np.count_nonzero(background > value)
                         for value in true], dtype=np.int64)
    background_std = float(background.std())
    effect = ((float(true.mean()) - float(background.mean())) /
              background_std) if background_std else None
    return {
        "true_scores": true.tolist(),
        "background_mean": float(background.mean()),
        "background_std_ddof0": background_std,
        "background_max": float(background.max()),
        "best_true_rank": int(ranks[true_mask].min()),
        "worst_true_rank": int(ranks[true_mask].max()),
        "mean_beaten_by_background": float(beaten.mean()),
        "median_beaten_by_background": float(np.median(beaten)),
        "effect_true_mean_minus_background_mean_over_background_sd": effect,
    }


def hard_pool(fixture, models, hard_count=HARD_COUNT,
              hard_iterations=HARD_ITERATIONS,
              prefix_binary=width30.DEFAULT_BINARY,
              board_binary=joint.COARSE_BINARY):
    if hard_count < 1:
        raise ValueError("hard-negative count must be positive")
    blocks = prefix.blocks_from_observed(fixture)
    pair = tuple(fixture["pair"])
    truth = prefix.order_to_sequence(fixture["order"])
    truth_paths = sorted(bidi.true_windows(truth, DEPTH))
    paths, _ = joint.build_depth8_shortlist(
        fixture, models=models, binary=prefix_binary)
    quad, _ = base.load_language_model()
    screen_scores, _, _ = joint.gpu_coarse_screen(
        board_binary, blocks, pair, quad, paths,
        iterations=hard_iterations, seed=HARD_SEED)
    false_mask = ~width30.true_path_mask(paths, truth, DEPTH)
    false_indices = np.flatnonzero(false_mask)
    ranked_false = width30.ranked_indices(paths, screen_scores, false_indices)
    chosen = ranked_false[:hard_count]
    hard_paths = [tuple(map(int, path)) for path in paths[chosen]]
    pool = truth_paths + hard_paths
    return pool, {
        "shortlist_size": len(paths),
        "true_paths_present_in_shortlist": int(np.count_nonzero(~false_mask)),
        "hard_count": len(hard_paths),
        "hard_selection_restarts": HARD_RESTARTS,
        "hard_selection_iterations": hard_iterations,
        "hard_selection_seed": HARD_SEED,
        "hard_selection_best_score": float(screen_scores[chosen[0]]),
        "hard_selection_worst_score": float(screen_scores[chosen[-1]]),
    }


def run_stability(fixture_index=16, hard_count=HARD_COUNT,
                  hard_iterations=HARD_ITERATIONS,
                  restarts=STABILITY_RESTARTS,
                  iterations=STABILITY_ITERATIONS,
                  prefix_binary=width30.DEFAULT_BINARY,
                  board_binary=joint.COARSE_BINARY,
                  models=None) -> dict:
    if restarts < 2:
        raise ValueError("stability requires at least two restarts")
    fixture = width30.width30_fixture(fixture_index, "dev")
    if models is None:
        models = width30.train_models()
    blocks = prefix.blocks_from_observed(fixture)
    pair = tuple(fixture["pair"])
    truth = prefix.order_to_sequence(fixture["order"])
    quad, _ = base.load_language_model()
    began = time.monotonic()
    pool, pool_metadata = hard_pool(
        fixture, models, hard_count, hard_iterations,
        prefix_binary, board_binary)
    paths = np.asarray(pool, dtype=np.uint8)
    true_mask = width30.true_path_mask(paths, truth, DEPTH)

    score_runs, board_runs = [], []
    for restart in range(restarts):
        seed = base.derive_seed(STABILITY_SEED, restart)
        scores, _, boards = joint.gpu_coarse_screen(
            board_binary, blocks, pair, quad, paths,
            iterations=iterations, seed=seed)
        score_runs.append(scores)
        board_runs.append(boards)
    score_runs = np.asarray(score_runs)
    board_runs = np.asarray(board_runs)
    best_scores = score_runs.max(axis=0)
    agreements = np.empty(len(paths), dtype=np.float64)
    for index, path in enumerate(paths):
        rows = joint.canonical_token_rows(blocks, pair, path)
        tokens = np.concatenate(rows) if rows else np.empty(0, dtype=np.int64)
        agreements[index] = weighted_board_agreement(
            board_runs[:, index, :], tokens)

    per_candidate = [{
        "path": path.tolist(),
        "is_true": bool(true_mask[index]),
        "best_full_row_score": float(best_scores[index]),
        "weighted_board_agreement": float(agreements[index]),
    } for index, path in enumerate(paths)]
    return {
        "phase": "484AA",
        "status": "development_width30_board_stability_not_frozen",
        "faed_scored": False,
        "holdout_consumed": False,
        "fixture_index": fixture_index,
        "width": width30.WIDTH,
        "depth": DEPTH,
        "pair": list(pair),
        "pool_sha256": pool_sha256(pool),
        "pool_size": len(pool),
        "true_count": int(true_mask.sum()),
        "hard_negative_count": int((~true_mask).sum()),
        "pool_metadata": pool_metadata,
        "stability_restarts": restarts,
        "stability_iterations": iterations,
        "stability_seed": STABILITY_SEED,
        "seed_scheme": "CUDA path_seed_v1",
        "raw_full_row_score": summarize(best_scores, true_mask),
        "weighted_board_agreement": summarize(agreements, true_mask),
        "per_candidate": per_candidate,
        "wall_seconds": time.monotonic() - began,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--fixture-index", type=int, default=16)
    parser.add_argument("--hard-count", type=int, default=HARD_COUNT)
    parser.add_argument("--hard-iterations", type=int,
                        default=HARD_ITERATIONS)
    parser.add_argument("--restarts", type=int, default=STABILITY_RESTARTS)
    parser.add_argument("--iterations", type=int,
                        default=STABILITY_ITERATIONS)
    parser.add_argument("--prefix-binary", type=Path,
                        default=width30.DEFAULT_BINARY)
    parser.add_argument("--board-binary", type=Path,
                        default=joint.COARSE_BINARY)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.run:
        parser.error("use --run")
    result = run_stability(
        args.fixture_index, args.hard_count, args.hard_iterations,
        args.restarts, args.iterations,
        args.prefix_binary, args.board_binary)
    output = args.output or SCRIPT_DIR / (
        f"phase484aa_width30_stability_i{args.fixture_index}_"
        f"h{args.hard_count}_r{args.restarts}_n{args.iterations}.json")
    output.write_text(json.dumps(result, indent=2) + "\n")
    print("raw", result["raw_full_row_score"])
    print("agreement", result["weighted_board_agreement"])
    print("wall", round(result["wall_seconds"], 3))
    print("wrote", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
