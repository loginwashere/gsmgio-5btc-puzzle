#!/usr/bin/env python3
"""Tests for the frozen Phase 443 answer_321 precedent-gap follow-up."""

import phase443_answer321_prime_basics_followup as phase443


def test_phase443_self_test_passes():
    phase443.self_test()


def test_phase443_closes_second_eligible_representation():
    result = phase443.audit()
    assert result["source"]["is_pure_uppercase_letters"] is True
    assert result["answer321_prime_rule_selection"] == phase443.EXPECTED_SELECTION
    assert result["candidate_count"] == 3
    assert result["material_count"] == 6


def test_phase443_is_new_and_negative():
    result = phase443.audit()
    assert result["overlap_with_phase270_materials"] == 0
    assert result["overlap_with_phase442_materials"] == 0
    assert result["structural_oracle"] == {"trial_count": 36, "hits": 0}
    assert result["disposition"] == "two_representation_precedent_family_exhausted_negative"
