#!/usr/bin/env python3
"""Regression tests for Phase 458."""

import phase458_new_window_creator_sweep as phase458


def test_phase458_mechanics():
    result = phase458.self_test()
    assert result["verdict"] == "gap_vocabulary_hit_licensed"
    assert result["creator_message_count"] == 2
    assert result["any_creator_media"] is True


def test_phase458_real_corpus():
    result = phase458.real_corpus_self_test()
    assert result["verdict"] == "no_creator_activity_in_window"
    assert result["window_message_count"] == 2516
    assert result["creator_message_count"] == 0
    assert len(result["creator_media"]) == 0


if __name__ == "__main__":
    test_phase458_mechanics()
    test_phase458_real_corpus()
    print("[*] Phase 458 tests passed")
