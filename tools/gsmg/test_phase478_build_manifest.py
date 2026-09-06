"""Self-tests for the Phase 478 manifest builder, against fabricated raw
captures, annotations, and discovery locks only -- never the real
phase478_raw_capture.jsonl or phase478_manifest_annotations.json."""

import hashlib
import json
import shutil
import tempfile
from pathlib import Path

from phase478_build_manifest import (
    ManifestBuildError,
    build_manifest_entries,
    classify_candidate,
    load_raw_capture,
    run,
    verify_provenance,
    write_manifest_jsonl,
)


def _write_jsonl(path, records):
    with open(path, "w") as f:
        for r in records:
            f.write(json.dumps(r))
            f.write("\n")


def _basic_header(lock_sha):
    return {
        "record_type": "header",
        "phase": 478,
        "discovery_lock_sha256": lock_sha,
        "cutoff_commit": "deadbeef",
        "generator_oracle_count": 1,
        "total_candidate_count": 1,
    }


def _basic_source(source_file="a.py", blob_sha="0" * 40, status="ok", candidate_count=1):
    return {
        "record_type": "source",
        "source_file": source_file,
        "source_blob_sha": blob_sha,
        "status": status,
        "candidate_count": candidate_count,
    }


def _basic_candidate(source_file="a.py", bytes_b64="AAAA", lines=(10,)):
    return {
        "record_type": "candidate",
        "source_file": source_file,
        "bytes_b64": bytes_b64,
        "call_sites": [
            {
                "entrypoint": "aes_try_open_bytes",
                "caller_file": f"/tmp/phase478_snapshot_xyz/{source_file}",
                "caller_line": line,
                "caller_function": "f",
            }
            for line in lines
        ],
    }


def _basic_lock(source_file="a.py", blob_sha="0" * 40):
    return {
        "eligible_py_file_classification": [
            {"path": source_file, "blob_sha": blob_sha, "category": "generator+oracle"},
        ]
    }


def _basic_annotation(construction_label="build the literal", lines=(10,), eligible=True, eligible_reason=None):
    return {
        "phase": "unknown",
        "constructions": [
            {
                "construction_label": construction_label,
                "transformation": "raw",
                "applies_to_lines": list(lines),
                "applies_to_function": "f",
                "eligible": eligible,
                "eligible_reason": eligible_reason,
            }
        ],
    }


# ---------------------------------------------------------------------------
# load_raw_capture
# ---------------------------------------------------------------------------

def test_load_raw_capture_parses_header_source_and_candidates():
    tmp = Path(tempfile.mkdtemp())
    try:
        p = tmp / "raw.jsonl"
        _write_jsonl(p, [_basic_header("x"), _basic_source(), _basic_candidate()])
        header, sources, candidates = load_raw_capture(p)
        assert header["discovery_lock_sha256"] == "x"
        assert "a.py" in sources
        assert len(candidates["a.py"]) == 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_load_raw_capture_rejects_duplicate_header():
    tmp = Path(tempfile.mkdtemp())
    try:
        p = tmp / "raw.jsonl"
        _write_jsonl(p, [_basic_header("x"), _basic_header("x")])
        try:
            load_raw_capture(p)
            assert False, "expected ManifestBuildError"
        except ManifestBuildError:
            pass
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------------------
# verify_provenance
# ---------------------------------------------------------------------------

