#!/usr/bin/env python3
"""Phase 475: dependency-aware direct DBBI/P91 algebra audit.

The protocol was frozen before execution in
``doc/Brainstorms/2026-09-03 - Phase 475 Dependency-Aware DBBI P91 Protocol.md``.
It tests exactly three mod-26 and three DBBI-square coordinate operations.  Its
null shuffles the upstream FAED stream, reruns the full-block Phase-386 Bifid
decode, and only then extracts P91, retaining DBBI's dual role as square source
and comparator.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from data import DBBI, FAED  # noqa: E402
from phase386_btcseed_bifid_faed_decode_audit import (  # noqa: E402
    ALPHABET_NO_J,
    audit as phase386_audit,
    build_grid,
)
from phase387_btcseed_kmodest_checkpoint_audit import (  # noqa: E402
    load_quadgrams,
    quadgram_score,
)
from phase396_p91_header_aware_block_audit import TARGET_KEYWORDS  # noqa: E402

DEFAULT_TRIALS = 100_000
DEFAULT_SEED = 0x475
DEFAULT_BATCH_SIZE = 512
PROMOTION_P = 0.005
FAMILY_LABELS = (
    "AS1_P91_minus_DBBI",
    "AS2_P91_plus_DBBI",
    "AS3_DBBI_minus_P91",
    "CS1_coordsP91_minus_coordsDBBI",
    "CS2_coordsP91_plus_coordsDBBI",
    "CS3_coordsDBBI_minus_coordsP91",
)


def alpha_indices(text: str) -> np.ndarray:
    return np.fromiter((ord(ch.upper()) - 65 for ch in text), dtype=np.int16)


def square_arrays():
    grid_keyword, _grid, _pos = build_grid(DBBI[:13])
    lookup = alpha_indices(grid_keyword).reshape(5, 5)
    positions = np.empty((26, 2), dtype=np.int16)
    for row in range(5):
        for col in range(5):
            positions[int(lookup[row, col])] = (row, col)
    positions[ord("J") - 65] = positions[ord("I") - 65]
    return grid_keyword, lookup, positions


def decode_p91_batch(faed_batch: np.ndarray, lookup: np.ndarray, positions: np.ndarray):
    """Full-block Bifid decryption, restricted only after transformation.

    Phase 386 flattens all 570 row/column pairs and joins the two 570-element
    halves.  Output indexes 7:98 therefore use flat-coordinate indexes 7:98
    and 577:668 respectively.
    """
    n = faed_batch.shape[1]
    assert n == len(FAED) == 570
    stream = positions[faed_batch].reshape(faed_batch.shape[0], 2 * n)
    rows = stream[:, 7:98]
    cols = stream[:, n + 7:n + 98]
    return lookup[rows, cols]


def family_batch(p91: np.ndarray, lookup: np.ndarray, positions: np.ndarray):
    dbbi = alpha_indices(DBBI)[None, :]
    assert p91.shape[1] == dbbi.shape[1] == 91

    pcoords = positions[p91]
    dcoords = positions[dbbi[0]][None, :, :]
    coordinate_outputs = [
        lookup[(pcoords[:, :, 0] - dcoords[:, :, 0]) % 5,
               (pcoords[:, :, 1] - dcoords[:, :, 1]) % 5],
        lookup[(pcoords[:, :, 0] + dcoords[:, :, 0]) % 5,
               (pcoords[:, :, 1] + dcoords[:, :, 1]) % 5],
        lookup[(dcoords[:, :, 0] - pcoords[:, :, 0]) % 5,
               (dcoords[:, :, 1] - pcoords[:, :, 1]) % 5],
    ]
    alphabet_outputs = [
        (p91 - dbbi) % 26,
        (p91 + dbbi) % 26,
        (dbbi - p91) % 26,
    ]
    return np.stack(alphabet_outputs + coordinate_outputs, axis=1).astype(np.int16)


def text_from_indices(indices: np.ndarray) -> str:
    return "".join(chr(int(value) + 65) for value in indices)


def quadgram_table():
    logs, floor = load_quadgrams()
    table = np.full(26 ** 4, floor, dtype=np.float64)
    for gram, score in logs.items():
        values = [ord(ch) - 65 for ch in gram]
        index = ((values[0] * 26 + values[1]) * 26 + values[2]) * 26 + values[3]
        table[index] = score
    return table, logs, floor


def score_batch(outputs: np.ndarray, table: np.ndarray) -> np.ndarray:
    # 26**4 exceeds int16; promote before positional-base arithmetic.
    outputs = outputs.astype(np.int64, copy=False)
    scores = np.zeros(outputs.shape[:2], dtype=np.float64)
    for offset in range(outputs.shape[2] - 3):
        indexes = (
            ((outputs[:, :, offset] * 26 + outputs[:, :, offset + 1]) * 26
             + outputs[:, :, offset + 2]) * 26
            + outputs[:, :, offset + 3]
        )
        scores += table[indexes]
    return scores


def observed(lookup: np.ndarray, positions: np.ndarray, table: np.ndarray, logs, floor):
    decoded = phase386_audit()["decoded"]
    p91_text = decoded[7:98]
    p91 = alpha_indices(p91_text)[None, :]
    family = family_batch(p91, lookup, positions)[0]
    scores = score_batch(family[None, :, :], table)[0]
    entries = {}
    for label, values, score in zip(FAMILY_LABELS, family, scores):
        text = text_from_indices(values)
        scalar_score = quadgram_score(text, logs, floor)
        assert math.isclose(float(score), scalar_score, rel_tol=0.0, abs_tol=1e-10)
        entries[label] = {
            "text": text,
            "quadgram_score": float(score),
            "keyword_hits": [keyword for keyword in TARGET_KEYWORDS if keyword in text],
        }
    winning_label = max(entries, key=lambda label: entries[label]["quadgram_score"])
    return {
        "decoded_prefix": decoded[:7],
        "p91": p91_text,
        "p91_matches_phase386_slice": p91_text == phase386_audit()["decoded"][7:98],
        "family": entries,
        "winning_label": winning_label,
        "family_max_quadgram": entries[winning_label]["quadgram_score"],
        "keyword_hits": {
            label: entry["keyword_hits"] for label, entry in entries.items()
            if entry["keyword_hits"]
        },
    }


def null_distribution(trials, seed, batch_size, lookup, positions, table):
    faed = alpha_indices(FAED)
    rng = np.random.default_rng(seed)
    maxima = np.empty(trials, dtype=np.float64)
    winners = np.empty(trials, dtype=np.int8)
    cursor = 0
    while cursor < trials:
        count = min(batch_size, trials - cursor)
        shuffled = np.empty((count, len(faed)), dtype=np.int16)
        for row in range(count):
            shuffled[row] = rng.permutation(faed)
        p91 = decode_p91_batch(shuffled, lookup, positions)
        scores = score_batch(family_batch(p91, lookup, positions), table)
        maxima[cursor:cursor + count] = scores.max(axis=1)
        winners[cursor:cursor + count] = scores.argmax(axis=1)
        cursor += count
    return maxima, winners


def planted_positive(lookup, positions, table, logs, floor):
    target = ("THISISAPLANTEDSATOSHIENGLISHPOSITIVE" + "X" * 91)[:91]
    dbbi = text_from_indices(alpha_indices(DBBI))
    synthetic_p91 = text_from_indices((alpha_indices(target) + alpha_indices(dbbi)) % 26)
    outputs = family_batch(alpha_indices(synthetic_p91)[None, :], lookup, positions)
    recovered = text_from_indices(outputs[0, 0])
    assert recovered == target
    score = float(score_batch(outputs, table)[0, 0])
    assert math.isclose(score, quadgram_score(target, logs, floor), abs_tol=1e-10)
    return {"operation": FAMILY_LABELS[0], "recovered": recovered,
            "contains_satoshi": "SATOSHI" in recovered, "quadgram_score": score}


def audit(trials=DEFAULT_TRIALS, seed=DEFAULT_SEED, batch_size=DEFAULT_BATCH_SIZE):
    grid_keyword, lookup, positions = square_arrays()
    table, logs, floor = quadgram_table()
    real = observed(lookup, positions, table, logs, floor)

    # Algebraic inverse checks on the observed pair.
    p91 = alpha_indices(real["p91"])[None, :]
    dbbi = alpha_indices(DBBI)[None, :]
    family = family_batch(p91, lookup, positions)
    alphabet_roundtrip = np.array_equal((family[:, 0, :] + dbbi) % 26, p91)
    coord_difference = positions[family[:, 3, :]]
    dbbi_coords = positions[dbbi[0]][None, :, :]
    coordinate_roundtrip = np.array_equal(
        lookup[(coord_difference[:, :, 0] + dbbi_coords[:, :, 0]) % 5,
               (coord_difference[:, :, 1] + dbbi_coords[:, :, 1]) % 5],
        p91,
    )

    maxima, winners = null_distribution(
        trials, seed, batch_size, lookup, positions, table
    )
    threshold = real["family_max_quadgram"]
    tail_count = int(np.count_nonzero(maxima >= threshold))
    empirical_p = (tail_count + 1) / (trials + 1)
    quantiles = np.quantile(maxima, [0.0, 0.25, 0.5, 0.75, 0.95, 0.99, 1.0])
    outcome = "promoted_direct_relation" if empirical_p <= PROMOTION_P else "closed_negative"
    return {
        "phase": 475,
        "outcome": outcome,
        "grid_keyword": grid_keyword,
        "family_labels": list(FAMILY_LABELS),
        "observed": real,
        "null": {
            "kind": "exact_FAED_multiset_permutation_then_full_block_Bifid_then_fixed_P91_slice",
            "trials": trials,
            "seed": seed,
            "tail_count": tail_count,
            "raw_tail_fraction": tail_count / trials,
            "add_one_empirical_p": empirical_p,
            "family_max_quantiles": dict(zip(
                ("min", "q25", "median", "q75", "q95", "q99", "max"),
                (float(value) for value in quantiles),
            )),
            "winning_operation_counts": {
                FAMILY_LABELS[index]: int(np.count_nonzero(winners == index))
                for index in range(len(FAMILY_LABELS))
            },
        },
        "promotion_threshold": PROMOTION_P,
        "alphabet_subtraction_roundtrip": alphabet_roundtrip,
        "coordinate_subtraction_roundtrip": coordinate_roundtrip,
        "planted_positive": planted_positive(lookup, positions, table, logs, floor),
        "oracle_calls": 0,
        "bitcoin_endpoint_calls": 0,
    }


def self_test():
    report = audit(trials=128, seed=DEFAULT_SEED, batch_size=32)
    assert report["grid_keyword"] == "DBIFHCEGAKLMNOPQRSTUVWXYZ"
    assert report["observed"]["decoded_prefix"] == "BTCSEED"
    assert len(report["observed"]["p91"]) == len(DBBI) == 91
    assert report["observed"]["p91_matches_phase386_slice"] is True
    assert len(report["observed"]["family"]) == 6
    assert report["alphabet_subtraction_roundtrip"] is True
    assert report["coordinate_subtraction_roundtrip"] is True
    assert report["planted_positive"]["contains_satoshi"] is True
    assert report["null"]["trials"] == 128
    assert sum(report["null"]["winning_operation_counts"].values()) == 128
    assert report["oracle_calls"] == report["bitcoin_endpoint_calls"] == 0
    print(
        "[*] self-test OK: upstream FAED permutations regenerate P91; six direct "
        "DBBI/P91 operations score as one family; both inverse checks and the "
        "planted English positive pass"
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=DEFAULT_TRIALS)
    parser.add_argument("--seed", type=lambda value: int(value, 0), default=DEFAULT_SEED)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    report = self_test() if args.self_test else audit(args.trials, args.seed, args.batch_size)
    payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")


if __name__ == "__main__":
    main()
