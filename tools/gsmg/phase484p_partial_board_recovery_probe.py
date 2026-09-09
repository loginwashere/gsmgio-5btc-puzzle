#!/usr/bin/env python3
"""Can a genuine width-19 depth-8 segment seed a usable checkerboard?"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

import phase484a_raw_symbol_vic_solver as base
import phase484g_hard_negative_discriminator as learned
import phase484j_constructive_prefix_beam_probe as prefix
import phase484k_bidirectional_segment_assembly_probe as bidi
import phase484o_joint_board_order_ceiling as ceiling

SCRIPT_DIR = Path(__file__).resolve().parent
WIDTH = 19
DEPTH = 8
RESTARTS = 4
ITERATIONS = 10000
T0 = 12.0
T1 = 0.3
RANDOM_CONTROLS = 12
SEED = 0x4840C00


def token_rows(blocks, pair, path):
    codes = base.slot_codes(pair)
    code_to_slot = {code: i for i, code in enumerate(codes)}
    rows = []
    for row in range(len(blocks[0])):
        raw = "".join(blocks[column][row] for column in path)
        segmented = base.segment_raw(raw, pair)
        if segmented is None:
            segmented = base.segment_raw(raw[:-1], pair)
        rows.append(np.asarray([code_to_slot[code] for code in segmented], dtype=np.int64))
    return rows


def row_score(key, rows, quad):
    return sum(base.score_indices(key[row], quad) for row in rows)


def row_windows(rows):
    return sum(max(0, len(row) - 3) for row in rows)


def anneal(rows, quad, rng, iterations=ITERATIONS):
    key = np.asarray(rng.permutation(25), dtype=np.int64)
    current = row_score(key, rows, quad)
    best, best_key = current, key.copy()
    cooling = (T1 / T0) ** (1 / iterations)
    temperature = T0
    for _ in range(iterations):
        i, j = rng.below(25), rng.below(25)
        if i != j:
            key[i], key[j] = key[j], key[i]
            proposed = row_score(key, rows, quad)
            delta = proposed - current
            if delta >= 0 or rng.random() < math.exp(delta / temperature):
                current = proposed
                if proposed > best:
                    best, best_key = proposed, key.copy()
            else:
                key[i], key[j] = key[j], key[i]
        temperature *= cooling
    return best_key, best


def solve_path(fixture, blocks, quad, path, label, index,
               restarts=RESTARTS, iterations=ITERATIONS):
    pair = tuple(fixture["pair"])
    rows = token_rows(blocks, pair, path)
    best_key, best_score = None, -math.inf
    for restart in range(restarts):
        rng = base.PCG32(base.derive_seed(SEED, index, restart))
        key, score = anneal(rows, quad, rng, iterations)
        if score > best_score:
            best_key, best_score = key, score
    truth = np.frombuffer(ceiling.planted_board(fixture), dtype=np.uint8)
    return {
        "label": label,
        "path": list(path),
        "quadgram_windows": row_windows(rows),
        "normalized_score": best_score / max(1, row_windows(rows)),
        "board_accuracy": float(np.mean(best_key == truth)),
        "board": best_key.tolist(),
    }


def run(mode="vic_profile", fixture_index=23, restarts=RESTARTS,
        iterations=ITERATIONS, random_controls=RANDOM_CONTROLS):
    fixture = base.make_fixture(WIDTH, learned.PAIR_INDEX, fixture_index,
        seed=learned.SEED, board_mode=mode, split="dev")
    blocks = prefix.blocks_from_observed(fixture)
    truth = prefix.order_to_sequence(fixture["order"])
    quad, _ = base.load_language_model()
    true_paths = sorted(bidi.true_windows(truth, DEPTH))
    rng = base.PCG32(base.derive_seed(SEED, fixture_index, 999))
    random_paths = set()
    while len(random_paths) < random_controls:
        path = tuple(rng.permutation(WIDTH)[:DEPTH])
        if path not in true_paths:
            random_paths.add(path)
    records = []
    for index, path in enumerate(true_paths):
        records.append(solve_path(fixture, blocks, quad, path, "true", index,
                                  restarts, iterations))
    for offset, path in enumerate(sorted(random_paths), start=len(true_paths)):
        records.append(solve_path(fixture, blocks, quad, path, "random", offset,
                                  restarts, iterations))
    true_records = [r for r in records if r["label"] == "true"]
    random_records = [r for r in records if r["label"] == "random"]
    return {
        "phase": "484P",
        "status": "development_partial_board_recovery_not_frozen",
        "faed_scored": False,
        "holdout_consumed": False,
        "board_mode": mode,
        "fixture_index": fixture_index,
        "depth": DEPTH,
        "budgets": {"restarts": restarts, "iterations": iterations,
                    "t0": T0, "t1": T1,
                    "random_controls": random_controls},
        "true_max_board_accuracy": max(r["board_accuracy"] for r in true_records),
        "true_max_normalized_score": max(r["normalized_score"] for r in true_records),
        "random_max_normalized_score": max(r["normalized_score"] for r in random_records),
        "records": records,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--mode", choices=base.BOARD_MODES, default="vic_profile")
    parser.add_argument("--fixture-index", type=int, default=23)
    parser.add_argument("--restarts", type=int, default=RESTARTS)
    parser.add_argument("--iterations", type=int, default=ITERATIONS)
    parser.add_argument("--random-controls", type=int, default=RANDOM_CONTROLS)
    args = parser.parse_args()
    if not args.run: parser.error("use --run")
    result = run(args.mode, args.fixture_index, args.restarts, args.iterations,
                 args.random_controls)
    output = SCRIPT_DIR / (f"phase484p_partial_board_{args.mode}_i{args.fixture_index}_"
                           f"r{args.restarts}_n{args.iterations}_"
                           f"c{args.random_controls}.json")
    output.write_text(json.dumps(result, indent=2) + "\n")
    print("true board accuracy", result["true_max_board_accuracy"],
          "true score", result["true_max_normalized_score"],
          "random score", result["random_max_normalized_score"])
    print("wrote", output)
    return 0


if __name__ == "__main__": raise SystemExit(main())
