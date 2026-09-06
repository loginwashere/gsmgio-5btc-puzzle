"""Self-tests for the Phase 478 fail-closed harvest runner, against
fabricated locks and results only. `verify_lock`'s git-blob checks are
exercised against a throwaway, fully synthetic git repository (created
and destroyed within each test) -- never the real project repository.
The runner's full end-to-end `run()` is not exercised here (it hardwires
the harvester module's own REPO_ROOT); that path's real-world validation
is the actual locked harvest run itself, the same relationship the
harvester's own tests have to `materialize_commit_snapshot`'s one
real-commit smoke test.
"""

import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path

import json

from phase478_run_harvest import (
    EXPECTED_ZERO_CANDIDATE_POLICY_PATHS,
    LockVerificationError,
    check_results,
    extract_locked_recipes,
    git_blob_sha,
    sha256_file,
    verify_lock,
    write_raw_capture_jsonl,
)


def _fake_classification(n_generator=23, n_structural=71, n_infra=2, missing_recipe_at=None):
    entries = []
    for i in range(n_generator):
        entry = {
            "path": f"tools/gsmg/gen_{i}.py", "blob_sha": "0" * 40,
            "category": "generator+oracle", "recipe": {"mode": "cli", "argv": []},
        }
        if missing_recipe_at == i:
            del entry["recipe"]
        entries.append(entry)
    for i in range(n_structural):
        entries.append({"path": f"tools/gsmg/struct_{i}.py", "blob_sha": "0" * 40, "category": "structural/no-oracle"})
    for i in range(n_infra):
        entries.append({"path": f"tools/gsmg/infra_{i}.py", "blob_sha": "0" * 40, "category": "infrastructure"})
    return entries


# ---------------------------------------------------------------------------
# extract_locked_recipes
# ---------------------------------------------------------------------------

def test_extract_locked_recipes_happy_path():
    lock = {"eligible_py_file_classification": _fake_classification()}
    recipes = extract_locked_recipes(lock, expected_count=23)
    assert len(recipes) == 23
    assert recipes["tools/gsmg/gen_0.py"] == {"mode": "cli", "argv": []}
    assert all(p.startswith("tools/gsmg/gen_") for p in recipes)


def test_extract_locked_recipes_wrong_count_raises():
    lock = {"eligible_py_file_classification": _fake_classification(n_generator=22)}
    try:
        extract_locked_recipes(lock, expected_count=23)
        assert False, "expected LockVerificationError"
    except LockVerificationError as exc:
        assert "22" in str(exc)


def test_extract_locked_recipes_missing_recipe_raises():
    lock = {"eligible_py_file_classification": _fake_classification(missing_recipe_at=5)}
    try:
        extract_locked_recipes(lock, expected_count=23)
        assert False, "expected LockVerificationError"
    except LockVerificationError as exc:
        assert "gen_5.py" in str(exc)


# ---------------------------------------------------------------------------
# check_results: the fail-closed acceptance gate
# ---------------------------------------------------------------------------

def _ok_result(path, candidates=None):
    if candidates is None:
        candidates = [{"bytes_b64": "aGk="}]
    return {"source_file": path, "status": "ok", "error": None, "candidates": candidates}


def test_check_results_happy_path_does_not_raise():
    recipes = {"a.py": {}, "b.py": {}}
    results = [_ok_result("a.py"), _ok_result("b.py")]
    check_results(recipes, results)  # must not raise


def test_check_results_missing_raises():
    recipes = {"a.py": {}, "b.py": {}}
    results = [_ok_result("a.py")]
    try:
        check_results(recipes, results)
        assert False
    except LockVerificationError as exc:
        assert "b.py" in str(exc)


def test_check_results_additional_raises():
    recipes = {"a.py": {}}
    results = [_ok_result("a.py"), _ok_result("c.py")]
    try:
        check_results(recipes, results)
        assert False
    except LockVerificationError as exc:
        assert "c.py" in str(exc)


def test_check_results_failed_status_raises():
    recipes = {"a.py": {}}
    results = [{"source_file": "a.py", "status": "harvest_failed", "error": "boom", "candidates": []}]
    try:
        check_results(recipes, results)
        assert False
    except LockVerificationError as exc:
        assert "a.py" in str(exc) and "boom" in str(exc)


