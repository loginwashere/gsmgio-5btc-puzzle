#!/usr/bin/env python3
"""Tests for the frozen Phase 440 source-comment prime reading."""

from collections import Counter

import phase440_source_comment_prime_reading as phase440


def test_phase440_inventory_and_partition():
    report = phase440.audit()
    assert report["variant_count"] == 32
    assert Counter(row["unit"] for row in report["rows"]) == {"letters": 16, "words": 16}
    groups = {}
    for row in report["rows"]:
        key = (row["unit"], row["boundary"], row["index_base"], row["direction"])
        groups.setdefault(key, {})[row["rail"]] = row
    assert len(groups) == 16
    for rails in groups.values():
        assert rails["prime"]["selected_unit_count"] + rails["nonprime"]["selected_unit_count"] == rails["prime"]["source_unit_count"]


def test_phase440_outputs_and_stop_conditions():
    report = phase440.audit()
    assert all(row["display"] for row in report["rows"])
    assert all(len(row["sha256"]) == 64 for row in report["rows"])
    assert report["password_materials_generated"] == 0
    assert report["oracle_calls"] == 0
    assert report["docker_touched"] is False
    assert report["gpu_touched"] is False
