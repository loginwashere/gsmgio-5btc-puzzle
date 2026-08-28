#!/usr/bin/env python3
"""Tests for the frozen Phase 441 completed-run analysis."""

import json

import phase441_completed_bifid16_run_analysis as phase441


def test_phase441_saved_full_result():
    report = json.loads((phase441.REPO_ROOT / "tools/gsmg/phase441_result.json").read_text())
    assert report["completion"]["complete_fraction"] == 1.0
    assert report["completion"]["interrupted"] is False
    assert report["completion"]["shortlist_is_exact_top_k"] is False
    assert report["exact_winner"]["rank"] == 8_041_961_541_600
    assert report["equivalence_and_invariance"]["class_sizes_descending"] == [524, 469, 1, 1, 1, 1, 1, 1, 1]
    assert report["equivalence_and_invariance"]["fixed_keyword_union"] == []
    assert report["decision"] == "exact_16factorial_negative_quadgram_selection_pathology_confirmed"


def test_phase441_stop_conditions():
    report = json.loads((phase441.REPO_ROOT / "tools/gsmg/phase441_result.json").read_text())
    assert report["password_materials_generated"] == 0
    assert report["oracle_calls"] == 0
    assert report["new_gpu_work"] is False
    assert report["docker_mutated"] is False
