#!/usr/bin/env python3
"""Development probe: move the invariant->board-objective switch to depth 6.

Phase 484Z/AC/AF's pipeline scores depths 4-7 with a permutation-invariant
order statistic, then switches to GPU board-annealed scoring at depth 7
(SWITCH_DEPTH=7). A per-depth true-rank trace on fixture 22 showed the
invariant score's discriminative signal erodes steadily and multiplicatively
through depths 4-7 (roughly 10x worse in percentile terms per depth), and a
484AG follow-up showed parent-reservation cannot rescue it there -- the local
signal is genuinely too weak, not just globally unlucky. Since depth 6's raw
invariant rank was still moderately close (55,156 of ~524k kept, well inside
any 1M-scale preboard cut), this probe tests whether switching to the board
objective one depth earlier -- at depth 6 instead of depth 7 -- keeps the true
window alive further than the current depth-7 switch does, for fixtures that
currently fail. It imports no FAED ciphertext and does not use holdout
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
import phase484z_width30_early_board_switch_probe as switch
import phase484ac_width30_partition_constrained_board_probe as constrained

SCRIPT_DIR = Path(__file__).resolve().parent
SWITCH_DEPTH = 6
KEEP_EARLY = 262144
KEEP_PENULTIMATE = 524288
KEEP_PREBOARD = 1048576
KEEP_BOARD = 262144
KEEP_NEXT_COARSE = 1310720
RESTARTS = 3
ITERATIONS = 2000


def invariant_to_switch_depth(fixture, models, switch_depth,
                              keep_early=KEEP_EARLY,
                              keep_penultimate=KEEP_PENULTIMATE,
                              keep_preboard=KEEP_PREBOARD,
                              binary=width30.DEFAULT_BINARY):
    """Generalizes 484Z's invariant_to_depth7 to an arbitrary switch depth.

    Mirrors the original schedule's keep magnitudes, shifted so the
    second-to-last invariant depth uses keep_penultimate and the final
    invariant selection (at switch_depth itself) uses keep_preboard."""
    blocks = prefix.blocks_from_observed(fixture)
    pair = tuple(fixture["pair"])
    paths = width30.initial_paths(width30.START_DEPTH)
    with width30.GpuWidth30Scorer(
            binary, blocks, pair, models[width30.START_DEPTH]) as scorer:
        scores = width30.score_chunked(scorer, paths)
    diagnostics = []
    for depth in range(width30.START_DEPTH, switch_depth):
        capacity = keep_penultimate if depth == switch_depth - 1 else keep_early
        paths, scores, unique_count = width30.select_diverse(
            paths, scores, capacity)
        diagnostics.append({"depth": depth, "generated_unique": unique_count,
                            "retained": len(paths)})
        paths = width30.expand_bidirectional(paths)
        with width30.GpuWidth30Scorer(
                binary, blocks, pair, models[depth + 1]) as scorer:
            scores = width30.score_chunked(scorer, paths)
    paths, scores, unique_count = width30.select_diverse(
        paths, scores, keep_preboard)
    diagnostics.append({"depth": switch_depth, "generated_unique": unique_count,
                        "retained": len(paths)})
    return paths, scores, diagnostics, blocks, pair


def run(fixture_index=22, switch_depth=SWITCH_DEPTH,
        keep_board=KEEP_BOARD, keep_next_coarse=KEEP_NEXT_COARSE,
        restarts=RESTARTS, iterations=ITERATIONS,
        board_binary=constrained.GPU_BINARY,
        prefix_binary=width30.DEFAULT_BINARY, models=None) -> dict:
    fixture = width30.width30_fixture(fixture_index, "dev")
    if models is None:
        models = width30.train_models()
    truth = prefix.order_to_sequence(fixture["order"])
    quad, _ = base.load_language_model()
    began = time.monotonic()

    paths_sw, invariant_sw, prefix_diagnostics, blocks, pair = (
        invariant_to_switch_depth(fixture, models, switch_depth,
                                  binary=prefix_binary))
    invariant_selected = switch.recovery_record(
        paths_sw, invariant_sw, truth, switch_depth)

    stage_began = time.monotonic()
    board_sw = switch.board_screen(
        paths_sw, blocks, pair, quad, restarts, iterations, board_binary)
    board_seconds = time.monotonic() - stage_began
    board_raw = switch.recovery_record(paths_sw, board_sw, truth, switch_depth)
    paths_sw, board_sw, unique_sw = width30.select_diverse(
        paths_sw, board_sw, keep_board)
    board_selected = switch.recovery_record(paths_sw, board_sw, truth, switch_depth)

    next_depth = switch_depth + 1
    next_stage = None
    if board_selected["true_segments"]:
        stage_began = time.monotonic()
        paths_next = width30.expand_bidirectional(paths_sw)
        scores_next = switch.board_screen(
            paths_next, blocks, pair, quad, restarts, iterations, board_binary)
        next_raw = switch.recovery_record(paths_next, scores_next, truth, next_depth)
        paths_next, scores_next, unique_next = width30.select_diverse(
            paths_next, scores_next, keep_next_coarse)
        next_selected = switch.recovery_record(
            paths_next, scores_next, truth, next_depth)
        next_stage = {
            "depth": next_depth,
            "generated_unique": unique_next,
            "before_selection": next_raw,
            "after_selection": next_selected,
            "keep": keep_next_coarse,
            "board_screen_seconds": time.monotonic() - stage_began,
        }

    return {
        "phase": "484AH",
        "status": "development_early_switch_depth_probe_not_frozen",
        "faed_scored": False,
        "holdout_consumed": False,
        "fixture_index": fixture_index,
        "switch_depth": switch_depth,
        "keep_board": keep_board,
        "keep_next_coarse": keep_next_coarse,
        "restarts": restarts,
        "iterations": iterations,
        "prefix_diagnostics": prefix_diagnostics,
        "switch_stage": {
            "after_invariant_selection": invariant_selected,
            "board_objective_before_selection": board_raw,
            "after_board_selection": board_selected,
            "board_screen_seconds": board_seconds,
        },
        "next_stage": next_stage,
        "survived_switch_depth": bool(board_selected["true_segments"]),
        "survived_next_depth": bool(next_stage and
                                    next_stage["after_selection"]["true_segments"]),
        "wall_seconds": time.monotonic() - began,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--fixture-index", type=int, default=22)
    parser.add_argument("--switch-depth", type=int, default=SWITCH_DEPTH)
    parser.add_argument("--keep-board", type=int, default=KEEP_BOARD)
    parser.add_argument("--keep-next-coarse", type=int,
                        default=KEEP_NEXT_COARSE)
    parser.add_argument("--restarts", type=int, default=RESTARTS)
    parser.add_argument("--iterations", type=int, default=ITERATIONS)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.run:
        parser.error("use --run")
    result = run(args.fixture_index, args.switch_depth, args.keep_board,
                 args.keep_next_coarse, args.restarts, args.iterations)
    output = args.output or SCRIPT_DIR / (
        f"phase484ah_width30_early_switch_i{args.fixture_index}_"
        f"sd{args.switch_depth}.json")
    output.write_text(json.dumps(result, indent=2) + "\n")
    print("switch_stage", result["switch_stage"])
    print("next_stage", result["next_stage"])
    print("survived_switch_depth", result["survived_switch_depth"],
          "survived_next_depth", result["survived_next_depth"])
    print("wall", round(result["wall_seconds"], 3), "wrote", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
