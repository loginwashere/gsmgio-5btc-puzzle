#!/usr/bin/env python3
"""Synthetic-only hard-negative discriminator for Phase 484 Model B."""

from __future__ import annotations

import concurrent.futures
import json
import math
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

import phase484a_raw_symbol_vic_solver as base
import phase484f_modelb_spectral_annealing_probe as prior

SCRIPT_DIR = Path(__file__).resolve().parent
WIDTHS = (10, 15, 19)
BOARD_MODES = base.BOARD_MODES
PAIR_INDEX = 0
SEED = 0x4846000
TRAIN_INDICES = tuple(range(6, 16))
EVAL_INDICES = tuple(range(16, 21))
TRAIN_RANDOM = 4
TRAIN_HARD = 2
EVAL_RANDOM = 12
EVAL_HARD = 4
ANNEAL_ITERS = 2000
T0 = 0.04
T1 = 0.0008
REFINE_STEPS = 8
PASS_OVERALL = 0.80
PASS_PER_CELL = 0.60
WORKERS = 6


def order_score(model, fixture, order) -> float | None:
    return model.score_order(
        fixture["observed"], fixture["width"], order, tuple(fixture["pair"])
    )


def random_valid_order(model, fixture, rng: base.PCG32) -> list[int]:
    for _ in range(10000):
        order = rng.permutation(fixture["width"])
        if order_score(model, fixture, order) is not None:
            return order
    raise RuntimeError("could not draw valid order")


def anneal_false_maximum(model, fixture, rng: base.PCG32) -> list[int]:
    current = random_valid_order(model, fixture, rng)
    current_score = order_score(model, fixture, current)
    best, best_score = list(current), current_score
    cooling = (T1 / T0) ** (1.0 / ANNEAL_ITERS)
    temperature = T0
    for _ in range(ANNEAL_ITERS):
        candidate = prior.propose(current, rng)
        score = order_score(model, fixture, candidate)
        if score is not None:
            delta = score - current_score
            if delta >= 0 or rng.random() < math.exp(delta / temperature):
                current, current_score = candidate, score
                if score > best_score:
                    best, best_score = list(candidate), score
        temperature *= cooling
    for _ in range(REFINE_STEPS):
        winner, winner_score = best, best_score
        for i in range(len(best)):
            for j in range(i + 1, len(best)):
                candidate = list(best)
                candidate[i], candidate[j] = candidate[j], candidate[i]
                score = order_score(model, fixture, candidate)
                if score is not None and score > winner_score:
                    winner, winner_score = candidate, score
        if winner is best:
            break
        best, best_score = winner, winner_score
    return best


def entropy(values: np.ndarray) -> float:
    positive = values[values > 0]
    return -float(np.dot(positive, np.log(positive))) if len(positive) else 0.0


