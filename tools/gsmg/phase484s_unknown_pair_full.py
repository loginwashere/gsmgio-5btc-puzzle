#!/usr/bin/env python3
"""End-to-end 36-pair development ranking for the width-19 solver."""
from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import phase484q_blind_joint_width19_solver as solver

SCRIPT_DIR = Path(__file__).resolve().parent
KEEP, REFINE_KEEP, EXTEND_SEEDS = 16384, 64, 8


def pair_score(cell):
    score = cell["top1_final_normalized_score"]
    return score if score is not None and math.isfinite(score) else -math.inf


def rank_pairs(cells):
    ranked = sorted(cells, key=lambda cell:
                    (-pair_score(cell), cell["hypothesis_pair_index"]))
    for rank, cell in enumerate(ranked, 1):
        cell["full_pair_rank"] = rank
    return ranked


def compact(result):
    top = result["final_candidates"][0] if result["final_candidates"] else None
    return {
        "hypothesis_pair_index": result["hypothesis_pair_index"],
        "hypothesis_pair": result["hypothesis_pair"],
        "hypothesis_is_true_pair": result["hypothesis_is_true_pair"],
        "best_refined_normalized_score": result["best_refined_normalized_score"],
        "top1_final_normalized_score": result["top1_final_normalized_score"],
        "top1_decoded_length": top["decoded_length"] if top else None,
        "top1_plaintext_prefix": top["plaintext"][:120] if top else None,
        "true_segments_retained": result["true_segments_retained"],
        "best_true_refined_rank": result["best_true_refined_rank"],
        "exact_order_in_terminals": result["exact_order_in_terminals"],
        "top1_exact_order": result["top1_exact_order"],
        "top1_plaintext_accuracy": result["top1_plaintext_accuracy"],
        "terminals_total": result["terminals_total"],
        "terminals_valid": result["terminals_valid"],
        "wall_seconds": sum(result[key] for key in (
            "shortlist_seconds", "gpu_screen_seconds", "gpu_refine_seconds",
            "extension_seconds", "final_seconds")),
    }


def run(mode, fixture_index, output):
    began = time.monotonic()
    artifact = {
        "phase": "484S",
        "status": "development_unknown_pair_full_in_progress_not_frozen",
        "faed_scored": False,
        "holdout_consumed": False,
        "board_mode": mode,
        "fixture_index": fixture_index,
        "true_pair_index": solver.learned.PAIR_INDEX,
        "budgets": {"shortlist": KEEP, "refine_keep": REFINE_KEEP,
                    "extension_seed_count": EXTEND_SEEDS},
        "cells": [],
    }
    for pair_index in range(len(solver.base.ESCAPE_PAIRS)):
        result = solver.screen_fixture(
            mode, fixture_index, keep=KEEP, refine_keep=REFINE_KEEP,
            extend_seed_count=EXTEND_SEEDS,
            hypothesis_pair_index=pair_index)
        artifact["cells"].append(compact(result))
        ranked = rank_pairs(artifact["cells"])
        true = next(cell for cell in ranked if cell["hypothesis_is_true_pair"])
        artifact["true_pair_rank_so_far"] = true["full_pair_rank"]
        artifact["wall_seconds_so_far"] = time.monotonic() - began
        output.write_text(json.dumps(artifact, indent=2) + "\n")
        print(pair_index, result["hypothesis_pair"],
              result["top1_final_normalized_score"], flush=True)
    artifact["cells"] = rank_pairs(artifact["cells"])
    true = next(cell for cell in artifact["cells"] if cell["hypothesis_is_true_pair"])
    artifact["true_pair_rank"] = true["full_pair_rank"]
    artifact["true_pair_top1_exact_order"] = true["top1_exact_order"]
    artifact["status"] = "development_unknown_pair_full_complete_not_frozen"
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
        f"phase484s_pair_full_{args.mode}_i{args.fixture_index}.json")
    result = run(args.mode, args.fixture_index, output)
    print("true pair rank", result["true_pair_rank"], "of", len(result["cells"]))
    print("wrote", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