def test_verify_provenance_happy_path():
    tmp = Path(tempfile.mkdtemp())
    try:
        lock_path = tmp / "lock.json"
        lock = _basic_lock()
        lock_path.write_text(json.dumps(lock))
        lock_sha = hashlib.sha256(lock_path.read_bytes()).hexdigest()

        header = _basic_header(lock_sha)
        sources = {"a.py": _basic_source()}
        verify_provenance(header, sources, lock, lock_path)  # must not raise
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_verify_provenance_rejects_wrong_lock_hash():
    tmp = Path(tempfile.mkdtemp())
    try:
        lock_path = tmp / "lock.json"
        lock = _basic_lock()
        lock_path.write_text(json.dumps(lock))

        header = _basic_header("not-the-real-hash")
        sources = {"a.py": _basic_source()}
        try:
            verify_provenance(header, sources, lock, lock_path)
            assert False, "expected ManifestBuildError"
        except ManifestBuildError:
            pass
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_verify_provenance_rejects_non_ok_status():
    tmp = Path(tempfile.mkdtemp())
    try:
        lock_path = tmp / "lock.json"
        lock = _basic_lock()
        lock_path.write_text(json.dumps(lock))
        lock_sha = hashlib.sha256(lock_path.read_bytes()).hexdigest()

        header = _basic_header(lock_sha)
        sources = {"a.py": _basic_source(status="harvest_failed")}
        try:
            verify_provenance(header, sources, lock, lock_path)
            assert False, "expected ManifestBuildError"
        except ManifestBuildError:
            pass
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_verify_provenance_rejects_blob_sha_mismatch():
    tmp = Path(tempfile.mkdtemp())
    try:
        lock_path = tmp / "lock.json"
        lock = _basic_lock(blob_sha="1" * 40)
        lock_path.write_text(json.dumps(lock))
        lock_sha = hashlib.sha256(lock_path.read_bytes()).hexdigest()

        header = _basic_header(lock_sha)
        sources = {"a.py": _basic_source(blob_sha="2" * 40)}
        try:
            verify_provenance(header, sources, lock, lock_path)
            assert False, "expected ManifestBuildError"
        except ManifestBuildError:
            pass
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_verify_provenance_rejects_missing_classification_entry():
    tmp = Path(tempfile.mkdtemp())
    try:
        lock_path = tmp / "lock.json"
        lock = _basic_lock(source_file="other.py")
        lock_path.write_text(json.dumps(lock))
        lock_sha = hashlib.sha256(lock_path.read_bytes()).hexdigest()

        header = _basic_header(lock_sha)
        sources = {"a.py": _basic_source()}
        try:
            verify_provenance(header, sources, lock, lock_path)
            assert False, "expected ManifestBuildError"
        except ManifestBuildError:
            pass
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------------------
# classify_candidate / build_manifest_entries
# ---------------------------------------------------------------------------

def test_classify_candidate_single_construction():
    ann = _basic_annotation(lines=(10, 11))
    cand = _basic_candidate(lines=(10,))
    assert classify_candidate("a.py", cand, ann["constructions"]) == [0]


def test_classify_candidate_raises_on_uncovered_line():
    ann = _basic_annotation(lines=(10, 11))
    cand = _basic_candidate(lines=(99,))
    try:
        classify_candidate("a.py", cand, ann["constructions"])
        assert False, "expected ManifestBuildError"
    except ManifestBuildError:
        pass


def test_classify_candidate_matches_multiple_constructions():
    annotations = {
        "phase": "unknown",
        "constructions": [
            {
                "construction_label": "construction A",
                "transformation": "raw",
                "applies_to_lines": [10],
                "applies_to_function": "f",
                "eligible": True,
                "eligible_reason": None,
            },
            {
                "construction_label": "construction B",
                "transformation": "hex",
                "applies_to_lines": [20],
                "applies_to_function": "g",
                "eligible": True,
                "eligible_reason": None,
            },
        ],
    }
    # A single candidate whose call sites hit lines from BOTH constructions
    # (the same bytes genuinely produced by two historical code paths).
    cand = {
        "record_type": "candidate",
        "source_file": "a.py",
        "bytes_b64": "AAAA",
        "call_sites": [
            {"entrypoint": "aes_try_open_bytes", "caller_file": "a.py", "caller_line": 10, "caller_function": "f"},
            {"entrypoint": "aes_try_open_bytes", "caller_file": "a.py", "caller_line": 20, "caller_function": "g"},
        ],
    }
    assert classify_candidate("a.py", cand, annotations["constructions"]) == [0, 1]

    sources = {"a.py": _basic_source()}
    entries = build_manifest_entries(sources, {"a.py": [cand]}, {"a.py": annotations})
    assert len(entries) == 1
    assert "construction A" in entries[0]["construction_label"]
    assert "construction B" in entries[0]["construction_label"]
    assert entries[0]["eligible"] is True


def test_build_manifest_entries_raises_on_missing_annotation():
    sources = {"a.py": _basic_source()}
    candidates = {"a.py": [_basic_candidate()]}
    try:
        build_manifest_entries(sources, candidates, {})
        assert False, "expected ManifestBuildError"
    except ManifestBuildError:
        pass


