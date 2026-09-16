#!/usr/bin/env python3
"""Fail-closed verifier for the locked Phase-512G FAED crib run."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import phase512g_locked_faed_width15_credential as phase512g


VERIFICATION = phase512g.SCRIPT_DIR / "phase512g_verification.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify() -> dict:
    lock = phase512g.verify_lock()
    errors = []
    if not phase512g.RESULT.is_file():
        raise RuntimeError("Phase-512G result is absent")
    if not phase512g.CHECKPOINT.is_file():
        raise RuntimeError("Phase-512G checkpoint is absent")
    result = json.loads(phase512g.RESULT.read_text())
    checkpoint = json.loads(phase512g.CHECKPOINT.read_text())

    expected_identity = {
        "schema": "phase512e-parallel-blind-crib-v1",
        "fixture_kind": "real_faed",
        "crib_id": lock["crib_id"],
        "fixture_index": 0,
        "crib_sha256": lock["crib_ascii_sha256"],
        "observed_sha256": lock["faed_ascii_sha256"],
        "width": lock["width"],
        "patterns_sha256": lock["length_patterns_sha256"],
        "legal_length_pattern_count": lock["legal_length_pattern_count"],
        "pair_indices": list(range(len(lock["escape_pairs"]))),
        "start_begin": lock["raw_start_begin"],
        "start_count": lock["raw_start_count"],
        "per_cell_node_limit": lock["per_pair_start_node_limit"],
    }
    if checkpoint.get("identity") != expected_identity:
        errors.append("checkpoint identity differs from lock")
    rows = checkpoint.get("completed_starts", [])
    if len(rows) != lock["raw_start_count"]:
        errors.append("wrong completed-start count")
    pair_indices = list(range(len(lock["escape_pairs"])))
    hit_count = 0
    incomplete_count = 0
    for expected_start, row in enumerate(rows):
        if row.get("raw_start") != expected_start:
            errors.append(f"noncontiguous raw start at row {expected_start}")
            break
        cells = row.get("cells", [])
        if [cell.get("pair_index") for cell in cells] != pair_indices:
            errors.append(f"pair family mismatch at raw start {expected_start}")
            break
        for cell in cells:
            if cell.get("pair") != lock["escape_pairs"][cell["pair_index"]]:
                errors.append(f"pair label mismatch at raw start {expected_start}")
                break
            hit_count += int(cell.get("hit_count", 0))
            incomplete_count += int(not cell.get("search_complete", False))
    expected_cells = lock["raw_start_count"] * len(lock["escape_pairs"])
    if checkpoint.get("pair_start_cells_completed") != expected_cells:
        errors.append("wrong pair/start-cell count")
    if checkpoint.get("status") != "no_hit_in_complete_requested_family":
        errors.append("checkpoint is not a complete zero-hit family")
    if checkpoint.get("hit_cells") or hit_count:
        errors.append("checkpoint contains an unreported hit")
    if checkpoint.get("incomplete_cells") or incomplete_count:
        errors.append("checkpoint contains an incomplete cell")
    if phase512g.HITS.exists():
        errors.append("sensitive-hit artifact exists despite zero-hit result")

    expected_result = {
        "phase": phase512g.PHASE,
        "status": "locked_faed_crib_search_complete",
        "execution_lock_sha256": sha(phase512g.LOCK),
        "faed_ascii_sha256": lock["faed_ascii_sha256"],
        "crib_ascii_sha256": lock["crib_ascii_sha256"],
        "width": lock["width"],
        "direction": lock["direction"],
        "starts_completed": lock["raw_start_count"],
        "pair_start_cells_completed": expected_cells,
        "hit_count": 0,
        "incomplete_cell_count": 0,
        "checkpoint_sha256": sha(phase512g.CHECKPOINT),
        "verdict": "bounded_negative",
    }
    if result != expected_result:
        errors.append("result summary is inconsistent with lock/checkpoint")
    return {
        "phase": "512G-verification",
        "consistent": not errors,
        "errors": errors,
        "execution_lock_sha256": sha(phase512g.LOCK),
        "result_sha256": sha(phase512g.RESULT),
        "checkpoint_sha256": sha(phase512g.CHECKPOINT),
        "starts_revalidated": len(rows),
        "cells_revalidated": sum(len(row.get("cells", [])) for row in rows),
        "hits_recomputed": hit_count,
        "incomplete_cells_recomputed": incomplete_count,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    value = verify()
    if args.write:
        phase512g.atomic_json(VERIFICATION, value)
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0 if value["consistent"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
