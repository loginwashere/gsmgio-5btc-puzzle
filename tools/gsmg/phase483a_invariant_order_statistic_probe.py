#!/usr/bin/env python3
"""Phase 483A: synthetic power probe for a local equality-pattern statistic.

No FAED data is imported or scored by this module.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
CORPUS_FILE = REPO_ROOT / "wordlists/gsmg/cosmic_duality_book_full_text.txt"
PROTOCOL = REPO_ROOT / "doc/Brainstorms/2026-09-06 - Phase 483A Substitution-Invariant Order Statistic Probe.md"
DEFAULT_LOCK = SCRIPT_DIR / "phase483a_execution_lock.json"

LENGTH = 436
WIDTHS = (7, 10, 12, 15, 19, 25, 30, 38, 40)
DIRECTIONS = ("untranspose", "transpose")
PATTERN_LENGTHS = (5, 6, 7, 8)
SMOOTHING = 0.2
FIXTURES_PER_CELL = 10
RANDOM_ORDERS = 10_000
CORRUPTIONS_PER_SEVERITY = 100
SEVERITIES = (1, 2, 4)
SEED_DEV = 0x483A0DE
SEED_HOLDOUT = 0x483A401D
M64 = (1 << 64) - 1
PCG_MULT = 6364136223846793005
NON_PROSE_PATTERNS = (
    r"^Table of Contents", r"INDEX", r"Acknowledgments", r"colophon",
    r"^Back matter", r"^End of transcription", r"^Front matter",
)


class PCG32:
    def __init__(self, initstate: int, initseq: int = 0x483A):
        self.state = 0
        self.inc = ((initseq << 1) | 1) & M64
        self.next_u32()
        self.state = (self.state + (initstate & M64)) & M64
        self.next_u32()

    def next_u32(self) -> int:
        old = self.state
        self.state = (old * PCG_MULT + self.inc) & M64
        xorshifted = (((old >> 18) ^ old) >> 27) & 0xFFFFFFFF
        rot = old >> 59
        return ((xorshifted >> rot) | (xorshifted << ((-rot) & 31))) & 0xFFFFFFFF

    def below(self, n: int) -> int:
        if n <= 0:
            raise ValueError("bound must be positive")
        return self.next_u32() % n

    def shuffle(self, values: list) -> None:
        for i in range(len(values) - 1, 0, -1):
            j = self.below(i + 1)
            values[i], values[j] = values[j], values[i]

    def permutation(self, n: int) -> list[int]:
        result = list(range(n))
        self.shuffle(result)
        return result


def derive_seed(base: int, *parts: int) -> int:
    value = base & M64
    for part in parts:
        value = ((value ^ (part & M64)) * 0x9E3779B97F4A7C15) & M64
        value ^= value >> 29
    return value


class Geometry:
    """Phase 477A ragged geometry; sigma means plain[p] = observed[sigma[p]]."""

    def __init__(self, length: int, width: int):
        self.length = length
        self.width = width
        self.rows = -(-length // width)
        self.short = width * self.rows - length
        self.lengths = np.array([
            self.rows - 1 if column >= width - self.short else self.rows
            for column in range(width)
        ], dtype=np.int64)
        positions = np.arange(length)
        self.row_of = positions // width
        self.col_of = positions % width

    def sigma(self, order) -> np.ndarray:
        order = np.asarray(order, dtype=np.int64)
        starts = np.concatenate(([0], np.cumsum(self.lengths[order])[:-1]))
        offsets = np.empty(self.width, dtype=np.int64)
        offsets[order] = starts
        return offsets[self.col_of] + self.row_of

    def position_map(self, order, direction: str) -> np.ndarray:
        untranspose = self.sigma(order)
        if direction == "untranspose":
            return untranspose
        if direction != "transpose":
            raise ValueError(f"unknown direction: {direction}")
        inverse = np.empty(self.length, dtype=np.int64)
        inverse[untranspose] = np.arange(self.length)
        return inverse


def corpus_letters() -> str:
    keep = True
    chunks = []
    for line in CORPUS_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section = line[3:]
            keep = not any(re.search(pattern, section) for pattern in NON_PROSE_PATTERNS)
            continue
        if line.startswith("#") or not keep:
            continue
        chunks.append(line)
    letters = "".join(ch for ch in "\n".join(chunks).upper() if "A" <= ch <= "Z")
    return letters.replace("J", "I")


def corpus_splits() -> dict[str, str]:
    text = corpus_letters()
    midpoint = len(text) // 2
    third = midpoint + len(text) // 4
    return {
        "train": text[:midpoint - 500],
        "dev": text[midpoint + 500:third - 500],
        "holdout": text[third + 500:],
    }


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lock_payload() -> dict:
    splits = corpus_splits()
    verifier = SCRIPT_DIR / "phase483a_verify_run.py"
    return {
        "phase": "483A",
        "status": "locked-before-holdout",
        "files_sha256": {
            "protocol": sha256_file(PROTOCOL),
            "audit_script": sha256_file(Path(__file__)),
            "verifier": sha256_file(verifier),
            "corpus": sha256_file(CORPUS_FILE),
        },
        "split_sha256": {
            name: hashlib.sha256(value.encode("ascii")).hexdigest()
            for name, value in splits.items()
        },
        "length": LENGTH,
        "widths": list(WIDTHS),
        "directions": list(DIRECTIONS),
        "pattern_lengths": list(PATTERN_LENGTHS),
        "smoothing": SMOOTHING,
        "seeds": {"dev": SEED_DEV, "holdout": SEED_HOLDOUT},
        "budgets": {
            "fixtures_per_cell": FIXTURES_PER_CELL,
            "random_orders_per_fixture": RANDOM_ORDERS,
            "corruptions_per_severity": CORRUPTIONS_PER_SEVERITY,
            "severities": list(SEVERITIES),
        },
        "gate": {
            "minimum_passed_fixtures": 8,
            "maximum_tie_inclusive_random_exceedances": 10,
            "requires_monotone_corruption_medians": True,
        },
        "faed_scored": False,
    }


def equality_codes(sequence: np.ndarray, size: int) -> np.ndarray:
    """Complete equality partition of every size-window as a uint32 mask."""
    sequence = np.asarray(sequence)
    windows = sequence.shape[0] - size + 1
    if windows <= 0:
        return np.empty(0, dtype=np.uint32)
    codes = np.zeros(windows, dtype=np.uint32)
    bit = 0
    for left in range(size):
        for right in range(left + 1, size):
            codes |= ((sequence[left:left + windows] == sequence[right:right + windows])
                      .astype(np.uint32) << bit)
            bit += 1
    return codes


@dataclass(frozen=True)
class PatternTable:
    size: int
    keys: np.ndarray
    log_probabilities: np.ndarray
    floor: float


class EqualityModel:
    def __init__(self, tables: tuple[PatternTable, ...]):
        self.tables = tables

    @classmethod
    def train(cls, text: str) -> "EqualityModel":
        sequence = np.frombuffer(text.encode("ascii"), dtype=np.uint8)
        tables = []
        for size in PATTERN_LENGTHS:
            codes = equality_codes(sequence, size)
            keys, counts = np.unique(codes, return_counts=True)
            denominator = float(codes.size + SMOOTHING * (keys.size + 1))
            floor = math.log(SMOOTHING / denominator)
            probabilities = np.log((counts.astype(np.float64) + SMOOTHING) / denominator)
            tables.append(PatternTable(size, keys, probabilities, floor))
        return cls(tuple(tables))

    def score(self, sequence: np.ndarray) -> float:
        total = 0.0
        for table in self.tables:
            codes = equality_codes(sequence, table.size)
            indices = np.searchsorted(table.keys, codes)
            valid = indices < table.keys.size
            found = np.zeros(codes.size, dtype=bool)
            found[valid] = table.keys[indices[valid]] == codes[valid]
            values = np.full(codes.size, table.floor, dtype=np.float64)
            values[found] = table.log_probabilities[indices[found]]
            total += float(values.sum())
        return total


def make_fixture(split: str, width: int, direction: str, index: int) -> dict:
    if split not in ("dev", "holdout"):
        raise ValueError("fixtures must use dev or holdout")
    base = SEED_DEV if split == "dev" else SEED_HOLDOUT
    direction_index = DIRECTIONS.index(direction)
    rng = PCG32(derive_seed(base, width, direction_index, index))
    source = corpus_splits()[split]
    start = rng.below(len(source) - LENGTH + 1)
    alphabet = "ABCDEFGHIKLMNOPQRSTUVWXYZ"
    letter_to_index = {letter: index for index, letter in enumerate(alphabet)}
    plain = np.fromiter(
        (letter_to_index[letter] for letter in source[start:start + LENGTH]),
        dtype=np.int64,
        count=LENGTH,
    )
    renaming = np.array(rng.permutation(25), dtype=np.int64)
    observed_plain = renaming[plain]
    order = rng.permutation(width)
    geometry = Geometry(LENGTH, width)
    observed = np.empty(LENGTH, dtype=np.int64)
    observed[geometry.position_map(order, direction)] = observed_plain
    return {
        "split": split,
        "width": width,
        "direction": direction,
        "index": index,
        "start": start,
        "order": order,
        "observed": observed,
    }


def corrupt_order(order: list[int], rng: PCG32, steps: int) -> list[int]:
    result = list(order)
    width = len(result)
    for _ in range(steps):
        move = rng.below(4)
        if move == 0:
            a, b = rng.below(width), rng.below(width)
            while b == a:
                b = rng.below(width)
            result[a], result[b] = result[b], result[a]
        elif move == 1:
            a, b = rng.below(width), rng.below(width)
            value = result.pop(a)
            result.insert(b, value)
        elif move == 2:
            a, b = sorted((rng.below(width), rng.below(width)))
            if a != b:
                result[a:b + 1] = reversed(result[a:b + 1])
        else:
            positions = []
            while len(positions) < 3:
                candidate = rng.below(width)
                if candidate not in positions:
                    positions.append(candidate)
            a, b, c = positions
            result[a], result[b], result[c] = result[c], result[a], result[b]
    return result


def reconstructed(fixture: dict, order: list[int]) -> np.ndarray:
    geometry = Geometry(LENGTH, fixture["width"])
    return fixture["observed"][geometry.position_map(order, fixture["direction"])]


def quantiles(values: list[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=np.float64)
    return {name: float(np.quantile(array, q)) for name, q in (
        ("q00", 0.0), ("q25", 0.25), ("q50", 0.5), ("q75", 0.75), ("q100", 1.0)
    )}


def evaluate_fixture(model: EqualityModel, fixture: dict, random_orders: int,
                     corruptions: int) -> dict:
    base = SEED_DEV if fixture["split"] == "dev" else SEED_HOLDOUT
    rng = PCG32(derive_seed(base, 0xE7A1, fixture["width"],
                            DIRECTIONS.index(fixture["direction"]), fixture["index"]))
    planted_score = model.score(reconstructed(fixture, fixture["order"]))
    random_scores = [
        model.score(reconstructed(fixture, rng.permutation(fixture["width"])))
        for _ in range(random_orders)
    ]
    exceedances = sum(score >= planted_score for score in random_scores)
    corruption = {}
    medians = []
    for severity in SEVERITIES:
        scores = [
            model.score(reconstructed(
                fixture, corrupt_order(fixture["order"], rng, severity)))
            for _ in range(corruptions)
        ]
        corruption[str(severity)] = quantiles(scores)
        medians.append(corruption[str(severity)]["q50"])
    local_degradation = (
        all(planted_score > median for median in medians)
        and medians[0] >= medians[1] >= medians[2]
    )
    random_gate = random_orders == RANDOM_ORDERS and exceedances <= 10
    return {
        "index": fixture["index"],
        "source_start": fixture["start"],
        "planted_score": planted_score,
        "random_orders": random_orders,
        "random_tie_inclusive_exceedances": exceedances,
        "random_percentile": 1.0 - exceedances / random_orders,
        "random_score_quantiles": quantiles(random_scores),
        "corruption_score_quantiles": corruption,
        "local_degradation": local_degradation,
        "full_budget_fixture_pass": random_gate and local_degradation,
    }


def run_probe(split: str, fixtures: int, random_orders: int, corruptions: int) -> dict:
    model = EqualityModel.train(corpus_splits()["train"])
    cells = []
    full_budget = (fixtures == FIXTURES_PER_CELL and random_orders == RANDOM_ORDERS
                   and corruptions == CORRUPTIONS_PER_SEVERITY)
    for width in WIDTHS:
        for direction in DIRECTIONS:
            rows = [evaluate_fixture(
                model, make_fixture(split, width, direction, index), random_orders, corruptions
            ) for index in range(fixtures)]
            passed = sum(row["full_budget_fixture_pass"] for row in rows)
            meets_numeric_gate = full_budget and passed >= 8
            cells.append({
                "width": width,
                "direction": direction,
                "fixture_count": fixtures,
                "passed_fixtures": passed,
                "meets_numeric_gate": meets_numeric_gate,
                "statistic_powered": split == "holdout" and meets_numeric_gate,
                "fixtures": rows,
            })
    return {
        "phase": "483A",
        "synthetic_only": True,
        "faed_scored": False,
        "split": split,
        "budgets": {
            "fixtures_per_cell": fixtures,
            "random_orders_per_fixture": random_orders,
            "corruptions_per_severity": corruptions,
        },
        "full_frozen_budget": full_budget,
        "cells": cells,
        "powered_cells": [
            {"width": row["width"], "direction": row["direction"]}
            for row in cells if row["statistic_powered"]
        ],
        "development_gate_equivalent_cells": [
            {"width": row["width"], "direction": row["direction"]}
            for row in cells if split == "dev" and row["meets_numeric_gate"]
        ],
    }


def self_test() -> bool:
    assert PATTERN_LENGTHS == (5, 6, 7, 8)
    assert len(corpus_splits()["train"]) > LENGTH
    base = np.array([0, 1, 2, 1, 0, 3, 3, 4], dtype=np.int64)
    renamed = np.array([9, 7, 4, 7, 9, 2, 2, 1], dtype=np.int64)
    for size in PATTERN_LENGTHS:
        assert np.array_equal(equality_codes(base, size), equality_codes(renamed, size))
    model = EqualityModel.train(corpus_splits()["train"])
    assert model.score(base) == model.score(renamed)
    for width in (7, 38):
        for direction in DIRECTIONS:
            fixture = make_fixture("dev", width, direction, 0)
            recovered = reconstructed(fixture, fixture["order"])
            assert recovered.shape == (LENGTH,)
            assert len(set(fixture["order"])) == width
    rng1, rng2 = PCG32(123), PCG32(123)
    assert [rng1.next_u32() for _ in range(20)] == [rng2.next_u32() for _ in range(20)]
    order = list(range(10))
    changed = corrupt_order(order, PCG32(99), 4)
    assert sorted(changed) == order
    assert changed != order
    tiny = run_probe("dev", fixtures=1, random_orders=2, corruptions=2)
    assert tiny["synthetic_only"] and not tiny["faed_scored"]
    assert not tiny["full_frozen_budget"] and not tiny["powered_cells"]
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write-lock", action="store_true")
    parser.add_argument("--probe", choices=("dev", "holdout"))
    parser.add_argument("--fixtures", type=int, default=FIXTURES_PER_CELL)
    parser.add_argument("--random-orders", type=int, default=RANDOM_ORDERS)
    parser.add_argument("--corruptions", type=int, default=CORRUPTIONS_PER_SEVERITY)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps({"self_test": self_test()}))
        return 0
    if args.write_lock:
        DEFAULT_LOCK.write_text(
            json.dumps(lock_payload(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(DEFAULT_LOCK)
        return 0
    if not args.probe:
        parser.error("choose --self-test or --probe")
    if min(args.fixtures, args.random_orders, args.corruptions) <= 0:
        parser.error("all budgets must be positive")
    result = run_probe(args.probe, args.fixtures, args.random_orders, args.corruptions)
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

