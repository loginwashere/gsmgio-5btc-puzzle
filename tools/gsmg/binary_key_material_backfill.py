#!/usr/bin/env python3
"""Backfill SALPH/P32TRAILING for non-printable 64-byte key material.

The shared CBC oracle historically required readable plaintext after valid
PKCS7 padding. That can silently reject the clue-supported output shape
`private key | private key`: 64 arbitrary bytes followed by a complete
16-byte AES padding block inside each target's 80-byte ciphertext.

This driver:

* tests the curated candidate corpus against all 24 existing CBC/KDF variants
  and the bounded 12 AES-ECB/KDF variants;
* checkpoints every normalized keystring for exact resume;
* stores structural-hit plaintext and WIFs only in a mode-0600 sensitive file;
* derives compressed and uncompressed P2PKH addresses for each 32-byte half;
* checks their hash160 values against the repository's BLMCACHE file;
* appends Bloom positives to an address-only JSONL API-verification queue;
* optionally verifies pending queue entries through the Blockstream API.

Bloom misses never invalidate a structural decrypt. A Bloom hit is provisional
until API verification removes the filter's false positives.
"""

import argparse
import hashlib
import io
import json
import math
import mmap
import os
import struct
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from cryptography.hazmat.primitives.asymmetric import ec

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

import cb_common  # noqa: E402
from aes_key_wrap_sweep import ALL_CBC_VARIANTS  # noqa: E402
from cb_common import (  # noqa: E402
    BLOBS,
    ECB_CIPHER_VARIANTS,
    aes_try_open,
    aes_try_open_ecb,
    answer_forms,
    keystr_forms,
)
from extended_cipher_recheck import (  # noqa: E402
    candidate_list_digest,
    load_curated_candidates,
)
from first_hint_hash_audit import (  # noqa: E402
    HALVING_ADDRESS,
    PRIZE_ADDRESS,
    SECP256K1_ORDER,
    base58check,
)

TARGET_BLOBS = {
    "SALPH": BLOBS["SALPH"],
    "P32TRAILING": BLOBS["P32TRAILING"],
}
KNOWN_GSMG_ADDRESSES = {PRIZE_ADDRESS, HALVING_ADDRESS}
DEFAULT_CHECKPOINT = SCRIPT_DIR / "binary_key_material_checkpoint.jsonl"
DEFAULT_HITS = SCRIPT_DIR / "binary_key_material_hits.jsonl"
DEFAULT_QUEUE = SCRIPT_DIR / "binary_key_material_api_queue.jsonl"
DEFAULT_BLOOM = REPO_ROOT / "db" / "addresses.hash160.bloom"
DEFAULT_API_BASE = "https://blockstream.info/api/address"
SECP256K1_FIELD = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
MURMUR_SEED = 0x9747B28C


def _u32(value):
    return value & 0xFFFFFFFF


def murmur3_x86_32_20(data, seed):
    """Match src/checker/bloom.rs and kernels/secp256k1.cu exactly."""
    if len(data) != 20:
        raise ValueError("Bloom keys must be 20-byte hash160 values")
    c1 = 0xCC9E2D51
    c2 = 0x1B873593
    h = seed
    for offset in range(0, 20, 4):
        key = int.from_bytes(data[offset:offset + 4], "little")
        key = _u32(key * c1)
        key = _u32((key << 15) | (key >> 17))
        key = _u32(key * c2)
        h ^= key
        h = _u32((h << 13) | (h >> 19))
        h = _u32(h * 5 + 0xE6546B64)
    h ^= 20
    h ^= h >> 16
    h = _u32(h * 0x85EBCA6B)
    h ^= h >> 13
    h = _u32(h * 0xC2B2AE35)
    h ^= h >> 16
    return _u32(h)


