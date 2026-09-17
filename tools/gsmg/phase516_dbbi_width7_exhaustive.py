#!/usr/bin/env python3
"""Phase 516 -- exhaustive-order transposition search applied to DBBI's own
raw stream at width 7 (91 = 7 x 13, DBBI's only nontrivial rectangular
factorization). Development pass for
`doc/Brainstorms/2026-09-16 - Phase 516 DBBI Unrestricted-Order Transposition
Scoping.md`.

Two-stage architecture, chosen after a real self-test failure exposed the
naive single-stage design as under-annealed:

  Stage 1 (cheap): every one of the 7! = 5,040 orders is scored once with a
  cheap board anneal (`CHEAP_ITERS`/`CHEAP_RESTARTS`). A direct diagnostic on
  a synthetic width-7/length-91 fixture found the TRUE order ranked #5 of
  3,840 valid candidates under this cheap pass -- comfortably inside a
  generous shortlist.
  Stage 2 (expensive): only the top `SHORTLIST_KEEP` orders by stage-1 score
  are re-annealed with a much heavier budget (`REFINE_ITERS`/
  `REFINE_RESTARTS`), which a direct diagnostic showed is what it actually
  takes for the true order to reliably outscore a strong false competitor at
  DBBI's short (~56-90 letter) decoded-plaintext regime -- this project's own
  FAED solver hit the same under-annealing failure mode at a much larger
  scale (Phase 500).

This two-stage design is why a naive "anneal every order heavily" plan
(estimated at ~12 CPU-hours per pair) was abandoned in favor of this
architecture (~15-20 minutes total across all 36 pairs at 16-way
parallelism), not because full-exhaustive-heavy annealing was proven
infeasible in principle.

Width 13 (91/13 = 7 rows; `13! ~= 6.2e9` orders) is NOT attempted here --
even the cheap stage-1 pass would cost ~100 CPU-days at this scale. It needs
a genuinely different (CSP/pruned or spectral-shortlist) order search, not
brute enumeration; left for a follow-up phase.

Modes:
  --self-test   synthetic plant/recovery check (known plaintext, known
                order, known board)
  --calibrate N run N shuffled-DBBI-multiset null trials, full 36-pair
                width-7 two-stage sweep each
  --run         the real, locked DBBI width-7 sweep (writes an execution
                lock first, pinning DBBI's SHA-256 and every search
                parameter, so nothing can be tuned after seeing real output)
  --verify-lock re-check a previously written lock against current inputs
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import multiprocessing as mp
import time
from pathlib import Path

import numpy as np

from data import DBBI
from phase484a_raw_symbol_vic_solver import (
    PCG32,
    Geometry,
    LETTER_ALPHABET,
    NINE_SYMBOLS,
    anneal_board,
    corpus_splits,
    corpus_word_starts,
    decode_raw,
    derive_seed,
    encode_plaintext,
    exact_length_passage,
    load_language_model,
    normalized_quadgram_score,
    segment_raw,
    slot_codes,
)

SCRIPT_DIR = Path(__file__).resolve().parent
DBBI_SHA256 = hashlib.sha256(DBBI.encode("ascii")).hexdigest()

WIDTH = 7
LENGTH = len(DBBI)
assert LENGTH == 91 and LENGTH % WIDTH == 0, "DBBI length/width assumption changed"

ALL_PAIRS = tuple(itertools.combinations(NINE_SYMBOLS, 2))
assert len(ALL_PAIRS) == 36

# Stage 1: cheap score for every valid order.
CHEAP_ITERS = 6000
CHEAP_RESTARTS = 2
# Stage 2: expensive re-score of the top SHORTLIST_KEEP stage-1 orders.
# Chosen with a 20x safety margin over the observed true-order rank (5 of
# 3,840 valid candidates in the calibration diagnostic).
SHORTLIST_KEEP = 100
REFINE_ITERS = 60000
REFINE_RESTARTS = 30
BOARD_T0, BOARD_T1 = 20.0, 0.3

NULL_TRIALS = 3
SEED_BASE = 0x51600DE

LOCK_PATH = SCRIPT_DIR / "phase516_execution_lock.json"
RESULT_PATH = SCRIPT_DIR / "phase516_width7_result.json"
NULL_PATH = SCRIPT_DIR / "phase516_width7_null.json"

_QUAD_CACHE: np.ndarray | None = None


def quad_table() -> np.ndarray:
    global _QUAD_CACHE
    if _QUAD_CACHE is None:
        _QUAD_CACHE, _ = load_language_model()
    return _QUAD_CACHE


def all_orders(width: int = WIDTH) -> list[tuple[int, ...]]:
    return list(itertools.permutations(range(width)))


def _anneal_best(token_slots: np.ndarray, quad: np.ndarray, seed_parts: tuple, iters: int, restarts: int):
    best_score, best_key = -np.inf, None
    for restart in range(restarts):
        seed = derive_seed(SEED_BASE, *seed_parts, restart)
        key, score = anneal_board(token_slots, quad, PCG32(seed), iters, BOARD_T0, BOARD_T1)
        if score > best_score:
            best_score, best_key = score, key
    return best_score, best_key


def search_pair(observed: str, pair: tuple[str, str]) -> dict | None:
    """Two-stage exhaustive-order search for one escape pair at WIDTH."""
    quad = quad_table()
    geometry = Geometry(len(observed), WIDTH)
    codes = slot_codes(pair)
    code_to_slot = {code: index for index, code in enumerate(codes)}

    stage1 = []
    for order in all_orders():
        raw = geometry.decrypt(observed, order)
        tokens = segment_raw(raw, pair)
        if tokens is None:
            continue
        token_slots = np.array([code_to_slot[code] for code in tokens], dtype=np.int64)
        score, _ = _anneal_best(token_slots, quad, (ord(pair[0]), ord(pair[1]), *order, 1), CHEAP_ITERS, CHEAP_RESTARTS)
        stage1.append((normalized_quadgram_score(score, len(tokens)), order, token_slots, len(tokens)))
    if not stage1:
        return None

    stage1.sort(key=lambda item: item[0], reverse=True)
    shortlist = stage1[:SHORTLIST_KEEP]

    best = None
    for _, order, token_slots, token_count in shortlist:
        score, key = _anneal_best(token_slots, quad, (ord(pair[0]), ord(pair[1]), *order, 2), REFINE_ITERS, REFINE_RESTARTS)
        normalized = normalized_quadgram_score(score, token_count)
        if best is None or normalized > best["normalized_score"]:
            code_to_letter = {codes[slot]: LETTER_ALPHABET[int(key[slot])] for slot in range(25)}
            raw = geometry.decrypt(observed, order)
            decoded = decode_raw(raw, pair, code_to_letter)
            best = {
                "pair": list(pair),
                "order": list(order),
                "normalized_score": normalized,
                "quadgram_score": float(score),
                "token_count": token_count,
                "decoded": decoded,
                "stage1_rank": [o for _, o, *_ in stage1].index(order),
                "stage1_candidates": len(stage1),
            }
    return best


def _pair_worker(args: tuple[str, tuple[str, str]]) -> tuple[tuple[str, str], dict | None]:
    observed, pair = args
    return pair, search_pair(observed, pair)


def _load_checkpoint(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _write_checkpoint(path: Path, per_pair: dict) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(per_pair, indent=2), encoding="utf-8")
    tmp.replace(path)


def full_sweep(observed: str, pairs: tuple = ALL_PAIRS, workers: int = 16,
               checkpoint_path: Path | None = None) -> dict:
    """Embarrassingly-parallel per-pair sweep. If checkpoint_path is given,
    already-completed pairs (from a prior, possibly interrupted run against
    the exact same `observed` string) are skipped, and each newly-completed
    pair is written to disk immediately -- so a kill/shutdown mid-sweep loses
    at most the in-flight pairs, not the whole sweep. Re-running the same
    command resumes automatically."""
    quad_table()  # warm cache in parent before fork
    per_pair: dict = {}
    if checkpoint_path is not None:
        saved = _load_checkpoint(checkpoint_path)
        if saved.get("observed_sha256") == hashlib.sha256(observed.encode("ascii")).hexdigest():
            per_pair = saved.get("per_pair", {})

    remaining = [pair for pair in pairs if "".join(pair) not in per_pair]
    print(f"resuming: {len(per_pair)} pairs already done, {len(remaining)} remaining", flush=True)
    tasks = [(observed, pair) for pair in remaining]

    if tasks:
        with mp.Pool(workers) as pool:
            for pair, result in pool.imap_unordered(_pair_worker, tasks):
                if result is not None:
                    per_pair["".join(pair)] = result
                if checkpoint_path is not None:
                    _write_checkpoint(checkpoint_path, {
                        "observed_sha256": hashlib.sha256(observed.encode("ascii")).hexdigest(),
                        "per_pair": per_pair,
                    })
                done = len(per_pair)
                print(f"pair {''.join(pair)} done ({done}/{len(pairs)} total)", flush=True)

    if not per_pair:
        return {"per_pair": {}, "winner": None}
    winner_pair, winner = max(per_pair.items(), key=lambda kv: kv[1]["normalized_score"])
    return {"per_pair": per_pair, "winner_pair": winner_pair, "winner": winner}


def build_self_test_fixture(seed_tag: int, pair: tuple[str, str] = ("b", "e")):
    rng = PCG32(derive_seed(SEED_BASE, seed_tag))
    codes = slot_codes(pair)
    letters = list(LETTER_ALPHABET)
    rng.shuffle(letters)
    letter_to_code = dict(zip(letters, codes))

    dev_source = corpus_splits()["dev"]
    starts = [s for s in corpus_word_starts("dev") if s <= len(dev_source) - LENGTH]
    rng.shuffle(starts)
    plaintext = None
    for start in starts:
        candidate = exact_length_passage(dev_source, start, letter_to_code, target=LENGTH)
        if candidate is not None:
            plaintext = candidate
            break
    if plaintext is None:
        raise RuntimeError("could not build an exact-91 self-test fixture")

    raw = encode_plaintext(plaintext, letter_to_code)
    order = tuple(rng.permutation(WIDTH))
    observed = Geometry(LENGTH, WIDTH).encrypt(raw, order)
    return pair, plaintext, order, observed


def self_test(trials: int = 1) -> dict:
    outcomes = []
    for trial in range(trials):
        pair, plaintext, order, observed = build_self_test_fixture(0xDEADBEEF ^ trial)
        result = search_pair(observed, pair)
        order_ok = result is not None and tuple(result["order"]) == order
        decoded = result["decoded"] if result else None
        char_accuracy = (
            sum(a == b for a, b in zip(decoded, plaintext)) / len(plaintext)
            if decoded is not None else 0.0
        )
        outcomes.append({
            "order_ok": order_ok,
            "char_accuracy": char_accuracy,
            "pair": list(pair),
            "planted_order": list(order),
            "recovered_order": result["order"] if result else None,
            "planted_plaintext": plaintext,
            "recovered_plaintext": decoded,
            "stage1_rank": result["stage1_rank"] if result else None,
        })
    # Order recovery is the thing this phase actually tests; exact board
    # recovery on ~55-90 letter plaintexts is a known-hard secondary problem
    # in classical substitution cryptanalysis, not evidence the order search
    # failed. Report both, gate self-test pass/fail on order recovery only.
    return {
        "trials": outcomes,
        "all_orders_ok": all(o["order_ok"] for o in outcomes),
        "mean_char_accuracy": sum(o["char_accuracy"] for o in outcomes) / len(outcomes),
    }


def null_trial(trial_index: int) -> dict:
    rng = PCG32(derive_seed(SEED_BASE, 0x50171 ^ trial_index))
    symbols = list(DBBI)
    rng.shuffle(symbols)
    shuffled = "".join(symbols)
    checkpoint = SCRIPT_DIR / f"phase516_width7_null{trial_index}_checkpoint.json"
    sweep = full_sweep(shuffled, checkpoint_path=checkpoint)
    return {
        "trial": trial_index,
        "shuffled_sha256": hashlib.sha256(shuffled.encode("ascii")).hexdigest(),
        "winner_pair": sweep.get("winner_pair"),
        "best_normalized_score": sweep["winner"]["normalized_score"] if sweep.get("winner") else None,
        "winner_decoded": sweep["winner"]["decoded"] if sweep.get("winner") else None,
    }


def lock_payload() -> dict:
    return {
        "phase": 516,
        "dbbi_sha256": DBBI_SHA256,
        "dbbi_length": LENGTH,
        "width": WIDTH,
        "pairs": ["".join(p) for p in ALL_PAIRS],
        "cheap_iters": CHEAP_ITERS,
        "cheap_restarts": CHEAP_RESTARTS,
        "shortlist_keep": SHORTLIST_KEEP,
        "refine_iters": REFINE_ITERS,
        "refine_restarts": REFINE_RESTARTS,
        "board_t0": BOARD_T0,
        "board_t1": BOARD_T1,
        "null_trials": NULL_TRIALS,
        "seed_base": SEED_BASE,
    }


def write_lock() -> None:
    LOCK_PATH.write_text(json.dumps(lock_payload(), indent=2, sort_keys=True), encoding="utf-8")


def verify_lock() -> bool:
    if not LOCK_PATH.exists():
        return False
    return json.loads(LOCK_PATH.read_text(encoding="utf-8")) == lock_payload()


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", type=int, nargs="?", const=1, metavar="TRIALS")
    group.add_argument("--calibrate", type=int, metavar="N")
    group.add_argument("--run", action="store_true")
    group.add_argument("--verify-lock", action="store_true")
    parser.add_argument("--workers", type=int, default=16)
    args = parser.parse_args()

    if args.self_test is not None:
        result = self_test(args.self_test)
        print(json.dumps(result, indent=2))
        return 0 if result["all_orders_ok"] else 1

    if args.verify_lock:
        ok = verify_lock()
        print("lock consistent" if ok else "lock MISSING or INCONSISTENT")
        return 0 if ok else 1

    if args.calibrate is not None:
        if not verify_lock():
            write_lock()
        trials = []
        for i in range(args.calibrate):
            t0 = time.time()
            trials.append(null_trial(i))
            trials[-1]["elapsed_seconds"] = time.time() - t0
            print(json.dumps(trials[-1]))
        NULL_PATH.write_text(json.dumps({"trials": trials}, indent=2), encoding="utf-8")
        return 0

    if args.run:
        write_lock()
        t0 = time.time()
        checkpoint = SCRIPT_DIR / "phase516_width7_real_checkpoint.json"
        sweep = full_sweep(DBBI, workers=args.workers, checkpoint_path=checkpoint)
        elapsed = time.time() - t0
        payload = {
            "phase": 516,
            "status": "real_dbbi_width7_two_stage_complete",
            "elapsed_seconds": elapsed,
            "dbbi_sha256": DBBI_SHA256,
            "lock": lock_payload(),
            **sweep,
        }
        RESULT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(json.dumps({"winner_pair": sweep.get("winner_pair"),
                          "winner": sweep.get("winner"),
                          "elapsed_seconds": elapsed}, indent=2))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
