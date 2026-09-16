#!/usr/bin/env python3
"""Phase 509B: exact digest-as-private-key check for 43 FAED terminals."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path

from binary_key_material_backfill import private_key_details
from first_hint_hash_audit import HALVING_ADDRESS, PRIZE_ADDRESS, SECP256K1_ORDER
import phase507_faed_terminal_aes_oracle as phase507


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
PROTOCOL = (REPO_ROOT / "doc" / "Brainstorms" /
            "2026-09-15 - Phase 509B Terminal Digest to Known Address Protocol.md")
LOCK = SCRIPT_DIR / "phase509b_execution_lock.json"
RESULT = SCRIPT_DIR / "phase509b_result.json"
HITS = SCRIPT_DIR / "phase509b_sensitive_hits.json"
TARGETS = (PRIZE_ADDRESS, HALVING_ADDRESS)


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def manifest() -> dict:
    value = phase507.validate_manifest()
    if value.get("candidate_count") != 43 or len(value.get("candidates", [])) != 43:
        raise RuntimeError("Phase-507 terminal universe changed")
    return value


def terminal_digest(row: dict) -> bytes:
    terminal = base64.b64decode(row["preimage_b64"], validate=True)
    digest = hashlib.sha256(terminal).digest()
    if digest.hex() != row["preimage_sha256"]:
        raise RuntimeError("Phase-507 terminal digest mismatch")
    return digest


def derived_addresses(key: bytes) -> dict[str, str] | None:
    if len(key) != 32 or not 1 <= int.from_bytes(key, "big") < SECP256K1_ORDER:
        return None
    details = private_key_details(key)
    if details is None:
        return None
    return {kind: details[kind]["address"]
            for kind in ("compressed", "uncompressed")}


def lock_payload() -> dict:
    rows = manifest()["candidates"]
    # Validate input digests, but do not invoke the address consumer pre-lock.
    for row in rows:
        terminal_digest(row)
    return {
        "phase": "509B",
        "status": "locked_before_address_derivation",
        "files_sha256": {
            "protocol": sha(PROTOCOL),
            "runner": sha(Path(__file__)),
            "phase507_manifest": sha(phase507.MANIFEST),
            "phase507_runner": sha(Path(phase507.__file__)),
            "binary_key_material_backfill": sha(Path(private_key_details.__code__.co_filename)),
        },
        "candidate_count": 43,
        "transformation": "SHA256(terminal).digest()",
        "targets": list(TARGETS),
        "public_key_encodings": ["compressed", "uncompressed"],
        "derived_address_count": 86,
        "exact_comparison_count": 172,
        "acceptance": "exact derived P2PKH address equality only",
        "prohibitions": [
            "candidate mutation", "alternate or double hash", "substring",
            "scalar algebra", "derived-neighbor target", "AES query",
            "Bloom filter", "network request",
        ],
    }


def verify_lock() -> dict:
    if not LOCK.is_file():
        raise RuntimeError("Phase-509B execution lock is absent")
    actual = json.loads(LOCK.read_text())
    if actual != lock_payload():
        raise RuntimeError("Phase-509B execution lock mismatch")
    return actual


def self_test() -> dict:
    rows = manifest()["candidates"]
    if len({terminal_digest(row) for row in rows}) != 43:
        raise AssertionError("terminal digests are not unique")
    key = (1).to_bytes(32, "big")
    addresses = derived_addresses(key)
    if addresses is None:
        raise AssertionError("valid scalar was rejected")
    if addresses["compressed"] != private_key_details(key)["compressed"]["address"]:
        raise AssertionError("address derivation disagrees with project primitive")
    if derived_addresses(bytes(32)) is not None:
        raise AssertionError("zero scalar was accepted")
    return {"self_test": "pass", "candidate_count": 43,
            "derived_addresses": 86, "exact_comparisons": 172}


def run() -> dict:
    locked = verify_lock()
    if RESULT.exists() or HITS.exists():
        raise FileExistsError("refusing to overwrite or repeat Phase-509B")
    attempts = []
    hits = []
    for row in manifest()["candidates"]:
        digest = terminal_digest(row)
        addresses = derived_addresses(digest)
        record = {
            "candidate_id": row["candidate_id"],
            "terminal_sha256": row["preimage_sha256"],
            "scalar_valid": addresses is not None,
            "addresses": addresses,
            "matched_targets": (sorted(set(addresses.values()) & set(TARGETS))
                                if addresses else []),
        }
        attempts.append(record)
        if record["matched_targets"]:
            hits.append(record)
    if hits:
        descriptor = os.open(HITS, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump({"phase": "509B", "hits": hits}, handle,
                      indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
    result = {
        "phase": "509B",
        "status": "locked_address_oracle_complete",
        "execution_lock_sha256": sha(LOCK),
        "candidate_count": len(attempts),
        "derived_address_count": sum(
            len(row["addresses"] or {}) for row in attempts),
        "exact_comparison_count": locked["exact_comparison_count"],
        "scalar_invalid_count": sum(not row["scalar_valid"] for row in attempts),
        "hit_count": len(hits),
        "attempts": attempts,
        "verdict": "exact_hit_requires_review" if hits else "bounded_negative",
    }
    phase507.atomic_json(RESULT, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--print-lock", action="store_true")
    group.add_argument("--verify-lock", action="store_true")
    group.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        value = self_test()
    elif args.print_lock:
        value = lock_payload()
    elif args.verify_lock:
        value = verify_lock()
    else:
        value = run()
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

