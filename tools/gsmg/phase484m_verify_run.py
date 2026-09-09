#!/usr/bin/env python3
"""Fail-closed verifier for Phase 484M."""

from __future__ import annotations

import json

import phase484m_powered_bidirectional_faed_real as real


def verify() -> dict:
    lock = real.verify_lock()
    result = json.loads(real.RESULT_PATH.read_text())
    errors = []
    if result.get("execution_lock_sha256") != real.sha256_file(real.LOCK_PATH):
        errors.append("lock hash mismatch")
    if result.get("faed_ascii_sha256") != lock["faed_ascii_sha256"]:
        errors.append("FAED hash mismatch")
    for field in ("scope", "budgets"):
        if result.get(field) != lock[field]:
            errors.append(f"{field} mismatch")
    cells = result.get("cells", [])
    expected = {
        (width, pair_index)
        for width in real.WIDTHS for pair_index in range(len(real.PAIRS))
    }
    seen = {(cell.get("width"), cell.get("pair_index")) for cell in cells}
    if seen != expected or len(cells) != len(expected):
        errors.append("cell set mismatch")
    ranked = sorted(
        cells,
        key=lambda cell: (
            -cell["normalized_score"], cell["width"],
            cell["pair_index"], cell["order"],
        ),
    )
    if ranked:
        if result.get("family_best") != ranked[0]:
            errors.append("family best mismatch")
        if result.get("top") != ranked[:real.TOP_RESULTS]:
            errors.append("top list mismatch")
        trigger = ranked[0]["normalized_score"] >= real.SCORE_FLOOR
        if result.get("score_trigger") is not trigger:
            errors.append("trigger mismatch")
    return {
        "phase": "484M",
        "consistent": not errors,
        "errors": errors,
        "execution_lock_sha256": real.sha256_file(real.LOCK_PATH),
        "result_sha256": real.sha256_file(real.RESULT_PATH),
        "score_trigger": result.get("score_trigger"),
    }


def main() -> int:
    record = verify()
    path = real.SCRIPT_DIR / "phase484m_verification.json"
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(json.dumps(record, indent=2, sort_keys=True))
    return 0 if record["consistent"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
