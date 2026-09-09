#!/usr/bin/env python3
"""Phase 479: exhaustive placement of two contiguous 32-byte objects in P32.

The protocol is frozen in:
doc/Brainstorms/2026-09-06 - Phase 479 P32 64-in-80 Alignment Protocol.md
"""

import argparse
import hashlib
import hmac
import importlib.metadata
import json
import os
import sys
from pathlib import Path

import coincurve
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

import cb_common  # noqa: E402
from binary_key_material_backfill import normalized_keystrings  # noqa: E402
from extended_cipher_recheck import candidate_list_digest, load_curated_candidates  # noqa: E402
from first_hint_hash_audit import HALVING_ADDRESS, PRIZE_ADDRESS  # noqa: E402
from half_better_half_algebra_audit import combine_pairs  # noqa: E402
from key_shape_classifier import base58check_decode  # noqa: E402
from raw_key_chunk_audit import EC_NEIGHBOR_HASH160S  # noqa: E402
from data import PHASE32_PASSWORD, PHASE32_PLAINTEXT_PREFIX  # noqa: E402

PHASE = 479
PROTOCOL = REPO_ROOT / "doc/Brainstorms/2026-09-06 - Phase 479 P32 64-in-80 Alignment Protocol.md"
DEFAULT_LOCK = SCRIPT_DIR / "phase479_execution_lock.json"
DEFAULT_RESULT = SCRIPT_DIR / "phase479_result.json"
DEFAULT_HITS = SCRIPT_DIR / "phase479_sensitive_hits.jsonl"
ALIGNMENTS = tuple(range(17))
EXPECTED_CANDIDATES = 648
EXPECTED_CANDIDATE_DIGEST = "2d233645ef49a141"
EXPECTED_KEYSTRINGS = 14551
SECP256K1_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def address_hash160(address):
    decoded = base58check_decode(address)
    if decoded is None or len(decoded) != 21 or decoded[0] != 0:
        raise ValueError(f"not a mainnet P2PKH address: {address}")
    return decoded[1:].hex()


AUTHENTICATED_TARGETS = {
    address_hash160(PRIZE_ADDRESS): "PRIZE_ADDRESS",
    address_hash160(HALVING_ADDRESS): "HALVING_ADDRESS",
}
DERIVED_TARGETS = dict(EC_NEIGHBOR_HASH160S)
ALL_TARGETS = {**AUTHENTICATED_TARGETS, **DERIVED_TARGETS}
TARGET_ADDRESSES = {
    PRIZE_ADDRESS: "PRIZE_ADDRESS",
    HALVING_ADDRESS: "HALVING_ADDRESS",
}


def corpus():
    candidates = load_curated_candidates()
    if len(candidates) != EXPECTED_CANDIDATES:
        raise AssertionError(f"candidate count drift: {len(candidates)}")
    digest = candidate_list_digest(candidates)
    if digest != EXPECTED_CANDIDATE_DIGEST:
        raise AssertionError(f"candidate digest drift: {digest}")
    keystrings = normalized_keystrings(candidates, whitespace_variants=False)
    if len(keystrings) != EXPECTED_KEYSTRINGS:
        raise AssertionError(f"keystring count drift: {len(keystrings)}")
    return candidates, keystrings


def decrypt_nopad(passwd):
    salt, ciphertext = cb_common.BLOBS["P32TRAILING"]
    key, iv = cb_common.evp_bytes_to_key(passwd, salt, "sha256", 32, 16)
    decryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
    body = decryptor.update(ciphertext) + decryptor.finalize()
    if len(body) != 80:
        raise AssertionError(f"P32 body length drift: {len(body)}")
    return body


def scalar_hash160s(value):
    scalar = int.from_bytes(value, "big")
    if not 1 <= scalar < SECP256K1_ORDER:
        return {}
    public = coincurve.PrivateKey(value).public_key
    out = {}
    for kind, encoded in (
        ("compressed", public.format(compressed=True)),
        ("uncompressed", public.format(compressed=False)),
    ):
        out[kind] = hashlib.new("ripemd160", hashlib.sha256(encoded).digest()).hexdigest()
    return out


def classify_hash160(value):
    hits = []
    for address_type, digest in scalar_hash160s(value).items():
        label = ALL_TARGETS.get(digest)
        if label:
            hits.append({
                "address_type": address_type,
                "target": label,
                "target_tier": "authenticated" if digest in AUTHENTICATED_TARGETS else "derived_control",
                "hash160": digest,
            })
    return hits


