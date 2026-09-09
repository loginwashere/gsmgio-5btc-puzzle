#!/usr/bin/env python3
"""Synthetic-only multi-start annealing probe for Phase 484 Model B."""

from __future__ import annotations

import concurrent.futures
import json
import math
import time
from pathlib import Path

import numpy as np

import phase484a_raw_symbol_vic_solver as base

SCRIPT_DIR = Path(__file__).resolve().parent
WIDTHS = (10, 15, 19)
BOARD_MODES = base.BOARD_MODES
PAIR_INDEX = 0
FIXTURE_INDEX = 5
SEED = 0x484F0DE
POPULATION_SAMPLES = 512
SPECTRAL_STARTS = 4
RANDOM_STARTS = 2
CONTROLLED_DEPTHS = (1, 2, 4)
ANNEAL_ITERS = 5000
T0 = 0.05
T1 = 0.0005
MAX_REFINE_STEPS = 30
WORKERS = 6


def valid_score(model, fixture, order) -> float | None:
    return model.score_order(
        fixture["observed"], fixture["width"], order, tuple(fixture["pair"])
    )


def propose(order: list[int], rng: base.PCG32) -> list[int]:
    result = list(order)
    width = len(result)
    move = rng.below(4)
    i, j = rng.below(width), rng.below(width)
    while j == i:
        j = rng.below(width)
    if i > j:
        i, j = j, i
    if move == 0:
        result[i], result[j] = result[j], result[i]
    elif move == 1:
        value = result.pop(j)
        result.insert(i, value)
    elif move == 2:
        result[i:j + 1] = reversed(result[i:j + 1])
    else:
        k = rng.below(width)
        while k in (i, j):
            k = rng.below(width)
        i, j, k = sorted((i, j, k))
        result[i], result[j], result[k] = result[k], result[i], result[j]
    return result


def anneal(model, fixture, start: list[int], seed: int) -> tuple[list[int], float]:
    rng = base.PCG32(seed)
    current = list(start)
    current_score = valid_score(model, fixture, current)
    if current_score is None:
        raise ValueError("annealing start must have a valid segmentation")
    best, best_score = list(current), current_score
    cooling = (T1 / T0) ** (1.0 / ANNEAL_ITERS)
    temperature = T0
    for _ in range(ANNEAL_ITERS):
        candidate = propose(current, rng)
        candidate_score = valid_score(model, fixture, candidate)
        if candidate_score is not None:
            delta = candidate_score - current_score
            if delta >= 0 or rng.random() < math.exp(delta / temperature):
                current, current_score = candidate, candidate_score
                if current_score > best_score:
                    best, best_score = list(current), current_score
        temperature *= cooling
    return best, best_score


def swap_refine(model, fixture, start: list[int]) -> tuple[list[int], float, int]:
    current = list(start)
    current_score = valid_score(model, fixture, current)
    for step in range(MAX_REFINE_STEPS):
        best_order, best_score = current, current_score
        for i in range(len(current)):
            for j in range(i + 1, len(current)):
                candidate = list(current)
                candidate[i], candidate[j] = candidate[j], candidate[i]
                score = valid_score(model, fixture, candidate)
                if score is not None and score > best_score:
                    best_order, best_score = candidate, score
        if best_order is current:
            return current, current_score, step
        current, current_score = best_order, best_score
    return current, current_score, MAX_REFINE_STEPS


def random_valid_order(model, fixture, rng: base.PCG32) -> list[int]:
    for _ in range(10000):
        order = rng.permutation(fixture["width"])
        if valid_score(model, fixture, order) is not None:
            return order
    raise RuntimeError("could not draw valid random order")


def controlled_start(model, fixture, depth: int, seed: int) -> list[int]:
    rng = base.PCG32(seed)
    truth = list(fixture["order"])
    for _ in range(1000):
        positions = rng.permutation(fixture["width"])[:2 * depth]
        candidate = list(truth)
        for index in range(0, len(positions), 2):
            i, j = positions[index:index + 2]
            candidate[i], candidate[j] = candidate[j], candidate[i]
        if valid_score(model, fixture, candidate) is not None:
            return candidate
    raise RuntimeError("could not construct valid controlled start")


