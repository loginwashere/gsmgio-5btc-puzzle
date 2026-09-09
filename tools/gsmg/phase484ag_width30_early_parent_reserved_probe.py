#!/usr/bin/env python3
"""Development probe: parent-reserved bridging applied to the early
depth-6->7 invariant-selection step, not just the depth-10->11 board step.

Phase 484AF's fixed-schedule generalization test showed fixtures 19/21/22 all
lose their true depth-7 window at the very first invariant-score selection
cut, well before Phase 484AD's depth-10->11 bridge is ever reached. A direct
per-depth true-rank trace (fixture 22) shows this is NOT the same failure
shape as fixture 15's depth-10->11 cliff: the true window's rank erodes
steadily across depths 4->7 (roughly 10x worse in percentile terms at each
step) rather than collapsing in one noisy step after being consistently
strong. A follow-up check found the true depth-7 extension still ranks only
mid-pack (5th-24th of 48) among its own true depth-6 parent's local children
-- a real but much weaker local signal than fixture 15's cliff case.

This probe tests whether restricting reservation to the TOP-SCORED depth-6
parents (mirroring how 484AD's bridge actually narrowed its parent set, not a
blanket per-parent reservation over all survivors) can still rescue the true
depth-7 window despite that weaker local signal. It imports no FAED
ciphertext and does not use holdout fixtures.
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
import phase484ad_width30_parent_reserved_bridge as bridge

SCRIPT_DIR = Path(__file__).resolve().parent
PARENT_DEPTH = 6
PARENT_KEEP = 65536
CHILDREN_PER_PARENT = 16
DEPTH7_KEEP = 1048576


def depth6_population(fixture, models):
    blocks = prefix.blocks_from_observed(fixture)
    pair = tuple(fixture["pair"])
    paths = width30.initial_paths(width30.START_DEPTH)
    with width30.GpuWidth30Scorer(
            width30.DEFAULT_BINARY, blocks, pair,
            models[width30.START_DEPTH]) as scorer:
        scores = width30.score_chunked(scorer, paths)
    for depth in range(width30.START_DEPTH, PARENT_DEPTH):
        paths, scores, _ = width30.select_diverse(paths, scores, 262144)
        paths = width30.expand_bidirectional(paths)
        with width30.GpuWidth30Scorer(
                width30.DEFAULT_BINARY, blocks, pair,
                models[depth + 1]) as scorer:
            scores = width30.score_chunked(scorer, paths)
    paths, scores, _ = width30.select_diverse(paths, scores, 524288)
    return paths, scores, blocks, pair


def run(fixture_index=22, parent_keep=PARENT_KEEP,
        children_per_parent=CHILDREN_PER_PARENT,
        depth7_keep=DEPTH7_KEEP, models=None) -> dict:
    fixture = width30.width30_fixture(fixture_index, "dev")
    if models is None:
        models = width30.train_models()
    truth = prefix.order_to_sequence(fixture["order"])
    began = time.monotonic()

    paths6, scores6, blocks, pair = depth6_population(fixture, models)
    depth6_record = switch.recovery_record(paths6, scores6, truth, PARENT_DEPTH)

    ranked = width30.ranked_indices(paths6, scores6)
    ranked = ranked[:min(parent_keep, len(ranked))]
    parents = paths6[ranked]
    parent_true_mask = width30.true_path_mask(parents, truth, PARENT_DEPTH)

    children7, parent_indices = bridge.expand_with_parent_indices(parents)
    with width30.GpuWidth30Scorer(
            width30.DEFAULT_BINARY, blocks, pair, models[7]) as scorer:
        scores7 = width30.score_chunked(scorer, children7)
    before7 = switch.recovery_record(children7, scores7, truth, 7)

    reserved7, reserved_scores7 = bridge.reserve_local_children(
        children7, scores7, parent_indices, children_per_parent)
    after_reservation7 = switch.recovery_record(reserved7, reserved_scores7, truth, 7)

    final7, final_scores7, unique7 = width30.select_diverse(
        reserved7, reserved_scores7, depth7_keep)
    after_selection7 = switch.recovery_record(final7, final_scores7, truth, 7)

    return {
        "phase": "484AG",
        "status": "development_early_parent_reserved_bridge_not_frozen",
        "faed_scored": False,
        "holdout_consumed": False,
        "fixture_index": fixture_index,
        "parent_depth": PARENT_DEPTH,
        "parent_keep": len(parents),
        "parent_true_count_in_reserved_set": int(parent_true_mask.sum()),
        "children_per_parent": children_per_parent,
        "depth7_keep": depth7_keep,
        "depth6": depth6_record,
        "depth7": {
            "before_reservation": before7,
            "after_reservation": after_reservation7,
            "generated_unique_after_selection": unique7,
            "after_selection": after_selection7,
        },
        "wall_seconds": time.monotonic() - began,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--fixture-index", type=int, default=22)
    parser.add_argument("--parent-keep", type=int, default=PARENT_KEEP)
    parser.add_argument("--children-per-parent", type=int,
                        default=CHILDREN_PER_PARENT)
    parser.add_argument("--depth7-keep", type=int, default=DEPTH7_KEEP)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.run:
        parser.error("use --run")
    result = run(args.fixture_index, args.parent_keep,
                 args.children_per_parent, args.depth7_keep)
    output = args.output or SCRIPT_DIR / (
        f"phase484ag_width30_early_bridge_i{args.fixture_index}.json")
    output.write_text(json.dumps(result, indent=2) + "\n")
    print("depth6", result["depth6"])
    print("parent_true_count_in_reserved_set",
          result["parent_true_count_in_reserved_set"])
    print("depth7 before/after_reservation/after_selection",
          result["depth7"]["before_reservation"],
          result["depth7"]["after_reservation"],
          result["depth7"]["after_selection"])
    print("wall", round(result["wall_seconds"], 3), "wrote", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
