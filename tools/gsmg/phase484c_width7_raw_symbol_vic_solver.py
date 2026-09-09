#!/usr/bin/env python3
"""Phase 484C synthetic-only exhaustive width-7 joint rank development."""

from __future__ import annotations

import argparse
import concurrent.futures
import itertools
import json
import math
import time
from pathlib import Path

import numpy as np

import phase484a_raw_symbol_vic_solver as base

SCRIPT_DIR = Path(__file__).resolve().parent
WIDTH = 7
HYPOTHESES_TOTAL = len(base.ESCAPE_PAIRS) * math.factorial(WIDTH)
DEFAULT_START = 50
DEFAULT_COUNT = 5
WORKERS = 8
SEED_HOLDOUT = 0x484C401D
JOINT_KEEP = 1536
BOARD_RESTARTS = 2
BOARD_ITERS = 6000
TAIL_FIXTURES = (("vic_profile", 57), ("broad_random", 56))


def enumerate_joint(observed: str, model: base.SpectralModel,
                    keep: int | None = None) -> dict:
    """Rank all width-7 escape-pair/order hypotheses deterministically."""
    if len(observed) != base.RAW_LENGTH:
        raise ValueError("observed stream must contain exactly 570 symbols")
    if keep is not None and keep <= 0:
        raise ValueError("keep must be positive")
    ranked = []
    invalid = 0
    for pair_index, pair in enumerate(base.ESCAPE_PAIRS):
        result = base.enumerate_orders_by_spectral(
            observed, WIDTH, pair, model, keep=None,
        )
        invalid += result["invalid_segmentations"]
        ranked.extend(
            (entry["score"], pair_index, tuple(entry["order"]))
            for entry in result["shortlist"]
        )
    ranked.sort(key=lambda item: (-item[0], item[1], item[2]))
    selected = ranked if keep is None else ranked[:keep]
    return {
        "width": WIDTH,
        "hypotheses_total": HYPOTHESES_TOTAL,
        "valid_hypotheses": len(ranked),
        "invalid_segmentations": invalid,
        "shortlist": [
            {
                "score": score,
                "pair_index": pair_index,
                "pair": list(base.ESCAPE_PAIRS[pair_index]),
                "order": list(order),
            }
            for score, pair_index, order in selected
        ],
    }


def planted_rank(fixture: dict, model: base.SpectralModel) -> dict:
    ranked = enumerate_joint(fixture["observed"], model)
    pair_index = base.ESCAPE_PAIRS.index(tuple(fixture["pair"]))
    order = list(fixture["order"])
    for rank, entry in enumerate(ranked["shortlist"], start=1):
        if entry["pair_index"] == pair_index and entry["order"] == order:
            return {
                "rank": rank,
                "score": entry["score"],
                "valid_hypotheses": ranked["valid_hypotheses"],
                "invalid_segmentations": ranked["invalid_segmentations"],
            }
    raise AssertionError("planted hypothesis was not valid")


def rank_job(job: tuple[str, int]) -> dict:
    board_mode, fixture_index = job
    model = base.SpectralModel.from_training_corpus()
    fixture = base.make_fixture(
        WIDTH, 0, fixture_index, board_mode=board_mode, split="dev",
    )
    began = time.monotonic()
    result = planted_rank(fixture, model)
    return {
        "board_mode": board_mode,
        "fixture_index": fixture_index,
        **result,
        "wall_seconds": time.monotonic() - began,
    }


def run_rank_batch(start: int = DEFAULT_START, count: int = DEFAULT_COUNT,
                   workers: int = WORKERS) -> dict:
    if count <= 0:
        raise ValueError("count must be positive")
    began = time.monotonic()
    jobs = [
        (board_mode, fixture_index)
        for board_mode in base.BOARD_MODES
        for fixture_index in range(start, start + count)
    ]
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as pool:
        completed = list(pool.map(rank_job, jobs))
    cells = []
    for board_mode in base.BOARD_MODES:
        records = [record for record in completed if record["board_mode"] == board_mode]
        ranks = [record["rank"] for record in records]
        cells.append({
            "board_mode": board_mode,
            "fixture_count": count,
            "minimum_rank": min(ranks),
            "median_rank": float(np.median(ranks)),
            "maximum_rank": max(ranks),
            "records": records,
        })
    return {
        "phase": "484C",
        "status": "informal_width7_joint_rank_dev_not_frozen",
        "faed_scored": False,
        "fixture_split": "dev",
        "width": WIDTH,
        "pair_index": 0,
        "fixture_index_start": start,
        "fixtures_per_pool": count,
        "hypotheses_total": HYPOTHESES_TOTAL,
        "workers": workers,
        "wall_seconds": time.monotonic() - began,
        "cells": cells,
    }


