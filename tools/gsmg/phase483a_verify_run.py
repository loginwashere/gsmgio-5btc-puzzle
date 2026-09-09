#!/usr/bin/env python3
"""Fail-closed structural verifier for Phase 483A's locked holdout result."""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import phase483a_invariant_order_statistic_probe as probe  # noqa: E402
LOCK = SCRIPT_DIR / "phase483a_execution_lock.json"
RESULT = SCRIPT_DIR / "phase483a_holdout_result.json"

def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def verify(lock_path: Path = LOCK, result_path: Path = RESULT) -> dict:
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    result = json.loads(result_path.read_text(encoding="utf-8"))
    expected_files = {
        "protocol": probe.PROTOCOL,
        "audit_script": Path(probe.__file__),
        "verifier": Path(__file__),
        "corpus": probe.CORPUS_FILE,
    }
    checks = {
        "file_hashes": all(lock["files_sha256"].get(name) == sha256_file(path)
                           for name, path in expected_files.items()),
        "lock_payload": lock == probe.lock_payload(),
        "holdout_identity": (
            result.get("phase") == "483A"
            and result.get("synthetic_only") is True
            and result.get("faed_scored") is False
            and result.get("split") == "holdout"
            and result.get("full_frozen_budget") is True
            and result.get("budgets") == {
                "fixtures_per_cell": probe.FIXTURES_PER_CELL,
                "random_orders_per_fixture": probe.RANDOM_ORDERS,
                "corruptions_per_severity": probe.CORRUPTIONS_PER_SEVERITY,
            }
        ),
    }
    expected_cells = {(w, d) for w in probe.WIDTHS for d in probe.DIRECTIONS}
    cells = result.get("cells", [])
    checks["cell_set"] = (len(cells) == len(expected_cells)
                          and {(r.get("width"), r.get("direction")) for r in cells}
                          == expected_cells)
    classifications = True
    powered = []
    for cell in cells:
        fixtures = cell.get("fixtures", [])
        if len(fixtures) != probe.FIXTURES_PER_CELL:
            classifications = False
            continue
        passed = 0
        for index, row in enumerate(fixtures):
            numeric_pass = (
                row.get("index") == index
                and row.get("random_orders") == probe.RANDOM_ORDERS
                and row.get("random_tie_inclusive_exceedances", probe.RANDOM_ORDERS + 1) <= 10
                and row.get("local_degradation") is True
            )
            if row.get("full_budget_fixture_pass") is not numeric_pass:
                classifications = False
            passed += int(numeric_pass)
        expected_power = passed >= 8
        if (cell.get("passed_fixtures") != passed
                or cell.get("meets_numeric_gate") is not expected_power
                or cell.get("statistic_powered") is not expected_power):
            classifications = False
        if expected_power:
            powered.append({"width": cell["width"], "direction": cell["direction"]})
    checks["classifications"] = classifications
    checks["powered_list"] = result.get("powered_cells") == powered
    checks["no_development_alias"] = result.get("development_gate_equivalent_cells") == []
    consistent = all(checks.values())
    return {
        "consistent": consistent,
        "checks": checks,
        "lock_sha256": sha256_file(lock_path),
        "result_sha256": sha256_file(result_path),
        "powered_cells": powered,
    }

def main() -> int:
    report = verify()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["consistent"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
