#!/usr/bin/env python3
"""Fail-closed verifier for Phase 484C's locked width-7 holdout."""

import json

import phase484c_width7_holdout_gate as gate


def verify() -> dict:
    gate.verify_lock()
    result = json.loads(gate.RESULT_PATH.read_text())
    errors = []
    lock_hash = gate.sha256_file(gate.LOCK_PATH)
    if result.get("execution_lock_sha256") != lock_hash:
        errors.append("result lock hash mismatch")
    records = [r for c in result.get("cells", []) for r in c.get("records", [])]
    expected = {
        (mode, index, pair_index)
        for mode in gate.solver.base.BOARD_MODES
        for index, pair_index in enumerate(gate.PAIR_INDICES)
    }
    actual = {(r.get("board_mode"), r.get("fixture_index"), r.get("pair_index")) for r in records}
    if actual != expected or len(records) != len(expected):
        errors.append("holdout job set mismatch")
    if any(r.get("gate_pass") != gate.fixture_passes(r) for r in records):
        errors.append("fixture gate recomputation mismatch")
    if gate.aggregate(records, lock_hash) != result:
        errors.append("aggregate recomputation mismatch")
    return {
        "phase": "484C",
        "consistent": not errors,
        "errors": errors,
        "gate_pass": result.get("gate_pass"),
        "execution_lock_sha256": lock_hash,
        "result_sha256": gate.sha256_file(gate.RESULT_PATH),
    }


if __name__ == "__main__":
    output = verify()
    print(json.dumps(output, indent=2))
    raise SystemExit(0 if output["consistent"] else 1)
