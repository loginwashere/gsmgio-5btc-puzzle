#!/usr/bin/env python3
"""Locked real FAED width-7 run using the Phase 484C powered solver."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

import phase484c_width7_raw_symbol_vic_solver as solver
from data import FAED

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
LOCK_PATH = SCRIPT_DIR / "phase484d_execution_lock.json"
RESULT_PATH = SCRIPT_DIR / "phase484d_result.json"
TOP_COUNT = 10
SEED_REAL = 0x484D0001
HOLDOUT_SCORE_FLOOR = -4.507065492983351


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def faed_sha256() -> str:
    return hashlib.sha256(FAED.encode("ascii")).hexdigest()


def verify_lock() -> dict:
    lock = json.loads(LOCK_PATH.read_text())
    paths = {name: REPO_ROOT / relative for name, relative in lock["paths"].items()}
    if {name: sha256_file(path) for name, path in paths.items()} != lock["files_sha256"]:
        raise RuntimeError("execution lock hash mismatch")
    expected = {
        "width": 7,
        "joint_keep": solver.JOINT_KEEP,
        "board_restarts": solver.BOARD_RESTARTS,
        "board_iters": solver.BOARD_ITERS,
        "board_t0": 20.0,
        "board_t1": 1.0,
        "top_count": TOP_COUNT,
        "seed_real": SEED_REAL,
        "holdout_score_floor": HOLDOUT_SCORE_FLOOR,
    }
    if lock["configuration"] != expected:
        raise RuntimeError("execution lock configuration mismatch")
    if len(FAED) != 570 or faed_sha256() != lock["faed_ascii_sha256"]:
        raise RuntimeError("FAED input mismatch")
    return lock


def run_real() -> dict:
    model = solver.base.SpectralModel.from_training_corpus()
    quad, _ = solver.base.load_language_model()
    ranked = solver.enumerate_joint(FAED, model, keep=solver.JOINT_KEEP)
    geometry = solver.base.Geometry(len(FAED), solver.WIDTH)
    candidates = []
    for spectral_rank, entry in enumerate(ranked["shortlist"], start=1):
        pair_index = entry["pair_index"]
        pair = solver.base.ESCAPE_PAIRS[pair_index]
        codes = solver.base.slot_codes(pair)
        code_to_slot = {code: index for index, code in enumerate(codes)}
        raw = geometry.decrypt(FAED, entry["order"])
        segmented = solver.base.segment_raw(raw, pair)
        if segmented is None:
            continue
        slots = np.array([code_to_slot[code] for code in segmented], dtype=np.int64)
        best_key, best_score = None, -math.inf
        for restart in range(solver.BOARD_RESTARTS):
            rng = solver.base.PCG32(solver.base.derive_seed(
                SEED_REAL, solver.WIDTH, pair_index, *entry["order"], restart,
            ))
            key, score = solver.base.anneal_board(
                slots, quad, rng, solver.BOARD_ITERS, 20.0, 1.0,
            )
            if score > best_score:
                best_key, best_score = key, score
        board = {
            codes[index]: solver.base.LETTER_ALPHABET[int(best_key[index])]
            for index in range(25)
        }
        plaintext = solver.base.decode_raw(raw, pair, board)
        candidates.append({
            "spectral_rank": spectral_rank,
            "pair_index": pair_index,
            "pair": list(pair),
            "order": entry["order"],
            "decoded_length": len(segmented),
            "quadgram_score": best_score,
            "normalized_score": solver.base.normalized_quadgram_score(best_score, len(segmented)),
            "plaintext": plaintext,
            "board": board,
        })
    eligible = [c for c in candidates if c["decoded_length"] >= solver.base.MIN_DECODED_LENGTH]
    eligible.sort(key=lambda c: (-c["normalized_score"], c["pair_index"], c["order"]))
    top = eligible[:TOP_COUNT]
    trigger = top[0]["normalized_score"] >= HOLDOUT_SCORE_FLOOR
    return {
        "phase": "484D",
        "status": "locked_width7_real_complete",
        "faed_ascii_sha256": faed_sha256(),
        "execution_lock_sha256": sha256_file(LOCK_PATH),
        "hypotheses_total": ranked["hypotheses_total"],
        "valid_hypotheses": ranked["valid_hypotheses"],
        "retained_hypotheses": len(ranked["shortlist"]),
        "top": top,
        "family_best": top[0],
        "score_trigger": trigger,
        "disposition": (
            "confirmation_required" if trigger
            else "no_powered_width7_solve_no_calibrated_null_claim"
        ),
    }


def self_test() -> None:
    assert len(FAED) == 570
    assert faed_sha256() == "066191b4aafc114fbca7f0d168382f40129c4ff18490375b689741081d5ef3c2"
    assert solver.HYPOTHESES_TOTAL == 181440
    assert solver.base.Geometry(570, 7).column_lengths == (82, 82, 82, 81, 81, 81, 81)


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
        print("lock verified; pass --run for the one width-7 FAED search")
        return 0
    result = run_real()
    temporary = RESULT_PATH.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(result, indent=2, sort_keys=True))
    temporary.replace(RESULT_PATH)
    best = result["family_best"]
    print("best", best["pair"], best["order"], best["normalized_score"])
    print("plaintext", best["plaintext"])
    print("score_trigger", result["score_trigger"])
    print("disposition", result["disposition"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
