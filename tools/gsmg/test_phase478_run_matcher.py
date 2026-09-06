"""Self-tests for the Phase 478 matcher, against fabricated manifests and
oracle locks only -- never the real phase478_manifest.jsonl. Positive
fixtures use a REAL SHA-256 of a chosen synthetic byte string and target
that digest's own genuinely-computed equality pattern (never DBBI's real
pattern) -- the matcher's comparison logic is exercised honestly, without
needing to search for a preimage of an arbitrary pattern."""

import base64
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

from phase478_common import equality_pattern
from phase478_run_matcher import (
    MatcherError,
    iter_eligible_manifest_entries,
    run,
    run_matcher,
    score_entry,
    verify_oracle_lock,
)


def _entry(bytes_literal: bytes, source_file="a.py", eligible=True, phase="unknown"):
    return {
        "bytes_b64": base64.b64encode(bytes_literal).decode(),
        "source_file": source_file,
        "source_blob_sha": "0" * 40,
        "call_sites": [],
        "phase": phase,
        "construction_label": "synthetic fixture literal",
        "transformation": "raw",
        "eligible": eligible,
        "eligible_reason": None,
    }


def _write_manifest(path, entries):
    with open(path, "w") as f:
        for e in entries:
            f.write(json.dumps(e))
            f.write("\n")


def _real_pattern_of(bytes_literal: bytes) -> str:
    digest_hex = hashlib.sha256(bytes_literal).hexdigest()
    return equality_pattern(list(digest_hex))


# ---------------------------------------------------------------------------
# score_entry
# ---------------------------------------------------------------------------

def test_score_entry_matches_its_own_real_pattern():
    literal = b"phase478-synthetic-fixture-one"
    own_pattern = _real_pattern_of(literal)
    entry = _entry(literal)
    is_match, positions, pattern = score_entry(entry, target_pattern=own_pattern)
    assert is_match is True
    assert positions == 64
    assert pattern == own_pattern


def test_score_entry_rejects_flipped_target_pattern():
    literal = b"phase478-synthetic-fixture-two"
    own_pattern = _real_pattern_of(literal)
    # Flip a single character of the target so it cannot equal `own_pattern`,
    # by construction, while keeping everything else the same shape.
    flipped_char = "1" if own_pattern[0] != "1" else "2"
    flipped_target = flipped_char + own_pattern[1:]
    entry = _entry(literal)
    is_match, positions, pattern = score_entry(entry, target_pattern=flipped_target)
    assert is_match is False
    assert positions == 63


def test_score_entry_never_renormalizes_bytes():
    literal = b"\x00\x01\xffsome-raw-bytes"
    entry = _entry(literal)
    is_match, positions, pattern = score_entry(entry, target_pattern=_real_pattern_of(literal))
    assert is_match is True


# ---------------------------------------------------------------------------
# iter_eligible_manifest_entries
# ---------------------------------------------------------------------------

def test_iter_eligible_manifest_entries_skips_ineligible():
    tmp = Path(tempfile.mkdtemp())
    try:
        p = tmp / "manifest.jsonl"
        _write_manifest(p, [
            _entry(b"one", eligible=True),
            _entry(b"two", eligible=False),
            _entry(b"three", eligible=True),
        ])
        seen = [e["bytes_b64"] for e in iter_eligible_manifest_entries(p)]
        assert seen == [
            base64.b64encode(b"one").decode(),
            base64.b64encode(b"three").decode(),
        ]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------------------
# run_matcher
# ---------------------------------------------------------------------------

def test_run_matcher_reports_no_match_on_all_misses():
    tmp = Path(tempfile.mkdtemp())
    try:
        p = tmp / "manifest.jsonl"
        _write_manifest(p, [_entry(b"alpha"), _entry(b"beta"), _entry(b"gamma")])
        # A target pattern that is a real digest's own pattern with one
        # character flipped can never equal any of the three real patterns
        # by the flip alone being an insufficient coincidence at this scale,
        # but to make the negative deterministic rather than merely
        # improbable, use an impossible-shape target: 64 copies of the same
        # label, which no SHA-256 hex digest can ever produce (a digest
        # using exactly 1 distinct hex value across 64 characters is
        # astronomically improbable and not present in these 3 fixtures).
        impossible_target = "0" * 64
        report = run_matcher(p, target_pattern=impossible_target)
        assert report["match_found"] is False
        assert report["eligible_scored"] == 3
        assert "best_miss" in report
        assert report["best_miss"]["matching_positions"] < 64
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_run_matcher_finds_a_planted_match():
    tmp = Path(tempfile.mkdtemp())
    try:
        p = tmp / "manifest.jsonl"
        literal = b"phase478-synthetic-planted-hit"
        target = _real_pattern_of(literal)
        _write_manifest(p, [
            _entry(b"decoy-one", source_file="decoy.py"),
            _entry(literal, source_file="hit.py"),
            _entry(b"decoy-two", source_file="decoy2.py"),
        ])
        report = run_matcher(p, target_pattern=target)
        assert report["match_found"] is True
        assert report["match"]["source_file"] == "hit.py"
        assert report["match"]["pattern"] == target
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_run_matcher_ignores_ineligible_even_if_it_would_match():
    tmp = Path(tempfile.mkdtemp())
    try:
        p = tmp / "manifest.jsonl"
        literal = b"phase478-would-match-but-ineligible"
        target = _real_pattern_of(literal)
        _write_manifest(p, [_entry(literal, eligible=False)])
        report = run_matcher(p, target_pattern=target)
        assert report["match_found"] is False
        assert report["eligible_scored"] == 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------------------
