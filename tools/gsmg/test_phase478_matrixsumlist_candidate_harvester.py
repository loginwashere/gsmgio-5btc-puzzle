"""Self-tests for the Phase 478 harvester, against fully SYNTHETIC snapshot
directories only -- per the protocol, the harvester must be proven correct
before it is ever pointed at a real, pinned-commit snapshot. No git access,
no real project file's content is read here except in the one dedicated
infrastructure smoke test at the bottom. Fixture snapshots ship their own
minimal stub `cb_common.py`, entirely decoupled from the real project's
`cb_common.py`.

Path convention matches the harvester: every target file lives at
`tools/gsmg/<name>.py` inside the synthetic snapshot ROOT, and is referred
to everywhere by that REPOSITORY-RELATIVE path -- mirroring exactly how
`materialize_commit_snapshot` lays out a real pinned-commit snapshot.
"""

import base64
import shutil
import tempfile
from pathlib import Path

from phase478_matrixsumlist_candidate_harvester import (
    DRIVER_PATH,
    run_driver_in_snapshot,
    dedupe_candidates,
)

STUB_CB_COMMON = b"""
def aes_try_open_bytes(passwd, kdf_variants=None, blobs=None):
    return []
def aes_try_open_stream_bytes(passwd, kdf_variants=None, blobs=None):
    return []
def aes_try_open_ecb_bytes(passwd, kdf_variants=None, blobs=None):
    return []
def aes_keywrap_try_open_bytes(passwd, kdf_variants=None, blobs=None):
    return []
def raw_key_try_open(key, blobs=None):
    return []
def aes_try_open(keystr, kdf_variants=None, blobs=None):
    return aes_try_open_bytes(keystr.encode(), kdf_variants, blobs)
def aes_try_open_ecb(keystr, kdf_variants=None, blobs=None):
    return aes_try_open_ecb_bytes(keystr.encode(), kdf_variants, blobs)
def aes_try_open_stream(keystr, kdf_variants=None, blobs=None):
    return aes_try_open_stream_bytes(keystr.encode(), kdf_variants, blobs)
def aes_keywrap_try_open(keystr, kdf_variants=None, blobs=None):
    return aes_keywrap_try_open_bytes(keystr.encode(), kdf_variants, blobs)
"""

TARGET = "tools/gsmg/target.py"


def _build_snapshot(gsmg_files: dict) -> Path:
    """A throwaway directory standing in for a materialized commit
    snapshot's REPOSITORY ROOT: `tools/gsmg/` holding the stub cb_common,
    the real harvest driver (copied, exactly as `materialize_commit_snapshot`
    does), and whatever fixture files the test needs, each keyed by its
    filename under `tools/gsmg/`."""
    root = Path(tempfile.mkdtemp(prefix="phase478_test_snapshot_"))
    gsmg = root / "tools" / "gsmg"
    gsmg.mkdir(parents=True)
    (gsmg / "cb_common.py").write_bytes(STUB_CB_COMMON)
    shutil.copy(DRIVER_PATH, gsmg / DRIVER_PATH.name)
    for name, content in gsmg_files.items():
        (gsmg / name).write_bytes(content)
    return root


def _run(gsmg_files: dict, target_name: str, recipe: dict, timeout_s: float = 10) -> dict:
    root = _build_snapshot(gsmg_files)
    try:
        return run_driver_in_snapshot(root, f"tools/gsmg/{target_name}", recipe, timeout_s=timeout_s)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _bytes_of(cand: dict) -> bytes:
    return base64.b64decode(cand["bytes_b64"])


# ---------------------------------------------------------------------------
# Basic interception
# ---------------------------------------------------------------------------

def test_simple_module_level_call():
    fixture = b"import cb_common\ncb_common.aes_try_open_bytes(b'hello_candidate')\n"
    result = _run({"target.py": fixture}, "target.py", {"mode": "cli", "argv": []})
    assert result["status"] == "ok", result
    cands = dedupe_candidates(result["candidates"])
    assert len(cands) == 1
    assert _bytes_of(cands[0]) == b"hello_candidate"
    assert "sha256" not in cands[0], "discovery-side manifest must never carry a candidate digest"


def test_main_guarded_call_is_captured_under_cli_mode():
    fixture = (
        b"import cb_common\n"
        b"def main():\n"
        b"    cb_common.aes_try_open_bytes(b'guarded_candidate')\n"
        b"if __name__ == '__main__':\n"
        b"    main()\n"
    )
    result = _run({"target.py": fixture}, "target.py", {"mode": "cli", "argv": []})
    assert result["status"] == "ok", result
    cands = dedupe_candidates(result["candidates"])
    assert len(cands) == 1
    assert _bytes_of(cands[0]) == b"guarded_candidate"


