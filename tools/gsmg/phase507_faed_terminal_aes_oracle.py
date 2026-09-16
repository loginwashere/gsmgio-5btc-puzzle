#!/usr/bin/env python3
"""Locked AES-oracle pass over exact Phase 489/504/506 FAED terminals."""
from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path

import cb_common
import phase480_p32_address_password_audit as oracle


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
PROTOCOL = (REPO_ROOT / "doc" / "Brainstorms" /
            "2026-09-15 - Phase 507 FAED Terminal AES Oracle.md")
MANIFEST = SCRIPT_DIR / "phase507_candidate_manifest.json"
LOCK = SCRIPT_DIR / "phase507_execution_lock.json"
RESULT = SCRIPT_DIR / "phase507_result.json"
HITS = SCRIPT_DIR / "phase507_sensitive_hits.jsonl"
TARGETS = ("SALPH", "COSMIC", "P32TRAILING")
EXPECTED_SOURCE_COUNTS = {
    "phase489_width30_gi": 4,
    "phase504_width19_gi_unrestricted": 5,
    "phase506_rank1_ei": 7,
    "phase506_rank2_ac": 7,
    "phase506_rank3_bi": 8,
    "phase506_rank4_dh": 4,
    "phase506_rank5_fi": 8,
}
SOURCES = {
    "phase489_width30_gi": SCRIPT_DIR / "phase489_faed_width30_gi_result.json",
    "phase504_width19_gi_unrestricted": (
        REPO_ROOT / "_work/phase504/real_gi_w19_unrestricted/phase504_real_result.json"),
    "phase506_rank1_ei": REPO_ROOT / "_work/phase506b/ranked_pair_29_ei/phase506b_real_result.json",
    "phase506_rank2_ac": REPO_ROOT / "_work/phase506b/ranked_pair_01_ac/phase506b_real_result.json",
    "phase506_rank3_bi": REPO_ROOT / "_work/phase506b/ranked_pair_14_bi/phase506b_real_result.json",
    "phase506_rank4_dh": REPO_ROOT / "_work/phase506b/ranked_pair_24_dh/phase506b_real_result.json",
    "phase506_rank5_fi": REPO_ROOT / "_work/phase506b/ranked_pair_32_fi/phase506b_real_result.json",
}


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
    by_bytes: dict[bytes, dict] = {}
    source_hashes = {}
    for label, path in SOURCES.items():
        payload = json.loads(path.read_text())
        candidates = payload.get("final_candidates")
        if not isinstance(candidates, list) or len(candidates) != EXPECTED_SOURCE_COUNTS[label]:
            raise AssertionError(f"{label} candidate count changed")
        source_hashes[label] = sha256_file(path)
        for ordinal, record in enumerate(candidates, 1):
            plaintext = record.get("plaintext")
            if (not isinstance(plaintext, str) or not plaintext or
                    not plaintext.isascii() or not plaintext.isalpha() or
                    not plaintext.isupper()):
                raise AssertionError(f"{label} candidate is not uppercase ASCII")
            raw = plaintext.encode("ascii")
            provenance = {
                "source": label,
                "source_ordinal": ordinal,
                "recorded_final_rank": record.get("final_rank"),
                "normalized_score": record.get("normalized_score"),
            }
            if raw not in by_bytes:
                password = hashlib.sha256(raw).hexdigest().encode("ascii")
                by_bytes[raw] = {
                    "preimage_b64": base64.b64encode(raw).decode("ascii"),
                    "preimage_length": len(raw),
                    "preimage_sha256": hashlib.sha256(raw).hexdigest(),
                    "password_b64": base64.b64encode(password).decode("ascii"),
                    "password_sha256": hashlib.sha256(password).hexdigest(),
                    "provenance": [],
                }
            by_bytes[raw]["provenance"].append(provenance)
    rows = sorted(by_bytes.values(), key=lambda row: row["preimage_sha256"])
    for index, row in enumerate(rows):
        row["candidate_id"] = f"terminal_{index:02d}"
        row["provenance"] = sorted(
            row["provenance"], key=lambda p: (p["source"], p["source_ordinal"]))
    if len(rows) != 43:
        raise AssertionError(f"expected 43 unique candidates, found {len(rows)}")
    return rows, source_hashes


def manifest_payload() -> dict:
    rows, hashes = source_candidates()
    return {
        "phase": 507,
        "status": "candidate_manifest_no_oracle_run",
        "candidate_count": len(rows),
        "source_record_count": sum(EXPECTED_SOURCE_COUNTS.values()),
        "source_artifacts_sha256": hashes,
        "transformation": "sha256(preimage).hexdigest().encode('ascii')",
        "targets": list(TARGETS),
        "planned_decryptions": len(rows) * len(TARGETS),
        "candidates": rows,
    }


def validate_manifest() -> dict:
    if not MANIFEST.is_file():
        raise RuntimeError("Phase-507 candidate manifest is absent")
    actual = json.loads(MANIFEST.read_text())
    if actual != manifest_payload():
        raise RuntimeError("Phase-507 candidate manifest mismatch")
    return actual


