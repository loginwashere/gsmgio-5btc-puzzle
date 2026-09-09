#!/usr/bin/env python3
"""Fail-closed verifier for the Phase 484D width-7 real result."""

import json

import phase484d_width7_real_audit as audit


def verify() -> dict:
    audit.verify_lock()
    result = json.loads(audit.RESULT_PATH.read_text())
    errors = []
    if result.get("execution_lock_sha256") != audit.sha256_file(audit.LOCK_PATH):
        errors.append("lock hash mismatch")
    if result.get("faed_ascii_sha256") != audit.faed_sha256():
        errors.append("FAED hash mismatch")
    if result.get("hypotheses_total") != audit.solver.HYPOTHESES_TOTAL:
        errors.append("hypothesis total mismatch")
    top = result.get("top", [])
    if len(top) != audit.TOP_COUNT:
        errors.append("top count mismatch")
    keys = [(-c["normalized_score"], c["pair_index"], c["order"]) for c in top]
    if keys != sorted(keys):
        errors.append("candidate ordering mismatch")
    for candidate in top:
        if candidate["pair"] != list(audit.solver.base.ESCAPE_PAIRS[candidate["pair_index"]]):
            errors.append("pair mapping mismatch")
        if len(candidate["plaintext"]) != candidate["decoded_length"]:
            errors.append("plaintext length mismatch")
        expected = audit.solver.base.normalized_quadgram_score(
            candidate["quadgram_score"], candidate["decoded_length"]
        )
        if abs(expected - candidate["normalized_score"]) > 1e-12:
            errors.append("normalized score mismatch")
    if not top or result.get("family_best") != top[0]:
        errors.append("family maximum mismatch")
    else:
        trigger = top[0]["normalized_score"] >= audit.HOLDOUT_SCORE_FLOOR
        if result.get("score_trigger") != trigger:
            errors.append("trigger mismatch")
        expected = "confirmation_required" if trigger else "no_powered_width7_solve_no_calibrated_null_claim"
        if result.get("disposition") != expected:
            errors.append("disposition mismatch")
    return {
        "phase": "484D",
        "consistent": not errors,
        "errors": errors,
        "score_trigger": result.get("score_trigger"),
        "execution_lock_sha256": audit.sha256_file(audit.LOCK_PATH),
        "result_sha256": audit.sha256_file(audit.RESULT_PATH),
    }


if __name__ == "__main__":
    output = verify()
    print(json.dumps(output, indent=2))
    raise SystemExit(0 if output["consistent"] else 1)
