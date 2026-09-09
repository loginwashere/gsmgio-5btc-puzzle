#!/usr/bin/env python3
"""Fail-closed verifier for the locked Phase 480 result."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
FILE_PATHS = {
    "protocol": REPO_ROOT / "doc/Brainstorms/2026-09-06 - Phase 480 Closed-System Address Construction Protocol.md",
    "audit_script": SCRIPT_DIR / "phase480_p32_address_password_audit.py",
    "verifier": SCRIPT_DIR / "phase480_verify_run.py",
    "novelty_comparator": SCRIPT_DIR / "phase480_address_novelty_comparator.py",
    "novelty_result": SCRIPT_DIR / "phase480_address_novelty_result.json",
    "cb_common": SCRIPT_DIR / "cb_common.py",
    "first_hint_hash_audit": SCRIPT_DIR / "first_hint_hash_audit.py",
    "data": SCRIPT_DIR / "data.py",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(lock_path: Path, result_path: Path, verification_path: Path, recompute: bool = True) -> dict:
    lock_path = Path(lock_path)
    result_path = Path(result_path)
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    result = json.loads(result_path.read_text(encoding="utf-8"))
    errors = []

    if set(lock.get("files_sha256", {})) != set(FILE_PATHS):
        errors.append("locked file set differs from verifier's frozen file map")
    for name, path in FILE_PATHS.items():
        if lock.get("files_sha256", {}).get(name) != sha256_file(path):
            errors.append(f"hash mismatch: {name}")
    if lock.get("phase") != 480 or lock.get("status") != "locked-before-real-run":
        errors.append("lock phase/status mismatch")
    if lock.get("material_count") != 8 or lock.get("planned_decryptions") != 8:
        errors.append("locked material/decryption budget mismatch")
    if lock.get("primary_count") != 4 or lock.get("representation_control_count") != 4:
        errors.append("locked tier counts mismatch")
    if result.get("lock_sha256") != sha256_file(lock_path):
        errors.append("result lock hash mismatch")
    for key, expected in (
        ("phase", 480), ("target_blob", "P32TRAILING"),
        ("material_count", 8), ("decryptions", 8),
    ):
        if result.get(key) != expected:
            errors.append(f"result field mismatch: {key}")

    attempts = result.get("attempts")
    if not isinstance(attempts, list) or len(attempts) != 8:
        errors.append("attempt list is not exactly eight records")
        attempts = []
    expected_ids = {
        (row["construction"], row["level"], row["tier"], row["material_sha256"])
        for row in lock.get("materials", [])
    }
    actual_ids = {
        (row.get("construction"), row.get("level"), row.get("tier"), row.get("password_sha256"))
        for row in attempts
    }
    if actual_ids != expected_ids:
        errors.append("attempt identity set differs from locked materials")
    primary = sum(bool(row.get("promoted")) and row.get("tier") == "primary" for row in attempts)
    controls = sum(
        bool(row.get("promoted")) and row.get("tier") == "representation_control"
        for row in attempts
    )
    padded = sum(bool(row.get("padding_valid")) for row in attempts)
    if result.get("primary_promoted_count") != primary:
        errors.append("primary promoted count mismatch")
    if result.get("representation_control_promoted_count") != controls:
        errors.append("representation-control promoted count mismatch")
    if result.get("padding_valid_diagnostic_count") != padded:
        errors.append("padding-valid diagnostic count mismatch")
    expected_verdict = "positive_requires_sensitive_review" if primary + controls else "bounded_negative"
    if result.get("verdict") != expected_verdict:
        errors.append("verdict mismatch")

    if not errors and recompute:
        spec = importlib.util.spec_from_file_location("phase480_locked", FILE_PATHS["audit_script"])
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.verify_lock(lock_path)
        with tempfile.TemporaryDirectory() as directory:
            replay = module.run(
                lock_path, Path(directory) / "result.json", Path(directory) / "hits.jsonl"
            )
        if replay != result:
            errors.append("full recomputation differs from saved result")

    record = {
        "phase": 480,
        "consistent": not errors,
        "errors": errors,
        "recomputed": recompute,
        "lock_sha256": sha256_file(lock_path),
        "result_sha256": sha256_file(result_path),
        "primary_promoted_count": result.get("primary_promoted_count"),
        "representation_control_promoted_count": result.get("representation_control_promoted_count"),
        "padding_valid_diagnostic_count": result.get("padding_valid_diagnostic_count"),
        "verdict": result.get("verdict"),
    }
    Path(verification_path).write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("lock", type=Path)
    parser.add_argument("result", type=Path)
    parser.add_argument("verification", type=Path)
    parser.add_argument("--no-recompute", action="store_true")
    args = parser.parse_args()
    record = verify(args.lock, args.result, args.verification, recompute=not args.no_recompute)
    print(json.dumps(record, indent=2, sort_keys=True))
    return 0 if record["consistent"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