def test_str_wrapper_forwards_to_bytes_entrypoint():
    fixture = b"import cb_common\ncb_common.aes_try_open('stringform')\n"
    result = _run({"target.py": fixture}, "target.py", {"mode": "cli", "argv": []})
    assert result["status"] == "ok", result
    cands = dedupe_candidates(result["candidates"])
    assert len(cands) == 1
    assert _bytes_of(cands[0]) == b"stringform"


def test_wrapper_call_site_records_originating_target_frame_not_cb_common():
    # cb_common.aes_try_open("wrapped") forwards, inside cb_common.py, to
    # the patched aes_try_open_bytes -- the immediate caller frame is
    # therefore cb_common.py's own wrapper, not the target script. The
    # recorded provenance must walk past that to the real originating
    # frame in the target file.
    fixture = (
        b"import cb_common\n"
        b"def submit_via_wrapper():\n"
        b"    cb_common.aes_try_open('wrapped')\n"
        b"submit_via_wrapper()\n"
    )
    result = _run({"target.py": fixture}, "target.py", {"mode": "cli", "argv": []})
    assert result["status"] == "ok", result
    cands = dedupe_candidates(result["candidates"])
    assert len(cands) == 1
    assert _bytes_of(cands[0]) == b"wrapped"
    site = cands[0]["call_sites"][0]
    assert site["caller_function"] == "submit_via_wrapper"
    assert site["caller_file"].endswith("target.py")
    assert "cb_common.py" not in site["caller_file"], (
        f"provenance must not point at cb_common.py's own wrapper frame: {site}"
    )


def test_same_bytes_from_distinct_call_sites_dedupe_to_one_candidate_with_all_sites():
    # KDF/cipher fan-out happens INSIDE cb_common's own oracle functions
    # (kdf_variants iterated in the function body), invisible to the
    # recorder -- a calling script submits one candidate material once per
    # call site, not once per KDF variant. The realistic dedup case is
    # therefore two or more genuinely distinct call sites (different
    # functions/lines) that happen to submit the identical bytes, which
    # must collapse to one candidate while preserving every distinct site.
    fixture = (
        b"import cb_common\n"
        b"def path_one():\n"
        b"    cb_common.aes_try_open_bytes(b'same_material_multi_site')\n"
        b"def path_two():\n"
        b"    cb_common.aes_try_open_bytes(b'same_material_multi_site')\n"
        b"path_one()\n"
        b"path_two()\n"
        b"cb_common.aes_try_open_bytes(b'same_material_multi_site')\n"  # module-level, third site
    )
    result = _run({"target.py": fixture}, "target.py", {"mode": "cli", "argv": []})
    assert result["status"] == "ok", result
    cands = dedupe_candidates(result["candidates"])
    assert len(cands) == 1, "identical bytes from distinct call sites must collapse to one entry"
    assert _bytes_of(cands[0]) == b"same_material_multi_site"
    functions = {s["caller_function"] for s in cands[0]["call_sites"]}
    assert functions == {"path_one", "path_two", "<module>"}
    assert len(cands[0]["call_sites"]) == 3


def test_repeated_identical_call_site_does_not_inflate_call_sites():
    # The SAME source line invoked N times (e.g. inside a real loop over
    # KDF variants a script might -- unusually -- drive itself) is one
    # call site, not N: call_sites records distinct locations, not a
    # per-invocation tally.
    fixture = (
        b"import cb_common\n"
        b"for _ in range(6):\n"
        b"    cb_common.aes_try_open_bytes(b'same_material_same_line')\n"
    )
    result = _run({"target.py": fixture}, "target.py", {"mode": "cli", "argv": []})
    assert result["status"] == "ok", result
    cands = dedupe_candidates(result["candidates"])
    assert len(cands) == 1
    assert len(cands[0]["call_sites"]) == 1
    assert _bytes_of(cands[0]) == b"same_material_same_line"


def test_multiple_entrypoints_each_captured():
    fixture = (
        b"import cb_common\n"
        b"cb_common.aes_try_open_bytes(b'cbc_candidate')\n"
        b"cb_common.raw_key_try_open(b'raw_key_candidate')\n"
        b"cb_common.aes_keywrap_try_open_bytes(b'wrap_candidate')\n"
        b"cb_common.aes_try_open_stream_bytes(b'stream_candidate')\n"
        b"cb_common.aes_try_open_ecb_bytes(b'ecb_candidate')\n"
    )
    result = _run({"target.py": fixture}, "target.py", {"mode": "cli", "argv": []})
    assert result["status"] == "ok", result
    cands = dedupe_candidates(result["candidates"])
    got = {_bytes_of(c) for c in cands}
    assert got == {
        b"cbc_candidate", b"raw_key_candidate", b"wrap_candidate",
        b"stream_candidate", b"ecb_candidate",
    }


