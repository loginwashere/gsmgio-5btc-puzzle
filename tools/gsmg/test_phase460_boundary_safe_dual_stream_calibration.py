#!/usr/bin/env python3
"""Regression entry point for Phase 460."""

import json
import math

import phase460_boundary_safe_dual_stream_calibration as phase460


def test_phase460_mechanics():
    result = phase460.self_test()
    assert result["specialized_fixture"]["contrast"] > 0

    stored = json.loads(phase460.DEFAULT_OUTPUT.read_text(encoding="utf-8"))
    real = phase460.score_streams({"DBBI": phase460.DBBI, "FAED": phase460.FAED})
    assert math.isclose(real["contrast"], 0.007259571881754762, abs_tol=1e-15)
    assert json.loads(json.dumps(real)) == stored["observed"]
    assert stored["decision"] == "no_calibrated_specialization"


if __name__ == "__main__":
    test_phase460_mechanics()
    print("[*] Phase 460 tests passed")