def evaluate_body(body, targets=None, literal_addresses=None):
    if len(body) != 80:
        raise ValueError("body must be exactly 80 bytes")
    targets = ALL_TARGETS if targets is None else targets
    literal_addresses = TARGET_ADDRESSES if literal_addresses is None else literal_addresses
    # Tests override the module target registry, so classification stays local.
    authenticated = set(AUTHENTICATED_TARGETS) if targets is ALL_TARGETS else set(targets)
    hits = []
    pair_hits = []
    per_half_authenticated = {}
    for start in ALIGNMENTS:
        a = body[start:start + 32]
        b = body[start + 32:start + 64]
        values = {"A": a, "B": b, **combine_pairs(a, b)}
        for operation, value in values.items():
            for address_type, digest in scalar_hash160s(value).items():
                if digest not in targets:
                    continue
                label = targets[digest]
                tier = "authenticated" if digest in authenticated else "derived_control"
                hits.append({
                    "kind": "derived_from_scalar",
                    "alignment": start,
                    "operation": operation,
                    "address_type": address_type,
                    "target": label,
                    "target_tier": tier,
                    "hash160": digest,
                })
                if operation in {"A", "B"} and tier == "authenticated":
                    per_half_authenticated.setdefault(start, {}).setdefault(operation, set()).add(label)
        halves = per_half_authenticated.get(start, {})
        for left in halves.get("A", set()):
            for right in halves.get("B", set()):
                if left != right:
                    pair_hits.append({
                        "alignment": start,
                        "A_target": left,
                        "B_target": right,
                    })

    for address, label in literal_addresses.items():
        needle = address.encode("ascii")
        offset = body.find(needle)
        if offset >= 0:
            hits.append({
                "kind": "literal_address",
                "offset": offset,
                "target": label,
                "target_tier": "authenticated",
            })
    for digest, label in targets.items():
        needle = bytes.fromhex(digest)
        offset = body.find(needle)
        if offset >= 0:
            hits.append({
                "kind": "literal_hash160",
                "offset": offset,
                "target": label,
                "target_tier": "authenticated" if digest in authenticated else "derived_control",
                "hash160": digest,
            })
    return hits, pair_hits


def _synthetic_target(private_key, label):
    hashes = scalar_hash160s(private_key)
    return {hashes["compressed"]: label}


def self_test():
    candidates, keystrings = corpus()
    assert len(candidates) == 648 and len(keystrings) == 14551
    salt, ciphertext = cb_common.BLOBS["P32TRAILING"]
    assert len(salt) == 8 and len(ciphertext) == 80

    # Positive crypto-profile control from the solved Phase 3.2 vector.
    psalt, pct = cb_common.BLOBS.get("PHASE32", (None, None)) if "PHASE32" in cb_common.BLOBS else (None, None)
    if psalt is None:
        from data import PHASE32_BLOB_B64
        psalt, pct = cb_common._load_blob(PHASE32_BLOB_B64)
    key, iv = cb_common.evp_bytes_to_key(PHASE32_PASSWORD.encode("ascii"), psalt, "sha256", 32, 16)
    dec = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
    known = dec.update(pct) + dec.finalize()
    assert known.startswith(PHASE32_PLAINTEXT_PREFIX.encode("ascii"))

    key_a = (1).to_bytes(32, "big")
    key_b = (2).to_bytes(32, "big")
    target_pair = {**_synthetic_target(key_a, "A_SYNTH"), **_synthetic_target(key_b, "B_SYNTH")}
    for start in ALIGNMENTS:
        body = bytearray(hashlib.shake_256(f"phase479:{start}".encode()).digest(80))
        body[start:start + 32] = key_a
        body[start + 32:start + 64] = key_b
        hits, pairs = evaluate_body(bytes(body), targets=target_pair, literal_addresses={})
        direct = {(h.get("alignment"), h.get("operation"), h["target"]) for h in hits}
        assert (start, "A", "A_SYNTH") in direct
        assert (start, "B", "B_SYNTH") in direct
        assert {p["alignment"] for p in pairs} == {start}

    # Reverse assignment remains a valid two-distinct-target pair.
    body = key_b + key_a + b"R" * 16
    _, pairs = evaluate_body(body, targets=target_pair, literal_addresses={})
    assert {tuple((p["A_target"], p["B_target"])) for p in pairs} == {("B_SYNTH", "A_SYNTH")}

    # Combination-only recovery: A+B mod n == 3.
    key_three = (3).to_bytes(32, "big")
    hits, _ = evaluate_body(key_a + key_b + b"C" * 16,
                            targets=_synthetic_target(key_three, "SUM_SYNTH"), literal_addresses={})
    assert any(h.get("operation") == "add_mod_n" and h["target"] == "SUM_SYNTH" for h in hits)

    # Literal address and raw-HASH160 detection.
    literal = "1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH"
    literal_body = (b"X" * 7 + literal.encode() + b"Y" * 39)[:80]
    hits, _ = evaluate_body(literal_body, targets={}, literal_addresses={literal: "LITERAL_SYNTH"})
    assert any(h["kind"] == "literal_address" for h in hits)
    digest = next(iter(_synthetic_target(key_a, "RAW_SYNTH")))
    hits, _ = evaluate_body(b"Z" * 11 + bytes.fromhex(digest) + b"Q" * 49,
                            targets={digest: "RAW_SYNTH"}, literal_addresses={})
    assert any(h["kind"] == "literal_hash160" for h in hits)

    wrong = hashlib.shake_256(b"phase479-wrong-body").digest(80)
    hits, pairs = evaluate_body(wrong, targets=target_pair, literal_addresses={})
    assert hits == [] and pairs == []
    return True