def test_oracle_calls_from_forked_worker_processes_are_captured():
    # The real bug this proves fixed: an in-memory RECORDED list is NOT
    # shared across a fork -- a worker's appends land in its own
    # copy-on-write memory and vanish when it exits, even though
    # cb_common's patch (applied before any fork) is correctly inherited
    # and the call genuinely happens. Found by running a real locked file
    # (matrix_instruction_sweep.py: ProcessPoolExecutor, status "ok",
    # 0 candidates) before this fix existed.
    fixture = (
        b"import cb_common\n"
        b"from concurrent.futures import ProcessPoolExecutor\n"
        b"def _worker(i):\n"
        b"    cb_common.aes_try_open_bytes(f'candidate_from_worker_{i}'.encode())\n"
        b"    return i\n"
        b"def main():\n"
        b"    with ProcessPoolExecutor(max_workers=2) as ex:\n"
        b"        list(ex.map(_worker, range(4)))\n"
        b"if __name__ == '__main__':\n"
        b"    main()\n"
    )
    result = _run({"target.py": fixture}, "target.py", {"mode": "cli", "argv": []}, timeout_s=30)
    assert result["status"] == "ok", result
    cands = dedupe_candidates(result["candidates"])
    got = {_bytes_of(c) for c in cands}
    assert got == {f"candidate_from_worker_{i}".encode() for i in range(4)}


def test_structural_only_yields_zero_candidates():
    fixture = b"x = 'matrixsumlist structural analysis, no oracle call here'\nassert len(x) > 0\n"
    result = _run({"target.py": fixture}, "target.py", {"mode": "cli", "argv": []})
    assert result["status"] == "ok", result
    assert dedupe_candidates(result["candidates"]) == []


# ---------------------------------------------------------------------------
# Exit-status discipline (correction #4)
# ---------------------------------------------------------------------------

def test_exception_is_harvest_failed_and_prior_candidates_survive():
    fixture = (
        b"import cb_common\n"
        b"cb_common.aes_try_open_bytes(b'captured_before_crash')\n"
        b"raise RuntimeError('boom')\n"
    )
    result = _run({"target.py": fixture}, "target.py", {"mode": "cli", "argv": []})
    assert result["status"] == "harvest_failed", result
    assert "RuntimeError" in result["error"]
    cands = dedupe_candidates(result["candidates"])
    assert len(cands) == 1
    assert _bytes_of(cands[0]) == b"captured_before_crash"


def test_system_exit_zero_and_bare_are_ok():
    for label, tail in (("zero", b"sys.exit(0)\n"), ("bare", b"sys.exit()\n")):
        fixture = (
            b"import sys, cb_common\n"
            b"cb_common.aes_try_open_bytes(b'before_exit_" + label.encode() + b"')\n"
            + tail
        )
        result = _run({"target.py": fixture}, "target.py", {"mode": "cli", "argv": []})
        assert result["status"] == "ok", (label, result)
        cands = dedupe_candidates(result["candidates"])
        assert len(cands) == 1
        assert _bytes_of(cands[0]) == f"before_exit_{label}".encode()


def test_system_exit_nonzero_or_message_is_harvest_failed():
    cases = [
        (b"sys.exit(1)\n", "SystemExit(1)"),
        (b"sys.exit(2)\n", "SystemExit(2)"),
        (b"sys.exit('some error message')\n", "SystemExit('some error message')"),
    ]
    for tail, expected_error_fragment in cases:
        fixture = (
            b"import sys, cb_common\n"
            b"cb_common.aes_try_open_bytes(b'before_bad_exit')\n"
            + tail
        )
        result = _run({"target.py": fixture}, "target.py", {"mode": "cli", "argv": []})
        assert result["status"] == "harvest_failed", (tail, result)
        assert expected_error_fragment in result["error"], (tail, result["error"])
        cands = dedupe_candidates(result["candidates"])
        assert len(cands) == 1
        assert _bytes_of(cands[0]) == b"before_bad_exit"


# ---------------------------------------------------------------------------
# argparse gating and invocation recipes (correction #3)
# ---------------------------------------------------------------------------

ARGPARSE_GATED_FIXTURE = (
    b"import argparse\n"
    b"import cb_common\n"
    b"def main():\n"
    b"    parser = argparse.ArgumentParser()\n"
    b"    parser.add_argument('--oracle', action='store_true', required=True)\n"
    b"    parser.parse_args()\n"
    b"    cb_common.aes_try_open_bytes(b'argparse_gated_candidate')\n"
    b"if __name__ == '__main__':\n"
    b"    main()\n"
)


