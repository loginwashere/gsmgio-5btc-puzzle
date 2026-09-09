#!/usr/bin/env python3
"""Synthetic constructive column-prefix beam search for Phase 484 Model B."""

from __future__ import annotations

import heapq
import itertools
import json
import math
import time
from pathlib import Path

import numpy as np

import phase484a_raw_symbol_vic_solver as base
import phase484g_hard_negative_discriminator as learned
import phase484h_discriminator_landscape_probe as full_model

SCRIPT_DIR = Path(__file__).resolve().parent
WIDTHS = (10, 15, 19)
BOARD_MODES = base.BOARD_MODES
TRAIN_INDICES = learned.TRAIN_INDICES
EVAL_INDEX = 22
START_DEPTH = 4
BEAM_WIDTH = 4096
EARLY_BEAM_WIDTH = 16384
EARLY_THROUGH_DEPTH = 6
NEGATIVE_RATIO = 2
SEED = 0x484A000


def blocks_from_observed(fixture: dict) -> list[str]:
    width = fixture["width"]
    if len(fixture["observed"]) % width:
        raise ValueError("constructive probe requires exact-width geometry")
    length = len(fixture["observed"]) // width
    return [
        fixture["observed"][i * length:(i + 1) * length]
        for i in range(width)
    ]


def order_to_sequence(order) -> list[int]:
    sequence = [0] * len(order)
    for block_index, column_index in enumerate(order):
        sequence[column_index] = block_index
    return sequence


def sequence_to_order(sequence) -> list[int]:
    order = [0] * len(sequence)
    for column_index, block_index in enumerate(sequence):
        order[block_index] = column_index
    return order


def entropy(values: np.ndarray) -> float:
    positive = values[values > 0]
    return -float(np.dot(positive, np.log(positive))) if len(positive) else 0.0


def prefix_features(blocks: list[str], path, pair: tuple[str, str]) -> np.ndarray:
    path = tuple(path)
    rows = len(blocks[0])
    codes = base.slot_codes(pair)
    code_index = {code: index for index, code in enumerate(codes)}
    token_rows = []
    incomplete = 0
    end_escape = 0
    start_escape = 0
    raw_equal = 0
    raw_pairs = 0
    singles = 0
    raw_symbols = 0
    for row in range(rows):
        chars = "".join(blocks[block][row] for block in path)
        raw_symbols += len(chars)
        start_escape += chars[0] in pair
        end_escape += chars[-1] in pair
        raw_equal += sum(a == b for a, b in zip(chars, chars[1:]))
        raw_pairs += max(0, len(chars) - 1)
        tokens = []
        index = 0
        while index < len(chars):
            if chars[index] in pair:
                if index + 1 == len(chars):
                    incomplete += 1
                    break
                tokens.append(chars[index:index + 2])
                index += 2
            else:
                tokens.append(chars[index])
                singles += 1
                index += 1
        token_rows.append([code_index[token] for token in tokens])

    flat = [token for row in token_rows for token in row]
    counts = np.bincount(flat, minlength=25).astype(np.float64)
    frequencies = counts / max(1.0, counts.sum())
    matrix = np.zeros((25, 25), dtype=np.float64)
    for row in token_rows:
        if len(row) > 1:
            left = np.asarray(row[:-1], dtype=np.int64)
            right = np.asarray(row[1:], dtype=np.int64)
            np.add.at(matrix, (left, right), 1.0)
    if matrix.sum():
        matrix /= matrix.sum()
    values = [
        len(flat) / raw_symbols,
        singles / max(1, len(flat)),
        np.count_nonzero(counts) / 25.0,
        entropy(frequencies) / math.log(25),
        entropy(matrix.ravel()) / math.log(625),
        float(np.trace(matrix)),
        float(np.sum(matrix * matrix.T)),
        np.count_nonzero(matrix) / 625.0,
        incomplete / rows,
        end_escape / rows,
        start_escape / rows,
        raw_equal / max(1, raw_pairs),
    ]
    for lag in range(1, 9):
        matches = total = 0
        for row in token_rows:
            if len(row) > lag:
                matches += sum(a == b for a, b in zip(row[:-lag], row[lag:]))
                total += len(row) - lag
        values.append(matches / max(1, total))
    result = np.asarray(values, dtype=np.float64)
    if result.shape != (20,) or not np.all(np.isfinite(result)):
        raise AssertionError("unexpected prefix feature vector")
    return result


def fit_centroid(positives, negatives) -> learned.CentroidDiscriminator:
    values = np.asarray(list(positives) + list(negatives), dtype=np.float64)
    labels = np.asarray([True] * len(positives) + [False] * len(negatives))
    mean = values.mean(axis=0)
    scale = values.std(axis=0)
    scale[scale < 1e-9] = 1.0
    standardized = (values - mean) / scale
    pos = standardized[labels].mean(axis=0)
    neg = standardized[~labels].mean(axis=0)
    weight = pos - neg
    weight /= np.linalg.norm(weight)
    intercept = -0.5 * (float(np.dot(pos, weight)) + float(np.dot(neg, weight)))
    return learned.CentroidDiscriminator(mean, scale, weight, intercept)


