#!/usr/bin/env python3
"""Tests for the frozen Phase 438 provenance audit."""

import phase438_phase32_representation_provenance_audit as phase438


def test_phase438_live_audit():
    report = phase438.audit()
    assert report["representations"]["raw_encoded_321"]["distinct_symbols"] == 26
    assert report["transcoding_comparison"]["cp273_equals_cp1141"] is True
    assert report["transcoding_comparison"]["differing_position_count"] == 0
    assert report["notebook"]["first_commit"]["commit"] == phase438.FIRST_NOTEBOOK_COMMIT
    assert report["telegram"]["union_hit_count"] == phase438.EXPECTED_UNION_COUNT
    assert report["telegram"]["creator_authored_hit_ids"] == []
    assert report["telegram"]["creator_direct_reply_ids"] == []
    assert report["decision"] == "workflow_privilege_without_downstream_binding"


def test_phase438_is_nonexecuting():
    report = phase438.audit()
    assert report["password_materials_generated"] == 0
    assert report["oracle_calls"] == 0
    assert report["gpu_touched"] is False
    assert not any(
        gates["locally_selected"] or gates["unique_representation"]
        for gates in report["phase437_gate_updates"].values()
    )
