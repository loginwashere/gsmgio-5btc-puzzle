#!/usr/bin/env python3
"""Locked Phase 480B test of four closed-system address constructions."""

from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.metadata
import json
import os
import sys
from pathlib import Path

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

import cb_common  # noqa: E402
from data import PHASE32_BLOB_B64, PHASE32_PASSWORD, PHASE32_PLAINTEXT_PREFIX  # noqa: E402
from phase480_address_novelty_comparator import proposed_preimages  # noqa: E402


PHASE = 480
PROTOCOL = REPO_ROOT / "doc/Brainstorms/2026-09-06 - Phase 480 Closed-System Address Construction Protocol.md"
COMPARATOR = SCRIPT_DIR / "phase480_address_novelty_comparator.py"
NOVELTY_RESULT = SCRIPT_DIR / "phase480_address_novelty_result.json"
DEFAULT_LOCK = SCRIPT_DIR / "phase480_execution_lock.json"
DEFAULT_RESULT = SCRIPT_DIR / "phase480_result.json"
DEFAULT_HITS = SCRIPT_DIR / "phase480_sensitive_hits.jsonl"
CHAT_EXPORT_SHA256 = "645da52bce92e3de7fc29b77b21f0f946411c706f0fba805c6b84330f999cc8c"
EXPECTED_NOVELTY_RESULT_SHA256 = "d084155c6bbd2afb46d33d49b6ea5906d8d036a648e4c9d42da88f03b08f29f5"
EXPECTED_LEVELS = ("sha256_hex_password", "preimage")
EXPECTED_CONSTRUCTIONS = (
    "prize_then_halving",
    "halving_then_prize",
    "banner_prize_halving",
    "banner_halving_prize",
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def material_rows() -> list[dict]:
    rows = []
    preimages = proposed_preimages()
    if tuple(preimages) != EXPECTED_CONSTRUCTIONS:
        raise AssertionError("construction order or set drift")
    for construction, preimage in preimages.items():
        materials = {
            "preimage": preimage,
            "sha256_hex_password": hashlib.sha256(preimage).hexdigest().encode("ascii"),
        }
        for level in EXPECTED_LEVELS:
            material = materials[level]
            rows.append({
                "construction": construction,
                "level": level,
                "tier": "primary" if level == "sha256_hex_password" else "representation_control",
                "length": len(material),
                "material_b64": base64.b64encode(material).decode("ascii"),
                "material_sha256": hashlib.sha256(material).hexdigest(),
            })
    return rows


def strict_pkcs7_unpad(padded: bytes) -> tuple[bytes | None, int | None]:
    if not padded:
        return None, None
    pad = padded[-1]
    if not (1 <= pad <= 16 and padded[-pad:] == bytes((pad,)) * pad):
        return None, None
    return padded[:-pad], pad


def decrypt_padded(password: bytes, salt: bytes, ciphertext: bytes) -> bytes:
    key, iv = cb_common.evp_bytes_to_key(password, salt, "sha256", 32, 16)
    decryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
    return decryptor.update(ciphertext) + decryptor.finalize()


def classify_padded(padded: bytes) -> dict:
    body, pad = strict_pkcs7_unpad(padded)
    if body is None:
        return {
            "padding_valid": False,
            "padding_length": None,
            "plaintext_length": None,
            "printable_z": None,
            "strong_text": False,
            "structural_binary_64": False,
            "promoted": False,
        }
    z_score = cb_common.printable_z_score(body)
    strong_text = z_score >= cb_common.PRINTABLE_Z_STRONG_THRESHOLD
    structural = cb_common.is_structural_binary_plaintext("aes", 16, pad, body)
    return {
        "padding_valid": True,
        "padding_length": pad,
        "plaintext_length": len(body),
        "printable_z": round(z_score, 6),
        "strong_text": strong_text,
        "structural_binary_64": structural,
        "promoted": strong_text or structural,
        "plaintext_sha256": hashlib.sha256(body).hexdigest(),
    }


def encrypt_for_test(body: bytes, password: bytes, salt: bytes) -> bytes:
    pad = 16 - len(body) % 16
    padded = body + bytes((pad,)) * pad
    key, iv = cb_common.evp_bytes_to_key(password, salt, "sha256", 32, 16)
    encryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    return encryptor.update(padded) + encryptor.finalize()


def self_test() -> bool:
    rows = material_rows()
    assert len(rows) == 8
    assert len({row["material_b64"] for row in rows}) == 8
    assert sum(row["tier"] == "primary" for row in rows) == 4
    assert sum(row["tier"] == "representation_control" for row in rows) == 4
    assert [len(value) for value in proposed_preimages().values()] == [68, 68, 93, 93]

    novelty = json.loads(NOVELTY_RESULT.read_text(encoding="utf-8"))
    assert sha256_file(NOVELTY_RESULT) == EXPECTED_NOVELTY_RESULT_SHA256
    assert novelty["target_count"] == 8
    assert novelty["matched_target_count"] == 0
    assert novelty["oracle_calls"] == 0
    novelty_materials = {row["material_b64"] for row in novelty["targets"]}
    assert novelty_materials == {row["material_b64"] for row in rows}

    # The selected profile must reproduce the solved Phase 3.2 boundary.
    phase32_salt, phase32_ct = cb_common._load_blob(PHASE32_BLOB_B64)
    phase32_padded = decrypt_padded(PHASE32_PASSWORD.encode("ascii"), phase32_salt, phase32_ct)
    phase32_body, _ = strict_pkcs7_unpad(phase32_padded)
    assert phase32_body is not None
    assert phase32_body.startswith(PHASE32_PLAINTEXT_PREFIX.encode("ascii"))
    assert classify_padded(phase32_padded)["strong_text"] is True

    password = b"phase480-positive-control"
    salt = b"P480TEST"
    text = b"Closed system evidence should select the construction before any oracle run."
    text_class = classify_padded(decrypt_padded(password, salt, encrypt_for_test(text, password, salt)))
    assert text_class["strong_text"] and text_class["promoted"]

    binary = hashlib.shake_256(b"phase480-binary-control").digest(64)
    binary_class = classify_padded(decrypt_padded(password, salt, encrypt_for_test(binary, password, salt)))
    assert binary_class["padding_length"] == 16
    assert binary_class["structural_binary_64"] and binary_class["promoted"]

    assert classify_padded(b"X" * 80)["promoted"] is False
    weak_body = bytes(range(63))
    weak_padded = weak_body + b"\x01"
    weak_class = classify_padded(weak_padded)
    assert weak_class["padding_valid"] and not weak_class["promoted"]

    assert set(cb_common.BLOBS) >= {"P32TRAILING"}
    salt_real, ct_real = cb_common.BLOBS["P32TRAILING"]
    assert len(salt_real) == 8 and len(ct_real) == 80
    return True


def lock_payload() -> dict:
    rows = material_rows()
    salt, ciphertext = cb_common.BLOBS["P32TRAILING"]
    tracked = {
        "protocol": PROTOCOL,
        "audit_script": Path(__file__),
        "verifier": SCRIPT_DIR / "phase480_verify_run.py",
        "novelty_comparator": COMPARATOR,
        "novelty_result": NOVELTY_RESULT,
        "cb_common": SCRIPT_DIR / "cb_common.py",
        "first_hint_hash_audit": SCRIPT_DIR / "first_hint_hash_audit.py",
        "data": SCRIPT_DIR / "data.py",
    }
    manifest_digest = hashlib.sha256(
        json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "phase": PHASE,
        "status": "locked-before-real-run",
        "files_sha256": {name: sha256_file(path) for name, path in tracked.items()},
        "chat_export_sha256": CHAT_EXPORT_SHA256,
        "chat_message": {
            "file_line": 67235,
            "author": "Anton (@homeless_phd)",
            "timestamp": "2024-04-20 12:51 UTC",
            "provenance_tier": "unauthenticated-community-motivation",
        },
        "cryptography_version": importlib.metadata.version("cryptography"),
        "material_count": len(rows),
        "primary_count": 4,
        "representation_control_count": 4,
        "material_manifest_sha256": manifest_digest,
        "materials": rows,
        "target_blob": "P32TRAILING",
        "p32_salt_hex": salt.hex(),
        "p32_ciphertext_length": len(ciphertext),
        "p32_ciphertext_sha256": hashlib.sha256(ciphertext).hexdigest(),
        "crypto_profile": "legacy-evp-bytes-to-key-sha256/aes-256-cbc/pkcs7",
        "validators": {
            "strong_text_minimum_z": cb_common.PRINTABLE_Z_STRONG_THRESHOLD,
            "structural_binary": "aes/block16/pad16/body64",
            "padding_alone_promotes": False,
        },
        "planned_decryptions": 8,
    }


def write_json_atomic(path: Path, value: dict, mode: int = 0o644) -> None:
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
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


def verify_lock(lock_path: Path) -> dict:
    locked = json.loads(Path(lock_path).read_text(encoding="utf-8"))
    if locked != lock_payload():
        raise RuntimeError("execution lock does not match current protocol/code/inputs")
    return locked


def issue_lock(lock_path: Path) -> dict:
    self_test()
    payload = lock_payload()
    write_json_atomic(lock_path, payload)
    verify_lock(lock_path)
    return payload


def run(lock_path: Path, result_path: Path, hits_path: Path) -> dict:
    lock = verify_lock(lock_path)
    if Path(hits_path).exists():
        raise FileExistsError(f"refusing ambiguous run with existing sensitive file: {hits_path}")
    salt, ciphertext = cb_common.BLOBS["P32TRAILING"]
    attempts = []
    sensitive = []
    for row in lock["materials"]:
        password = base64.b64decode(row["material_b64"], validate=True)
        padded = decrypt_padded(password, salt, ciphertext)
        classification = classify_padded(padded)
        public = {
            "construction": row["construction"],
            "level": row["level"],
            "tier": row["tier"],
            "password_sha256": row["material_sha256"],
            **classification,
        }
        attempts.append(public)
        if classification["promoted"]:
            body, _ = strict_pkcs7_unpad(padded)
            sensitive.append({
                **public,
                "password_b64": row["material_b64"],
                "plaintext_b64": base64.b64encode(body).decode("ascii"),
            })

    if sensitive:
        descriptor = os.open(hits_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            for row in sensitive:
                handle.write(json.dumps(row, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    result = {
        "phase": PHASE,
        "lock_sha256": sha256_file(lock_path),
        "target_blob": lock["target_blob"],
        "material_count": lock["material_count"],
        "decryptions": len(attempts),
        "primary_promoted_count": sum(row["promoted"] and row["tier"] == "primary" for row in attempts),
        "representation_control_promoted_count": sum(
            row["promoted"] and row["tier"] == "representation_control" for row in attempts
        ),
        "padding_valid_diagnostic_count": sum(row["padding_valid"] for row in attempts),
        "attempts": attempts,
    }
    promoted = result["primary_promoted_count"] + result["representation_control_promoted_count"]
    result["verdict"] = "positive_requires_sensitive_review" if promoted else "bounded_negative"
    write_json_atomic(result_path, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--self-test", action="store_true")
    action.add_argument("--issue-lock", action="store_true")
    action.add_argument("--run", action="store_true")
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    parser.add_argument("--result", type=Path, default=DEFAULT_RESULT)
    parser.add_argument("--hits", type=Path, default=DEFAULT_HITS)
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("[*] Phase 480 self-test passed")
    elif args.issue_lock:
        print(json.dumps(issue_lock(args.lock), indent=2, sort_keys=True))
    else:
        print(json.dumps(run(args.lock, args.result, args.hits), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