def solve_fixture_joint(fixture: dict, joint_keep: int = JOINT_KEEP,
                        board_restarts: int = BOARD_RESTARTS,
                        board_iters: int = BOARD_ITERS,
                        seed: int = base.SEED_DEV) -> dict:
    """Blind width-7 pair/order/board solve using the exhaustive ranker."""
    if fixture["width"] != WIDTH:
        raise ValueError("Phase 484C solver accepts only width-7 fixtures")
    model = base.SpectralModel.from_training_corpus()
    quad, _ = base.load_language_model()
    ranked = enumerate_joint(fixture["observed"], model, keep=joint_keep)
    geometry = base.Geometry(base.RAW_LENGTH, WIDTH)
    candidates = []
    for rank, entry in enumerate(ranked["shortlist"], start=1):
        pair_index = entry["pair_index"]
        pair = base.ESCAPE_PAIRS[pair_index]
        codes = base.slot_codes(pair)
        code_to_slot = {code: index for index, code in enumerate(codes)}
        raw = geometry.decrypt(fixture["observed"], entry["order"])
        segmented = base.segment_raw(raw, pair)
        if segmented is None:
            continue
        token_slots = np.array([code_to_slot[code] for code in segmented], dtype=np.int64)
        best_key, best_score = None, -math.inf
        for restart in range(board_restarts):
            rng = base.PCG32(base.derive_seed(
                seed, WIDTH, pair_index, *entry["order"], restart,
            ))
            key, score = base.anneal_board(
                token_slots, quad, rng, board_iters, 20.0, 1.0,
            )
            if score > best_score:
                best_key, best_score = key, score
        candidates.append({
            "rank": rank,
            "pair_index": pair_index,
            "pair": pair,
            "order": entry["order"],
            "decoded_length": len(segmented),
            "quadgram_score": best_score,
            "normalized_score": base.normalized_quadgram_score(best_score, len(segmented)),
            "key": best_key,
        })
    eligible = [c for c in candidates if c["decoded_length"] >= base.MIN_DECODED_LENGTH]
    winner = max(eligible, key=lambda c: c["normalized_score"])
    codes = base.slot_codes(winner["pair"])
    code_to_letter = {
        codes[slot]: base.LETTER_ALPHABET[int(winner["key"][slot])]
        for slot in range(25)
    }
    raw = geometry.decrypt(fixture["observed"], winner["order"])
    plaintext = base.decode_raw(raw, winner["pair"], code_to_letter)
    truth = fixture["plaintext"]
    matches = sum(a == b for a, b in zip(plaintext, truth))
    true_pair = tuple(fixture["pair"])
    pair_recovered = winner["pair"] == true_pair
    board_accuracy = 0.0
    if pair_recovered:
        true_board = {code: letter for letter, code in fixture["letter_to_code"].items()}
        board_accuracy = sum(code_to_letter[c] == true_board[c] for c in codes) / 25
    planted_pair_index = base.ESCAPE_PAIRS.index(true_pair)
    planted_rank_value = next(
        (rank for rank, entry in enumerate(ranked["shortlist"], start=1)
         if entry["pair_index"] == planted_pair_index
         and entry["order"] == list(fixture["order"])),
        None,
    )
    exact_order = winner["order"] == list(fixture["order"])
    return {
        "width": WIDTH,
        "joint_keep": joint_keep,
        "planted_in_shortlist": planted_rank_value is not None,
        "planted_rank": planted_rank_value,
        "winner_rank": winner["rank"],
        "escape_pair_recovery": pair_recovered,
        "exact_order_recovery": exact_order,
        "joint_recovery": pair_recovered and exact_order,
        "kendall_tau": base.kendall_tau(fixture["order"], winner["order"]),
        "board_accuracy": board_accuracy,
        "plaintext_char_accuracy": matches / len(truth),
        "decoded_length": len(plaintext),
        "true_length": len(truth),
        "winner_pair": list(winner["pair"]),
        "winner_order": winner["order"],
        "winner_normalized_score": winner["normalized_score"],
    }


def solve_tail_job(spec: tuple[str, int]) -> dict:
    board_mode, fixture_index = spec
    fixture = base.make_fixture(
        WIDTH, 0, fixture_index, board_mode=board_mode, split="dev",
    )
    result = solve_fixture_joint(
        fixture, seed=base.derive_seed(base.SEED_DEV, WIDTH, fixture_index),
    )
    return {"board_mode": board_mode, "fixture_index": fixture_index, **result}


def run_tail_batch() -> dict:
    with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
        records = list(pool.map(solve_tail_job, TAIL_FIXTURES))
    return {
        "phase": "484C",
        "status": "informal_width7_joint_tail_dev_not_frozen",
        "faed_scored": False,
        "fixture_split": "dev",
        "budgets": {
            "joint_keep": JOINT_KEEP,
            "board_restarts": BOARD_RESTARTS,
            "board_iters": BOARD_ITERS,
            "board_t0": 20.0,
            "board_t1": 1.0,
        },
        "joint_recovery_count": sum(r["joint_recovery"] for r in records),
        "fixture_count": len(records),
        "records": records,
    }


def self_test() -> None:
    assert WIDTH == 7
    assert HYPOTHESES_TOTAL == 181440
    geometry = base.Geometry(base.RAW_LENGTH, WIDTH)
    assert geometry.column_lengths == (82, 82, 82, 81, 81, 81, 81)
    fixture = base.make_fixture(WIDTH, 0, 49, board_mode="broad_random")
    base.verify_fixture(fixture)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--rank-dev", action="store_true")
    parser.add_argument("--tail-dev", action="store_true")
    parser.add_argument("--start", type=int, default=DEFAULT_START)
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT)
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("self-test: ok")
        return 0
    if args.tail_dev:
        result = run_tail_batch()
        path = SCRIPT_DIR / "phase484c_width7_tail_dev_result.json"
        path.write_text(json.dumps(result, indent=2))
        for record in result["records"]:
            print(record["board_mode"], record["fixture_index"],
                  "rank", record["planted_rank"],
                  "recovered", record["joint_recovery"])
        print("wrote", path)
        return 0
    if not args.rank_dev:
        parser.error("pass --self-test, --rank-dev, or --tail-dev")
    result = run_rank_batch(args.start, args.count)
    path = SCRIPT_DIR / "phase484c_width7_rank_dev_result.json"
    path.write_text(json.dumps(result, indent=2))
    for cell in result["cells"]:
        print(cell["board_mode"], "median", cell["median_rank"],
              "max", cell["maximum_rank"])
    print("wrote", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
