#!/usr/bin/env python3
"""Resumable pair-fair width-19 capacity run on development fixtures."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import phase484q_blind_joint_width19_solver as solver
import phase484s_unknown_pair_full as pair_audit

SCRIPT_DIR = Path(__file__).resolve().parent
KEEP = 262144
REFINE_KEEP = 8192
EXTEND_SEEDS = 256
EXTEND_WORKERS = 8


def budgets():
    return {
        "shortlist": KEEP,
        "refine_keep": REFINE_KEEP,
        "extension_seed_count": EXTEND_SEEDS,
        "extension_workers": EXTEND_WORKERS,
        "extension_beam": solver.EXTEND_BEAM,
        "terminals_per_seed": solver.TERMINALS_PER_SEED,
    }


def write_artifact(path, artifact):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(artifact, indent=2) + "\n")
    temporary.replace(path)


def new_artifact(mode, fixture_index, true_pair_index=solver.learned.PAIR_INDEX):
    if not 0 <= true_pair_index < len(solver.base.ESCAPE_PAIRS):
        raise ValueError("true pair index out of range")
    return {
        "phase": "484T",
        "status": "development_pair_fair_capacity_in_progress_not_frozen",
        "faed_scored": False,
        "holdout_consumed": False,
        "board_mode": mode,
        "fixture_index": fixture_index,
        "true_pair_index": true_pair_index,
        "true_pair": list(solver.base.ESCAPE_PAIRS[true_pair_index]),
        "budgets": budgets(),
        "cells": [],
    }


def load_or_create(mode, fixture_index, output,
                   true_pair_index=solver.learned.PAIR_INDEX):
    if not output.exists():
        return new_artifact(mode, fixture_index, true_pair_index)
    artifact = json.loads(output.read_text())
    expected = new_artifact(mode, fixture_index, true_pair_index)
    for key in ("phase", "faed_scored", "holdout_consumed", "board_mode",
                "fixture_index", "true_pair_index", "true_pair", "budgets"):
        if artifact.get(key) != expected[key]:
            raise ValueError(f"resume artifact mismatch: {key}")
    indices = [cell["hypothesis_pair_index"] for cell in artifact["cells"]]
    if len(indices) != len(set(indices)) or any(
            not 0 <= index < len(solver.base.ESCAPE_PAIRS) for index in indices):
        raise ValueError("resume artifact has invalid pair indices")
    return artifact


def true_pair_rank(cells):
    ranked = pair_audit.rank_pairs(cells)
    true = next((cell for cell in ranked
                 if cell["hypothesis_is_true_pair"]), None)
    return true["full_pair_rank"] if true is not None else None


def run(mode, fixture_index, output,
        true_pair_index=solver.learned.PAIR_INDEX):
    artifact = load_or_create(mode, fixture_index, output, true_pair_index)
    if artifact["status"] == "development_pair_fair_capacity_complete_not_frozen":
        return artifact
    completed = {cell["hypothesis_pair_index"] for cell in artifact["cells"]}
    began = time.monotonic()
    prior_seconds = artifact.get("wall_seconds_so_far", 0.0)
    for pair_index in range(len(solver.base.ESCAPE_PAIRS)):
        if pair_index in completed:
            continue
        result = solver.screen_fixture(
            mode=mode, fixture_index=fixture_index, keep=KEEP,
            refine_keep=REFINE_KEEP, extend_seed_count=EXTEND_SEEDS,
            extend_workers=EXTEND_WORKERS,
            hypothesis_pair_index=pair_index,
            true_pair_index=true_pair_index)
        artifact["cells"].append(pair_audit.compact(result))
        rank = true_pair_rank(artifact["cells"])
        if rank is None:
            artifact.pop("true_pair_rank_so_far", None)
        else:
            artifact["true_pair_rank_so_far"] = rank
        artifact["wall_seconds_so_far"] = prior_seconds + time.monotonic() - began
        write_artifact(output, artifact)
        print(pair_index, result["hypothesis_pair"],
              result["top1_final_normalized_score"], flush=True)
    artifact["cells"] = pair_audit.rank_pairs(artifact["cells"])
    true = next(cell for cell in artifact["cells"] if cell["hypothesis_is_true_pair"])
    artifact["true_pair_rank"] = true["full_pair_rank"]
    artifact["true_pair_top1_exact_order"] = true["top1_exact_order"]
    artifact["status"] = "development_pair_fair_capacity_complete_not_frozen"
    artifact["wall_seconds"] = prior_seconds + time.monotonic() - began
    artifact.pop("wall_seconds_so_far", None)
    artifact.pop("true_pair_rank_so_far", None)
    write_artifact(output, artifact)
    return artifact


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--mode", choices=solver.base.BOARD_MODES,
                        default="broad_random")
    parser.add_argument("--fixture-index", type=int, default=51)
    parser.add_argument("--true-pair-index", type=int,
                        default=solver.learned.PAIR_INDEX)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.run:
        parser.error("use --run")
    suffix = ("" if args.true_pair_index == solver.learned.PAIR_INDEX
              else f"_true{args.true_pair_index}")
    output = args.output or SCRIPT_DIR / (
        f"phase484t_pair_fair_{args.mode}_i{args.fixture_index}{suffix}.json")
    result = run(args.mode, args.fixture_index, output, args.true_pair_index)
    print("true pair rank", result["true_pair_rank"], "of", len(result["cells"]))
    print("wrote", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
