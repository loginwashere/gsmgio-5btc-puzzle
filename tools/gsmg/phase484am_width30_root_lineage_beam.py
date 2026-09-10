#!/usr/bin/env python3
"""Streaming root-lineage continuation for the width-30 dev diagnosis.

The ordinary global beam loses fixture 19 even though its correct extension is
strong within its own ancestry.  This probe keeps a fixed number of descendants
per original depth-7 root.  It is development-only and never imports FAED or a
holdout fixture.
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
import phase484z_width30_early_board_switch_probe as early
import phase484ad_width30_parent_reserved_bridge as bridge
import phase484ac_width30_partition_constrained_board_probe as constrained

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_SOURCE = (SCRIPT_DIR.parents[1] / "_work" / "phase484diagnose" /
                  "i19_root_beam4" / "depth8_root_beam4.npz")
DEFAULT_WORK_DIR = (SCRIPT_DIR.parents[1] / "_work" / "phase484am" /
                    "i19_root_beam4")
DESCENDANTS_PER_ROOT = 4
ROOT_CHUNK = 16384
RESTARTS = 3
ITERATIONS = 2000


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def load_state(path: Path):
    path = Path(path)
    with np.load(path) as payload:
        paths = np.asarray(payload["paths"], dtype=np.uint8)
        scores = np.asarray(payload["scores"], dtype=np.float64)
        roots = np.asarray(payload["root_ids"], dtype=np.int64)
    if paths.ndim != 2 or not 7 <= paths.shape[1] < width30.WIDTH:
        raise ValueError("state paths must have depth 7..29")
    if scores.shape != (len(paths),) or roots.shape != (len(paths),):
        raise ValueError("state arrays have inconsistent lengths")
    if len(paths) == 0 or np.any(roots < 0):
        raise ValueError("state must be nonempty with nonnegative root IDs")
    if np.any(roots[1:] < roots[:-1]):
        raise ValueError("state root IDs must be sorted")
    return paths, scores, roots, sha256_file(path)


def unique_root_path_indices(roots, paths, scores):
    """Keep the best exact duplicate for each (root, path) key."""
    roots = np.asarray(roots, dtype=np.int64)
    paths = np.ascontiguousarray(paths, dtype=np.uint8)
    scores = np.asarray(scores, dtype=np.float64)
    if roots.shape != (len(paths),) or scores.shape != (len(paths),):
        raise ValueError("root/path/score length mismatch")
    key_type = np.dtype([("root", "<i8"),
                         ("path", np.uint8, (paths.shape[1],))])
    keys = np.empty(len(paths), dtype=key_type)
    keys["root"] = roots
    keys["path"] = paths
    # root, then path bytes, then descending score.  ``lexsort`` treats the
    # last key as primary, so score must be the least-significant key here.
    order = np.lexsort((-scores,) + tuple(paths[:, c] for c in range(
        paths.shape[1] - 1, -1, -1)) + (roots,))
    ordered = keys[order]
    first = np.r_[True, ordered[1:] != ordered[:-1]]
    return order[first]


def select_per_root(paths, scores, roots, keep=DESCENDANTS_PER_ROOT):
    """Exact-deduplicate, then retain each root's best ``keep`` paths."""
    if keep < 1:
        raise ValueError("keep must be positive")
    unique = unique_root_path_indices(roots, paths, scores)
    paths = np.asarray(paths, dtype=np.uint8)[unique]
    scores = np.asarray(scores, dtype=np.float64)[unique]
    roots = np.asarray(roots, dtype=np.int64)[unique]
    order = np.lexsort(tuple(paths[:, c] for c in range(
        paths.shape[1] - 1, -1, -1)) + (-scores, roots))
    sorted_roots = roots[order]
    boundaries = np.flatnonzero(np.r_[True, sorted_roots[1:] != sorted_roots[:-1], True])
    chosen = np.concatenate([
        order[left:min(right, left + keep)]
        for left, right in zip(boundaries[:-1], boundaries[1:])
    ])
    final = np.lexsort(tuple(paths[chosen, c] for c in range(
        paths.shape[1] - 1, -1, -1)) + (-scores[chosen], roots[chosen]))
    chosen = chosen[final]
    return paths[chosen].copy(), scores[chosen].copy(), roots[chosen].copy()


def expand_root_chunk(paths, roots):
    children, parent_indices = bridge.expand_with_parent_indices(paths)
    return children, np.asarray(roots, dtype=np.int64)[parent_indices]


