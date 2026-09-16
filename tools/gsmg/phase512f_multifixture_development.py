#!/usr/bin/env python3
"""Resumable multi-fixture development batch for the Phase-512 crib CSP."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import time

import phase512a_transposition_crib_feasibility as phase512a
import phase512b_crib_csp_ceiling as phase512b
import phase512e_parallel_blind_crib as phase512e


SCRIPT_DIR = Path(__file__).resolve().parent
RESULT = SCRIPT_DIR / "phase512f_development_result.json"
CHECKPOINT_DIR = SCRIPT_DIR / "phase512f_checkpoints"
SCHEMA = "phase512f-multifixture-development-v1"


def default_manifest() -> tuple[dict, ...]:
    """Small development batch, deliberately not a frozen holdout gate."""
    return tuple(
        {"kind": "present", "crib_id": "phase1_credential",
         "width": width, "fixture_index": 1}
        for width in phase512a.WIDTHS
    ) + (
        {"kind": "absent", "crib_id": "phase1_credential",
         "width": 15, "fixture_index": 0},
    )


def manifest_sha256(manifest) -> str:
    payload = json.dumps(manifest, sort_keys=True,
                         separators=(",", ":")).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def fixture_for(row: dict) -> dict:
    if row["kind"] == "present":
        return phase512a.make_fixture(
            row["crib_id"], row["width"], row["fixture_index"])
    if row["kind"] == "absent":
        return phase512e.make_absent_fixture(
            row["crib_id"], row["width"], row["fixture_index"])
    raise ValueError("unknown fixture kind")


def evaluate(row: dict, checkpoint_dir: Path, workers: int,
             node_limit: int, pattern_shards: int) -> dict:
    fixture = fixture_for(row)
    name = (f"{row['kind']}_{row['crib_id']}_w{row['width']}_"
            f"i{row['fixture_index']}.json")
    checkpoint = checkpoint_dir / name
    search = phase512e.scan_fixture(
        fixture, workers=workers, per_cell_node_limit=node_limit,
        checkpoint_path=checkpoint, pattern_shards=pattern_shards)
    if row["kind"] == "present":
        truth = list(phase512b.truth_column_to_chunk(fixture["order"]))
        exact_hits = [
            hit
            for cell in search["hit_cells"]
            for hit in cell["hits"]
            if (cell["raw_start"] == fixture["planted_raw_offset"]
                and tuple(cell["pair"]) == phase512a.PAIR
                and hit["column_to_chunk"] == truth)
        ]
        passed = (
            search["status"] == "hit_at_earliest_completed_start"
            and len(search["hit_cells"]) == 1
            and len(exact_hits) == 1
        )
    else:
        passed = (
            search["status"] == "no_hit_in_complete_requested_family"
            and not search["hit_cells"]
        )
    return {
        **row,
        "observed_sha256": phase512e.sha_ascii(fixture["observed"]),
        "planted_raw_offset": fixture.get("planted_raw_offset"),
        "status": search["status"],
        "starts_completed": search["starts_completed"],
        "pair_start_cells_completed": search["pair_start_cells_completed"],
        "hit_cells": search["hit_cells"],
        "incomplete_cells": search["incomplete_cells"],
        "passed": passed,
        "checkpoint": str(checkpoint),
    }


def run(manifest, checkpoint_dir: Path, result_path: Path,
        workers: int, node_limit: int, pattern_shards: int = 1) -> dict:
    manifest = tuple(manifest)
    started = time.monotonic()
    rows = []
    for row in manifest:
        result = evaluate(row, checkpoint_dir, workers, node_limit, pattern_shards)
        rows.append(result)
        partial = {
            "schema": SCHEMA,
            "status": "in_progress",
            "faed_imported_or_scored": False,
            "manifest": list(manifest),
            "manifest_sha256": manifest_sha256(manifest),
            "workers": workers,
            "per_cell_node_limit": node_limit,
            "pattern_shards": pattern_shards,
            "fixtures": rows,
            "elapsed_seconds": time.monotonic() - started,
        }
        phase512e._atomic_json(result_path, partial)
        if not result["passed"]:
            break
    output = {
        "schema": SCHEMA,
        "status": ("development_pass" if len(rows) == len(manifest)
                   and all(row["passed"] for row in rows)
                   else "development_fail_or_incomplete"),
        "faed_imported_or_scored": False,
        "manifest": list(manifest),
        "manifest_sha256": manifest_sha256(manifest),
        "workers": workers,
        "per_cell_node_limit": node_limit,
        "pattern_shards": pattern_shards,
        "fixtures": rows,
        "elapsed_seconds": time.monotonic() - started,
    }
    phase512e._atomic_json(result_path, output)
    return output


def describe() -> dict:
    manifest = default_manifest()
    return {
        "schema": SCHEMA,
        "status": "development_not_run",
        "faed_imported_or_scored": False,
        "manifest": list(manifest),
        "manifest_sha256": manifest_sha256(manifest),
        "positive_fixture_count": sum(row["kind"] == "present" for row in manifest),
        "absent_fixture_count": sum(row["kind"] == "absent" for row in manifest),
    }


def self_test() -> dict:
    manifest = default_manifest()
    if len(manifest) != 5 or sum(row["kind"] == "absent" for row in manifest) != 1:
        raise AssertionError("development manifest changed")
    fixtures = [fixture_for(row) for row in manifest]
    if len({phase512e.sha_ascii(value["observed"]) for value in fixtures}) != 5:
        raise AssertionError("development fixtures are not distinct")
    return {"self_test": "pass", "manifest_sha256": manifest_sha256(manifest)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--describe", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--workers", type=int, default=min(16, os.cpu_count() or 1))
    parser.add_argument("--node-limit", type=int, default=2_000_000)
    parser.add_argument("--pattern-shards", type=int, default=1)
    parser.add_argument("--checkpoint-dir", type=Path, default=CHECKPOINT_DIR)
    parser.add_argument("--result", type=Path, default=RESULT)
    args = parser.parse_args()
    if sum((args.self_test, args.describe, args.run)) != 1:
        parser.error("choose exactly one action")
    value = (self_test() if args.self_test else describe() if args.describe else
             run(default_manifest(), args.checkpoint_dir, args.result,
                 args.workers, args.node_limit, args.pattern_shards))
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
