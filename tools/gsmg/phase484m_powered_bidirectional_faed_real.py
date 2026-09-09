#!/usr/bin/env python3
"""Locked real FAED run of the powered Phase 484K/L bidirectional solver."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import heapq
import itertools
import json
import math
import os
from pathlib import Path

import numpy as np

import phase484a_raw_symbol_vic_solver as base
import phase484g_hard_negative_discriminator as learned
import phase484h_discriminator_landscape_probe as full_model
import phase484j_constructive_prefix_beam_probe as prefix
import phase484k_bidirectional_segment_assembly_probe as order_solver
from data import FAED

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
PROTOCOL = REPO_ROOT / "doc/Brainstorms/2026-09-07 - Phase 484M Powered Bidirectional FAED Real Protocol.md"
LOCK_PATH = SCRIPT_DIR / "phase484m_execution_lock.json"
RESULT_PATH = SCRIPT_DIR / "phase484m_result.json"
WIDTHS = (10, 15)
PAIRS = base.ESCAPE_PAIRS
BOARD_RESTARTS = 2
BOARD_ITERS = 6000
BOARD_T0 = 20.0
BOARD_T1 = 1.0
SCORE_FLOOR = -4.571151156706407
SEED_REAL = 0x484B100
WORKERS = 6
TOP_RESULTS = 20
_MODEL_CACHE = {}
_CLASSIFIER = None
_SPECTRAL = None
_QUAD = None


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def faed_hash() -> str:
    return hashlib.sha256(FAED.encode("ascii")).hexdigest()


def pinned_files() -> dict[str, Path]:
    return {
        "protocol": PROTOCOL,
        "real_runner": Path(__file__),
        "verifier": SCRIPT_DIR / "phase484m_verify_run.py",
        "base_solver": SCRIPT_DIR / "phase484a_raw_symbol_vic_solver.py",
        "discriminator": SCRIPT_DIR / "phase484g_hard_negative_discriminator.py",
        "discriminator_result": SCRIPT_DIR / "phase484g_hard_negative_discriminator_result.json",
        "prefix_solver": SCRIPT_DIR / "phase484j_constructive_prefix_beam_probe.py",
        "bidirectional_solver": SCRIPT_DIR / "phase484k_bidirectional_segment_assembly_probe.py",
        "holdout_runner": SCRIPT_DIR / "phase484l_bidirectional_holdout_gate.py",
        "holdout_lock": SCRIPT_DIR / "phase484l_execution_lock.json",
        "holdout_result": SCRIPT_DIR / "phase484l_holdout_result.json",
        "holdout_verification": SCRIPT_DIR / "phase484l_verification.json",
        "quadgrams": base.QUADGRAM_FILE,
        "corpus": base.CORPUS_FILE,
    }


def lock_payload() -> dict:
    return {
        "phase": "484M",
        "status": "locked_before_real_run",
        "files_sha256": {
            name: sha256_file(path) for name, path in pinned_files().items()
        },
        "faed_ascii_sha256": faed_hash(),
        "faed_length": len(FAED),
        "scope": {
            "widths": list(WIDTHS),
            "pairs": [list(pair) for pair in PAIRS],
            "cell_count": len(WIDTHS) * len(PAIRS),
        },
        "budgets": {
            "start_depth": prefix.START_DEPTH,
            "beam_width": order_solver.BEAM_WIDTH,
            "reserved_fraction": order_solver.RESERVED_FRACTION,
            "board_restarts": BOARD_RESTARTS,
            "board_iters": BOARD_ITERS,
            "board_t0": BOARD_T0,
            "board_t1": BOARD_T1,
            "score_floor": SCORE_FLOOR,
            "seed_real": SEED_REAL,
            "workers": WORKERS,
            "top_results": TOP_RESULTS,
        },
        "prohibitions": {
            "rerun": True,
            "width_19": True,
            "ragged_widths": True,
            "post_lock_tuning": True,
        },
    }


def verify_lock() -> dict:
    lock = json.loads(LOCK_PATH.read_text())
    if lock != lock_payload():
        raise RuntimeError("Phase 484M execution lock mismatch")
    return lock


def runtime_models(width: int):
    global _CLASSIFIER, _SPECTRAL, _QUAD
    if width not in _MODEL_CACHE:
        _MODEL_CACHE[width] = prefix.train_models(width)
    if _CLASSIFIER is None:
        _CLASSIFIER = full_model.load_model()
    if _SPECTRAL is None:
        _SPECTRAL = base.SpectralModel.from_training_corpus()
    if _QUAD is None:
        _QUAD, _ = base.load_language_model()
    return _MODEL_CACHE[width], _CLASSIFIER, _SPECTRAL, _QUAD


def blind_order_search(observed: str, width: int, pair: tuple[str, str]) -> dict:
    models, classifier, spectral, _ = runtime_models(width)
    fixture = {"observed": observed, "width": width, "pair": list(pair)}
    blocks = prefix.blocks_from_observed(fixture)
    candidates = {
        path: prefix.score_prefix(models[prefix.START_DEPTH], blocks, pair, path)
        for path in itertools.permutations(range(width), prefix.START_DEPTH)
    }
    beam = order_solver.select_diverse(candidates, width)
    for depth in range(prefix.START_DEPTH, width):
        next_depth = depth + 1
        extended = {}
        for _, path in beam:
            used = set(path)
            for block in range(width):
                if block in used:
                    continue
                for candidate in ((block,) + path, path + (block,)):
                    if candidate in extended:
                        continue
                    if next_depth == width:
                        order = prefix.sequence_to_order(candidate)
                        score = full_model.objective(
                            classifier, spectral, fixture, order
                        )
                    else:
                        score = prefix.score_prefix(
                            models[next_depth], blocks, pair, candidate
                        )
                    if score is not None:
                        extended[candidate] = score
        if not extended:
            raise RuntimeError("real beam produced no valid extensions")
        beam = order_solver.select_diverse(extended, width)
    best_score, sequence = beam[0]
    return {
        "order_score": best_score,
        "sequence": list(sequence),
        "order": prefix.sequence_to_order(sequence),
        "terminal_beam_size": len(beam),
    }


def solve_cell(spec) -> dict:
    width, pair_index = spec
    pair = PAIRS[pair_index]
    search = blind_order_search(FAED, width, pair)
    geometry = base.Geometry(len(FAED), width)
    raw = geometry.decrypt(FAED, search["order"])
    segmented = base.segment_raw(raw, pair)
    if segmented is None:
        raise RuntimeError("winning order has invalid segmentation")
    codes = base.slot_codes(pair)
    code_to_slot = {code: index for index, code in enumerate(codes)}
    token_slots = np.asarray([code_to_slot[code] for code in segmented], dtype=np.int64)
    _, _, _, quad = runtime_models(width)
    best_key, best_quad = None, -math.inf
    for restart in range(BOARD_RESTARTS):
        rng = base.PCG32(base.derive_seed(
            SEED_REAL, width, pair_index, *search["order"], restart
        ))
        key, score = base.anneal_board(
            token_slots, quad, rng, BOARD_ITERS, BOARD_T0, BOARD_T1
        )
        if score > best_quad:
            best_key, best_quad = key, score
    board = {
        codes[slot]: base.LETTER_ALPHABET[int(best_key[slot])]
        for slot in range(25)
    }
    plaintext = base.decode_raw(raw, pair, board)
    return {
        "width": width,
        "pair_index": pair_index,
        "pair": list(pair),
        **search,
        "decoded_length": len(segmented),
        "quadgram_score": best_quad,
        "normalized_score": base.normalized_quadgram_score(
            best_quad, len(segmented)
        ),
        "plaintext": plaintext,
        "board": board,
    }


def run_real() -> dict:
    lock = verify_lock()
    specs = [
        (width, pair_index)
        for width in WIDTHS for pair_index in range(len(PAIRS))
    ]
    with concurrent.futures.ProcessPoolExecutor(max_workers=WORKERS) as pool:
        cells = list(pool.map(solve_cell, specs))
    cells.sort(key=lambda cell: (cell["width"], cell["pair_index"]))
    ranked = sorted(
        cells,
        key=lambda cell: (
            -cell["normalized_score"], cell["width"],
            cell["pair_index"], cell["order"],
        ),
    )
    best = ranked[0]
    trigger = best["normalized_score"] >= SCORE_FLOOR
    return {
        "phase": "484M",
        "status": "locked_real_run_complete",
        "execution_lock_sha256": sha256_file(LOCK_PATH),
        "faed_ascii_sha256": faed_hash(),
        "scope": lock["scope"],
        "budgets": lock["budgets"],
        "cell_count": len(cells),
        "cells": cells,
        "top": ranked[:TOP_RESULTS],
        "family_best": best,
        "score_trigger": trigger,
        "disposition": (
            "confirmation_required" if trigger
            else "no_powered_width10_15_bidirectional_solve"
        ),
    }


def self_test() -> None:
    assert len(FAED) == 570
    assert faed_hash() == "066191b4aafc114fbca7f0d168382f40129c4ff18490375b689741081d5ef3c2"
    assert len(PAIRS) == 36 and len(WIDTHS) * len(PAIRS) == 72
    assert 570 % 10 == 0 and 570 % 15 == 0
    assert 19 not in WIDTHS
    sequence = list(range(10))
    assert prefix.sequence_to_order(sequence) == sequence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write-lock", action="store_true")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if sum((args.self_test, args.write_lock, args.run)) != 1:
        parser.error("choose exactly one action")
    if args.self_test:
        self_test()
        print("self-test: ok")
        return 0
    if args.write_lock:
        LOCK_PATH.write_text(json.dumps(lock_payload(), indent=2, sort_keys=True) + "\n")
        print(LOCK_PATH)
        return 0
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    result = run_real()
    temporary = RESULT_PATH.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    temporary.replace(RESULT_PATH)
    best = result["family_best"]
    print("best", best["width"], best["pair"],
          round(best["normalized_score"], 6))
    print("plaintext", best["plaintext"])
    print("score_trigger", result["score_trigger"])
    print("disposition", result["disposition"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
