#!/usr/bin/env python3
"""Planted-board upper bound for width-19 order assembly."""

from __future__ import annotations

import argparse
import itertools
import json
import struct
import subprocess
import time
from pathlib import Path

import numpy as np

import phase484a_raw_symbol_vic_solver as base
import phase484g_hard_negative_discriminator as learned
import phase484j_constructive_prefix_beam_probe as prefix
import phase484k_bidirectional_segment_assembly_probe as bidi
import phase484n_gpu_width19_beam_probe as gpu_beam
from phase484n_hybrid_prefix_scorer import canonical_blocks, read_exact, DEFAULT_BINARY

SCRIPT_DIR = Path(__file__).resolve().parent
BOARD_BINARY = SCRIPT_DIR.parents[1] / "_work/phase484o/board_server"
WIDTH = 19
SWITCH_DEPTH = 8
DEFAULT_BEAM = 65536
PERTURB_SEED = 0x4840B00


def planted_board(fixture) -> bytes:
    letter_index = {letter: i for i, letter in enumerate(base.LETTER_ALPHABET)}
    code_to_letter = {code: letter for letter, code in fixture["letter_to_code"].items()}
    return bytes(letter_index[code_to_letter[code]]
                 for code in base.slot_codes(tuple(fixture["pair"])))


def perturb_board(board: bytes, swap_count: int, fixture_index: int) -> bytes:
    if not 0 <= swap_count <= 12:
        raise ValueError("swap count must be in 0..12")
    values = list(board)
    slots = list(range(25))
    rng = base.PCG32(base.derive_seed(PERTURB_SEED, fixture_index, swap_count))
    rng.shuffle(slots)
    for index in range(swap_count):
        left, right = slots[2 * index:2 * index + 2]
        values[left], values[right] = values[right], values[left]
    return bytes(values)


def cpu_board_score(blocks, pair, board, quad, path):
    codes = base.slot_codes(pair)
    code_to_slot = {code: i for i, code in enumerate(codes)}
    total, windows = 0.0, 0
    for row in range(30):
        raw = "".join(blocks[column][row] for column in path)
        segmented = base.segment_raw(raw, pair)
        if segmented is None:
            # Only a terminal escape is incomplete; score the complete prefix.
            segmented = base.segment_raw(raw[:-1], pair)
        letters = np.asarray([board[code_to_slot[code]] for code in segmented], dtype=np.int64)
        if len(letters) >= 4:
            total += base.score_indices(letters, quad)
            windows += len(letters) - 3
    return total / windows if windows else -1e9


