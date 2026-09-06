"""Phase 478 candidate harvester.

Extracts, for a `generator+oracle`-classified source file pinned at a git
commit, the exact byte strings that file's own existing code submitted to
one of this project's recognized cryptographic oracle entrypoints, by
running the file's own unmodified code -- via its frozen invocation
recipe -- inside a subprocess whose complete repository snapshot is a
disposable materialization of that exact commit. Only the target file's
content is not enough: its own imports (`cb_common`, `data`, sibling
modules, `__file__`-relative data reads) must resolve against the SAME
pinned commit, never the live working tree.

Path convention: every path this module accepts or returns for a source
file is REPOSITORY-RELATIVE (e.g. `tools/gsmg/foo.py`), matching what
`git rev-parse <commit>:<path>` expects. `materialize_commit_snapshot`
yields the snapshot's REPOSITORY ROOT, not a `tools/gsmg` subdirectory --
resolving a repo-relative path against anything else double-joins
`tools/gsmg` and silently fails to find the file.

See "doc/Brainstorms/2026-09-05 - Phase 478 DBBI Substituted-Digest
Matrixsumlist Match Protocol.md" for the full design and the two-lock
sequencing this module is one step of. This module performs discovery-side
work only: it never computes a SHA-256 of a candidate or an equality
pattern (see the protocol's "No sha256 field" note), and must not be used
after the oracle lock without a fresh protocol amendment.
"""

from __future__ import annotations

import contextlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DRIVER_PATH = SCRIPT_DIR / "phase478_harvest_driver.py"
REPO_ROOT = SCRIPT_DIR.parent.parent

DEFAULT_TIMEOUT_S = 30

# Must match phase478_harvest_driver.py's own CAPTURE_FILE_ENV constant.
# This module OWNS the capture file's lifecycle (creates the path, sets
# the env var, reads it back, deletes it) precisely because it -- unlike
# the driver subprocess -- is guaranteed to run its cleanup even when the
# subprocess is killed outright on a timeout, which never reaches the
# driver's own `finally` blocks at all.
CAPTURE_FILE_ENV = "PHASE478_CAPTURE_FILE"

# Every Phase 478 tool script (the standard driver plus any dedicated
# adapter for a file whose oracle boundary the standard driver cannot
# reach) that must be copied into a materialized snapshot so it can be
# invoked with the snapshot as its cwd/sys.path root. None of these are
# part of the PINNED universe -- they are Phase 478's own code, always the
# current version, never read from the snapshot itself.
ADAPTER_PATHS = [
    SCRIPT_DIR / "phase478_adapter_cosmic_raw_digest.py",
]
TOOL_SCRIPTS = [DRIVER_PATH, *ADAPTER_PATHS]


def git_blob_sha(commit: str, repo_relative_path: str) -> str:
    out = subprocess.run(
        ["git", "rev-parse", f"{commit}:{repo_relative_path}"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    )
    return out.stdout.strip()


@contextlib.contextmanager
def materialize_commit_snapshot(commit: str):
    """Extract the COMPLETE repository tree at `commit` into a fresh
    temporary directory via `git archive | tar -x` -- not merely the
    target files -- so every import a target script performs (cb_common,
    data, wordlist reads relative to __file__, etc.) resolves against the
    pinned commit, never the live working tree. Yields the path to that
    snapshot's REPOSITORY ROOT (so repo-relative paths resolve directly
    against it, with no `tools/gsmg` double-join), with a fresh copy of
    this project's own (unpinned -- it is Phase 478's own tool, not part
    of the pinned universe) harvest driver placed at
    `<root>/tools/gsmg/phase478_harvest_driver.py`."""
    tmp_root = Path(tempfile.mkdtemp(prefix="phase478_snapshot_"))
    try:
        archive = subprocess.Popen(
            ["git", "archive", commit], cwd=REPO_ROOT, stdout=subprocess.PIPE,
        )
        subprocess.run(["tar", "-x", "-C", str(tmp_root)], stdin=archive.stdout, check=True)
        archive.stdout.close()
        archive.wait()
        if archive.returncode != 0:
            raise RuntimeError(f"git archive {commit} failed (rc={archive.returncode})")
        snapshot_gsmg = tmp_root / "tools" / "gsmg"
        if not snapshot_gsmg.is_dir():
            raise RuntimeError(f"pinned commit {commit} has no tools/gsmg directory")
        for tool_script in TOOL_SCRIPTS:
            shutil.copy(tool_script, snapshot_gsmg / tool_script.name)
        yield tmp_root
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)


