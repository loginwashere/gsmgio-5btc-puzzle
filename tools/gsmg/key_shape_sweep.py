#!/usr/bin/env python3
"""Sweep the curated candidate corpus against all four blobs, classifying
every weak/strong/structural hit's body for private-key-shaped substrings
(`key_shape_classifier.classify_body`) instead of just eyeballing it.

Existing sweeps already decide "does this body look like plausible output"
(`cb_common`'s printable z-score gate, or the raw 32|32-byte binary shape
`binary_key_material_backfill.py` handles directly). This driver reuses that
same gate unmodified -- `aes_try_open`/`aes_try_open_ecb` only return a
result once it clears weak/strong/structural -- and adds one more question on
top: is any of this body's text/bytes actually a valid private key (hex64,
WIF, or a checksum-valid BIP39 mnemonic)? `binary_key_material_backfill.py`
already covers the raw-binary case for SALPH/P32TRAILING; this driver widens
that to all four blobs (`cb_common.BLOBS`) and to the three text encodings.

Every match is address-derived, Bloom-checked, and queued through the exact
same `BloomCache`/`queue_address`/`verify_pending_queue` machinery
`binary_key_material_backfill.py` already uses and self-tests -- imported
directly, not reimplemented, so there is one Bloom/API code path in this
project. A Bloom miss never invalidates a checksum-valid key-shaped match; a
Bloom hit is provisional until `--verify-queue` confirms it against the
Blockstream API.
"""

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import cb_common  # noqa: E402
from aes_key_wrap_sweep import ALL_CBC_VARIANTS  # noqa: E402
from binary_key_material_backfill import (  # noqa: E402
    BloomCache,
    append_jsonl,
    existing_hit_ids,
    load_checkpoint,
    ensure_checkpoint_header,
    latest_queue_state,
    private_key_details,
    queue_address,
    verify_pending_queue,
)
from cb_common import BLOBS, ECB_CIPHER_VARIANTS, aes_try_open, aes_try_open_ecb  # noqa: E402
from extended_cipher_recheck import candidate_list_digest, load_curated_candidates  # noqa: E402
from key_shape_classifier import classify_body  # noqa: E402

DEFAULT_CHECKPOINT = SCRIPT_DIR / "key_shape_sweep_checkpoint.jsonl"
DEFAULT_HITS = SCRIPT_DIR / "key_shape_sweep_hits.jsonl"
DEFAULT_QUEUE = SCRIPT_DIR / "key_shape_sweep_api_queue.jsonl"
DEFAULT_BLOOM = SCRIPT_DIR.parents[1] / "db" / "addresses.hash160.bloom"
DEFAULT_API_BASE = "https://blockstream.info/api/address"


def normalized_keystrings(candidates):
    """Same normalization as `binary_key_material_backfill.py` (newline
    variants, no whitespace variants) -- kept independent rather than
    imported so this driver's keystring set never silently changes if that
    module's default changes."""
    seen = set()
    records = []
    for candidate in candidates:
        for form in sorted(cb_common.answer_forms(candidate)):
            for keystr in cb_common.keystr_forms(form, newline_variants=True):
                if keystr in seen:
                    continue
                seen.add(keystr)
                records.append((candidate, form, keystr))
    return records


def run_fingerprint(candidates, keystrings):
    blob_digest = hashlib.sha256()
    for tag, (salt, ciphertext) in sorted(BLOBS.items()):
        blob_digest.update(tag.encode() + b"\0" + salt + ciphertext)
    variant_digest = hashlib.sha256(
        repr((ALL_CBC_VARIANTS, ECB_CIPHER_VARIANTS)).encode()
    ).hexdigest()[:16]
    return {
        "version": 1,
        "candidate_digest": candidate_list_digest(candidates),
        "candidate_count": len(candidates),
        "keystring_count": len(keystrings),
        "blob_digest": blob_digest.hexdigest()[:16],
        "variant_digest": variant_digest,
        "classifier_sha256": hashlib.sha256(
            (SCRIPT_DIR / "key_shape_classifier.py").read_bytes()
        ).hexdigest()[:16],
        "driver_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:16],
    }


