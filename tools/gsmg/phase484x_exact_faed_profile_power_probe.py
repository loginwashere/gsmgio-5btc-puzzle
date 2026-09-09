#!/usr/bin/env python3
"""Development power probe at FAED's exact {g,i} marginal profile.

Only the already-recorded token and raw-symbol histograms are imported as
constants.  No FAED ordering or content is used.  Plaintexts start as
closed-corpus development passages and receive the minimum number of
score-aware substitutions needed to match the 25 token-class counts exactly.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
from functools import lru_cache
from pathlib import Path

import numpy as np

import phase484a_raw_symbol_vic_solver as base
import phase484g_hard_negative_discriminator as learned
import phase484q_blind_joint_width19_solver as solver
import phase484j_constructive_prefix_beam_probe as prefix

SCRIPT_DIR = Path(__file__).resolve().parent
WIDTH = 19
PAIR = ("g", "i")
PAIR_INDEX = base.ESCAPE_PAIRS.index(PAIR)
PLAINTEXT_LENGTH = 436
TARGET_RAW_COUNTS = {
    "a": 54, "b": 49, "c": 52, "d": 49, "e": 69,
    "f": 57, "g": 107, "h": 58, "i": 75,
}
TARGET_TOKEN_COUNTS = {
    "a": 42, "b": 38, "c": 45, "d": 40, "e": 54, "f": 38,
    "h": 45, "ga": 8, "gb": 7, "gc": 2, "gd": 4, "ge": 10,
    "gf": 10, "gg": 21, "gh": 8, "gi": 6, "ia": 4, "ib": 4,
    "ic": 5, "id": 5, "ie": 5, "if": 9, "ig": 10, "ih": 5,
    "ii": 11,
}
SEED = 0x484EAC7
PROFILE_TRAIN_INDICES = tuple(range(3, 13))
FINAL_SHORTLIST_KEEP = 1048576


def normalized_quadgram(text, quad=None):
    if quad is None:
        quad, _ = base.load_language_model()
    indices = {letter: index for index, letter in enumerate(base.LETTER_ALPHABET)}
    values = np.asarray([indices[letter] for letter in text], dtype=np.int64)
    return base.score_indices(values, quad) / max(1, len(values) - 3)


def training_groups():
    frequencies = collections.Counter(base.corpus_splits()["train"])
    letters = sorted(base.LETTER_ALPHABET,
                     key=lambda letter: (-frequencies[letter], letter))
    return tuple(letters[:7]), tuple(letters[7:])


def closest_board(passage):
    counts = collections.Counter(passage)
    common, other = training_groups()
    singles = base.slot_codes(PAIR)[:7]
    doubles = base.slot_codes(PAIR)[7:]

    def assign(letters, codes):
        ranked_letters = sorted(letters,
                                key=lambda letter: (-counts[letter], letter))
        ranked_codes = sorted(codes,
                              key=lambda code: (-TARGET_TOKEN_COUNTS[code], code))
        return dict(zip(ranked_letters, ranked_codes))

    board = assign(common, singles)
    board.update(assign(other, doubles))
    target = {letter: TARGET_TOKEN_COUNTS[code]
              for letter, code in board.items()}
    edits = sum(abs(counts[letter] - target[letter])
                for letter in base.LETTER_ALPHABET) // 2
    return board, target, edits


@lru_cache(maxsize=None)
def ranked_passages(split="dev"):
    source = base.corpus_splits()[split]
    candidates = []
    for start in base.corpus_word_starts(split):
        passage = source[start:start + PLAINTEXT_LENGTH]
        if len(passage) != PLAINTEXT_LENGTH:
            continue
        board, _, edits = closest_board(passage)
        candidates.append((edits, start, passage, board))
    candidates.sort(key=lambda record: (record[0], record[1]))
    separated = []
    for record in candidates:
        if all(abs(record[1] - kept[1]) >= PLAINTEXT_LENGTH
               for kept in separated):
            separated.append(record)
    return tuple(separated)


def score_aware_minimum_edits(passage, target, quad):
    current = list(passage)
    counts = collections.Counter(current)
    edit_count = sum(abs(counts[letter] - target[letter])
                     for letter in base.LETTER_ALPHABET) // 2
    for _ in range(edit_count):
        surplus = {letter for letter in base.LETTER_ALPHABET
                   if counts[letter] > target[letter]}
        deficits = [letter for letter in base.LETTER_ALPHABET
                    if counts[letter] < target[letter]]
        best = None
        for position, old in enumerate(current):
            if old not in surplus:
                continue
            for new in deficits:
                current[position] = new
                score = normalized_quadgram(current, quad)
                current[position] = old
                candidate = (-score, position, new, old)
                if best is None or candidate < best:
                    best = candidate
        if best is None:
            raise AssertionError("no legal minimum-edit substitution")
        _, position, new, old = best
        current[position] = new
        counts[old] -= 1
        counts[new] += 1
    if any(counts[letter] != target[letter]
           for letter in base.LETTER_ALPHABET):
        raise AssertionError("target letter histogram was not reached")
    return "".join(current), edit_count


@lru_cache(maxsize=None)
def make_fixture(fixture_index=0, split="dev"):
    choices = ranked_passages(split)
    if not 0 <= fixture_index < len(choices):
        raise ValueError("fixture index exceeds separated passage pool")
    _, start, passage, board = choices[fixture_index]
    target = {letter: TARGET_TOKEN_COUNTS[code]
              for letter, code in board.items()}
    quad, _ = base.load_language_model()
    plaintext, edit_count = score_aware_minimum_edits(passage, target, quad)
    raw = base.encode_plaintext(plaintext, board)
    rng = base.PCG32(base.derive_seed(SEED, fixture_index))
    order = rng.permutation(WIDTH)
    observed = base.Geometry(base.RAW_LENGTH, WIDTH).encrypt(raw, order)
    fixture = {
        "width": WIDTH,
        "pair": list(PAIR),
        "fixture_index": fixture_index,
        "board_mode": "faed_exact_gi_profile",
        "split": split,
        "source_start": start,
        "source_plaintext": passage,
        "plaintext": plaintext,
        "plaintext_length": len(plaintext),
        "minimum_edit_count": edit_count,
        "letter_to_code": board,
        "order": order,
        "raw": raw,
        "observed": observed,
        "raw_sha256": hashlib.sha256(raw.encode("ascii")).hexdigest(),
        "normalized_quadgram": normalized_quadgram(plaintext, quad),
    }
    verify_exact_profile(fixture)
    return fixture


def verify_exact_profile(fixture):
    base.verify_fixture(fixture)
    tokens = base.segment_raw(fixture["raw"], PAIR)
    if len(tokens) != PLAINTEXT_LENGTH:
        raise AssertionError("wrong decoded token count")
    if collections.Counter(tokens) != collections.Counter(TARGET_TOKEN_COUNTS):
        raise AssertionError("token histogram differs from frozen target")
    if collections.Counter(fixture["raw"]) != collections.Counter(TARGET_RAW_COUNTS):
        raise AssertionError("raw-symbol histogram differs from frozen target")
    if sum(1 for token in tokens if len(token) == 1) != 302:
        raise AssertionError("single-slot count differs from 302")


def fixture_summary(fixture):
    return {
        "fixture_index": fixture["fixture_index"],
        "source_start": fixture["source_start"],
        "minimum_edit_count": fixture["minimum_edit_count"],
        "normalized_quadgram": fixture["normalized_quadgram"],
        "plaintext_sha256": hashlib.sha256(
            fixture["plaintext"].encode("ascii")).hexdigest(),
        "raw_sha256": fixture["raw_sha256"],
        "single_slots": 302,
        "tokens": 436,
        "raw_symbols": 570,
    }


@lru_cache(maxsize=None)
def train_profile_models(train_indices=PROFILE_TRAIN_INDICES):
    fixtures = [make_fixture(index) for index in train_indices]
    models = {}
    for depth in range(prefix.START_DEPTH, solver.DEPTH + 1):
        positives, negatives = [], []
        for fixture in fixtures:
            blocks = prefix.blocks_from_observed(fixture)
            truth = prefix.order_to_sequence(fixture["order"])
            true_paths = {
                tuple(truth[start:start + depth])
                for start in range(WIDTH - depth + 1)
            }
            positives.extend(prefix.prefix_features(blocks, path, PAIR)
                             for path in sorted(true_paths))
            rng = base.PCG32(base.derive_seed(
                SEED, depth, fixture["fixture_index"]))
            made = set()
            while len(made) < prefix.NEGATIVE_RATIO * len(true_paths):
                path = tuple(rng.permutation(WIDTH)[:depth])
                if path not in true_paths:
                    made.add(path)
            negatives.extend(prefix.prefix_features(blocks, path, PAIR)
                             for path in sorted(made))
        models[depth] = prefix.fit_centroid(positives, negatives)
    return models


def run(fixture_index=8, final_keep=FINAL_SHORTLIST_KEEP):
    fixture = make_fixture(fixture_index)
    models = train_profile_models()
    result = solver.screen_fixture(
        fixture_override=fixture,
        hypothesis_pair_index=PAIR_INDEX,
        keep=262144,
        refine_keep=8192,
        extend_seed_count=256,
        extend_workers=8,
        extension_backend="persistent",
        shortlist_models=models,
        shortlist_final_keep=final_keep,
    )
    result["phase"] = "484X"
    result["status"] = "development_exact_faed_profile_power_probe"
    result["exact_profile_fixture"] = fixture_summary(fixture)
    return result


def self_test():
    reconstructed = collections.Counter()
    for token, count in TARGET_TOKEN_COUNTS.items():
        for symbol in token:
            reconstructed[symbol] += count
    if reconstructed != collections.Counter(TARGET_RAW_COUNTS):
        raise AssertionError("frozen token/raw histograms disagree")
    fixture = make_fixture(0)
    verify_exact_profile(fixture)
    if fixture != make_fixture(0):
        raise AssertionError("fixture construction is not deterministic")
    if fixture["minimum_edit_count"] != sum(
            left != right for left, right in zip(
                fixture["source_plaintext"], fixture["plaintext"])):
        raise AssertionError("reported edit count differs from Hamming distance")
    return fixture_summary(fixture)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--describe", type=int)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--batch", nargs="+", type=int)
    parser.add_argument("--fixture-index", type=int, default=8)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), indent=2))
        return 0
    if args.describe is not None:
        print(json.dumps([fixture_summary(make_fixture(index))
                          for index in range(args.describe)], indent=2))
        return 0
    if args.batch:
        train_profile_models()
        for index in args.batch:
            result = run(index)
            output = SCRIPT_DIR / f"phase484x_exact_faed_profile_i{index}.json"
            output.write_text(json.dumps(result, indent=2) + "\n")
            print("fixture", index, "top1 exact", result["top1_exact_order"],
                  "plaintext accuracy", result["top1_plaintext_accuracy"],
                  "true segments", result["true_segments_retained"])
            print("wrote", output)
        return 0
    if not args.run:
        parser.error("use --self-test, --describe, --batch, or --run")
    result = run(args.fixture_index)
    output = args.output or SCRIPT_DIR / (
        f"phase484x_exact_faed_profile_i{args.fixture_index}.json")
    output.write_text(json.dumps(result, indent=2) + "\n")
    print("top1 exact", result["top1_exact_order"],
          "plaintext accuracy", result["top1_plaintext_accuracy"],
          "true segments", result["true_segments_retained"],
          "extension seconds", round(result["extension_seconds"], 3))
    print("wrote", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