def run_depth(source=DEFAULT_SOURCE, fixture_index=19,
              descendants_per_root=DESCENDANTS_PER_ROOT,
              root_chunk=ROOT_CHUNK, restarts=RESTARTS,
              iterations=ITERATIONS, work_dir=DEFAULT_WORK_DIR):
    source, work_dir = Path(source), Path(work_dir)
    paths, _, roots, source_sha256 = load_state(source)
    start_depth = paths.shape[1]
    target_depth = start_depth + 1
    root_values = np.unique(roots)
    if not np.array_equal(root_values, np.arange(root_values[-1] + 1)):
        raise ValueError("root IDs must form a dense zero-based range")
    fixture = width30.width30_fixture(fixture_index, "dev")
    truth = prefix.order_to_sequence(fixture["order"])
    blocks = prefix.blocks_from_observed(fixture)
    pair = tuple(fixture["pair"])
    quad, _ = base.load_language_model()
    true_parent_roots = np.unique(roots[width30.true_path_mask(
        paths, truth, start_depth)])
    began = time.monotonic()
    output_paths, output_scores, output_roots = [], [], []
    for root_start in range(0, len(root_values), root_chunk):
        root_stop = min(len(root_values), root_start + root_chunk)
        left = np.searchsorted(roots, root_start, side="left")
        right = np.searchsorted(roots, root_stop, side="left")
        children, child_roots = expand_root_chunk(paths[left:right], roots[left:right])
        child_scores = early.board_screen(
            children, blocks, pair, quad, restarts, iterations,
            constrained.GPU_BINARY)
        selected = select_per_root(
            children, child_scores, child_roots, descendants_per_root)
        output_paths.append(selected[0])
        output_scores.append(selected[1])
        output_roots.append(selected[2])
        print("roots", root_start, root_stop, "retained", len(selected[0]),
              flush=True)
    selected_paths = np.concatenate(output_paths)
    selected_scores = np.concatenate(output_scores)
    selected_roots = np.concatenate(output_roots)
    work_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = work_dir / f"depth{target_depth}_root_beam{descendants_per_root}.npz"
    np.savez(checkpoint, paths=selected_paths, scores=selected_scores,
             root_ids=selected_roots)
    root_best = np.full(len(root_values), -np.inf)
    np.maximum.at(root_best, selected_roots, selected_scores)
    root_order = np.lexsort((np.arange(len(root_best)), -root_best))
    rank_of = np.empty(len(root_best), dtype=np.int64)
    rank_of[root_order] = np.arange(1, len(root_best) + 1)
    true_mask = width30.true_path_mask(selected_paths, truth, target_depth)
    true_roots_after = np.unique(selected_roots[true_mask])
    result = {
        "phase": "484AM",
        "status": "development_streaming_root_lineage_depth_complete_not_frozen",
        "faed_scored": False,
        "holdout_consumed": False,
        "fixture_index": fixture_index,
        "source": str(source),
        "source_sha256": source_sha256,
        "start_depth": start_depth,
        "target_depth": target_depth,
        "root_count": len(root_values),
        "descendants_per_root": descendants_per_root,
        "root_chunk": root_chunk,
        "restarts": restarts,
        "iterations": iterations,
        "retained_count": len(selected_paths),
        "true_parent_roots": true_parent_roots.tolist(),
        "true_roots_after": true_roots_after.tolist(),
        "true_paths_after": int(np.count_nonzero(true_mask)),
        "true_root_ranks": {str(int(root)): int(rank_of[root])
                            for root in true_roots_after},
        "checkpoint": str(checkpoint),
        "checkpoint_sha256": sha256_file(checkpoint),
        "wall_seconds": time.monotonic() - began,
    }
    write_json(work_dir / f"depth{target_depth}_result.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-depth", action="store_true")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--fixture-index", type=int, default=19)
    parser.add_argument("--descendants-per-root", type=int,
                        default=DESCENDANTS_PER_ROOT)
    parser.add_argument("--root-chunk", type=int, default=ROOT_CHUNK)
    parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK_DIR)
    args = parser.parse_args()
    if not args.run_depth:
        parser.error("use --run-depth")
    result = run_depth(args.source, args.fixture_index,
                       args.descendants_per_root, args.root_chunk,
                       work_dir=args.work_dir)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