def test_argparse_gated_script_reaches_oracle_with_correct_argv():
    result = _run(
        {"target.py": ARGPARSE_GATED_FIXTURE}, "target.py",
        {"mode": "cli", "argv": ["--oracle"]},
    )
    assert result["status"] == "ok", result
    cands = dedupe_candidates(result["candidates"])
    assert len(cands) == 1
    assert _bytes_of(cands[0]) == b"argparse_gated_candidate"


def test_argparse_gated_script_without_required_flag_is_harvest_failed_not_zero_candidates():
    result = _run({"target.py": ARGPARSE_GATED_FIXTURE}, "target.py", {"mode": "cli", "argv": []})
    assert result["status"] == "harvest_failed", (
        "a missing required --oracle flag must be reported as a failed run, "
        "never as a spurious zero-candidate success"
    )
    assert "SystemExit(2)" in result["error"], result["error"]
    assert dedupe_candidates(result["candidates"]) == []


CALL_MODE_BYPASS_FIXTURE = (
    b"import argparse\n"
    b"import cb_common\n"
    b"def run_oracle_calls():\n"
    b"    cb_common.aes_try_open_bytes(b'call_mode_candidate')\n"
    b"def main():\n"
    b"    parser = argparse.ArgumentParser()\n"
    b"    parser.add_argument('--oracle', action='store_true', required=True)\n"
    b"    parser.parse_args()\n"
    b"    run_oracle_calls()\n"
    b"if __name__ == '__main__':\n"
    b"    main()\n"
)


def test_call_mode_bypasses_argparse_via_entry_function():
    result = _run(
        {"target.py": CALL_MODE_BYPASS_FIXTURE}, "target.py",
        {"mode": "call", "entry_function": "run_oracle_calls"},
    )
    assert result["status"] == "ok", result
    cands = dedupe_candidates(result["candidates"])
    assert len(cands) == 1
    assert _bytes_of(cands[0]) == b"call_mode_candidate"


# ---------------------------------------------------------------------------
# Isolation (correction #2): sibling imports must resolve against the
# SNAPSHOT, never the live tools/gsmg the tests themselves run from.
# ---------------------------------------------------------------------------

def test_sibling_import_resolves_against_the_snapshot_not_the_live_tree():
    # The real project's tools/gsmg/data.py defines DBBI/FAED but has no
    # `MARKER` attribute. If isolation ever leaked to the live tree (the
    # exact failure mode corrected here), this import would raise
    # ImportError instead of succeeding with the synthetic value.
    fixture = (
        b"import cb_common\n"
        b"from data import MARKER\n"
        b"cb_common.aes_try_open_bytes(MARKER.encode())\n"
    )
    result = _run(
        {"target.py": fixture, "data.py": b"MARKER = 'pinned_snapshot_value'\n"},
        "target.py", {"mode": "cli", "argv": []},
    )
    assert result["status"] == "ok", result
    cands = dedupe_candidates(result["candidates"])
    assert len(cands) == 1
    assert _bytes_of(cands[0]) == b"pinned_snapshot_value"


# ---------------------------------------------------------------------------
# Path mapping (correction #1): a repository-relative source_file must
# resolve to exactly one location under the snapshot root, never doubled
# onto an already-tools/gsmg-rooted directory.
# ---------------------------------------------------------------------------

def test_repo_relative_path_resolves_without_doubling_tools_gsmg():
    fixture = b"import cb_common\ncb_common.aes_try_open_bytes(b'path_mapping_candidate')\n"
    root = _build_snapshot({"target.py": fixture})
    try:
        # The bug this guards against: joining a repo-relative path
        # ("tools/gsmg/target.py") onto a snapshot root that was ALREADY
        # `<root>/tools/gsmg` produces `<root>/tools/gsmg/tools/gsmg/target.py`,
        # which does not exist -- confirm that path is absent...
        doubled = root / "tools" / "gsmg" / "tools" / "gsmg" / "target.py"
        assert not doubled.exists()
        # ...and that resolving the correct repo-relative path against the
        # snapshot ROOT succeeds and reaches the real fixture.
        result = run_driver_in_snapshot(root, "tools/gsmg/target.py", {"mode": "cli", "argv": []})
        assert result["status"] == "ok", result
        cands = dedupe_candidates(result["candidates"])
        assert len(cands) == 1
        assert _bytes_of(cands[0]) == b"path_mapping_candidate"
    finally:
        shutil.rmtree(root, ignore_errors=True)


# ---------------------------------------------------------------------------
# Call-site provenance
# ---------------------------------------------------------------------------

