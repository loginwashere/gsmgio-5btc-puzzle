#!/usr/bin/env python3
"""Resume constrained width-30 rolling selection from an NPZ checkpoint."""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np

import phase484a_raw_symbol_vic_solver as base
import phase484j_constructive_prefix_beam_probe as prefix
import phase484y_width30_feasibility_probe as width30
import phase484y_width30_blind_joint_solver as joint
import phase484z_width30_early_board_switch_probe as early
import phase484ac_width30_partition_constrained_board_probe as constrained

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_SOURCE = (SCRIPT_DIR.parents[1] /
                  "_work/phase484ac/i15_replay/depth12_selected.npz")
KEEP = 262144
RESTARTS = 3
ITERATIONS = 2000


def load_checkpoint(path):
    path = Path(path)
    with np.load(path) as payload:
        paths = np.asarray(payload["paths"], dtype=np.uint8)
        scores = np.asarray(payload["scores"], dtype=np.float64)
    if paths.ndim != 2 or not 4 <= paths.shape[1] <= width30.WIDTH:
        raise ValueError("checkpoint paths have invalid depth")
    if scores.shape != (len(paths),):
        raise ValueError("checkpoint scores do not match paths")
    if np.any(np.apply_along_axis(lambda row: len(set(row)) != len(row), 1,
                                  paths)):
        raise ValueError("checkpoint contains a repeated-column path")
    return paths, scores, hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_final(source, fixture_index=15, top=8, restarts=4,
                  iterations=10000, split="dev"):
    source = Path(source)
    paths, scores, source_sha256 = load_checkpoint(source)
    if paths.shape[1] != width30.WIDTH:
        raise ValueError("final resolution requires depth-30 paths")
    fixture = width30.width30_fixture(fixture_index, split)
    truth = prefix.order_to_sequence(fixture["order"])
    blocks = prefix.blocks_from_observed(fixture)
    pair = tuple(fixture["pair"])
    quad, _ = base.load_language_model()
    ranked = width30.ranked_indices(paths, scores)[:min(top, len(paths))]
    terminals = [{
        "extension_rank": rank,
        "extension_score": float(scores[index]),
        "order": paths[index].tolist(),
    } for rank, index in enumerate(ranked, 1)]
    final, skipped = joint.resolve_terminals(
        blocks, pair, quad, terminals, restarts, iterations)
    truth_tuple = tuple(truth)
    truth_plaintext = fixture["plaintext"]
    for record in final:
        record["is_exact_order"] = tuple(record["order"]) == truth_tuple
        record["plaintext_accuracy"] = sum(
            a == b for a, b in zip(record["plaintext"], truth_plaintext)
        ) / max(len(record["plaintext"]), len(truth_plaintext))
    exact = next((record for record in final
                  if record["is_exact_order"]), None)
    return {
        "phase": "484AE",
        "status": "development_final_resolve_not_frozen",
        "faed_scored": False,
        "holdout_consumed": split == "holdout",
        "fixture_index": fixture_index,
        "split": split,
        "source": str(source),
        "source_sha256": source_sha256,
        "top": len(terminals),
        "restarts": restarts,
        "iterations": iterations,
        "skipped": len(skipped),
        "exact_order_final_rank": exact["final_rank"] if exact else None,
        "exact_order_plaintext_accuracy": (
            exact["plaintext_accuracy"] if exact else None),
        "top1_exact_order": bool(final and final[0]["is_exact_order"]),
        "top1_plaintext_accuracy": (
            final[0]["plaintext_accuracy"] if final else None),
        "final_candidates": final,
    }