def test_check_results_unauthorized_zero_candidates_raises():
    # No zero_candidate_policy on this recipe -- zero candidates here is a
    # broken recipe, not a quiet pass.
    recipes = {"a.py": {}}
    results = [_ok_result("a.py", candidates=[])]
    try:
        check_results(recipes, results)
        assert False
    except LockVerificationError as exc:
        assert "unauthorized zero-candidate" in str(exc)
        assert "a.py" in str(exc)


def test_check_results_duplicate_raises():
    recipes = {"a.py": {}}
    results = [_ok_result("a.py"), _ok_result("a.py")]
    try:
        check_results(recipes, results)
        assert False
    except LockVerificationError as exc:
        assert "duplicate" in str(exc)


# ---------------------------------------------------------------------------
# check_results: zero_candidate_policy (the digraphic_sweep.py /
# adjacent_diff_sweep.py exception -- a frozen, deterministic significance
# gate that legitimately does not clear on real data)
# ---------------------------------------------------------------------------

def test_check_results_authorized_conditional_zero_passes():
    recipes = {
        "a.py": {"zero_candidate_policy": {"allowed": True, "reason": "gate did not clear"}},
        "b.py": {},
    }
    results = [_ok_result("a.py", candidates=[]), _ok_result("b.py")]
    positive, authorized_zero = check_results(
        recipes, results, expected_zero_candidate_paths=frozenset({"a.py"}),
    )
    assert positive == ["b.py"]
    assert authorized_zero == ["a.py"]


def test_check_results_unauthorized_zero_still_fails_even_with_other_policies_present():
    # b.py has no policy grant of its own -- a.py being authorized does
    # not blanket-authorize every zero-candidate result in the batch.
    recipes = {
        "a.py": {"zero_candidate_policy": {"allowed": True, "reason": "gate did not clear"}},
        "b.py": {},
    }
    results = [_ok_result("a.py", candidates=[]), _ok_result("b.py", candidates=[])]
    try:
        check_results(recipes, results, expected_zero_candidate_paths=frozenset({"a.py"}))
        assert False
    except LockVerificationError as exc:
        message = str(exc)
        assert "b.py" in message
        assert "a.py" not in message, "a.py is authorized and must not appear as a violator"


def test_check_results_authorized_file_with_failed_status_still_fails():
    # zero_candidate_policy excuses zero CANDIDATES; it never excuses a
    # non-"ok" status. A crashed/timed-out run is fatal regardless.
    recipes = {
        "a.py": {"zero_candidate_policy": {"allowed": True, "reason": "gate did not clear"}},
    }
    results = [{"source_file": "a.py", "status": "harvest_failed", "error": "timeout", "candidates": []}]
    try:
        check_results(recipes, results, expected_zero_candidate_paths=frozenset({"a.py"}))
        assert False, "a failed status must be fatal even for a policy-authorized path"
    except LockVerificationError as exc:
        assert "a.py" in str(exc) and "timeout" in str(exc)


def test_check_results_extra_zero_policy_path_fails():
    # The lock grants the exception to a THIRD file the real deployment
    # never intended -- caught even before looking at any result.
    recipes = {
        "a.py": {"zero_candidate_policy": {"allowed": True, "reason": "x"}},
        "b.py": {"zero_candidate_policy": {"allowed": True, "reason": "x"}},
    }
    results = [_ok_result("a.py", candidates=[]), _ok_result("b.py", candidates=[])]
    try:
        check_results(recipes, results, expected_zero_candidate_paths=frozenset({"a.py"}))
        assert False
    except LockVerificationError as exc:
        assert "b.py" in str(exc)


def test_check_results_missing_zero_policy_path_fails():
    # The lock was supposed to grant the exception to a.py but doesn't --
    # caught even before looking at any result.
    recipes = {"a.py": {}, "b.py": {}}
    results = [_ok_result("a.py"), _ok_result("b.py")]
    try:
        check_results(recipes, results, expected_zero_candidate_paths=frozenset({"a.py"}))
        assert False
    except LockVerificationError as exc:
        assert "a.py" in str(exc)