def test_call_site_captures_caller_file_line_function():
    fixture = (
        b"import cb_common\n"
        b"def submit():\n"
        b"    cb_common.aes_try_open_bytes(b'located_candidate')\n"
        b"submit()\n"
    )
    result = _run({"target.py": fixture}, "target.py", {"mode": "cli", "argv": []})
    assert result["status"] == "ok", result
    cands = dedupe_candidates(result["candidates"])
    assert len(cands) == 1
    site = cands[0]["call_sites"][0]
    assert site["caller_function"] == "submit"
    assert site["caller_file"].endswith("target.py")
    assert site["entrypoint"] == "aes_try_open_bytes"
    assert isinstance(site["caller_line"], int) and site["caller_line"] > 0


def test_no_real_cryptography_performed():
    fixture = b"import cb_common\ncb_common.aes_try_open_bytes(b'noop_check')\n"
    result = _run({"target.py": fixture}, "target.py", {"mode": "cli", "argv": []}, timeout_s=5)
    assert result["status"] == "ok"


# ---------------------------------------------------------------------------
# Per-recipe timeout_s: the recipe schema has always named this field;
# harvest_file previously never read it, silently applying one shared
# batch-wide timeout regardless of what a locked recipe itself specified.
# ---------------------------------------------------------------------------

def test_harvest_file_honors_recipe_level_timeout_override():
    from phase478_matrixsumlist_candidate_harvester import harvest_file

    sleepy_fixture = (
        b"import time, cb_common\n"
        b"time.sleep(2)\n"
        b"cb_common.aes_try_open_bytes(b'slow_candidate')\n"
    )
    # Named tools/gsmg/data.py purely so git_blob_sha (which always looks
    # up the REAL repository, independent of this synthetic snapshot's
    # content) has a real blob to resolve; harvest_file never cross-checks
    # that blob's content against what it actually executes -- that
    # cross-check is the discovery lock's job (verify_lock), not
    # harvest_file's.
    root = _build_snapshot({"data.py": sleepy_fixture})
    try:
        too_short = harvest_file(
            root, "HEAD", "tools/gsmg/data.py",
            {"mode": "cli", "argv": [], "timeout_s": 0.5},
        )
        assert too_short["status"] == "harvest_failed"
        assert too_short["error"] == "timeout"

        long_enough = harvest_file(
            root, "HEAD", "tools/gsmg/data.py",
            {"mode": "cli", "argv": [], "timeout_s": 10},
        )
        assert long_enough["status"] == "ok", long_enough
        assert len(long_enough["candidates"]) == 1
        assert _bytes_of(long_enough["candidates"][0]) == b"slow_candidate"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_timeout_does_not_leak_the_capture_file():
    # The bug this guards against: the capture file's path used to be
    # chosen and owned by the DRIVER subprocess itself, which is SIGKILLed
    # on a timeout and never reaches its own cleanup code -- leaking a
    # temp file per timeout. Ownership now belongs to this function's own
    # try/finally, which always runs regardless of how the subprocess exits.
    import glob
    import tempfile as _tempfile

    sleepy_fixture = b"import time, cb_common\ntime.sleep(5)\n"
    root = _build_snapshot({"target.py": sleepy_fixture})
    try:
        tmp_dir = _tempfile.gettempdir()
        before = set(glob.glob(f"{tmp_dir}/phase478_capture_*"))
        result = run_driver_in_snapshot(root, "tools/gsmg/target.py", {"mode": "cli", "argv": []}, timeout_s=0.5)
        assert result["status"] == "harvest_failed" and result["error"] == "timeout"
        after = set(glob.glob(f"{tmp_dir}/phase478_capture_*"))
        assert after == before, f"leaked capture file(s): {after - before}"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_harvest_file_falls_back_to_default_timeout_when_recipe_has_none():
    from phase478_matrixsumlist_candidate_harvester import harvest_file

    sleepy_fixture = b"import time, cb_common\ntime.sleep(2)\ncb_common.aes_try_open_bytes(b'x')\n"
    root = _build_snapshot({"data.py": sleepy_fixture})
    try:
        result = harvest_file(
            root, "HEAD", "tools/gsmg/data.py",
            {"mode": "cli", "argv": []},  # no timeout_s in the recipe
            default_timeout_s=0.5,
        )
        assert result["status"] == "harvest_failed"
        assert result["error"] == "timeout"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_gate_witness_captured_only_when_recipe_carries_zero_candidate_policy():
    from phase478_matrixsumlist_candidate_harvester import harvest_file

    # A fixture shaped like the real gated files: it prints its own
    # diagnostic/gate line, then legitimately submits nothing.
    gated_fixture = (
        b"print('Not statistically exceptional (p=0.87421 >= 0.05) -- not escalating')\n"
    )
    root = _build_snapshot({"data.py": gated_fixture})
    try:
        with_policy = harvest_file(
            root, "HEAD", "tools/gsmg/data.py",
            {
                "mode": "cli", "argv": [],
                "zero_candidate_policy": {
                    "allowed": True,
                    "reason": "historical deterministic significance gate did not clear on real data",
                },
            },
        )
        assert with_policy["status"] == "ok"
        assert with_policy["candidates"] == []
        assert "gate_witness" in with_policy
        assert "0.87421" in with_policy["gate_witness"]

        without_policy = harvest_file(
            root, "HEAD", "tools/gsmg/data.py", {"mode": "cli", "argv": []},
        )
        assert without_policy["status"] == "ok"
        assert "gate_witness" not in without_policy
    finally:
        shutil.rmtree(root, ignore_errors=True)


