#!/usr/bin/env python3
"""Fail-closed verifier for Phase 484L."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import phase484l_bidirectional_holdout_gate as gate


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify() -> dict:
    lock = json.loads(gate.LOCK_PATH.read_text())
    gate.verify_lock(lock)
    result = json.loads(gate.RESULT_PATH.read_text())
    errors = []
    if result.get("execution_lock_sha256") != sha256_file(gate.LOCK_PATH):
        errors.append("result lock hash mismatch")
    for field in ("scope", "budgets", "gate"):
        if result.get(field) != lock[field]:
            errors.append(f"{field} mismatch")
    if result.get("faed_scored") is not False:
        errors.append("FAED marker mismatch")
    expected = {(mode, width) for mode in gate.BOARD_MODES for width in gate.WIDTHS}
    seen = set()
    family_pass = True
    for cell in result.get("cells", []):
        key = (cell.get("board_mode"), cell.get("width"))
        seen.add(key)
        records = cell.get("records", [])
        if sorted(r.get("fixture_index") for r in records) != list(range(gate.FIXTURES_PER_CELL)):
            errors.append(f"{key}: fixture indices mismatch")
        exact = sum(r.get("exact_recovery") is True for r in records)
        if cell.get("exact_recovery_count") != exact:
            errors.append(f"{key}: exact count mismatch")
        passed = exact >= gate.MINIMUM_EXACT
        if cell.get("gate_pass") is not passed:
            errors.append(f"{key}: gate mismatch")
        family_pass &= passed
    if seen != expected:
        errors.append("cell set mismatch")
    if result.get("all_cells_pass") is not family_pass:
        errors.append("family disposition mismatch")
    return {
        "phase": "484L",
        "consistent": not errors,
        "errors": errors,
        "execution_lock_sha256": sha256_file(gate.LOCK_PATH),
        "holdout_result_sha256": sha256_file(gate.RESULT_PATH),
        "all_cells_pass": result.get("all_cells_pass"),
    }


def main() -> int:
    record = verify()
    path = gate.SCRIPT_DIR / "phase484l_verification.json"
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(json.dumps(record, indent=2, sort_keys=True))
    return 0 if record["consistent"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