def candidate_features(model, fixture, order, include_neighborhood: bool = True) -> np.ndarray:
    pair = tuple(fixture["pair"])
    raw = base.Geometry(len(fixture["observed"]), fixture["width"]).decrypt(
        fixture["observed"], order
    )
    tokens = base.segment_raw(raw, pair)
    if tokens is None:
        raise ValueError("feature extraction requires a valid segmentation")
    matrix = base.transition_matrix(tokens, pair)
    spectral = base.spectral_features(matrix)
    difference = spectral - model.target
    result = []
    for block in np.split(difference, 5):
        absolute = np.abs(block)
        result.extend((
            float(np.dot(block, block)),
            float(np.mean(absolute)),
            float(np.std(block)),
            float(np.max(absolute)),
        ))

    code_index = {code: index for index, code in enumerate(base.slot_codes(pair))}
    indices = np.asarray([code_index[token] for token in tokens], dtype=np.int64)
    counts = np.bincount(indices, minlength=25).astype(np.float64)
    frequencies = counts / counts.sum()
    result.extend((
        len(tokens) / len(raw),
        sum(len(token) == 1 for token in tokens) / len(tokens),
        np.count_nonzero(counts) / 25.0,
        entropy(frequencies) / math.log(25),
        entropy(matrix.ravel()) / math.log(625),
        float(np.trace(matrix)),
        float(np.sum(matrix * matrix.T)),
        np.count_nonzero(matrix) / 625.0,
    ))
    for lag in range(1, 13):
        result.append(float(np.mean(indices[:-lag] == indices[lag:])))

    if not include_neighborhood:
        vector = np.asarray(result, dtype=np.float64)
        if vector.shape != (40,) or not np.all(np.isfinite(vector)):
            raise AssertionError("unexpected cheap feature vector")
        return vector

    planted_scalar = order_score(model, fixture, order)
    gains, invalid = [], 0
    for i in range(len(order)):
        for j in range(i + 1, len(order)):
            neighbor = list(order)
            neighbor[i], neighbor[j] = neighbor[j], neighbor[i]
            score = order_score(model, fixture, neighbor)
            if score is None:
                invalid += 1
            else:
                gains.append(score - planted_scalar)
    gain_array = np.asarray(gains, dtype=np.float64)
    total = len(gains) + invalid
    result.extend((
        planted_scalar,
        invalid / total,
        float(np.mean(gain_array > 0)),
        float(np.max(gain_array)),
        float(np.mean(gain_array)),
        float(np.std(gain_array)),
        float(np.quantile(gain_array, 0.10)),
        float(np.median(gain_array)),
        float(np.quantile(gain_array, 0.90)),
    ))
    vector = np.asarray(result, dtype=np.float64)
    if vector.shape != (49,) or not np.all(np.isfinite(vector)):
        raise AssertionError("unexpected feature vector")
    return vector


def fixture_examples(spec: tuple[str, int, int, int, int]) -> dict:
    board_mode, width, fixture_index, random_count, hard_count = spec
    model = base.SpectralModel.from_training_corpus()
    fixture = base.make_fixture(
        width, PAIR_INDEX, fixture_index, seed=SEED,
        board_mode=board_mode, split="dev",
    )
    rng = base.PCG32(base.derive_seed(
        SEED, base.BOARD_MODES.index(board_mode), width, fixture_index
    ))
    truth = list(fixture["order"])
    examples = [{
        "kind": "planted",
        "feature": candidate_features(model, fixture, truth).tolist(),
        "tau": 1.0,
    }]
    seen = {tuple(truth)}
    for kind, count in (("random", random_count), ("hard", hard_count)):
        made = 0
        while made < count:
            order = (random_valid_order(model, fixture, rng) if kind == "random"
                     else anneal_false_maximum(model, fixture, rng))
            key = tuple(order)
            if key in seen:
                continue
            seen.add(key)
            examples.append({
                "kind": kind,
                "feature": candidate_features(model, fixture, order).tolist(),
                "tau": base.kendall_tau(truth, order),
            })
            made += 1
    return {
        "board_mode": board_mode,
        "width": width,
        "fixture_index": fixture_index,
        "examples": examples,
    }


@dataclass
class CentroidDiscriminator:
    mean: np.ndarray
    scale: np.ndarray
    weight: np.ndarray
    intercept: float

    def score(self, features) -> np.ndarray:
        values = np.asarray(features, dtype=np.float64)
        standardized = (values - self.mean) / self.scale
        return standardized @ self.weight + self.intercept


def fit_discriminator(records: list[dict]) -> CentroidDiscriminator:
    features, labels = [], []
    for record in records:
        for example in record["examples"]:
            features.append(example["feature"])
            labels.append(example["kind"] == "planted")
    values = np.asarray(features, dtype=np.float64)
    labels = np.asarray(labels, dtype=bool)
    mean = values.mean(axis=0)
    scale = values.std(axis=0)
    scale[scale < 1e-9] = 1.0
    standardized = (values - mean) / scale
    positive = standardized[labels].mean(axis=0)
    negative = standardized[~labels].mean(axis=0)
    weight = positive - negative
    norm = np.linalg.norm(weight)
    if norm == 0:
        raise ValueError("classes have identical centroids")
    weight /= norm
    intercept = -0.5 * (float(np.dot(positive, weight)) +
                        float(np.dot(negative, weight)))
    return CentroidDiscriminator(mean, scale, weight, intercept)