def test_build_manifest_entries_skips_files_with_zero_candidates():
    sources = {"a.py": _basic_source(candidate_count=0)}
    candidates = {}  # zero-candidate file never appears in the candidates dict
    entries = build_manifest_entries(sources, candidates, {})
    assert entries == []


def test_build_manifest_entries_preserves_ineligible_entries():
    ann = _basic_annotation(eligible=False, eligible_reason="doc/FOO.md: superseded")
    sources = {"a.py": _basic_source()}
    candidates = {"a.py": [_basic_candidate()]}
    entries = build_manifest_entries(sources, candidates, {"a.py": ann})
    assert len(entries) == 1
    assert entries[0]["eligible"] is False
    assert entries[0]["eligible_reason"] == "doc/FOO.md: superseded"


def test_build_manifest_entries_strips_snapshot_prefix_from_call_sites():
    sf = "tools/gsmg/a.py"
    ann = _basic_annotation(lines=(10,))
    sources = {sf: _basic_source(source_file=sf)}
    candidates = {sf: [_basic_candidate(source_file=sf, lines=(10,))]}
    entries = build_manifest_entries(sources, candidates, {sf: ann})
    assert entries[0]["call_sites"][0]["caller_file"] == sf


# ---------------------------------------------------------------------------
# write_manifest_jsonl / ordering
# ---------------------------------------------------------------------------

def test_write_manifest_jsonl_is_sorted_by_source_then_bytes():
    entries = [
        {"source_file": "z.py", "bytes_b64": "BBBB", "call_sites": [], "phase": "unknown",
         "construction_label": "x", "transformation": "raw", "eligible": True, "eligible_reason": None,
         "source_blob_sha": "0" * 40},
        {"source_file": "a.py", "bytes_b64": "ZZZZ", "call_sites": [], "phase": "unknown",
         "construction_label": "x", "transformation": "raw", "eligible": True, "eligible_reason": None,
         "source_blob_sha": "0" * 40},
        {"source_file": "a.py", "bytes_b64": "AAAA", "call_sites": [], "phase": "unknown",
         "construction_label": "x", "transformation": "raw", "eligible": True, "eligible_reason": None,
         "source_blob_sha": "0" * 40},
    ]
    tmp = Path(tempfile.mkdtemp())
    try:
        out = tmp / "manifest.jsonl"
        write_manifest_jsonl(entries, out)
        lines = out.read_text().splitlines()
        parsed = [json.loads(l) for l in lines]
        keys = [(e["source_file"], e["bytes_b64"]) for e in parsed]
        assert keys == [("a.py", "AAAA"), ("a.py", "ZZZZ"), ("z.py", "BBBB")]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_manifest_entries_never_contain_a_sha256_field():
    ann = _basic_annotation(lines=(10,))
    sources = {"a.py": _basic_source()}
    candidates = {"a.py": [_basic_candidate(lines=(10,))]}
    entries = build_manifest_entries(sources, candidates, {"a.py": ann})
    assert "sha256" not in entries[0]
    assert set(entries[0].keys()) == {
        "bytes_b64", "source_file", "source_blob_sha", "call_sites",
        "phase", "construction_label", "transformation", "eligible", "eligible_reason",
    }


# ---------------------------------------------------------------------------
# run() end-to-end, synthetic fixtures only
# ---------------------------------------------------------------------------

def test_run_end_to_end_synthetic():
    tmp = Path(tempfile.mkdtemp())
    try:
        lock = _basic_lock()
        lock_path = tmp / "lock.json"
        lock_path.write_text(json.dumps(lock))
        lock_sha = hashlib.sha256(lock_path.read_bytes()).hexdigest()

        raw_path = tmp / "raw.jsonl"
        _write_jsonl(raw_path, [
            _basic_header(lock_sha),
            _basic_source(candidate_count=2),
            _basic_candidate(bytes_b64="AAAA", lines=(10,)),
            _basic_candidate(bytes_b64="BBBB", lines=(10,)),
        ])

        ann_path = tmp / "ann.json"
        ann_path.write_text(json.dumps({"a.py": _basic_annotation(lines=(10,))}))

        out_path = tmp / "manifest.jsonl"
        summary = run(raw_path, ann_path, lock_path, out_path)
        assert summary["total_entries"] == 2
        assert summary["eligible_entries"] == 2
        assert summary["ineligible_entries"] == 0
        assert summary["manifest_sha256"] == hashlib.sha256(out_path.read_bytes()).hexdigest()
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
