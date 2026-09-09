#!/usr/bin/env python3
"""Fail-closed verifier for the Phase 484A synthetic holdout artifact."""

from __future__ import annotations

import json
from pathlib import Path

import phase484a_holdout_gate as gate


def verify() -> dict:
    lock = gate.verify_lock()
    result = json.loads(gate.RESULT_PATH.read_text())
    errors = []
    if result.get("execution_lock_sha256") != gate.sha256_file(gate.LOCK_PATH):
        errors.append("result lock hash mismatch")
    records = [record for cell in result.get("cells", []) for record in cell.get("records", [])]
    expected_jobs = {
        (mode, width, index, pair_index)
        for mode in gate.BOARD_MODES for width in gate.WIDTHS
        for index, pair_index in enumerate(gate.PAIR_INDICES)
    }
    actual_jobs = {
        (r.get("board_mode"), r.get("width"), r.get("fixture_index"), r.get("pair_index"))
        for r in records
    }
    if actual_jobs != expected_jobs or len(records) != len(expected_jobs):
        errors.append("holdout job set mismatch")
    for record in records:
        if record.get("gate_pass") != gate.fixture_passes(record):
            errors.append("fixture gate recomputation mismatch")
            break
    rebuilt = gate.aggregate(records, gate.sha256_file(gate.LOCK_PATH))
    if rebuilt != result:
        errors.append("aggregate recomputation mismatch")
    return {
        "phase": "484A",
        "consistent": not errors,
        "errors": errors,
        "gate_pass": result.get("gate_pass"),
        "execution_lock_sha256": gate.sha256_file(gate.LOCK_PATH),
        "result_sha256": gate.sha256_file(gate.RESULT_PATH),
        "locked_status": lock["status"],
    }


if __name__ == "__main__":
    output = verify()
    print(json.dumps(output, indent=2))
    raise SystemExit(0 if output["consistent"] else 1)