def evaluate(model: CentroidDiscriminator, records: list[dict]) -> dict:
    cells = []
    for board_mode in BOARD_MODES:
        for width in WIDTHS:
            selected = [
                record for record in records
                if record["board_mode"] == board_mode and record["width"] == width
            ]
            fixture_results = []
            for record in selected:
                scores = model.score([e["feature"] for e in record["examples"]])
                planted_score = float(scores[0])
                rank = 1 + int(np.sum(scores[1:] >= planted_score))
                negatives = [e for e in record["examples"][1:]]
                fixture_results.append({
                    "fixture_index": record["fixture_index"],
                    "planted_rank": rank,
                    "candidate_count": len(scores),
                    "planted_score": planted_score,
                    "best_negative_score": float(np.max(scores[1:])),
                    "hard_negative_count": sum(e["kind"] == "hard" for e in negatives),
                    "best_hard_negative_tau": max(
                        e["tau"] for e in negatives if e["kind"] == "hard"
                    ),
                })
            rank_one = sum(r["planted_rank"] == 1 for r in fixture_results)
            cells.append({
                "board_mode": board_mode,
                "width": width,
                "fixture_count": len(fixture_results),
                "rank_one_count": rank_one,
                "rank_one_fraction": rank_one / len(fixture_results),
                "median_planted_rank": float(np.median(
                    [r["planted_rank"] for r in fixture_results]
                )),
                "records": fixture_results,
            })
    total = sum(c["fixture_count"] for c in cells)
    rank_one = sum(c["rank_one_count"] for c in cells)
    passed = (rank_one / total >= PASS_OVERALL and
              all(c["rank_one_fraction"] >= PASS_PER_CELL for c in cells))
    return {
        "overall_rank_one_count": rank_one,
        "overall_fixture_count": total,
        "overall_rank_one_fraction": rank_one / total,
        "passed_development_criterion": passed,
        "cells": cells,
    }


def select_features(records: list[dict], indices) -> list[dict]:
    indices = tuple(indices)
    selected = []
    for record in records:
        selected.append({
            **record,
            "examples": [
                {
                    **example,
                    "feature": [example["feature"][index] for index in indices],
                }
                for example in record["examples"]
            ],
        })
    return selected


def compact_evaluation(evaluation: dict) -> dict:
    return {
        "overall_rank_one_count": evaluation["overall_rank_one_count"],
        "overall_fixture_count": evaluation["overall_fixture_count"],
        "overall_rank_one_fraction": evaluation["overall_rank_one_fraction"],
        "passed_development_criterion": evaluation["passed_development_criterion"],
        "cells": [
            {
                "board_mode": cell["board_mode"],
                "width": cell["width"],
                "rank_one_count": cell["rank_one_count"],
                "fixture_count": cell["fixture_count"],
                "rank_one_fraction": cell["rank_one_fraction"],
                "median_planted_rank": cell["median_planted_rank"],
            }
            for cell in evaluation["cells"]
        ],
    }


