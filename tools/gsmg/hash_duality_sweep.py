#!/usr/bin/env python3
"""Test "last command" + "ans too" as a dual-hash construction.

The solved phases establish four verified SHA-256 command states (see
data.VERIFIED_PRIOR_COMMAND_HASHES for derivations). The strongest "your last command"
candidate is the final 89727... hash used to enter the SalPhaseIon page. For each
candidate answer this script combines each prior state with SHA256(answer) using
concatenation, XOR, SHA-256, and HMAC-SHA256.

Both binary 32-byte digests and 64-character hexadecimal representations are
tested byte-exactly against the real AES oracle. Candidate answers come from the
known clue phrases and, optionally, the bounded matrix-instruction pipeline.

Usage:
    python3 tools/gsmg/hash_duality_sweep.py --self-test --scope core
    python3 tools/gsmg/hash_duality_sweep.py --scope all
    python3 tools/gsmg/hash_duality_sweep.py --primary-hash-only
    python3 tools/gsmg/hash_duality_sweep.py --newline-variants
"""
import argparse
import hashlib
import hmac
import json
import os
import sys
import time
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from itertools import islice
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cb_common import aes_try_open_bytes  # noqa: E402
from data import PRIOR_COMMAND_HASHES, VALIDATION_ANSWER  # noqa: E402
from matrix_instruction_sweep import (  # noqa: E402
    generate_extraction_candidates,
    generate_matrix_candidates,
    compose_candidates,
)

CORE_CANDIDATES = {
    "validation_answer": VALIDATION_ANSWER,
    "matrixsumlist": "matrixsumlist",
    "lastwordsbeforearchichoice": "lastwordsbeforearchichoice",
    "thispassword": "thispassword",
    "enter": "enter",
    "first_hint_last_command": "ourfirsthintisyourlastcommand",
    "answer_too": "anstoo",
    "yin_yang": "yinyang",
    "cosmic_duality": "cosmicduality",
    "salphaseion": "salphaseion",
}


def xor_bytes(left, right):
    if len(left) != len(right):
        raise ValueError("XOR inputs must have equal length")
    return bytes(a ^ b for a, b in zip(left, right))


def operation_materials(previous_hex, answer):
    answer_bytes = answer.encode()
    previous_binary = bytes.fromhex(previous_hex)
    answer_hash_binary = hashlib.sha256(answer_bytes).digest()
    previous_text = previous_hex.encode()
    answer_hash_text = hashlib.sha256(answer_bytes).hexdigest().encode()

    binary_xor = xor_bytes(previous_binary, answer_hash_binary)
    text_xor = xor_bytes(previous_text, answer_hash_text)

    return {
        "binary/sha256(previous+answer)": hashlib.sha256(
            previous_binary + answer_bytes
        ).digest(),
        "binary/sha256(answer+previous)": hashlib.sha256(
            answer_bytes + previous_binary
        ).digest(),
        "binary/previous_xor_sha256answer": binary_xor,
        "binary/sha256(previous_xor_sha256answer)": hashlib.sha256(binary_xor).digest(),
        "binary/hmac_previous_answer": hmac.new(
            previous_binary, answer_bytes, hashlib.sha256
        ).digest(),
        "binary/hmac_sha256answer_previous": hmac.new(
            answer_hash_binary, previous_binary, hashlib.sha256
        ).digest(),
        "binary/previous+sha256answer": previous_binary + answer_hash_binary,
        "binary/sha256answer+previous": answer_hash_binary + previous_binary,
        "hex/sha256(previous+answer)": hashlib.sha256(
            previous_text + answer_bytes
        ).digest(),
        "hex/sha256(answer+previous)": hashlib.sha256(
            answer_bytes + previous_text
        ).digest(),
        "hex/previous_xor_sha256answer": text_xor,
        "hex/sha256(previous_xor_sha256answer)": hashlib.sha256(text_xor).digest(),
        "hex/hmac_previous_answer": hmac.new(
            previous_text, answer_bytes, hashlib.sha256
        ).digest(),
        "hex/hmac_sha256answer_previous": hmac.new(
            answer_hash_text, previous_text, hashlib.sha256
        ).digest(),
        "hex/previous+sha256answer": previous_text + answer_hash_text,
        "hex/sha256answer+previous": answer_hash_text + previous_text,
    }


def material_forms(material, newline_variants):
    forms = [("raw", material), ("hex", material.hex().encode())]
    if newline_variants:
        forms.extend([
            ("raw_lf", material + b"\n"),
            ("raw_crlf", material + b"\r\n"),
            ("hex_lf", material.hex().encode() + b"\n"),
            ("hex_crlf", material.hex().encode() + b"\r\n"),
        ])
    output = []
    seen = set()
    for label, body in forms:
        if body not in seen:
            seen.add(body)
            output.append((label, body))
    return output


def test_candidate(candidate, prior_hashes, newline_variants):
    candidate_label, answer = candidate
    tested = set()
    attempts = 0
    hits = []
    for prior_label, previous_hex in prior_hashes:
        for operation, material in operation_materials(previous_hex, answer).items():
            for representation, passphrase in material_forms(material, newline_variants):
                if passphrase in tested:
                    continue
                tested.add(passphrase)
                attempts += 1
                result = aes_try_open_bytes(passphrase)
                if result:
                    tag, plaintext, digest_name, key_len = result
                    hits.append({
                        "candidate_label": candidate_label,
                        "answer": answer,
                        "prior_hash": prior_label,
                        "operation": operation,
                        "representation": representation,
                        "passphrase_hex": passphrase.hex(),
                        "blob": tag,
                        "kdf": f"{digest_name}/aes{key_len * 8}",
                        "plaintext": plaintext[:500].decode("utf-8", errors="replace"),
                    })
    return attempts, hits


