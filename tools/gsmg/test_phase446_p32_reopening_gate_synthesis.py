#!/usr/bin/env python3
"""Tests for the Phase 446 P32 reopening-gate synthesis."""

import phase446_p32_reopening_gate_synthesis as phase446


def test_phase446_self_test_passes():
    phase446.self_test()


def test_phase446_has_unique_family_rows_and_valid_phase_citations():
    report = phase446.audit()
    ids = [row["id"] for row in report["families"]]
    assert len(ids) == len(set(ids)) == 15
    assert all(row["phases"] for row in report["families"])


def test_phase446_separates_the_only_directly_runnable_residual():
    report = phase446.audit()
    assert report["directly_runnable_finite_residuals"] == ["P32-F09"]
    row = next(row for row in report["families"] if row["id"] == "P32-F09")
    assert row["residual_class"] == "finite_unrun"
    assert "whitespace" in row["untested"].lower()


def test_phase446_is_synthesis_only():
    report = phase446.audit()
    assert report["password_materials_generated"] == 0
    assert report["oracle_calls"] == 0
    assert report["gpu_touched"] is False
    assert report["docker_touched"] is False
    assert report["network_touched"] is False
    assert report["external_agents_used"] is False