def make_starts(model, fixture, seed: int) -> list[dict]:
    starts = []
    for depth in CONTROLLED_DEPTHS:
        order = controlled_start(model, fixture, depth, base.derive_seed(seed, 0, depth))
        starts.append({"class": "controlled", "index": depth, "order": order})
    rng = base.PCG32(base.derive_seed(seed, 1))
    population = []
    for index in range(POPULATION_SAMPLES):
        order = random_valid_order(model, fixture, rng)
        population.append((valid_score(model, fixture, order), index, order))
    population.sort(key=lambda item: (-item[0], item[1]))
    for rank, (_, _, order) in enumerate(population[:SPECTRAL_STARTS], start=1):
        starts.append({"class": "spectral_population", "index": rank, "order": order})
    for index in range(RANDOM_STARTS):
        starts.append({
            "class": "random",
            "index": index,
            "order": random_valid_order(model, fixture, rng),
        })
    return starts


def run_fixture(spec: tuple[str, int]) -> dict:
    board_mode, width = spec
    model = base.SpectralModel.from_training_corpus()
    fixture = base.make_fixture(
        width, PAIR_INDEX, FIXTURE_INDEX, seed=SEED,
        board_mode=board_mode, split="dev",
    )
    truth = list(fixture["order"])
    fixture_seed = base.derive_seed(SEED, BOARD_MODES.index(board_mode), width, FIXTURE_INDEX)
    records = []
    began = time.monotonic()
    for start_number, start in enumerate(make_starts(model, fixture, fixture_seed)):
        start_tau = base.kendall_tau(truth, start["order"])
        annealed, _ = anneal(
            model, fixture, start["order"],
            base.derive_seed(fixture_seed, 2, start_number),
        )
        final, final_score, refine_steps = swap_refine(model, fixture, annealed)
        records.append({
            "start_class": start["class"],
            "start_index": start["index"],
            "start_tau": start_tau,
            "final_score": final_score,
            "final_tau": base.kendall_tau(truth, final),
            "exact_recovery": final == truth,
            "refine_steps": refine_steps,
            "final_order": final,
        })
    usable = [r for r in records if r["start_class"] != "controlled"]
    controlled = [r for r in records if r["start_class"] == "controlled"]
    return {
        "board_mode": board_mode,
        "width": width,
        "fixture_index": FIXTURE_INDEX,
        "planted_score": valid_score(model, fixture, truth),
        "usable_exact_recovery": any(r["exact_recovery"] for r in usable),
        "usable_best_tau": max(r["final_tau"] for r in usable),
        "controlled_exact_recovery": any(r["exact_recovery"] for r in controlled),
        "controlled_best_tau": max(r["final_tau"] for r in controlled),
        "wall_seconds": time.monotonic() - began,
        "records": records,
    }


def run_smoke() -> dict:
    specs = [(mode, width) for mode in BOARD_MODES for width in WIDTHS]
    began = time.monotonic()
    with concurrent.futures.ProcessPoolExecutor(max_workers=WORKERS) as pool:
        cells = list(pool.map(run_fixture, specs))
    return {
        "phase": "484F",
        "status": "informal_annealing_smoke_dev_not_frozen",
        "faed_scored": False,
        "fixture_split": "dev",
        "budgets": {
            "population_samples": POPULATION_SAMPLES,
            "spectral_starts": SPECTRAL_STARTS,
            "random_starts": RANDOM_STARTS,
            "controlled_depths": list(CONTROLLED_DEPTHS),
            "anneal_iters": ANNEAL_ITERS,
            "t0": T0,
            "t1": T1,
            "max_refine_steps": MAX_REFINE_STEPS,
        },
        "wall_seconds": time.monotonic() - began,
        "cells": cells,
    }


def self_test() -> None:
    rng = base.PCG32(1)
    order = list(range(10))
    for _ in range(20):
        candidate = propose(order, rng)
        assert sorted(candidate) == order and candidate != order
    assert set(WIDTHS) == {10, 15, 19}


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
        self_test()
        print("self-test: ok")
        raise SystemExit(0)
    result = run_smoke()
    path = SCRIPT_DIR / "phase484f_annealing_smoke_result.json"
    path.write_text(json.dumps(result, indent=2))
    for cell in result["cells"]:
        print(cell["board_mode"], cell["width"],
              "usable_exact", cell["usable_exact_recovery"],
              "usable_tau", round(cell["usable_best_tau"], 3),
              "controlled_exact", cell["controlled_exact_recovery"],
              "controlled_tau", round(cell["controlled_best_tau"], 3))
    print("wrote", path)
