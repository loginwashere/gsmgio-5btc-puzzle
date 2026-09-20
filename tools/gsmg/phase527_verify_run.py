#!/usr/bin/env python3
"""Fail-closed verification of the completed locked Phase-527 run."""
from __future__ import annotations

import collections
import hashlib
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

import phase524_slot_grammar_sweep_prep as p524  # noqa: E402
import phase527_selection_a_oracle_lock as p527  # noqa: E402

OUTPUT_DIR = REPO_ROOT / "tools/gpu_oracle/output_local"
CHECKPOINT = OUTPUT_DIR / "phase527.checkpoint"
HITS = OUTPUT_DIR / "phase527.hits.jsonl"
KEYSHAPE = OUTPUT_DIR / "phase527.keyshape.jsonl"
RUN_LOG = OUTPUT_DIR / "phase527.run.log"
VERIFICATION = SCRIPT_DIR / "phase527_verification.json"
EXPECTED_LOCK_SHA256 = "179022a1e9c7319bdd2bbbc4435ba48bbbd29fc50fcb9fda6c56c20a5cb14864"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def verify_checkpoint() -> dict:
    with CHECKPOINT.open("r", encoding="utf-8") as handle:
        first = handle.readline()
        header = json.loads(first)
        if not header.get("header") or header.get("version") != 1:
            raise AssertionError("checkpoint header is missing or unsupported")
        if header.get("candidate_count") != p527.EXPECTED_FORM_COUNT:
            raise AssertionError("checkpoint candidate count differs from the lock")
        completed = 0
        for completed, line in enumerate(handle, start=1):
            expected = completed - 1
            if int(line) != expected:
                raise AssertionError(f"checkpoint discontinuity at {expected}: {line!r}")
    if completed != p527.EXPECTED_FORM_COUNT:
        raise AssertionError(f"checkpoint incomplete: {completed}/{p527.EXPECTED_FORM_COUNT}")
    return {"header": header, "completed_forms": completed, "line_count": completed + 1}


def verify() -> dict:
    lock_sha = sha256_file(p527.LOCK)
    if lock_sha != EXPECTED_LOCK_SHA256:
        raise AssertionError(f"execution lock drifted: {lock_sha}")
    checkpoint = verify_checkpoint()

    hits = jsonl(HITS)
    if any(record.get("hit_kind") != "weak" for record in hits):
        raise AssertionError("a non-weak hit requires manual positive handling")
    weak_review = p524.classify_weak(HITS)
    if weak_review["weak_rows"] != len(hits):
        raise AssertionError("weak-review row count mismatch")
    if (
        weak_review["reconstructed"] != len(hits)
        or weak_review["padding_reconstruct_failures"]
        or weak_review["z_mismatches"]
        or weak_review["key_shaped_matches"]
    ):
        raise AssertionError(f"weak-hit review failed: {weak_review}")

    keyshape = jsonl(KEYSHAPE)
    if any(record.get("confirmed_funded") is not False for record in keyshape):
        raise AssertionError("a funded or unverified key-shape row exists")
    if any(record.get("target_label") for record in keyshape):
        raise AssertionError("a known-target match exists")

    log = RUN_LOG.read_text(encoding="utf-8", errors="replace")
    required = [
        "[selftest] PASSED -- GPU kernel output matches the CPU reference oracle.",
        "[main] 112624 base candidates",
        "[main] expanded to 5137056 passphrase forms",
        "[main] Bloom cache loaded:",
        "[main] folded in 8 known EC-derived target address(es)",
        "[main] 5137056/5137056 candidates (100.0%)",
        "[main] sweep complete.",
    ]
    missing = [marker for marker in required if marker not in log]
    if missing:
        raise AssertionError(f"run log is missing required markers: {missing}")
    forbidden = [
        "[HIT:strong]",
        "[HIT:structural]",
        "EXACT MATCH on EC-derived target",
        "CONFIRMED FUNDED ADDRESS(ES)",
    ]
    present = [marker for marker in forbidden if marker in log]
    if present:
        raise AssertionError(f"run log contains positive markers: {present}")

    weak_by_blob = dict(collections.Counter(record["blob_tag"] for record in hits))
    result = {
        "phase": 527,
        "consistent": True,
        "lock_sha256": lock_sha,
        "completed_forms": checkpoint["completed_forms"],
        "checkpoint_header": checkpoint["header"],
        "weak_rows": len(hits),
        "unique_weak_candidate_kdf_blob": len(
            {(r["candidate"], r["kdf"], r["blob_tag"]) for r in hits}
        ),
        "weak_by_blob": weak_by_blob,
        "weak_z_min": min((r["z_score"] for r in hits), default=None),
        "weak_z_max": max((r["z_score"] for r in hits), default=None),
        "weak_review": weak_review,
        "keyshape_rows": len(keyshape),
        "unique_keyshape_addresses": len({r["address"] for r in keyshape}),
        "confirmed_funded": sum(bool(r["confirmed_funded"]) for r in keyshape),
        "known_target_matches": sum(bool(r.get("target_label")) for r in keyshape),
        "strong_hits": 0,
        "structural_hits": 0,
        "artifacts": {
            "checkpoint_sha256": sha256_file(CHECKPOINT),
            "hits_sha256": sha256_file(HITS),
            "keyshape_sha256": sha256_file(KEYSHAPE),
            "run_log_sha256": sha256_file(RUN_LOG),
        },
        "disposition": (
            "bounded negative for the locked Selection-A 16-value matrixsumlist "
            "slot extension under the Phase-523 grammar and Phase-524 oracle"
        ),
    }
    return result


def main() -> int:
    result = verify()
    VERIFICATION.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