def test_check_results_without_expected_set_skips_the_exact_set_check():
    # expected_zero_candidate_paths=None (the default) exercises only the
    # per-file authorized/unauthorized logic, useful for generic tests
    # that don't want to hardcode the real project's specific filenames.
    recipes = {"a.py": {"zero_candidate_policy": {"allowed": True, "reason": "x"}}}
    results = [_ok_result("a.py", candidates=[])]
    positive, authorized_zero = check_results(recipes, results)  # no expected_zero_candidate_paths
    assert positive == []
    assert authorized_zero == ["a.py"]


def test_expected_zero_candidate_policy_paths_is_exactly_five():
    # A frozen fact about THIS project's actual harvest, not a generic
    # property of check_results -- caught by direct execution of all 23
    # locked files, not assumed from the original 2.
    assert EXPECTED_ZERO_CANDIDATE_POLICY_PATHS == frozenset({
        "tools/gsmg/adjacent_diff_sweep.py",
        "tools/gsmg/digraphic_sweep.py",
        "tools/gsmg/native_prime_zeroing_sweep.py",
        "tools/gsmg/prefix_boundary_sweep.py",
        "tools/gsmg/faed_monoalphabetic_sweep.py",
    })


# ---------------------------------------------------------------------------
# check_results: reason_code partition (the two distinct, frozen reasons
# -- a real significance gate that closed vs. an escalation that never
# historically ran at all -- must not be interchangeable or mislabeled)
# ---------------------------------------------------------------------------

def test_check_results_reason_code_mismatch_raises():
    recipes = {
        "a.py": {"zero_candidate_policy": {"allowed": True, "reason_code": "gate_closed"}},
    }
    results = [_ok_result("a.py", candidates=[])]
    try:
        check_results(
            recipes, results,
            expected_zero_candidate_paths=frozenset({"a.py"}),
            expected_reason_codes={"a.py": "escalation_never_run"},  # wrong on purpose
        )
        assert False
    except LockVerificationError as exc:
        assert "a.py" in str(exc) and "reason_code" in str(exc)


def test_check_results_reason_code_correct_passes():
    recipes = {
        "a.py": {"zero_candidate_policy": {"allowed": True, "reason_code": "gate_closed"}},
        "b.py": {"zero_candidate_policy": {"allowed": True, "reason_code": "escalation_never_run"}},
    }
    results = [_ok_result("a.py", candidates=[]), _ok_result("b.py", candidates=[])]
    positive, authorized_zero = check_results(
        recipes, results,
        expected_zero_candidate_paths=frozenset({"a.py", "b.py"}),
        expected_reason_codes={"a.py": "gate_closed", "b.py": "escalation_never_run"},
    )
    assert authorized_zero == ["a.py", "b.py"]


# ---------------------------------------------------------------------------
# verify_lock: local file hashes
# ---------------------------------------------------------------------------

def test_verify_lock_local_file_hash_mismatch_raises():
    tmp = Path(tempfile.mkdtemp())
    try:
        (tmp / "protocol.md").write_text("protocol content")
        (tmp / "harvester.py").write_text("harvester content")
        (tmp / "driver.py").write_text("driver content")
        (tmp / "phase478_common.py").write_text("common content")
        lock = {
            "cutoff_commit": "unused",
            "protocol_path": "protocol.md",
            "protocol_sha256": "0" * 64,  # wrong on purpose
            "harvester_script": "harvester.py",
            "harvester_script_sha256": sha256_file(tmp / "harvester.py"),
            "driver_script": "driver.py",
            "driver_script_sha256": sha256_file(tmp / "driver.py"),
            "runner_script": "driver.py",
            "runner_script_sha256": sha256_file(tmp / "driver.py"),
            "phase478_common_sha256": sha256_file(tmp / "phase478_common.py"),
            "adapter_scripts": {},
            "eligible_py_file_classification": [],
            "reference_doc_files": [],
            "reference_findings_files": [],
        }
        try:
            verify_lock(lock, repo_root=tmp, adapter_dir=tmp)
            assert False, "expected LockVerificationError"
        except LockVerificationError as exc:
            assert "protocol.md" in str(exc)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_verify_lock_passes_when_every_hash_matches():
    tmp = Path(tempfile.mkdtemp())
    try:
        (tmp / "protocol.md").write_text("protocol content")
        (tmp / "harvester.py").write_text("harvester content")
        (tmp / "driver.py").write_text("driver content")
        (tmp / "phase478_common.py").write_text("common content")
        (tmp / "adapter_x.py").write_text("adapter content")
        lock = {
            "cutoff_commit": "unused",
            "protocol_path": "protocol.md",
            "protocol_sha256": sha256_file(tmp / "protocol.md"),
            "harvester_script": "harvester.py",
            "harvester_script_sha256": sha256_file(tmp / "harvester.py"),
            "driver_script": "driver.py",
            "driver_script_sha256": sha256_file(tmp / "driver.py"),
            "runner_script": "driver.py",
            "runner_script_sha256": sha256_file(tmp / "driver.py"),
            "phase478_common_sha256": sha256_file(tmp / "phase478_common.py"),
            "adapter_scripts": {"adapter_x.py": sha256_file(tmp / "adapter_x.py")},
            "eligible_py_file_classification": [],
            "reference_doc_files": [],
            "reference_findings_files": [],
        }
        verify_lock(lock, repo_root=tmp, adapter_dir=tmp)  # must not raise
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------------------
# verify_lock: git blob hashes, against a throwaway synthetic repo
# ---------------------------------------------------------------------------