def train_models(
    width: int, board_modes=BOARD_MODES
) -> dict[int, learned.CentroidDiscriminator]:
    fixtures = [
        base.make_fixture(
            width, learned.PAIR_INDEX, index, seed=learned.SEED,
            board_mode=mode, split="dev",
        )
        for mode in board_modes for index in TRAIN_INDICES
    ]
    models = {}
    for depth in range(START_DEPTH, width):
        positives, negatives = [], []
        for fixture in fixtures:
            blocks = blocks_from_observed(fixture)
            truth = order_to_sequence(fixture["order"])
            true_paths = {
                tuple(truth[start:start + depth])
                for start in range(width - depth + 1)
            }
            positives.extend(
                prefix_features(blocks, path, tuple(fixture["pair"]))
                for path in sorted(true_paths)
            )
            rng = base.PCG32(base.derive_seed(
                SEED, width, depth, fixture["fixture_index"],
                BOARD_MODES.index(fixture["board_mode"]),
            ))
            target = NEGATIVE_RATIO * len(true_paths)
            made = set()
            while len(made) < target:
                path = tuple(rng.permutation(width)[:depth])
                if path not in true_paths:
                    made.add(path)
            negatives.extend(
                prefix_features(blocks, path, tuple(fixture["pair"]))
                for path in sorted(made)
            )
        models[depth] = fit_centroid(positives, negatives)
    return models


def score_prefix(model, blocks, pair, path) -> float:
    return float(model.score([prefix_features(blocks, path, pair)])[0])


def constructive_search(
    fixture, models, beam_width: int = BEAM_WIDTH,
    early_beam_width: int | None = None,
    early_through_depth: int = START_DEPTH,
) -> dict:
    width = fixture["width"]
    blocks = blocks_from_observed(fixture)
    pair = tuple(fixture["pair"])
    truth_sequence = order_to_sequence(fixture["order"])
    began = time.monotonic()
    initial = []
    for path in itertools.permutations(range(width), START_DEPTH):
        score = score_prefix(models[START_DEPTH], blocks, pair, path)
        initial.append((score, path))
    first_width = early_beam_width or beam_width
    beam = heapq.nlargest(first_width, initial, key=lambda item: (item[0], item[1]))
    diagnostics = []
    for depth in range(START_DEPTH, width):
        truth_prefix = tuple(truth_sequence[:depth])
        rank = next(
            (index for index, (_, path) in enumerate(
                sorted(beam, key=lambda item: (-item[0], item[1])), start=1
            ) if path == truth_prefix),
            None,
        )
        diagnostics.append({
            "depth": depth,
            "beam_size": len(beam),
            "truth_prefix_retained": rank is not None,
            "truth_prefix_rank": rank,
        })
        if depth == width - 1:
            break
        candidates = []
        model = models[depth + 1]
        for _, path in beam:
            used = set(path)
            for block in range(width):
                if block not in used:
                    extended = path + (block,)
                    candidates.append((
                        score_prefix(model, blocks, pair, extended),
                        extended,
                    ))
        next_depth = depth + 1
        retain = (
            early_beam_width
            if early_beam_width is not None and next_depth <= early_through_depth
            else beam_width
        )
        beam = heapq.nlargest(retain, candidates, key=lambda item: (item[0], item[1]))

    complete = []
    classifier = full_model.load_model()
    spectral = base.SpectralModel.from_training_corpus()
    for _, path in beam:
        missing = [block for block in range(width) if block not in path]
        if len(missing) != 1:
            raise AssertionError("penultimate beam path has wrong remainder")
        sequence = path + (missing[0],)
        order = sequence_to_order(sequence)
        score = full_model.objective(classifier, spectral, fixture, order)
        if score is not None:
            complete.append((score, sequence, order))
    if not complete:
        raise RuntimeError("beam produced no valid terminal segmentation")
    complete.sort(key=lambda item: (-item[0], item[1]))
    best_score, best_sequence, best_order = complete[0]
    truth_rank = next(
        (index for index, (_, sequence, _) in enumerate(complete, start=1)
         if list(sequence) == truth_sequence),
        None,
    )
    diagnostics.append({
        "depth": width,
        "beam_size": len(complete),
        "truth_prefix_retained": truth_rank is not None,
        "truth_prefix_rank": truth_rank,
    })
    return {
        "exact_recovery": best_order == fixture["order"],
        "best_tau": base.kendall_tau(fixture["order"], best_order),
        "best_score": best_score,
        "best_sequence": list(best_sequence),
        "best_order": best_order,
        "truth_full_rank_if_retained": truth_rank,
        "valid_terminal_count": len(complete),
        "depth_diagnostics": diagnostics,
        "wall_seconds": time.monotonic() - began,
    }


