#!/usr/bin/env python3
"""Tests for the frozen Phase 448 brute-force eligibility audit."""

import phase448_bruteforce_eligibility_audit as phase448


def test_phase448_self_test_passes():
    phase448.self_test()


def test_all_open_gaps_are_covered_once():
    report = phase448.audit()
    ids = [row["id"] for row in report["rows"]]
    assert tuple(report["open_gap_ids"]) == phase448.EXPECTED_GAPS
    assert all(ids.count(gap_id) == 1 for gap_id in phase448.EXPECTED_GAPS)


def test_no_row_passes_all_seven_gates():
    report = phase448.audit()
    assert len(report["gate_names"]) == 7
    assert report["eligible_constructions"] == []
    assert all(row["failed_gates"] for row in report["rows"])


def test_finite_backfill_is_not_misclassified_as_a_construction():
    report = phase448.audit()
    row = next(row for row in report["rows"] if row["id"] == "P32-F09-BACKFILL")
    assert row["finite_skeleton"] is True
    assert row["gates"]["clue_selected_operands"] is False
    assert row["passed_gate_count"] == 6
    assert row["bruteforce_eligible"] is False


def test_phase448_is_oracle_free():
    report = phase448.audit()
    assert report["password_materials_generated"] == 0
    assert report["oracle_calls"] == 0
    assert report["gpu_touched"] is False
    assert report["docker_touched"] is False
    assert report["network_touched"] is False
    assert report["external_agents_used"] is False
