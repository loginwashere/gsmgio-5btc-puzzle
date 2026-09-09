#!/usr/bin/env python3
"""Development-only 36-way escape-pair screen for the width-19 solver."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import phase484q_blind_joint_width19_solver as solver

SCRIPT_DIR = Path(__file__).resolve().parent
KEEP = 16384
REFINE_KEEP = 64


def compact(result):
    return {
        "hypothesis_pair_index": result["hypothesis_pair_index"],
        "hypothesis_pair": result["hypothesis_pair"],
        "hypothesis_is_true_pair": result["hypothesis_is_true_pair"],
        "best_refined_normalized_score": result["best_refined_normalized_score"],
        "true_segments_retained": result["true_segments_retained"],
        "best_true_coarse_rank": result["best_true_coarse_rank"],
        "best_true_refined_rank": result["best_true_refined_rank"],
        "shortlist_seconds": result["shortlist_seconds"],
        "gpu_screen_seconds": result["gpu_screen_seconds"],
        "gpu_refine_seconds": result["gpu_refine_seconds"],
    }


def rank_pairs(cells):
    ranked = sorted(cells, key=lambda cell:
                    (-cell["best_refined_normalized_score"],
                     cell["hypothesis_pair_index"]))
    for rank, cell in enumerate(ranked, 1):
        cell["pair_screen_rank"] = rank
    return ranked


def run(mode, fixture_index, output):
    began = time.monotonic()
    artifact = {
        "phase": "484S",
        "status": "development_unknown_pair_screen_in_progress_not_frozen",
        "faed_scored": False,
        "holdout_consumed": False,
        "board_mode": mode,
        "fixture_index": fixture_index,
        "true_pair_index": solver.learned.PAIR_INDEX,
        "screen_budgets": {"shortlist": KEEP, "refine_keep": REFINE_KEEP,
                           "extension_seed_count": 0},
        "cells": [],
    }
    for pair_index in range(len(solver.base.ESCAPE_PAIRS)):
        result = solver.screen_fixture(
            mode, fixture_index, keep=KEEP, refine_keep=REFINE_KEEP,
            extend_seed_count=0, hypothesis_pair_index=pair_index)
        artifact["cells"].append(compact(result))
        ranked = rank_pairs(artifact["cells"])
        true = next(cell for cell in ranked if cell["hypothesis_is_true_pair"])
        artifact["true_pair_rank_so_far"] = true["pair_screen_rank"]
        artifact["wall_seconds_so_far"] = time.monotonic() - began
        output.write_text(json.dumps(artifact, indent=2) + "\n")
        print(pair_index, result["hypothesis_pair"],
              round(result["best_refined_normalized_score"], 6), flush=True)
    artifact["cells"] = rank_pairs(artifact["cells"])
    true = next(cell for cell in artifact["cells"] if cell["hypothesis_is_true_pair"])
    artifact["true_pair_rank"] = true["pair_screen_rank"]
    artifact["true_pair_score"] = true["best_refined_normalized_score"]
    artifact["status"] = "development_unknown_pair_screen_complete_not_frozen"
    artifact["wall_seconds"] = time.monotonic() - began
    artifact.pop("wall_seconds_so_far", None)
    artifact.pop("true_pair_rank_so_far", None)
    output.write_text(json.dumps(artifact, indent=2) + "\n")
    return artifact


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--mode", choices=solver.base.BOARD_MODES,
                        default="vic_profile")
    parser.add_argument("--fixture-index", type=int, default=50)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.run:
        parser.error("use --run")
    output = args.output or SCRIPT_DIR / (
        f"phase484s_pair_screen_{args.mode}_i{args.fixture_index}.json")
    result = run(args.mode, args.fixture_index, output)
    print("true pair rank", result["true_pair_rank"], "of", len(result["cells"]))
    print("wrote", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
