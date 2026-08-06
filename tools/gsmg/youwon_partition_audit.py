#!/usr/bin/env python3
"""Audit the DBBI/INCASE ``YOUWON`` partition without broadening transforms.

The community framing ``21 | YOUWON | 64`` misses DBBI's established 13x7
geometry. The hit begins at zero-based offset 21, exactly the start of row 4
when the 91-character output is laid out as 13 rows of 7:

    YOUWONX

This audit checks that geometry, calibrates both ``YOUWON`` and the post-hoc
seven-character ``YOUWONX`` row under exact DBBI-multiset permutations, and
tests only the directly implied remove/zero candidate forms against the
tracked CBC oracles. It does not add transpositions, ciphers, or arbitrary
uses of 21/64.
"""

import argparse
import json
from collections import Counter
from fractions import Fraction
from math import prod
from pathlib import Path

from cb_common import (
    BLOBS,
    EXTENDED_CIPHER_VARIANTS,
    KDF_VARIANTS,
    QUARANTINED_BLOBS,
    aes_try_open,
    answer_forms,
)
from data import DBBI, VALIDATION_ANSWER
from external_archive_lead_audit import subtract_mod26
from telegram_export_manifest import DEFAULT_EXPORT_DIR

CREATOR_FROM_ID = "user9815232"
ORIGIN_MESSAGE_ID = 23912
EXPLANATION_MESSAGE_ID = 26597
ROWS = 13
COLUMNS = 7
WORD = "YOUWON"
ROW_TEXT = "YOUWONX"
EXPECTED_START_0 = 21


def flatten_text(value):
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "".join(
            flatten_text(item.get("text", "")) if isinstance(item, dict) else str(item)
            for item in value
        )
    return str(value)


def transcript_provenance(export_dir=DEFAULT_EXPORT_DIR):
    payload = json.loads((Path(export_dir) / "result.json").read_text(encoding="utf-8"))
    messages = {message["id"]: message for message in payload["messages"]}
    origin = messages[ORIGIN_MESSAGE_ID]
    explanation = messages[EXPLANATION_MESSAGE_ID]
    assert WORD in flatten_text(origin.get("text", ""))
    assert "one-time pad" in flatten_text(explanation.get("text", "")).lower()
    assert origin.get("from_id") != CREATOR_FROM_ID
    assert explanation.get("from_id") != CREATOR_FROM_ID

    exact_posts = {
        message["id"]
        for message in payload["messages"]
        if WORD in flatten_text(message.get("text", "")).upper()
    }
    creator_replies = [
        message["id"]
        for message in payload["messages"]
        if message.get("from_id") == CREATOR_FROM_ID
        and message.get("reply_to_message_id") in exact_posts
    ]
    assert not creator_replies
    return {
        "origin_from": origin.get("from"),
        "origin_date": origin["date"],
        "explanation_from": explanation.get("from"),
        "creator_replies": tuple(creator_replies),
    }


def exact_target_probability(target, allowed_starts=None):
    plaintext = VALIDATION_ANSWER.lower()
    counts = Counter(ord(character) - ord("a") for character in DBBI)
    target_values = [ord(character) - ord("A") for character in target]
    denominator = prod(
        range(len(DBBI) - len(target_values) + 1, len(DBBI) + 1)
    )
    starts = (
        range(len(DBBI) - len(target_values) + 1)
        if allowed_starts is None
        else allowed_starts
    )
    feasible = []
    for start in starts:
        if start + len(target_values) > len(DBBI):
            continue
        required = tuple(
            (
                target_values[offset]
                + ord(plaintext[start + offset])
                - ord("a")
            )
            % 26
            for offset in range(len(target_values))
        )
        needed = Counter(required)
        if any(
            value not in counts or amount > counts[value]
            for value, amount in needed.items()
        ):
            continue
        numerator = 1
        for value, amount in needed.items():
            numerator *= prod(
                range(counts[value] - amount + 1, counts[value] + 1)
            )
        feasible.append((start, required, Fraction(numerator, denominator)))
    return tuple(feasible)


