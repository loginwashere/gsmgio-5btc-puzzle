#!/usr/bin/env python3
"""Phase 476: P91 as a dynamic second Bifid key over Q472."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from data import DBBI, FAED  # noqa: E402
from phase386_btcseed_bifid_faed_decode_audit import (  # noqa: E402
    ALPHABET_NO_J,
    audit as phase386_audit,
    bifid_decrypt,
    build_grid,
)
from phase387_btcseed_kmodest_checkpoint_audit import (  # noqa: E402
    load_quadgrams,
    quadgram_score,
)
from phase396_p91_header_aware_block_audit import TARGET_KEYWORDS  # noqa: E402
from phase408_bifid_period_robustness_audit import bifid_encrypt_block  # noqa: E402
from phase475_dbbi_p91_dependency_aware_audit import (  # noqa: E402
    alpha_indices,
    quadgram_table,
    score_batch,
    square_arrays,
    text_from_indices,
)

DEFAULT_TRIALS = 100_000
DEFAULT_SEED = 0x476
FIXED_KEY_SEED = 0x47601
DEFAULT_BATCH_SIZE = 384
PROMOTION_P = 0.005
Q472_START = 98


def decode_full_batch(ciphertext: np.ndarray, lookup: np.ndarray, positions: np.ndarray):
    n = ciphertext.shape[1]
    stream = positions[ciphertext].reshape(ciphertext.shape[0], 2 * n)
    return lookup[stream[:, :n], stream[:, n:]]


def dynamic_squares_from_p91(p91_batch: np.ndarray) -> np.ndarray:
    """Return one standard-A-Z-valued 25-cell keyed square per P91 row."""
    alphabet = alpha_indices(ALPHABET_NO_J)
    squares = np.empty((p91_batch.shape[0], 25), dtype=np.int16)
    for row_index, row in enumerate(p91_batch):
        seen = np.zeros(26, dtype=bool)
        ordered = []
        for raw in row:
            value = int(raw)
            if value == 9:  # J -> I
                value = 8
            if not seen[value]:
                seen[value] = True
                ordered.append(value)
        for raw in alphabet:
            value = int(raw)
            if not seen[value]:
                seen[value] = True
                ordered.append(value)
        assert len(ordered) == 25
        squares[row_index] = ordered
    return squares


def dynamic_positions(squares: np.ndarray) -> np.ndarray:
    batch = squares.shape[0]
    positions = np.empty((batch, 26, 2), dtype=np.int16)
    positions.fill(-1)
    coords = np.array([divmod(index, 5) for index in range(25)], dtype=np.int16)
    rows = np.arange(batch)[:, None]
    positions[rows, squares] = coords[None, :, :]
    positions[:, 9] = positions[:, 8]  # J -> I
    assert np.all(positions[:, alpha_indices(ALPHABET_NO_J)] >= 0)
    return positions


def dynamic_bifid_decrypt(ciphertext: np.ndarray, squares: np.ndarray):
    positions = dynamic_positions(squares)
    rows = np.arange(ciphertext.shape[0])[:, None]
    stream = positions[rows, ciphertext].reshape(ciphertext.shape[0], 2 * ciphertext.shape[1])
    n = ciphertext.shape[1]
    cell_indexes = stream[:, :n] * 5 + stream[:, n:]
    return np.take_along_axis(squares, cell_indexes, axis=1)


def observed_cascade(table, logs, floor):
    first = phase386_audit()["decoded"]
    p91_text = first[7:98]
    q472_text = first[98:]
    p91 = alpha_indices(p91_text)[None, :]
    q472 = alpha_indices(q472_text)[None, :]
    squares = dynamic_squares_from_p91(p91)
    second = dynamic_bifid_decrypt(q472, squares)[0]
    second_text = text_from_indices(second)

    grid_keyword, grid, pos = build_grid(p91_text)
    scalar = bifid_decrypt(q472_text, pos, grid)
    assert second_text == scalar
    vector_score = float(score_batch(second[None, None, :], table)[0, 0])
    scalar_score = quadgram_score(second_text, logs, floor)
    assert math.isclose(vector_score, scalar_score, rel_tol=0.0, abs_tol=1e-10)
    reencrypted = "".join(bifid_encrypt_block(list(second_text), pos, grid))

    return {
        "first_pass_prefix": first[:7],
        "p91": p91_text,
        "q472_sha256": hashlib.sha256(q472_text.encode("ascii")).hexdigest(),
        "p91_grid_keyword": grid_keyword,
        "second_pass": second_text,
        "second_pass_sha256": hashlib.sha256(second_text.encode("ascii")).hexdigest(),
        "second_pass_quadgram": vector_score,
        "second_pass_prefix_96": second_text[:96],
        "keyword_hits": [keyword for keyword in TARGET_KEYWORDS if keyword in second_text],
        "roundtrip_matches_q472": reencrypted == q472_text,
        "vectorized_matches_scalar": second_text == scalar,
    }


def upstream_null(trials, seed, batch_size, fixed_lookup, fixed_positions, table, threshold):
    faed = alpha_indices(FAED)
    rng = np.random.default_rng(seed)
    scores = np.empty(trials, dtype=np.float64)
    cursor = 0
    while cursor < trials:
        count = min(batch_size, trials - cursor)
        shuffled = np.empty((count, len(faed)), dtype=np.int16)
        for row in range(count):
            shuffled[row] = rng.permutation(faed)
        first = decode_full_batch(shuffled, fixed_lookup, fixed_positions)
        p91 = first[:, 7:98]
        q472 = first[:, 98:]
        squares = dynamic_squares_from_p91(p91)
        second = dynamic_bifid_decrypt(q472, squares)
        scores[cursor:cursor + count] = score_batch(second[:, None, :], table)[:, 0]
        cursor += count
    return summarize_null(scores, trials, seed, threshold)


def fixed_key_null(trials, seed, batch_size, q472, square, table, threshold):
    rng = np.random.default_rng(seed)
    scores = np.empty(trials, dtype=np.float64)
    cursor = 0
    while cursor < trials:
        count = min(batch_size, trials - cursor)
        shuffled = np.empty((count, len(q472)), dtype=np.int16)
        for row in range(count):
            shuffled[row] = rng.permutation(q472)
        squares = np.repeat(square, count, axis=0)
        second = dynamic_bifid_decrypt(shuffled, squares)
        scores[cursor:cursor + count] = score_batch(second[:, None, :], table)[:, 0]
        cursor += count
    return summarize_null(scores, trials, seed, threshold)


def summarize_null(scores, trials, seed, threshold):
    tail = int(np.count_nonzero(scores >= threshold))
    quantiles = np.quantile(scores, [0.0, 0.25, 0.5, 0.75, 0.95, 0.99, 1.0])
    return {
        "trials": trials,
        "seed": seed,
        "tail_count": tail,
        "raw_tail_fraction": tail / trials,
        "add_one_empirical_p": (tail + 1) / (trials + 1),
        "quadgram_quantiles": dict(zip(
            ("min", "q25", "median", "q75", "q95", "q99", "max"),
            (float(value) for value in quantiles),
        )),
    }


def planted_positive(table, logs, floor):
    key = "PLANTEDSECONDKEY"
    grid_keyword, grid, pos = build_grid(key)
    plaintext = ("THISISAPLANTEDSATOSHIPOSITIVEFORASECONDBIFIDPASS" * 10)[:472]
    ciphertext = "".join(bifid_encrypt_block(list(plaintext), pos, grid))
    recovered = bifid_decrypt(ciphertext, pos, grid)
    score = quadgram_score(recovered, logs, floor)
    return {
        "grid_keyword": grid_keyword,
        "roundtrip": recovered == plaintext,
        "contains_satoshi": "SATOSHI" in recovered,
        "quadgram_score": score,
    }


def audit(trials=DEFAULT_TRIALS, seed=DEFAULT_SEED, fixed_key_seed=FIXED_KEY_SEED,
          batch_size=DEFAULT_BATCH_SIZE):
    grid_keyword, fixed_lookup, fixed_positions = square_arrays()
    table, logs, floor = quadgram_table()
    real = observed_cascade(table, logs, floor)
    threshold = real["second_pass_quadgram"]

    primary = upstream_null(
        trials, seed, batch_size, fixed_lookup, fixed_positions, table, threshold
    )
    first = phase386_audit()["decoded"]
    q472 = alpha_indices(first[98:])
    p91_square = dynamic_squares_from_p91(alpha_indices(first[7:98])[None, :])
    secondary = fixed_key_null(
        trials, fixed_key_seed, batch_size, q472, p91_square, table, threshold
    )
    outcome = (
        "promoted_second_bifid_layer"
        if primary["add_one_empirical_p"] <= PROMOTION_P
        else "closed_negative"
    )
    return {
        "phase": 476,
        "outcome": outcome,
        "ordered_schedule": "FAED--DBBI_square_period570_decrypt-->P91,Q472--P91_square_period472_decrypt-->candidate",
        "first_square": grid_keyword,
        "observed": real,
        "primary_upstream_null": primary,
        "secondary_fixed_p91_key_null": secondary,
        "promotion_threshold": PROMOTION_P,
        "planted_positive": planted_positive(table, logs, floor),
        "oracle_calls": 0,
        "bitcoin_endpoint_calls": 0,
    }


def self_test():
    report = audit(trials=96, seed=DEFAULT_SEED, fixed_key_seed=FIXED_KEY_SEED,
                   batch_size=24)
    observed = report["observed"]
    assert report["first_square"] == "DBIFHCEGAKLMNOPQRSTUVWXYZ"
    assert observed["first_pass_prefix"] == "BTCSEED"
    assert len(observed["p91"]) == 91 and len(observed["second_pass"]) == 472
    assert observed["vectorized_matches_scalar"] is True
    assert observed["roundtrip_matches_q472"] is True
    assert len(observed["p91_grid_keyword"]) == 25
    assert report["planted_positive"]["roundtrip"] is True
    assert report["planted_positive"]["contains_satoshi"] is True
    assert report["primary_upstream_null"]["trials"] == 96
    assert report["secondary_fixed_p91_key_null"]["trials"] == 96
    assert report["oracle_calls"] == report["bitcoin_endpoint_calls"] == 0
    print("[*] self-test OK: DBBI->P91 dynamic-square cascade, scalar/vectorized agreement, second-pass roundtrip, two null pipelines, and planted positive pass")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=DEFAULT_TRIALS)
    parser.add_argument("--seed", type=lambda value: int(value, 0), default=DEFAULT_SEED)
    parser.add_argument("--fixed-key-seed", type=lambda value: int(value, 0), default=FIXED_KEY_SEED)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    report = self_test() if args.self_test else audit(
        args.trials, args.seed, args.fixed_key_seed, args.batch_size
    )
    payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")


if __name__ == "__main__":
    main()