def _make_throwaway_repo():
    # A disposable, isolated synthetic repository under /tmp, created and
    # destroyed solely to exercise verify_lock's git-blob checks -- never
    # the real project repository. commit.gpgsign is disabled LOCALLY, for
    # this throwaway repo only, so the test doesn't depend on interactive
    # pinentry; this has no bearing on any real commit anywhere.
    tmp = Path(tempfile.mkdtemp())
    subprocess.run(["git", "init", "-q"], cwd=tmp, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp, check=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=tmp, check=True)
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=tmp, check=True)
    (tmp / "tools").mkdir()
    (tmp / "tools" / "example.py").write_text("print('hello')\n")
    subprocess.run(["git", "add", "tools/example.py"], cwd=tmp, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=tmp, check=True)
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=tmp, capture_output=True, text=True, check=True,
    ).stdout.strip()
    return tmp, commit


def _minimal_lock_for_repo(commit, blob_entries):
    return {
        "cutoff_commit": commit,
        "protocol_path": "tools/example.py", "protocol_sha256": None,
        "harvester_script": "tools/example.py", "harvester_script_sha256": None,
        "driver_script": "tools/example.py", "driver_script_sha256": None,
        "runner_script": "tools/example.py", "runner_script_sha256": None,
        "phase478_common_sha256": None,
        "adapter_scripts": {},
        "eligible_py_file_classification": blob_entries,
        "reference_doc_files": [], "reference_findings_files": [],
    }


def test_verify_lock_git_blob_matches_real_commit():
    tmp, commit = _make_throwaway_repo()
    try:
        real_sha = git_blob_sha(commit, "tools/example.py", repo_root=tmp)
        lock = _minimal_lock_for_repo(commit, [{"path": "tools/example.py", "blob_sha": real_sha}])
        # Fill in the "local file" hashes so only the blob check is exercised.
        lock["protocol_sha256"] = sha256_file(tmp / "tools/example.py")
        lock["harvester_script_sha256"] = lock["protocol_sha256"]
        lock["driver_script_sha256"] = lock["protocol_sha256"]
        lock["runner_script_sha256"] = lock["protocol_sha256"]
        (tmp / "phase478_common.py").write_text("x")
        lock["phase478_common_sha256"] = sha256_file(tmp / "phase478_common.py")
        verify_lock(lock, repo_root=tmp, adapter_dir=tmp)  # must not raise
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_verify_lock_git_blob_mismatch_raises():
    tmp, commit = _make_throwaway_repo()
    try:
        lock = _minimal_lock_for_repo(commit, [{"path": "tools/example.py", "blob_sha": "f" * 40}])
        lock["protocol_sha256"] = sha256_file(tmp / "tools/example.py")
        lock["harvester_script_sha256"] = lock["protocol_sha256"]
        lock["driver_script_sha256"] = lock["protocol_sha256"]
        lock["runner_script_sha256"] = lock["protocol_sha256"]
        (tmp / "phase478_common.py").write_text("x")
        lock["phase478_common_sha256"] = sha256_file(tmp / "phase478_common.py")
        try:
            verify_lock(lock, repo_root=tmp, adapter_dir=tmp)
            assert False, "expected LockVerificationError"
        except LockVerificationError as exc:
            assert "tools/example.py" in str(exc)
            assert "blob hash mismatch" in str(exc)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------------------