def lock_payload():
    candidates, keystrings = corpus()
    tracked = {
        "protocol": PROTOCOL,
        "audit_script": Path(__file__),
        "cb_common": Path(cb_common.__file__),
        "binary_key_material_backfill": SCRIPT_DIR / "binary_key_material_backfill.py",
        "extended_cipher_recheck": SCRIPT_DIR / "extended_cipher_recheck.py",
        "first_hint_hash_audit": SCRIPT_DIR / "first_hint_hash_audit.py",
        "half_better_half_algebra_audit": SCRIPT_DIR / "half_better_half_algebra_audit.py",
        "key_shape_classifier": SCRIPT_DIR / "key_shape_classifier.py",
        "raw_key_chunk_audit": SCRIPT_DIR / "raw_key_chunk_audit.py",
        "data": SCRIPT_DIR / "data.py",
    }
    salt, ciphertext = cb_common.BLOBS["P32TRAILING"]
    return {
        "phase": PHASE,
        "status": "locked-before-real-run",
        "coincurve_version": importlib.metadata.version("coincurve"),
        "cryptography_version": importlib.metadata.version("cryptography"),
        "files_sha256": {name: sha256_file(path) for name, path in tracked.items()},
        "candidate_count": len(candidates),
        "candidate_digest": candidate_list_digest(candidates),
        "keystring_count": len(keystrings),
        "alignments": list(ALIGNMENTS),
        "crypto_profile": "legacy-evp-bytes-to-key-sha256/aes-256-cbc/nopad",
        "p32_salt_hex": salt.hex(),
        "p32_ciphertext_sha256": hashlib.sha256(ciphertext).hexdigest(),
        "authenticated_targets": AUTHENTICATED_TARGETS,
        "derived_targets": DERIVED_TARGETS,
    }


def write_json_atomic(path, value, mode=0o644):
    path = Path(path)
    temp = path.with_name(path.name + ".tmp")
    descriptor = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp, mode)
        os.replace(temp, path)
    except Exception:
        try:
            os.unlink(temp)
        except FileNotFoundError:
            pass
        raise


def verify_lock(lock_path):
    lock = json.loads(Path(lock_path).read_text(encoding="utf-8"))
    expected = lock_payload()
    if lock != expected:
        raise RuntimeError("execution lock does not match current protocol/code/inputs")
    return lock


def issue_lock(lock_path):
    self_test()
    payload = lock_payload()
    write_json_atomic(lock_path, payload)
    verify_lock(lock_path)
    return payload


def run(lock_path, result_path, hits_path):
    lock = verify_lock(lock_path)
    _, keystrings = corpus()
    public_hits = []
    sensitive_hits = []
    for index, (candidate, form, keystr) in enumerate(keystrings):
        passwd = keystr.encode("utf-8")
        body = decrypt_nopad(passwd)
        hits, pair_hits = evaluate_body(body)
        if hits or pair_hits:
            identity = {
                "index": index,
                "candidate_sha256": hashlib.sha256(candidate.encode("utf-8")).hexdigest(),
                "form_sha256": hashlib.sha256(form.encode("utf-8")).hexdigest(),
                "passphrase_sha256": hashlib.sha256(passwd).hexdigest(),
            }
            public_hits.append({**identity, "hits": hits, "pair_hits": pair_hits})
            sensitive_hits.append({
                **identity,
                "candidate": candidate,
                "form": form,
                "passphrase_b64_hex": passwd.hex(),
                "body_hex": body.hex(),
                "hits": hits,
                "pair_hits": pair_hits,
            })
    if sensitive_hits:
        descriptor = os.open(hits_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            for record in sensitive_hits:
                handle.write(json.dumps(record, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
    result = {
        "phase": PHASE,
        "lock_sha256": sha256_file(lock_path),
        "candidate_count": lock["candidate_count"],
        "keystring_count": lock["keystring_count"],
        "decryptions": len(keystrings),
        "alignments_per_decryption": len(ALIGNMENTS),
        "scalar_candidates_per_alignment": 17,
        "exact_hits": public_hits,
        "exact_hit_count": len(public_hits),
        "verdict": "positive_requires_sensitive_review" if public_hits else "bounded_negative",
    }
    write_json_atomic(result_path, result)
    return result


def main():
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
        print("[*] Phase 479 self-test passed")
    elif args.issue_lock:
        payload = issue_lock(args.lock)
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        result = run(args.lock, args.result, args.hits)
        print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

