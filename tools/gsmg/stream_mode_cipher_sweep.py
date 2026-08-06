#!/usr/bin/env python3
"""Checkpointed curated-candidate sweep for AES CFB/OFB/CTR modes.

The OpenSSL Salted__ envelope does not identify cipher mode. This tests the
bounded 36-variant AES CFB/OFB/CTR family against all tracked blobs while
binding checkpoints to the exact candidates, blobs, variants, oracle source,
and driver source. Every target is tested separately so a hit on one blob
cannot prevent inspection of another.
"""

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

import cb_common
from cb_common import (
    BLOBS,
    QUARANTINED_BLOBS,
    STREAM_CIPHER_VARIANTS,
    aes_try_open_stream,
    answer_forms,
    keystr_forms,
)
from extended_cipher_recheck import candidate_list_digest, load_curated_candidates

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CHECKPOINT = SCRIPT_DIR / "stream_mode_cipher_checkpoint.jsonl"
DEFAULT_HITS = SCRIPT_DIR / "stream_mode_cipher_hits.jsonl"
ALL_BLOBS = {**BLOBS, **QUARANTINED_BLOBS}


def append_jsonl(path, record, sensitive=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_APPEND,
        0o600 if sensitive else 0o644,
    )
    try:
        if sensitive:
            os.fchmod(descriptor, 0o600)
        os.write(descriptor, (json.dumps(record, sort_keys=True) + "\n").encode())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def load_candidates(candidate_file=None):
    if candidate_file is None:
        return load_curated_candidates()
    seen = set()
    candidates = []
    for line in Path(candidate_file).read_text(errors="replace").splitlines():
        candidate = line.strip()
        if candidate and candidate not in seen:
            seen.add(candidate)
            candidates.append(candidate)
    return candidates


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


def run_fingerprint(candidates, keystrings, blobs):
    blob_digest = hashlib.sha256()
    for tag, (salt, ciphertext) in blobs.items():
        blob_digest.update(tag.encode() + b"\0" + salt + ciphertext)
    return {
        "version": 2,
        "candidate_count": len(candidates),
        "candidate_digest": candidate_list_digest(candidates),
        "keystring_count": len(keystrings),
        "blob_digest": blob_digest.hexdigest()[:16],
        "variant_count": len(STREAM_CIPHER_VARIANTS),
        "variant_digest": hashlib.sha256(
            repr(STREAM_CIPHER_VARIANTS).encode()
        ).hexdigest()[:16],
        "oracle_sha256": hashlib.sha256(
            Path(cb_common.__file__).read_bytes()
        ).hexdigest()[:16],
        "driver_sha256": hashlib.sha256(
            Path(__file__).read_bytes()
        ).hexdigest()[:16],
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


def sweep(candidates, blobs, checkpoint, hits_path, limit=None):
    keystrings = normalized_keystrings(candidates)
    if limit is not None:
        keystrings = keystrings[:limit]
    fingerprint = run_fingerprint(candidates, keystrings, blobs)
    completed = load_checkpoint(checkpoint, fingerprint)
    ensure_checkpoint_header(checkpoint, fingerprint)
    total_operations = (
        len(keystrings) * len(STREAM_CIPHER_VARIANTS) * len(blobs)
    )
    print(
        f"[*] candidates={len(candidates):,} "
        f"digest={fingerprint['candidate_digest']} "
        f"keystrings={len(keystrings):,} operations={total_operations:,}"
    )
    hit_count = 0
    for index, (candidate, form, keystr) in enumerate(keystrings):
        keystr_digest = hashlib.sha256(keystr.encode()).hexdigest()
        if keystr_digest in completed:
            continue
        per_key_hits = 0
        for tag, blob in blobs.items():
            result = aes_try_open_stream(
                keystr,
                kdf_variants=STREAM_CIPHER_VARIANTS,
                blobs={tag: blob},
            )
            if not result:
                continue
            result_tag, plaintext, kdf_label, key_len = result
            append_jsonl(hits_path, {
                "candidate": candidate,
                "form": form,
                "passphrase_hex": keystr.encode().hex(),
                "blob": result_tag,
                "kdf": kdf_label,
                "key_bits": key_len * 8,
                "plaintext_hex": plaintext.hex(),
                "plaintext_sha256": hashlib.sha256(plaintext).hexdigest(),
            }, sensitive=True)
            print(
                f"[+++ HIT] {result_tag} {kdf_label}/{key_len * 8} "
                f"preview={plaintext[:200]!r}"
            )
            per_key_hits += 1
            hit_count += 1
        append_jsonl(checkpoint, {
            "index": index,
            "keystr_sha256": keystr_digest,
            "hits": per_key_hits,
        })
        if (index + 1) % 250 == 0 or index + 1 == len(keystrings):
            print(f"[*] progress {index + 1:,}/{len(keystrings):,}")
    return {
        "keystrings": len(keystrings),
        "operations": total_operations,
        "hits": hit_count,
    }


def self_test():
    with tempfile.TemporaryDirectory() as directory:
        checkpoint = Path(directory) / "checkpoint.jsonl"
        candidates = ["Alpha", "Beta"]
        keystrings = normalized_keystrings(candidates)
        fingerprint = run_fingerprint(candidates, keystrings, {"SYNTH": (b"12345678", b"x")})
        ensure_checkpoint_header(checkpoint, fingerprint)
        digest = hashlib.sha256(keystrings[0][2].encode()).hexdigest()
        append_jsonl(checkpoint, {
            "index": 0,
            "keystr_sha256": digest,
            "hits": 0,
        })
        assert load_checkpoint(checkpoint, fingerprint) == {digest}
        changed = {**fingerprint, "driver_sha256": "changed"}
        try:
            load_checkpoint(checkpoint, changed)
        except ValueError:
            pass
        else:
            raise AssertionError("mismatched source fingerprint was accepted")
    print("[*] self-test OK: deterministic forms, checkpoint resume, source guard")


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-file", type=Path)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--hits", type=Path, default=DEFAULT_HITS)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.self_test:
        self_test()
        return
    candidates = load_candidates(args.candidate_file)
    result = sweep(
        candidates,
        ALL_BLOBS,
        args.checkpoint,
        args.hits,
        limit=args.limit,
    )
    if not result["hits"]:
        print("[*] no candidate opened any blob under CFB/OFB/CTR")


if __name__ == "__main__":
    main()
