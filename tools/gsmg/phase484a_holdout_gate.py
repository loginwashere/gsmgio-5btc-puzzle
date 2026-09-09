#!/usr/bin/env python3
"""Locked synthetic holdout gate for Phase 484A's blind small-width solver."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path

import phase484a_raw_symbol_vic_solver as solver

SCRIPT_DIR = Path(__file__).resolve().parent
LOCK_PATH = SCRIPT_DIR / "phase484a_execution_lock.json"
RESULT_PATH = SCRIPT_DIR / "phase484a_holdout_result.json"
WIDTHS = (2, 3, 5, 6)
BOARD_MODES = solver.BOARD_MODES
PAIR_INDICES = (0, 1, 5, 9, 14, 18, 23, 27, 32, 35)
JOINT_KEEP = 1536
BOARD_RESTARTS = 2
BOARD_ITERS = 6000
BOARD_T0 = 20.0
BOARD_T1 = 1.0
MINIMUM_CELL_PASSES = 8
MINIMUM_PLAINTEXT_ACCURACY = 0.95
MINIMUM_BOARD_ACCURACY = 0.80
WORKERS = 8


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_lock() -> dict:
    lock = json.loads(LOCK_PATH.read_text())
    paths = {
        "protocol": solver.REPO_ROOT / lock["paths"]["protocol"],
        "solver": solver.REPO_ROOT / lock["paths"]["solver"],
        "runner": solver.REPO_ROOT / lock["paths"]["runner"],
        "verifier": solver.REPO_ROOT / lock["paths"]["verifier"],
        "corpus": solver.REPO_ROOT / lock["paths"]["corpus"],
        "quadgrams": solver.REPO_ROOT / lock["paths"]["quadgrams"],
    }
    actual = {name: sha256_file(path) for name, path in paths.items()}
    if actual != lock["files_sha256"]:
        raise RuntimeError("execution lock hash mismatch")
    expected = {
        "widths": list(WIDTHS),
        "board_modes": list(BOARD_MODES),
        "pair_indices": list(PAIR_INDICES),
        "joint_keep": JOINT_KEEP,
        "board_restarts": BOARD_RESTARTS,
        "board_iters": BOARD_ITERS,
        "board_t0": BOARD_T0,
        "board_t1": BOARD_T1,
        "minimum_cell_passes": MINIMUM_CELL_PASSES,
        "minimum_plaintext_accuracy": MINIMUM_PLAINTEXT_ACCURACY,
        "minimum_board_accuracy": MINIMUM_BOARD_ACCURACY,
        "seed_holdout": solver.SEED_HOLDOUT,
        "workers": WORKERS,
    }
    if lock["configuration"] != expected:
        raise RuntimeError("execution lock configuration mismatch")
    return lock


def fixture_passes(record: dict) -> bool:
    return (
        record["joint_recovery"]
        and record["plaintext_char_accuracy"] >= MINIMUM_PLAINTEXT_ACCURACY
        and record["board_accuracy"] >= MINIMUM_BOARD_ACCURACY
        and record["decoded_length"] == record["true_length"]
    )


def solve_job(job: tuple[str, int, int, int]) -> dict:
    board_mode, width, fixture_index, pair_index = job
    model = solver.SpectralModel.from_training_corpus()
    quad, _ = solver.load_language_model()
    fixture = solver.make_fixture(
        width, pair_index, fixture_index, seed=solver.SEED_HOLDOUT,
        board_mode=board_mode, split="holdout",
    )
    result = solver.solve_fixture_joint_pairs(
        fixture, model, quad, joint_keep=JOINT_KEEP,
        board_restarts=BOARD_RESTARTS, board_iters=BOARD_ITERS,
        board_t0=BOARD_T0, board_t1=BOARD_T1,
        seed=solver.derive_seed(solver.SEED_HOLDOUT, width, fixture_index, pair_index),
    )
    record = {
        "board_mode": board_mode,
        "width": width,
        "fixture_index": fixture_index,
        "pair_index": pair_index,
        **result,
    }
    record["gate_pass"] = fixture_passes(record)
    return record


def aggregate(records: list[dict], lock_sha256: str) -> dict:
    ordered = sorted(records, key=lambda r: (r["board_mode"], r["width"], r["fixture_index"]))
    cells = []
    for board_mode in BOARD_MODES:
        for width in WIDTHS:
            cell_records = [r for r in ordered if r["board_mode"] == board_mode and r["width"] == width]
            passed = sum(r["gate_pass"] for r in cell_records)
            cells.append({
                "board_mode": board_mode,
                "width": width,
                "fixture_count": len(cell_records),
                "passed": passed,
                "cell_gate_pass": passed >= MINIMUM_CELL_PASSES,
                "records": cell_records,
            })
    return {
        "phase": "484A",
        "status": "locked_synthetic_holdout_complete",
        "faed_scored": False,
        "fixture_split": "holdout",
        "execution_lock_sha256": lock_sha256,
        "gate_pass": all(cell["cell_gate_pass"] for cell in cells),
        "cells": cells,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    lock = verify_lock()
    if not args.run:
        print("lock verified; pass --run to consume the frozen holdout")
        return 0
    jobs = [
        (board_mode, width, fixture_index, pair_index)
        for board_mode in BOARD_MODES
        for width in WIDTHS
        for fixture_index, pair_index in enumerate(PAIR_INDICES)
    ]
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    with concurrent.futures.ProcessPoolExecutor(max_workers=WORKERS) as pool:
        records = list(pool.map(solve_job, jobs))
    result = aggregate(records, sha256_file(LOCK_PATH))
    temporary = RESULT_PATH.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(result, indent=2))
    temporary.replace(RESULT_PATH)
    for cell in result["cells"]:
        print(cell["board_mode"], cell["width"], cell["passed"], "/", cell["fixture_count"])
    print("gate_pass", result["gate_pass"])
    return 0 if result["gate_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