# ---------------------------------------------------------------------------
# Infrastructure smoke test for the real git-archive extraction mechanism
# itself. This does NOT run the driver against any real candidate-
# generating file (that stays off-limits until after classification and
# the discovery lock) -- it only proves `materialize_commit_snapshot`
# correctly extracts the pinned commit's repository root, byte-for-byte,
# and cleans up after itself.
# ---------------------------------------------------------------------------

def test_materialize_commit_snapshot_extracts_real_pinned_commit():
    import subprocess
    from phase478_matrixsumlist_candidate_harvester import (
        materialize_commit_snapshot, REPO_ROOT,
    )

    commit = "64f8063939d1d4d89402b87f88aa22b8fb956a7b"
    expected = subprocess.run(
        ["git", "show", f"{commit}:tools/gsmg/data.py"],
        cwd=REPO_ROOT, capture_output=True, check=True,
    ).stdout

    snapshot_path_holder = {}
    with materialize_commit_snapshot(commit) as snapshot_root:
        snapshot_path_holder["path"] = snapshot_root
        gsmg = snapshot_root / "tools" / "gsmg"
        assert (gsmg / "data.py").is_file()
        assert (gsmg / "data.py").read_bytes() == expected
        assert (gsmg / "cb_common.py").is_file()
        assert (gsmg / "phase478_harvest_driver.py").is_file(), (
            "the driver must be copied into the snapshot for sys.path correctness"
        )
        assert (gsmg / "phase478_adapter_cosmic_raw_digest.py").is_file(), (
            "every registered adapter must be copied into the snapshot too"
        )
        # Phase 478's own files must not exist at this pre-Phase-478 commit.
        assert not (gsmg / "phase478_common.py").is_file()
        # The yielded path is the REPOSITORY ROOT, not tools/gsmg itself.
        assert (snapshot_root / "doc").is_dir()

    # Cleaned up on context exit.
    assert not snapshot_path_holder["path"].exists()


# ---------------------------------------------------------------------------
# Dependency-remap adapter (attr_overrides): covers
# matrixsumlist_title_and_iteration_audit.py's unpinned
# ARCHITECT_PDF_PATH -- a hardcoded absolute path outside the repository --
# by substituting the pinned snapshot's own tracked, byte-identical
# equivalent before the target's entry function runs.
# ---------------------------------------------------------------------------

ATTR_OVERRIDE_FIXTURE = (
    b"import argparse\n"
    b"from pathlib import Path\n"
    b"import cb_common\n"
    b"SOME_EXTERNAL_PATH = Path('/this/path/does/not/exist/on/purpose.txt')\n"
    b"def main():\n"
    b"    parser = argparse.ArgumentParser()\n"
    b"    parser.add_argument('--go', action='store_true', required=True)\n"
    b"    parser.parse_args()\n"
    b"    content = SOME_EXTERNAL_PATH.read_text()\n"
    b"    cb_common.aes_try_open_bytes(content.encode())\n"
    b"if __name__ == '__main__':\n"
    b"    main()\n"
)


def test_attr_overrides_remaps_dependency_to_pinned_snapshot_file():
    root = _build_snapshot({"target.py": ATTR_OVERRIDE_FIXTURE})
    try:
        pinned_dependency_dir = root / "wordlists" / "matrix"
        pinned_dependency_dir.mkdir(parents=True)
        (pinned_dependency_dir / "pinned_equivalent.txt").write_text("pinned_snapshot_content")

        result = run_driver_in_snapshot(
            root, "tools/gsmg/target.py",
            {
                "mode": "call", "entry_function": "main", "argv": ["--go"],
                "attr_overrides": {"SOME_EXTERNAL_PATH": "wordlists/matrix/pinned_equivalent.txt"},
            },
        )
        assert result["status"] == "ok", result
        cands = dedupe_candidates(result["candidates"])
        assert len(cands) == 1
        assert _bytes_of(cands[0]) == b"pinned_snapshot_content"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_without_attr_overrides_the_unpinned_path_fails_closed():
    # Confirms the fixture genuinely depends on the override -- absent it,
    # the nonexistent external path raises, proving the override (not
    # some other path) is what made the previous test pass.
    root = _build_snapshot({"target.py": ATTR_OVERRIDE_FIXTURE})
    try:
        result = run_driver_in_snapshot(
            root, "tools/gsmg/target.py",
            {"mode": "call", "entry_function": "main", "argv": ["--go"]},
        )
        assert result["status"] == "harvest_failed", result
        assert "FileNotFoundError" in result["error"]
    finally:
        shutil.rmtree(root, ignore_errors=True)


