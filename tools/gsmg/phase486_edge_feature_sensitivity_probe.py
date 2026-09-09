#!/usr/bin/env python3
"""Phase 486 development infrastructure for a raw-symbol column-adjacency
edge-feature sensitivity probe.

This module intentionally does not import or score FAED. It tests whether a
permutation-invariant spectral edge score can identify a raw-symbol column's
true right-neighbor among the other width-1 candidate columns, at Lane 2's
exact-division widths (10, 15, 19, 30, 38), reusing the checkerboard raw-
symbol construction already powered in Phase 484A-D.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

import phase484a_raw_symbol_vic_solver as base

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
PROTOCOL = REPO_ROOT / "doc/Brainstorms/2026-09-07 - Phase 486 Edge-Feature Sensitivity Probe Protocol.md"
DEFAULT_LOCK = SCRIPT_DIR / "phase486_execution_lock.json"

WIDTHS = (10, 15, 19, 30, 38)
BOARD_MODES = base.BOARD_MODES
PAIR_INDEX = 0
FIXTURES_PER_CELL = 10
SEED_DEV = 0x486A0DE
SEED_HOLDOUT = 0x486A401D
SEED_TRAIN = 0x486A7A21
SYMBOL_INDEX = {symbol: index for index, symbol in enumerate(base.NINE_SYMBOLS)}


def draw_board(board_mode: str, rng: base.PCG32, pair: tuple[str, str]) -> dict[str, str]:
    """Mirrors phase484a_raw_symbol_vic_solver.make_fixture's board construction."""
    codes = base.slot_codes(pair)
    if board_mode == "broad_random":
        letters = list(base.LETTER_ALPHABET)
        rng.shuffle(letters)
    elif board_mode == "vic_profile":
        training = base.corpus_splits()["train"]
        frequencies = {letter: training.count(letter) for letter in base.LETTER_ALPHABET}
        common = sorted(base.LETTER_ALPHABET, key=lambda letter: (-frequencies[letter], letter))[:7]
        other = [letter for letter in base.LETTER_ALPHABET if letter not in common]
        rng.shuffle(common)
        rng.shuffle(other)
        letters = common + other
    else:
        raise ValueError(f"unknown board mode: {board_mode}")
    return dict(zip(letters, codes))


def raw_symbol_transition_matrix(raw: str) -> np.ndarray:
    indices = np.array([SYMBOL_INDEX[ch] for ch in raw], dtype=np.int64)
    matrix = np.zeros((9, 9), dtype=np.float64)
    np.add.at(matrix, (indices[:-1], indices[1:]), 1.0)
    total = float(matrix.sum())
    if total:
        matrix /= total
    return matrix


def train_reference_target(board_mode: str) -> np.ndarray:
    """Permutation-invariant spectral signature of real-language adjacent-
    raw-symbol co-occurrence, under this board_mode's structural template.
    Trained only from the frozen training corpus split; never dev or holdout."""
    pair = base.ESCAPE_PAIRS[PAIR_INDEX]
    rng = base.PCG32(base.derive_seed(SEED_TRAIN, BOARD_MODES.index(board_mode)))
    board = draw_board(board_mode, rng, pair)
    training = base.corpus_splits()["train"]
    raw = base.encode_plaintext(training, board)
    matrix = raw_symbol_transition_matrix(raw)
    return base.spectral_features(matrix)


def edge_score(col_a: str, col_b: str, target: np.ndarray) -> float:
    a = np.array([SYMBOL_INDEX[ch] for ch in col_a], dtype=np.int64)
    b = np.array([SYMBOL_INDEX[ch] for ch in col_b], dtype=np.int64)
    matrix = np.zeros((9, 9), dtype=np.float64)
    np.add.at(matrix, (a, b), 1.0)
    total = float(matrix.sum())
    if total:
        matrix /= total
    difference = base.spectral_features(matrix) - target
    return -float(np.dot(difference, difference))


def true_columns(raw: str, width: int) -> list[str]:
    if len(raw) % width:
        raise ValueError("phase 486 only covers exact-division widths")
    return [raw[c::width] for c in range(width)]


def raw_symbol_fixture(width: int, fixture_index: int, seed: int, board_mode: str, split: str) -> dict:
    return base.make_fixture(width=width, pair_index=PAIR_INDEX, fixture_index=fixture_index,
                             seed=seed, board_mode=board_mode, split=split)


def evaluate_fixture(fixture: dict, target: np.ndarray) -> dict:
    width = fixture["width"]
    cols = true_columns(fixture["raw"], width)
    ranks = []
    for c in range(width - 1):
        scored = []
        for other in range(width):
            if other == c:
                continue
            scored.append((edge_score(cols[c], cols[other], target), other))
        scored.sort(key=lambda item: (-item[0], item[1]))
        rank = next(i for i, (_, other) in enumerate(scored, start=1) if other == c + 1)
        ranks.append(rank)
    ranks_arr = np.array(ranks, dtype=np.float64)
    return {
        "fixture_index": fixture["fixture_index"],
        "width": width,
        "board_mode": fixture["board_mode"],
        "boundaries": int(len(ranks)),
        "top1_accuracy": float(np.mean(ranks_arr == 1)),
        "mean_reciprocal_rank": float(np.mean(1.0 / ranks_arr)),
        "ranks": [int(r) for r in ranks],
    }


