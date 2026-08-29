#!/usr/bin/env python3
"""Regression tests for Phase 449."""

import phase449_g_esc_pair_discrimination_audit as phase449


def test_phase449_decision():
    result = phase449.self_test()
    assert result["working_ranking"] == ["GI", "HE"]
    assert result["contradiction_audit"]["HE_english_checkerboard_profile_strongly_disfavored"]
    assert not result["contradiction_audit"]["HE_pair_level_contradicted"]
    assert result["password_materials_generated"] == 0
    assert result["oracle_calls"] == 0


if __name__ == "__main__":
    test_phase449_decision()
    print("[*] Phase 449 tests passed")