# verify_oracle_lock / run
# ---------------------------------------------------------------------------

def _real_dbbi_pattern():
    from phase478_common import DBBI_PATTERN
    return DBBI_PATTERN


def test_verify_oracle_lock_rejects_manifest_hash_mismatch():
    tmp = Path(tempfile.mkdtemp())
    try:
        manifest_path = tmp / "manifest.jsonl"
        _write_manifest(manifest_path, [_entry(b"x")])
        lock = {
            "manifest_sha256": "0" * 64,
            "dbbi_pattern": _real_dbbi_pattern(),
            "matcher_script_sha256": "irrelevant-for-this-test",
        }
        try:
            verify_oracle_lock(lock, manifest_path, Path(__file__))
            assert False, "expected MatcherError"
        except MatcherError as e:
            assert "manifest_sha256" in str(e)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_verify_oracle_lock_rejects_dbbi_pattern_mismatch():
    tmp = Path(tempfile.mkdtemp())
    try:
        manifest_path = tmp / "manifest.jsonl"
        _write_manifest(manifest_path, [_entry(b"x")])
        actual_sha = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        lock = {
            "manifest_sha256": actual_sha,
            "dbbi_pattern": "0" * 64,  # deliberately wrong
            "matcher_script_sha256": "irrelevant-for-this-test",
        }
        try:
            verify_oracle_lock(lock, manifest_path, Path(__file__))
            assert False, "expected MatcherError"
        except MatcherError as e:
            assert "dbbi_pattern" in str(e)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_verify_oracle_lock_rejects_matcher_script_hash_mismatch():
    tmp = Path(tempfile.mkdtemp())
    try:
        manifest_path = tmp / "manifest.jsonl"
        _write_manifest(manifest_path, [_entry(b"x")])
        actual_sha = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        lock = {
            "manifest_sha256": actual_sha,
            "dbbi_pattern": _real_dbbi_pattern(),
            "matcher_script_sha256": "0" * 64,
        }
        try:
            verify_oracle_lock(lock, manifest_path, Path(__file__))
            assert False, "expected MatcherError"
        except MatcherError as e:
            assert "matcher_script_sha256" in str(e)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_verify_oracle_lock_happy_path():
    tmp = Path(tempfile.mkdtemp())
    try:
        manifest_path = tmp / "manifest.jsonl"
        _write_manifest(manifest_path, [_entry(b"x")])
        actual_sha = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        # Use THIS test file itself as a stand-in "matcher script" so we can
        # compute its real hash without depending on the real matcher's
        # current on-disk content (which changes as this file is edited).
        stand_in_script = Path(__file__)
        matcher_sha = hashlib.sha256(stand_in_script.read_bytes()).hexdigest()
        lock = {
            "manifest_sha256": actual_sha,
            "dbbi_pattern": _real_dbbi_pattern(),
            "matcher_script_sha256": matcher_sha,
        }
        verify_oracle_lock(lock, manifest_path, stand_in_script)  # must not raise
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_run_end_to_end_rejects_unlocked_manifest():
    tmp = Path(tempfile.mkdtemp())
    try:
        manifest_path = tmp / "manifest.jsonl"
        _write_manifest(manifest_path, [_entry(b"x")])
        lock_path = tmp / "oracle_lock.json"
        lock_path.write_text(json.dumps({
            "manifest_sha256": "0" * 64,
            "dbbi_pattern": _real_dbbi_pattern(),
            "matcher_script_sha256": "0" * 64,
        }))
        report_path = tmp / "report.json"
        try:
            run(lock_path, manifest_path, report_path)
            assert False, "expected MatcherError"
        except MatcherError:
            pass
        assert not report_path.exists(), "no report artifact may be written on a rejected lock"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    import sys
    import traceback

    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    failures = 0
    for t in tests:
        try:
            t()
            print(f"OK   {t.__name__}")
        except AssertionError:
            failures += 1
            print(f"FAIL {t.__name__}")
            traceback.print_exc()
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    sys.exit(1 if failures else 0)
