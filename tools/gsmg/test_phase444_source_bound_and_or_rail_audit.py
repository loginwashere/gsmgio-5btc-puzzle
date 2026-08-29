#!/usr/bin/env python3
"""Tests for the frozen Phase 444 source-bound AND/OR rail audit."""

import phase444_source_bound_and_or_rail_audit as phase444


def test_phase444_self_test_passes():
    phase444.self_test()


def test_phase444_rails_and_intertwined_regressions():
    result = phase444.audit()
    for source_id, expected in phase444.EXPECTED_SOURCES.items():
        assert result["sources"][source_id]["rails"]["blue_only"] == expected["blue_only"]
        assert result["sources"][source_id]["rails"]["yellow_only"] == expected["yellow_only"]
        assert (
            result["sources"][source_id]["rails"]["blue_then_yellow"]
            == expected["blue_then_yellow"]
        )
        assert (
            result["sources"][source_id]["rails"]["intertwined"]
            == expected["intertwined"]
        )


def test_phase444_sealed_inventory_is_new_and_negative():
    result = phase444.audit()
    assert result["candidate_count"] == 18
    assert result["material_count"] == 36
    assert result["new_material_count"] == 36
    assert all(
        count == 0 for count in result["prior_overlap_material_counts"].values()
    )
    assert result["structural_oracle"] == {"trial_count": 216, "hits": 0}
    assert result["disposition"] == "bounded_two_source_and_or_rail_family_negative"
