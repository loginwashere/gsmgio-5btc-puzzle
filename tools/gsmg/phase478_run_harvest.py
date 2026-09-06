"""Phase 478 fail-closed harvest runner.

Usage: phase478_run_harvest.py <discovery_lock_path> [<output_path>]

Consumes ONLY the discovery lock -- never arbitrary paths or recipes
supplied on the command line. Before touching anything it re-verifies
every pinned hash and blob the lock claims (the protocol, harvester,
driver, adapter, and common-module scripts; every one of the 96 classified
`.py` files' git blob hash at the cutoff commit; every one of the 157
reference `doc`/`findings` blob hashes; and, where locally reachable, the
two motivation-input file hashes), extracts exactly the locked
`generator+oracle` recipes, dispatches each through the standard driver or
its named adapter, and REJECTS -- raises, writes no artifact -- if any
locked entry is missing from the result set, if any extra entry appears,
if any locked entry's run status is not "ok", or if any locked entry
produces zero candidates WITHOUT a locked `zero_candidate_policy` (a
frozen, deterministic historical significance gate verified not to clear
on real data -- exactly `EXPECTED_ZERO_CANDIDATE_POLICY_PATHS`, no more,
no fewer). A `zero_candidate_policy` never excuses a non-"ok" status.

Never computes a SHA-256 of any candidate byte string -- see the
protocol's "No sha256 field" note. The one hash this script does compute
and record is the discovery lock FILE's own SHA-256, stamped into the raw
capture artifact so it stays traceable to the exact lock it was produced
under.

Output is a RAW CAPTURE artifact only (bytes_b64 + call_sites per
candidate) -- not the final candidate manifest. Structural provenance
annotation (`phase`, `construction_label`, `transformation`, `eligible`,
`eligible_reason`) is a separate step, performed afterward using only
already-pinned sources, and must not itself compute any candidate digest
or equality pattern (see the protocol's "Dedicated adapters" /
"Manifest schema" sections).

Output format: newline-delimited JSON (JSONL), not one indented JSON
blob -- at real scale (~2,000,000 deduplicated candidates across the 21
positive files) an indented monolithic document means multi-gigabyte
transient memory and a document no tool can stream. Each line is a
complete, independently-parseable, compact (no extra whitespace) JSON
object, written incrementally as results come in:

    {"record_type": "header", ...}                  -- exactly one, first
    {"record_type": "source", "source_file": ..., ...}   -- one per locked file (23)
    {"record_type": "candidate", "source_file": ..., "bytes_b64": ..., "call_sites": [...]}

A candidate line's `source_file` is its only provenance reference back to
its "source" record -- the file-level facts (blob hash, status, gate
witness) are stored ONCE per file, not repeated per candidate.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent

EXPECTED_GENERATOR_ORACLE_COUNT = 23

# The ONLY five locked files whose recipe may carry zero_candidate_policy,
# under exactly two distinct, frozen reasons. Any other path producing
# zero candidates is a broken recipe, not a quiet pass -- this set was
# expanded from an initial 2 to these 5 only after running every one of
# the 23 locked files for real and reading each zero-candidate file's own
# control flow; it was never assumed or extrapolated from the first two.
#
# historical_significance_gate_closed: a frozen, deterministic shuffle-
# based significance test gates AES escalation; run against real DBBI/FAED
# data under the locked recipe, the gate does not clear (real p-values
# recorded as each result's own `gate_witness`, well above the file's own
# threshold in every case).
ZERO_CANDIDATE_REASON_GATE_CLOSED = "historical_significance_gate_closed"

# historical_escalation_never_executed_no_frozen_threshold: this file's
# escalation is gated by a CLI-supplied --escalate-if-above threshold with
# no default -- but per Phase 43 (tools/gsmg/findings/P00043.md, verified
# directly, not taken on trust), no historical run of this file ever
# crossed that gate, and no calibrated threshold value was ever frozen.
# Phase 43's own verdict rests instead on a separate, complete 100-trial
# token-preserving null test (real=-2544.1, null median=-2539.0,
# p=0.63366) that does not require running the AES escalation at all.
# Deriving a threshold now, to force this file into the "positive-capture"
# bucket, would be a NEW Phase 478 candidate-generating experiment outside
# the closed historical harvest -- not a lock formality -- so it is not
# done; this file's zero is authorized on the historical record as-is.
ZERO_CANDIDATE_REASON_ESCALATION_NEVER_RUN = "historical_escalation_never_executed_no_frozen_threshold"

EXPECTED_ZERO_CANDIDATE_POLICY_PATHS = frozenset({
    "tools/gsmg/adjacent_diff_sweep.py",
    "tools/gsmg/digraphic_sweep.py",
    "tools/gsmg/native_prime_zeroing_sweep.py",
    "tools/gsmg/prefix_boundary_sweep.py",
    "tools/gsmg/faed_monoalphabetic_sweep.py",
})


class LockVerificationError(RuntimeError):
    """Raised on any fail-closed rejection -- a hash/blob mismatch, a
    malformed lock, or a harvest result that doesn't exactly match the
    locked expectations. No artifact is written when this is raised."""


def sha256_file(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git_blob_sha(commit: str, repo_relative_path: str, repo_root: Path = REPO_ROOT) -> str:
    out = subprocess.run(
        ["git", "rev-parse", f"{commit}:{repo_relative_path}"],
        cwd=repo_root, capture_output=True, text=True, check=True,
    )
    return out.stdout.strip()


def verify_lock(lock: dict, repo_root: Path = REPO_ROOT, adapter_dir: Path = SCRIPT_DIR) -> None:
    """Re-derive every hash and blob the lock claims, independently, and
    raise on the first mismatch. Never trusts the lock's own numbers as
    self-certifying -- each is recomputed from the actual pinned source."""
    commit = lock["cutoff_commit"]

    for repo_relative_path, expected_sha in (
        (lock["protocol_path"], lock["protocol_sha256"]),
        (lock["harvester_script"], lock["harvester_script_sha256"]),
        (lock["driver_script"], lock["driver_script_sha256"]),
        (lock["runner_script"], lock["runner_script_sha256"]),
    ):
        actual = sha256_file(repo_root / repo_relative_path)
        if actual != expected_sha:
            raise LockVerificationError(
                f"{repo_relative_path}: hash mismatch (locked {expected_sha}, actual {actual})"
            )

    actual_common = sha256_file(adapter_dir / "phase478_common.py")
    if actual_common != lock["phase478_common_sha256"]:
        raise LockVerificationError("phase478_common.py: hash mismatch")

    for name, expected_sha in lock["adapter_scripts"].items():
        actual = sha256_file(adapter_dir / name)
        if actual != expected_sha:
            raise LockVerificationError(f"adapter {name}: hash mismatch")

    for entry in (
        lock["eligible_py_file_classification"]
        + lock["reference_doc_files"]
        + lock["reference_findings_files"]
    ):
        actual = git_blob_sha(commit, entry["path"], repo_root=repo_root)
        if actual != entry["blob_sha"]:
            raise LockVerificationError(
                f"{entry['path']}: blob hash mismatch (locked {entry['blob_sha']}, actual {actual})"
            )

    for label, info in lock.get("motivation_inputs", {}).items():
        path = Path(info["path"])
        if not path.is_file():
            raise LockVerificationError(f"motivation input {label!r} not found at {path}")
        actual = sha256_file(path)
        if actual != info["sha256"]:
            raise LockVerificationError(f"motivation input {label!r}: hash mismatch")


def extract_locked_recipes(
    lock: dict, expected_count: int = EXPECTED_GENERATOR_ORACLE_COUNT,
) -> dict:
    """Return {repo_relative_path: recipe} for every locked
    `generator+oracle` entry -- the ONLY set of files this runner will
    ever execute. Raises if the count doesn't match what the lock is
    supposed to certify, or if any such entry lacks a recipe."""
    entries = [
        e for e in lock["eligible_py_file_classification"]
        if e["category"] == "generator+oracle"
    ]
    if len(entries) != expected_count:
        raise LockVerificationError(
            f"expected exactly {expected_count} generator+oracle entries, found {len(entries)}"
        )
    recipes = {}
    for entry in entries:
        if "recipe" not in entry:
            raise LockVerificationError(f"{entry['path']}: generator+oracle entry has no recipe")
        recipes[entry["path"]] = entry["recipe"]
    return recipes


def check_results(
    recipes: dict,
    results: list,
    expected_zero_candidate_paths: frozenset | None = None,
    expected_reason_codes: dict | None = None,
) -> tuple[list, list]:
    """The fail-closed acceptance gate. Every locked path must appear
    exactly once, with status "ok". A path may produce zero candidates
    ONLY if its recipe carries `zero_candidate_policy: {"allowed": true,
    ...}` -- never as an excuse for a non-"ok" status, which is always
    fatal regardless. When `expected_zero_candidate_paths` is given, the
    set of policy-granted paths in `recipes` must equal it EXACTLY (catches
    a lock that quietly grants the exception to an extra file, or drops it
    from one of the intended ones). When `expected_reason_codes` is also
    given (`{path: reason_code}`), each granted path's own
    `zero_candidate_policy["reason_code"]` must match it exactly (catches
    a file mislabeled under the wrong one of the two frozen reasons).

    Returns `(positive_paths, authorized_zero_paths)` on success, both
    sorted."""
    result_paths = [r["source_file"] for r in results]
    result_path_set = set(result_paths)
    locked_paths = set(recipes.keys())

    if len(result_paths) != len(result_path_set):
        dupes = sorted({p for p in result_paths if result_paths.count(p) > 1})
        raise LockVerificationError(f"duplicate results for locked entries: {dupes}")

    missing = locked_paths - result_path_set
    if missing:
        raise LockVerificationError(f"missing results for locked entries: {sorted(missing)}")

    additional = result_path_set - locked_paths
    if additional:
        raise LockVerificationError(f"unexpected extra results not in the lock: {sorted(additional)}")

    failed = sorted(r["source_file"] for r in results if r["status"] != "ok")
    if failed:
        details = {r["source_file"]: r.get("error") for r in results if r["status"] != "ok"}
        raise LockVerificationError(f"locked entries did not run cleanly: {details}")

    permitted_zero_paths = {
        path for path, recipe in recipes.items()
        if recipe.get("zero_candidate_policy", {}).get("allowed") is True
    }
    if expected_zero_candidate_paths is not None and permitted_zero_paths != set(expected_zero_candidate_paths):
        raise LockVerificationError(
            f"zero_candidate_policy path set must be exactly "
            f"{sorted(expected_zero_candidate_paths)}, got {sorted(permitted_zero_paths)}"
        )

    if expected_reason_codes is not None:
        mismatched = {}
        for path in permitted_zero_paths:
            actual_reason = recipes[path]["zero_candidate_policy"].get("reason_code")
            expected_reason = expected_reason_codes.get(path)
            if actual_reason != expected_reason:
                mismatched[path] = {"expected": expected_reason, "actual": actual_reason}
        if mismatched:
            raise LockVerificationError(f"zero_candidate_policy reason_code mismatch: {mismatched}")

    unauthorized_zero = sorted(
        r["source_file"] for r in results
        if not r["candidates"] and r["source_file"] not in permitted_zero_paths
    )
    if unauthorized_zero:
        raise LockVerificationError(
            f"unauthorized zero-candidate results (broken recipe, not a quiet pass): {unauthorized_zero}"
        )

    authorized_zero = sorted(
        r["source_file"] for r in results
        if not r["candidates"] and r["source_file"] in permitted_zero_paths
    )
    positive = sorted(r["source_file"] for r in results if r["candidates"])
    return positive, authorized_zero


def write_raw_capture_jsonl(
    lock: dict, lock_path, results: list, output_path, recipes: dict | None = None,
) -> dict:
    """Stream the raw capture artifact as compact JSONL: one header line,
    one source-level record per locked file (status, blob hash, gate
    witness and zero_candidate_policy where applicable -- NEVER a
    candidate digest), then one record per deduplicated candidate, each
    referencing its source_file rather than repeating file-level facts.
    Returns summary counts. `recipes`, when given, lets a zero-candidate
    file's authorizing policy (reason_code and reason) ride along in its
    own source record, so the artifact is self-documenting without needing
    to cross-reference the lock separately."""
    sorted_results = sorted(results, key=lambda r: r["source_file"])
    total_candidates = sum(len(r["candidates"]) for r in sorted_results)

    with open(output_path, "w", encoding="utf-8") as f:
        header = {
            "record_type": "header",
            "phase": 478,
            "artifact_kind": "raw_capture",
            "discovery_lock_path": str(lock_path),
            "discovery_lock_sha256": sha256_file(lock_path),
            "cutoff_commit": lock["cutoff_commit"],
            "generator_oracle_count": len(sorted_results),
            "total_candidate_count": total_candidates,
        }
        f.write(json.dumps(header, separators=(",", ":")) + "\n")

        for r in sorted_results:
            source_record = {
                "record_type": "source",
                "source_file": r["source_file"],
                "source_blob_sha": r["source_blob_sha"],
                "status": r["status"],
                "candidate_count": len(r["candidates"]),
            }
            if "gate_witness" in r:
                source_record["gate_witness"] = r["gate_witness"]
            if recipes is not None:
                policy = recipes.get(r["source_file"], {}).get("zero_candidate_policy")
                if policy:
                    source_record["zero_candidate_policy"] = policy
            f.write(json.dumps(source_record, separators=(",", ":")) + "\n")

        for r in sorted_results:
            for c in sorted(r["candidates"], key=lambda c: c["bytes_b64"]):
                candidate_record = {
                    "record_type": "candidate",
                    "source_file": r["source_file"],
                    "bytes_b64": c["bytes_b64"],
                    "call_sites": c["call_sites"],
                }
                f.write(json.dumps(candidate_record, separators=(",", ":")) + "\n")

    return header


EXPECTED_ZERO_CANDIDATE_REASON_CODES = {
    "tools/gsmg/adjacent_diff_sweep.py": ZERO_CANDIDATE_REASON_GATE_CLOSED,
    "tools/gsmg/digraphic_sweep.py": ZERO_CANDIDATE_REASON_GATE_CLOSED,
    "tools/gsmg/native_prime_zeroing_sweep.py": ZERO_CANDIDATE_REASON_GATE_CLOSED,
    "tools/gsmg/prefix_boundary_sweep.py": ZERO_CANDIDATE_REASON_GATE_CLOSED,
    "tools/gsmg/faed_monoalphabetic_sweep.py": ZERO_CANDIDATE_REASON_ESCALATION_NEVER_RUN,
}


def run(lock_path: str, output_path: str) -> dict:
    lock = json.loads(Path(lock_path).read_text())
    verify_lock(lock)
    recipes = extract_locked_recipes(lock)

    from phase478_matrixsumlist_candidate_harvester import harvest_files

    results = harvest_files(lock["cutoff_commit"], recipes)
    positive, authorized_zero = check_results(
        recipes, results,
        expected_zero_candidate_paths=EXPECTED_ZERO_CANDIDATE_POLICY_PATHS,
        expected_reason_codes=EXPECTED_ZERO_CANDIDATE_REASON_CODES,
    )

    header = write_raw_capture_jsonl(lock, lock_path, results, output_path, recipes=recipes)
    print(
        f"wrote {output_path}: {header['generator_oracle_count']} locked entries "
        f"({len(positive)} positive, {len(authorized_zero)} authorized-zero: {authorized_zero}), "
        f"{header['total_candidate_count']} deduplicated candidates total"
    )
    return header


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        print("usage: phase478_run_harvest.py <discovery_lock_path> [<output_path>]")
        sys.exit(1)
    lock_path_arg = sys.argv[1]
    output_path_arg = sys.argv[2] if len(sys.argv) == 3 else "phase478_raw_capture.jsonl"
    try:
        run(lock_path_arg, output_path_arg)
    except LockVerificationError as exc:
        print(f"REJECTED: {exc}")
        sys.exit(1)
