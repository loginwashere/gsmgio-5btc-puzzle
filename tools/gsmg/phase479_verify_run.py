#!/usr/bin/env python3
"""Fail-closed verifier for the locked Phase 479 result."""

import argparse
import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]

FILE_PATHS = {
    "protocol": REPO_ROOT / "doc/Brainstorms/2026-09-06 - Phase 479 P32 64-in-80 Alignment Protocol.md",
    "audit_script": SCRIPT_DIR / "phase479_p32_alignment_audit.py",
    "cb_common": SCRIPT_DIR / "cb_common.py",
    "binary_key_material_backfill": SCRIPT_DIR / "binary_key_material_backfill.py",
    "extended_cipher_recheck": SCRIPT_DIR / "extended_cipher_recheck.py",
    "first_hint_hash_audit": SCRIPT_DIR / "first_hint_hash_audit.py",
    "half_better_half_algebra_audit": SCRIPT_DIR / "half_better_half_algebra_audit.py",
    "key_shape_classifier": SCRIPT_DIR / "key_shape_classifier.py",
    "raw_key_chunk_audit": SCRIPT_DIR / "raw_key_chunk_audit.py",
    "data": SCRIPT_DIR / "data.py",
}


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(lock_path, result_path, verification_path, recompute=True):
    lock_path = Path(lock_path)
    result_path = Path(result_path)
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    result = json.loads(result_path.read_text(encoding="utf-8"))
    errors = []
    if set(lock.get("files_sha256", {})) != set(FILE_PATHS):
        errors.append("locked file set differs from verifier's frozen file map")
    for name, path in FILE_PATHS.items():
        expected = lock.get("files_sha256", {}).get(name)
        actual = sha256_file(path)
        if expected != actual:
            errors.append(f"hash mismatch: {name}")
    if result.get("lock_sha256") != sha256_file(lock_path):
        errors.append("result lock hash mismatch")
    expected_summary = {
        "phase": 479,
        "candidate_count": 648,
        "keystring_count": 14551,
        "decryptions": 14551,
        "alignments_per_decryption": 17,
        "scalar_candidates_per_alignment": 17,
    }
    for key, expected in expected_summary.items():
        if result.get(key) != expected:
            errors.append(f"result field mismatch: {key}")
    recomputed = None
    if not errors and recompute:
        spec = importlib.util.spec_from_file_location("phase479_locked", FILE_PATHS["audit_script"])
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.verify_lock(lock_path)
        with tempfile.TemporaryDirectory() as directory:
            replay_result = Path(directory) / "result.json"
            replay_hits = Path(directory) / "hits.jsonl"
            recomputed = module.run(lock_path, replay_result, replay_hits)
        if recomputed != result:
            errors.append("full recomputation differs from saved result")
    record = {
        "phase": 479,
        "consistent": not errors,
        "errors": errors,
        "recomputed": recompute,
        "lock_sha256": sha256_file(lock_path),
        "result_sha256": sha256_file(result_path),
        "exact_hit_count": result.get("exact_hit_count"),
        "verdict": result.get("verdict"),
    }
    Path(verification_path).write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return record


def main():
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