def test_batch(batch, prior_hashes, newline_variants):
    attempts = 0
    hits = []
    for candidate in batch:
        candidate_attempts, candidate_hits = test_candidate(
            candidate, prior_hashes, newline_variants
        )
        attempts += candidate_attempts
        hits.extend(candidate_hits)
    return len(batch), attempts, hits


def collect_candidates(scope):
    candidates = {value: label for label, value in CORE_CANDIDATES.items()}
    if scope == "core":
        return candidates

    matrix_candidates = generate_matrix_candidates()
    extraction_candidates = generate_extraction_candidates({}, max_words=13)
    for candidate in (*matrix_candidates.values(), *extraction_candidates.values()):
        candidates.setdefault(candidate.value, candidate.label)
    if scope == "matrix":
        return candidates

    composed_candidates = compose_candidates(matrix_candidates, extraction_candidates)
    for candidate in composed_candidates.values():
        candidates.setdefault(candidate.value, candidate.label)
    return candidates


def selected_prior_hashes(primary_only):
    if primary_only:
        return [("salphaseion_entry", PRIOR_COMMAND_HASHES["salphaseion_entry"])]
    return list(PRIOR_COMMAND_HASHES.items())


def run_self_tests():
    assert len(PRIOR_COMMAND_HASHES) == 4
    assert all(len(value) == 64 for value in PRIOR_COMMAND_HASHES.values())
    assert xor_bytes(b"\x00\xff", b"\xff\x0f") == b"\xff\xf0"
    materials = operation_materials(
        PRIOR_COMMAND_HASHES["salphaseion_entry"],
        "answer",
    )
    assert len(materials) == 16
    assert all(len(value) in (32, 64, 128) for value in materials.values())
    assert len(material_forms(b"\x00\xff", False)) == 2
    assert len(material_forms(b"\x00\xff", True)) == 6
    text_result = aes_try_open_bytes(b"test")
    assert text_result is None
    print("[*] hash-duality self-tests passed")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--scope",
        choices=("core", "matrix", "all"),
        default="all",
        help="candidate-answer source: core clues, matrix outputs, or all composed outputs",
    )
    parser.add_argument(
        "--primary-hash-only",
        action="store_true",
        help="use only the final 89727... SalPhaseIon-entry hash",
    )
    parser.add_argument("--newline-variants", action="store_true")
    parser.add_argument("--workers", type=int, default=min(os.cpu_count() or 4, 16))
    parser.add_argument("--chunk-size", type=int, default=20)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--json-out")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        run_self_tests()

    candidate_map = collect_candidates(args.scope)
    candidates = [(label, value) for value, label in candidate_map.items()]
    if args.limit:
        candidates = candidates[:args.limit]
    prior_hashes = selected_prior_hashes(args.primary_hash_only)
    chunks = [
        candidates[index:index + args.chunk_size]
        for index in range(0, len(candidates), args.chunk_size)
    ]
    print(
        f"[*] {len(candidates):,} answer candidates x {len(prior_hashes)} prior hashes, "
        f"{args.workers} workers, newline_variants={args.newline_variants}"
    )

    start = time.time()
    completed_candidates = 0
    attempts = 0
    hits = []
    max_in_flight = max(args.workers * 4, 8)
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        chunk_iter = iter(chunks)
        in_flight = {}
        for chunk in islice(chunk_iter, max_in_flight):
            future = executor.submit(
                test_batch, chunk, prior_hashes, args.newline_variants
            )
            in_flight[future] = len(chunk)

        while in_flight:
            completed, _ = wait(in_flight, return_when=FIRST_COMPLETED)
            for future in completed:
                in_flight.pop(future)
                count, batch_attempts, batch_hits = future.result()
                completed_candidates += count
                attempts += batch_attempts
                hits.extend(batch_hits)
                for hit in batch_hits:
                    print(f"\n[+++ AES HIT] {hit}\n")
                next_chunk = next(chunk_iter, None)
                if next_chunk is not None:
                    next_future = executor.submit(
                        test_batch,
                        next_chunk,
                        prior_hashes,
                        args.newline_variants,
                    )
                    in_flight[next_future] = len(next_chunk)
            elapsed = time.time() - start
            rate = completed_candidates / max(elapsed, 1e-9)
            print(
                f"\r[*] {completed_candidates:,}/{len(candidates):,} candidates "
                f"({rate:.1f}/s), {attempts:,} passphrases, hits={len(hits)}   ",
                end="",
                flush=True,
            )
    print()

    elapsed = time.time() - start
    stats = {
        "scope": args.scope,
        "answer_candidates": len(candidates),
        "prior_hashes": len(prior_hashes),
        "passphrase_attempts": attempts,
        "aes_hits": len(hits),
        "elapsed_seconds": round(elapsed, 3),
    }
    print(f"[*] completed in {elapsed:.1f}s: {attempts:,} passphrases, {len(hits)} hits")
    if not hits:
        print("[*] no hash-duality candidate opened either AES blob")

    if args.json_out:
        output_path = Path(args.json_out)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps({"stats": stats, "hits": hits}, indent=2),
            encoding="utf-8",
        )
        print(f"[*] wrote JSON report to {output_path}")


if __name__ == "__main__":
    main()
