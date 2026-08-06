#!/usr/bin/env python3
"""Bounded cross-target coupling sweep for dbbi/faed.

This closes the lower-priority coupling variants left by chain_sweep.py:

  1. reverse chain:
       candidate -> decode(faed) -> derived board -> decode(dbbi) -> AES
  2. raw coupling:
       fold faed to 91 symbols and add/subtract it with dbbi;
       repeat dbbi over faed and add/subtract it with faed;
       test raw/base-9 forms and clue-derived checkerboard decodes.

The statistically negative dual-ternary branch is deliberately excluded.

Usage:
    python3 tools/gsmg/cross_target_coupling_sweep.py --self-test --mode raw
    python3 tools/gsmg/cross_target_coupling_sweep.py --mode reverse
    python3 tools/gsmg/cross_target_coupling_sweep.py --mode both --workers 16
"""
import argparse
import hashlib
import json
import os
import sys
import time
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from itertools import islice
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cb_common import (  # noqa: E402
    aes_try_open,
    aes_try_open_bytes,
    answer_forms,
    decode_9ary,
    keystr_forms,
    pad25,
)
from data import DBBI, FAED, VALIDATION_ANSWER  # noqa: E402

NINE = "abcdefghi"
NINE_INDEX = {symbol: index for index, symbol in enumerate(NINE)}
ESCAPE_ORDERS = (
    ("b", "e"), ("e", "b"),
    ("g", "i"), ("i", "g"),
    ("h", "e"), ("e", "h"),
)
CORE_ALPHABET_SEEDS = (
    "matrixsumlist",
    "lastwordsbeforearchichoice",
    "thispassword",
    "yinyang",
    "cosmicduality",
    "salphaseion",
    "yellowblueprimes",
    "theproblemischoice",
    "ourfirsthintisyourlastcommand",
    VALIDATION_ANSWER,
)
DEFAULT_WORDLISTS = ("wordlists/gsmg/session_combined_for_chain.txt",)


def to_values(text):
    return [NINE_INDEX[symbol] for symbol in text]


def to_symbols(values):
    return "".join(NINE[value % 9] for value in values)


