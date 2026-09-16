#!/usr/bin/env python3
"""Phase 512I -- Rust single-cell CSP port, checked for exact parity with
the frozen Python reference (`phase512d.search_lengths_at_start`).

This is step 1-2 of the Rust-port plan: implement one pair/start cell
without parallelism, then diff exact hits, node counts, pattern order, and
node-limit behavior against Python on synthetic fixtures. Every fixture
here comes from `phase512a.make_fixture`; FAED itself is never referenced
or scored, though importing `phase512a` does load the `data` module that
defines the `FAED` constant among others.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import phase512a_transposition_crib_feasibility as phase512a
import phase512d_length_pattern_csp as phase512d


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
CRATE_DIR = REPO_ROOT / "tools" / "crib_csp"
BINARY = CRATE_DIR / "target" / "release" / "crib_csp"
WORK_DIR = REPO_ROOT / "_work" / "phase512i"
RESULT = SCRIPT_DIR / "phase512i_result.json"


def ensure_binary() -> None:
    if BINARY.exists():
        return
    subprocess.run(["cargo", "build", "--release"], cwd=CRATE_DIR, check=True)
    if not BINARY.exists():
        raise RuntimeError("cargo build did not produce the crib_csp binary")


def export_fixture(fixture: dict, path: Path) -> None:
    payload = {
        "observed": fixture["observed"],
        "width": fixture["width"],
        "crib": fixture["crib"],
        "order": list(fixture["order"]),
        "pair": list(fixture["pair"]),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload))


def run_rust_cell(fixture_path: Path, raw_start: int, pair: tuple[str, str],
                  node_limit: int) -> dict:
    proc = subprocess.run(
        [str(BINARY), "cell", "--fixture", str(fixture_path), "--raw-start", str(raw_start),
         "--pair", "".join(pair), "--node-limit", str(node_limit)],
        capture_output=True, text=True, check=True)
    return json.loads(proc.stdout)


def run_python_cell(fixture: dict, raw_start: int, pair: tuple[str, str],
                    node_limit: int) -> dict:
    result = phase512d.search_lengths_at_start(
        fixture, raw_start, node_limit, pair=pair)
    return result


def canonicalize(result: dict) -> dict:
    """Drop wall-clock fields and normalize types so Python and Rust JSON
    can be compared with plain equality."""
    stripped = {key: value for key, value in result.items() if key != "elapsed_seconds"}
    stripped["pair"] = list(stripped["pair"])
    stripped["hits"] = [
        {
            "pattern_index": hit["pattern_index"],
            "single_letters": hit["single_letters"],
            "column_to_chunk": list(hit["column_to_chunk"]),
            "exact_truth": hit["exact_truth"],
            "nodes_for_pattern": hit["nodes_for_pattern"],
        }
        for hit in stripped["hits"]
    ]
    return stripped


def compare_cell(crib_id: str, width: int, raw_start: int, pair: tuple[str, str],
                 node_limit: int, fixture: dict, fixture_path: Path) -> dict:
    python_result = canonicalize(run_python_cell(fixture, raw_start, pair, node_limit))
    rust_result = canonicalize(run_rust_cell(fixture_path, raw_start, pair, node_limit))
    match = python_result == rust_result
    return {
        "crib_id": crib_id, "width": width, "raw_start": raw_start,
        "pair": list(pair), "node_limit": node_limit,
        "match": match,
        "python": python_result, "rust": rust_result,
    }


def run_battery() -> dict:
    ensure_binary()
    rows = []

    credential = phase512a.make_fixture("phase1_credential", 15)
    credential_path = WORK_DIR / "phase1_credential_w15.json"
    export_fixture(credential, credential_path)
    true_pair = tuple(credential["pair"])
    true_start = credential["planted_raw_offset"]
    wrong_pair = phase512a.base.ESCAPE_PAIRS[0]
    if wrong_pair == true_pair:
        wrong_pair = phase512a.base.ESCAPE_PAIRS[1]

    rows.append(compare_cell("phase1_credential", 15, true_start, true_pair,
                             2_000_000, credential, credential_path))
    rows.append(compare_cell("phase1_credential", 15, true_start + 1, true_pair,
                             2_000_000, credential, credential_path))
    rows.append(compare_cell("phase1_credential", 15, true_start, wrong_pair,
                             2_000_000, credential, credential_path))

    # Node-limit transition cases: the known-hit cell's total node count is
    # exactly 3872 (verified against Phase 512A's documented figure), so
    # 3871 must show Python's one-node overshoot (nodes increment happens
    # before the node_limit check, so a rejected node still gets counted)
    # while 3872 must be the first limit that actually reaches the hit.
    for node_limit in (1, 10, 100, 3_871, 3_872, 4_000):
        rows.append(compare_cell("phase1_credential", 15, true_start, true_pair,
                                 node_limit, credential, credential_path))

    macro = phase512a.make_fixture("creator_macro_message", 15)
    macro_path = WORK_DIR / "creator_macro_message_w15.json"
    export_fixture(macro, macro_path)
    macro_true_pair = tuple(macro["pair"])
    macro_true_start = macro["planted_raw_offset"]
    rows.append(compare_cell("creator_macro_message", 15, macro_true_start,
                             macro_true_pair, 20_000_000, macro, macro_path))

    all_match = all(row["match"] for row in rows)
    result = {
        "phase": "512I",
        "status": "rust_single_cell_parity",
        "faed_imported_or_scored": False,
        "cells": [
            {key: value for key, value in row.items() if key not in ("python", "rust")}
            for row in rows
        ],
        "all_cells_match": all_match,
        "mismatches": [row for row in rows if not row["match"]],
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def self_test() -> dict:
    ensure_binary()
    credential = phase512a.make_fixture("phase1_credential", 15)
    path = WORK_DIR / "self_test_fixture.json"
    export_fixture(credential, path)
    row = compare_cell("phase1_credential", 15, credential["planted_raw_offset"],
                       tuple(credential["pair"]), 2_000_000, credential, path)
    if not row["match"]:
        raise AssertionError("Rust and Python cells disagree on the known-hit case")
    if row["python"]["hit_count"] != 1 or not row["python"]["first_hit_exact_truth"]:
        raise AssertionError("known-hit case did not recover the planted truth")
    return {"self_test": "pass", "nodes": row["python"]["total_nodes"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run-battery", action="store_true")
    args = parser.parse_args()
    if args.self_test == args.run_battery:
        parser.error("choose exactly one of --self-test or --run-battery")
    value = self_test() if args.self_test else run_battery()
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0 if value.get("all_cells_match", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
