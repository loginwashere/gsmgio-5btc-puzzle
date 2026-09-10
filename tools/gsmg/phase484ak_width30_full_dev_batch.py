#!/usr/bin/env python3
"""Resumable full-depth continuation of Phase 484AJ development survivors.

The input screen already ran the fixed, truth-blind depth-6/depth-7 search on
non-training dev fixtures 13..22. This batch continues every post-hoc survivor
from its saved depth-7 checkpoint through the unchanged Phase 484AI bridge,
rolling extension, and final resolution. Survivor filtering is only a
synthetic development compute shortcut; it is not a deployable selector.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import phase484ai_width30_early_switch_full_solve as full
import phase484ad_width30_parent_reserved_bridge as bridge
import phase484ae_width30_checkpointed_rolling as rolling
import phase484ac_width30_partition_constrained_board_probe as constrained

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_SCREEN = SCRIPT_DIR.parents[1] / "_work" / "phase484aj" / "result.json"
DEFAULT_WORK_DIR = SCRIPT_DIR.parents[1] / "_work" / "phase484ak"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def load_screen(path: Path) -> tuple[dict, str]:
    path = Path(path)
    screen = json.loads(path.read_text())
    if screen.get("status") != "development_depth6_screen_complete_not_frozen":
        raise ValueError("screen is not complete")
    if screen.get("faed_scored") or screen.get("holdout_consumed"):
        raise ValueError("screen crossed the development-only boundary")
    if screen.get("schedule_sha256") != full.schedule_sha256():
        raise ValueError("screen schedule drift")
    indices = screen.get("fixture_indices")
    if indices != list(range(13, 23)):
        raise ValueError("unexpected screen fixture set")
    survivors = [row["fixture_index"] for row in screen.get("records", [])
                 if row.get("survived_depth7_refined")]
    if survivors != screen.get("survivor_indices"):
        raise ValueError("screen survivor list does not match records")
    return screen, sha256_file(path)


def continue_fixture(fixture_index: int, source: Path, work_dir: Path) -> dict:
    work_dir.mkdir(parents=True, exist_ok=True)
    began = time.monotonic()

    to_depth10 = rolling.run(
        source=source, fixture_index=fixture_index, max_depth=10,
        keep=full.SCHEDULE["depth8_10_keep"],
        restarts=full.SCHEDULE["coarse_restarts"],
        iterations=full.SCHEDULE["coarse_iterations"],
        binary=constrained.GPU_BINARY, checkpoint_dir=work_dir,
        stop_on_truth_loss=False)
    write_json(work_dir / "stage_d8_d10.json", to_depth10)
    depth10 = full.require_file(work_dir / "depth10_selected.npz", "depth8-10 stage")

    bridged = bridge.run(
        source=depth10, fixture_index=fixture_index,
        parent_keep=full.SCHEDULE["bridge_parent_keep"],
        children_per_parent=full.SCHEDULE["bridge_children_per_parent"],
        depth12_keep=full.SCHEDULE["depth12_16_keep"],
        restarts=full.SCHEDULE["coarse_restarts"],
        iterations=full.SCHEDULE["coarse_iterations"],
        binary=constrained.GPU_BINARY, checkpoint_dir=work_dir)
    write_json(work_dir / "stage_bridge_d11_d12.json", bridged)
    depth12 = full.require_file(work_dir / "depth12_selected.npz", "bridge stage")

    middle = rolling.run(
        source=depth12, fixture_index=fixture_index, max_depth=16,
        keep=full.SCHEDULE["depth12_16_keep"],
        restarts=full.SCHEDULE["coarse_restarts"],
        iterations=full.SCHEDULE["coarse_iterations"],
        binary=constrained.GPU_BINARY, checkpoint_dir=work_dir,
        stop_on_truth_loss=False)
    write_json(work_dir / "stage_d13_d16.json", middle)
    depth16 = full.require_file(work_dir / "depth16_selected.npz", "middle stage")

    tail = rolling.run(
        source=depth16, fixture_index=fixture_index, max_depth=30,
        keep=full.SCHEDULE["depth17_30_keep"],
        restarts=full.SCHEDULE["coarse_restarts"],
        iterations=full.SCHEDULE["coarse_iterations"],
        binary=constrained.GPU_BINARY, checkpoint_dir=work_dir,
        stop_on_truth_loss=False)
    write_json(work_dir / "stage_d17_d30.json", tail)
    depth30 = full.require_file(work_dir / "depth30_selected.npz", "tail stage")

    final = rolling.resolve_final(
        depth30, fixture_index=fixture_index, top=full.SCHEDULE["final_top"],
        restarts=full.SCHEDULE["final_restarts"],
        iterations=full.SCHEDULE["final_iterations"])
    write_json(work_dir / "stage_final_resolve.json", final)

    return {
        "phase": "484AK",
        "status": "development_full_continuation_complete_not_frozen",
        "faed_scored": False,
        "holdout_consumed": False,
        "fixture_index": fixture_index,
        "source": str(source),
        "source_sha256": sha256_file(source),
        "schedule": full.SCHEDULE,
        "schedule_sha256": full.schedule_sha256(),
        "truth_survival": {
            "depth10": to_depth10["depth_diagnostics"][-1]["after_selection"]["true_segments"],
            "depth11": bridged["depth11"]["after_reservation"]["true_segments"],
            "depth12": bridged["depth12"]["after_selection"]["true_segments"],
            "depth16": middle["depth_diagnostics"][-1]["after_selection"]["true_segments"],
            "depth30": tail["depth_diagnostics"][-1]["after_selection"]["true_segments"],
        },
        "exact_order_final_rank": final["exact_order_final_rank"],
        "top1_exact_order": final["top1_exact_order"],
        "top1_plaintext_accuracy": final["top1_plaintext_accuracy"],
        "wall_seconds": time.monotonic() - began,
        "work_dir": str(work_dir),
    }


def validate_completed(record: dict, fixture_index: int) -> None:
    if record.get("phase") != "484AK" or record.get("fixture_index") != fixture_index:
        raise ValueError("completed record identity mismatch")
    if record.get("schedule_sha256") != full.schedule_sha256():
        raise ValueError("completed record schedule drift")
    if record.get("faed_scored") or record.get("holdout_consumed"):
        raise ValueError("completed record crossed development-only boundary")


def build_summary(records: list[dict], survivors: list[int], screen_path: Path,
                  screen_sha256: str, began: float) -> dict:
    for record, fixture_index in zip(records, survivors):
        validate_completed(record, fixture_index)
    if [record["fixture_index"] for record in records] != survivors[:len(records)]:
        raise ValueError("completed records are not the survivor prefix")
    return {
        "phase": "484AK",
        "status": ("development_full_batch_complete_not_frozen"
                   if len(records) == len(survivors)
                   else "development_full_batch_in_progress_not_frozen"),
        "faed_scored": False,
        "holdout_consumed": False,
        "selection_policy": "post-hoc depth7 truth survival; development compute shortcut only",
        "screen": str(screen_path),
        "screen_sha256": screen_sha256,
        "schedule": full.SCHEDULE,
        "schedule_sha256": full.schedule_sha256(),
        "survivor_indices": survivors,
        "records": records,
        "completed_count": len(records),
        "exact_top1_count": sum(record["top1_exact_order"] for record in records),
        "batch_wall_seconds": time.monotonic() - began,
    }


def run(screen_path: Path = DEFAULT_SCREEN,
        work_dir: Path = DEFAULT_WORK_DIR) -> dict:
    screen_path, work_dir = Path(screen_path), Path(work_dir)
    screen, screen_sha256 = load_screen(screen_path)
    survivors = screen["survivor_indices"]
    work_dir.mkdir(parents=True, exist_ok=True)
    began = time.monotonic()
    records = []
    for fixture_index in survivors:
        fixture_dir = work_dir / f"i{fixture_index}"
        result_path = fixture_dir / "result.json"
        if result_path.exists():
            record = json.loads(result_path.read_text())
            validate_completed(record, fixture_index)
        else:
            source = screen_path.parent / f"i{fixture_index}" / "depth7_refined.npz"
            if not source.is_file():
                raise FileNotFoundError(f"missing depth-7 screen checkpoint: {source}")
            record = continue_fixture(fixture_index, source, fixture_dir)
            validate_completed(record, fixture_index)
            write_json(result_path, record)
        records.append(record)
        summary = build_summary(records, survivors, screen_path, screen_sha256, began)
        write_json(work_dir / "result.json", summary)
        print("fixture", fixture_index,
              "exact_rank", record["exact_order_final_rank"],
              "top1", record["top1_exact_order"],
              "accuracy", record["top1_plaintext_accuracy"],
              "seconds", round(record["wall_seconds"], 2), flush=True)
    return build_summary(records, survivors, screen_path, screen_sha256, began)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--screen", type=Path, default=DEFAULT_SCREEN)
    parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK_DIR)
    args = parser.parse_args()
    if not args.run:
        parser.error("use --run")
    result = run(args.screen, args.work_dir)
    write_json(args.work_dir / "result.json", result)
    print(json.dumps({
        "status": result["status"],
        "completed_count": result["completed_count"],
        "exact_top1_count": result["exact_top1_count"],
        "survivor_indices": result["survivor_indices"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