def candidate_forms(output):
    prefix = output[:EXPECTED_START_0]
    suffix_after_word = output[EXPECTED_START_0 + len(WORD) :]
    suffix_after_row = output[EXPECTED_START_0 + COLUMNS :]
    without_row = prefix + suffix_after_row
    return {
        "word": WORD,
        "row": ROW_TEXT,
        "prefix21": prefix,
        "tail64": suffix_after_word,
        "tail63": suffix_after_row,
        "without_row": without_row,
        "zero_row_a": prefix + ("A" * COLUMNS) + suffix_after_row,
        "zero_row_literal": prefix + ("0" * COLUMNS) + suffix_after_row,
        "full_output": output,
    }


def oracle_sweep(candidates, blobs=BLOBS):
    variants = tuple(KDF_VARIANTS) + tuple(EXTENDED_CIPHER_VARIANTS)
    tested = set()
    hits = []
    for label, candidate in candidates.items():
        for form in answer_forms(candidate):
            key = (label, form)
            if key in tested:
                continue
            tested.add(key)
            hit = aes_try_open(form, kdf_variants=variants, blobs=blobs)
            if hit:
                hits.append((label, form, hit))
    return {"forms": len(tested), "variants": len(variants), "hits": hits}


def audit(
    run_oracle=True,
    export_dir=DEFAULT_EXPORT_DIR,
    include_quarantined=False,
    word_row_only=False,
):
    provenance = transcript_provenance(export_dir)
    output = subtract_mod26(DBBI, VALIDATION_ANSWER)
    assert len(output) == ROWS * COLUMNS
    grid = tuple(
        output[offset : offset + COLUMNS]
        for offset in range(0, len(output), COLUMNS)
    )
    start = output.index(WORD)
    assert start == EXPECTED_START_0
    assert grid[3] == ROW_TEXT
    assert start + 1 == 22

    row_starts = tuple(range(0, len(output), COLUMNS))
    word_anywhere = exact_target_probability(WORD)
    word_row_aligned = exact_target_probability(WORD, row_starts)
    row_exact = exact_target_probability(ROW_TEXT, row_starts)
    assert len(word_anywhere) == 1
    assert word_anywhere == word_row_aligned
    assert word_anywhere[0][0] == EXPECTED_START_0
    assert len(row_exact) == 1 and row_exact[0][0] == EXPECTED_START_0

    candidates = candidate_forms(output)
    assert len(candidates["tail64"]) == 64
    assert len(candidates["tail63"]) == 63
    assert any(character not in "0123456789ABCDEF" for character in candidates["tail64"])
    oracle_candidates = (
        {label: candidates[label] for label in ("word", "row")}
        if word_row_only
        else candidates
    )
    blobs = (
        {**BLOBS, **QUARANTINED_BLOBS}
        if include_quarantined
        else BLOBS
    )
    oracle = oracle_sweep(oracle_candidates, blobs) if run_oracle else None
    if oracle is not None:
        assert not oracle["hits"]

    return {
        "provenance": provenance,
        "output": output,
        "grid": grid,
        "word_probability": word_anywhere[0][2],
        "row_probability": row_exact[0][2],
        "candidates": candidates,
        "oracle": oracle,
        "blob_count": len(blobs),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-oracle", action="store_true")
    parser.add_argument("--include-quarantined", action="store_true")
    parser.add_argument("--word-row-only", action="store_true")
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    args = parser.parse_args()
    result = audit(
        not args.skip_oracle,
        args.export_dir,
        args.include_quarantined,
        args.word_row_only,
    )
    print("13x7 output:")
    for row_number, row in enumerate(result["grid"], start=1):
        print(f"{row_number:2}: {row}")
    print(
        f"YOUWON probability: {float(result['word_probability']):.9g}; "
        f"YOUWONX row probability: {float(result['row_probability']):.9g}"
    )
    print(
        "partition correction: 21|6|64 is community-derived; the established "
        "grid gives 21|7|63 with fourth row YOUWONX."
    )
    print(
        "creator provenance: no creator-authored post or direct creator reply "
        "confirms YOUWON."
    )
    if result["oracle"] is not None:
        print(
            f"CBC oracle: {result['oracle']['forms']} candidate forms x "
            f"{result['oracle']['variants']} variants x "
            f"{result['blob_count']} blobs, "
            "0 hits."
        )


if __name__ == "__main__":
    main()
