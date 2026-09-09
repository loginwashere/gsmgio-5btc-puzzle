#!/usr/bin/env python3
"""Phase 483B development infrastructure for a population-search recovery
probe over Phase 483A's substitution-invariant equality-pattern statistic.

This module intentionally does not import or score FAED. Phase 483A showed
the statistic ranks the true order near the top of 10,000 random draws for
untranspose widths 15, 25 and 38; it explicitly did not show that a search
algorithm can find that order inside the full (unenumerable) permutation
space. This module tests that directly with simulated annealing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

import phase483a_invariant_order_statistic_probe as base483a

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
PROTOCOL = REPO_ROOT / "doc/Brainstorms/2026-09-07 - Phase 483B Population Search Recovery Probe Protocol.md"
DEFAULT_LOCK = SCRIPT_DIR / "phase483b_execution_lock.json"

DIRECTION = "untranspose"
WIDTHS = (15, 25, 38)
SEED_DEV = 0x483B0DE
SEED_HOLDOUT = 0x483B401D
FIXTURES_PER_CELL = 10
DEFAULT_ITERS = 20_000
DEFAULT_RESTARTS = 4
DEFAULT_T0 = 8.0
DEFAULT_T1 = 0.05


def uniform01(rng: base483a.PCG32) -> float:
    return rng.next_u32() / 4294967296.0


def kendall_tau(order_a, order_b) -> float:
    width = len(order_a)
    rank_a = np.empty(width, dtype=np.int64)
    rank_b = np.empty(width, dtype=np.int64)
    rank_a[np.asarray(order_a)] = np.arange(width)
    rank_b[np.asarray(order_b)] = np.arange(width)
    concordant = 0
    for i in range(width):
        for j in range(i + 1, width):
            concordant += 1 if (rank_a[i] - rank_a[j]) * (rank_b[i] - rank_b[j]) > 0 else -1
    denominator = width * (width - 1) / 2
    return concordant / denominator if denominator else 1.0


def anneal_order(fixture: dict, model: base483a.EqualityModel, rng: base483a.PCG32,
                 iters: int, t0: float, t1: float,
                 start_order: list[int] | None = None) -> tuple[list[int], float]:
    """Metropolis simulated annealing over column-order permutations, using
    Phase 483A's four-move corruption kernel (swap / move / reversal /
    3-cycle) as the proposal distribution."""
    width = fixture["width"]
    order = start_order if start_order is not None else rng.permutation(width)

    def score(candidate: list[int]) -> float:
        return model.score(base483a.reconstructed(fixture, candidate))

    current_score = score(order)
    best_order, best_score = list(order), current_score
    cool = (t1 / t0) ** (1.0 / max(1, iters))
    temperature = t0
    for _ in range(iters):
        proposed = base483a.corrupt_order(order, rng, 1)
        proposed_score = score(proposed)
        delta = proposed_score - current_score
        if delta >= 0 or uniform01(rng) < math.exp(delta / temperature):
            order, current_score = proposed, proposed_score
            if current_score > best_score:
                best_order, best_score = list(order), current_score
        temperature *= cool
    return best_order, best_score


def search_fixture(fixture: dict, model: base483a.EqualityModel, seed: int,
                   iters: int, restarts: int, t0: float, t1: float) -> dict:
    planted_score = model.score(base483a.reconstructed(fixture, fixture["order"]))
    best_order, best_score = None, -math.inf
    for restart in range(restarts):
        rng = base483a.PCG32(base483a.derive_seed(seed, fixture["width"], fixture["index"], restart))
        order, score = anneal_order(fixture, model, rng, iters, t0, t1)
        if score > best_score:
            best_order, best_score = order, score
    exact = best_order == list(fixture["order"])
    return {
        "fixture_index": fixture["index"],
        "width": fixture["width"],
        "direction": fixture["direction"],
        "planted_score": planted_score,
        "best_found_score": best_score,
        "found_at_least_planted": best_score >= planted_score,
        "exact_order_recovery": exact,
        "kendall_tau_to_truth": kendall_tau(fixture["order"], best_order),
        "best_found_order": list(best_order),
    }


def fixture_passes(record: dict) -> bool:
    return record["exact_order_recovery"]


def run_batch(split: str, widths=WIDTHS, fixtures_per_cell: int = FIXTURES_PER_CELL,
             iters: int = DEFAULT_ITERS, restarts: int = DEFAULT_RESTARTS,
             t0: float = DEFAULT_T0, t1: float = DEFAULT_T1,
             gate_frozen: bool = False) -> dict:
    if split not in ("dev", "holdout"):
        raise ValueError("split must be dev or holdout")
    seed = SEED_DEV if split == "dev" else SEED_HOLDOUT
    model = base483a.EqualityModel.train(base483a.corpus_splits()["train"])
    cells = []
    for width in widths:
        records = []
        for index in range(fixtures_per_cell):
            fixture = base483a.make_fixture(split, width, DIRECTION, index)
            records.append(search_fixture(fixture, model, seed, iters, restarts, t0, t1))
        passed = sum(fixture_passes(r) for r in records)
        cells.append({
            "width": width,
            "direction": DIRECTION,
            "fixture_count": fixtures_per_cell,
            "exact_recovery_count": passed,
            "gate_pass": (passed >= 8) if gate_frozen else None,
            "mean_kendall_tau": float(np.mean([r["kendall_tau_to_truth"] for r in records])),
            "reached_or_beat_planted_score_count": sum(r["found_at_least_planted"] for r in records),
            "records": records,
        })
    return {
        "phase": "483B",
        "status": "locked_holdout" if gate_frozen else "informal_dev_scoping_not_frozen",
        "split": split,
        "faed_scored": False,
        "budgets": {"iters": iters, "restarts": restarts, "t0": t0, "t1": t1,
                    "fixtures_per_cell": fixtures_per_cell},
        "cells": cells,
        "powered_cells": (
            [{"width": c["width"], "direction": c["direction"]}
             for c in cells if c["gate_pass"]]
            if gate_frozen else None
        ),
    }


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lock_payload(iters: int, restarts: int, t0: float, t1: float) -> dict:
    base_module = SCRIPT_DIR / "phase483a_invariant_order_statistic_probe.py"
    verifier = SCRIPT_DIR / "phase483b_verify_run.py"
    return {
        "phase": "483B",
        "status": "locked-before-holdout",
        "files_sha256": {
            "protocol": sha256_file(PROTOCOL),
            "audit_script": sha256_file(Path(__file__)),
            "base_module": sha256_file(base_module),
            "verifier": sha256_file(verifier),
            "corpus": sha256_file(base483a.CORPUS_FILE),
        },
        "widths": list(WIDTHS),
        "direction": DIRECTION,
        "seeds": {"dev": SEED_DEV, "holdout": SEED_HOLDOUT},
        "budgets": {"iters": iters, "restarts": restarts, "t0": t0, "t1": t1,
                    "fixtures_per_cell": FIXTURES_PER_CELL},
        "gate": {"minimum_passed_fixtures": 8, "pass_condition": "exact_order_recovery"},
        "prohibitions": {
            "faed_scoring": True,
            "widths_other_than_483a_powered_cells": True,
            "budget_tuning_after_holdout": True,
        },
        "faed_scored": False,
    }


def self_test() -> bool:
    model = base483a.EqualityModel.train(base483a.corpus_splits()["train"])
    fixture = base483a.make_fixture("dev", 15, DIRECTION, 0)
    rng = base483a.PCG32(1)
    order, score = anneal_order(fixture, model, rng, iters=200, t0=DEFAULT_T0, t1=DEFAULT_T1)
    assert sorted(order) == list(range(15))
    assert isinstance(score, float)
    truth = list(fixture["order"])
    assert kendall_tau(truth, truth) == 1.0
    tiny = run_batch("dev", widths=(15,), fixtures_per_cell=1, iters=50, restarts=1)
    assert tiny["faed_scored"] is False and tiny["powered_cells"] is None
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--dev-batch", action="store_true")
    parser.add_argument("--holdout", action="store_true")
    parser.add_argument("--write-lock", action="store_true")
    parser.add_argument("--iters", type=int, default=DEFAULT_ITERS)
    parser.add_argument("--restarts", type=int, default=DEFAULT_RESTARTS)
    parser.add_argument("--t0", type=float, default=DEFAULT_T0)
    parser.add_argument("--t1", type=float, default=DEFAULT_T1)
    parser.add_argument("--fixtures", type=int, default=FIXTURES_PER_CELL)
    parser.add_argument("--widths", type=int, nargs="+", default=list(WIDTHS))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps({"self_test": self_test()}))
        return 0
    if args.write_lock:
        DEFAULT_LOCK.write_text(
            json.dumps(lock_payload(args.iters, args.restarts, args.t0, args.t1),
                      indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(DEFAULT_LOCK)
        return 0
    if args.dev_batch:
        result = run_batch("dev", widths=tuple(args.widths), fixtures_per_cell=args.fixtures,
                           iters=args.iters, restarts=args.restarts, t0=args.t0, t1=args.t1)
    elif args.holdout:
        result = run_batch("holdout", widths=tuple(args.widths), fixtures_per_cell=args.fixtures,
                           iters=args.iters, restarts=args.restarts, t0=args.t0, t1=args.t1,
                           gate_frozen=True)
    else:
        parser.error("choose --self-test, --dev-batch, --holdout, or --write-lock")
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
