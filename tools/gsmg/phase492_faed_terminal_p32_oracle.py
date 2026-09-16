#!/usr/bin/env python3
"""Locked Phase-492 P32 oracle for ten saved FAED terminal plaintexts."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path

import cb_common
import phase480_p32_address_password_audit as oracle


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
PROTOCOL = (REPO_ROOT / "doc" / "Brainstorms" /
            "2026-09-13 - Phase 492 FAED Terminal P32 Oracle Protocol.md")
WIDTH30_RESULT = SCRIPT_DIR / "phase489_faed_width30_gi_result.json"
WIDTH19_RESULT = REPO_ROOT / "_work" / "phase490" / "real_gi_w19" / "phase490_real_result.json"
MANIFEST = SCRIPT_DIR / "phase492_faed_terminal_manifest.json"
LOCK = SCRIPT_DIR / "phase492_execution_lock.json"
RESULT = SCRIPT_DIR / "phase492_result.json"
HITS = SCRIPT_DIR / "phase492_sensitive_hits.jsonl"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_json(path: Path, value: dict, mode: int = 0o644) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def source_candidates() -> tuple[list[dict], dict]:
    sources = {
        "width30": WIDTH30_RESULT,
        "width19": WIDTH19_RESULT,
    }
    rows = []
    expected = {"width30": 4, "width19": 6}
    for label, path in sources.items():
        payload = json.loads(path.read_text())
        candidates = payload["final_candidates"]
        if len(candidates) != expected[label]:
            raise AssertionError(f"{label} candidate count changed")
        width = 30 if label == "width30" else 19
        for record in candidates:
            plaintext = record["plaintext"]
            if not plaintext or not plaintext.isascii() or not plaintext.isalpha() or not plaintext.isupper():
                raise AssertionError("candidate is not exact nonempty uppercase ASCII")
            preimage = plaintext.encode("ascii")
            password = hashlib.sha256(preimage).hexdigest().encode("ascii")
            rows.append({
                "candidate_id": f"{label}_final_rank_{record['final_rank']}",
                "width": width, "final_rank": record["final_rank"],
                "normalized_score": record["normalized_score"],
                "preimage_length": len(preimage),
                "preimage_b64": base64.b64encode(preimage).decode("ascii"),
                "preimage_sha256": hashlib.sha256(preimage).hexdigest(),
                "password_b64": base64.b64encode(password).decode("ascii"),
                "password_sha256": hashlib.sha256(password).hexdigest(),
            })
    if len(rows) != 10 or len({row["preimage_b64"] for row in rows}) != 10:
        raise AssertionError("candidate universe is not ten unique plaintexts")
    return rows, {label: sha256_file(path) for label, path in sources.items()}


def manifest_payload() -> dict:
    rows, source_hashes = source_candidates()
    return {
        "phase": 492, "status": "candidate_manifest_no_oracle_run",
        "candidate_count": len(rows),
        "source_artifacts_sha256": source_hashes,
        "transformation": "sha256(preimage).hexdigest().encode('ascii')",
        "candidates": rows,
    }


def validate_manifest() -> dict:
    manifest = json.loads(MANIFEST.read_text())
    if manifest != manifest_payload():
        raise RuntimeError("candidate manifest mismatch")
    return manifest


def lock_payload() -> dict:
    manifest = validate_manifest()
    salt, ciphertext = cb_common.BLOBS["P32TRAILING"]
    files = {
        "protocol": PROTOCOL, "runner": Path(__file__), "manifest": MANIFEST,
        "phase480_oracle": Path(oracle.__file__),
        "cb_common": Path(cb_common.__file__), "data": SCRIPT_DIR / "data.py",
    }
    return {
        "phase": 492, "status": "locked_before_real_p32_oracle",
        "files_sha256": {name: sha256_file(path) for name, path in files.items()},
        "source_artifacts_sha256": manifest["source_artifacts_sha256"],
        "candidate_count": 10, "planned_decryptions": 10,
        "target_blob": "P32TRAILING", "salt_hex": salt.hex(),
        "ciphertext_length": len(ciphertext),
        "ciphertext_sha256": hashlib.sha256(ciphertext).hexdigest(),
        "crypto_profile": "legacy-evp-bytes-to-key-sha256/aes-256-cbc/pkcs7",
        "validators": {
            "strong_text_minimum_z": cb_common.PRINTABLE_Z_STRONG_THRESHOLD,
            "structural_binary": "aes/block16/pad16/body64",
            "padding_alone_promotes": False,
        },
    }


def verify_lock() -> dict:
    locked = json.loads(LOCK.read_text())
    if locked != lock_payload():
        raise RuntimeError("execution lock mismatch")
    return locked


def self_test() -> dict:
    rows, _ = source_candidates()
    for row in rows:
        preimage = base64.b64decode(row["preimage_b64"], validate=True)
        expected = hashlib.sha256(preimage).hexdigest().encode("ascii")
        if base64.b64decode(row["password_b64"], validate=True) != expected:
            raise AssertionError("Phase-410 password transformation changed")
    password = b"phase492-positive-control"
    salt = b"P492TEST"
    body = b"A positive control for the exact locked P32 oracle profile."
    ciphertext = oracle.encrypt_for_test(body, password, salt)
    classified = oracle.classify_padded(oracle.decrypt_padded(password, salt, ciphertext))
    if not classified["promoted"]:
        raise AssertionError("positive control did not promote")
    return {"candidate_count": len(rows), "positive_control": True}


def run() -> dict:
    locked = verify_lock()
    if RESULT.exists() or HITS.exists():
        raise FileExistsError("refusing to overwrite or ambiguously repeat oracle run")
    manifest = validate_manifest()
    salt, ciphertext = cb_common.BLOBS["P32TRAILING"]
    attempts, sensitive = [], []
    for row in manifest["candidates"]:
        password = base64.b64decode(row["password_b64"], validate=True)
        padded = oracle.decrypt_padded(password, salt, ciphertext)
        classification = oracle.classify_padded(padded)
        public = {
            "candidate_id": row["candidate_id"],
            "preimage_sha256": row["preimage_sha256"],
            "password_sha256": row["password_sha256"],
            **classification,
        }
        attempts.append(public)
        if classification["promoted"]:
            body, _ = oracle.strict_pkcs7_unpad(padded)
            sensitive.append({
                **public, "password_b64": row["password_b64"],
                "plaintext_b64": base64.b64encode(body).decode("ascii"),
            })
    if sensitive:
        descriptor = os.open(HITS, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            for row in sensitive:
                handle.write(json.dumps(row, sort_keys=True) + "\n")
            handle.flush(); os.fsync(handle.fileno())
    result = {
        "phase": 492, "status": "locked_oracle_run_complete",
        "execution_lock_sha256": sha256_file(LOCK),
        "target_blob": locked["target_blob"], "decryptions": len(attempts),
        "promoted_count": len(sensitive),
        "padding_valid_diagnostic_count": sum(x["padding_valid"] for x in attempts),
        "attempts": attempts,
        "verdict": "positive_requires_sensitive_review" if sensitive else "bounded_negative",
    }
    atomic_json(RESULT, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--write-manifest", action="store_true")
    group.add_argument("--write-lock", action="store_true")
    group.add_argument("--verify-lock", action="store_true")
    group.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        result = self_test()
    elif args.write_manifest:
        if MANIFEST.exists():
            raise FileExistsError("refusing to overwrite candidate manifest")
        atomic_json(MANIFEST, manifest_payload())
        result = {"manifest_sha256": sha256_file(MANIFEST)}
    elif args.write_lock:
        if LOCK.exists():
            raise FileExistsError("refusing to overwrite execution lock")
        self_test(); atomic_json(LOCK, lock_payload()); result = verify_lock()
    elif args.verify_lock:
        result = verify_lock()
    else:
        result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
