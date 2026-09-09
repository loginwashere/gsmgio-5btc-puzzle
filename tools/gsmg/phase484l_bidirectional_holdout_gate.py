#!/usr/bin/env python3
"""Locked synthetic holdout gate for Phase 484K widths 10 and 15."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import time
from pathlib import Path

import phase484a_raw_symbol_vic_solver as base
import phase484g_hard_negative_discriminator as learned
import phase484j_constructive_prefix_beam_probe as prefix
import phase484k_bidirectional_segment_assembly_probe as solver

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
PROTOCOL = REPO_ROOT / "doc/Brainstorms/2026-09-07 - Phase 484L Bidirectional Solver Holdout Protocol.md"
LOCK_PATH = SCRIPT_DIR / "phase484l_execution_lock.json"
RESULT_PATH = SCRIPT_DIR / "phase484l_holdout_result.json"
WIDTHS = (10, 15)
BOARD_MODES = base.BOARD_MODES
FIXTURES_PER_CELL = 10
MINIMUM_EXACT = 8
WORKERS = 6
_MODEL_CACHE = {}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pinned_files() -> dict[str, Path]:
    return {
        "protocol": PROTOCOL,
        "holdout_runner": Path(__file__),
        "verifier": SCRIPT_DIR / "phase484l_verify_run.py",
        "base_solver": SCRIPT_DIR / "phase484a_raw_symbol_vic_solver.py",
        "discriminator": SCRIPT_DIR / "phase484g_hard_negative_discriminator.py",
        "discriminator_result": SCRIPT_DIR / "phase484g_hard_negative_discriminator_result.json",
        "prefix_solver": SCRIPT_DIR / "phase484j_constructive_prefix_beam_probe.py",
        "bidirectional_solver": SCRIPT_DIR / "phase484k_bidirectional_segment_assembly_probe.py",
        "dev_batch_result": SCRIPT_DIR / "phase484k_width10_15_dev_batch_result.json",
        "corpus": base.CORPUS_FILE,
    }


def lock_payload() -> dict:
    return {
        "phase": "484L",
        "status": "locked_before_holdout",
        "files_sha256": {
            name: sha256_file(path) for name, path in pinned_files().items()
        },
        "scope": {
            "widths": list(WIDTHS),
            "board_modes": list(BOARD_MODES),
            "pair_index": learned.PAIR_INDEX,
            "fixture_split": "holdout",
            "fixture_indices": list(range(FIXTURES_PER_CELL)),
            "holdout_seed": base.SEED_HOLDOUT,
        },
        "budgets": {
            "start_depth": prefix.START_DEPTH,
            "beam_width": solver.BEAM_WIDTH,
            "reserved_fraction": solver.RESERVED_FRACTION,
            "workers": WORKERS,
        },
        "gate": {
            "minimum_exact_recoveries_per_cell": MINIMUM_EXACT,
            "fixtures_per_cell": FIXTURES_PER_CELL,
            "all_cells_must_pass": True,
        },
        "prohibitions": {
            "faed_scoring": True,
            "width_19": True,
            "holdout_rerun": True,
            "post_lock_tuning": True,
        },
        "faed_scored": False,
    }


def verify_lock(lock: dict) -> None:
    if lock != lock_payload():
        raise ValueError("execution lock does not match current pinned inputs")


def holdout_cell(spec):
    mode, width, fixture_index = spec
    if width not in _MODEL_CACHE:
        _MODEL_CACHE[width] = prefix.train_models(width)
    fixture = base.make_fixture(
        width, learned.PAIR_INDEX, fixture_index, seed=base.SEED_HOLDOUT,
        board_mode=mode, split="holdout",
    )
    return {
        "board_mode": mode,
        "width": width,
        "fixture_index": fixture_index,
        **solver.search_fixture(fixture, _MODEL_CACHE[width]),
    }


def run_holdout() -> dict:
    lock = json.loads(LOCK_PATH.read_text())
    verify_lock(lock)
    specs = [
        (mode, width, index)
        for mode in BOARD_MODES
        for width in WIDTHS
        for index in range(FIXTURES_PER_CELL)
    ]
    began = time.monotonic()
    with concurrent.futures.ProcessPoolExecutor(max_workers=WORKERS) as pool:
        records = list(pool.map(holdout_cell, specs))
    cells = []
    for mode in BOARD_MODES:
        for width in WIDTHS:
            selected = [
                record for record in records
                if record["board_mode"] == mode and record["width"] == width
            ]
            exact = sum(record["exact_recovery"] for record in selected)
            cells.append({
                "board_mode": mode,
                "width": width,
                "fixture_count": len(selected),
                "exact_recovery_count": exact,
                "gate_pass": exact >= MINIMUM_EXACT,
                "records": selected,
            })
    return {
        "phase": "484L",
        "status": "locked_holdout_complete",
        "execution_lock_sha256": sha256_file(LOCK_PATH),
        "faed_scored": False,
        "fixture_split": "holdout",
        "scope": lock["scope"],
        "budgets": lock["budgets"],
        "gate": lock["gate"],
        "all_cells_pass": all(cell["gate_pass"] for cell in cells),
        "cells": cells,
        "wall_seconds": time.monotonic() - began,
    }


def self_test() -> None:
    assert WIDTHS == (10, 15) and 19 not in WIDTHS
    assert FIXTURES_PER_CELL == 10 and MINIMUM_EXACT == 8
    assert solver.BEAM_WIDTH == 4096
    assert solver.RESERVED_FRACTION == 0.5


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write-lock", action="store_true")
    parser.add_argument("--holdout", action="store_true")
    args = parser.parse_args()
    if sum((args.self_test, args.write_lock, args.holdout)) != 1:
        parser.error("choose exactly one action")
    if args.self_test:
        self_test()
        print("self-test: ok")
        return 0
    if args.write_lock:
        LOCK_PATH.write_text(json.dumps(lock_payload(), indent=2, sort_keys=True) + "\n")
        print(LOCK_PATH)
        return 0
    result = run_holdout()
    RESULT_PATH.write_text(json.dumps(result, indent=2) + "\n")
    print("all_cells_pass", result["all_cells_pass"])
    for cell in result["cells"]:
        print(cell["board_mode"], cell["width"],
              cell["exact_recovery_count"], "/", cell["fixture_count"],
              "gate", cell["gate_pass"])
    print(RESULT_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
