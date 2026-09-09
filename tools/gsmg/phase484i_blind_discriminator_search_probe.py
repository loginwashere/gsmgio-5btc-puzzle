#!/usr/bin/env python3
"""Blind synthetic search using Phase 484G's cheap discriminator."""

from __future__ import annotations

import concurrent.futures
import json
import math
import time
from pathlib import Path

import phase484a_raw_symbol_vic_solver as base
import phase484f_modelb_spectral_annealing_probe as moves
import phase484g_hard_negative_discriminator as features
import phase484h_discriminator_landscape_probe as landscape

SCRIPT_DIR = Path(__file__).resolve().parent
WIDTHS = features.WIDTHS
BOARD_MODES = features.BOARD_MODES
FIXTURE_INDEX = 21
SEED = 0x4849000
POPULATION_SAMPLES = 256
POPULATION_STARTS = 4
RANDOM_STARTS = 4
ANNEAL_ITERS = 5000
T0 = 2.5
T1 = 0.02
MAX_REFINE_STEPS = 50
WORKERS = 6


def objective(classifier, spectral, fixture, order) -> float | None:
    if features.order_score(spectral, fixture, order) is None:
        return None
    vector = features.candidate_features(
        spectral, fixture, order, include_neighborhood=False
    )[20:40]
    return float(classifier.score([vector])[0])


def random_valid(classifier, spectral, fixture, rng):
    for _ in range(10000):
        order = rng.permutation(fixture["width"])
        score = objective(classifier, spectral, fixture, order)
        if score is not None:
            return order, score
    raise RuntimeError("could not draw a valid blind order")


def make_starts(classifier, spectral, fixture, rng):
    population = []
    seen = set()
    while len(population) < POPULATION_SAMPLES:
        order, score = random_valid(classifier, spectral, fixture, rng)
        key = tuple(order)
        if key not in seen:
            seen.add(key)
            population.append((score, key))
    population.sort(key=lambda item: (-item[0], item[1]))
    starts = [list(order) for _, order in population[:POPULATION_STARTS]]
    while len(starts) < POPULATION_STARTS + RANDOM_STARTS:
        order, _ = random_valid(classifier, spectral, fixture, rng)
        if tuple(order) not in {tuple(start) for start in starts}:
            starts.append(order)
    return starts


def anneal(classifier, spectral, fixture, start, rng):
    current = list(start)
    current_score = objective(classifier, spectral, fixture, current)
    best, best_score = list(current), current_score
    cooling = (T1 / T0) ** (1.0 / ANNEAL_ITERS)
    temperature = T0
    for _ in range(ANNEAL_ITERS):
        candidate = moves.propose(current, rng)
        score = objective(classifier, spectral, fixture, candidate)
        if score is not None:
            delta = score - current_score
            if delta >= 0 or rng.random() < math.exp(delta / temperature):
                current, current_score = candidate, score
                if score > best_score:
                    best, best_score = list(candidate), score
        temperature *= cooling
    return best, best_score


def refine(classifier, spectral, fixture, start):
    current = list(start)
    current_score = objective(classifier, spectral, fixture, current)
    for step in range(MAX_REFINE_STEPS):
        winner, winner_score = current, current_score
        for i in range(len(current)):
            for j in range(i + 1, len(current)):
                candidate = list(current)
                candidate[i], candidate[j] = candidate[j], candidate[i]
                score = objective(classifier, spectral, fixture, candidate)
                if score is not None and score > winner_score:
                    winner, winner_score = candidate, score
        if winner is current:
            return current, current_score, step
        current, current_score = winner, winner_score
    return current, current_score, MAX_REFINE_STEPS


def run_cell(spec):
    board_mode, width = spec
    classifier = landscape.load_model()
    spectral = base.SpectralModel.from_training_corpus()
    fixture = base.make_fixture(
        width, features.PAIR_INDEX, FIXTURE_INDEX, seed=features.SEED,
        board_mode=board_mode, split="dev",
    )
    truth = list(fixture["order"])
    truth_score = objective(classifier, spectral, fixture, truth)
    cell_seed = base.derive_seed(
        SEED, BOARD_MODES.index(board_mode), width, FIXTURE_INDEX
    )
    start_rng = base.PCG32(cell_seed)
    starts = make_starts(classifier, spectral, fixture, start_rng)
    records = []
    began = time.monotonic()
    for index, start in enumerate(starts):
        annealed, _ = anneal(
            classifier, spectral, fixture, start,
            base.PCG32(base.derive_seed(cell_seed, index)),
        )
        final, score, refine_steps = refine(
            classifier, spectral, fixture, annealed
        )
        records.append({
            "start_class": "population" if index < POPULATION_STARTS else "random",
            "start_index": index,
            "start_tau": base.kendall_tau(truth, start),
            "final_score": score,
            "final_tau": base.kendall_tau(truth, final),
            "exact_recovery": final == truth,
            "refine_steps": refine_steps,
            "final_order": final,
        })
    return {
        "board_mode": board_mode,
        "width": width,
        "fixture_index": FIXTURE_INDEX,
        "exact_recovery": any(r["exact_recovery"] for r in records),
        "best_tau": max(r["final_tau"] for r in records),
        "truth_score": truth_score,
        "best_endpoint_score": max(r["final_score"] for r in records),
        "best_endpoint_minus_truth": (
            max(r["final_score"] for r in records) - truth_score
        ),
        "wall_seconds": time.monotonic() - began,
        "records": records,
    }


def run_probe():
    specs = [(mode, width) for mode in BOARD_MODES for width in WIDTHS]
    began = time.monotonic()
    with concurrent.futures.ProcessPoolExecutor(max_workers=WORKERS) as pool:
        cells = list(pool.map(run_cell, specs))
    return {
        "phase": "484I",
        "status": "informal_blind_discriminator_search_smoke_dev_not_frozen",
        "faed_scored": False,
        "fixture_split": "dev",
        "fixture_index": FIXTURE_INDEX,
        "budgets": {
            "population_samples": POPULATION_SAMPLES,
            "population_starts": POPULATION_STARTS,
            "random_starts": RANDOM_STARTS,
            "anneal_iters": ANNEAL_ITERS,
            "t0": T0,
            "t1": T1,
            "max_refine_steps": MAX_REFINE_STEPS,
        },
        "exact_recovery_count": sum(c["exact_recovery"] for c in cells),
        "cell_count": len(cells),
        "cells": cells,
        "wall_seconds": time.monotonic() - began,
    }


def self_test():
    assert POPULATION_STARTS + RANDOM_STARTS == 8
    classifier = landscape.load_model()
    spectral = base.SpectralModel.from_training_corpus()
    fixture = base.make_fixture(
        10, 0, FIXTURE_INDEX, seed=features.SEED,
        board_mode="vic_profile", split="dev",
    )
    truth = fixture["order"]
    assert objective(classifier, spectral, fixture, truth) is not None


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
        self_test()
        print("self-test: ok")
        raise SystemExit(0)
    result = run_probe()
    path = SCRIPT_DIR / "phase484i_blind_discriminator_search_result.json"
    path.write_text(json.dumps(result, indent=2))
    print("exact", result["exact_recovery_count"], "/", result["cell_count"])
    for cell in result["cells"]:
        print(cell["board_mode"], cell["width"],
              "exact", cell["exact_recovery"],
              "best_tau", round(cell["best_tau"], 3))
    print("wrote", path)
