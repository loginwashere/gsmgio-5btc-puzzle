#!/usr/bin/env python3
"""Development probe: local vs. global rank at the width-30 depth-10->11 cliff.

Phase 484AC's rolling probe showed the true depth-10 fragment ranks strongly
(45,288th of ~10.6M before selection) and survives, then its depth-11 child
collapses to global rank 1,174,176 of ~10.1M and is cut. That is consistent
with two different explanations: (a) the true depth-10 lineage has genuinely
gone cold (no good depth-11 continuation exists under the board objective), or
(b) the true child is still locally strong among its own parent's ~2*(30-10)
bidirectional extensions, but loses a one-shot global contest against many
unrelated depth-11 candidates descended from other (false) depth-10 parents.

This probe reconstructs the exact depth-10 selected population using Phase
484AC's own pipeline stages, then scores ONLY the true depth-10 parent's own
local children (both true and false) with the identical board-objective seed
scheme, and reports the true child's LOCAL rank alongside its already-known
GLOBAL rank. A small local rank would support a cheap, principled fix: reserve
a few beam slots per surviving parent (not just per global top-K cut) at each
extension step. It imports no FAED ciphertext and does not use holdout
fixtures.
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
import phase484z_width30_early_board_switch_probe as switch

SCRIPT_DIR = Path(__file__).resolve().parent
CLIFF_DEPTH = 11


def rebuild_depth10_population(fixture, models, quad, blocks, pair, truth,
                               keep, depth6_keep, depth7_keep, depth8_keep,
                               restarts, iterations,
                               depth8_restarts, depth8_iterations,
                               refine_restarts, refine_iterations, refine_keep,
                               rolling_restarts, rolling_iterations, rolling_keep,
                               prefix_binary, board_binary) -> dict:
    """Replay Phase 484AC's own stages, keeping every intermediate population
    and its true-fragment recovery record, so a divergence from the original
    484AC run can be localized to a specific stage instead of only observed
    at the final depth-10 population."""
    stages = {}
    recovery = {}
    paths7, invariant7, prefix_diagnostics = switch.invariant_to_depth7(
        fixture, models, keep, depth6_keep, depth7_keep, prefix_binary)
    recovery["depth7_invariant"] = switch.recovery_record(
        paths7, invariant7, truth, 7)
    board7 = switch.board_screen(
        paths7, blocks, pair, quad, restarts, iterations, board_binary)
    recovery["depth7_board_raw"] = switch.recovery_record(
        paths7, board7, truth, 7)
    paths7, board7, _ = width30.select_diverse(paths7, board7, keep)
    recovery["depth7_selected"] = switch.recovery_record(
        paths7, board7, truth, 7)
    stages["depth7_selected"] = (paths7, board7)

    paths8 = width30.expand_bidirectional(paths7)
    board8 = switch.board_screen(
        paths8, blocks, pair, quad, depth8_restarts, depth8_iterations,
        board_binary)
    recovery["depth8_board_raw"] = switch.recovery_record(
        paths8, board8, truth, 8)
    paths8, board8, _ = width30.select_diverse(paths8, board8, depth8_keep)
    recovery["depth8_selected"] = switch.recovery_record(
        paths8, board8, truth, 8)
    stages["depth8_selected"] = (paths8, board8)

    refined8 = switch.board_screen(
        paths8, blocks, pair, quad, refine_restarts, refine_iterations,
        board_binary)
    recovery["depth8_refined_raw"] = switch.recovery_record(
        paths8, refined8, truth, 8)
    refined_paths, refined_scores, _ = width30.select_diverse(
        paths8, refined8, refine_keep)
    recovery["depth8_refined_selected"] = switch.recovery_record(
        refined_paths, refined_scores, truth, 8)
    stages["depth8_refined"] = (refined_paths, refined_scores)

    rolling_paths, rolling_scores = refined_paths, refined_scores
    for target_depth in range(9, 11):
        generated = width30.expand_bidirectional(rolling_paths)
        generated_scores = switch.board_screen(
            generated, blocks, pair, quad, rolling_restarts,
            rolling_iterations, board_binary)
        recovery[f"depth{target_depth}_raw"] = switch.recovery_record(
            generated, generated_scores, truth, target_depth)
        rolling_paths, rolling_scores, _ = width30.select_diverse(
            generated, generated_scores, rolling_keep)
        recovery[f"depth{target_depth}_selected"] = switch.recovery_record(
            rolling_paths, rolling_scores, truth, target_depth)
        stages[f"depth{target_depth}_selected"] = (rolling_paths, rolling_scores)
    return stages, recovery


def local_rank_diagnostic(depth10_paths, depth10_scores, truth, blocks, pair,
                          quad, restarts, iterations, board_binary) -> dict:
    true_mask = width30.true_path_mask(depth10_paths, truth, 10)
    true_indices = np.flatnonzero(true_mask)
    global_true_rank = None
    if len(true_indices):
        order = width30.ranked_indices(depth10_paths, depth10_scores)
        rank_of = {int(idx): position + 1 for position, idx in enumerate(order)}
        global_true_rank = min(rank_of[int(i)] for i in true_indices)

    records = []
    for parent_index in true_indices:
        parent = depth10_paths[parent_index:parent_index + 1]
        children = width30.expand_bidirectional(parent)
        child_scores = switch.board_screen(
            children, blocks, pair, quad, restarts, iterations, board_binary)
        child_true_mask = width30.true_path_mask(children, truth, CLIFF_DEPTH)
        child_order = width30.ranked_indices(children, child_scores)
        local_rank_of = {int(idx): position + 1
                         for position, idx in enumerate(child_order)}
        true_child_local_ranks = [local_rank_of[int(i)]
                                  for i in np.flatnonzero(child_true_mask)]
        records.append({
            "parent_path": parent[0].tolist(),
            "parent_depth10_global_score": float(depth10_scores[parent_index]),
            "parent_depth10_global_rank_among_10.6m": global_true_rank,
            "local_child_count": len(children),
            "local_true_child_count": int(child_true_mask.sum()),
            "true_child_local_ranks": sorted(true_child_local_ranks),
            "best_true_child_local_score": float(
                child_scores[child_true_mask].max())
            if child_true_mask.any() else None,
            "best_false_child_local_score": float(
                child_scores[~child_true_mask].max())
            if (~child_true_mask).any() else None,
            "local_score_gap_true_minus_best_false": (
                float(child_scores[child_true_mask].max() -
                     child_scores[~child_true_mask].max())
                if child_true_mask.any() and (~child_true_mask).any() else None),
        })
    return {
        "depth10_population_size": len(depth10_paths),
        "depth10_true_parent_count": len(true_indices),
        "records": records,
    }


def run(fixture_index=15, keep=width30.DEFAULT_KEEP,
        depth6_keep=width30.DEFAULT_DEPTH6_KEEP,
        depth7_keep=width30.DEFAULT_DEPTH7_KEEP,
        depth8_keep=1310720, restarts=3, iterations=2000,
        depth8_restarts=3, depth8_iterations=2000,
        refine_restarts=4, refine_iterations=10000, refine_keep=262144,
        rolling_restarts=3, rolling_iterations=2000, rolling_keep=262144,
        local_restarts=3, local_iterations=2000,
        prefix_binary=width30.DEFAULT_BINARY,
        board_binary=joint.COARSE_BINARY,
        models=None) -> dict:
    fixture = width30.width30_fixture(fixture_index, "dev")
    if models is None:
        models = width30.train_models()
    blocks = prefix.blocks_from_observed(fixture)
    pair = tuple(fixture["pair"])
    truth = prefix.order_to_sequence(fixture["order"])
    quad, _ = base.load_language_model()
    began = time.monotonic()

    stages, recovery = rebuild_depth10_population(
        fixture, models, quad, blocks, pair, truth, keep, depth6_keep,
        depth7_keep, depth8_keep, restarts, iterations, depth8_restarts,
        depth8_iterations, refine_restarts, refine_iterations, refine_keep,
        rolling_restarts, rolling_iterations, rolling_keep,
        prefix_binary, board_binary)
    rebuild_seconds = time.monotonic() - began

    depth10_paths, depth10_scores = stages["depth10_selected"]
    diagnostic_began = time.monotonic()
    diagnostic = local_rank_diagnostic(
        depth10_paths, depth10_scores, truth, blocks, pair, quad,
        local_restarts, local_iterations, board_binary)
    diagnostic_seconds = time.monotonic() - diagnostic_began

    stage_sizes = {name: len(paths) for name, (paths, _) in stages.items()}
    return {
        "phase": "484AD",
        "status": "development_width30_local_rank_cliff_diagnostic_not_frozen",
        "faed_scored": False,
        "holdout_consumed": False,
        "fixture_index": fixture_index,
        "width": width30.WIDTH,
        "cliff_depth": CLIFF_DEPTH,
        "pipeline_params": {
            "keep": keep, "depth6_keep": depth6_keep,
            "depth7_keep": depth7_keep, "depth8_keep": depth8_keep,
            "restarts": restarts, "iterations": iterations,
            "depth8_restarts": depth8_restarts,
            "depth8_iterations": depth8_iterations,
            "refine_restarts": refine_restarts,
            "refine_iterations": refine_iterations,
            "refine_keep": refine_keep,
            "rolling_restarts": rolling_restarts,
            "rolling_iterations": rolling_iterations,
            "rolling_keep": rolling_keep,
            "local_restarts": local_restarts,
            "local_iterations": local_iterations,
        },
        "stage_sizes": stage_sizes,
        "recovery_by_stage": recovery,
        "local_rank_diagnostic": diagnostic,
        "rebuild_seconds": rebuild_seconds,
        "diagnostic_seconds": diagnostic_seconds,
        "wall_seconds": time.monotonic() - began,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--fixture-index", type=int, default=15)
    parser.add_argument("--depth8-keep", type=int, default=1310720)
    parser.add_argument("--restarts", type=int, default=3)
    parser.add_argument("--iterations", type=int, default=2000)
    parser.add_argument("--refine-restarts", type=int, default=4)
    parser.add_argument("--refine-iterations", type=int, default=10000)
    parser.add_argument("--refine-keep", type=int, default=262144)
    parser.add_argument("--rolling-restarts", type=int, default=3)
    parser.add_argument("--rolling-iterations", type=int, default=2000)
    parser.add_argument("--rolling-keep", type=int, default=262144)
    parser.add_argument("--local-restarts", type=int, default=3)
    parser.add_argument("--local-iterations", type=int, default=2000)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.run:
        parser.error("use --run")
    result = run(
        args.fixture_index, depth8_keep=args.depth8_keep,
        restarts=args.restarts, iterations=args.iterations,
        depth8_restarts=args.restarts, depth8_iterations=args.iterations,
        refine_restarts=args.refine_restarts,
        refine_iterations=args.refine_iterations,
        refine_keep=args.refine_keep,
        rolling_restarts=args.rolling_restarts,
        rolling_iterations=args.rolling_iterations,
        rolling_keep=args.rolling_keep,
        local_restarts=args.local_restarts,
        local_iterations=args.local_iterations)
    output = args.output or SCRIPT_DIR / (
        f"phase484ad_width30_local_rank_i{args.fixture_index}_"
        f"cliff{CLIFF_DEPTH}.json")
    output.write_text(json.dumps(result, indent=2) + "\n")
    print("stage sizes", result["stage_sizes"])
    for name, record in result["recovery_by_stage"].items():
        print(f"  {name}: true_segments={record['true_segments']} "
              f"best_true_rank={record['best_true_rank']}")
    diagnostic = result["local_rank_diagnostic"]
    print("depth10 true parent count", diagnostic["depth10_true_parent_count"])
    for record in diagnostic["records"]:
        print("local rank of true child(ren) among",
              record["local_child_count"], "siblings:",
              record["true_child_local_ranks"],
              "gap true-best_false", record["local_score_gap_true_minus_best_false"])
    print("rebuild", round(result["rebuild_seconds"], 1),
          "diagnostic", round(result["diagnostic_seconds"], 1),
          "wall", round(result["wall_seconds"], 1))
    print("wrote", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
