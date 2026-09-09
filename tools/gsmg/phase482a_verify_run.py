#!/usr/bin/env python3
"""Fail-closed verifier for Phase 482A."""

import argparse
import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
FILE_PATHS = {
    "protocol": REPO_ROOT / "doc/Brainstorms/2026-09-06 - Phase 482A FAED Plaintext Frequency Signature Protocol.md",
    "audit_script": SCRIPT_DIR / "phase482a_faed_frequency_signature_audit.py",
    "verifier": SCRIPT_DIR / "phase482a_verify_run.py",
    "cb_common": SCRIPT_DIR / "cb_common.py",
    "data": SCRIPT_DIR / "data.py",
    "segmenter": SCRIPT_DIR / "checkerboard_code_ic_oracle.py",
    "phase410": SCRIPT_DIR / "phase410_solved_vector_toolchain_provenance_audit.py",
    "p32_sibling": SCRIPT_DIR / "p32_sibling_password_audit.py",
    "wayback_phase23": REPO_ROOT / "doc/html/choiceisanillusioncreatedbetweenthosewithpowerandthosewithoutaveryspecialdessertiwroteitmyself.html",
    "readme": REPO_ROOT / "README.md",
    "matrix_scene": REPO_ROOT / "wordlists/gsmg/matrix_architect_scene_through_choice_words.txt",
    "book_transcription": REPO_ROOT / "wordlists/gsmg/cosmic_duality_book_full_text.txt",
}


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(lock_path, result_path, verification_path, recompute=True):
    lock_path, result_path = Path(lock_path), Path(result_path)
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    result = json.loads(result_path.read_text(encoding="utf-8"))
    errors = []
    if set(lock.get("files_sha256", {})) != set(FILE_PATHS):
        errors.append("locked file set mismatch")
    for name, path in FILE_PATHS.items():
        if lock.get("files_sha256", {}).get(name) != sha256_file(path):
            errors.append(f"hash mismatch: {name}")
    for key, expected in (("phase", 482), ("source_count", 6), ("lane_count", 2)):
        if result.get(key) != expected:
            errors.append(f"result field mismatch: {key}")
    if result.get("lock_sha256") != sha256_file(lock_path):
        errors.append("result lock hash mismatch")
    matches = result.get("matches", [])
    if result.get("match_location_count") != len(matches):
        errors.append("match location count mismatch")
    if result.get("unique_passage_count") != len({row.get("passage_sha256") for row in matches}):
        errors.append("unique passage count mismatch")
    expected_decision = "trigger_phase482b" if matches else "bounded_negative_no_exact_passage"
    if result.get("decision") != expected_decision:
        errors.append("decision mismatch")
    diagnostics = result.get("diagnostics", [])
    if result.get("total_windows") != sum(row.get("window_count", 0) for row in diagnostics):
        errors.append("total window count mismatch")

    if not errors and recompute:
        spec = importlib.util.spec_from_file_location("phase482a_locked", FILE_PATHS["audit_script"])
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.verify_lock(lock_path)
        with tempfile.TemporaryDirectory() as directory:
            replay = module.run(lock_path, Path(directory) / "result.json")
        if replay != result:
            errors.append("full recomputation differs from saved result")
    record = {
        "phase": 482,
        "consistent": not errors,
        "errors": errors,
        "recomputed": recompute,
        "lock_sha256": sha256_file(lock_path),
        "result_sha256": sha256_file(result_path),
        "total_windows": result.get("total_windows"),
        "match_location_count": result.get("match_location_count"),
        "unique_passage_count": result.get("unique_passage_count"),
        "decision": result.get("decision"),
    }
    Path(verification_path).write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("lock", type=Path)
    parser.add_argument("result", type=Path)
    parser.add_argument("verification", type=Path)
    parser.add_argument("--no-recompute", action="store_true")
    args = parser.parse_args()
    record = verify(args.lock, args.result, args.verification, not args.no_recompute)
    print(json.dumps(record, indent=2, sort_keys=True))
    return 0 if record["consistent"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
