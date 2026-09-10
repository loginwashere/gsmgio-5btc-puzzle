#!/usr/bin/env python3
"""Resumable non-training development screen for the width-30 depth-6 switch.

Runs the truth-blind initial stage from Phase 484AI unchanged on exact-profile
development fixtures 13..22. Synthetic truth is inspected only after each
fixed search stage has completed. No holdout fixture or FAED data is used.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import phase484ai_width30_early_switch_full_solve as full
import phase484y_width30_feasibility_probe as width30

FIXTURE_INDICES = tuple(range(13, 23))
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_WORK_DIR = SCRIPT_DIR.parents[1] / "_work" / "phase484aj"


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def summarize_initial(record: dict) -> dict:
    if record.get("phase") != "484AI":
        raise ValueError("unexpected initial-stage phase")
    if record.get("schedule_sha256") != full.schedule_sha256():
        raise ValueError("initial-stage schedule drift")
    refined = record["depth7"]["refine"]["after_selection"]
    return {
        "fixture_index": record["fixture_index"],
        "schedule_sha256": record["schedule_sha256"],
        "depth6_true_segments": record["switch_stage"]["after_board_selection"]["true_segments"],
        "depth7_coarse_true_segments": record["depth7"]["after_selection"]["true_segments"],
        "depth7_refined_true_segments": refined["true_segments"],
        "survived_depth7_refined": bool(refined["true_segments"]),
        "wall_seconds": record["wall_seconds"],
    }


def load_completed(path: Path, fixture_index: int) -> dict:
    record = json.loads(path.read_text())
    if record.get("fixture_index") != fixture_index:
        raise ValueError(f"fixture mismatch in {path}")
    summarize_initial(record)
    return record


def build_summary(records: list[dict], began: float) -> dict:
    rows = [summarize_initial(record) for record in records]
    completed = {row["fixture_index"] for row in rows}
    expected_prefix = set(FIXTURE_INDICES[:len(rows)])
    if completed != expected_prefix:
        raise ValueError("completed fixture set is not the expected prefix")
    return {
        "phase": "484AJ",
        "status": ("development_depth6_screen_complete_not_frozen"
                   if len(rows) == len(FIXTURE_INDICES)
                   else "development_depth6_screen_in_progress_not_frozen"),
        "faed_scored": False,
        "holdout_consumed": False,
        "fixture_split": "dev",
        "fixture_indices": list(FIXTURE_INDICES),
        "training_indices": list(width30.TRAIN_INDICES),
        "schedule": full.SCHEDULE,
        "schedule_sha256": full.schedule_sha256(),
        "records": rows,
        "survivor_indices": [row["fixture_index"] for row in rows
                             if row["survived_depth7_refined"]],
        "survived_count": sum(row["survived_depth7_refined"] for row in rows),
        "completed_count": len(rows),
        "batch_wall_seconds": time.monotonic() - began,
    }


def run(work_dir: Path = DEFAULT_WORK_DIR) -> dict:
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    summary_path = work_dir / "result.json"
    began = time.monotonic()
    models = width30.train_models()
    records = []
    for fixture_index in FIXTURE_INDICES:
        fixture_dir = work_dir / f"i{fixture_index}"
        record_path = fixture_dir / "initial_to_depth7.json"
        if record_path.exists():
            record = load_completed(record_path, fixture_index)
        else:
            fixture_dir.mkdir(parents=True, exist_ok=True)
            record = full.initial_to_depth7(fixture_index, fixture_dir, models=models)
            if record.get("fixture_index") != fixture_index:
                raise ValueError("initial stage returned wrong fixture")
            summarize_initial(record)
            write_json(record_path, record)
        records.append(record)
        summary = build_summary(records, began)
        write_json(summary_path, summary)
        row = summary["records"][-1]
        print("fixture", fixture_index,
              "d6", row["depth6_true_segments"],
              "d7", row["depth7_coarse_true_segments"],
              "refined", row["depth7_refined_true_segments"],
              "seconds", round(row["wall_seconds"], 2), flush=True)
    return build_summary(records, began)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK_DIR)
    args = parser.parse_args()
    if not args.run:
        parser.error("use --run")
    result = run(args.work_dir)
    write_json(args.work_dir / "result.json", result)
    print(json.dumps({
        "status": result["status"],
        "completed_count": result["completed_count"],
        "survived_count": result["survived_count"],
        "survivor_indices": result["survivor_indices"],
        "schedule_sha256": result["schedule_sha256"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
