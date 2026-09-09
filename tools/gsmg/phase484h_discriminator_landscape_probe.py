#!/usr/bin/env python3
"""Local landscape audit for Phase 484G's cheap discriminator objective."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

import phase484a_raw_symbol_vic_solver as base
import phase484g_hard_negative_discriminator as discriminator

SCRIPT_DIR = Path(__file__).resolve().parent
MODEL_PATH = SCRIPT_DIR / "phase484g_hard_negative_discriminator_result.json"
WIDTHS = discriminator.WIDTHS
BOARD_MODES = discriminator.BOARD_MODES
FIXTURE_INDICES = discriminator.EVAL_INDICES
RANDOM_RANK_SAMPLES = 2000
SEED = 0x4848000


def load_model(path: Path = MODEL_PATH) -> discriminator.CentroidDiscriminator:
    payload = json.loads(path.read_text())
    record = payload["ablations"]["segmentation_transition_lag_only"]
    if record["feature_indices"] != list(range(20, 40)):
        raise ValueError("unexpected Phase 484G feature selection")
    model = record["classifier"]
    return discriminator.CentroidDiscriminator(
        np.asarray(model["mean"], dtype=np.float64),
        np.asarray(model["scale"], dtype=np.float64),
        np.asarray(model["weight"], dtype=np.float64),
        float(model["intercept"]),
    )


def objective(model, spectral_model, fixture, order) -> float | None:
    if discriminator.order_score(spectral_model, fixture, order) is None:
        return None
    features = discriminator.candidate_features(
        spectral_model, fixture, order, include_neighborhood=False
    )[20:40]
    return float(model.score([features])[0])


def audit_fixture(spec: tuple[str, int, int]) -> dict:
    board_mode, width, fixture_index = spec
    classifier = load_model()
    spectral = base.SpectralModel.from_training_corpus()
    fixture = base.make_fixture(
        width, discriminator.PAIR_INDEX, fixture_index,
        seed=discriminator.SEED, board_mode=board_mode, split="dev",
    )
    truth = list(fixture["order"])
    truth_score = objective(classifier, spectral, fixture, truth)
    improving, invalid, gains = 0, 0, []
    best_gain = -float("inf")
    for i in range(width):
        for j in range(i + 1, width):
            candidate = list(truth)
            candidate[i], candidate[j] = candidate[j], candidate[i]
            score = objective(classifier, spectral, fixture, candidate)
            if score is None:
                invalid += 1
                continue
            gain = score - truth_score
            gains.append(gain)
            improving += gain > 0
            best_gain = max(best_gain, gain)

    rng = base.PCG32(base.derive_seed(
        SEED, BOARD_MODES.index(board_mode), width, fixture_index
    ))
    exceedances, valid = 0, 0
    for _ in range(RANDOM_RANK_SAMPLES):
        candidate = discriminator.random_valid_order(spectral, fixture, rng)
        score = objective(classifier, spectral, fixture, candidate)
        valid += 1
        exceedances += score >= truth_score
    return {
        "board_mode": board_mode,
        "width": width,
        "fixture_index": fixture_index,
        "truth_score": truth_score,
        "valid_swap_neighbors": len(gains),
        "invalid_swap_neighbors": invalid,
        "improving_swap_neighbors": improving,
        "truth_is_strict_local_optimum": improving == 0,
        "best_neighbor_gain": best_gain,
        "mean_neighbor_gain": float(np.mean(gains)),
        "random_rank_samples": valid,
        "random_at_or_above_truth": exceedances,
        "tie_inclusive_empirical_top_fraction": (exceedances + 1) / (valid + 1),
    }


def run_probe() -> dict:
    records = [
        audit_fixture((mode, width, index))
        for mode in BOARD_MODES
        for width in WIDTHS
        for index in FIXTURE_INDICES
    ]
    cells = []
    for mode in BOARD_MODES:
        for width in WIDTHS:
            selected = [
                record for record in records
                if record["board_mode"] == mode and record["width"] == width
            ]
            cells.append({
                "board_mode": mode,
                "width": width,
                "fixture_count": len(selected),
                "local_optimum_count": sum(
                    r["truth_is_strict_local_optimum"] for r in selected
                ),
                "median_random_top_fraction": float(np.median([
                    r["tie_inclusive_empirical_top_fraction"] for r in selected
                ])),
                "records": selected,
            })
    return {
        "phase": "484H",
        "status": "informal_discriminator_landscape_dev_not_frozen",
        "faed_scored": False,
        "fixture_split": "dev",
        "model_path": MODEL_PATH.name,
        "feature_indices": list(range(20, 40)),
        "random_rank_samples_per_fixture": RANDOM_RANK_SAMPLES,
        "cells": cells,
    }


def self_test() -> None:
    model = load_model()
    assert model.weight.shape == (20,)
    spectral = base.SpectralModel.from_training_corpus()
    fixture = base.make_fixture(
        10, 0, FIXTURE_INDICES[0], seed=discriminator.SEED,
        board_mode="vic_profile", split="dev",
    )
    assert np.isfinite(objective(model, spectral, fixture, fixture["order"]))


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
        self_test()
        print("self-test: ok")
        raise SystemExit(0)
    result = run_probe()
    path = SCRIPT_DIR / "phase484h_discriminator_landscape_result.json"
    path.write_text(json.dumps(result, indent=2))
    for cell in result["cells"]:
        print(cell["board_mode"], cell["width"],
              "local", cell["local_optimum_count"], "/", cell["fixture_count"],
              "median_random_top", round(cell["median_random_top_fraction"], 6))
    print("wrote", path)
