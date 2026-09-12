#!/usr/bin/env python3
"""Development probe: bridge a noisy width-30 layer by parent reservation.

Loads a retained depth-10 synthetic population, takes the highest-ranked
parents, retains a fixed number of their locally best children at depth 11,
then tests ordinary constrained-board selection again at depth 12.  No FAED or
holdout data is imported.
"""
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
                  "_work/phase484ac/i15_replay/depth10_selected.npz")
PARENT_DEPTH = 10
PARENT_KEEP = 65536
CHILDREN_PER_PARENT = 8
DEPTH12_KEEP = 262144
RESTARTS = 3
ITERATIONS = 2000


def load_population(path: Path):
    path = Path(path)
    with np.load(path) as payload:
        paths = np.asarray(payload["paths"], dtype=np.uint8)
        scores = np.asarray(payload["scores"], dtype=np.float64)
    if paths.ndim != 2 or paths.shape[1] != PARENT_DEPTH:
        raise ValueError("checkpoint must contain depth-10 paths")
    if scores.shape != (len(paths),):
        raise ValueError("checkpoint scores do not match paths")
    return paths, scores, hashlib.sha256(path.read_bytes()).hexdigest()


def expand_with_parent_indices(paths: np.ndarray):
    """Match width30.expand_bidirectional and retain each source row index."""
    paths = np.asarray(paths, dtype=np.uint8)
    width, depth = width30.WIDTH, paths.shape[1]
    total = 2 * len(paths) * (width - depth)
    expanded = np.empty((total, depth + 1), dtype=np.uint8)
    parents = np.empty(total, dtype=np.int64)
    offset = 0
    all_indices = np.arange(len(paths), dtype=np.int64)
    for column in range(width):
        mask = ~np.any(paths == column, axis=1)
        subset = paths[mask]
        indices = all_indices[mask]
        count = len(subset)
        expanded[offset:offset + count, 0] = column
        expanded[offset:offset + count, 1:] = subset
        parents[offset:offset + count] = indices
        offset += count
        expanded[offset:offset + count, :-1] = subset
        expanded[offset:offset + count, -1] = column
        parents[offset:offset + count] = indices
        offset += count
    if offset != total:
        raise AssertionError("parent-index expansion count mismatch")
    return expanded, parents


def reserve_local_children(paths, scores, parent_indices,
                           children_per_parent=CHILDREN_PER_PARENT):
    """Select each parent's best K children, then exact-deduplicate."""
    paths = np.asarray(paths, dtype=np.uint8)
    scores = np.asarray(scores, dtype=np.float64)
    parent_indices = np.asarray(parent_indices, dtype=np.int64)
    parent_count = int(parent_indices.max()) + 1
    group_size = len(paths) // parent_count
    if len(paths) != parent_count * group_size:
        raise ValueError("children are not balanced across parents")
    keys = tuple(paths[:, column]
                 for column in range(paths.shape[1] - 1, -1, -1))
    order = np.lexsort((*keys, -scores, parent_indices))
    grouped = order.reshape(parent_count, group_size)
    selected = grouped[:, :min(children_per_parent, group_size)].reshape(-1)
    selected_paths, selected_scores = paths[selected], scores[selected]
    unique = width30.unique_path_indices(selected_paths)
    return selected_paths[unique].copy(), selected_scores[unique].copy()


def run(source=DEFAULT_SOURCE, fixture_index=15,
        parent_keep=PARENT_KEEP, children_per_parent=CHILDREN_PER_PARENT,
        depth12_keep=DEPTH12_KEEP, restarts=RESTARTS,
        iterations=ITERATIONS, binary=constrained.GPU_BINARY,
        checkpoint_dir=None, split="dev", board_seed=early.joint.SEED):
    source = Path(source)
    paths10, scores10, source_sha256 = load_population(source)
    ranked = width30.ranked_indices(paths10, scores10)
    ranked = ranked[:min(parent_keep, len(ranked))]
    parents = paths10[ranked]
    fixture = width30.width30_fixture(fixture_index, split)
    truth = prefix.order_to_sequence(fixture["order"])
    blocks = prefix.blocks_from_observed(fixture)
    pair = tuple(fixture["pair"])
    quad, _ = base.load_language_model()
    began = time.monotonic()

    children11, parent_indices = expand_with_parent_indices(parents)
    scores11 = early.board_screen(
        children11, blocks, pair, quad, restarts, iterations, binary,
        seed=board_seed)
    before11 = early.recovery_record(
        children11, scores11, truth, 11, include_best=True)
    reserved11, reserved_scores11 = reserve_local_children(
        children11, scores11, parent_indices, children_per_parent)
    after11 = early.recovery_record(
        reserved11, reserved_scores11, truth, 11, include_best=True)
    after11["checkpoint"] = early.save_checkpoint(
        checkpoint_dir, "depth11_parent_reserved", reserved11,
        reserved_scores11)

    children12 = width30.expand_bidirectional(reserved11)
    scores12 = early.board_screen(
        children12, blocks, pair, quad, restarts, iterations, binary,
        seed=board_seed)
    before12 = early.recovery_record(
        children12, scores12, truth, 12, include_best=True)
    selected12, selected_scores12, unique12 = width30.select_diverse(
        children12, scores12, depth12_keep)
    after12 = early.recovery_record(
        selected12, selected_scores12, truth, 12, include_best=True)
    after12["checkpoint"] = early.save_checkpoint(
        checkpoint_dir, "depth12_selected", selected12,
        selected_scores12)
    return {
        "phase": "484AD",
        "status": "development_parent_reserved_bridge_not_frozen",
        "faed_scored": False,
        "holdout_consumed": split == "holdout",
        "fixture_index": fixture_index,
        "split": split,
        "source": str(source),
        "source_sha256": source_sha256,
        "parent_keep": len(parents),
        "children_per_parent": children_per_parent,
        "restarts": restarts,
        "iterations": iterations,
        "board_seed": board_seed,
        "checkpoint_dir": str(checkpoint_dir) if checkpoint_dir else None,
        "depth11": {
            "before_reservation": before11,
            "after_reservation": after11,
            "reserved_count": len(reserved11),
        },
        "depth12": {
            "generated_unique": unique12,
            "before_selection": before12,
            "after_selection": after12,
            "keep": depth12_keep,
        },
        "wall_seconds": time.monotonic() - began,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--fixture-index", type=int, default=15)
    parser.add_argument("--parent-keep", type=int, default=PARENT_KEEP)
    parser.add_argument("--children-per-parent", type=int,
                        default=CHILDREN_PER_PARENT)
    parser.add_argument("--depth12-keep", type=int, default=DEPTH12_KEEP)
    parser.add_argument("--restarts", type=int, default=RESTARTS)
    parser.add_argument("--iterations", type=int, default=ITERATIONS)
    parser.add_argument("--binary", type=Path, default=constrained.GPU_BINARY)
    parser.add_argument("--checkpoint-dir", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.run:
        parser.error("use --run")
    result = run(args.source, args.fixture_index, args.parent_keep,
                 args.children_per_parent, args.depth12_keep,
                 args.restarts, args.iterations, args.binary,
                 args.checkpoint_dir)
    output = args.output or SCRIPT_DIR / "phase484ad_width30_bridge_result.json"
    output.write_text(json.dumps(result, indent=2) + "\n")
    print("depth11", result["depth11"])
    print("depth12", result["depth12"])
    print("wall", round(result["wall_seconds"], 3), "wrote", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