def record_hit(hit_path, queue_path, candidate, form, keystr, tag, mode, kdf_label,
                key_len, body, bloom):
    matches = classify_body(body)
    if not matches:
        return 0
    hit_id = hashlib.sha256(
        tag.encode() + b"\0" + mode.encode() + b"\0" + kdf_label.encode()
        + b"\0" + keystr.encode() + b"\0" + body
    ).hexdigest()[:24]
    sources = {}
    seen_keys = set()
    for source_label, key in matches:
        if key in seen_keys:
            continue
        seen_keys.add(key)
        details = private_key_details(key)
        sources.setdefault(source_label, []).append({
            "private_key_hex": key.hex(),
            "addresses": details or {},
        })
    record = {
        "hit_id": hit_id,
        "blob": tag,
        "mode": mode,
        "kdf": kdf_label,
        "key_bits": key_len * 8,
        "candidate": candidate,
        "form": form,
        "passphrase_hex": keystr.encode().hex(),
        "plaintext_hex": body.hex(),
        "plaintext_sha256": hashlib.sha256(body).hexdigest(),
        "sources": sources,
        "created_at": int(time.time()),
    }
    if hit_id not in existing_hit_ids(hit_path):
        append_jsonl(hit_path, record, sensitive=True)

    queued = 0
    for source_label, entries in sources.items():
        for entry in entries:
            for address_type, address_data in entry["addresses"].items():
                bloom_hit = bloom.contains(bytes.fromhex(address_data["hash160"])) if bloom else False
                print(
                    f"[+++ KEYSHAPE HIT] {tag} {mode} {kdf_label} {source_label}/"
                    f"{address_type}: {address_data['address']} bloom={bloom_hit}"
                )
                if bloom_hit:
                    queue_address(
                        queue_path, hit_id, source_label,
                        address_type, address_data, bloom,
                    )
                    queued += 1
    return queued


def sweep(args):
    candidates = load_candidates(args.candidate_file)
    keystrings = normalized_keystrings(candidates)
    if args.limit is not None:
        keystrings = keystrings[:args.limit]
    fingerprint = run_fingerprint(candidates, keystrings)
    completed = load_checkpoint(args.checkpoint, fingerprint)
    ensure_checkpoint_header(args.checkpoint, fingerprint)
    bloom = None if args.no_bloom else BloomCache(args.bloom_cache)
    operations_per_key = len(BLOBS) * (len(ALL_CBC_VARIANTS) + len(ECB_CIPHER_VARIANTS))
    print(
        f"[*] candidates={len(candidates):,} digest={fingerprint['candidate_digest']} "
        f"keystrings={len(keystrings):,} operations/key={operations_per_key} "
        f"blobs={sorted(BLOBS)}"
    )
    try:
        for index, (candidate, form, keystr) in enumerate(keystrings):
            keystr_digest = hashlib.sha256(keystr.encode()).hexdigest()
            if keystr_digest in completed:
                continue
            hit_count = 0
            for tag, blob in BLOBS.items():
                scoped_blob = {tag: blob}
                for mode, fn, variants in (
                    ("cbc", aes_try_open, ALL_CBC_VARIANTS),
                    ("ecb", aes_try_open_ecb, ECB_CIPHER_VARIANTS),
                ):
                    result = fn(keystr, kdf_variants=variants, blobs=scoped_blob)
                    if result:
                        result_tag, body, kdf_label, key_len = result
                        hit_count += record_hit(
                            args.hits, args.queue, candidate, form, keystr,
                            result_tag, mode, kdf_label, key_len, body, bloom,
                        )
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


def load_candidates(candidate_file):
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