class BloomCache:
    """Read-only mmap of the Rust checker's BLMCACHE v1 format."""

    def __init__(self, path):
        self.path = Path(path)
        self.file = self.path.open("rb")
        self.mapping = mmap.mmap(self.file.fileno(), 0, access=mmap.ACCESS_READ)
        if len(self.mapping) < 21 or self.mapping[:8] != b"BLMCACHE":
            self.close()
            raise ValueError(f"{self.path}: invalid Bloom cache magic")
        if self.mapping[8] != 1:
            self.close()
            raise ValueError(f"{self.path}: unsupported Bloom cache version")
        self.m = struct.unpack_from("<Q", self.mapping, 9)[0]
        self.k = struct.unpack_from("<I", self.mapping, 17)[0]
        expected_size = 21 + (self.m // 64) * 8
        if not self.m or self.m % 64 or not self.k or len(self.mapping) != expected_size:
            self.close()
            raise ValueError(f"{self.path}: invalid or truncated Bloom cache")
        stat = self.path.stat()
        self.identity = {
            "path": str(self.path),
            "size": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
            "m": self.m,
            "k": self.k,
        }

    def contains(self, hash160):
        h1 = murmur3_x86_32_20(hash160, MURMUR_SEED)
        h2 = murmur3_x86_32_20(hash160, h1)
        for index in range(self.k):
            bit = (h1 + index * h2) % self.m
            word = struct.unpack_from("<Q", self.mapping, 21 + (bit // 64) * 8)[0]
            if not word & (1 << (bit % 64)):
                return False
        return True

    def close(self):
        mapping = getattr(self, "mapping", None)
        if mapping is not None:
            mapping.close()
            self.mapping = None
        file_obj = getattr(self, "file", None)
        if file_obj is not None:
            file_obj.close()
            self.file = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


def hash160(data):
    return hashlib.new("ripemd160", hashlib.sha256(data).digest()).digest()


def private_key_details(private_key):
    value = int.from_bytes(private_key, "big")
    if not 1 <= value < SECP256K1_ORDER:
        return None
    public = ec.derive_private_key(value, ec.SECP256K1()).public_key().public_numbers()
    x_bytes = public.x.to_bytes(32, "big")
    y_bytes = public.y.to_bytes(32, "big")
    public_keys = {
        "compressed": bytes([2 + (public.y & 1)]) + x_bytes,
        "uncompressed": b"\x04" + x_bytes + y_bytes,
    }
    addresses = {}
    for address_type, public_key in public_keys.items():
        digest = hash160(public_key)
        addresses[address_type] = {
            "address": base58check(b"\x00" + digest),
            "hash160": digest.hex(),
            "wif": base58check(
                b"\x80" + private_key + (b"\x01" if address_type == "compressed" else b"")
            ),
        }
    return addresses


def xy_point_valid(body):
    if len(body) != 64:
        return False
    x = int.from_bytes(body[:32], "big")
    y = int.from_bytes(body[32:], "big")
    return x < SECP256K1_FIELD and y < SECP256K1_FIELD and (
        y * y - (x * x * x + 7)
    ) % SECP256K1_FIELD == 0


def append_jsonl(path, record, sensitive=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
    descriptor = os.open(path, flags, 0o600 if sensitive else 0o644)
    try:
        if sensitive:
            os.fchmod(descriptor, 0o600)
        os.write(descriptor, (json.dumps(record, sort_keys=True) + "\n").encode())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def normalized_keystrings(candidates):
    seen = set()
    records = []
    for candidate in candidates:
        for form in sorted(answer_forms(candidate)):
            for keystr in keystr_forms(form, newline_variants=True):
                if keystr in seen:
                    continue
                seen.add(keystr)
                records.append((candidate, form, keystr))
    return records


def load_candidates(candidate_file=None):
    if candidate_file is None:
        return load_curated_candidates()
    seen = set()
    candidates = []
    for line in Path(candidate_file).read_text(errors="replace").splitlines():
        candidate = line.strip()
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        candidates.append(candidate)
    return candidates


def run_fingerprint(candidates, keystrings):
    blob_digest = hashlib.sha256()
    for tag, (salt, ciphertext) in TARGET_BLOBS.items():
        blob_digest.update(tag.encode() + b"\0" + salt + ciphertext)
    variant_digest = hashlib.sha256(
        repr((ALL_CBC_VARIANTS, ECB_CIPHER_VARIANTS)).encode()
    ).hexdigest()[:16]
    return {
        "version": 2,
        "candidate_digest": candidate_list_digest(candidates),
        "candidate_count": len(candidates),
        "keystring_count": len(keystrings),
        "blob_digest": blob_digest.hexdigest()[:16],
        "variant_digest": variant_digest,
        "oracle_sha256": hashlib.sha256(
            Path(cb_common.__file__).read_bytes()
        ).hexdigest()[:16],
        "driver_sha256": hashlib.sha256(
            Path(__file__).read_bytes()
        ).hexdigest()[:16],
        "cbc_variants": len(ALL_CBC_VARIANTS),
        "ecb_variants": len(ECB_CIPHER_VARIANTS),
    }


def load_checkpoint(path, fingerprint):
    path = Path(path)
    if not path.exists() or path.stat().st_size == 0:
        return set()
    records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    expected_header = {"header": True, **fingerprint}
    if not records or records[0] != expected_header:
        raise ValueError(
            f"{path}: checkpoint header does not match this run; use a new checkpoint"
        )
    return {
        record["keystr_sha256"]
        for record in records[1:]
        if "keystr_sha256" in record
    }


def ensure_checkpoint_header(path, fingerprint):
    path = Path(path)
    if not path.exists() or path.stat().st_size == 0:
        append_jsonl(path, {"header": True, **fingerprint})


def latest_queue_state(path):
    path = Path(path)
    state = {}
    if not path.exists():
        return state
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if "queue_id" in record:
            state[record["queue_id"]] = record
    return state


def existing_hit_ids(path):
    path = Path(path)
    if not path.exists():
        return set()
    return {
        record.get("hit_id")
        for line in path.read_text().splitlines()
        if line.strip()
        for record in (json.loads(line),)
        if record.get("hit_id")
    }


def queue_address(queue_path, hit_id, half_label, address_type, address_data, bloom):
    queue_id = hashlib.sha256(
        f"{hit_id}|{half_label}|{address_type}|{address_data['address']}".encode()
    ).hexdigest()[:24]
    existing = latest_queue_state(queue_path).get(queue_id)
    if existing and existing.get("status") in {
        "pending", "confirmed_funded", "confirmed_used_empty",
        "bloom_false_positive",
    }:
        return
    append_jsonl(queue_path, {
        "queue_id": queue_id,
        "hit_id": hit_id,
        "half": half_label,
        "address_type": address_type,
        "address": address_data["address"],
        "hash160": address_data["hash160"],
        "bloom": bloom.identity,
        "status": "pending",
        "attempt_count": 0,
        "created_at": int(time.time()),
    })


def record_hit(hit_path, queue_path, candidate, form, keystr, mode, result, bloom):
    tag, body, kdf_label, key_len = result
    classification = "binary64" if len(body) == 64 else "readable"
    hit_id = hashlib.sha256(
        tag.encode() + b"\0" + mode.encode() + b"\0" + kdf_label.encode()
        + b"\0" + keystr.encode() + b"\0" + body
    ).hexdigest()[:24]
    halves = {}
    if classification == "binary64":
        for half_label, private_key in (
            ("half", body[:32]),
            ("better_half", body[32:]),
        ):
            details = private_key_details(private_key)
            halves[half_label] = {
                "private_key_hex": private_key.hex(),
                "valid_scalar": details is not None,
                "addresses": details or {},
            }
    record = {
        "hit_id": hit_id,
        "blob": tag,
        "mode": mode,
        "classification": classification,
        "kdf": kdf_label,
        "key_bits": key_len * 8,
        "candidate": candidate,
        "form": form,
        "passphrase_hex": keystr.encode().hex(),
        "plaintext_hex": body.hex(),
        "plaintext_sha256": hashlib.sha256(body).hexdigest(),
        "xy_point_valid": xy_point_valid(body),
        "halves": halves,
        "created_at": int(time.time()),
    }
    if hit_id not in existing_hit_ids(hit_path):
        append_jsonl(hit_path, record, sensitive=True)

    print(
        f"[+++ {classification.upper()} HIT] "
        f"{tag} {mode} {kdf_label}/{key_len * 8}"
    )
    if classification != "binary64":
        print(f"    readable preview: {body[:200]!r}")
        return
    for half_label, half in halves.items():
        if not half["valid_scalar"]:
            print(f"    {half_label}: invalid secp256k1 scalar")
            continue
        for address_type, address_data in half["addresses"].items():
            address = address_data["address"]
            known = address in KNOWN_GSMG_ADDRESSES
            bloom_hit = bloom.contains(bytes.fromhex(address_data["hash160"])) if bloom else False
            print(
                f"    {half_label}/{address_type}: {address} "
                f"known={known} bloom={bloom_hit}"
            )
            if bloom_hit:
                queue_address(
                    queue_path, hit_id, half_label, address_type, address_data, bloom,
                )


def sweep(args):
    candidates = load_candidates(args.candidate_file)
    keystrings = normalized_keystrings(candidates)
    if args.limit is not None:
        keystrings = keystrings[:args.limit]
    fingerprint = run_fingerprint(candidates, keystrings)
    completed = load_checkpoint(args.checkpoint, fingerprint)
    ensure_checkpoint_header(args.checkpoint, fingerprint)
    bloom = None if args.no_bloom else BloomCache(args.bloom_cache)
    operations_per_key = len(TARGET_BLOBS) * (
        len(ALL_CBC_VARIANTS) + len(ECB_CIPHER_VARIANTS)
    )
    print(
        f"[*] candidates={len(candidates):,} digest={fingerprint['candidate_digest']} "
        f"keystrings={len(keystrings):,} operations/key={operations_per_key}"
    )
    try:
        for index, (candidate, form, keystr) in enumerate(keystrings):
            keystr_digest = hashlib.sha256(keystr.encode()).hexdigest()
            if keystr_digest in completed:
                continue
            hit_count = 0
            for tag, blob in TARGET_BLOBS.items():
                scoped_blob = {tag: blob}
                cbc_result = aes_try_open(
                    keystr, kdf_variants=ALL_CBC_VARIANTS, blobs=scoped_blob,
                )
                if cbc_result:
                    record_hit(
                        args.hits, args.queue, candidate, form, keystr,
                        "cbc", cbc_result, bloom,
                    )
                    hit_count += 1
                ecb_result = aes_try_open_ecb(
                    keystr, kdf_variants=ECB_CIPHER_VARIANTS, blobs=scoped_blob,
                )
                if ecb_result:
                    record_hit(
                        args.hits, args.queue, candidate, form, keystr,
                        "ecb", ecb_result, bloom,
                    )
                    hit_count += 1
            append_jsonl(args.checkpoint, {
                "index": index,
                "keystr_sha256": keystr_digest,
                "hits": hit_count,
            })
            if (index + 1) % 250 == 0 or index + 1 == len(keystrings):
                print(f"[*] progress {index + 1:,}/{len(keystrings):,}")
    finally:
        if bloom:
            bloom.close()


def verify_pending_queue(args):
    state = latest_queue_state(args.queue)
    pending = [
        record for record in state.values()
        if record.get("status") in {"pending", "error"}
        and record.get("attempt_count", 0) < args.max_attempts
    ]
    print(f"[*] {len(pending)} queue entries pending verification")
    for record in pending:
        address = record["address"]
        attempts = record.get("attempt_count", 0) + 1
        request = urllib.request.Request(
            f"{args.api_base.rstrip('/')}/{address}",
            headers={"User-Agent": "key-seeker-gsmg-audit/1"},
        )
        try:
            with urllib.request.urlopen(request, timeout=args.api_timeout) as response:
                payload = json.load(response)
            chain = payload.get("chain_stats", {})
            mempool = payload.get("mempool_stats", {})
            funded = int(chain.get("funded_txo_sum", 0)) + int(
                mempool.get("funded_txo_sum", 0)
            )
            spent = int(chain.get("spent_txo_sum", 0)) + int(
                mempool.get("spent_txo_sum", 0)
            )
            tx_count = int(chain.get("tx_count", 0)) + int(
                mempool.get("tx_count", 0)
            )
            if funded > spent:
                status = "confirmed_funded"
            elif tx_count:
                status = "confirmed_used_empty"
            else:
                status = "bloom_false_positive"
            event = {
                **record,
                "status": status,
                "attempt_count": attempts,
                "funded_txo_sum": funded,
                "spent_txo_sum": spent,
                "tx_count": tx_count,
                "checked_at": int(time.time()),
            }
            print(f"[*] {address}: {status}")
        except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
            event = {
                **record,
                "status": "error",
                "attempt_count": attempts,
                "last_error": str(exc),
                "checked_at": int(time.time()),
            }
            print(f"[!] {address}: {exc}")
        append_jsonl(args.queue, event)
        time.sleep(args.api_interval)


def _write_test_bloom(path, entries):
    n = max(1, len(entries))
    probability = 0.0001
    m_raw = math.ceil((-n * math.log(probability)) / (math.log(2) ** 2))
    m = ((m_raw + 63) // 64) * 64
    k = math.ceil((m / n) * math.log(2))
    words = [0] * (m // 64)
    for entry in entries:
        h1 = murmur3_x86_32_20(entry, MURMUR_SEED)
        h2 = murmur3_x86_32_20(entry, h1)
        for index in range(k):
            bit = (h1 + index * h2) % m
            words[bit // 64] |= 1 << (bit % 64)
    with open(path, "wb") as output:
        output.write(b"BLMCACHE" + bytes([1]))
        output.write(struct.pack("<QI", m, k))
        output.write(b"".join(struct.pack("<Q", word) for word in words))


def self_test():
    key_one = (1).to_bytes(32, "big")
    key_two = (2).to_bytes(32, "big")
    details = private_key_details(key_one)
    assert details["compressed"]["address"] == "1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH"
    assert details["uncompressed"]["address"] == "1EHNa6Q4Jz2uvNExL497mE43ikXhwF6kZm"
    assert not xy_point_valid(key_one + key_one)
    target = bytes.fromhex(details["compressed"]["hash160"])
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "test.bloom"
        hit_path = Path(directory) / "hits.jsonl"
        queue_path = Path(directory) / "queue.jsonl"
        candidate_path = Path(directory) / "candidates.txt"
        candidate_path.write_text("#literal\nalpha\nalpha\nbeta\n")
        assert load_candidates(candidate_path) == ["#literal", "alpha", "beta"]
        checkpoint_path = Path(directory) / "checkpoint.jsonl"
        fingerprint = run_fingerprint(["alpha"], normalized_keystrings(["alpha"]))
        ensure_checkpoint_header(checkpoint_path, fingerprint)
        assert load_checkpoint(checkpoint_path, fingerprint) == set()
        changed_fingerprint = {**fingerprint, "oracle_sha256": "changed"}
        try:
            load_checkpoint(checkpoint_path, changed_fingerprint)
        except ValueError:
            pass
        else:
            raise AssertionError("mismatched oracle source fingerprint was accepted")
        _write_test_bloom(path, [target])
        with BloomCache(path) as bloom:
            assert bloom.contains(target)
            assert not bloom.contains(bytes([0xA5]) * 20)
            synthetic_result = (
                "SYNTH", key_one + key_two, "sha256", 32,
            )
            record_hit(
                hit_path, queue_path, "candidate", "form", "keystr",
                "cbc", synthetic_result, bloom,
            )
            first_queue_lines = queue_path.read_text().splitlines()
            record_hit(
                hit_path, queue_path, "candidate", "form", "keystr",
                "cbc", synthetic_result, bloom,
            )
        assert len(hit_path.read_text().splitlines()) == 1
        assert hit_path.stat().st_mode & 0o777 == 0o600
        queue_text = queue_path.read_text()
        assert queue_text.splitlines() == first_queue_lines
        queue_records = [json.loads(line) for line in first_queue_lines]
        assert any(record["hash160"] == target.hex() for record in queue_records)
        assert key_one.hex() not in queue_text
        assert '"wif"' not in queue_text and "passphrase" not in queue_text

        api_queue = Path(directory) / "api_queue.jsonl"
        for queue_id, address in (
            ("funded", "1FundedSynthetic"),
            ("false", "1FalsePositiveSynthetic"),
        ):
            append_jsonl(api_queue, {
                "queue_id": queue_id,
                "address": address,
                "status": "pending",
                "attempt_count": 0,
            })

        def fake_urlopen(request, timeout):
            if request.full_url.endswith("1FundedSynthetic"):
                payload = {
                    "chain_stats": {
                        "funded_txo_sum": 100,
                        "spent_txo_sum": 25,
                        "tx_count": 2,
                    },
                    "mempool_stats": {},
                }
            else:
                payload = {
                    "chain_stats": {
                        "funded_txo_sum": 0,
                        "spent_txo_sum": 0,
                        "tx_count": 0,
                    },
                    "mempool_stats": {},
                }
            return io.BytesIO(json.dumps(payload).encode())

        api_args = SimpleNamespace(
            queue=api_queue,
            max_attempts=3,
            api_base="https://mock.invalid/address",
            api_timeout=1.0,
            api_interval=0.0,
        )
        with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
            verify_pending_queue(api_args)
        api_state = latest_queue_state(api_queue)
        assert api_state["funded"]["status"] == "confirmed_funded"
        assert api_state["false"]["status"] == "bloom_false_positive"
        assert all(record["attempt_count"] == 1 for record in api_state.values())
    print(
        "[*] self-test OK: addresses, point test, Bloom cache, hit dedupe, "
        "sensitive/queue separation, source guard, mocked API verification"
    )


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument(
        "--candidate-file",
        type=Path,
        help="one literal candidate per nonempty line; default is the existing "
             "648-candidate loader",
    )
    parser.add_argument("--hits", type=Path, default=DEFAULT_HITS)
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--bloom-cache", type=Path, default=DEFAULT_BLOOM)
    parser.add_argument("--no-bloom", action="store_true")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--verify-queue", action="store_true")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE)
    parser.add_argument("--api-timeout", type=float, default=15.0)
    parser.add_argument("--api-interval", type=float, default=0.4)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.self_test:
        self_test()
    elif args.verify_queue:
        verify_pending_queue(args)
    else:
        sweep(args)


if __name__ == "__main__":
    main()
