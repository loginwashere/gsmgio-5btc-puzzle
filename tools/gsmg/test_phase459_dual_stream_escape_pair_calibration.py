#!/usr/bin/env python3
"""Regression entry point for Phase 459."""

import json
import math

import phase459_dual_stream_escape_pair_calibration as phase459


def test_phase459_mechanics():
    result = phase459.self_test()
    assert result["specialized_fixture"]["contrast"] > 0
    assert result["shared_fixture"]["contrast"] <= 0.002

    stored = json.loads(phase459.DEFAULT_OUTPUT.read_text(encoding="utf-8"))
    real = phase459.score_streams({"DBBI": phase459.DBBI, "FAED": phase459.FAED})
    assert math.isclose(real["contrast"], -0.48448680439150293, abs_tol=1e-15)
    assert json.loads(json.dumps(real)) == stored["observed"]
    assert stored["decision"] == "no_calibrated_specialization"


if __name__ == "__main__":
    test_phase459_mechanics()
    print("[*] Phase 459 tests passed")