def self_test():
    import tempfile
    from unittest import mock
    import io

    with tempfile.TemporaryDirectory() as directory:
        directory = Path(directory)
        candidate_path = directory / "candidates.txt"
        candidate_path.write_text("alpha\nalpha\nbeta\n")
        assert load_candidates(candidate_path) == ["alpha", "beta"]

        checkpoint_path = directory / "checkpoint.jsonl"
        fingerprint = run_fingerprint(["alpha"], normalized_keystrings(["alpha"]))
        ensure_checkpoint_header(checkpoint_path, fingerprint)
        assert load_checkpoint(checkpoint_path, fingerprint) == set()

        # A synthetic hit whose body is a known-good WIF for private key 1
        # (cross-checked, not hand-typed): confirms classify_body() firing on
        # a *readable* body -- not the raw-binary shape -- reaches the same
        # Bloom/queue path as binary_key_material_backfill.py's binary64 case.
        wif = private_key_details((1).to_bytes(32, "big"))["compressed"]["wif"]
        body = f"the key is {wif} end".encode()
        target_hash160 = bytes.fromhex(
            private_key_details((1).to_bytes(32, "big"))["compressed"]["hash160"]
        )

        # A bloom filter sized for a single entry (as this synthetic one is)
        # saturates almost all of its bits, so an *unrelated* lookup (here,
        # the uncompressed address derived from the same scalar) can also
        # come back as a Bloom hit -- expected small-filter behavior, not a
        # bug, and exactly why every Bloom hit is provisional pending API
        # verification rather than trusted outright. The test therefore only
        # pins down that the real target is queued and dedup works, not an
        # exact hit count.
        from binary_key_material_backfill import _write_test_bloom
        bloom_path = directory / "test.bloom"
        _write_test_bloom(bloom_path, [target_hash160])

        hit_path = directory / "hits.jsonl"
        queue_path = directory / "queue.jsonl"
        with BloomCache(bloom_path) as bloom:
            queued = record_hit(
                hit_path, queue_path, "candidate", "form", "keystr",
                "SYNTH", "cbc", "sha256", 32, body, bloom,
            )
            assert queued >= 1, queued
            queued_again = record_hit(
                hit_path, queue_path, "candidate", "form", "keystr",
                "SYNTH", "cbc", "sha256", 32, body, bloom,
            )
            assert queued_again == queued  # same Bloom hits reported again,
            # but queue_address must dedupe on queue_id rather than append
            # duplicates (checked next)

        hit_lines = hit_path.read_text().splitlines()
        assert len(hit_lines) == 1  # hit dedup on hit_id
        assert hit_path.stat().st_mode & 0o777 == 0o600
        queue_records = [json.loads(line) for line in queue_path.read_text().splitlines()]
        assert len(queue_records) == len({r["queue_id"] for r in queue_records}) == queued  # queue dedup
        assert target_hash160.hex() in {r["hash160"] for r in queue_records}
        assert "1" * 33 not in hit_path.read_text()  # no raw private key text
        hit_record = json.loads(hit_lines[0])
        assert "compressed" in json.dumps(hit_record["sources"])  # addresses present
        assert (1).to_bytes(32, "big").hex() in json.dumps(hit_record), (
            "sensitive hit file should retain the recovered key -- unlike the "
            "queue file -- for manual follow-up"
        )

        # A body with no key-shaped content produces no hit at all.
        no_hit_path = directory / "no_hit.jsonl"
        no_hit_queue = directory / "no_hit_queue.jsonl"
        with BloomCache(bloom_path) as bloom:
            queued = record_hit(
                no_hit_path, no_hit_queue, "candidate", "form", "keystr",
                "SYNTH", "cbc", "sha256", 32, b"just ordinary printable text", bloom,
            )
        assert queued == 0
        assert not no_hit_path.exists()

        # verify_pending_queue is the exact imported function already
        # self-tested by binary_key_material_backfill.py; a light smoke check
        # here only confirms this driver's queue records are shaped
        # compatibly with it (same field names it reads).
        api_queue = directory / "api_queue.jsonl"
        append_jsonl(api_queue, {
            "queue_id": "smoke", "address": "1Smoke", "status": "pending", "attempt_count": 0,
        })

        def fake_urlopen(request, timeout):
            payload = {"chain_stats": {"funded_txo_sum": 0, "spent_txo_sum": 0, "tx_count": 0},
                       "mempool_stats": {}}
            return io.BytesIO(json.dumps(payload).encode())

        from types import SimpleNamespace
        api_args = SimpleNamespace(
            queue=api_queue, max_attempts=3, api_base="https://mock.invalid/address",
            api_timeout=1.0, api_interval=0.0,
        )
        with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
            verify_pending_queue(api_args)
        assert latest_queue_state(api_queue)["smoke"]["status"] == "bloom_false_positive"

    print(
        "[*] self-test OK: candidate loading, fingerprint/checkpoint reuse, "
        "readable-body (WIF) key-shape hit reaching Bloom+queue, hit/queue "
        "dedupe, no-match body produces no file, verify_pending_queue "
        "compatibility"
    )


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument(
        "--candidate-file", type=Path,
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
