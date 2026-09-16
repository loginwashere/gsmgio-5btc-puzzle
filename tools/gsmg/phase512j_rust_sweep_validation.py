#!/usr/bin/env python3
"""Phase 512J -- Rust in-process parallel sweep, checked against Python's
`phase512e.scan_fixture` cell-by-cell, plus a full exhaustive crib-absent
control run through the Rust sweep alone.

This is steps 3-4 of the Rust-port plan:
  3. validate a crib-absent control (the crib genuinely is not present, so a
     full family must complete with zero hits and zero incomplete cells);
  4. add deterministic in-process parallelism (`crib_csp sweep`) and prove it
     agrees with the single-cell-per-invocation reference architecture.

Every fixture here is synthetic (`phase512a.make_fixture` /
`phase512e.make_absent_fixture`); FAED itself is never referenced or scored,
though importing `phase512a` loads the `data` module that defines it.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path

import phase512a_transposition_crib_feasibility as phase512a
import phase512e_parallel_blind_crib as phase512e
import phase512i_rust_parity as phase512i


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
BINARY = phase512i.BINARY
WORK_DIR = REPO_ROOT / "_work" / "phase512j"
RESULT = SCRIPT_DIR / "phase512j_result.json"


def run_rust_sweep(fixture_path: Path, start_begin: int, start_count: int,
                   pair_begin: int, pair_count: int, node_limit: int,
                   workers: int, checkpoint_path: Path | None = None) -> dict:
    cmd = [str(BINARY), "sweep", "--fixture", str(fixture_path),
           "--start-begin", str(start_begin), "--start-count", str(start_count),
           "--pair-begin", str(pair_begin), "--pair-count", str(pair_count),
           "--node-limit", str(node_limit), "--workers", str(workers)]
    if checkpoint_path is not None:
        cmd += ["--checkpoint", str(checkpoint_path)]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(proc.stdout)


def canonical_python_cells(checkpoint: dict) -> dict:
    cells = {}
    for row in checkpoint["completed_starts"]:
        for cell in row["cells"]:
            key = (row["raw_start"], cell["pair_index"])
            cells[key] = {
                "total_nodes": cell["total_nodes"],
                "patterns_tested": cell["patterns_tested"],
                "search_complete": cell["search_complete"],
                "node_limit_reached": cell["node_limit_reached"],
                "hit_count": cell["hit_count"],
                "hits": [
                    {"pattern_index": hit["pattern_index"],
                     "column_to_chunk": list(hit["column_to_chunk"]),
                     "exact_truth": hit["exact_truth"]}
                    for hit in cell["hits"]
                ],
            }
    return cells


def canonical_rust_cells(checkpoint: dict) -> dict:
    cells = {}
    for row in checkpoint["completed_starts"]:
        for cell in row["cells"]:
            key = (row["raw_start"], cell["pair_index"])
            cells[key] = {
                "total_nodes": cell["total_nodes"],
                "patterns_tested": cell["patterns_tested"],
                "search_complete": cell["search_complete"],
                "node_limit_reached": cell["node_limit_reached"],
                "hit_count": cell["hit_count"],
                "hits": [
                    {"pattern_index": hit["pattern_index"],
                     "column_to_chunk": list(hit["column_to_chunk"]),
                     "exact_truth": hit["exact_truth"]}
                    for hit in cell["hits"]
                ],
            }
    return cells


def run_sweep_parity() -> dict:
    phase512i.ensure_binary()
    fixture = phase512a.make_fixture("phase1_credential", 15)
    path = WORK_DIR / "phase1_credential_w15.json"
    phase512i.export_fixture(fixture, path)

    true_pair = tuple(fixture["pair"])
    true_pair_index = phase512a.base.ESCAPE_PAIRS.index(true_pair)
    true_start = fixture["planted_raw_offset"]
    pair_begin = max(0, true_pair_index - 1)
    pair_count = 3
    start_begin = true_start - 1
    start_count = 3
    node_limit = 2_000_000

    python_checkpoint = phase512e.scan_fixture(
        fixture, workers=4, per_cell_node_limit=node_limit,
        pair_indices=range(pair_begin, pair_begin + pair_count),
        start_begin=start_begin, start_count=start_count,
        checkpoint_path=None, pattern_shards=1)

    rust_checkpoint = run_rust_sweep(
        path, start_begin, start_count, pair_begin, pair_count,
        node_limit, workers=4)

    python_cells = canonical_python_cells(python_checkpoint)
    rust_cells = canonical_rust_cells(rust_checkpoint)

    match = python_cells == rust_cells
    status_match = python_checkpoint["status"] == rust_checkpoint["status"]
    return {
        "match": match and status_match,
        "python_status": python_checkpoint["status"],
        "rust_status": rust_checkpoint["status"],
        "python_cell_count": len(python_cells),
        "rust_cell_count": len(rust_cells),
        "python_hit_cells": len(python_checkpoint["hit_cells"]),
        "rust_hit_cells": len(rust_checkpoint["hit_cells"]),
        "cells_match": python_cells == rust_cells,
        "true_pair_index": true_pair_index,
        "true_start": true_start,
        "swept_range": {"start_begin": start_begin, "start_count": start_count,
                        "pair_begin": pair_begin, "pair_count": pair_count},
    }


def run_absent_fixture_validation(workers: int = 16) -> dict:
    phase512i.ensure_binary()
    absent = phase512e.make_absent_fixture("phase1_credential", 15)
    path = WORK_DIR / "absent_phase1_credential_w15.json"
    phase512i.export_fixture(absent, path)

    # Small cross-check first: a handful of cells on the *absent* fixture
    # must also agree between Python and Rust before trusting a large Rust-
    # only run of it.
    small_pair_count = 3
    small_start_count = 2
    node_limit = 2_000_000
    python_small = phase512e.scan_fixture(
        absent, workers=4, per_cell_node_limit=node_limit,
        pair_indices=range(small_pair_count),
        start_begin=0, start_count=small_start_count,
        checkpoint_path=None, pattern_shards=1)
    rust_small = run_rust_sweep(path, 0, small_start_count, 0, small_pair_count,
                                node_limit, workers=4)
    small_match = canonical_python_cells(python_small) == canonical_rust_cells(rust_small)
    if not small_match:
        raise AssertionError("Python and Rust disagree on the crib-absent fixture's small cross-check")

    # Full exhaustive family through the Rust sweep alone: this is the
    # "measure the complete 16-core Rust runner" deliverable -- the same
    # 518 x 36 = 18,648-cell shape as the real locked Phase 512G FAED run,
    # on a fixture where the crib provably is not present.
    maximum_start = len(absent["observed"]) - len(absent["crib"])
    start_count = maximum_start + 1
    checkpoint_path = WORK_DIR / "absent_full_checkpoint.json"
    if checkpoint_path.exists():
        checkpoint_path.unlink()
    started = time.monotonic()
    full = run_rust_sweep(path, 0, start_count, 0, 36, node_limit, workers,
                          checkpoint_path=checkpoint_path)
    elapsed = time.monotonic() - started

    return {
        "small_cross_check_match": small_match,
        "small_cross_check_cells": len(canonical_rust_cells(rust_small)),
        "full_status": full["status"],
        "full_starts_completed": full["starts_completed"],
        "full_cells_completed": full["pair_start_cells_completed"],
        "full_hit_count": len(full["hit_cells"]),
        "full_incomplete_count": len(full["incomplete_cells"]),
        "expected_cells": start_count * 36,
        "elapsed_seconds": elapsed,
        "workers": workers,
    }


def run_all(workers: int = 16) -> dict:
    sweep_parity = run_sweep_parity()
    if not sweep_parity["match"]:
        raise AssertionError("Rust sweep disagrees with Python phase512e.scan_fixture")
    absent = run_absent_fixture_validation(workers)
    if absent["full_hit_count"] != 0 or absent["full_incomplete_count"] != 0:
        raise AssertionError("crib-absent full family did not close cleanly")
    if absent["full_cells_completed"] != absent["expected_cells"]:
        raise AssertionError("crib-absent full family did not complete every cell")
    result = {
        "phase": "512J",
        "status": "rust_sweep_parity_and_absent_fixture_validation",
        "faed_imported_or_scored": False,
        "sweep_parity": sweep_parity,
        "absent_fixture": absent,
        "verdict": "pass",
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def self_test() -> dict:
    parity = run_sweep_parity()
    if not parity["match"]:
        raise AssertionError("small sweep parity check failed")
    return {"self_test": "pass", "cells_checked": parity["rust_cell_count"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run-all", action="store_true")
    parser.add_argument("--workers", type=int, default=16)
    args = parser.parse_args()
    if args.self_test == args.run_all:
        parser.error("choose exactly one of --self-test or --run-all")
    value = self_test() if args.self_test else run_all(args.workers)
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0 if value.get("verdict", "pass") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
