#!/usr/bin/env python3
"""Targeted development-capacity probe for diagnosed Phase 484Q misses.

This consumes neither holdout fixtures nor FAED.  The cases were selected from
the completed indices-40..49 development batch and therefore may tune the next
solver, but may not validate it.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import phase484q_blind_joint_width19_solver as solver

SCRIPT_DIR = Path(__file__).resolve().parent
REFINE_CASES = (("broad_random", 47), ("broad_random", 48))


def compact_result(result):
    return {
        "board_mode": result["board_mode"],
        "fixture_index": result["fixture_index"],
        "shortlist_size": result["shortlist_size"],
        "true_segments_retained": result["true_segments_retained"],
        "best_true_coarse_rank": result["best_true_coarse_rank"],
        "best_true_refined_rank": result["best_true_refined_rank"],
        "best_true_refined_board_accuracy": result["best_true_refined_board_accuracy"],
        "shortlist_seconds": result["shortlist_seconds"],
        "gpu_screen_seconds": result["gpu_screen_seconds"],
        "gpu_refine_seconds": result["gpu_refine_seconds"],
        "true_records": result["true_records"],
        "refined_true_records": [r for r in result["refined_population"] if r["is_true_segment"]],
    }


def run_refine_probe(output):
    began = time.monotonic()
    artifact = {
        "phase": "484Q-capacity",
        "status": "development_tuning_in_progress_not_frozen",
        "faed_scored": False,
        "holdout_consumed": False,
        "source_batch_fixture_indices": list(range(40, 50)),
        "purpose": "measure refined ranks for the two truth paths excluded by refine_keep=64",
        "budgets": {"shortlist": 16384, "refine_keep": 4096, "extension_seed_count": 0},
        "cells": [],
    }
    for mode, index in REFINE_CASES:
        result = solver.screen_fixture(mode, index, refine_keep=4096, extend_seed_count=0)
        artifact["cells"].append(compact_result(result))
        artifact["wall_seconds_so_far"] = time.monotonic() - began
        output.write_text(json.dumps(artifact, indent=2) + "\n")
        print(mode, index, "coarse", result["best_true_coarse_rank"],
              "refined", result["best_true_refined_rank"], flush=True)
    artifact["status"] = "development_tuning_complete_not_frozen"
    artifact["wall_seconds"] = time.monotonic() - began
    artifact.pop("wall_seconds_so_far", None)
    output.write_text(json.dumps(artifact, indent=2) + "\n")
    return artifact


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-refine-probe", action="store_true")
    parser.add_argument("--output", type=Path,
                        default=SCRIPT_DIR / "phase484q_capacity_refine_probe.json")
    args = parser.parse_args()
    if not args.run_refine_probe:
        parser.error("use --run-refine-probe")
    run_refine_probe(args.output)
    print("wrote", args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