class BoardScorer:
    def __init__(self, binary, blocks, pair, board, quad):
        self.process = subprocess.Popen(
            [str(binary)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.process.stdin.write(b"P484OG1\0")
        self.process.stdin.write(canonical_blocks(blocks, pair))
        self.process.stdin.write(bytes(board))
        self.process.stdin.write(np.asarray(quad, dtype="<f8").tobytes())
        self.process.stdin.flush()

    def score(self, paths):
        paths = np.asarray(paths, dtype=np.uint8)
        self.process.stdin.write(struct.pack("<II", len(paths), paths.shape[1]))
        self.process.stdin.write(np.ascontiguousarray(paths).tobytes())
        self.process.stdin.flush()
        data = read_exact(self.process.stdout, len(paths) * 8)
        if len(data) != len(paths) * 8:
            raise RuntimeError(self.process.stderr.read().decode("utf-8", "replace"))
        return np.frombuffer(data, dtype="<f8").copy()

    def close(self):
        if self.process.poll() is None:
            self.process.stdin.write(struct.pack("<II", 0, 0))
            self.process.stdin.flush(); self.process.stdin.close()
            if self.process.wait(timeout=10):
                raise RuntimeError(self.process.stderr.read().decode("utf-8", "replace"))

    def __enter__(self): return self
    def __exit__(self, *args): self.close()


def search(fixture, models, quad, invariant_binary, board_binary, beam_width,
           board_override=None):
    blocks = prefix.blocks_from_observed(fixture)
    pair = tuple(fixture["pair"])
    truth = prefix.order_to_sequence(fixture["order"])
    board = board_override if board_override is not None else planted_board(fixture)
    diagnostics = []
    paths = list(itertools.permutations(range(WIDTH), prefix.START_DEPTH))
    began = time.monotonic()
    for depth in range(prefix.START_DEPTH, SWITCH_DEPTH + 1):
        if depth > prefix.START_DEPTH:
            paths = gpu_beam.expand_bidirectional(beam, WIDTH)
        scores = gpu_beam.score_paths(
            invariant_binary, blocks, pair, models[depth], paths
        )
        beam = gpu_beam.select_diverse_arrays(paths, scores, WIDTH, beam_width)
        diagnostics.append(diagnostic(depth, beam, truth, "board_invariant"))
    with BoardScorer(board_binary, blocks, pair, board, quad) as scorer:
        for depth in range(SWITCH_DEPTH + 1, WIDTH + 1):
            paths = gpu_beam.expand_bidirectional(beam, WIDTH)
            scores = scorer.score(paths)
            beam = gpu_beam.select_diverse_arrays(paths, scores, WIDTH, beam_width)
            record = diagnostic(depth, beam, truth, "planted_board_quadgram")
            diagnostics.append(record)
            if not record["true_segment_count_retained"]:
                break
    truth_tuple = tuple(truth)
    truth_rank = next((i for i, (_, path) in enumerate(beam, 1)
                       if path == truth_tuple), None)
    return {
        "exact_top1_recovery": diagnostics[-1]["depth"] == WIDTH and beam[0][1] == truth_tuple,
        "truth_full_rank": truth_rank,
        "depth_diagnostics": diagnostics,
        "wall_seconds": time.monotonic() - began,
    }


def diagnostic(depth, beam, truth, statistic):
    genuine = bidi.true_windows(truth, depth)
    ranks = [rank for rank, (_, path) in enumerate(beam, 1) if path in genuine]
    return {"depth": depth, "statistic": statistic,
            "true_segment_count_retained": len(ranks),
            "best_true_segment_rank": min(ranks) if ranks else None}


def run(mode, fixture_index, beam_width, invariant_binary, board_binary,
        board_swaps=0):
    models = prefix.train_models(WIDTH)
    quad, _ = base.load_language_model()
    fixture = base.make_fixture(WIDTH, learned.PAIR_INDEX, fixture_index,
        seed=learned.SEED, board_mode=mode, split="dev")
    truth_board = planted_board(fixture)
    supplied_board = perturb_board(truth_board, board_swaps, fixture_index)
    return {"phase": "484O", "status": "development_planted_board_ceiling_not_frozen",
            "faed_scored": False, "holdout_consumed": False,
            "board_mode": mode, "fixture_index": fixture_index,
            "beam_width": beam_width, "board_swaps": board_swaps,
            "board_accuracy": sum(a == b for a, b in zip(truth_board, supplied_board)) / 25,
            **search(fixture, models, quad, invariant_binary, board_binary,
                     beam_width, supplied_board)}


def self_test(board_binary):
    fixture = base.make_fixture(WIDTH, 0, 23, seed=learned.SEED,
        board_mode="vic_profile", split="dev")
    blocks = prefix.blocks_from_observed(fixture); pair = tuple(fixture["pair"])
    board = planted_board(fixture); quad, _ = base.load_language_model()
    paths = np.asarray(list(itertools.islice(itertools.permutations(range(WIDTH), 8), 64)))
    expected = np.asarray([cpu_board_score(blocks, pair, board, quad, p) for p in paths])
    with BoardScorer(board_binary, blocks, pair, board, quad) as scorer:
        actual = scorer.score(paths)
    error = float(np.max(np.abs(expected - actual)))
    if error > 1e-10: raise AssertionError(error)
    return {"paths": len(paths), "max_abs_error": error}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--mode", choices=base.BOARD_MODES, default="vic_profile")
    parser.add_argument("--fixture-index", type=int, default=23)
    parser.add_argument("--beam", type=int, default=DEFAULT_BEAM)
    parser.add_argument("--board-swaps", type=int, default=0)
    parser.add_argument("--invariant-binary", type=Path, default=DEFAULT_BINARY)
    parser.add_argument("--board-binary", type=Path, default=BOARD_BINARY)
    args = parser.parse_args()
    if args.self_test:
        print(self_test(args.board_binary)); return 0
    if not args.run: parser.error("use --self-test or --run")
    result = run(args.mode, args.fixture_index, args.beam,
                 args.invariant_binary, args.board_binary, args.board_swaps)
    output = SCRIPT_DIR / (f"phase484o_ceiling_{args.mode}_i{args.fixture_index}_"
                           f"b{args.beam}_s{args.board_swaps}.json")
    output.write_text(json.dumps(result, indent=2) + "\n")
    print("exact", result["exact_top1_recovery"], "rank", result["truth_full_rank"],
          "wall", round(result["wall_seconds"], 3))
    for r in result["depth_diagnostics"]:
        print(r["depth"], r["statistic"], r["true_segment_count_retained"], r["best_true_segment_rank"])
    print("wrote", output); return 0


if __name__ == "__main__": raise SystemExit(main())
