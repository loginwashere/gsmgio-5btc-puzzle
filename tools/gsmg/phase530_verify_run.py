#!/usr/bin/env python3
"""Capture and fail-closed verify the completed Phase-530 GPU run."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
OUTPUT_DIR = REPO_ROOT / "tools/gpu_oracle/output_local"
LOCK = SCRIPT_DIR / "phase530_execution_lock.json"
CHECKPOINT = OUTPUT_DIR / "phase530.checkpoint"
HITS = OUTPUT_DIR / "phase530.hits.jsonl"
KEYSHAPE = OUTPUT_DIR / "phase530.keyshape.jsonl"
RUN_LOG = OUTPUT_DIR / "phase530.run.log"
RESULT = SCRIPT_DIR / "phase530_verification.json"
CONTAINER = "gsmg-phase530"
EXPECTED_LOCK_SHA256 = "5e4bca0760f5ba62dc93d54e5b5351bd7742a7aaf0b40405263296ad5ec8709d"
EXPECTED_FORMS = 90


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def capture_runtime() -> None:
    state = subprocess.run(
        ["docker", "inspect", CONTAINER, "--format", "{{.State.Status}} {{.State.ExitCode}}"],
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()
    if state != "exited 0":
        raise AssertionError(f"container did not exit cleanly: {state}")
    logs = subprocess.run(
        ["docker", "logs", CONTAINER], check=True, text=True, capture_output=True
    )
    text = logs.stdout + logs.stderr
    RUN_LOG.write_text(text, encoding="utf-8")


def verify_checkpoint(path: Path = CHECKPOINT) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        header = json.loads(handle.readline())
        if not header.get("header") or header.get("version") != 1:
            raise AssertionError("checkpoint header missing or unsupported")
        if header.get("candidate_count") != EXPECTED_FORMS:
            raise AssertionError("checkpoint candidate count drifted")
        completed = 0
        for completed, line in enumerate(handle, start=1):
            if int(line) != completed - 1:
                raise AssertionError(f"checkpoint discontinuity at {completed - 1}")
    if completed != EXPECTED_FORMS:
        raise AssertionError(f"checkpoint incomplete: {completed}/{EXPECTED_FORMS}")
    return {"header": header, "completed_forms": completed, "line_count": completed + 1}


def nonempty_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def verify() -> dict:
    lock_sha = sha256_file(LOCK)
    if lock_sha != EXPECTED_LOCK_SHA256:
        raise AssertionError(f"execution lock drifted: {lock_sha}")
    checkpoint = verify_checkpoint()
    hits = nonempty_jsonl(HITS)
    keyshape = nonempty_jsonl(KEYSHAPE)
    if hits or keyshape:
        raise AssertionError("Phase 530 has a hit requiring positive manual handling")
    log = RUN_LOG.read_text(encoding="utf-8", errors="replace")
    required = [
        "[selftest] PASSED -- GPU kernel output matches the CPU reference oracle.",
        "[main] 5 base candidates",
        "[main] expanded to 90 passphrase forms",
        "[main] Bloom cache loaded:",
        "[main] folded in 8 known EC-derived target address(es)",
        "[main] 90/90 candidates (100.0%)",
        "[main] sweep complete.",
    ]
    missing = [marker for marker in required if marker not in log]
    if missing:
        raise AssertionError(f"run log missing markers: {missing}")
    forbidden = [
        "[HIT:strong]",
        "[HIT:structural]",
        "EXACT MATCH on EC-derived target",
        "CONFIRMED FUNDED ADDRESS(ES)",
    ]
    present = [marker for marker in forbidden if marker in log]
    if present:
        raise AssertionError(f"positive markers present: {present}")
    return {
        "phase": 530,
        "consistent": True,
        "execution_lock_sha256": lock_sha,
        "completed_forms": checkpoint["completed_forms"],
        "checkpoint_header": checkpoint["header"],
        "strong_hits": 0,
        "structural_hits": 0,
        "weak_rows": 0,
        "keyshape_rows": 0,
        "known_target_matches": 0,
        "confirmed_funded": 0,
        "artifacts": {
            "checkpoint_sha256": sha256_file(CHECKPOINT),
            "hits_sha256": sha256_file(HITS),
            "keyshape_sha256": sha256_file(KEYSHAPE),
            "run_log_sha256": sha256_file(RUN_LOG),
        },
        "disposition": (
            "bounded negative for five Phase-528 payload bases, 90 standard forms, "
            "and the unchanged Phase-527 four-blob 60-variant oracle"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture-runtime", action="store_true")
    args = parser.parse_args()
    if args.capture_runtime:
        capture_runtime()
    result = verify()
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

