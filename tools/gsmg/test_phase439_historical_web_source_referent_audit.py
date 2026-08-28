#!/usr/bin/env python3
"""Tests for the frozen Phase 439 web-source eligibility audit."""

import phase439_historical_web_source_referent_audit as phase439


def test_phase439_live_audit():
    report = phase439.audit()
    assert report["candidate_count"] == 11
    assert report["eligible_referents"] == ()
    assert report["newly_registered_historical_source_referents"] == (
        "raw_seed_html", "raw_choice_html", "ordered_prior_html_pair", "ordered_source_comment_pair"
    )
    rows = {row["id"]: row for row in report["candidates"]}
    assert rows["ordered_source_comment_pair"]["gates"]["stable_representation"] is True
    assert rows["ordered_source_comment_pair"]["failed_gates"] == (
        "locally_selected", "operator_fixed", "unit_boundary_fixed", "consumer_fixed"
    )
    assert rows["csrf_values"]["gates"]["creator_puzzle_artifact"] is False
    assert rows["restored_puzzle_html"]["gates"]["chronologically_returnable"] is False


def test_phase439_is_nonexecuting():
    report = phase439.audit()
    assert report["decision"] == "new_source_referent_registered_but_ineligible"
    assert report["prime_extractions_generated"] == 0
    assert report["password_materials_generated"] == 0
    assert report["oracle_calls"] == 0
    assert report["docker_touched"] is False
    assert report["gpu_touched"] is False
