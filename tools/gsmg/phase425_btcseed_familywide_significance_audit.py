#!/usr/bin/env python3
"""Phase 425: family-wide significance audit of the FAED ``BTCSEED`` prefix.

The frozen protocol is documented in:

``doc/Brainstorms/2026-08-27 - Phase 425 BTCSEED Family-Wide Significance Audit Pre-Registration.md``

This script evaluates a bounded page-local family of Bifid keyword squares and
common conventions, then compares the observed family-maximum prefix match to
10,000 exact-multiset shuffles of FAED.  It never generates passwords or calls
any ciphertext/blob oracle.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from data import DBBI, FAED  # noqa: E402
from page_structure_audit import (  # noqa: E402
    DECIMAL_INSTRUCTIONS,
    ENTER_INSTRUCTION,
    HASH_PREFIX,
    HASH_SUFFIX,
    MATRIX_INSTRUCTION,
)
from phase386_btcseed_bifid_faed_decode_audit import (  # noqa: E402
    ALPHABET_NO_J,
    audit as phase386_audit,
    build_grid,
)
from phase408_bifid_period_robustness_audit import (  # noqa: E402
    CUSTOM_SCHEDULE,
    STANDARD_PERIODS,
    block_sizes_for_period,
)

TARGET = "BTCSEED"
DEFAULT_TRIALS = 10_000
DEFAULT_SEED = 0x425

KEYWORD_SOURCES = {
    "dbbi": DBBI,
    "faed": FAED,
    "matrixsumlist": MATRIX_INSTRUCTION,
    "lastwordsbeforearchichoice": DECIMAL_INSTRUCTIONS[0],
    "thispassword": DECIMAL_INSTRUCTIONS[1],
    "enter": ENTER_INSTRUCTION,
    "hash_prefix": HASH_PREFIX,
    "hash_suffix": HASH_SUFFIX,
    "salphaseion": "SalPhaseIon",
    "cosmic_duality": "Cosmic Duality",
}


@dataclass(frozen=True)
class Config:
    square_id: str
    schedule: str
    operation: str
    coordinate_order: str
    input_orientation: str
    output_orientation: str

    @property
    def label(self) -> str:
        return "/".join(
            (
                self.square_id,
                self.schedule,
                self.operation,
                self.coordinate_order,
                self.input_orientation,
                self.output_orientation,
            )
        )


def normalize_letters(text: str) -> str:
    return "".join("I" if ch == "J" else ch for ch in text.upper() if ch.isalpha())


def keyword_square_manifest():
    by_square: dict[str, dict] = {}
    for source_label, source_text in KEYWORD_SOURCES.items():
        normalized = normalize_letters(source_text)
        for scope, scoped in (("first13", normalized[:13]), ("full", normalized)):
            square, _grid, _pos = build_grid(scoped)
            entry = by_square.setdefault(
                square,
                {
                    "square_id": f"square_{len(by_square):02d}",
                    "grid_keyword": square,
                    "provenance": [],
                },
            )
            entry["provenance"].append(
                {
                    "source": source_label,
                    "scope": scope,
                    "normalized_keyword": scoped,
                }
            )
    return list(by_square.values())


def schedules():
    result = {
        f"period_{period}": block_sizes_for_period(period, len(FAED))
        for period in STANDARD_PERIODS
    }
    result["custom_98_472"] = CUSTOM_SCHEDULE
    return result


def configs(square_manifest):
    return [
        Config(square["square_id"], schedule, operation, coordinate_order, input_orientation, output_orientation)
        for square in square_manifest
        for schedule in schedules()
        for operation in ("decrypt", "encrypt")
        for coordinate_order in ("rc", "cr")
        for input_orientation in ("forward", "reverse")
        for output_orientation in ("forward", "reverse")
    ]


def square_arrays(grid_keyword: str):
    char_to_index = {ch: i for i, ch in enumerate(ALPHABET_NO_J)}
    lookup = np.array([char_to_index[ch] for ch in grid_keyword], dtype=np.int16).reshape(5, 5)
    positions = np.empty((25, 2), dtype=np.int16)
    for row in range(5):
        for col in range(5):
            positions[lookup[row, col]] = (row, col)
    return lookup, positions, char_to_index


def decode_indices(indices, lookup):
    return "".join(ALPHABET_NO_J[int(i)] for i in indices)


def transform_block(block, lookup, positions, operation, coordinate_order):
    reps = positions[np.asarray(block, dtype=np.int16)]
    if coordinate_order == "cr":
        reps = reps[:, ::-1]
    n = len(reps)
    if operation == "decrypt":
        stream = reps.reshape(2 * n)
        pairs = np.column_stack((stream[:n], stream[n:]))
    else:
        stream = np.concatenate((reps[:, 0], reps[:, 1]))
        pairs = stream.reshape(n, 2)
    if coordinate_order == "cr":
        pairs = pairs[:, ::-1]
    return lookup[pairs[:, 0], pairs[:, 1]]


def transform_full(text_indices, lookup, positions, block_sizes, operation, coordinate_order):
    parts = []
    cursor = 0
    for size in block_sizes:
        block = text_indices[cursor : cursor + size]
        parts.append(transform_block(block, lookup, positions, operation, coordinate_order))
        cursor += size
    assert cursor == len(text_indices)
    return np.concatenate(parts)


def longest_common_prefix(a: str, b: str) -> int:
    for index, (left, right) in enumerate(zip(a, b)):
        if left != right:
            return index
    return min(len(a), len(b))


def observed_family(square_manifest, configuration_manifest):
    schedule_manifest = schedules()
    square_by_id = {entry["square_id"]: entry for entry in square_manifest}
    normalized_faed = normalize_letters(FAED)
    base_char_to_index = {ch: i for i, ch in enumerate(ALPHABET_NO_J)}
    faed_indices = np.array([base_char_to_index[ch] for ch in normalized_faed], dtype=np.int16)

    candidates = []
    outputs: dict[str, dict] = {}
    for config in configuration_manifest:
        square = square_by_id[config.square_id]
        lookup, positions, _char_to_index = square_arrays(square["grid_keyword"])
        oriented = faed_indices if config.input_orientation == "forward" else faed_indices[::-1]
        transformed = transform_full(
            oriented,
            lookup,
            positions,
            schedule_manifest[config.schedule],
            config.operation,
            config.coordinate_order,
        )
        if config.output_orientation == "reverse":
            transformed = transformed[::-1]
        output = decode_indices(transformed, lookup)
        output_hash = hashlib.sha256(output.encode("ascii")).hexdigest()
        lcp = longest_common_prefix(output, TARGET)
        candidate = {
            "label": config.label,
            "output_sha256": output_hash,
            "first_32": output[:32],
            "lcp_with_btcseed": lcp,
            "starts_with_btcseed": output.startswith(TARGET),
            "contains_btcseed": TARGET in output,
        }
        candidates.append(candidate)
        aggregate = outputs.setdefault(
            output_hash,
            {
                "output_sha256": output_hash,
                "first_32": output[:32],
                "lcp_with_btcseed": lcp,
                "starts_with_btcseed": output.startswith(TARGET),
                "contains_btcseed": TARGET in output,
                "config_labels": [],
            },
        )
        aggregate["config_labels"].append(config.label)

    original_label = "square_00/period_570/decrypt/rc/forward/forward"
    original = next(entry for entry in candidates if entry["label"] == original_label)
    phase386 = phase386_audit()
    original_matches_phase386 = original["output_sha256"] == hashlib.sha256(
        phase386["decoded"].encode("ascii")
    ).hexdigest()

    distinct_outputs = list(outputs.values())
    return {
        "configuration_count": len(candidates),
        "distinct_output_count": len(distinct_outputs),
        "maximum_lcp": max(entry["lcp_with_btcseed"] for entry in distinct_outputs),
        "exact_prefix_output_count": sum(entry["starts_with_btcseed"] for entry in distinct_outputs),
        "anywhere_output_count": sum(entry["contains_btcseed"] for entry in distinct_outputs),
        "exact_prefix_outputs": [entry for entry in distinct_outputs if entry["starts_with_btcseed"]],
        "anywhere_outputs": [entry for entry in distinct_outputs if entry["contains_btcseed"]],
        "original_config_label": original_label,
        "original_matches_phase386": original_matches_phase386,
        "candidates": candidates,
    }


def transform_edge_batch(block, lookup, positions, operation, coordinate_order, edge, width=7):
    reps = positions[block]
    if coordinate_order == "cr":
        reps = reps[:, :, ::-1]
    trial_count, n, _two = reps.shape
    if operation == "decrypt":
        stream = reps.reshape(trial_count, 2 * n)
        indexes = np.arange(width) if edge == "first" else np.arange(n - width, n)
        pairs = np.stack((stream[:, indexes], stream[:, n + indexes]), axis=2)
    else:
        stream = np.concatenate((reps[:, :, 0], reps[:, :, 1]), axis=1)
        indexes = np.arange(width) if edge == "first" else np.arange(n - width, n)
        left = stream[:, 2 * indexes]
        right = stream[:, 2 * indexes + 1]
        pairs = np.stack((left, right), axis=2)
    if coordinate_order == "cr":
        pairs = pairs[:, :, ::-1]
    return lookup[pairs[:, :, 0], pairs[:, :, 1]]


def transformed_last_batch(oriented, block_sizes, lookup, positions, operation, coordinate_order, width=7):
    """Return the final ``width`` symbols across block boundaries.

    Several standard periods leave a final remainder shorter than BTCSEED, so
    a reversed-output prefix can include the tail of two Bifid blocks.
    """
    remaining = width
    cursor = oriented.shape[1]
    chunks = []
    for size in reversed(block_sizes):
        start = cursor - size
        take = min(remaining, size)
        block = oriented[:, start:cursor]
        chunk = transform_edge_batch(
            block, lookup, positions, operation, coordinate_order, "last", take
        )
        chunks.insert(0, chunk)
        remaining -= take
        cursor = start
        if remaining == 0:
            break
    assert remaining == 0
    return np.concatenate(chunks, axis=1)


def null_family(square_manifest, configuration_manifest, trials, seed):
    base_char_to_index = {ch: i for i, ch in enumerate(ALPHABET_NO_J)}
    faed_indices = np.array(
        [base_char_to_index[ch] for ch in normalize_letters(FAED)], dtype=np.int16
    )
    rng = np.random.default_rng(seed)
    shuffled = np.empty((trials, len(faed_indices)), dtype=np.int16)
    for trial in range(trials):
        shuffled[trial] = rng.permutation(faed_indices)

    target_indices = np.array([base_char_to_index[ch] for ch in TARGET], dtype=np.int16)
    maxima = np.zeros(trials, dtype=np.int8)
    schedule_manifest = schedules()
    square_by_id = {entry["square_id"]: entry for entry in square_manifest}

    for config in configuration_manifest:
        square = square_by_id[config.square_id]
        lookup, positions, _char_to_index = square_arrays(square["grid_keyword"])
        oriented = shuffled if config.input_orientation == "forward" else shuffled[:, ::-1]
        sizes = schedule_manifest[config.schedule]
        if config.output_orientation == "forward":
            size = sizes[0]
            block = oriented[:, :size]
            prefixes = transform_edge_batch(
                block, lookup, positions, config.operation,
                config.coordinate_order, "first", len(TARGET)
            )
        else:
            prefixes = transformed_last_batch(
                oriented, sizes, lookup, positions, config.operation,
                config.coordinate_order, len(TARGET)
            )[:, ::-1]
        equal = prefixes == target_indices
        lcp = np.cumprod(equal, axis=1).sum(axis=1)
        maxima = np.maximum(maxima, lcp)

    histogram = Counter(int(value) for value in maxima)
    return {
        "trials": trials,
        "seed": seed,
        "maximum_lcp_histogram": {str(key): histogram[key] for key in sorted(histogram)},
        "null_maximum_lcp": int(maxima.max()),
        "null_trials_reaching_exact_target": int(np.count_nonzero(maxima >= len(TARGET))),
        "maxima": maxima,
    }


def planted_positive(square_manifest):
    square = square_manifest[0]
    lookup, positions, char_to_index = square_arrays(square["grid_keyword"])
    plaintext = TARGET + "X" * (len(FAED) - len(TARGET))
    plaintext_indices = np.array([char_to_index[ch] for ch in plaintext], dtype=np.int16)
    encrypted = transform_full(
        plaintext_indices, lookup, positions, (len(FAED),), "encrypt", "rc"
    )
    recovered = transform_full(encrypted, lookup, positions, (len(FAED),), "decrypt", "rc")
    recovered_text = decode_indices(recovered, lookup)
    return {
        "roundtrip_matches": recovered_text == plaintext,
        "recovered_prefix": recovered_text[: len(TARGET)],
        "detector_lcp": longest_common_prefix(recovered_text, TARGET),
    }


def audit(trials=DEFAULT_TRIALS, seed=DEFAULT_SEED, include_candidates=True):
    square_manifest = keyword_square_manifest()
    configuration_manifest = configs(square_manifest)
    observed = observed_family(square_manifest, configuration_manifest)
    null = null_family(square_manifest, configuration_manifest, trials, seed)
    maxima = null.pop("maxima")
    tail_count = int(np.count_nonzero(maxima >= observed["maximum_lcp"]))
    empirical_p = (tail_count + 1) / (trials + 1)

    if not observed["original_matches_phase386"]:
        outcome = "regression_failure"
    elif observed["maximum_lcp"] == len(TARGET) and empirical_p <= 0.01:
        outcome = "family_corrected_positive_checkpoint_only"
    elif observed["maximum_lcp"] == len(TARGET) and empirical_p <= 0.05:
        outcome = "suggestive_checkpoint_only"
    else:
        outcome = "not_exceptional"

    if not include_candidates:
        observed.pop("candidates")

    return {
        "phase": 425,
        "target": TARGET,
        "outcome": outcome,
        "keyword_source_count": len(KEYWORD_SOURCES),
        "distinct_square_count": len(square_manifest),
        "square_manifest": square_manifest,
        "schedule_manifest": {key: list(value) for key, value in schedules().items()},
        "configuration_axes": {
            "operation": ["decrypt", "encrypt"],
            "coordinate_order": ["rc", "cr"],
            "input_orientation": ["forward", "reverse"],
            "output_orientation": ["forward", "reverse"],
        },
        "observed": observed,
        "null": null,
        "tail_count": tail_count,
        "empirical_familywise_p": empirical_p,
        "planted_positive": planted_positive(square_manifest),
        "oracle_calls": 0,
    }


def self_test():
    square_manifest = keyword_square_manifest()
    assert square_manifest[0]["grid_keyword"] == "DBIFHCEGAKLMNOPQRSTUVWXYZ"
    assert square_manifest[0]["provenance"][0]["source"] == "dbbi"
    assert len(schedules()) == 8

    # Every coordinate convention and schedule must round-trip independently.
    char_to_index = {ch: i for i, ch in enumerate(ALPHABET_NO_J)}
    real = np.array([char_to_index[ch] for ch in normalize_letters(FAED)], dtype=np.int16)
    for square in square_manifest:
        lookup, positions, _mapping = square_arrays(square["grid_keyword"])
        for block_sizes in schedules().values():
            for order in ("rc", "cr"):
                decoded = transform_full(real, lookup, positions, block_sizes, "decrypt", order)
                recovered = transform_full(decoded, lookup, positions, block_sizes, "encrypt", order)
                assert np.array_equal(recovered, real), (square["square_id"], block_sizes, order)

    report = audit(trials=100, seed=DEFAULT_SEED, include_candidates=False)
    assert report["observed"]["original_matches_phase386"] is True
    assert report["observed"]["maximum_lcp"] == 7
    assert report["observed"]["exact_prefix_output_count"] >= 1
    assert report["planted_positive"] == {
        "roundtrip_matches": True,
        "recovered_prefix": TARGET,
        "detector_lcp": 7,
    }
    assert report["oracle_calls"] == 0
    print(
        "[*] self-test OK: all square/schedule/order round trips hold; "
        "the original Phase 386 output is reproduced; the observed family "
        "reaches exact BTCSEED; planted detector positive recovered"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--trials", type=int, default=DEFAULT_TRIALS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--compact", action="store_true", help="omit per-configuration manifest")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    print(
        json.dumps(
            audit(args.trials, args.seed, include_candidates=not args.compact),
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()