def contiguous_groups(values, count):
    return [
        values[(index * len(values)) // count:((index + 1) * len(values)) // count]
        for index in range(count)
    ]


def fold_faed(method):
    values = to_values(FAED)
    target_length = len(DBBI)
    if method == "residue_sum":
        buckets = [[] for _ in range(target_length)]
        for index, value in enumerate(values):
            buckets[index % target_length].append(value)
        return [sum(bucket) % 9 for bucket in buckets]
    groups = contiguous_groups(values, target_length)
    if method == "contiguous_sum":
        return [sum(group) % 9 for group in groups]
    if method == "contiguous_first":
        return [group[0] for group in groups]
    if method == "contiguous_last":
        return [group[-1] for group in groups]
    if method == "first_91":
        return values[:target_length]
    if method == "last_91":
        return values[-target_length:]
    raise ValueError(method)


FOLD_METHODS = (
    "residue_sum",
    "contiguous_sum",
    "contiguous_first",
    "contiguous_last",
    "first_91",
    "last_91",
)


def combine_values(left, right, operation):
    if operation == "add":
        return [(a + b) % 9 for a, b in zip(left, right)]
    if operation == "left_minus_right":
        return [(a - b) % 9 for a, b in zip(left, right)]
    if operation == "right_minus_left":
        return [(b - a) % 9 for a, b in zip(left, right)]
    raise ValueError(operation)


OPERATIONS = ("add", "left_minus_right", "right_minus_left")


def derived_streams():
    output = {}
    dbbi_values = to_values(DBBI)
    faed_values = to_values(FAED)

    for method in FOLD_METHODS:
        folded = fold_faed(method)
        for operation in OPERATIONS:
            output[f"fold/{method}/{operation}"] = to_symbols(
                combine_values(dbbi_values, folded, operation)
            )
        masks = {
            "prime": {2, 3, 5, 7},
            "even": {0, 2, 4, 6, 8},
            "nonzero": set(range(1, 9)),
        }
        for mask_name, accepted in masks.items():
            output[f"select/{method}/{mask_name}"] = "".join(
                symbol
                for symbol, selector in zip(DBBI, folded)
                if selector in accepted
            )

    for repeat_name, repeated in (
        ("forward", [dbbi_values[index % len(dbbi_values)] for index in range(len(FAED))]),
        ("reverse", [
            dbbi_values[::-1][index % len(dbbi_values)]
            for index in range(len(FAED))
        ]),
    ):
        for operation in OPERATIONS:
            output[f"repeat/{repeat_name}/{operation}"] = to_symbols(
                combine_values(faed_values, repeated, operation)
            )
    return output


def base9_bytes(text):
    value = 0
    for symbol in text:
        value = value * 9 + NINE_INDEX[symbol]
    length = max(1, (value.bit_length() + 7) // 8)
    return value.to_bytes(length, "big")


def check_text_answer(answer, metadata):
    hits = []
    attempts = 0
    if "?" in answer:
        return attempts, hits
    tested = set()
    for form in answer_forms(answer):
        if not form:
            continue
        for keystring in keystr_forms(form):
            if keystring in tested:
                continue
            tested.add(keystring)
            attempts += 1
            result = aes_try_open(keystring)
            if result:
                tag, plaintext, digest_name, key_len = result
                hits.append({
                    **metadata,
                    "answer": answer,
                    "form": form,
                    "passphrase": keystring,
                    "blob": tag,
                    "kdf": f"{digest_name}/aes{key_len * 8}",
                    "plaintext": plaintext[:500].decode("utf-8", errors="replace"),
                })
    return attempts, hits


def run_raw_coupling():
    attempts = 0
    hits = []
    streams = derived_streams()
    alphabets = {pad25(seed) for seed in CORE_ALPHABET_SEEDS}

    for label, stream in streams.items():
        materials = {
            "symbols": stream.encode(),
            "digits_a0i8": "".join(str(NINE_INDEX[symbol]) for symbol in stream).encode(),
            "digits_a1i9": "".join(str(NINE_INDEX[symbol] + 1) for symbol in stream).encode(),
            "base9_raw": base9_bytes(stream),
            "base9_hex": base9_bytes(stream).hex().encode(),
        }
        tested_materials = set()
        for representation, material in materials.items():
            if material in tested_materials:
                continue
            tested_materials.add(material)
            for passphrase in (material, hashlib.sha256(material).hexdigest().encode()):
                attempts += 1
                result = aes_try_open_bytes(passphrase)
                if result:
                    tag, plaintext, digest_name, key_len = result
                    hits.append({
                        "mode": "raw",
                        "stream": label,
                        "representation": representation,
                        "passphrase_hex": passphrase.hex(),
                        "blob": tag,
                        "kdf": f"{digest_name}/aes{key_len * 8}",
                        "plaintext": plaintext[:500].decode("utf-8", errors="replace"),
                    })

        if len(stream) < 20:
            continue
        for alphabet in alphabets:
            for topology in ("top_first", "escapes_first"):
                for first_escape, second_escape in ESCAPE_ORDERS:
                    answer = decode_9ary(
                        stream,
                        alphabet,
                        first_escape,
                        second_escape,
                        topology,
                    )
                    answer_attempts, answer_hits = check_text_answer(
                        answer,
                        {
                            "mode": "raw_checkerboard",
                            "stream": label,
                            "alphabet": alphabet,
                            "topology": topology,
                            "escapes": (first_escape, second_escape),
                        },
                    )
                    attempts += answer_attempts
                    hits.extend(answer_hits)
    return len(streams), attempts, hits


def load_candidates(paths):
    output = []
    seen = set()
    for path_string in paths:
        path = Path(path_string)
        if not path.exists():
            print(f"[!] missing wordlist: {path}", file=sys.stderr)
            continue
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            candidate = line.strip()
            if candidate and candidate not in seen:
                seen.add(candidate)
                output.append(candidate)
    return output


def test_reverse_candidate(candidate):
    attempts = 0
    hits = []
    first_alphabet = pad25(candidate)
    second_alphabets = set()
    for first_escape, second_escape in ESCAPE_ORDERS:
        decoded_faed = decode_9ary(
            FAED,
            first_alphabet,
            first_escape,
            second_escape,
            "top_first",
        )
        if "?" in decoded_faed:
            continue
        for form in answer_forms(decoded_faed):
            if form:
                second_alphabets.add(pad25(form))

    tested_answers = set()
    for second_alphabet in second_alphabets:
        for first_escape, second_escape in ESCAPE_ORDERS:
            decoded_dbbi = decode_9ary(
                DBBI,
                second_alphabet,
                first_escape,
                second_escape,
                "top_first",
            )
            if "?" in decoded_dbbi:
                continue
            if decoded_dbbi in tested_answers:
                continue
            tested_answers.add(decoded_dbbi)
            answer_attempts, answer_hits = check_text_answer(
                decoded_dbbi,
                {
                    "mode": "reverse_chain",
                    "candidate": candidate,
                    "derived_alphabet": second_alphabet,
                    "escapes": (first_escape, second_escape),
                },
            )
            attempts += answer_attempts
            hits.extend(answer_hits)
    return attempts, hits


def test_reverse_batch(batch):
    attempts = 0
    hits = []
    for candidate in batch:
        candidate_attempts, candidate_hits = test_reverse_candidate(candidate)
        attempts += candidate_attempts
        hits.extend(candidate_hits)
    return len(batch), attempts, hits


def run_reverse_chain(candidates, workers, chunk_size):
    chunks = [
        candidates[index:index + chunk_size]
        for index in range(0, len(candidates), chunk_size)
    ]
    done = 0
    attempts = 0
    hits = []
    start = time.time()
    max_in_flight = max(workers * 4, 8)
    with ProcessPoolExecutor(max_workers=workers) as executor:
        chunk_iter = iter(chunks)
        in_flight = {}
        for chunk in islice(chunk_iter, max_in_flight):
            in_flight[executor.submit(test_reverse_batch, chunk)] = len(chunk)
        while in_flight:
            completed, _ = wait(in_flight, return_when=FIRST_COMPLETED)
            for future in completed:
                in_flight.pop(future)
                count, batch_attempts, batch_hits = future.result()
                done += count
                attempts += batch_attempts
                hits.extend(batch_hits)
                for hit in batch_hits:
                    print(f"\n[+++ AES HIT] {hit}\n")
                next_chunk = next(chunk_iter, None)
                if next_chunk is not None:
                    in_flight[executor.submit(test_reverse_batch, next_chunk)] = len(next_chunk)
            elapsed = time.time() - start
            rate = done / max(elapsed, 1e-9)
            print(
                f"\r[*] reverse chain {done:,}/{len(candidates):,} "
                f"({rate:.1f}/s), {attempts:,} passphrases, hits={len(hits)}   ",
                end="",
                flush=True,
            )
    print()
    return attempts, hits


def run_self_tests():
    assert len(DBBI) == 91
    assert all(len(fold_faed(method)) == len(DBBI) for method in FOLD_METHODS)
    groups = contiguous_groups(list(range(10)), 3)
    assert groups == [[0, 1, 2], [3, 4, 5], [6, 7, 8, 9]]
    assert combine_values([8, 0], [1, 1], "add") == [0, 1]
    assert combine_values([0], [1], "left_minus_right") == [8]
    assert to_symbols(to_values("abcdefghi")) == "abcdefghi"
    streams = derived_streams()
    assert streams
    assert all(set(stream) <= set(NINE) for stream in streams.values())
    print(f"[*] cross-target self-tests passed ({len(streams)} derived streams)")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--mode", choices=("raw", "reverse", "both"), default="both")
    parser.add_argument("--wordlist", action="append")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--workers", type=int, default=min(os.cpu_count() or 4, 16))
    parser.add_argument("--chunk-size", type=int, default=50)
    parser.add_argument("--json-out")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        run_self_tests()

    report = {"raw": {}, "reverse": {}, "hits": []}
    all_hits = []
    if args.mode in ("raw", "both"):
        stream_count, attempts, hits = run_raw_coupling()
        report["raw"] = {
            "derived_streams": stream_count,
            "passphrase_attempts": attempts,
            "aes_hits": len(hits),
        }
        all_hits.extend(hits)
        print(
            f"[*] raw coupling: {stream_count} streams, "
            f"{attempts:,} passphrases, {len(hits)} hits"
        )

    if args.mode in ("reverse", "both"):
        candidates = load_candidates(args.wordlist or DEFAULT_WORDLISTS)
        if args.limit:
            candidates = candidates[:args.limit]
        print(f"[*] reverse chain: {len(candidates):,} candidate alphabets")
        attempts, hits = run_reverse_chain(candidates, args.workers, args.chunk_size)
        report["reverse"] = {
            "candidate_alphabets": len(candidates),
            "passphrase_attempts": attempts,
            "aes_hits": len(hits),
        }
        all_hits.extend(hits)

    report["hits"] = all_hits
    if args.json_out:
        output_path = Path(args.json_out)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"[*] wrote JSON report to {output_path}")
    if not all_hits:
        print("[*] no cross-target coupling candidate opened either AES blob")


if __name__ == "__main__":
    main()
