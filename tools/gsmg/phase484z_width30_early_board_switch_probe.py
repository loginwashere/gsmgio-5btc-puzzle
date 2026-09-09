#!/usr/bin/env python3
"""Development probe: switch width-30 prefix selection to a learned board at depth 7.

The collision-corrected width-30 pipeline can recover a complete order whenever a
true depth-8 window survives the invariant shortlist. Its remaining bottleneck is
shortlist recall. This probe uses the invariant objective only through depth 7,
then applies the existing GPU checkerboard annealer before selecting at depths 7
and 8. It imports no FAED ciphertext and does not use holdout fixtures.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

import phase484a_raw_symbol_vic_solver as base
import phase484j_constructive_prefix_beam_probe as prefix
import phase484y_width30_feasibility_probe as width30
import phase484y_width30_blind_joint_solver as joint
import phase484y_width30_board_ceiling_map as ceiling_map
import phase484o_joint_board_order_ceiling as ceiling

SCRIPT_DIR = Path(__file__).resolve().parent
SWITCH_DEPTH = 7
DEFAULT_KEEP = width30.DEFAULT_KEEP
DEFAULT_DEPTH6_KEEP = width30.DEFAULT_DEPTH6_KEEP
DEFAULT_DEPTH7_KEEP = width30.DEFAULT_DEPTH7_KEEP
DEFAULT_DEPTH8_KEEP = width30.DEFAULT_FINAL_KEEP
DEFAULT_RESTARTS = 1
DEFAULT_ITERATIONS = 2000
BOARD_CHUNK = 1 << 20


def recovery_record(paths, scores, truth, depth: int,
                    include_best=False) -> dict:
    count, best_rank = width30.generated_true_metrics(
        np.asarray(paths, dtype=np.uint8), np.asarray(scores), truth, depth)
    record = {"candidate_count": len(paths), "true_segments": count,
              "best_true_rank": best_rank}
    if include_best and count:
        paths = np.asarray(paths, dtype=np.uint8)
        scores = np.asarray(scores, dtype=np.float64)
        mask = width30.true_path_mask(paths, truth, depth)
        candidates = np.flatnonzero(mask)
        winner = width30.ranked_indices(paths, scores, candidates)[0]
        record.update({
            "best_true_path": paths[winner].tolist(),
            "best_true_score": float(scores[winner]),
        })
    return record


def save_checkpoint(directory, label, paths, scores):
    if directory is None:
        return None
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / f"{label}.npz"
    np.savez(destination, paths=np.asarray(paths, dtype=np.uint8),
             scores=np.asarray(scores, dtype=np.float64))
    return str(destination)


def invariant_to_depth7(fixture, models, keep=DEFAULT_KEEP,
                        depth6_keep=DEFAULT_DEPTH6_KEEP,
                        depth7_keep=DEFAULT_DEPTH7_KEEP,
                        binary=width30.DEFAULT_BINARY):
    """Return the invariant-selected depth-7 population and scores."""
    blocks = prefix.blocks_from_observed(fixture)
    pair = tuple(fixture["pair"])
    paths = width30.initial_paths(width30.START_DEPTH)
    with width30.GpuWidth30Scorer(
            binary, blocks, pair, models[width30.START_DEPTH]) as scorer:
        scores = width30.score_chunked(scorer, paths)
    diagnostics = []
    for depth in range(width30.START_DEPTH, SWITCH_DEPTH):
        capacity = depth6_keep if depth == 6 else keep
        paths, scores, unique_count = width30.select_diverse(
            paths, scores, capacity)
        diagnostics.append({"depth": depth, "generated_unique": unique_count,
                            "retained": len(paths)})
        paths = width30.expand_bidirectional(paths)
        with width30.GpuWidth30Scorer(
                binary, blocks, pair, models[depth + 1]) as scorer:
            scores = width30.score_chunked(scorer, paths)
    paths, scores, unique_count = width30.select_diverse(
        paths, scores, depth7_keep)
    diagnostics.append({"depth": SWITCH_DEPTH,
                        "generated_unique": unique_count,
                        "retained": len(paths)})
    return paths, scores, diagnostics


def board_screen(paths, blocks, pair, quad, restarts=DEFAULT_RESTARTS,
                 iterations=DEFAULT_ITERATIONS,
                 binary=joint.COARSE_BINARY, chunk_size=BOARD_CHUNK):
    """Return scores with CUDA-cap-sized, path-seed-invariant chunks."""
    paths = np.asarray(paths, dtype=np.uint8)
    if chunk_size < 1:
        raise ValueError("board chunk size must be positive")
    scores = []
    for start in range(0, len(paths), chunk_size):
        chunk_scores, _, _, _ = joint.gpu_multistart_screen(
            binary, blocks, pair, quad, paths[start:start + chunk_size],
            restarts=restarts, iterations=iterations)
        scores.append(chunk_scores)
    return np.concatenate(scores) if scores else np.empty(0, dtype=np.float64)


def run_fixture(fixture_index=15, keep=DEFAULT_KEEP,
                depth6_keep=DEFAULT_DEPTH6_KEEP,
                depth7_keep=DEFAULT_DEPTH7_KEEP,
                depth8_keep=DEFAULT_DEPTH8_KEEP,
                restarts=DEFAULT_RESTARTS,
                iterations=DEFAULT_ITERATIONS,
                depth8_restarts=None,
                depth8_iterations=None,
                prefix_binary=width30.DEFAULT_BINARY,
                board_binary=joint.COARSE_BINARY,
                measure_planted_ceiling=False,
                continue_depth8=True,
                diagnose_true_parent=False,
                models=None,
                refine_depth8=False,
                refine_depth8_keep=8192,
                refine_depth8_restarts=4,
                refine_depth8_iterations=10000,
                probe_depth9=False,
                depth9_keep=262144,
                depth9_restarts=3,
                depth9_iterations=2000,
                rolling_max_depth=9,
                checkpoint_dir=None,
                stop_on_truth_loss=True) -> dict:
    fixture = width30.width30_fixture(fixture_index, "dev")
    if models is None:
        models = width30.train_models()
    blocks = prefix.blocks_from_observed(fixture)
    pair = tuple(fixture["pair"])
    truth = prefix.order_to_sequence(fixture["order"])
    quad, _ = base.load_language_model()
    depth8_restarts = restarts if depth8_restarts is None else depth8_restarts
    depth8_iterations = iterations if depth8_iterations is None else depth8_iterations
    began = time.monotonic()

    paths7, invariant7, prefix_diagnostics = invariant_to_depth7(
        fixture, models, keep, depth6_keep, depth7_keep, prefix_binary)
    invariant_selected7 = recovery_record(
        paths7, invariant7, truth, SWITCH_DEPTH)

    planted7 = None
    if measure_planted_ceiling:
        planted_board = ceiling.planted_board(fixture)
        with ceiling_map.BoardScorer(
                ceiling_map.DEFAULT_BINARY, blocks, pair,
                planted_board, quad) as scorer:
            planted_scores = scorer.score(paths7)
        planted7 = recovery_record(
            paths7, planted_scores, truth, SWITCH_DEPTH)

    stage_began = time.monotonic()
    boards7 = best_restarts7 = None
    if diagnose_true_parent:
        board7, _, boards7, best_restarts7 = joint.gpu_multistart_screen(
            board_binary, blocks, pair, quad, paths7,
            restarts=restarts, iterations=iterations)
    else:
        board7 = board_screen(
            paths7, blocks, pair, quad, restarts, iterations, board_binary)
    board7_seconds = time.monotonic() - stage_began
    learned7 = recovery_record(paths7, board7, truth, SWITCH_DEPTH)

    true_parent_diagnostics = []
    if diagnose_true_parent:
        for index in np.flatnonzero(width30.true_path_mask(
                paths7, truth, SWITCH_DEPTH)):
            parent = paths7[index:index + 1]
            children = width30.expand_bidirectional(parent)
            with joint.BoardScorer(
                    joint.EXTEND_BINARY, blocks, pair,
                    boards7[index], quad) as scorer:
                fixed_scores = scorer.score(children)
            record = recovery_record(children, fixed_scores, truth, 8)
            record.update({
                "parent_path": parent[0].tolist(),
                "parent_board_score": float(board7[index]),
                "parent_best_restart": int(best_restarts7[index]),
                "generated_children": len(children),
            })
            true_parent_diagnostics.append(record)
    paths7, board7, unique7 = width30.select_diverse(
        paths7, board7, keep)
    selected7 = recovery_record(
        paths7, board7, truth, SWITCH_DEPTH, include_best=True)
    selected7.update({"checkpoint": save_checkpoint(
        checkpoint_dir, "depth7_selected", paths7, board7)})

    depth8 = None
    if (continue_depth8 and
            (selected7["true_segments"] or not stop_on_truth_loss)):
        stage_began = time.monotonic()
        paths8 = width30.expand_bidirectional(paths7)
        planted8 = None
        if measure_planted_ceiling:
            planted_board = ceiling.planted_board(fixture)
            with ceiling_map.BoardScorer(
                    ceiling_map.DEFAULT_BINARY, blocks, pair,
                    planted_board, quad) as scorer:
                planted8_scores = scorer.score(paths8)
            planted8 = recovery_record(
                paths8, planted8_scores, truth, 8)
        board8 = board_screen(
            paths8, blocks, pair, quad, depth8_restarts,
            depth8_iterations, board_binary)
        board8_seconds = time.monotonic() - stage_began
        raw8 = recovery_record(paths8, board8, truth, 8)
        paths8, board8, unique8 = width30.select_diverse(
            paths8, board8, depth8_keep)
        selected8 = recovery_record(
            paths8, board8, truth, 8, include_best=True)
        selected8.update({"checkpoint": save_checkpoint(
            checkpoint_dir, "depth8_selected", paths8, board8)})
        strong_refine = None
        depth9_probe = None
        rolling_probe = []
        if (refine_depth8 and
                (selected8["true_segments"] or not stop_on_truth_loss)):
            stage_began = time.monotonic()
            refined8 = board_screen(
                paths8, blocks, pair, quad, refine_depth8_restarts,
                refine_depth8_iterations, board_binary)
            raw_refined8 = recovery_record(paths8, refined8, truth, 8)
            selected_refine_paths, selected_refine_scores, refine_unique = (
                width30.select_diverse(
                    paths8, refined8, refine_depth8_keep))
            strong_refine = {
                "restarts": refine_depth8_restarts,
                "iterations": refine_depth8_iterations,
                "keep": refine_depth8_keep,
                "generated_unique": refine_unique,
                "before_selection": raw_refined8,
                "after_selection": recovery_record(
                    selected_refine_paths, selected_refine_scores, truth, 8,
                    include_best=True),
                "board_screen_seconds": time.monotonic() - stage_began,
            }
            strong_refine["after_selection"].update({
                "checkpoint": save_checkpoint(
                    checkpoint_dir, "depth8_strong_selected",
                    selected_refine_paths, selected_refine_scores)})
            if (probe_depth9 and
                    (strong_refine["after_selection"]["true_segments"] or
                     not stop_on_truth_loss)):
                rolling_paths = selected_refine_paths
                for target_depth in range(9, rolling_max_depth + 1):
                    stage_began = time.monotonic()
                    generated = width30.expand_bidirectional(rolling_paths)
                    generated_scores = board_screen(
                        generated, blocks, pair, quad, depth9_restarts,
                        depth9_iterations, board_binary)
                    before = recovery_record(
                        generated, generated_scores, truth, target_depth)
                    rolling_paths, rolling_scores, unique = (
                        width30.select_diverse(
                            generated, generated_scores, depth9_keep))
                    after = recovery_record(
                        rolling_paths, rolling_scores, truth, target_depth,
                        include_best=True)
                    after.update({"checkpoint": save_checkpoint(
                        checkpoint_dir, f"depth{target_depth}_selected",
                        rolling_paths, rolling_scores)})
                    record = {
                        "depth": target_depth,
                        "restarts": depth9_restarts,
                        "iterations": depth9_iterations,
                        "keep": depth9_keep,
                        "generated_unique": unique,
                        "before_selection": before,
                        "after_selection": after,
                        "board_screen_seconds": time.monotonic() - stage_began,
                    }
                    rolling_probe.append(record)
                    if target_depth == 9:
                        depth9_probe = record
                    if (stop_on_truth_loss and
                            not record["after_selection"]["true_segments"]):
                        break
        depth8 = {
            "generated_unique": unique8,
            "planted_board_ceiling": planted8,
            "board_objective_before_selection": raw8,
            "after_board_selection": selected8,
            "board_screen_seconds": board8_seconds,
            "strong_refine": strong_refine,
            "depth9_probe": depth9_probe,
            "rolling_probe": rolling_probe,
        }

    return {
        "phase": "484Z",
        "status": "development_width30_early_board_switch_not_frozen",
        "faed_scored": False,
        "holdout_consumed": False,
        "fixture_index": fixture_index,
        "width": width30.WIDTH,
        "switch_depth": SWITCH_DEPTH,
        "invariant_keep": keep,
        "depth6_keep": depth6_keep,
        "depth7_keep": depth7_keep,
        "depth8_keep": depth8_keep,
        "board_restarts": restarts,
        "board_iterations": iterations,
        "depth8_board_restarts": depth8_restarts,
        "depth8_board_iterations": depth8_iterations,
        "continue_depth8": continue_depth8,
        "diagnose_true_parent": diagnose_true_parent,
        "refine_depth8": refine_depth8,
        "probe_depth9": probe_depth9,
        "rolling_max_depth": rolling_max_depth,
        "checkpoint_dir": str(checkpoint_dir) if checkpoint_dir else None,
        "stop_on_truth_loss": stop_on_truth_loss,
        "exact_profile_fixture": width30.exact.fixture_summary(fixture),
        "prefix_diagnostics": prefix_diagnostics,
        "depth7": {
            "generated_unique": unique7,
            "after_invariant_selection": invariant_selected7,
            "planted_board_ceiling": planted7,
            "board_objective_before_selection": learned7,
            "after_board_selection": selected7,
            "true_parent_inherited_board_diagnostics": true_parent_diagnostics,
            "board_screen_seconds": board7_seconds,
        },
        "depth8": depth8,
        "survived_depth8": bool(depth8 and
                                depth8["after_board_selection"]["true_segments"]),
        "wall_seconds": time.monotonic() - began,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--fixture-index", type=int, default=15)
    parser.add_argument("--keep", type=int, default=DEFAULT_KEEP)
    parser.add_argument("--depth6-keep", type=int, default=DEFAULT_DEPTH6_KEEP)
    parser.add_argument("--depth7-keep", type=int, default=DEFAULT_DEPTH7_KEEP)
    parser.add_argument("--depth8-keep", type=int, default=DEFAULT_DEPTH8_KEEP)
    parser.add_argument("--restarts", type=int, default=DEFAULT_RESTARTS)
    parser.add_argument("--iterations", type=int, default=DEFAULT_ITERATIONS)
    parser.add_argument("--depth8-restarts", type=int)
    parser.add_argument("--depth8-iterations", type=int)
    parser.add_argument("--prefix-binary", type=Path,
                        default=width30.DEFAULT_BINARY)
    parser.add_argument("--board-binary", type=Path,
                        default=joint.COARSE_BINARY)
    parser.add_argument("--measure-planted-ceiling", action="store_true")
    parser.add_argument("--stop-after-depth7", action="store_true")
    parser.add_argument("--diagnose-true-parent", action="store_true")
    parser.add_argument("--refine-depth8", action="store_true")
    parser.add_argument("--refine-depth8-keep", type=int, default=8192)
    parser.add_argument("--refine-depth8-restarts", type=int, default=4)
    parser.add_argument("--refine-depth8-iterations", type=int, default=10000)
    parser.add_argument("--probe-depth9", action="store_true")
    parser.add_argument("--depth9-keep", type=int, default=262144)
    parser.add_argument("--depth9-restarts", type=int, default=3)
    parser.add_argument("--depth9-iterations", type=int, default=2000)
    parser.add_argument("--rolling-max-depth", type=int, default=9)
    parser.add_argument("--checkpoint-dir", type=Path)
    parser.add_argument("--continue-after-truth-loss", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.run:
        parser.error("use --run")
    result = run_fixture(
        args.fixture_index, args.keep, args.depth6_keep, args.depth7_keep,
        args.depth8_keep, args.restarts, args.iterations,
        args.depth8_restarts, args.depth8_iterations,
        args.prefix_binary, args.board_binary, args.measure_planted_ceiling,
        not args.stop_after_depth7, args.diagnose_true_parent, None,
        args.refine_depth8, args.refine_depth8_keep,
        args.refine_depth8_restarts, args.refine_depth8_iterations,
        args.probe_depth9, args.depth9_keep, args.depth9_restarts,
        args.depth9_iterations, args.rolling_max_depth,
        args.checkpoint_dir, not args.continue_after_truth_loss)
    output = args.output or SCRIPT_DIR / (
        f"phase484z_width30_early_switch_i{args.fixture_index}_"
        f"d6k{args.depth6_keep}_d7k{args.depth7_keep}_"
        f"r{args.restarts}_n{args.iterations}.json")
    output.write_text(json.dumps(result, indent=2) + "\n")
    d7 = result["depth7"]
    print("depth7 true ranks invariant/board/selected",
          d7["after_invariant_selection"]["best_true_rank"],
          d7["board_objective_before_selection"]["best_true_rank"],
          d7["after_board_selection"]["best_true_rank"])
    if result["depth8"]:
        print("depth8 true rank/selected",
              result["depth8"]["board_objective_before_selection"]["best_true_rank"],
              result["depth8"]["after_board_selection"]["best_true_rank"])
        if result["depth8"]["strong_refine"]:
            refined = result["depth8"]["strong_refine"]
            print("depth8 strong-refine true rank/selected",
                  refined["before_selection"]["best_true_rank"],
                  refined["after_selection"]["best_true_rank"])
        if result["depth8"]["depth9_probe"]:
            depth9 = result["depth8"]["depth9_probe"]
            print("depth9 true rank/selected",
                  depth9["before_selection"]["best_true_rank"],
                  depth9["after_selection"]["best_true_rank"])
        for record in result["depth8"]["rolling_probe"][1:]:
            print(f"depth{record['depth']} true rank/selected",
                  record["before_selection"]["best_true_rank"],
                  record["after_selection"]["best_true_rank"])
    print("survived depth8", result["survived_depth8"],
          "wall", round(result["wall_seconds"], 3))
    print("wrote", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
