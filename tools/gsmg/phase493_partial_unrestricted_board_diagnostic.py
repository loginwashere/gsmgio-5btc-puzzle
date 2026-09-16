#!/usr/bin/env python3
"""Depth-6/7 unrestricted-board diagnostic on partition-violating fixtures."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path

import numpy as np

import phase484a_raw_symbol_vic_solver as base
import phase484j_constructive_prefix_beam_probe as prefix
import phase484k_bidirectional_segment_assembly_probe as bidi
import phase484q_blind_joint_width19_solver as joint
import phase490_width19_dual_lane_dev as front
import phase491_raw_histogram_fixture as rawonly


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
UNRESTRICTED_BINARY = REPO_ROOT / "_work" / "phase484q" / "coarse_board_server"
CONSTRAINED_BINARY = front.CONSTRAINED_BINARY
DEFAULT_RESULT = SCRIPT_DIR / "phase493_partial_unrestricted_board_result.json"
FIXTURES = tuple(range(5))
SWAP_COUNTS = (1, 2, 3)
DEPTHS = (6, 7)
CONTROLS = 512
RESTARTS = 3
ITERATIONS = 2000
SEED = 0x493A001


def canonical_codes(pair=rawonly.PAIR) -> tuple[str, ...]:
    remaining = tuple(symbol for symbol in base.NINE_SYMBOLS if symbol not in pair)
    symbols = (*pair, *remaining)
    return (*remaining,
            *(escape + suffix for escape in pair for suffix in symbols))


def canonical_board(letter_to_code: dict[str, str]) -> np.ndarray:
    code_to_letter = {code: letter for letter, code in letter_to_code.items()}
    return np.asarray([base.LETTER_ALPHABET.index(code_to_letter[code])
                       for code in canonical_codes()], dtype=np.uint8)


def selected_swaps(fixture: dict, count: int) -> tuple[tuple[str, str], ...]:
    profile = rawonly.sampled_token_profile(fixture["fixture_index"], fixture["split"])
    board = fixture["letter_to_code"]
    singles = [letter for letter, code in board.items() if len(code) == 1]
    doubles = [letter for letter, code in board.items() if len(code) == 2]
    options = sorted(
        (abs(profile["token_counts"][board[left]] -
             profile["token_counts"][board[right]]), left, right)
        for left in singles for right in doubles)
    used, swaps = set(), []
    for _, left, right in options:
        if left not in used and right not in used:
            swaps.append((left, right)); used.update((left, right))
            if len(swaps) == count:
                break
    if len(swaps) != count:
        raise AssertionError("could not select disjoint partition swaps")
    return tuple(swaps)


def make_variant(fixture_index: int, swap_count: int) -> dict:
    original = rawonly.make_fixture(fixture_index, "dev")
    profile = rawonly.sampled_token_profile(fixture_index, "dev")
    swaps = selected_swaps(original, swap_count)
    board = dict(original["letter_to_code"])
    for left, right in swaps:
        board[left], board[right] = board[right], board[left]
    target = {letter: profile["token_counts"][code]
              for letter, code in board.items()}
    quad, _ = base.load_language_model()
    plaintext, edits = rawonly.minimum_edit_plaintext(
        original["source_plaintext"], target, quad)
    raw = base.encode_plaintext(plaintext, board)
    observed = base.Geometry(570, 19).encrypt(raw, original["order"])
    indices = np.asarray([base.LETTER_ALPHABET.index(x) for x in plaintext])
    normalized = base.score_indices(indices, quad) / max(1, len(indices)-3)
    variant = {
        **original,
        "board_mode": "raw_histogram_partition_violation",
        "partition_swap_count": swap_count,
        "partition_swaps": [list(pair) for pair in swaps],
        "letter_to_code": board, "plaintext": plaintext,
        "minimum_edit_count": edits, "edit_fraction": edits/len(plaintext),
        "normalized_quadgram": normalized, "raw": raw, "observed": observed,
        "raw_sha256": hashlib.sha256(raw.encode("ascii")).hexdigest(),
    }
    base.verify_fixture(variant)
    if collections.Counter(raw) != collections.Counter(rawonly.RAW_COUNTS):
        raise AssertionError("variant changed raw histogram")
    if variant["edit_fraction"] > rawonly.MAX_EDIT_FRACTION:
        raise AssertionError("variant exceeds edit gate")
    if normalized < rawonly.MIN_NORMALIZED_QUADGRAM:
        raise AssertionError("variant exceeds language-quality gate")
    return variant


def control_paths(width: int, depth: int, fixture_index: int, swap_count: int,
                  forbidden: set[tuple[int, ...]]) -> np.ndarray:
    rng = base.PCG32(base.derive_seed(SEED, fixture_index, swap_count, depth))
    made = set()
    while len(made) < CONTROLS:
        path = tuple(rng.permutation(width)[:depth])
        if path not in forbidden:
            made.add(path)
    return np.asarray(sorted(made), dtype=np.uint8)


def score_planted(paths, blocks, pair, board, quad) -> np.ndarray:
    scores = []
    for path in paths:
        rows = front.canonical_token_rows(blocks, pair, path)
        windows = sum(max(0, len(row)-3) for row in rows)
        total = sum(base.score_indices(board[row].astype(np.int64), quad)
                    for row in rows if len(row) >= 4)
        scores.append(total/windows if windows else -1e9)
    return np.asarray(scores)


def metrics(scores, boards, true_count: int, planted_board) -> dict:
    true_scores, control_scores = scores[:true_count], scores[true_count:]
    best_true_index = int(np.argmax(true_scores))
    best_true = float(true_scores[best_true_index])
    rank = 1 + int(np.count_nonzero(scores > best_true))
    result = {
        "best_true_rank": rank,
        "best_true_score": best_true,
        "best_control_score": float(np.max(control_scores)),
        "gap": best_true - float(np.max(control_scores)),
    }
    if boards is not None:
        accuracy = np.mean(boards[:true_count] == planted_board, axis=1)
        result["max_true_board_accuracy"] = float(np.max(accuracy))
        result["best_score_true_board_accuracy"] = float(accuracy[best_true_index])
    return result


def multistart(binary, paths, blocks, pair, quad):
    best = np.full(len(paths), -np.inf)
    best_boards = None
    for restart in range(RESTARTS):
        scores, _, boards = joint.gpu_coarse_screen(
            binary, blocks, pair, quad, paths, ITERATIONS,
            base.derive_seed(SEED, restart))
        improved = scores > best
        if best_boards is None:
            best_boards = boards.copy()
        best[improved] = scores[improved]
        best_boards[improved] = boards[improved]
    return best, best_boards


def run_cell(fixture_index: int, swap_count: int, depth: int) -> dict:
    fixture = make_variant(fixture_index, swap_count)
    blocks = prefix.blocks_from_observed(fixture)
    truth = prefix.order_to_sequence(fixture["order"])
    true = np.asarray(sorted(bidi.true_windows(truth, depth)), dtype=np.uint8)
    false = control_paths(19, depth, fixture_index, swap_count,
                          {tuple(path) for path in true})
    paths = np.concatenate((true, false))
    pair = tuple(fixture["pair"])
    quad, _ = base.load_language_model()
    planted_board = canonical_board(fixture["letter_to_code"])
    planted = score_planted(paths, blocks, pair, planted_board, quad)
    constrained_scores, constrained_boards = multistart(
        CONSTRAINED_BINARY, paths, blocks, pair, quad)
    unrestricted_scores, unrestricted_boards = multistart(
        UNRESTRICTED_BINARY, paths, blocks, pair, quad)
    return {
        "fixture_index": fixture_index, "swap_count": swap_count,
        "swaps": fixture["partition_swaps"], "depth": depth,
        "true_count": len(true), "control_count": len(false),
        "plaintext_length": len(fixture["plaintext"]),
        "edit_fraction": fixture["edit_fraction"],
        "normalized_quadgram": fixture["normalized_quadgram"],
        "planted": metrics(planted, None, len(true), planted_board),
        "constrained": metrics(constrained_scores, constrained_boards,
                               len(true), planted_board),
        "unrestricted": metrics(unrestricted_scores, unrestricted_boards,
                                len(true), planted_board),
    }


def run(output: Path = DEFAULT_RESULT) -> dict:
    if output.exists():
        raise FileExistsError("refusing to overwrite diagnostic result")
    records = [run_cell(i, swaps, depth) for i in FIXTURES
               for swaps in SWAP_COUNTS for depth in DEPTHS]
    planted_passes = sum(r["planted"]["best_true_rank"] == 1 for r in records)
    unrestricted_passes = sum(
        r["unrestricted"]["best_true_rank"] <= 5 for r in records)
    result = {
        "phase": 493, "status": "development_diagnostic_complete",
        "faed_scored": False, "holdout_consumed": False,
        "budgets": {"controls": CONTROLS, "restarts": RESTARTS,
                    "iterations": ITERATIONS, "seed": SEED},
        "cell_count": len(records), "planted_rank1": planted_passes,
        "unrestricted_top5": unrestricted_passes,
        "planted_gate_passed": planted_passes >= 24,
        "unrestricted_gate_passed": unrestricted_passes >= 20,
        "records": records,
    }
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(json.dumps(result, indent=2) + "\n")
    temporary.replace(output)
    return result


def self_test() -> dict:
    fixture = make_variant(0, 3)
    board = canonical_board(fixture["letter_to_code"])
    if sorted(board.tolist()) != list(range(25)):
        raise AssertionError("canonical board is not a permutation")
    common, _ = rawonly.training_groups()
    singles = {letter for letter, code in fixture["letter_to_code"].items()
               if len(code) == 1}
    if len(set(common) - singles) != 3:
        raise AssertionError("three-swap fixture has wrong partition distance")
    return {"fixture": 0, "swaps": fixture["partition_swaps"],
            "normalized_quadgram": fixture["normalized_quadgram"],
            "faed_scored": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--run", action="store_true")
    parser.add_argument("--output", type=Path, default=DEFAULT_RESULT)
    args = parser.parse_args()
    result = self_test() if args.self_test else run(args.output)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