def run_probe() -> dict:
    cells = []
    began = time.monotonic()
    for width in WIDTHS:
        trained_at = time.monotonic()
        models = train_models(width)
        training_seconds = time.monotonic() - trained_at
        for mode in BOARD_MODES:
            fixture = base.make_fixture(
                width, learned.PAIR_INDEX, EVAL_INDEX, seed=learned.SEED,
                board_mode=mode, split="dev",
            )
            cells.append({
                "board_mode": mode,
                "width": width,
                "fixture_index": EVAL_INDEX,
                "training_seconds_for_width": training_seconds,
                **constructive_search(fixture, models),
            })
    return {
        "phase": "484J",
        "status": "informal_constructive_prefix_beam_dev_not_frozen",
        "faed_scored": False,
        "fixture_split": "dev",
        "train_indices": list(TRAIN_INDICES),
        "eval_index": EVAL_INDEX,
        "budgets": {
            "start_depth": START_DEPTH,
            "beam_width": BEAM_WIDTH,
            "negative_ratio": NEGATIVE_RATIO,
        },
        "exact_recovery_count": sum(c["exact_recovery"] for c in cells),
        "cell_count": len(cells),
        "cells": cells,
        "wall_seconds": time.monotonic() - began,
    }


def run_adaptive_rescue() -> dict:
    specs = (
        ("vic_profile", 15),
        ("broad_random", 15),
        ("broad_random", 19),
    )
    cells = []
    began = time.monotonic()
    models_by_width = {}
    for mode, width in specs:
        if width not in models_by_width:
            models_by_width[width] = train_models(width)
        fixture = base.make_fixture(
            width, learned.PAIR_INDEX, EVAL_INDEX, seed=learned.SEED,
            board_mode=mode, split="dev",
        )
        cells.append({
            "board_mode": mode,
            "width": width,
            "fixture_index": EVAL_INDEX,
            **constructive_search(
                fixture, models_by_width[width],
                beam_width=BEAM_WIDTH,
                early_beam_width=EARLY_BEAM_WIDTH,
                early_through_depth=EARLY_THROUGH_DEPTH,
            ),
        })
    return {
        "phase": "484J",
        "status": "informal_adaptive_early_beam_rescue_dev_not_frozen",
        "faed_scored": False,
        "fixture_split": "dev",
        "source_result": "phase484j_constructive_prefix_beam_result.json",
        "failed_cells_only": True,
        "budgets": {
            "start_depth": START_DEPTH,
            "early_beam_width": EARLY_BEAM_WIDTH,
            "early_through_depth": EARLY_THROUGH_DEPTH,
            "later_beam_width": BEAM_WIDTH,
            "negative_ratio": NEGATIVE_RATIO,
        },
        "exact_recovery_count": sum(c["exact_recovery"] for c in cells),
        "cell_count": len(cells),
        "cells": cells,
        "wall_seconds": time.monotonic() - began,
    }


def self_test() -> None:
    order = [2, 0, 3, 1]
    sequence = order_to_sequence(order)
    assert sequence == [1, 3, 0, 2]
    assert sequence_to_order(sequence) == order
    fixture = base.make_fixture(
        10, 0, 777, seed=learned.SEED,
        board_mode="vic_profile", split="dev",
    )
    blocks = blocks_from_observed(fixture)
    sequence = order_to_sequence(fixture["order"])
    restored = "".join(
        "".join(blocks[index][row] for index in sequence)
        for row in range(len(blocks[0]))
    )
    assert restored == fixture["raw"]
    vector = prefix_features(blocks, order_to_sequence(fixture["order"])[:4],
                             tuple(fixture["pair"]))
    assert vector.shape == (20,) and np.all(np.isfinite(vector))


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
        self_test()
        print("self-test: ok")
        raise SystemExit(0)
    rescue = len(sys.argv) > 1 and sys.argv[1] == "--adaptive-rescue"
    result = run_adaptive_rescue() if rescue else run_probe()
    path = SCRIPT_DIR / (
        "phase484j_adaptive_rescue_result.json" if rescue
        else "phase484j_constructive_prefix_beam_result.json"
    )
    path.write_text(json.dumps(result, indent=2))
    print("exact", result["exact_recovery_count"], "/", result["cell_count"])
    for cell in result["cells"]:
        lost = next(
            (d["depth"] for d in cell["depth_diagnostics"]
             if not d["truth_prefix_retained"]),
            None,
        )
        print(cell["board_mode"], cell["width"],
              "exact", cell["exact_recovery"],
              "tau", round(cell["best_tau"], 3),
              "truth_lost_at", lost)
    print("wrote", path)
