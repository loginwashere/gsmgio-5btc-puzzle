#!/usr/bin/env python3
"""Development: full-depth solve attempt using the depth-6 board switch.

Phase 484AH showed switching to board-objective scoring at depth 6 instead of
depth 7 rescues the true window for fixtures that previously failed at the
depth-7 invariant cut: fixture 22's true depth-7 rank went from lost entirely
to rank 1 of 12.6M, fixture 21's to rank 475 of 12.6M (fixture 19 remained a
counter-example -- board scoring made its rank worse, not better).

This composes that earlier switch with the already-validated 484AD (parent-
reserved bridge) and 484AE (checkpointed rolling) stages -- the same recipe
that took fixture 15 to a full exact-order, 100%-plaintext solve -- to see
whether fixtures 21 and 22 reach a full solve too. Development only: no FAED
import, no holdout fixture; synthetic truth is used only for recovery
metrics along the way.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import phase484a_raw_symbol_vic_solver as base
import phase484j_constructive_prefix_beam_probe as prefix
import phase484y_width30_feasibility_probe as width30
import phase484z_width30_early_board_switch_probe as early
import phase484ah_width30_early_switch_depth_probe as switch6
import phase484ad_width30_parent_reserved_bridge as bridge
import phase484ae_width30_checkpointed_rolling as rolling
import phase484ac_width30_partition_constrained_board_probe as constrained

SCRIPT_DIR = Path(__file__).resolve().parent

SCHEDULE = {
    "switch_depth": 6,
    "keep_board": 262144,
    "depth7_coarse_keep": 1310720,
    "coarse_restarts": 3,
    "coarse_iterations": 2000,
    "depth7_refine_keep": 262144,
    "refine_restarts": 4,
    "refine_iterations": 10000,
    "depth8_10_keep": 262144,
    "bridge_parent_keep": 65536,
    "bridge_children_per_parent": 8,
    "depth12_16_keep": 262144,
    "depth17_30_keep": 4096,
    "final_top": 8,
    "final_restarts": 4,
    "final_iterations": 10000,
}


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n")


def require_file(path: Path, label: str) -> Path:
    if not path.is_file():
        raise RuntimeError(f"{label} did not produce {path}")
    return path


def initial_to_depth7(fixture_index, work_dir, models=None) -> dict:
    """Depth 4 -> switch at depth 6 -> board-anneal through a refined depth-7
    checkpoint, mirroring 484Z's depth-7-switch schedule shifted one depth
    earlier."""
    fixture = width30.width30_fixture(fixture_index, "dev")
    if models is None:
        models = width30.train_models()
    truth = prefix.order_to_sequence(fixture["order"])
    quad, _ = base.load_language_model()
    began = time.monotonic()

    paths6, invariant6, prefix_diagnostics, blocks, pair = (
        switch6.invariant_to_switch_depth(
            fixture, models, SCHEDULE["switch_depth"]))
    invariant_selected = early.recovery_record(
        paths6, invariant6, truth, SCHEDULE["switch_depth"])

    stage_began = time.monotonic()
    board6 = early.board_screen(
        paths6, blocks, pair, quad, SCHEDULE["coarse_restarts"],
        SCHEDULE["coarse_iterations"], constrained.GPU_BINARY)
    board6_seconds = time.monotonic() - stage_began
    board6_raw = early.recovery_record(paths6, board6, truth, SCHEDULE["switch_depth"])
    paths6, board6, unique6 = width30.select_diverse(
        paths6, board6, SCHEDULE["keep_board"])
    board6_selected = early.recovery_record(paths6, board6, truth, SCHEDULE["switch_depth"])

    depth7 = None
    depth7_refined_checkpoint = None
    if board6_selected["true_segments"]:
        stage_began = time.monotonic()
        paths7 = width30.expand_bidirectional(paths6)
        board7 = early.board_screen(
            paths7, blocks, pair, quad, SCHEDULE["coarse_restarts"],
            SCHEDULE["coarse_iterations"], constrained.GPU_BINARY)
        raw7 = early.recovery_record(paths7, board7, truth, 7)
        paths7, board7, unique7 = width30.select_diverse(
            paths7, board7, SCHEDULE["depth7_coarse_keep"])
        selected7 = early.recovery_record(paths7, board7, truth, 7)
        depth7_seconds = time.monotonic() - stage_began

        refine7 = None
        if selected7["true_segments"]:
            stage_began = time.monotonic()
            refined7 = early.board_screen(
                paths7, blocks, pair, quad, SCHEDULE["refine_restarts"],
                SCHEDULE["refine_iterations"], constrained.GPU_BINARY)
            raw_refined7 = early.recovery_record(paths7, refined7, truth, 7)
            refined_paths7, refined_scores7, refine_unique = width30.select_diverse(
                paths7, refined7, SCHEDULE["depth7_refine_keep"])
            refined_selected7 = early.recovery_record(
                refined_paths7, refined_scores7, truth, 7)
            depth7_refined_checkpoint = early.save_checkpoint(
                work_dir, "depth7_refined", refined_paths7, refined_scores7)
            refine7 = {
                "restarts": SCHEDULE["refine_restarts"],
                "iterations": SCHEDULE["refine_iterations"],
                "keep": SCHEDULE["depth7_refine_keep"],
                "generated_unique": refine_unique,
                "before_selection": raw_refined7,
                "after_selection": refined_selected7,
                "checkpoint": depth7_refined_checkpoint,
                "seconds": time.monotonic() - stage_began,
            }
        depth7 = {
            "generated_unique": unique7,
            "before_selection": raw7,
            "after_selection": selected7,
            "keep": SCHEDULE["depth7_coarse_keep"],
            "seconds": depth7_seconds,
            "refine": refine7,
        }

    return {
        "phase": "484AI",
        "status": "development_early_switch_full_solve_not_frozen",
        "faed_scored": False,
        "holdout_consumed": False,
        "fixture_index": fixture_index,
        "prefix_diagnostics": prefix_diagnostics,
        "switch_stage": {
            "depth": SCHEDULE["switch_depth"],
            "after_invariant_selection": invariant_selected,
            "board_objective_before_selection": board6_raw,
            "after_board_selection": board6_selected,
            "seconds": board6_seconds,
        },
        "depth7": depth7,
        "depth7_refined_checkpoint": depth7_refined_checkpoint,
        "wall_seconds": time.monotonic() - began,
    }


def run_fixture(fixture_index: int, work_dir: Path,
                output: Path | None = None) -> dict:
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    output = output or work_dir / "result.json"
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing result: {output}")
    began = time.monotonic()

    initial = initial_to_depth7(fixture_index, work_dir)
    write_json(work_dir / "stage_initial_to_d7.json", initial)
    if not initial["depth7_refined_checkpoint"]:
        summary = {
            "phase": "484AI",
            "status": "development_early_switch_full_solve_not_frozen",
            "faed_scored": False,
            "holdout_consumed": False,
            "fixture_index": fixture_index,
            "schedule": SCHEDULE,
            "stopped_at": "initial_to_depth7",
            "exact_order_final_rank": None,
            "top1_exact_order": False,
            "top1_plaintext_accuracy": None,
            "wall_seconds": time.monotonic() - began,
            "work_dir": str(work_dir),
        }
        write_json(output, summary)
        return summary
    depth7 = require_file(Path(initial["depth7_refined_checkpoint"]),
                          "initial stage")

    to_depth10 = rolling.run(
        source=depth7, fixture_index=fixture_index, max_depth=10,
        keep=SCHEDULE["depth8_10_keep"], restarts=SCHEDULE["coarse_restarts"],
        iterations=SCHEDULE["coarse_iterations"], binary=constrained.GPU_BINARY,
        checkpoint_dir=work_dir, stop_on_truth_loss=False)
    write_json(work_dir / "stage_d8_d10.json", to_depth10)
    depth10 = require_file(work_dir / "depth10_selected.npz", "depth8-10 stage")

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
        keep=SCHEDULE["depth12_16_keep"], restarts=SCHEDULE["coarse_restarts"],
        iterations=SCHEDULE["coarse_iterations"], binary=constrained.GPU_BINARY,
        checkpoint_dir=work_dir, stop_on_truth_loss=False)
    write_json(work_dir / "stage_d13_d16.json", middle)
    depth16 = require_file(work_dir / "depth16_selected.npz", "middle stage")

    tail = rolling.run(
        source=depth16, fixture_index=fixture_index, max_depth=30,
        keep=SCHEDULE["depth17_30_keep"], restarts=SCHEDULE["coarse_restarts"],
        iterations=SCHEDULE["coarse_iterations"], binary=constrained.GPU_BINARY,
        checkpoint_dir=work_dir, stop_on_truth_loss=False)
    write_json(work_dir / "stage_d17_d30.json", tail)
    depth30 = require_file(work_dir / "depth30_selected.npz", "tail stage")

    final = rolling.resolve_final(
        depth30, fixture_index=fixture_index, top=SCHEDULE["final_top"],
        restarts=SCHEDULE["final_restarts"],
        iterations=SCHEDULE["final_iterations"])
    write_json(work_dir / "stage_final_resolve.json", final)

    summary = {
        "phase": "484AI",
        "status": "development_early_switch_full_solve_not_frozen",
        "faed_scored": False,
        "holdout_consumed": False,
        "fixture_index": fixture_index,
        "schedule": SCHEDULE,
        "truth_survival": {
            "depth7_refined": initial["depth7"]["refine"]["after_selection"]["true_segments"],
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
    write_json(output, summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--fixture-index", type=int)
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.run or args.fixture_index is None or args.work_dir is None:
        parser.error("--run, --fixture-index, and --work-dir are required")
    result = run_fixture(args.fixture_index, args.work_dir, args.output)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