def target_identity(name: str) -> dict:
    salt, ciphertext = cb_common.BLOBS[name]
    return {
        "salt_hex": salt.hex(),
        "ciphertext_length": len(ciphertext),
        "ciphertext_sha256": hashlib.sha256(ciphertext).hexdigest(),
    }


def lock_payload() -> dict:
    manifest = validate_manifest()
    files = {
        "protocol": PROTOCOL,
        "runner": Path(__file__),
        "manifest": MANIFEST,
        "oracle": Path(oracle.__file__),
        "cb_common": Path(cb_common.__file__),
        "data": SCRIPT_DIR / "data.py",
    }
    return {
        "phase": 507,
        "status": "locked_before_real_aes_oracle",
        "files_sha256": {name: sha256_file(path) for name, path in files.items()},
        "source_artifacts_sha256": manifest["source_artifacts_sha256"],
        "candidate_count": 43,
        "targets": {name: target_identity(name) for name in TARGETS},
        "planned_decryptions": 129,
        "cryptography_version": importlib.metadata.version("cryptography"),
        "crypto_profile": "legacy-evp-bytes-to-key-sha256/aes-256-cbc/pkcs7",
        "password_construction": manifest["transformation"],
        "validators": {
            "strong_text_minimum_z": cb_common.PRINTABLE_Z_STRONG_THRESHOLD,
            "structural_binary": "aes/block16/pad16/body64",
            "padding_alone_promotes": False,
        },
        "prohibitions": {
            "urlblob": True,
            "candidate_mutations": True,
            "alternate_kdf_or_cipher": True,
            "repeat_after_result_inspection": True,
        },
    }


def verify_lock() -> dict:
    if not LOCK.is_file():
        raise RuntimeError("Phase-507 execution lock is absent")
    actual = json.loads(LOCK.read_text())
    if actual != lock_payload():
        raise RuntimeError("Phase-507 execution lock mismatch")
    return actual


def self_test() -> dict:
    rows, _ = source_candidates()
    for row in rows:
        raw = base64.b64decode(row["preimage_b64"], validate=True)
        password = hashlib.sha256(raw).hexdigest().encode("ascii")
        if base64.b64decode(row["password_b64"], validate=True) != password:
            raise AssertionError("password derivation changed")
    password = b"phase507-positive-control"
    salt = b"P507TEST"
    body = b"Exact consumer validation must distinguish a planted plaintext."
    ciphertext = oracle.encrypt_for_test(body, password, salt)
    classified = oracle.classify_padded(
        oracle.decrypt_padded(password, salt, ciphertext))
    if not classified["promoted"]:
        raise AssertionError("positive control failed")
    if tuple(TARGETS) != ("SALPH", "COSMIC", "P32TRAILING"):
        raise AssertionError("target set changed")
    return {"candidate_count": len(rows), "planned_decryptions": 129,
            "positive_control": True}


def run() -> dict:
    locked = verify_lock()
    if RESULT.exists() or HITS.exists():
        raise FileExistsError("refusing to overwrite or repeat Phase-507 oracle")
    manifest = validate_manifest()
    attempts, sensitive = [], []
    for row in manifest["candidates"]:
        password = base64.b64decode(row["password_b64"], validate=True)
        for target in TARGETS:
            salt, ciphertext = cb_common.BLOBS[target]
            padded = oracle.decrypt_padded(password, salt, ciphertext)
            classification = oracle.classify_padded(padded)
            public = {
                "candidate_id": row["candidate_id"],
                "preimage_sha256": row["preimage_sha256"],
                "password_sha256": row["password_sha256"],
                "target": target,
                **classification,
            }
            attempts.append(public)
            if classification["promoted"]:
                body, _ = oracle.strict_pkcs7_unpad(padded)
                sensitive.append({
                    **public,
                    "password_b64": row["password_b64"],
                    "plaintext_b64": base64.b64encode(body).decode("ascii"),
                })
    if sensitive:
        descriptor = os.open(HITS, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            for row in sensitive:
                handle.write(json.dumps(row, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
    result = {
        "phase": 507,
        "status": "locked_oracle_run_complete",
        "execution_lock_sha256": sha256_file(LOCK),
        "candidate_count": manifest["candidate_count"],
        "targets": list(TARGETS),
        "decryptions": len(attempts),
        "promoted_count": len(sensitive),
        "padding_valid_diagnostic_count": sum(
            attempt["padding_valid"] for attempt in attempts),
        "attempts": attempts,
        "verdict": ("positive_requires_sensitive_review" if sensitive
                    else "bounded_negative"),
    }
    if len(attempts) != locked["planned_decryptions"]:
        raise AssertionError("Phase-507 decryption count changed")
    atomic_json(RESULT, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--write-manifest", action="store_true")
    group.add_argument("--print-lock", action="store_true")
    group.add_argument("--verify-lock", action="store_true")
    group.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        result = self_test()
    elif args.write_manifest:
        if MANIFEST.exists():
            raise FileExistsError("refusing to overwrite Phase-507 manifest")
        atomic_json(MANIFEST, manifest_payload())
        result = {"manifest_sha256": sha256_file(MANIFEST)}
    elif args.print_lock:
        result = lock_payload()
    elif args.verify_lock:
        result = verify_lock()
    else:
        result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
