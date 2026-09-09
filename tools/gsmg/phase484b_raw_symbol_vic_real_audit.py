#!/usr/bin/env python3
"""Phase 484B: locked real FAED run of the powered small-width Model-B solver."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import math
import os
from pathlib import Path

import numpy as np

import phase484a_raw_symbol_vic_solver as solver
from data import FAED

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
LOCK_PATH = SCRIPT_DIR / "phase484b_execution_lock.json"
RESULT_PATH = SCRIPT_DIR / "phase484b_result.json"
WIDTHS = (2, 3, 5, 6)
JOINT_KEEP = 1536
BOARD_RESTARTS = 2
BOARD_ITERS = 6000
BOARD_T0 = 20.0
BOARD_T1 = 1.0
TOP_PER_WIDTH = 10
SEED_REAL = 0x484B0001
HOLDOUT_SCORE_FLOOR = -4.571151156706407
WORKERS = 4


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def input_sha256(observed: str) -> str:
    return hashlib.sha256(observed.encode("ascii")).hexdigest()


def verify_lock() -> dict:
    lock = json.loads(LOCK_PATH.read_text())
    paths = {name: REPO_ROOT / relative for name, relative in lock["paths"].items()}
    if {name: sha256_file(path) for name, path in paths.items()} != lock["files_sha256"]:
        raise RuntimeError("execution lock hash mismatch")
    expected = {
        "widths": list(WIDTHS),
        "joint_keep": JOINT_KEEP,
        "board_restarts": BOARD_RESTARTS,
        "board_iters": BOARD_ITERS,
        "board_t0": BOARD_T0,
        "board_t1": BOARD_T1,
        "top_per_width": TOP_PER_WIDTH,
        "seed_real": SEED_REAL,
        "holdout_score_floor": HOLDOUT_SCORE_FLOOR,
        "workers": WORKERS,
    }
    if lock["configuration"] != expected:
        raise RuntimeError("execution lock configuration mismatch")
    if input_sha256(FAED) != lock["faed_ascii_sha256"] or len(FAED) != 570:
        raise RuntimeError("FAED input mismatch")
    return lock


def solve_observed_width(observed: str, width: int, joint_keep: int = JOINT_KEEP,
                         board_restarts: int = BOARD_RESTARTS,
                         board_iters: int = BOARD_ITERS,
                         seed: int = SEED_REAL) -> dict:
    model = solver.SpectralModel.from_training_corpus()
    quad, _ = solver.load_language_model()
    ranked = solver.enumerate_pair_orders_by_spectral(observed, width, model, keep=joint_keep)
    geometry = solver.Geometry(len(observed), width)
    candidates = []
    for spectral_rank, entry in enumerate(ranked["shortlist"], start=1):
        pair_index = entry["pair_index"]
        pair = solver.ESCAPE_PAIRS[pair_index]
        codes = solver.slot_codes(pair)
        code_to_slot = {code: index for index, code in enumerate(codes)}
        raw = geometry.decrypt(observed, entry["order"])
        segmented = solver.segment_raw(raw, pair)
        if segmented is None:
            continue
        token_slots = np.array([code_to_slot[code] for code in segmented], dtype=np.int64)
        best_key, best_score = None, -math.inf
        for restart in range(board_restarts):
            rng = solver.PCG32(
                solver.derive_seed(seed, width, pair_index, *entry["order"], restart)
            )
            key, score = solver.anneal_board(
                token_slots, quad, rng, board_iters, BOARD_T0, BOARD_T1
            )
            if score > best_score:
                best_key, best_score = key, score
        code_to_letter = {
            codes[slot]: solver.LETTER_ALPHABET[int(best_key[slot])]
            for slot in range(25)
        }
        plaintext = solver.decode_raw(raw, pair, code_to_letter)
        candidates.append({
            "spectral_rank": spectral_rank,
            "pair_index": pair_index,
            "pair": list(pair),
            "order": entry["order"],
            "decoded_length": len(segmented),
            "quadgram_score": best_score,
            "normalized_score": solver.normalized_quadgram_score(best_score, len(segmented)),
            "plaintext": plaintext,
            "board": code_to_letter,
        })
    eligible = [c for c in candidates if c["decoded_length"] >= solver.MIN_DECODED_LENGTH]
    eligible.sort(key=lambda c: (-c["normalized_score"], c["pair_index"], c["order"]))
    top = eligible[:TOP_PER_WIDTH]
    return {
        "width": width,
        "hypotheses_total": ranked["hypotheses_total"],
        "valid_hypotheses": ranked["valid_hypotheses"],
        "retained_hypotheses": len(ranked["shortlist"]),
        "eligible_board_solutions": len(eligible),
        "top": top,
    }


def run_real() -> dict:
    with concurrent.futures.ProcessPoolExecutor(max_workers=WORKERS) as pool:
        cells = list(pool.map(solve_observed_width, [FAED] * len(WIDTHS), WIDTHS))
    all_top = [candidate | {"width": cell["width"]} for cell in cells for candidate in cell["top"]]
    all_top.sort(key=lambda c: (-c["normalized_score"], c["width"], c["pair_index"], c["order"]))
    best = all_top[0]
    return {
        "phase": "484B",
        "status": "locked_real_run_complete",
        "faed_ascii_sha256": input_sha256(FAED),
        "execution_lock_sha256": sha256_file(LOCK_PATH),
        "cells": cells,
        "family_best": best,
        "score_trigger": best["normalized_score"] >= HOLDOUT_SCORE_FLOOR,
        "disposition": (
            "confirmation_required" if best["normalized_score"] >= HOLDOUT_SCORE_FLOOR
            else "no_powered_family_solve_no_calibrated_null_claim"
        ),
    }


def self_test() -> None:
    assert len(FAED) == 570 and set(FAED) == set(solver.NINE_SYMBOLS)
    assert input_sha256(FAED) == "066191b4aafc114fbca7f0d168382f40129c4ff18490375b689741081d5ef3c2"
    fixture = solver.make_fixture(2, 0, 46, board_mode="broad_random")
    result = solve_observed_width(
        fixture["observed"], 2, joint_keep=4, board_restarts=1,
        board_iters=100, seed=7,
    )
    assert result["width"] == 2 and len(result["top"]) == 4
    assert all(len(candidate["plaintext"]) == candidate["decoded_length"] for candidate in result["top"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("self-test: ok")
        return 0
    verify_lock()
    if not args.run:
        print("lock verified; pass --run for the one real FAED search")
        return 0
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    result = run_real()
    temporary = RESULT_PATH.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(result, indent=2, sort_keys=True))
    temporary.replace(RESULT_PATH)
    best = result["family_best"]
    print("best", best["width"], best["pair"], best["normalized_score"])
    print("plaintext", best["plaintext"])
    print("score_trigger", result["score_trigger"])
    print("disposition", result["disposition"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