# verify_lock: motivation-input hashes
# ---------------------------------------------------------------------------

def test_verify_lock_motivation_input_missing_file_raises():
    tmp, commit = _make_throwaway_repo()
    try:
        lock = _minimal_lock_for_repo(commit, [])
        lock["protocol_sha256"] = sha256_file(tmp / "tools/example.py")
        lock["harvester_script_sha256"] = lock["protocol_sha256"]
        lock["driver_script_sha256"] = lock["protocol_sha256"]
        lock["runner_script_sha256"] = lock["protocol_sha256"]
        (tmp / "phase478_common.py").write_text("x")
        lock["phase478_common_sha256"] = sha256_file(tmp / "phase478_common.py")
        lock["motivation_inputs"] = {
            "progress_md": {"path": str(tmp / "does_not_exist.md"), "sha256": "0" * 64},
        }
        try:
            verify_lock(lock, repo_root=tmp, adapter_dir=tmp)
            assert False, "expected LockVerificationError"
        except LockVerificationError as exc:
            assert "progress_md" in str(exc)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_verify_lock_motivation_input_hash_mismatch_raises():
    tmp, commit = _make_throwaway_repo()
    try:
        motivation_file = tmp / "motivation.md"
        motivation_file.write_text("some content")
        lock = _minimal_lock_for_repo(commit, [])
        lock["protocol_sha256"] = sha256_file(tmp / "tools/example.py")
        lock["harvester_script_sha256"] = lock["protocol_sha256"]
        lock["driver_script_sha256"] = lock["protocol_sha256"]
        lock["runner_script_sha256"] = lock["protocol_sha256"]
        (tmp / "phase478_common.py").write_text("x")
        lock["phase478_common_sha256"] = sha256_file(tmp / "phase478_common.py")
        lock["motivation_inputs"] = {
            "progress_md": {"path": str(motivation_file), "sha256": "0" * 64},
        }
        try:
            verify_lock(lock, repo_root=tmp, adapter_dir=tmp)
            assert False, "expected LockVerificationError"
        except LockVerificationError as exc:
            assert "progress_md" in str(exc)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_verify_lock_motivation_input_correct_hash_passes():
    tmp, commit = _make_throwaway_repo()
    try:
        motivation_file = tmp / "motivation.md"
        motivation_file.write_text("some content")
        lock = _minimal_lock_for_repo(commit, [])
        lock["protocol_sha256"] = sha256_file(tmp / "tools/example.py")
        lock["harvester_script_sha256"] = lock["protocol_sha256"]
        lock["driver_script_sha256"] = lock["protocol_sha256"]
        lock["runner_script_sha256"] = lock["protocol_sha256"]
        (tmp / "phase478_common.py").write_text("x")
        lock["phase478_common_sha256"] = sha256_file(tmp / "phase478_common.py")
        lock["motivation_inputs"] = {
            "progress_md": {"path": str(motivation_file), "sha256": sha256_file(motivation_file)},
        }
        verify_lock(lock, repo_root=tmp, adapter_dir=tmp)  # must not raise
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------------------
# write_raw_capture_jsonl: streaming, source-provenance-once, no digest
# ---------------------------------------------------------------------------

