#!/usr/bin/env python3
"""Fixed-schedule width-30 development generalization runner.

This composes the independently tested 484Z/AD/AE stages without adapting any
budget to the fixture's known truth. It is development-only: no FAED import and
no holdout fixture. Synthetic truth is used only for recovery metrics.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import phase484z_width30_early_board_switch_probe as early
import phase484ad_width30_parent_reserved_bridge as bridge
import phase484ae_width30_checkpointed_rolling as rolling
import phase484ac_width30_partition_constrained_board_probe as constrained

SCRIPT_DIR = Path(__file__).resolve().parent

# Frozen after fixture 15 and before fresh generalization fixtures.
SCHEDULE = {
    "invariant_keep": 262144,
    "depth6_keep": 524288,
    "depth7_preboard_keep": 1048576,
    "depth7_board_keep": 262144,
    "depth8_coarse_keep": 1310720,
    "coarse_restarts": 3,
    "coarse_iterations": 2000,
    "depth8_refine_keep": 262144,
    "refine_restarts": 4,
    "refine_iterations": 10000,
    "depth9_10_keep": 262144,
    "bridge_parent_keep": 65536,
    "bridge_children_per_parent": 8,
    "depth12_16_keep": 262144,
    "depth17_30_keep": 4096,
    "final_top": 8,
    "final_restarts": 4,
    "final_iterations": 10000,
}
# These valid, non-training fixtures appeared in older development probes but
# did not tune this partition/bridge schedule. They are a transfer set, not a
# pristine holdout.
TRANSFER_DEV_INDICES = (19, 21, 22)


def canonical_schedule() -> bytes:
    return json.dumps(SCHEDULE, sort_keys=True,
                      separators=(",", ":")).encode("ascii")


def schedule_sha256() -> str:
    return hashlib.sha256(canonical_schedule()).hexdigest()


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n")


def require_file(path: Path, label: str) -> Path:
    if not path.is_file():
        raise RuntimeError(f"{label} did not produce {path}")
    return path


def run_fixture(fixture_index: int, work_dir: Path,
                output: Path | None = None) -> dict:
    """Run the complete schedule, irrespective of truth survival."""
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    output = output or work_dir / "result.json"
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing result: {output}")
    began = time.monotonic()

    initial = early.run_fixture(
        fixture_index=fixture_index,
        keep=SCHEDULE["depth7_board_keep"],
        depth6_keep=SCHEDULE["depth6_keep"],
        depth7_keep=SCHEDULE["depth7_preboard_keep"],
        depth8_keep=SCHEDULE["depth8_coarse_keep"],
        restarts=SCHEDULE["coarse_restarts"],
        iterations=SCHEDULE["coarse_iterations"],
        depth8_restarts=SCHEDULE["coarse_restarts"],
        depth8_iterations=SCHEDULE["coarse_iterations"],
        board_binary=constrained.GPU_BINARY,
        refine_depth8=True,
        refine_depth8_keep=SCHEDULE["depth8_refine_keep"],
        refine_depth8_restarts=SCHEDULE["refine_restarts"],
        refine_depth8_iterations=SCHEDULE["refine_iterations"],
        probe_depth9=True,
        depth9_keep=SCHEDULE["depth9_10_keep"],
        depth9_restarts=SCHEDULE["coarse_restarts"],
        depth9_iterations=SCHEDULE["coarse_iterations"],
        rolling_max_depth=10,
        checkpoint_dir=work_dir,
        stop_on_truth_loss=False,
    )
    write_json(work_dir / "stage_initial_to_d10.json", initial)
    depth10 = require_file(work_dir / "depth10_selected.npz", "initial stage")

    bridged = bridge.run(
        source=depth10, fixture_index=fixture_index,
        parent_keep=SCHEDULE["bridge_parent_keep"],
        children_per_parent=SCHEDULE["bridge_children_per_parent"],
        depth12_keep=SCHEDULE["depth12_16_keep"],
        restarts=SCHEDULE["coarse_restarts"],
        iterations=SCHEDULE["coarse_iterations"],
        binary=constrained.GPU_BINARY, checkpoint_dir=work_dir)
    write_json(work_dir / "stage_bridge_d11_d12.json", bridged)
    depth12 = require_file(work_dir / "depth12_selected.npz", "bridge stage")

    middle = rolling.run(
        source=depth12, fixture_index=fixture_index, max_depth=16,
        keep=SCHEDULE["depth12_16_keep"],
        restarts=SCHEDULE["coarse_restarts"],
        iterations=SCHEDULE["coarse_iterations"],
        binary=constrained.GPU_BINARY, checkpoint_dir=work_dir,
        stop_on_truth_loss=False)
    write_json(work_dir / "stage_d13_d16.json", middle)
    depth16 = require_file(work_dir / "depth16_selected.npz", "middle stage")

    tail = rolling.run(
        source=depth16, fixture_index=fixture_index, max_depth=30,
        keep=SCHEDULE["depth17_30_keep"],
        restarts=SCHEDULE["coarse_restarts"],
        iterations=SCHEDULE["coarse_iterations"],
        binary=constrained.GPU_BINARY, checkpoint_dir=work_dir,
        stop_on_truth_loss=False)
    write_json(work_dir / "stage_d17_d30.json", tail)
    depth30 = require_file(work_dir / "depth30_selected.npz", "tail stage")

    final = rolling.resolve_final(
        depth30, fixture_index=fixture_index,
        top=SCHEDULE["final_top"],
        restarts=SCHEDULE["final_restarts"],
        iterations=SCHEDULE["final_iterations"])
    write_json(work_dir / "stage_final_resolve.json", final)

    summary = {
        "phase": "484AF",
        "status": "development_fixed_schedule_generalization",
        "faed_scored": False,
        "holdout_consumed": False,
        "fixture_index": fixture_index,
        "schedule": SCHEDULE,
        "schedule_sha256": schedule_sha256(),
        "truth_survival": {
            "depth7": initial["depth7"]["after_board_selection"]["true_segments"],
            "depth8": initial["depth8"]["strong_refine"]["after_selection"]["true_segments"],
            "depth10": initial["depth8"]["rolling_probe"][-1]["after_selection"]["true_segments"],
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
    write_json(output, summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--fixture-index", type=int)
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps({"schedule": SCHEDULE,
                          "schedule_sha256": schedule_sha256()}, indent=2))
        return 0
    if not args.run or args.fixture_index is None or args.work_dir is None:
        parser.error("--run, --fixture-index, and --work-dir are required")
    result = run_fixture(args.fixture_index, args.work_dir, args.output)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
