#!/usr/bin/env python3
"""Fail-closed verifier for the locked Phase 481 result.

Unlike Phase 480's verifier (exact 8-attempt identity-set replay), this
recomputes only the aggregate counters -- storing 10,000,000 per-attempt
records is not reviewable -- by fully re-streaming the same locked,
hash-pinned wordlist through the same oracle.
"""

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
    "protocol": REPO_ROOT
    / "doc/Brainstorms/2026-09-06 - Phase 481 P32TRAILING Pwdb Wordlist Password Audit Protocol.md",
    "audit_script": SCRIPT_DIR / "phase481_p32_pwdb_wordlist_audit.py",
    "verifier": SCRIPT_DIR / "phase481_verify_run.py",
    "cb_common": SCRIPT_DIR / "cb_common.py",
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
    if lock.get("phase") != 481 or lock.get("status") != "locked-before-real-run":
        errors.append("lock phase/status mismatch")
    if lock.get("target_blob") != "P32TRAILING":
        errors.append("locked target blob mismatch")
    if lock.get("crypto_profile") != "legacy-evp-bytes-to-key-sha256/aes-256-cbc/pkcs7":
        errors.append("locked crypto profile mismatch")
    if lock.get("wordlist_sha256") != "18dc49ca32b62455a61e3398f4ab9f93eb700ff142fa0d4b9fd11a727f3b80e4":
        errors.append("locked wordlist hash mismatch")
    if lock.get("wordlist_line_count") != 10_000_000:
        errors.append("locked wordlist line count mismatch")
    if lock.get("wordlist_blank_lines") != 0 or lock.get("wordlist_duplicate_lines") != 0:
        errors.append("locked wordlist blank/duplicate control mismatch")

    if result.get("lock_sha256") != sha256_file(lock_path):
        errors.append("result lock hash mismatch")
    for key, expected in (
        ("phase", 481), ("target_blob", "P32TRAILING"),
        ("attempted", lock.get("wordlist_line_count")),
    ):
        if result.get(key) != expected:
            errors.append(f"result field mismatch: {key}")

    promoted = (
        result.get("strong_text_promoted_count", 0) + result.get("structural_binary_promoted_count", 0)
    )
    if result.get("promoted_count") != promoted:
        errors.append("promoted count is not the sum of its two tiers")
    expected_verdict = "positive_requires_sensitive_review" if promoted else "bounded_negative"
    if result.get("verdict") != expected_verdict:
        errors.append("verdict mismatch")

    if not errors and recompute:
        spec = importlib.util.spec_from_file_location("phase481_locked", FILE_PATHS["audit_script"])
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.verify_lock(lock_path)
        with tempfile.TemporaryDirectory() as directory:
            replay = module.run(
                lock_path,
                Path(directory) / "result.json",
                Path(directory) / "hits.jsonl",
                Path(directory) / "weak.jsonl",
                progress_every=0,
            )
        comparable_keys = (
            "phase", "target_blob", "attempted", "padding_valid_count",
            "weak_tier_count", "strong_text_promoted_count",
            "structural_binary_promoted_count", "promoted_count", "verdict",
        )
        for key in comparable_keys:
            if replay.get(key) != result.get(key):
                errors.append(f"full recomputation differs from saved result: {key}")

    record = {
        "phase": 481,
        "consistent": not errors,
        "errors": errors,
        "recomputed": recompute,
        "lock_sha256": sha256_file(lock_path),
        "result_sha256": sha256_file(result_path),
        "attempted": result.get("attempted"),
        "padding_valid_count": result.get("padding_valid_count"),
        "weak_tier_count": result.get("weak_tier_count"),
        "promoted_count": result.get("promoted_count"),
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