def _scan_for_forbidden_keys(obj, forbidden, path=""):
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in forbidden:
                hits.append(f"{path}.{k}")
            hits += _scan_for_forbidden_keys(v, forbidden, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits += _scan_for_forbidden_keys(v, forbidden, f"{path}[{i}]")
    return hits


def _read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def test_write_raw_capture_jsonl_never_contains_a_candidate_digest():
    tmp = Path(tempfile.mkdtemp())
    try:
        lock_path = tmp / "lock.json"
        lock_path.write_text('{"lock": true}')
        lock = {"cutoff_commit": "deadbeef"}
        results = [
            {
                "source_file": "a.py", "source_blob_sha": "0" * 40, "status": "ok", "error": None,
                "candidates": [{"bytes_b64": "aGk=", "call_sites": [{"entrypoint": "x"}]}],
            },
            {
                "source_file": "b.py", "source_blob_sha": "1" * 40, "status": "ok", "error": None,
                "candidates": [], "gate_witness": "p=0.9 -- not escalating",
            },
        ]
        output_path = tmp / "capture.jsonl"
        header = write_raw_capture_jsonl(lock, lock_path, results, output_path)

        records = _read_jsonl(output_path)
        hits = _scan_for_forbidden_keys(records, {"sha256", "digest", "equality_pattern"})
        assert hits == [], hits

        assert records[0]["record_type"] == "header"
        assert records[0]["discovery_lock_sha256"] == sha256_file(lock_path)
        assert records[0]["generator_oracle_count"] == 2
        assert records[0]["total_candidate_count"] == 1
        assert header == records[0]

        source_records = [r for r in records if r["record_type"] == "source"]
        assert {r["source_file"] for r in source_records} == {"a.py", "b.py"}
        b_record = next(r for r in source_records if r["source_file"] == "b.py")
        assert b_record["candidate_count"] == 0
        assert b_record["gate_witness"] == "p=0.9 -- not escalating"
        a_record = next(r for r in source_records if r["source_file"] == "a.py")
        assert "gate_witness" not in a_record

        candidate_records = [r for r in records if r["record_type"] == "candidate"]
        assert len(candidate_records) == 1
        assert candidate_records[0]["source_file"] == "a.py"
        assert candidate_records[0]["bytes_b64"] == "aGk="

        # Every line is independently valid, compact JSON (no indentation).
        with open(output_path, encoding="utf-8") as f:
            for line in f:
                assert "\n" not in line.strip()
                assert "  " not in line  # no pretty-printed indentation
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_write_raw_capture_jsonl_embeds_zero_candidate_policy_in_source_record():
    tmp = Path(tempfile.mkdtemp())
    try:
        lock_path = tmp / "lock.json"
        lock_path.write_text('{"lock": true}')
        lock = {"cutoff_commit": "deadbeef"}
        results = [
            {
                "source_file": "gated.py", "source_blob_sha": "0" * 40, "status": "ok", "error": None,
                "candidates": [], "gate_witness": "p=0.9 -- not escalating",
            },
        ]
        recipes = {
            "gated.py": {
                "zero_candidate_policy": {
                    "allowed": True, "reason_code": "gate_closed", "reason": "deterministic gate did not clear",
                },
            },
        }
        output_path = tmp / "capture.jsonl"
        write_raw_capture_jsonl(lock, lock_path, results, output_path, recipes=recipes)
        records = _read_jsonl(output_path)
        source_record = next(r for r in records if r["record_type"] == "source")
        assert source_record["zero_candidate_policy"] == {
            "allowed": True, "reason_code": "gate_closed", "reason": "deterministic gate did not clear",
        }
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_write_raw_capture_jsonl_is_deterministically_sorted():
    tmp = Path(tempfile.mkdtemp())
    try:
        lock_path = tmp / "lock.json"
        lock_path.write_text('{"lock": true}')
        lock = {"cutoff_commit": "deadbeef"}
        # Deliberately out of order.
        results = [
            {"source_file": "z.py", "source_blob_sha": "0" * 40, "status": "ok", "error": None,
             "candidates": [{"bytes_b64": "eg==", "call_sites": []}]},
            {"source_file": "a.py", "source_blob_sha": "1" * 40, "status": "ok", "error": None,
             "candidates": [{"bytes_b64": "yg==", "call_sites": []}, {"bytes_b64": "aA==", "call_sites": []}]},
        ]
        output_path = tmp / "capture.jsonl"
        write_raw_capture_jsonl(lock, lock_path, results, output_path)
        records = _read_jsonl(output_path)

        source_files_in_order = [r["source_file"] for r in records if r["record_type"] == "source"]
        assert source_files_in_order == ["a.py", "z.py"]

        a_candidates = [r["bytes_b64"] for r in records if r["record_type"] == "candidate" and r["source_file"] == "a.py"]
        assert a_candidates == sorted(a_candidates)
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