def run_probe(
    train_indices=TRAIN_INDICES,
    eval_indices=EVAL_INDICES,
    train_random=TRAIN_RANDOM,
    train_hard=TRAIN_HARD,
    eval_random=EVAL_RANDOM,
    eval_hard=EVAL_HARD,
) -> dict:
    if set(train_indices) & set(eval_indices):
        raise ValueError("training and evaluation fixture indices must be disjoint")
    train_specs = [
        (mode, width, index, train_random, train_hard)
        for mode in BOARD_MODES for width in WIDTHS for index in train_indices
    ]
    eval_specs = [
        (mode, width, index, eval_random, eval_hard)
        for mode in BOARD_MODES for width in WIDTHS for index in eval_indices
    ]
    began = time.monotonic()
    with concurrent.futures.ProcessPoolExecutor(max_workers=WORKERS) as pool:
        train_records = list(pool.map(fixture_examples, train_specs))
        eval_records = list(pool.map(fixture_examples, eval_specs))
    classifier = fit_discriminator(train_records)
    evaluation = evaluate(classifier, eval_records)
    ablations = {}
    for name, indices in {
        "cheap_no_neighborhood": range(40),
        "segmentation_transition_lag_only": range(20, 40),
        "neighborhood_only": range(40, 49),
    }.items():
        reduced_train = select_features(train_records, indices)
        reduced_eval = select_features(eval_records, indices)
        reduced_classifier = fit_discriminator(reduced_train)
        ablations[name] = {
            **compact_evaluation(evaluate(reduced_classifier, reduced_eval)),
            "feature_indices": list(indices),
            "classifier": {
                "type": "diagonal_nearest_centroid",
                "mean": reduced_classifier.mean.tolist(),
                "scale": reduced_classifier.scale.tolist(),
                "weight": reduced_classifier.weight.tolist(),
                "intercept": reduced_classifier.intercept,
            },
        }
    return {
        "phase": "484G",
        "status": "informal_hard_negative_discriminator_dev_not_frozen",
        "faed_scored": False,
        "fixture_split": "dev",
        "widths": list(WIDTHS),
        "board_modes": list(BOARD_MODES),
        "train_indices": list(train_indices),
        "eval_indices": list(eval_indices),
        "budgets": {
            "train_random_per_fixture": train_random,
            "train_hard_per_fixture": train_hard,
            "eval_random_per_fixture": eval_random,
            "eval_hard_per_fixture": eval_hard,
            "anneal_iters": ANNEAL_ITERS,
            "refine_steps": REFINE_STEPS,
        },
        "feature_count": len(classifier.weight),
        "classifier": {
            "type": "diagonal_nearest_centroid",
            "mean": classifier.mean.tolist(),
            "scale": classifier.scale.tolist(),
            "weight": classifier.weight.tolist(),
            "intercept": classifier.intercept,
        },
        "criterion": {
            "overall_rank_one_fraction": PASS_OVERALL,
            "per_cell_rank_one_fraction": PASS_PER_CELL,
        },
        "evaluation": evaluation,
        "ablations": ablations,
        "wall_seconds": time.monotonic() - began,
    }


def self_test() -> None:
    assert not (set(TRAIN_INDICES) & set(EVAL_INDICES))
    toy = [
        {"examples": [
            {"kind": "planted", "feature": [2.0, 1.0]},
            {"kind": "hard", "feature": [-2.0, -1.0]},
        ]},
        {"examples": [
            {"kind": "planted", "feature": [1.5, 0.8]},
            {"kind": "random", "feature": [-1.5, -0.8]},
        ]},
    ]
    classifier = fit_discriminator(toy)
    assert classifier.score([[2.0, 1.0]])[0] > classifier.score([[-2.0, -1.0]])[0]
    reduced = select_features(toy, (0,))
    assert all(len(e["feature"]) == 1 for r in reduced for e in r["examples"])
    model = base.SpectralModel.from_training_corpus()
    fixture = base.make_fixture(10, PAIR_INDEX, 999, seed=SEED,
                                board_mode="vic_profile", split="dev")
    feature = candidate_features(model, fixture, fixture["order"])
    assert feature.shape == (49,) and np.all(np.isfinite(feature))
    cheap = candidate_features(
        model, fixture, fixture["order"], include_neighborhood=False
    )
    assert cheap.shape == (40,) and np.all(np.isfinite(cheap))


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
        self_test()
        print("self-test: ok")
        raise SystemExit(0)
    result = run_probe()
    path = SCRIPT_DIR / "phase484g_hard_negative_discriminator_result.json"
    path.write_text(json.dumps(result, indent=2))
    evaluation = result["evaluation"]
    print("overall", evaluation["overall_rank_one_count"],
          "/", evaluation["overall_fixture_count"],
          "passed", evaluation["passed_development_criterion"])
    for cell in evaluation["cells"]:
        print(cell["board_mode"], cell["width"],
              cell["rank_one_count"], "/", cell["fixture_count"],
              "median_rank", cell["median_planted_rank"])
    print("wrote", path)
