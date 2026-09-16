#!/usr/bin/env python3
"""Raw-histogram-only Model-B fixtures for Phase 491.

This module never imports FAED.  Its only puzzle-derived values are the frozen
nine-symbol count vector and the scoped escape pair {g,i}.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
from functools import lru_cache

import numpy as np

import phase484a_raw_symbol_vic_solver as base


WIDTH, ROWS = 19, 30
PAIR = ("g", "i")
RAW_COUNTS = {
    "a": 54, "b": 49, "c": 52, "d": 49, "e": 69,
    "f": 57, "g": 107, "h": 58, "i": 75,
}
PROFILE_SEED = 0x491A001
ORDER_SEED = 0x491A002
SOURCE_REGIONS = 20
MAX_SHUFFLES = 1000
MAX_EDIT_FRACTION = 0.18
MIN_NORMALIZED_QUADGRAM = -4.70


def canonical_raw_multiset() -> list[str]:
    values = [symbol for symbol in base.NINE_SYMBOLS
              for _ in range(RAW_COUNTS[symbol])]
    if len(values) != WIDTH * ROWS:
        raise AssertionError("frozen raw histogram does not total 570")
    return values


def sampled_token_profile(fixture_index: int, split: str = "dev") -> dict:
    if fixture_index < 0:
        raise ValueError("fixture index must be nonnegative")
    if split not in base.FIXTURE_SPLITS:
        raise ValueError("unknown corpus split")
    split_index = base.FIXTURE_SPLITS.index(split)
    rng = base.PCG32(base.derive_seed(PROFILE_SEED, split_index, fixture_index))
    values = canonical_raw_multiset()
    for attempt in range(MAX_SHUFFLES):
        rng.shuffle(values)
        raw = "".join(values)
        tokens = base.segment_raw(raw, PAIR)
        if tokens is not None:
            counts = collections.Counter(tokens)
            return {
                "shuffle_attempt": attempt,
                "tokens": tokens,
                "token_counts": {code: counts[code]
                                 for code in base.slot_codes(PAIR)},
                "token_count": len(tokens),
                "single_count": sum(len(token) == 1 for token in tokens),
                "profile_sha256": hashlib.sha256(
                    json.dumps({code: counts[code]
                                for code in base.slot_codes(PAIR)},
                               sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest(),
            }
    raise RuntimeError("could not sample a valid latent token profile")


@lru_cache(maxsize=None)
def training_groups() -> tuple[tuple[str, ...], tuple[str, ...]]:
    frequencies = collections.Counter(base.corpus_splits()["train"])
    common = tuple(sorted(base.LETTER_ALPHABET,
                          key=lambda letter: (-frequencies[letter], letter))[:7])
    return common, tuple(letter for letter in base.LETTER_ALPHABET
                         if letter not in common)


def board_for_passage(passage: str, token_counts: dict[str, int]):
    passage_counts = collections.Counter(passage)
    common, other = training_groups()
    singles, doubles = base.slot_codes(PAIR)[:7], base.slot_codes(PAIR)[7:]
    board = {}
    for letters, codes in ((common, singles), (other, doubles)):
        ranked_letters = sorted(letters,
                                key=lambda x: (-passage_counts[x], x))
        ranked_codes = sorted(codes, key=lambda x: (-token_counts[x], x))
        board.update(zip(ranked_letters, ranked_codes))
    target = {letter: token_counts[code] for letter, code in board.items()}
    edits = sum(abs(passage_counts[letter] - target[letter])
                for letter in base.LETTER_ALPHABET) // 2
    return board, target, edits


def source_region(split: str, fixture_index: int) -> tuple[int, int]:
    source_length = len(base.corpus_splits()[split])
    region = fixture_index % SOURCE_REGIONS
    return (source_length * region // SOURCE_REGIONS,
            source_length * (region + 1) // SOURCE_REGIONS)


def select_passage(split: str, fixture_index: int,
                   token_counts: dict[str, int]):
    source = base.corpus_splits()[split]
    length = sum(token_counts.values())
    left, right = source_region(split, fixture_index)
    candidates = []
    for start in base.corpus_word_starts(split):
        if start < left or start + length > right:
            continue
        passage = source[start:start + length]
        board, target, edits = board_for_passage(passage, token_counts)
        candidates.append((edits, start, passage, board, target))
    if not candidates:
        raise RuntimeError("source region contains no complete passage")
    return min(candidates, key=lambda record: (record[0], record[1]))


def local_quad_score(indices: list[int], position: int, quad: np.ndarray) -> float:
    n = len(base.LETTER_ALPHABET)
    total = 0.0
    first = max(0, position - 3)
    last = min(position, len(indices) - 4)
    for start in range(first, last + 1):
        a, b, c, d = indices[start:start + 4]
        total += quad[((a * n + b) * n + c) * n + d]
    return total


def minimum_edit_plaintext(passage: str, target: dict[str, int],
                           quad: np.ndarray) -> tuple[str, int]:
    letters = base.LETTER_ALPHABET
    to_index = {letter: index for index, letter in enumerate(letters)}
    current = list(passage)
    indices = [to_index[letter] for letter in current]
    counts = collections.Counter(current)
    edit_count = sum(abs(counts[letter] - target[letter])
                     for letter in letters) // 2
    for _ in range(edit_count):
        surplus = {letter for letter in letters
                   if counts[letter] > target[letter]}
        deficits = [letter for letter in letters
                    if counts[letter] < target[letter]]
        best = None
        for position, old in enumerate(current):
            if old not in surplus:
                continue
            old_local = local_quad_score(indices, position, quad)
            old_index = indices[position]
            for new in deficits:
                new_index = to_index[new]
                indices[position] = new_index
                delta = local_quad_score(indices, position, quad) - old_local
                indices[position] = old_index
                candidate = (-delta, position, new_index, new, old)
                if best is None or candidate < best:
                    best = candidate
        if best is None:
            raise AssertionError("no legal count-correcting edit")
        _, position, new_index, new, old = best
        current[position] = new
        indices[position] = new_index
        counts[old] -= 1
        counts[new] += 1
    if any(counts[letter] != target[letter] for letter in letters):
        raise AssertionError("edited plaintext missed its target counts")
    return "".join(current), edit_count


@lru_cache(maxsize=None)
def make_fixture(fixture_index: int = 0, split: str = "dev") -> dict:
    profile = sampled_token_profile(fixture_index, split)
    edits, start, source_passage, board, target = select_passage(
        split, fixture_index, profile["token_counts"])
    quad, _ = base.load_language_model()
    plaintext, actual_edits = minimum_edit_plaintext(source_passage, target, quad)
    if actual_edits != edits:
        raise AssertionError("minimum edit count changed during application")
    raw = base.encode_plaintext(plaintext, board)
    split_index = base.FIXTURE_SPLITS.index(split)
    rng = base.PCG32(base.derive_seed(ORDER_SEED, split_index, fixture_index))
    order = rng.permutation(WIDTH)
    observed = base.Geometry(len(raw), WIDTH).encrypt(raw, order)
    values = np.asarray([base.LETTER_ALPHABET.index(x) for x in plaintext],
                        dtype=np.int64)
    normalized = base.score_indices(values, quad) / max(1, len(values) - 3)
    fixture = {
        "phase": "491", "fixture_index": fixture_index, "split": split,
        "width": WIDTH, "pair": list(PAIR),
        "board_mode": "raw_histogram_only_vic_profile",
        "source_region": list(source_region(split, fixture_index)),
        "source_start": start, "source_plaintext": source_passage,
        "plaintext": plaintext, "plaintext_length": len(plaintext),
        "minimum_edit_count": actual_edits,
        "edit_fraction": actual_edits / len(plaintext),
        "normalized_quadgram": normalized,
        "letter_to_code": board, "order": order,
        "raw": raw, "observed": observed,
        "raw_sha256": hashlib.sha256(raw.encode("ascii")).hexdigest(),
        "latent_profile_sha256": profile["profile_sha256"],
        "latent_token_count": profile["token_count"],
        "latent_single_count": profile["single_count"],
        "observed_token_count": len(base.segment_raw(observed, PAIR))
        if base.segment_raw(observed, PAIR) is not None else None,
        "observed_single_count": (sum(len(token) == 1 for token in
                                      base.segment_raw(observed, PAIR))
                                  if base.segment_raw(observed, PAIR) is not None
                                  else None),
        "profile_shuffle_attempt": profile["shuffle_attempt"],
    }
    verify_fixture(fixture)
    return fixture


def verify_fixture(fixture: dict) -> None:
    base.verify_fixture(fixture)
    if collections.Counter(fixture["raw"]) != collections.Counter(RAW_COUNTS):
        raise AssertionError("fixture missed frozen raw histogram")
    latent = base.segment_raw(fixture["raw"], PAIR)
    if latent is None or len(latent) != fixture["latent_token_count"]:
        raise AssertionError("latent segmentation metadata mismatch")
    if fixture["plaintext_length"] != fixture["latent_token_count"]:
        raise AssertionError("plaintext/token length mismatch")
    if fixture["edit_fraction"] > MAX_EDIT_FRACTION:
        raise AssertionError("fixture exceeds frozen edit-fraction gate")
    if fixture["normalized_quadgram"] < MIN_NORMALIZED_QUADGRAM:
        raise AssertionError("fixture falls below frozen language-quality gate")


def fixture_summary(fixture: dict) -> dict:
    return {key: fixture[key] for key in (
        "fixture_index", "split", "source_region", "source_start",
        "plaintext_length", "minimum_edit_count", "edit_fraction",
        "normalized_quadgram", "latent_profile_sha256",
        "latent_token_count", "latent_single_count",
        "observed_token_count", "observed_single_count", "raw_sha256")}


def build_batch(count: int = 10, start: int = 0, split: str = "dev") -> dict:
    fixtures = [make_fixture(index, split) for index in range(start, start + count)]
    profiles = [fixture["latent_profile_sha256"] for fixture in fixtures]
    if len(set(profiles)) != len(profiles):
        raise AssertionError("batch contains duplicate latent profiles")
    regions = [tuple(fixture["source_region"]) for fixture in fixtures]
    if len(set(regions)) != len(regions):
        raise AssertionError("batch reuses a source region")
    return {
        "phase": "491", "status": "raw_histogram_fixture_batch",
        "faed_order_imported": False, "split": split,
        "start": start, "count": count,
        "raw_counts": RAW_COUNTS,
        "records": [fixture_summary(fixture) for fixture in fixtures],
    }


def self_test() -> dict:
    profile = sampled_token_profile(0)
    contribution = collections.Counter("".join(
        code * count for code, count in profile["token_counts"].items()))
    if contribution != collections.Counter(RAW_COUNTS):
        raise AssertionError("sampled token profile changed raw counts")
    fixture = make_fixture(0)
    if fixture["latent_profile_sha256"] == hashlib.sha256(b"436/302").hexdigest():
        raise AssertionError("impossible sentinel collision")
    return fixture_summary(fixture)


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--batch", action="store_true")
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--split", choices=base.FIXTURE_SPLITS, default="dev")
    args = parser.parse_args()
    result = (self_test() if args.self_test else
              build_batch(args.count, args.start, args.split))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