def fixture_passes(record: dict, min_top1: float, min_mrr: float) -> bool:
    return (record["top1_accuracy"] >= min_top1
            and record["mean_reciprocal_rank"] >= min_mrr)


def run_batch(split: str, widths=WIDTHS, board_modes=BOARD_MODES,
             fixtures_per_cell: int = FIXTURES_PER_CELL,
             min_top1: float | None = None, min_mrr: float | None = None) -> dict:
    if split not in ("dev", "holdout"):
        raise ValueError("split must be dev or holdout")
    seed = SEED_DEV if split == "dev" else SEED_HOLDOUT
    cells = []
    for board_mode in board_modes:
        target = train_reference_target(board_mode)
        for width in widths:
            records = [
                evaluate_fixture(
                    raw_symbol_fixture(width, index, seed, board_mode, split), target
                )
                for index in range(fixtures_per_cell)
            ]
            passed = (
                sum(fixture_passes(r, min_top1, min_mrr) for r in records)
                if min_top1 is not None else None
            )
            cells.append({
                "board_mode": board_mode,
                "width": width,
                "fixture_count": fixtures_per_cell,
                "mean_top1_accuracy": float(np.mean([r["top1_accuracy"] for r in records])),
                "mean_reciprocal_rank": float(np.mean([r["mean_reciprocal_rank"] for r in records])),
                "passed_fixtures": passed,
                "gate_pass": (passed >= 8) if passed is not None else None,
                "records": records,
            })
    return {
        "phase": "486",
        "status": "informal_dev_scoping_not_frozen" if min_top1 is None or split == "dev" else "locked_holdout",
        "split": split,
        "faed_scored": False,
        "pair_index": PAIR_INDEX,
        "budgets": {"fixtures_per_cell": fixtures_per_cell},
        "gate": {"min_top1_accuracy": min_top1, "min_mean_reciprocal_rank": min_mrr},
        "cells": cells,
        "powered_cells": (
            [{"width": c["width"], "board_mode": c["board_mode"]}
             for c in cells if c["gate_pass"]]
            if min_top1 is not None else None
        ),
    }


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lock_payload(min_top1: float, min_mrr: float) -> dict:
    verifier = SCRIPT_DIR / "phase486_verify_run.py"
    corpus_file = base.CORPUS_FILE
    return {
        "phase": "486",
        "status": "locked-before-holdout",
        "files_sha256": {
            "protocol": sha256_file(PROTOCOL),
            "audit_script": sha256_file(Path(__file__)),
            "base_solver": sha256_file(SCRIPT_DIR / "phase484a_raw_symbol_vic_solver.py"),
            "verifier": sha256_file(verifier),
            "corpus": sha256_file(corpus_file),
        },
        "widths": list(WIDTHS),
        "board_modes": list(BOARD_MODES),
        "pair_index": PAIR_INDEX,
        "seeds": {"dev": SEED_DEV, "holdout": SEED_HOLDOUT, "train": SEED_TRAIN},
        "budgets": {"fixtures_per_cell": FIXTURES_PER_CELL},
        "gate": {
            "minimum_passed_fixtures": 8,
            "min_top1_accuracy": min_top1,
            "min_mean_reciprocal_rank": min_mrr,
        },
        "prohibitions": {
            "faed_scoring": True,
            "widths_other_than_lane2_five": True,
            "threshold_tuning_after_lock": True,
        },
        "faed_scored": False,
    }


def self_test() -> bool:
    assert base.RAW_LENGTH % 10 == 0 and base.RAW_LENGTH % 38 == 0
    for width in WIDTHS:
        assert base.RAW_LENGTH % width == 0
    matrix = np.eye(9, dtype=np.float64)
    features = base.spectral_features(matrix)
    assert features.shape[0] > 0
    cols = true_columns("abcdefghi" * 10, 9)
    assert len(cols) == 9 and all(len(c) == 10 for c in cols)
    target = train_reference_target("vic_profile")
    fixture = raw_symbol_fixture(10, 0, SEED_DEV, "vic_profile", "dev")
    record = evaluate_fixture(fixture, target)
    assert record["boundaries"] == 9
    assert all(1 <= r <= 9 for r in record["ranks"])
    tiny = run_batch("dev", widths=(10,), board_modes=("vic_profile",), fixtures_per_cell=1)
    assert tiny["faed_scored"] is False and tiny["powered_cells"] is None
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--dev-batch", action="store_true")
    parser.add_argument("--write-lock", action="store_true")
    parser.add_argument("--holdout", action="store_true")
    parser.add_argument("--min-top1", type=float)
    parser.add_argument("--min-mrr", type=float)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps({"self_test": self_test()}))
        return 0
    if args.write_lock:
        if args.min_top1 is None or args.min_mrr is None:
            parser.error("--write-lock requires --min-top1 and --min-mrr")
        DEFAULT_LOCK.write_text(
            json.dumps(lock_payload(args.min_top1, args.min_mrr), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(DEFAULT_LOCK)
        return 0
    if args.dev_batch:
        result = run_batch("dev", min_top1=args.min_top1, min_mrr=args.min_mrr)
    elif args.holdout:
        if args.min_top1 is None or args.min_mrr is None:
            parser.error("--holdout requires --min-top1 and --min-mrr")
        result = run_batch("holdout", min_top1=args.min_top1, min_mrr=args.min_mrr)
    else:
        parser.error("choose --self-test, --dev-batch, --holdout, or --write-lock")
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
