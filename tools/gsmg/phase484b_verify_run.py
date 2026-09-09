#!/usr/bin/env python3
"""Fail-closed structural verifier for the locked Phase 484B real run."""

from __future__ import annotations

import json
import math

import phase484b_raw_symbol_vic_real_audit as audit


def validate_result(result: dict, expected_lock_sha256: str | None = None) -> list[str]:
    errors = []
    if result.get("phase") != "484B" or result.get("faed_ascii_sha256") != audit.input_sha256(audit.FAED):
        errors.append("phase or FAED identity mismatch")
    if (expected_lock_sha256 is not None
            and result.get("execution_lock_sha256") != expected_lock_sha256):
        errors.append("execution lock hash mismatch")
    cells = result.get("cells", [])
    if [cell.get("width") for cell in cells] != list(audit.WIDTHS):
        errors.append("width cell set/order mismatch")
    candidates = []
    for cell in cells:
        top = cell.get("top", [])
        if len(top) != audit.TOP_PER_WIDTH:
            errors.append(f"top candidate count mismatch at width {cell.get('width')}")
        expected_total = len(audit.solver.ESCAPE_PAIRS) * math.factorial(cell.get("width", 0))
        if cell.get("hypotheses_total") != expected_total:
            errors.append(f"hypothesis total mismatch at width {cell.get('width')}")
        sort_keys = [(-c["normalized_score"], c["pair_index"], c["order"]) for c in top]
        if sort_keys != sorted(sort_keys):
            errors.append(f"candidate ordering mismatch at width {cell.get('width')}")
        for candidate in top:
            if candidate.get("pair") != list(audit.solver.ESCAPE_PAIRS[candidate["pair_index"]]):
                errors.append("pair index/value mismatch")
            expected_score = audit.solver.normalized_quadgram_score(
                candidate["quadgram_score"], candidate["decoded_length"]
            )
            if abs(candidate["normalized_score"] - expected_score) > 1e-12:
                errors.append("normalized score mismatch")
            if len(candidate.get("plaintext", "")) != candidate.get("decoded_length"):
                errors.append("plaintext length mismatch")
            candidates.append(candidate | {"width": cell["width"]})
    candidates.sort(key=lambda c: (-c["normalized_score"], c["width"], c["pair_index"], c["order"]))
    if not candidates or result.get("family_best") != candidates[0]:
        errors.append("family maximum mismatch")
    else:
        trigger = candidates[0]["normalized_score"] >= audit.HOLDOUT_SCORE_FLOOR
        if result.get("score_trigger") != trigger:
            errors.append("score trigger mismatch")
        expected_disposition = (
            "confirmation_required" if trigger
            else "no_powered_family_solve_no_calibrated_null_claim"
        )
        if result.get("disposition") != expected_disposition:
            errors.append("disposition mismatch")
    return errors


def verify() -> dict:
    audit.verify_lock()
    result = json.loads(audit.RESULT_PATH.read_text())
    lock_sha256 = audit.sha256_file(audit.LOCK_PATH)
    errors = validate_result(result, lock_sha256)
    return {
        "phase": "484B",
        "consistent": not errors,
        "errors": errors,
        "score_trigger": result.get("score_trigger"),
        "execution_lock_sha256": lock_sha256,
        "result_sha256": audit.sha256_file(audit.RESULT_PATH),
    }


if __name__ == "__main__":
    output = verify()
    print(json.dumps(output, indent=2))
    raise SystemExit(0 if output["consistent"] else 1)