# ---------------------------------------------------------------------------
# Dependency-remap adapter (dependency_overrides): covers the case
# attr_overrides CANNOT -- a path captured as a function's own DEFAULT
# ARGUMENT VALUE (baked in at definition time, during runpy.run_path,
# before any post-hoc override could possibly run), imported from a
# SEPARATE dependency module rather than defined in the target itself.
# This is exactly salph_cosmic_phase341_eligibility_audit.py's shape:
# `from page_structure_audit import DEFAULT_HTML` then
# `def literal_segments(html_path=DEFAULT_HTML): ...`.
# ---------------------------------------------------------------------------

DEPENDENCY_MODULE_FIXTURE = (
    b"from pathlib import Path\n"
    b"SOME_PATH = Path('/this/path/does/not/exist/on/purpose.txt')\n"
)

BAKED_IN_DEFAULT_FIXTURE = (
    b"import cb_common\n"
    b"from dep_module import SOME_PATH\n"
    b"def read_it(path=SOME_PATH):\n"
    b"    return path.read_text()\n"
    b"def main():\n"
    b"    cb_common.aes_try_open_bytes(read_it().encode())\n"
    b"if __name__ == '__main__':\n"
    b"    main()\n"
)


def test_attr_overrides_cannot_fix_a_baked_in_default_argument():
    # Establishes the failure mode dependency_overrides exists to fix:
    # attr_overrides patches the TARGET's own __globals__, which is
    # irrelevant here since `path=SOME_PATH` was already evaluated and
    # stored in read_it.__defaults__ during runpy.run_path, before any
    # override step runs.
    root = _build_snapshot({
        "target.py": BAKED_IN_DEFAULT_FIXTURE,
        "dep_module.py": DEPENDENCY_MODULE_FIXTURE,
    })
    try:
        result = run_driver_in_snapshot(
            root, "tools/gsmg/target.py",
            {
                "mode": "call", "entry_function": "main",
                "attr_overrides": {"SOME_PATH": "wordlists/pinned.txt"},
            },
        )
        assert result["status"] == "harvest_failed", (
            "attr_overrides is expected to be INEFFECTIVE against a "
            "baked-in default argument -- if this starts passing, the "
            "fixture or the mechanism changed and this test's premise "
            "needs re-checking"
        )
        assert "FileNotFoundError" in result["error"]
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dependency_overrides_fixes_the_baked_in_default_argument():
    root = _build_snapshot({
        "target.py": BAKED_IN_DEFAULT_FIXTURE,
        "dep_module.py": DEPENDENCY_MODULE_FIXTURE,
    })
    try:
        pinned_dir = root / "wordlists"
        pinned_dir.mkdir(parents=True)
        (pinned_dir / "pinned.txt").write_text("pinned_via_dependency_override")

        result = run_driver_in_snapshot(
            root, "tools/gsmg/target.py",
            {
                "mode": "cli", "argv": [],
                "dependency_overrides": {"dep_module": {"SOME_PATH": "wordlists/pinned.txt"}},
            },
        )
        assert result["status"] == "ok", result
        cands = dedupe_candidates(result["candidates"])
        assert len(cands) == 1
        assert _bytes_of(cands[0]) == b"pinned_via_dependency_override"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dependency_overrides_works_under_call_mode_too():
    root = _build_snapshot({
        "target.py": BAKED_IN_DEFAULT_FIXTURE,
        "dep_module.py": DEPENDENCY_MODULE_FIXTURE,
    })
    try:
        pinned_dir = root / "wordlists"
        pinned_dir.mkdir(parents=True)
        (pinned_dir / "pinned.txt").write_text("pinned_via_dependency_override_call_mode")

        result = run_driver_in_snapshot(
            root, "tools/gsmg/target.py",
            {
                "mode": "call", "entry_function": "main",
                "dependency_overrides": {"dep_module": {"SOME_PATH": "wordlists/pinned.txt"}},
            },
        )
        assert result["status"] == "ok", result
        cands = dedupe_candidates(result["candidates"])
        assert len(cands) == 1
        assert _bytes_of(cands[0]) == b"pinned_via_dependency_override_call_mode"
    finally:
        shutil.rmtree(root, ignore_errors=True)


