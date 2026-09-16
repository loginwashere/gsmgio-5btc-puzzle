#!/usr/bin/env python3
"""Locked Phase-512G exact credential-crib search against FAED."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

from data import FAED
import phase512a_transposition_crib_feasibility as phase512a
import phase512d_length_pattern_csp as phase512d
import phase512e_parallel_blind_crib as phase512e


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
PROTOCOL = (REPO_ROOT / "doc" / "Brainstorms" /
            "2026-09-15 - Phase 512G Locked FAED Width15 Credential Crib.md")
LOCK = SCRIPT_DIR / "phase512g_execution_lock.json"
RESULT = SCRIPT_DIR / "phase512g_result.json"
HITS = SCRIPT_DIR / "phase512g_sensitive_hits.json"
CHECKPOINT = REPO_ROOT / "_work" / "phase512g" / "checkpoint.json"

PHASE = "512G"
CRIB_ID = "phase1_credential"
CRIB = phase512a.CRIBS[CRIB_ID]
WIDTH = 15
WORKERS = 16
NODE_LIMIT = 2_000_000
PATTERN_SHARDS = 1
START_COUNT = len(FAED) - len(CRIB) + 1


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def lock_payload() -> dict:
    patterns = tuple(phase512d.length_patterns(CRIB))
    return {
        "phase": PHASE,
        "status": "locked_before_faed_crib_search",
        "files_sha256": {
            "protocol": sha_file(PROTOCOL),
            "runner": sha_file(Path(__file__)),
            "phase512a": sha_file(Path(phase512a.__file__)),
            "phase512d": sha_file(Path(phase512d.__file__)),
            "phase512e": sha_file(Path(phase512e.__file__)),
        },
        "faed_ascii_sha256": sha_bytes(FAED.encode("ascii")),
        "faed_length": len(FAED),
        "crib_id": CRIB_ID,
        "crib_ascii_sha256": sha_bytes(CRIB.encode("ascii")),
        "crib_length": len(CRIB),
        "width": WIDTH,
        "rows": len(FAED) // WIDTH,
        "direction": "untranspose_geometry_decrypt",
        "escape_pairs": [list(value) for value in phase512a.base.ESCAPE_PAIRS],
        "raw_start_begin": 0,
        "raw_start_count": START_COUNT,
        "legal_length_pattern_count": len(patterns),
        "length_patterns_sha256": phase512e.patterns_sha256(patterns),
        "per_pair_start_node_limit": NODE_LIMIT,
        "workers": WORKERS,
        "pattern_shards": PATTERN_SHARDS,
        "acceptance": "exact legal-board CSP match of the complete frozen crib",
    }


def verify_lock() -> dict:
    if not LOCK.is_file():
        raise RuntimeError("Phase-512G execution lock is absent")
    actual = json.loads(LOCK.read_text())
    expected = lock_payload()
    if actual != expected:
        raise RuntimeError("Phase-512G execution lock mismatch")
    return actual


def real_fixture() -> dict:
    return {
        "fixture_kind": "real_faed",
        "crib_id": CRIB_ID,
        "fixture_index": 0,
        "crib": CRIB,
        "width": WIDTH,
        "observed": FAED,
    }


def order_from_column_to_chunk(mapping) -> list[int]:
    if len(mapping) != WIDTH or set(mapping) != set(range(WIDTH)):
        raise ValueError("column-to-chunk mapping is not a permutation")
    order = [0] * WIDTH
    for column, chunk in enumerate(mapping):
        order[chunk] = column
    return order


def decode_hit(raw_start: int, pair, hit: dict) -> dict:
    order = order_from_column_to_chunk(hit["column_to_chunk"])
    raw = phase512a.base.Geometry(len(FAED), WIDTH).decrypt(FAED, order)
    if phase512a.base.segment_raw(raw[:raw_start], tuple(pair)) is None:
        raise AssertionError("hit begins inside a checkerboard token")
    singles = frozenset(hit["single_letters"])
    cursor = raw_start
    letter_to_code = {}
    code_to_letter = {}
    for letter in CRIB:
        length = 1 if letter in singles else 2
        code = raw[cursor:cursor + length]
        cursor += length
        if letter in letter_to_code and letter_to_code[letter] != code:
            raise AssertionError("hit does not assign one code per crib letter")
        if code in code_to_letter and code_to_letter[code] != letter:
            raise AssertionError("hit board is not injective")
        letter_to_code[letter] = code
        code_to_letter[code] = letter
    if "".join(code_to_letter[raw_code] for raw_code in
               phase512a.base.segment_raw(raw[raw_start:cursor], tuple(pair))) != CRIB:
        raise AssertionError("hit does not decode to the frozen crib")
    segmented = phase512a.base.segment_raw(raw, tuple(pair))
    if segmented is None:
        raise AssertionError("hit does not produce a fully segmentable stream")
    partial_plaintext = ("".join(code_to_letter.get(code, "?") for code in segmented)
                         if segmented is not None else None)
    return {
        "raw_start": raw_start,
        "raw_end": cursor,
        "pair": list(pair),
        "order": order,
        "column_to_chunk": hit["column_to_chunk"],
        "single_letters": hit["single_letters"],
        "letter_to_code": dict(sorted(letter_to_code.items())),
        "restored_raw_sha256": sha_bytes(raw.encode("ascii")),
        "partial_plaintext": partial_plaintext,
        "crib_verified_exact": True,
    }


def self_test() -> dict:
    if len(FAED) != 570 or len(CRIB) != 53 or START_COUNT != 518:
        raise AssertionError("frozen input dimensions changed")
    fixture = phase512a.make_fixture(CRIB_ID, WIDTH)
    real_like = {key: fixture[key] for key in
                 ("crib_id", "crib", "width", "observed")}
    singles = phase512d.true_single_letters(fixture)
    result = phase512d.search_lengths_at_start(
        real_like, fixture["planted_raw_offset"], 100_000,
        patterns=(singles,), pair=phase512a.PAIR)
    if result["hit_count"] != 1 or result["first_hit_exact_truth"] is not None:
        raise AssertionError("truth-agnostic CSP self-test failed")
    return {"self_test": "pass", "faed_length": 570,
            "pair_start_cells": START_COUNT * 36,
            "legal_length_patterns": len(tuple(phase512d.length_patterns(CRIB)))}


def atomic_json(path: Path, value: dict, mode: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if mode is None:
        temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    else:
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
    temporary.replace(path)


def run() -> dict:
    locked = verify_lock()
    if RESULT.exists() or HITS.exists():
        raise FileExistsError("refusing to overwrite or repeat Phase-512G")
    search = phase512e.scan_fixture(
        real_fixture(), workers=WORKERS, per_cell_node_limit=NODE_LIMIT,
        start_begin=0, start_count=START_COUNT, checkpoint_path=CHECKPOINT,
        pattern_shards=PATTERN_SHARDS)
    decoded_hits = [
        decode_hit(cell["raw_start"], cell["pair"], hit)
        for cell in search["hit_cells"]
        for hit in cell["hits"]
    ]
    if decoded_hits:
        atomic_json(HITS, {"phase": PHASE, "hits": decoded_hits}, mode=0o600)
    complete = (search["status"] in {
        "hit_at_earliest_completed_start",
        "no_hit_in_complete_requested_family",
    } and not search["incomplete_cells"])
    result = {
        "phase": PHASE,
        "status": "locked_faed_crib_search_complete" if complete else "incomplete",
        "execution_lock_sha256": sha_file(LOCK),
        "faed_ascii_sha256": locked["faed_ascii_sha256"],
        "crib_ascii_sha256": locked["crib_ascii_sha256"],
        "width": WIDTH,
        "direction": locked["direction"],
        "starts_completed": search["starts_completed"],
        "pair_start_cells_completed": search["pair_start_cells_completed"],
        "hit_count": len(decoded_hits),
        "incomplete_cell_count": len(search["incomplete_cells"]),
        "checkpoint_sha256": sha_file(CHECKPOINT),
        "verdict": ("exact_hit_requires_review" if decoded_hits else
                    "bounded_negative" if complete else "non_interpretable"),
    }
    atomic_json(RESULT, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--print-lock", action="store_true")
    group.add_argument("--verify-lock", action="store_true")
    group.add_argument("--run", action="store_true")
    args = parser.parse_args()
    value = (self_test() if args.self_test else lock_payload()
             if args.print_lock else verify_lock()
             if args.verify_lock else run())
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
