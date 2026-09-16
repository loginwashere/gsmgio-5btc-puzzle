#!/usr/bin/env python3
"""Phase 512K -- blind positive-recovery and crib-absent calibration for the
two remaining Phase-512 cribs (validation answer, creator macro message) at
width 15, using the Rust `crib_csp sweep` engine.

Per the Rust-port plan's gate: only a crib/width that (a) recovers its exact
planted pair/start/order with zero earlier false hits when run *blind*
(neither is supplied) and (b) closes a full crib-absent family with zero
hits and zero incomplete cells is eligible for a locked real-FAED run. This
phase supplies that evidence for the two remaining cribs; the credential was
already calibrated this way by Phase 512G's own locked run.

Every fixture here is synthetic (`phase512a.make_fixture` /
`phase512e.make_absent_fixture`); FAED itself is never referenced or scored,
though importing `phase512a` loads the `data` module that defines it.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import phase512a_transposition_crib_feasibility as phase512a
import phase512e_parallel_blind_crib as phase512e
import phase512i_rust_parity as phase512i
import phase512j_rust_sweep_validation as phase512j


SCRIPT_DIR = Path(__file__).resolve().parent
WORK_DIR = phase512j.WORK_DIR.parent / "phase512k"
RESULT = SCRIPT_DIR / "phase512k_result.json"
WIDTH = 15
NODE_LIMIT = 2_000_000
WORKERS = 16


def small_cross_check(fixture: dict, fixture_path: Path, start_begin: int,
                      pair_begin: int) -> bool:
    """A handful of cells cross-checked against Python before trusting a
    large Rust-only run, exactly as done for the credential in Phase 512J."""
    start_count = 2
    pair_count = 3
    python_checkpoint = phase512e.scan_fixture(
        fixture, workers=4, per_cell_node_limit=NODE_LIMIT,
        pair_indices=range(pair_begin, pair_begin + pair_count),
        start_begin=start_begin, start_count=start_count,
        checkpoint_path=None, pattern_shards=1)
    rust_checkpoint = phase512j.run_rust_sweep(
        fixture_path, start_begin, start_count, pair_begin, pair_count,
        NODE_LIMIT, workers=4)
    return (phase512j.canonical_python_cells(python_checkpoint)
            == phase512j.canonical_rust_cells(rust_checkpoint))


def calibrate_crib(crib_id: str) -> dict:
    phase512i.ensure_binary()
    positive = phase512a.make_fixture(crib_id, WIDTH)
    positive_path = WORK_DIR / f"{crib_id}_w{WIDTH}_positive.json"
    phase512i.export_fixture(positive, positive_path)

    true_pair = tuple(positive["pair"])
    true_pair_index = phase512a.base.ESCAPE_PAIRS.index(true_pair)
    true_start = positive["planted_raw_offset"]
    maximum_start = len(positive["observed"]) - len(positive["crib"])
    start_family_size = maximum_start + 1

    # Cross-check a few cells around the true (start, pair) before the long
    # blind run: catches a Python/Rust divergence cheaply rather than after
    # tens of minutes of compute.
    positive_small_match = small_cross_check(
        positive, positive_path,
        start_begin=max(0, true_start - 1),
        pair_begin=max(0, true_pair_index - 1))
    if not positive_small_match:
        raise AssertionError(f"{crib_id}: Python/Rust disagree on the small positive cross-check")

    # Blind positive recovery: neither pair nor start is supplied. The full
    # start-major, pair-parallel family is scanned from 0 until the sweep
    # stops (on a hit or exhaustion) -- exactly the real Phase 512G runner's
    # architecture, just with an unknown answer.
    positive_checkpoint_path = WORK_DIR / f"{crib_id}_w{WIDTH}_positive_checkpoint.json"
    if positive_checkpoint_path.exists():
        positive_checkpoint_path.unlink()
    started = time.monotonic()
    blind = phase512j.run_rust_sweep(
        positive_path, 0, start_family_size, 0, 36, NODE_LIMIT, WORKERS,
        checkpoint_path=positive_checkpoint_path)
    blind_elapsed = time.monotonic() - started

    hit_cells = blind["hit_cells"]
    blind_recovery = {
        "status": blind["status"],
        "hit_count": len(hit_cells),
        "starts_completed": blind["starts_completed"],
        "cells_completed": blind["pair_start_cells_completed"],
        "elapsed_seconds": blind_elapsed,
    }
    if len(hit_cells) == 1:
        hit = hit_cells[0]
        blind_recovery.update({
            "recovered_raw_start": hit["raw_start"],
            "recovered_pair": hit["pair"],
            "recovered_pair_index": hit["pair_index"],
            "planted_raw_start": true_start,
            "planted_pair": list(true_pair),
            "planted_pair_index": true_pair_index,
            "raw_start_matches": hit["raw_start"] == true_start,
            "pair_matches": hit["pair"] == list(true_pair),
            "exact_truth": hit["hits"][0]["exact_truth"] if hit["hits"] else None,
        })

    # Crib-absent control: a fixture engineered so the crib is provably not
    # present. The full family must close with zero hits and zero
    # incomplete cells.
    absent = phase512e.make_absent_fixture(crib_id, WIDTH)
    absent_path = WORK_DIR / f"{crib_id}_w{WIDTH}_absent.json"
    phase512i.export_fixture(absent, absent_path)
    absent_small_match = small_cross_check(absent, absent_path, start_begin=0, pair_begin=0)
    if not absent_small_match:
        raise AssertionError(f"{crib_id}: Python/Rust disagree on the small absent cross-check")

    absent_checkpoint_path = WORK_DIR / f"{crib_id}_w{WIDTH}_absent_checkpoint.json"
    if absent_checkpoint_path.exists():
        absent_checkpoint_path.unlink()
    started = time.monotonic()
    absent_result = phase512j.run_rust_sweep(
        absent_path, 0, start_family_size, 0, 36, NODE_LIMIT, WORKERS,
        checkpoint_path=absent_checkpoint_path)
    absent_elapsed = time.monotonic() - started

    absent_summary = {
        "status": absent_result["status"],
        "hit_count": len(absent_result["hit_cells"]),
        "incomplete_count": len(absent_result["incomplete_cells"]),
        "starts_completed": absent_result["starts_completed"],
        "cells_completed": absent_result["pair_start_cells_completed"],
        "expected_cells": start_family_size * 36,
        "elapsed_seconds": absent_elapsed,
    }

    gate_passed = (
        positive_small_match and absent_small_match
        and blind_recovery["hit_count"] == 1
        and blind_recovery.get("raw_start_matches") is True
        and blind_recovery.get("pair_matches") is True
        and blind_recovery.get("exact_truth") is True
        and absent_summary["status"] == "no_hit_in_complete_requested_family"
        and absent_summary["hit_count"] == 0
        and absent_summary["incomplete_count"] == 0
        and absent_summary["cells_completed"] == absent_summary["expected_cells"]
    )

    return {
        "crib_id": crib_id,
        "width": WIDTH,
        "start_family_size": start_family_size,
        "positive_small_cross_check_match": positive_small_match,
        "absent_small_cross_check_match": absent_small_match,
        "blind_recovery": blind_recovery,
        "absent_control": absent_summary,
        "gate_passed": gate_passed,
    }


def run_all() -> dict:
    rows = [calibrate_crib(crib_id) for crib_id in
            ("creator_macro_message", "phase322_validation_answer")]
    all_passed = all(row["gate_passed"] for row in rows)
    result = {
        "phase": "512K",
        "status": "blind_positive_and_absent_calibration",
        "faed_imported_or_scored": False,
        "cribs": rows,
        "all_gates_passed": all_passed,
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--crib", choices=("creator_macro_message", "phase322_validation_answer"))
    parser.add_argument("--run-all", action="store_true")
    args = parser.parse_args()
    if bool(args.crib) == args.run_all:
        parser.error("choose exactly one of --crib <id> or --run-all")
    value = calibrate_crib(args.crib) if args.crib else run_all()
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0 if value.get("gate_passed", value.get("all_gates_passed")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