# ---------------------------------------------------------------------------
# cosmic_raw_digest_checkpoint_audit.py's dedicated local-decrypt-boundary
# adapter. Exercised against a minimal SYNTHETIC stand-in matching the
# real file's relevant surface (xor_sha256_digests, decrypt, TOKENS,
# P5/P6/P7_CANDIDATES, published_uniqueness_family_report), not the real
# project file -- consistent with every other test in this module.
# ---------------------------------------------------------------------------

COSMIC_ADAPTER_FIXTURE = b"""
import hashlib

# TOKENS' own trailing (p5, p6, p7) = ("p5a", "p6a", "p7a") deliberately
# matches one member of the P5/P6/P7 uniqueness family below, mirroring
# the real file (whose default trailing tokens are themselves members of
# its own P5/P6/P7_CANDIDATES lists) -- so the default raw32 form and one
# family member are expected to dedupe into the same candidate.
TOKENS = ("alpha", "beta", "gamma", "delta", "p5a", "p6a", "p7a")
P5_CANDIDATES = ("p5a", "p5b")
P6_CANDIDATES = ("p6a", "p6b")
P7_CANDIDATES = ("p7a", "p7b")


def xor_sha256_digests(tokens=TOKENS):
    result = bytes(hashlib.sha256(tokens[0].encode()).digest_size)
    for token in tokens:
        digest = hashlib.sha256(token.encode()).digest()
        result = bytes(l ^ r for l, r in zip(result, digest))
    return result


def decrypt(password, digest_name):
    # Real implementation runs AES via `cryptography`; the adapter under
    # test replaces this entirely before this body ever runs.
    raise AssertionError("real decrypt() must never execute under the adapter")


def published_uniqueness_family_report():
    fixed = TOKENS[:4]
    hits = []
    attempts = 0
    for p5 in P5_CANDIDATES:
        for p6 in P6_CANDIDATES:
            for p7 in P7_CANDIDATES:
                attempts += 1
                tokens = fixed + (p5, p6, p7)
                result = decrypt(xor_sha256_digests(tokens), "md5")
                if result["valid_padding"]:
                    hits.append((p5, p6, p7))
    return {"attempts": attempts, "hits": tuple(hits)}
"""


def _build_cosmic_adapter_snapshot() -> Path:
    from phase478_matrixsumlist_candidate_harvester import ADAPTER_PATHS

    root = _build_snapshot({"target.py": COSMIC_ADAPTER_FIXTURE})
    for adapter_path in ADAPTER_PATHS:
        shutil.copy(adapter_path, root / "tools" / "gsmg" / adapter_path.name)
    return root


def test_cosmic_raw_digest_adapter_captures_default_forms_and_full_family():
    root = _build_cosmic_adapter_snapshot()
    try:
        result = run_driver_in_snapshot(
            root, "tools/gsmg/target.py",
            {"driver": "phase478_adapter_cosmic_raw_digest.py"},
        )
        assert result["status"] == "ok", result
        cands = dedupe_candidates(result["candidates"])

        # 2 default forms (raw32, hex64) + 2x2x2=8 uniqueness-family
        # members. One family member (p5a/p6a/p7a, the fixture's own
        # analogue of the real file's default p5/p6/p7 slot) reproduces
        # the exact same raw XOR as the default raw32 form, so it must
        # dedupe into that candidate rather than add a 3rd distinct one.
        assert len(cands) == 9, [c["bytes_b64"] for c in cands]

        digest_names_seen = {
            site["digest_name"]
            for c in cands for site in c["call_sites"]
        }
        assert digest_names_seen == {"md5", "sha256"}

        caller_functions_seen = {
            site["caller_function"]
            for c in cands for site in c["call_sites"]
        }
        assert "_submit_default_forms" in caller_functions_seen
        assert "published_uniqueness_family_report" in caller_functions_seen

        entrypoints_seen = {
            site["entrypoint"]
            for c in cands for site in c["call_sites"]
        }
        assert entrypoints_seen == {"cosmic_raw_digest_checkpoint_audit.decrypt"}
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cosmic_raw_digest_adapter_never_raises_the_real_decrypt():
    # COSMIC_ADAPTER_FIXTURE's own decrypt() raises AssertionError if ever
    # actually called -- a status of "ok" (not "harvest_failed") is
    # itself proof the adapter's stub, not the fixture's real body, ran
    # for every one of the 2 + 8 calls.
    root = _build_cosmic_adapter_snapshot()
    try:
        result = run_driver_in_snapshot(
            root, "tools/gsmg/target.py",
            {"driver": "phase478_adapter_cosmic_raw_digest.py"},
        )
        assert result["status"] == "ok", result
        assert result["error"] is None
    finally:
        shutil.rmtree(root, ignore_errors=True)


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