def _isolated_env(extra_env: dict | None = None) -> dict:
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    env["PYTHONHASHSEED"] = "0"
    if extra_env:
        env.update(extra_env)
    return env


def run_driver_in_snapshot(
    snapshot_root: Path,
    source_file: str,
    recipe: dict,
    timeout_s: float = DEFAULT_TIMEOUT_S,
) -> dict:
    """Run the harvest driver (or, if `recipe["driver"]` names one, a
    dedicated adapter script) against `source_file` (a REPOSITORY-RELATIVE
    path, e.g. `tools/gsmg/foo.py`) inside `snapshot_root` (a directory
    whose layout mirrors the repository root -- as
    `materialize_commit_snapshot` yields, or as a synthetic test fixture
    constructs) using `recipe` (`{"mode": "cli", "argv": [...]}` or
    `{"mode": "call", "entry_function": "name", ...}`). `snapshot_root`
    must already contain `tools/gsmg/<driver file>`. This function does
    not assume anything about the live working tree and never reads from
    it.

    Owns the capture file's entire lifecycle: creates it, tells the
    subprocess where it is, reads it back, and ALWAYS deletes it --
    including when the subprocess is killed outright on a timeout, which
    never reaches the driver's own cleanup code at all (a real leak this
    function's own `finally` exists specifically to close)."""
    driver_name = recipe.get("driver", DRIVER_PATH.name)
    driver = snapshot_root / "tools" / "gsmg" / driver_name
    target = snapshot_root / source_file
    cwd = snapshot_root / "tools" / "gsmg"

    capture_fd, capture_path_str = tempfile.mkstemp(prefix="phase478_capture_", suffix=".jsonl")
    os.close(capture_fd)
    capture_path = Path(capture_path_str)
    extra_env = dict(recipe.get("env") or {})
    extra_env[CAPTURE_FILE_ENV] = capture_path_str
    env = _isolated_env(extra_env)

    try:
        try:
            proc = subprocess.run(
                [sys.executable, str(driver), str(target), json.dumps(recipe)],
                cwd=str(cwd),
                capture_output=True, text=True, timeout=timeout_s, env=env,
            )
        except subprocess.TimeoutExpired:
            return {"status": "harvest_failed", "error": "timeout", "candidates": []}

        stdout = proc.stdout.strip()
        if not stdout:
            return {
                "status": "harvest_failed",
                "error": f"driver produced no output; stderr={proc.stderr[-2000:]!r}",
                "candidates": [],
            }
        lines = stdout.splitlines()
        last_line = lines[-1]  # driver's own JSON is always last
        # Everything before it is whatever the TARGET itself printed
        # (module runs in-process via runpy, so its stdout is interleaved
        # with the driver's own, always terminating in the driver's one
        # JSON line).
        target_stdout = "\n".join(lines[:-1])
        try:
            parsed = json.loads(last_line)
        except json.JSONDecodeError as exc:
            return {
                "status": "harvest_failed",
                "error": f"driver output not valid JSON: {exc}; stdout={stdout[-2000:]!r}",
                "candidates": [],
            }

        candidates = []
        if capture_path.is_file():
            with open(capture_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        candidates.append(json.loads(line))
        parsed["candidates"] = candidates
        parsed["_target_stdout"] = target_stdout
        return parsed
    finally:
        try:
            capture_path.unlink()
        except OSError:
            pass


def dedupe_candidates(raw_candidates: list[dict]) -> list[dict]:
    """Collapse exact-duplicate bytes (same file) to one manifest entry,
    keeping every distinct call site that produced it. A site carries
    every key the recorder attached beyond `bytes_b64` -- the standard
    driver always supplies `entrypoint`/`caller_file`/`caller_line`/
    `caller_function`; a dedicated adapter (e.g. the local-`decrypt`
    boundary adapter for `cosmic_raw_digest_checkpoint_audit.py`) may
    attach additional provenance fields (`digest_name`, `source`), which
    are preserved verbatim and participate in the dedup/sort key. No
    SHA-256 is computed here -- see the protocol's "No sha256 field" note;
    that value belongs only to post-oracle-lock scoring."""
    by_bytes: dict[str, dict] = {}
    for entry in raw_candidates:
        b64 = entry["bytes_b64"]
        site = {k: v for k, v in entry.items() if k != "bytes_b64"}
        if b64 not in by_bytes:
            by_bytes[b64] = {"bytes_b64": b64, "call_sites": []}
        if site not in by_bytes[b64]["call_sites"]:
            by_bytes[b64]["call_sites"].append(site)

    candidates = list(by_bytes.values())
    for c in candidates:
        c["call_sites"].sort(key=lambda s: sorted(s.items()))
    candidates.sort(key=lambda c: c["bytes_b64"])
    return candidates


def harvest_file(
    snapshot_root: Path,
    commit: str,
    source_file: str,
    recipe: dict,
    default_timeout_s: float = DEFAULT_TIMEOUT_S,
) -> dict:
    """Per-file timeout: `recipe["timeout_s"]` if the locked recipe sets
    one, else `default_timeout_s`. The recipe schema has always named a
    per-file `timeout_s` field; earlier revisions of this function never
    actually read it, silently applying one shared batch-wide timeout to
    every file regardless of its own recipe."""
    blob_sha = git_blob_sha(commit, source_file)
    timeout_s = recipe.get("timeout_s", default_timeout_s)
    driver_result = run_driver_in_snapshot(snapshot_root, source_file, recipe, timeout_s=timeout_s)
    result = {
        "source_file": source_file,
        "source_blob_sha": blob_sha,
        "status": driver_result["status"],
        "error": driver_result.get("error"),
        "candidates": dedupe_candidates(driver_result.get("candidates", [])),
    }
    # Preserve the target's own printed gate statistics (p-values,
    # thresholds, seeds, trial budgets -- whatever it prints) only for
    # files whose recipe carries a zero_candidate_policy: this is the
    # structural witness that a legitimate zero came from a real,
    # evaluated, deterministic gate, not from a silently broken recipe.
    # Not collected for every file to avoid bloating the artifact for
    # the (much larger) ordinary positive-candidate results.
    if recipe.get("zero_candidate_policy"):
        result["gate_witness"] = driver_result.get("_target_stdout", "")
    return result


def harvest_files(
    commit: str,
    path_recipes: dict[str, dict],
    default_timeout_s: float = DEFAULT_TIMEOUT_S,
) -> list[dict]:
    """`path_recipes` maps each eligible REPOSITORY-RELATIVE path (e.g.
    'tools/gsmg/matrixsumlist_title_and_iteration_audit.py') to its frozen
    recipe. One snapshot is materialized and reused for every file in the
    batch. `default_timeout_s` applies only to recipes that don't set
    their own `timeout_s`."""
    with materialize_commit_snapshot(commit) as snapshot_root:
        results = [
            harvest_file(snapshot_root, commit, path, recipe, default_timeout_s=default_timeout_s)
            for path, recipe in path_recipes.items()
        ]
    results.sort(key=lambda r: r["source_file"])
    return results


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: phase478_matrixsumlist_candidate_harvester.py <commit> <repo/relative/path.py>=<entry_function|(blank for cli)> [...]")
        sys.exit(1)
    commit_arg = sys.argv[1]
    recipes = {}
    for spec in sys.argv[2:]:
        # Minimal CLI convenience for ad-hoc single-file runs; the real
        # discovery-lock recipe set is authored explicitly, not via this
        # shorthand.
        path_arg, _, mode_arg = spec.partition("=")
        recipes[path_arg] = {"mode": "call", "entry_function": mode_arg} if mode_arg else {"mode": "cli", "argv": []}
    print(json.dumps(harvest_files(commit_arg, recipes), indent=2))
