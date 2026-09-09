#!/usr/bin/env python3
"""Planted-board signal map for exact-profile width-30 fragments.

Development diagnostic only.  The true board is an oracle used to establish
whether an order objective exists at depths 8, 10, and 13.  FAED is never
imported or scored.
"""
from __future__ import annotations

import argparse
import json
import struct
import subprocess
import time
from pathlib import Path

import numpy as np

import phase484a_raw_symbol_vic_solver as base
import phase484j_constructive_prefix_beam_probe as prefix
import phase484k_bidirectional_segment_assembly_probe as bidi
import phase484n_hybrid_prefix_scorer as gpu19
import phase484o_joint_board_order_ceiling as ceiling
import phase484x_exact_faed_profile_power_probe as exact
import phase484y_width30_feasibility_probe as width30

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_BINARY = SCRIPT_DIR.parents[1] / "_work/phase484y/board_server"
MAGIC = b"P484YB1\0"
DEPTHS = (8, 10, 13)
RANDOM_CONTROLS = 50000
SEED = 0x484A0C0


class BoardScorer:
    def __init__(self, binary, blocks, pair, board, quad):
        self.process = subprocess.Popen(
            [str(binary)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        self.process.stdin.write(MAGIC)
        self.process.stdin.write(width30.canonical_blocks(blocks, pair))
        self.process.stdin.write(bytes(board))
        self.process.stdin.write(np.asarray(quad, dtype="<f8").tobytes())
        self.process.stdin.flush()

    def score(self, paths):
        paths = np.ascontiguousarray(paths, dtype=np.uint8)
        if paths.ndim != 2 or not 4 <= paths.shape[1] <= width30.WIDTH:
            raise ValueError("paths must have depth 4..30")
        self.process.stdin.write(struct.pack("<II", len(paths), paths.shape[1]))
        self.process.stdin.write(paths.tobytes())
        self.process.stdin.flush()
        data = gpu19.read_exact(self.process.stdout, len(paths) * 8)
        if len(data) != len(paths) * 8:
            error = self.process.stderr.read().decode("utf-8", "replace")
            raise RuntimeError(f"board scorer stopped early: {error}")
        return np.frombuffer(data, dtype="<f8").copy()

    def close(self):
        if self.process.poll() is None:
            self.process.stdin.write(struct.pack("<II", 0, 0))
            self.process.stdin.flush()
            self.process.stdin.close()
            return_code = self.process.wait(timeout=10)
            if return_code:
                error = self.process.stderr.read().decode("utf-8", "replace")
                raise RuntimeError(f"board scorer exited {return_code}: {error}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.close()


def cpu_board_score(blocks, pair, board, quad, path):
    code_to_slot = {code: index for index, code in
                    enumerate(base.slot_codes(pair))}
    total, windows = 0.0, 0
    for row in range(len(blocks[0])):
        raw = "".join(blocks[column][row] for column in path)
        segmented = base.segment_raw(raw, pair)
        if segmented is None:
            segmented = base.segment_raw(raw[:-1], pair)
        letters = np.asarray(
            [board[code_to_slot[code]] for code in segmented],
            dtype=np.int64)
        if len(letters) >= 4:
            total += base.score_indices(letters, quad)
            windows += len(letters) - 3
    return total / windows if windows else -1e9


def random_paths(depth, count, forbidden, seed):
    rng = base.PCG32(seed)
    records = set()
    while len(records) < count:
        path = tuple(rng.permutation(width30.WIDTH)[:depth])
        if path not in forbidden:
            records.add(path)
    return np.asarray(sorted(records), dtype=np.uint8)


def one_column_corruptions(true_paths, depth):
    records = set()
    for path in true_paths:
        used = set(path)
        for position in range(depth):
            for replacement in range(width30.WIDTH):
                if replacement not in used:
                    changed = list(path)
                    changed[position] = replacement
                    records.add(tuple(changed))
    return np.asarray(sorted(records), dtype=np.uint8)


def summarize(true_scores, control_scores):
    best = float(np.max(true_scores))
    return {
        "true_count": len(true_scores),
        "true_min": float(np.min(true_scores)),
        "true_median": float(np.median(true_scores)),
        "true_max": best,
        "control_count": len(control_scores),
        "control_max": float(np.max(control_scores)),
        "controls_at_or_above_best_true": int(np.count_nonzero(
            control_scores >= best)),
        "true_above_all_controls": int(np.count_nonzero(
            true_scores > np.max(control_scores))),
        "best_true_rank_pooled": 1 + int(np.count_nonzero(
            control_scores > best)),
    }


def run_fixture(fixture_index, depths=DEPTHS,
                random_controls=RANDOM_CONTROLS,
                binary=DEFAULT_BINARY):
    fixture = width30.width30_fixture(fixture_index)
    blocks = prefix.blocks_from_observed(fixture)
    truth = prefix.order_to_sequence(fixture["order"])
    board = ceiling.planted_board(fixture)
    quad, _ = base.load_language_model()
    records = []
    began = time.monotonic()
    with BoardScorer(binary, blocks, exact.PAIR, board, quad) as scorer:
        for depth in depths:
            true_paths_set = bidi.true_windows(truth, depth)
            true_paths = np.asarray(sorted(true_paths_set), dtype=np.uint8)
            random = random_paths(
                depth, random_controls, true_paths_set,
                base.derive_seed(SEED, fixture_index, depth))
            corruptions = one_column_corruptions(true_paths_set, depth)
            true_scores = scorer.score(true_paths)
            random_scores = scorer.score(random)
            corruption_scores = scorer.score(corruptions)
            records.append({
                "depth": depth,
                "raw_symbols_per_fragment": depth * width30.ROWS,
                "random": summarize(true_scores, random_scores),
                "one_column_corruption": summarize(
                    true_scores, corruption_scores),
            })
    return {
        "phase": "484Y",
        "status": "development_width30_planted_board_ceiling_not_frozen",
        "faed_scored": False,
        "holdout_consumed": False,
        "fixture_index": fixture_index,
        "width": width30.WIDTH,
        "rows": width30.ROWS,
        "depths": list(depths),
        "random_controls_per_depth": random_controls,
        "records": records,
        "wall_seconds": time.monotonic() - began,
    }


def run_batch(indices, depths=DEPTHS, random_controls=RANDOM_CONTROLS,
              binary=DEFAULT_BINARY):
    began = time.monotonic()
    records = [run_fixture(index, depths, random_controls, binary)
               for index in indices]
    aggregate = []
    for depth in depths:
        cells = [next(item for item in record["records"]
                      if item["depth"] == depth) for record in records]
        aggregate.append({
            "depth": depth,
            "fixtures": len(cells),
            "best_true_beats_all_random": sum(
                cell["random"]["controls_at_or_above_best_true"] == 0
                for cell in cells),
            "best_true_beats_all_one_column_corruptions": sum(
                cell["one_column_corruption"][
                    "controls_at_or_above_best_true"] == 0 for cell in cells),
            "median_best_true_random_rank": float(np.median([
                cell["random"]["best_true_rank_pooled"] for cell in cells])),
            "median_best_true_corruption_rank": float(np.median([
                cell["one_column_corruption"]["best_true_rank_pooled"]
                for cell in cells])),
        })
    return {
        "phase": "484Y",
        "status": "development_width30_planted_board_ceiling_batch_not_frozen",
        "faed_scored": False,
        "holdout_consumed": False,
        "indices": list(indices),
        "depths": list(depths),
        "random_controls_per_depth": random_controls,
        "aggregate": aggregate,
        "records": records,
        "wall_seconds": time.monotonic() - began,
    }


def gpu_parity(binary=DEFAULT_BINARY):
    fixture = width30.width30_fixture(13)
    blocks = prefix.blocks_from_observed(fixture)
    board = ceiling.planted_board(fixture)
    quad, _ = base.load_language_model()
    paths = np.asarray(sorted(bidi.true_windows(
        prefix.order_to_sequence(fixture["order"]), 8))[:8], dtype=np.uint8)
    expected = np.asarray([cpu_board_score(
        blocks, exact.PAIR, board, quad, path) for path in paths])
    with BoardScorer(binary, blocks, exact.PAIR, board, quad) as scorer:
        actual = scorer.score(paths)
    error = float(np.max(np.abs(expected - actual)))
    if error > 1e-10:
        raise AssertionError(f"CPU/GPU board score mismatch: {error}")
    return {"paths": len(paths), "max_abs_error": error}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--batch", nargs="+", type=int)
    parser.add_argument("--fixture-index", type=int, default=13)
    parser.add_argument("--random-controls", type=int,
                        default=RANDOM_CONTROLS)
    parser.add_argument("--binary", type=Path, default=DEFAULT_BINARY)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(gpu_parity(args.binary), indent=2))
        return 0
    if args.batch:
        result = run_batch(args.batch, random_controls=args.random_controls,
                           binary=args.binary)
        output = args.output or SCRIPT_DIR / "phase484y_width30_ceiling_batch.json"
    elif args.run:
        result = run_fixture(args.fixture_index,
                             random_controls=args.random_controls,
                             binary=args.binary)
        output = args.output or SCRIPT_DIR / (
            f"phase484y_width30_ceiling_i{args.fixture_index}.json")
    else:
        parser.error("use --self-test, --run, or --batch")
    output.write_text(json.dumps(result, indent=2) + "\n")
    if "aggregate" in result:
        for record in result["aggregate"]:
            print(record)
    else:
        for record in result["records"]:
            print(record)
    print("wrote", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
