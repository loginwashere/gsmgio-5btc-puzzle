#!/usr/bin/env python3
"""Tests for the frozen Phase 442 prime-basics representation precedent audit."""

import phase442_prime_basics_representation_precedent_audit as phase442


def test_phase442_self_test_passes():
    phase442.self_test()


def test_phase442_representation_elimination():
    result = phase442.audit()
    check = result["representation_letter_check"]
    assert check["raw_block_is_pure_letters"] is False
    assert check["cipher_is_pure_letters"] is True


def test_phase442_no_overlap_and_zero_hits():
    result = phase442.audit()
    assert result["overlap_with_phase270_materials"] == 0
    assert result["structural_oracle"]["hits"] == 0
    assert result["new_candidate_count"] == 3
    assert result["new_material_count"] == 6
