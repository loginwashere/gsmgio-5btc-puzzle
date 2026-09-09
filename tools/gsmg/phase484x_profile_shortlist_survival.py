#!/usr/bin/env python3
"""Depth-localize exact-profile truth loss in the invariant shortlist."""
from __future__ import annotations

import argparse
import itertools
import json
import time
from pathlib import Path

import numpy as np

import phase484j_constructive_prefix_beam_probe as prefix
import phase484k_bidirectional_segment_assembly_probe as bidi
import phase484n_gpu_width19_beam_probe as gpu_beam
import phase484q_blind_joint_width19_solver as solver
import phase484x_exact_faed_profile_power_probe as exact

SCRIPT_DIR = Path(__file__).resolve().parent


def run(fixture_index=14, keep=262144):
    fixture = exact.make_fixture(fixture_index)
    models = exact.train_profile_models()
    blocks = prefix.blocks_from_observed(fixture)
    truth = prefix.order_to_sequence(fixture["order"])
    paths = list(itertools.permutations(range(solver.WIDTH),
                                        prefix.START_DEPTH))
    beam = None
    diagnostics = []
    began = time.monotonic()
    for depth in range(prefix.START_DEPTH, solver.DEPTH + 1):
        if depth > prefix.START_DEPTH:
            paths = gpu_beam.expand_bidirectional(beam, solver.WIDTH)
        scores = gpu_beam.score_paths(
            solver.DEFAULT_BINARY, blocks, exact.PAIR, models[depth], paths)
        genuine = bidi.true_windows(truth, depth)
        true_indices = [index for index, path in enumerate(paths)
                        if path in genuine]
        ranked_indices = np.lexsort((np.arange(len(scores)), -scores))
        ranks = np.empty(len(scores), dtype=np.int64)
        ranks[ranked_indices] = np.arange(1, len(scores) + 1)
        beam = gpu_beam.select_diverse_arrays(
            paths, scores, solver.WIDTH, keep)
        retained = [(rank, path) for rank, (_, path) in enumerate(beam, 1)
                    if path in genuine]
        diagnostics.append({
            "depth": depth,
            "generated": len(paths),
            "true_candidates_generated": len(true_indices),
            "best_true_raw_score_rank": min(
                (int(ranks[index]) for index in true_indices), default=None),
            "worst_true_raw_score_rank": max(
                (int(ranks[index]) for index in true_indices), default=None),
            "beam_size": len(beam),
            "true_segments_retained": len(retained),
            "best_true_post_selection_rank": min(
                (rank for rank, _ in retained), default=None),
        })
        if not retained:
            break
    return {
        "phase": "484X",
        "status": "development_exact_profile_shortlist_survival",
        "fixture_index": fixture_index,
        "train_indices": list(exact.PROFILE_TRAIN_INDICES),
        "keep": keep,
        "depth_diagnostics": diagnostics,
        "truth_survived_depth8": (
            diagnostics[-1]["depth"] == solver.DEPTH and
            diagnostics[-1]["true_segments_retained"] > 0),
        "wall_seconds": time.monotonic() - began,
    }


def self_test():
    if solver.DEPTH != 8 or prefix.START_DEPTH != 4:
        raise AssertionError("unexpected shortlist depth range")
    if 14 in exact.PROFILE_TRAIN_INDICES:
        raise AssertionError("default evaluation fixture leaks into training")
    return {"start_depth": 4, "stop_depth": 8}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--fixture-index", type=int, default=14)
    parser.add_argument("--keep", type=int, default=262144)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), indent=2))
        return 0
    if not args.run:
        parser.error("use --self-test or --run")
    result = run(args.fixture_index, args.keep)
    output = args.output or SCRIPT_DIR / (
        f"phase484x_survival_i{args.fixture_index}_k{args.keep}.json")
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    print("wrote", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
