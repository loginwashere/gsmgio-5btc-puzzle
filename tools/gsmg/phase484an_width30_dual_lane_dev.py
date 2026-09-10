#!/usr/bin/env python3
"""Truth-blind dual-lane width-30 development solver.

Combines the independently successful fixture-15 parent bridge and fixture-19
root-lineage beam under one fixed schedule. Synthetic truth is used only in
post-stage diagnostics inherited from the development probes; no branch or cut
depends on it. This module never imports or scores FAED or holdout fixtures.
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
import phase484ac_width30_partition_constrained_board_probe as constrained
import phase484ad_width30_parent_reserved_bridge as bridge
import phase484ae_width30_checkpointed_rolling as rolling
import phase484ai_width30_early_switch_full_solve as full
import phase484am_width30_root_lineage_beam as lineage

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_WORK_DIR = SCRIPT_DIR.parents[1] / "_work" / "phase484an"

SCHEDULE = {
    "switch_depth": 6,
    "keep_board": 524288,
    "depth7_coarse_keep": 1310720,
    "coarse_restarts": 3,
    "coarse_iterations": 2000,
    "depth7_refine_keep": 655360,
    "refine_restarts": 4,
    "refine_iterations": 10000,
    "lane_a_depth7_parent_keep": 32768,
    "lane_a_depth8_children_per_parent": 40,
    "lane_a_depth8_keep": 262144,
    "lane_a_bridge_parent_keep": 65536,
    "lane_a_bridge_children_per_parent": 8,
    "lane_b_descendants_per_root": 4,
    "lane_b_depth9_root_keep": 262144,
    "lane_b_depth10_root_keep": 65536,
    "merge_depth12_keep": 262144,
    "depth13_16_keep": 262144,
    "depth17_30_keep": 4096,
    "final_top": 8,
    "final_restarts": 4,
    "final_iterations": 10000,
}


def schedule_sha256() -> str:
    encoded = json.dumps(SCHEDULE, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def save_population(path: Path, paths, scores, **extra) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp.npz")
    np.savez(temporary, paths=np.asarray(paths, dtype=np.uint8),
             scores=np.asarray(scores, dtype=np.float64), **extra)
    temporary.replace(path)
    return path


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prune_root_population(source: Path, destination: Path,
                          keep_roots: int) -> dict:
    """Keep roots with the best descendant score and remap IDs densely."""
    source, destination = Path(source), Path(destination)
    with np.load(source) as payload:
        paths = np.asarray(payload["paths"], dtype=np.uint8)
        scores = np.asarray(payload["scores"], dtype=np.float64)
        roots = np.asarray(payload["root_ids"], dtype=np.int64)
        original = (np.asarray(payload["original_root_ids"], dtype=np.int64)
                    if "original_root_ids" in payload
                    else np.arange(int(roots.max()) + 1, dtype=np.int64))
    root_count = int(roots.max()) + 1
    if not np.array_equal(np.unique(roots), np.arange(root_count)):
        raise ValueError("root IDs must be a dense zero-based range")
    if original.shape != (root_count,):
        raise ValueError("original-root mapping has wrong length")
    if not 0 < keep_roots <= root_count:
        raise ValueError("keep_roots outside available root range")
    best = np.full(root_count, -np.inf)
    np.maximum.at(best, roots, scores)
    ranked = np.lexsort((np.arange(root_count), -best))
    chosen = np.sort(ranked[:keep_roots])
    mask = np.isin(roots, chosen)
    new_roots = np.searchsorted(chosen, roots[mask])
    save_population(destination, paths[mask], scores[mask],
                    root_ids=new_roots,
                    original_root_ids=original[chosen])
    return {
        "source": str(source),
        "source_sha256": sha256_file(source),
        "root_count_before": root_count,
        "root_count_after": keep_roots,
        "path_count_after": int(mask.sum()),
        "destination": str(destination),
        "destination_sha256": sha256_file(destination),
    }


def merge_populations(sources: list[Path], destination: Path,
                      keep: int) -> dict:
    populations = [rolling.load_checkpoint(path)[:2] for path in sources]
    paths = np.concatenate([item[0] for item in populations])
    scores = np.concatenate([item[1] for item in populations])
    # Scores come from independent anneals. Keep the strongest copy of an
    # exact path before invoking the shared selector, whose within-pass dedupe
    # intentionally keeps first occurrence.
    ranked = width30.ranked_indices(paths, scores)
    best_unique = ranked[width30.unique_path_indices(paths[ranked])]
    paths, scores = paths[best_unique], scores[best_unique]
    selected_paths, selected_scores, unique = width30.select_diverse(
        paths, scores, keep)
    save_population(destination, selected_paths, selected_scores)
    return {
        "sources": [str(path) for path in sources],
        "source_counts": [len(item[0]) for item in populations],
        "unique_before_cut": unique,
        "keep": len(selected_paths),
        "destination": str(destination),
        "destination_sha256": sha256_file(destination),
    }


def lane_a_depth8(source: Path, fixture_index: int, work_dir: Path) -> dict:
    """Fixture-15 mechanism: broad parent-local depth-8 refinement."""
    paths7, scores7, source_sha256 = rolling.load_checkpoint(source)
    if paths7.shape[1] != 7:
        raise ValueError("lane A requires a depth-7 population")
    ranked = width30.ranked_indices(paths7, scores7)
    parents = paths7[ranked[:SCHEDULE["lane_a_depth7_parent_keep"]]]
    fixture = width30.width30_fixture(fixture_index, "dev")
    truth = prefix.order_to_sequence(fixture["order"])
    blocks = prefix.blocks_from_observed(fixture)
    pair = tuple(fixture["pair"])
    quad, _ = base.load_language_model()
    began = time.monotonic()
    children, parent_ids = bridge.expand_with_parent_indices(parents)
    coarse = early.board_screen(
        children, blocks, pair, quad, SCHEDULE["coarse_restarts"],
        SCHEDULE["coarse_iterations"], constrained.GPU_BINARY)
    reserved, reserved_scores = bridge.reserve_local_children(
        children, coarse, parent_ids,
        SCHEDULE["lane_a_depth8_children_per_parent"])
    refined = early.board_screen(
        reserved, blocks, pair, quad, SCHEDULE["refine_restarts"],
        SCHEDULE["refine_iterations"], constrained.GPU_BINARY)
    selected, selected_scores, unique = width30.select_diverse(
        reserved, refined, SCHEDULE["lane_a_depth8_keep"])
    checkpoint = save_population(work_dir / "depth8_selected.npz",
                                 selected, selected_scores)
    return {
        "source": str(source), "source_sha256": source_sha256,
        "parent_count": len(parents), "child_count": len(children),
        "reserved_count": len(reserved), "unique_before_cut": unique,
        "before_cut": early.recovery_record(reserved, refined, truth, 8),
        "after_cut": early.recovery_record(selected, selected_scores, truth, 8),
        "checkpoint": str(checkpoint), "checkpoint_sha256": sha256_file(checkpoint),
        "wall_seconds": time.monotonic() - began,
    }


def run_lane_a(source: Path, fixture_index: int, work_dir: Path) -> Path:
    stage8 = lane_a_depth8(source, fixture_index, work_dir)
    write_json(work_dir / "stage_depth8.json", stage8)
    to10 = rolling.run(
        Path(stage8["checkpoint"]), fixture_index, 10,
        SCHEDULE["lane_a_depth8_keep"], SCHEDULE["coarse_restarts"],
        SCHEDULE["coarse_iterations"], constrained.GPU_BINARY, work_dir, False)
    write_json(work_dir / "stage_d9_d10.json", to10)
    stage12 = bridge.run(
        work_dir / "depth10_selected.npz", fixture_index,
        SCHEDULE["lane_a_bridge_parent_keep"],
        SCHEDULE["lane_a_bridge_children_per_parent"],
        SCHEDULE["merge_depth12_keep"], SCHEDULE["coarse_restarts"],
        SCHEDULE["coarse_iterations"], constrained.GPU_BINARY, work_dir)
    write_json(work_dir / "stage_d11_d12.json", stage12)
    return work_dir / "depth12_selected.npz"


def run_lane_b(source: Path, fixture_index: int, work_dir: Path) -> Path:
    paths7, scores7, _ = rolling.load_checkpoint(source)
    if paths7.shape[1] != 7:
        raise ValueError("lane B requires a depth-7 population")
    root7 = save_population(
        work_dir / "depth7_root_beam4.npz", paths7, scores7,
        root_ids=np.arange(len(paths7), dtype=np.int64),
        original_root_ids=np.arange(len(paths7), dtype=np.int64))
    depth8 = lineage.run_depth(root7, fixture_index, 4, 16384,
                               work_dir=work_dir)["checkpoint"]
    depth9 = lineage.run_depth(Path(depth8), fixture_index, 4, 16384,
                               work_dir=work_dir)["checkpoint"]
    prune9 = prune_root_population(
        Path(depth9), work_dir / "depth9_pruned262144.npz",
        SCHEDULE["lane_b_depth9_root_keep"])
    write_json(work_dir / "stage_prune_depth9.json", prune9)
    depth10 = lineage.run_depth(Path(prune9["destination"]), fixture_index,
                                4, 16384, work_dir=work_dir)["checkpoint"]
    prune10 = prune_root_population(
        Path(depth10), work_dir / "depth10_pruned65536.npz",
        SCHEDULE["lane_b_depth10_root_keep"])
    write_json(work_dir / "stage_prune_depth10.json", prune10)
    depth11 = lineage.run_depth(Path(prune10["destination"]), fixture_index,
                                4, 16384, work_dir=work_dir)["checkpoint"]
    stage12 = rolling.run(
        Path(depth11), fixture_index, 12, SCHEDULE["merge_depth12_keep"],
        SCHEDULE["coarse_restarts"], SCHEDULE["coarse_iterations"],
        constrained.GPU_BINARY, work_dir, False)
    write_json(work_dir / "stage_release_depth12.json", stage12)
    return work_dir / "depth12_selected.npz"


def run_fixture(fixture_index: int, work_dir: Path) -> dict:
    work_dir = Path(work_dir)
    initial_dir, lane_a_dir = work_dir / "initial", work_dir / "lane_a"
    lane_b_dir, merged_dir = work_dir / "lane_b", work_dir / "merged"
    for directory in (initial_dir, lane_a_dir, lane_b_dir, merged_dir):
        directory.mkdir(parents=True, exist_ok=True)
    began = time.monotonic()
    initial = full.initial_to_depth7(
        fixture_index, initial_dir, schedule=SCHEDULE)
    write_json(initial_dir / "stage_initial_to_d7.json", initial)
    depth7 = Path(initial["depth7_refined_checkpoint"])
    lane_a12 = run_lane_a(depth7, fixture_index, lane_a_dir)
    lane_b12 = run_lane_b(depth7, fixture_index, lane_b_dir)
    merged12 = merged_dir / "depth12_merged.npz"
    merge = merge_populations([lane_a12, lane_b12], merged12,
                              SCHEDULE["merge_depth12_keep"])
    write_json(merged_dir / "stage_merge_depth12.json", merge)
    middle = rolling.run(
        merged12, fixture_index, 16, SCHEDULE["depth13_16_keep"],
        SCHEDULE["coarse_restarts"], SCHEDULE["coarse_iterations"],
        constrained.GPU_BINARY, merged_dir, False)
    write_json(merged_dir / "stage_d13_d16.json", middle)
    tail = rolling.run(
        merged_dir / "depth16_selected.npz", fixture_index, 30,
        SCHEDULE["depth17_30_keep"], SCHEDULE["coarse_restarts"],
        SCHEDULE["coarse_iterations"], constrained.GPU_BINARY, merged_dir, False)
    write_json(merged_dir / "stage_d17_d30.json", tail)
    final = rolling.resolve_final(
        merged_dir / "depth30_selected.npz", fixture_index,
        SCHEDULE["final_top"], SCHEDULE["final_restarts"],
        SCHEDULE["final_iterations"])
    write_json(merged_dir / "stage_final.json", final)
    result = {
        "phase": "484AN",
        "status": "development_dual_lane_complete_not_frozen",
        "faed_scored": False, "holdout_consumed": False,
        "fixture_index": fixture_index, "schedule": SCHEDULE,
        "schedule_sha256": schedule_sha256(),
        "initial_depth7_true_segments": initial["depth7"]["refine"]["after_selection"]["true_segments"],
        "middle_truth_survived": middle["truth_survived"],
        "tail_truth_survived": tail["truth_survived"],
        "exact_order_final_rank": final["exact_order_final_rank"],
        "top1_exact_order": final["top1_exact_order"],
        "top1_plaintext_accuracy": final["top1_plaintext_accuracy"],
        "wall_seconds": time.monotonic() - began,
    }
    write_json(work_dir / "result.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--fixture-index", type=int)
    parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK_DIR)
    args = parser.parse_args()
    if not args.run or args.fixture_index is None:
        parser.error("--run and --fixture-index are required")
    print(json.dumps(run_fixture(args.fixture_index, args.work_dir), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
