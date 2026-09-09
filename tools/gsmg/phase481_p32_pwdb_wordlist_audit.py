#!/usr/bin/env python3
"""Locked Phase 481 test of a 10,000,000-entry external password wordlist
against P32TRAILING, under the sole Phase-410 crypto profile.

User-directed continuation of Phase 480: same target, same crypto profile,
same frozen validators (strict PKCS#7 + strong-text/structural-binary
promotion) -- only the candidate universe changes, from Phase 480's four
derived address constructions to a fixed, hash-pinned external wordlist file.
See doc/Brainstorms/2026-09-06 - Phase 481 P32TRAILING Pwdb Wordlist Password
Audit Protocol.md.

Unlike Phase 480 (8 fixed materials), this candidate universe is 10,000,000
lines, so the result records aggregate counts rather than one record per
attempt -- storing 10,000,000 attempt records is neither reviewable nor a
useful artifact. Any promoted or weak-tier body is still recorded in full.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.metadata
import json
import os
import sys
import time
from pathlib import Path

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

import cb_common  # noqa: E402
from data import PHASE32_BLOB_B64, PHASE32_PASSWORD, PHASE32_PLAINTEXT_PREFIX  # noqa: E402

PHASE = 481
PROTOCOL = (
    REPO_ROOT
    / "doc/Brainstorms/2026-09-06 - Phase 481 P32TRAILING Pwdb Wordlist Password Audit Protocol.md"
)
DEFAULT_LOCK = SCRIPT_DIR / "phase481_execution_lock.json"
DEFAULT_RESULT = SCRIPT_DIR / "phase481_result.json"
DEFAULT_HITS = SCRIPT_DIR / "phase481_sensitive_hits.jsonl"
DEFAULT_WEAK = SCRIPT_DIR / "phase481_weak_candidates.jsonl"

WORDLIST_PATH = Path(
    "/home/loginwashere/projects/key-seeker/wordlists/Pwdb_top-10000000.txt"
)
EXPECTED_WORDLIST_SHA256 = (
    "18dc49ca32b62455a61e3398f4ab9f93eb700ff142fa0d4b9fd11a727f3b80e4"
)
EXPECTED_LINE_COUNT = 10_000_000
EXPECTED_BLANK_LINES = 0
EXPECTED_DUPLICATE_LINES = 0

TARGET_BLOB = "P32TRAILING"
CRYPTO_PROFILE = "legacy-evp-bytes-to-key-sha256/aes-256-cbc/pkcs7"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def wordlist_stats(path: Path) -> dict:
    """Single streaming pass: content hash, line count, blank-line count, and
    exact-duplicate-line count. All four are load-bearing controls, not just
    the hash -- a byte-identical file with reordered/deduplicated lines would
    keep an unrelated hash meaningless without this."""
    digest = hashlib.sha256()
    seen = set()
    line_count = 0
    blank_count = 0
    duplicate_count = 0
    with open(path, "rb") as handle:
        for raw_line in handle:
            digest.update(raw_line)
            line_count += 1
            candidate = raw_line.rstrip(b"\n")
            if not candidate:
                blank_count += 1
            if candidate in seen:
                duplicate_count += 1
            else:
                seen.add(candidate)
    return {
        "sha256": digest.hexdigest(),
        "line_count": line_count,
        "blank_lines": blank_count,
        "duplicate_lines": duplicate_count,
        "unique_lines": len(seen),
    }


def iter_candidates(path: Path):
    with open(path, "rb") as handle:
        for raw_line in handle:
            yield raw_line.rstrip(b"\n")


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
    if not WORDLIST_PATH.is_file():
        raise AssertionError(f"wordlist missing: {WORDLIST_PATH}")
    stats = wordlist_stats(WORDLIST_PATH)
    assert stats["sha256"] == EXPECTED_WORDLIST_SHA256, stats
    assert stats["line_count"] == EXPECTED_LINE_COUNT, stats
    assert stats["blank_lines"] == EXPECTED_BLANK_LINES, stats
    assert stats["duplicate_lines"] == EXPECTED_DUPLICATE_LINES, stats

    # The selected profile must reproduce the solved Phase 3.2 boundary.
    phase32_salt, phase32_ct = cb_common._load_blob(PHASE32_BLOB_B64)
    phase32_padded = decrypt_padded(PHASE32_PASSWORD.encode("ascii"), phase32_salt, phase32_ct)
    phase32_body, _ = strict_pkcs7_unpad(phase32_padded)
    assert phase32_body is not None
    assert phase32_body.startswith(PHASE32_PLAINTEXT_PREFIX.encode("ascii"))
    assert classify_padded(phase32_padded)["strong_text"] is True

    password = b"phase481-positive-control"
    salt = b"P481TEST"
    text = b"Closed-profile evidence should select the candidate before any oracle run."
    text_class = classify_padded(decrypt_padded(password, salt, encrypt_for_test(text, password, salt)))
    assert text_class["strong_text"] and text_class["promoted"]

    binary = hashlib.shake_256(b"phase481-binary-control").digest(64)
    binary_class = classify_padded(decrypt_padded(password, salt, encrypt_for_test(binary, password, salt)))
    assert binary_class["padding_length"] == 16
    assert binary_class["structural_binary_64"] and binary_class["promoted"]

    assert classify_padded(b"X" * 80)["promoted"] is False
    weak_body = bytes(range(63))
    weak_padded = weak_body + b"\x01"
    weak_class = classify_padded(weak_padded)
    assert weak_class["padding_valid"] and not weak_class["promoted"]

    assert set(cb_common.BLOBS) >= {TARGET_BLOB}
    salt_real, ct_real = cb_common.BLOBS[TARGET_BLOB]
    assert len(salt_real) == 8 and len(ct_real) == 80

    # iter_candidates preserves whitespace-bearing lines byte-for-byte,
    # stripping only the trailing newline terminator.
    import tempfile

    with tempfile.TemporaryDirectory() as directory:
        sample = Path(directory) / "sample.txt"
        sample.write_bytes(b"abc\n  spaced  \nlast-no-newline")
        assert list(iter_candidates(sample)) == [b"abc", b"  spaced  ", b"last-no-newline"]

    return True


def lock_payload() -> dict:
    stats = wordlist_stats(WORDLIST_PATH)
    salt, ciphertext = cb_common.BLOBS[TARGET_BLOB]
    tracked = {
        "protocol": PROTOCOL,
        "audit_script": Path(__file__),
        "verifier": SCRIPT_DIR / "phase481_verify_run.py",
        "cb_common": SCRIPT_DIR / "cb_common.py",
        "data": SCRIPT_DIR / "data.py",
    }
    return {
        "phase": PHASE,
        "status": "locked-before-real-run",
        "files_sha256": {name: sha256_file(path) for name, path in tracked.items()},
        "cryptography_version": importlib.metadata.version("cryptography"),
        "wordlist_path": str(WORDLIST_PATH),
        "wordlist_sha256": stats["sha256"],
        "wordlist_line_count": stats["line_count"],
        "wordlist_blank_lines": stats["blank_lines"],
        "wordlist_duplicate_lines": stats["duplicate_lines"],
        "target_blob": TARGET_BLOB,
        "p32_salt_hex": salt.hex(),
        "p32_ciphertext_length": len(ciphertext),
        "p32_ciphertext_sha256": hashlib.sha256(ciphertext).hexdigest(),
        "crypto_profile": CRYPTO_PROFILE,
        "validators": {
            "strong_text_minimum_z": cb_common.PRINTABLE_Z_STRONG_THRESHOLD,
            "weak_text_minimum_z": cb_common.PRINTABLE_Z_WEAK_THRESHOLD,
            "structural_binary": "aes/block16/pad16/body64",
            "padding_alone_promotes": False,
        },
        "planned_decryptions": stats["line_count"],
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


def run(lock_path: Path, result_path: Path, hits_path: Path, weak_path: Path,
        progress_every: int = 1_000_000) -> dict:
    lock = verify_lock(lock_path)
    if Path(hits_path).exists():
        raise FileExistsError(f"refusing ambiguous run with existing sensitive file: {hits_path}")
    if Path(weak_path).exists():
        raise FileExistsError(f"refusing ambiguous run with existing weak-candidate file: {weak_path}")

    salt, ciphertext = cb_common.BLOBS[lock["target_blob"]]
    attempted = 0
    padding_valid_count = 0
    weak_count = 0
    strong_text_promoted = 0
    structural_promoted = 0
    sensitive = []
    weak = []
    started = time.time()

    for password in iter_candidates(WORDLIST_PATH):
        attempted += 1
        padded = decrypt_padded(password, salt, ciphertext)
        classification = classify_padded(padded)
        if classification["padding_valid"]:
            padding_valid_count += 1
            if classification["promoted"]:
                body, _ = strict_pkcs7_unpad(padded)
                record = {
                    **classification,
                    "password_b64": base64.b64encode(password).decode("ascii"),
                    "password_sha256": hashlib.sha256(password).hexdigest(),
                    "plaintext_b64": base64.b64encode(body).decode("ascii"),
                }
                sensitive.append(record)
                if classification["strong_text"]:
                    strong_text_promoted += 1
                if classification["structural_binary_64"]:
                    structural_promoted += 1
            elif classification["printable_z"] is not None and (
                classification["printable_z"] >= cb_common.PRINTABLE_Z_WEAK_THRESHOLD
            ):
                weak_count += 1
                weak.append({
                    **classification,
                    "password_sha256": hashlib.sha256(password).hexdigest(),
                })
        if progress_every and attempted % progress_every == 0:
            elapsed = time.time() - started
            print(
                f"[*] {attempted}/{lock['wordlist_line_count']} "
                f"({elapsed:.1f}s, {attempted / elapsed:.0f}/s)",
                file=sys.stderr,
            )

    if attempted != lock["wordlist_line_count"]:
        raise RuntimeError(
            f"streamed {attempted} candidates but lock declares "
            f"{lock['wordlist_line_count']}"
        )

    if sensitive:
        descriptor = os.open(hits_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            for row in sensitive:
                handle.write(json.dumps(row, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    if weak:
        descriptor = os.open(weak_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            for row in weak:
                handle.write(json.dumps(row, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    promoted_count = strong_text_promoted + structural_promoted
    result = {
        "phase": PHASE,
        "lock_sha256": sha256_file(lock_path),
        "target_blob": lock["target_blob"],
        "attempted": attempted,
        "padding_valid_count": padding_valid_count,
        "weak_tier_count": weak_count,
        "strong_text_promoted_count": strong_text_promoted,
        "structural_binary_promoted_count": structural_promoted,
        "promoted_count": promoted_count,
        "elapsed_seconds": round(time.time() - started, 3),
        "verdict": "positive_requires_sensitive_review" if promoted_count else "bounded_negative",
    }
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
    parser.add_argument("--weak", type=Path, default=DEFAULT_WEAK)
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("[*] Phase 481 self-test passed")
    elif args.issue_lock:
        print(json.dumps(issue_lock(args.lock), indent=2, sort_keys=True))
    else:
        print(json.dumps(run(args.lock, args.result, args.hits, args.weak), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
