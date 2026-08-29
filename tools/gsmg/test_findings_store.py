#!/usr/bin/env python3
"""Tests for the canonical per-phase findings store."""

import re
from urllib.parse import unquote

import findings_store


def test_fragment_store_rebuilds_compatibility_file_exactly():
    assert findings_store.read_findings() == findings_store.MONOLITH.read_text(
        encoding="utf-8"
    )


def test_manifest_and_five_digit_filenames_are_valid():
    data, fragments = findings_store.validate_store()
    assert data["phase_count"] == len(data["entries"]) == len(fragments)
    assert all(
        re.fullmatch(r"P\d{5}(?:-\d+)?(?:-[A-Z][A-Z0-9]*)?\.md", entry["file"])
        for entry in data["entries"]
    )


def test_exceptional_names_are_stable():
    data, _ = findings_store.validate_store()
    by_id = {entry["stable_id"]: entry["file"] for entry in data["entries"]}
    assert by_id["P0_1"] == "P00000-1.md"
    assert by_id["P0_2"] == "P00000-2.md"
    assert findings_store.phase_sort_stem("1") == "P00001"
    assert findings_store.phase_sort_stem("10000") == "P10000"
    assert by_id["P008-A"] == "P00008-A.md"
    assert by_id["P008-B"] == "P00008-B.md"
    assert by_id["P019-A"] == "P00019-A.md"
    assert by_id["P019-B"] == "P00019-B.md"


def test_each_fragment_contains_exactly_one_phase_heading():
    _, fragments = findings_store.validate_store()
    for fragment in fragments:
        findings_store.phase_heading(fragment)


def test_relative_markdown_links_resolve_from_both_locations():
    data, fragments = findings_store.validate_store()
    canonical = [
        (findings_store.STORE_DIR / data["preamble"]).read_text(encoding="utf-8")
    ] + fragments
    for text in canonical:
        for target in re.findall(r"!?\[[^\]]*\]\((\.\./[^)]+)\)", text):
            path = unquote(target.split("#", 1)[0])
            assert (findings_store.STORE_DIR / path).resolve().exists(), target

    generated = findings_store.read_findings()
    for target in re.findall(r"!?\[[^\]]*\]\((\.\./[^)]+)\)", generated):
        path = unquote(target.split("#", 1)[0])
        assert (findings_store.MONOLITH.parent / path).resolve().exists(), target


def test_link_depth_transform_round_trips():
    sample = "[report](../../doc/example.md) and https://example.com"
    assert findings_store.shallow_relative_links(
        findings_store.deepen_relative_links(sample)
    ) == sample
