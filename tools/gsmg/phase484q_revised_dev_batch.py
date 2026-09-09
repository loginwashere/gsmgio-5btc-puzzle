#!/usr/bin/env python3
"""Revised-capacity Phase 484Q development runner.

The tuning cases are already-open failures from indices 40..49.  The fresh
batch uses untouched development indices 50..59.  Neither mode imports FAED or
consumes holdout fixtures.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import phase484q_blind_joint_width19_solver as solver

SCRIPT_DIR = Path(__file__).resolve().parent
SHORTLIST = 262144
REFINE_KEEP = 8192
EXTEND_SEEDS = 64
TUNING_CASES = (("vic_profile", 41), ("vic_profile", 48),
                ("broad_random", 45), ("broad_random", 49))
FRESH_CASES = tuple((mode, index) for mode in ("vic_profile", "broad_random")
                    for index in range(50, 60))


def compact(result):
    keys = (
        "board_mode", "fixture_index", "shortlist_size",
        "true_segments_retained", "best_true_coarse_rank",
        "best_true_board_accuracy", "best_true_refined_rank",
        "best_true_refined_board_accuracy", "exact_order_in_terminals",
        "exact_order_extension_rank", "exact_order_final_rank",
        "top1_exact_order", "top1_plaintext_accuracy", "terminals_total",
        "terminals_valid", "terminals_skipped_invalid_segmentation",
        "shortlist_seconds", "gpu_screen_seconds", "gpu_refine_seconds",
        "extension_seconds", "final_seconds",
    )
    return {key: result[key] for key in keys}


def summarize(cells):
    return {
        "fixtures": len(cells),
        "shortlist_retained": sum(bool(c["true_segments_retained"]) for c in cells),
        "exact_order_in_terminals": sum(c["exact_order_in_terminals"] for c in cells),
        "exact_order_top1": sum(c["top1_exact_order"] for c in cells),
        "exact_order_top1_rate": (sum(c["top1_exact_order"] for c in cells) / len(cells)
                                  if cells else None),
    }


def run(cases, label, output):
    began = time.monotonic()
    artifact = {
        "phase": "484Q-revised",
        "status": "development_batch_in_progress_not_frozen",
        "batch": label,
        "faed_scored": False,
        "holdout_consumed": False,
        "budgets": {"shortlist": SHORTLIST, "refine_keep": REFINE_KEEP,
                    "extension_seed_count": EXTEND_SEEDS,
                    "extension_beam": solver.EXTEND_BEAM,
                    "terminals_per_seed": solver.TERMINALS_PER_SEED},
        "cases": [{"board_mode": mode, "fixture_index": index}
                  for mode, index in cases],
        "cells": [],
    }
    for mode, index in cases:
        result = solver.screen_fixture(
            mode, index, keep=SHORTLIST, refine_keep=REFINE_KEEP,
            extend_seed_count=EXTEND_SEEDS)
        artifact["cells"].append(compact(result))
        artifact["summary"] = summarize(artifact["cells"])
        artifact["wall_seconds_so_far"] = time.monotonic() - began
        output.write_text(json.dumps(artifact, indent=2) + "\n")
        print(mode, index, "truth", result["true_segments_retained"],
              "refined", result["best_true_refined_rank"],
              "top1", result["top1_exact_order"], flush=True)
    artifact["status"] = "development_batch_complete_not_frozen"
    artifact["wall_seconds"] = time.monotonic() - began
    artifact.pop("wall_seconds_so_far", None)
    artifact["summary"] = summarize(artifact["cells"])
    output.write_text(json.dumps(artifact, indent=2) + "\n")
    return artifact


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--run-tuning-cases", action="store_true")
    group.add_argument("--run-fresh-batch", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.run_tuning_cases:
        cases, label = TUNING_CASES, "already_open_tuning_cases"
        default = SCRIPT_DIR / "phase484q_revised_tuning_result.json"
    else:
        cases, label = FRESH_CASES, "untouched_dev_indices_50_59"
        default = SCRIPT_DIR / "phase484q_revised_fresh_result.json"
    result = run(cases, label, args.output or default)
    print(json.dumps(result["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