def run(source=DEFAULT_SOURCE, fixture_index=15, max_depth=16,
        keep=KEEP, restarts=RESTARTS, iterations=ITERATIONS,
        binary=constrained.GPU_BINARY, checkpoint_dir=None,
        stop_on_truth_loss=True, split="dev"):
    source = Path(source)
    paths, scores, source_sha256 = load_checkpoint(source)
    start_depth = paths.shape[1]
    if not start_depth < max_depth <= width30.WIDTH:
        raise ValueError("max_depth must exceed checkpoint depth and be <= 30")
    fixture = width30.width30_fixture(fixture_index, split)
    truth = prefix.order_to_sequence(fixture["order"])
    blocks = prefix.blocks_from_observed(fixture)
    pair = tuple(fixture["pair"])
    quad, _ = base.load_language_model()
    diagnostics = []
    began = time.monotonic()
    for depth in range(start_depth + 1, max_depth + 1):
        stage_began = time.monotonic()
        generated = width30.expand_bidirectional(paths)
        generated_scores = early.board_screen(
            generated, blocks, pair, quad, restarts, iterations, binary)
        before = early.recovery_record(
            generated, generated_scores, truth, depth, include_best=True)
        paths, scores, unique = width30.select_diverse(
            generated, generated_scores, keep)
        after = early.recovery_record(
            paths, scores, truth, depth, include_best=True)
        after["checkpoint"] = early.save_checkpoint(
            checkpoint_dir, f"depth{depth}_selected", paths, scores)
        diagnostics.append({
            "depth": depth,
            "generated_unique": unique,
            "before_selection": before,
            "after_selection": after,
            "seconds": time.monotonic() - stage_began,
        })
        if stop_on_truth_loss and not after["true_segments"]:
            break
    return {
        "phase": "484AE",
        "status": "development_checkpointed_rolling_not_frozen",
        "faed_scored": False,
        "holdout_consumed": split == "holdout",
        "fixture_index": fixture_index,
        "split": split,
        "source": str(source),
        "source_sha256": source_sha256,
        "start_depth": start_depth,
        "requested_max_depth": max_depth,
        "keep": keep,
        "restarts": restarts,
        "iterations": iterations,
        "checkpoint_dir": str(checkpoint_dir) if checkpoint_dir else None,
        "stop_on_truth_loss": stop_on_truth_loss,
        "completed_depth": diagnostics[-1]["depth"],
        "truth_survived": bool(
            diagnostics[-1]["after_selection"]["true_segments"]),
        "depth_diagnostics": diagnostics,
        "wall_seconds": time.monotonic() - began,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--resolve-final", action="store_true")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--fixture-index", type=int, default=15)
    parser.add_argument("--max-depth", type=int, default=16)
    parser.add_argument("--keep", type=int, default=KEEP)
    parser.add_argument("--restarts", type=int, default=RESTARTS)
    parser.add_argument("--iterations", type=int, default=ITERATIONS)
    parser.add_argument("--binary", type=Path, default=constrained.GPU_BINARY)
    parser.add_argument("--checkpoint-dir", type=Path)
    parser.add_argument("--continue-after-truth-loss", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.run == args.resolve_final:
        parser.error("choose exactly one of --run or --resolve-final")
    if args.resolve_final:
        result = resolve_final(
            args.source, args.fixture_index, top=8,
            restarts=args.restarts, iterations=args.iterations)
    else:
        result = run(args.source, args.fixture_index, args.max_depth, args.keep,
                     args.restarts, args.iterations, args.binary,
                     args.checkpoint_dir,
                     not args.continue_after_truth_loss)
    output = args.output or SCRIPT_DIR / "phase484ae_width30_rolling_result.json"
    output.write_text(json.dumps(result, indent=2) + "\n")
    if args.resolve_final:
        print("exact final rank", result["exact_order_final_rank"],
              "top1 exact", result["top1_exact_order"],
              "plaintext accuracy", result["top1_plaintext_accuracy"])
    else:
        for record in result["depth_diagnostics"]:
            print("depth", record["depth"], "true rank/selected",
                  record["before_selection"]["best_true_rank"],
                  record["after_selection"]["best_true_rank"])
        print("survived", result["truth_survived"],
              "wall", round(result["wall_seconds"], 3))
    print("wrote", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
