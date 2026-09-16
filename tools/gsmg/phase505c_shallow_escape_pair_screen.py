#!/usr/bin/env python3
"""Phase 505C: exhaustive depth-4 blind escape-pair screen.

This development lane replaces 505B's prohibitively expensive depth-7 matrix
with an exact enumeration of all 19P4 column fragments.  Every assumed escape
pair receives the identical path universe and unrestricted-board budget.
Synthetic truth is retained only under ``audit_only`` and never affects pair
ranking.  FAED is neither imported nor scored.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from pathlib import Path

import numpy as np

import phase484a_raw_symbol_vic_solver as base
import phase484j_constructive_prefix_beam_probe as prefix
import phase490_width19_dual_lane_dev as front
import phase493_partial_unrestricted_board_diagnostic as variants
import phase505_escape_pair_identifiability as ceiling


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
PROTOCOL = (REPO_ROOT / "doc" / "Brainstorms" /
            "2026-09-14 - Phase 505C Shallow Escape-Pair Screen Protocol.md")
LOCK_PATH = SCRIPT_DIR / "phase505c_pilot_lock.json"
DEFAULT_WORK_DIR = REPO_ROOT / "_work" / "phase505c" / "pilot"

WIDTH = 19
DEPTH = 4
EVAL_FIXTURE_INDEX = 1
PILOT_TRUE_PAIR_INDICES = (0, 17, 35)
RESTARTS = 3
ITERATIONS = 2000
BOARD_SEED = 0x505C001
TOP_PATHS_RECORDED = 32


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_json(path: Path, value: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def path_universe() -> np.ndarray:
    paths = front.initial_paths(WIDTH, DEPTH)
    expected = math.prod(range(WIDTH - DEPTH + 1, WIDTH + 1))
    if paths.shape != (expected, DEPTH):
        raise AssertionError("depth-4 path universe changed")
    return paths


def score_summary(scores) -> dict:
    values = np.asarray(scores, dtype=np.float64)
    if values.ndim != 1 or not len(values) or not np.all(np.isfinite(values)):
        raise ValueError("shallow score vector must be nonempty and finite")
    quantiles = np.quantile(values, (0.5, 0.9, 0.99, 0.999))
    best = float(np.max(values))
    return {
        "count": len(values), "best": best,
        "mean": float(np.mean(values)),
        "standard_deviation": float(np.std(values)),
        "q50": float(quantiles[0]), "q90": float(quantiles[1]),
        "q99": float(quantiles[2]), "q999": float(quantiles[3]),
        "best_minus_q99": best - float(quantiles[2]),
    }


def expected_lock_payload() -> dict:
    dependencies = (base, prefix, front, variants, ceiling)
    return {
        "phase": "505C-pilot", "status": "execution_lock",
        "protocol_sha256": sha256_file(PROTOCOL),
        "script_sha256": sha256_file(Path(__file__)),
        "dependencies_sha256": {
            str(Path(module.__file__).relative_to(REPO_ROOT)):
                sha256_file(Path(module.__file__))
            for module in dependencies
        },
        "phase505_fixture_manifest_sha256": sha256_file(
            ceiling.DEFAULT_MANIFEST),
        "phase505a_ceiling_result_sha256": sha256_file(
            REPO_ROOT / "_work" / "phase505" / "ceiling_result.json"),
        "phase505b_first_cell_sha256": sha256_file(
            REPO_ROOT / "_work" / "phase505b" / "development" /
            "true_00" / "hypothesis_00.json"),
        "unrestricted_board_binary_sha256": sha256_file(
            variants.UNRESTRICTED_BINARY),
        "width": WIDTH, "depth": DEPTH,
        "path_count": math.prod(range(WIDTH - DEPTH + 1, WIDTH + 1)),
        "evaluation_fixture_index": EVAL_FIXTURE_INDEX,
        "true_pair_indices": list(PILOT_TRUE_PAIR_INDICES),
        "hypothesis_pair_indices": list(range(len(ceiling.ALL_PAIRS))),
        "cell_count": len(PILOT_TRUE_PAIR_INDICES) * len(ceiling.ALL_PAIRS),
        "budgets": {"restarts": RESTARTS, "iterations": ITERATIONS,
                    "seed": BOARD_SEED},
        "primary_selector":
            "maximum unrestricted-board normalized score over all 19P4 paths",
        "faed_scored": False, "holdout_consumed": False,
    }


def verify_lock() -> dict:
    if not LOCK_PATH.is_file():
        raise RuntimeError("Phase-505C pilot execution lock is absent")
    actual = json.loads(LOCK_PATH.read_text())
    expected = expected_lock_payload()
    if actual != expected:
        raise RuntimeError("Phase-505C pilot execution lock mismatch")
    return actual


def run_cell(true_pair_index: int, hypothesis_pair_index: int,
             paths: np.ndarray | None = None) -> dict:
    fixture = ceiling.make_fixture(true_pair_index, EVAL_FIXTURE_INDEX)
    pair = ceiling.ALL_PAIRS[hypothesis_pair_index]
    blocks = prefix.blocks_from_observed(fixture)
    paths = path_universe() if paths is None else np.asarray(paths,
                                                             dtype=np.uint8)
    quad, _ = base.load_language_model()
    began = time.monotonic()
    scores = front.constrained_multistart(
        paths, blocks, pair, quad, RESTARTS, ITERATIONS,
        binary=variants.UNRESTRICTED_BINARY, seed=BOARD_SEED)
    summary = score_summary(scores)
    ranked = front.ranked_indices(paths, scores)[:TOP_PATHS_RECORDED]
    truth = prefix.order_to_sequence(fixture["order"])
    return {
        "phase": "505C", "status": "development_shallow_cell_complete",
        "faed_scored": False, "holdout_consumed": False,
        "true_pair_index": true_pair_index,
        "true_pair": list(ceiling.ALL_PAIRS[true_pair_index]),
        "hypothesis_pair_index": hypothesis_pair_index,
        "hypothesis_pair": list(pair),
        "evaluation_fixture_index": EVAL_FIXTURE_INDEX,
        "fixture_observed_sha256": hashlib.sha256(
            fixture["observed"].encode("ascii")).hexdigest(),
        "depth": DEPTH, "path_count": len(paths),
        "budgets": {"restarts": RESTARTS, "iterations": ITERATIONS,
                    "seed": BOARD_SEED},
        "observable": {
            "primary_selector": summary["best"],
            "primary_selector_definition":
                "maximum unrestricted-board normalized score over all 19P4 paths",
            "score_distribution": summary,
            "top_paths": [{"path": paths[index].tolist(),
                           "score": float(scores[index])}
                          for index in ranked],
        },
        "audit_only": {
            "true_pair": true_pair_index == hypothesis_pair_index,
            "true_fragment_recovery": front.true_record(
                paths, scores, truth, DEPTH),
        },
        "wall_seconds": time.monotonic() - began,
    }


def cell_path(root: Path, true_pair_index: int,
              hypothesis_pair_index: int) -> Path:
    return Path(root) / f"true_{true_pair_index:02d}" / (
        f"hypothesis_{hypothesis_pair_index:02d}.json")


def expected_identity(true_pair_index: int,
                      hypothesis_pair_index: int) -> dict:
    fixture = ceiling.make_fixture(true_pair_index, EVAL_FIXTURE_INDEX)
    return {
        "phase": "505C", "status": "development_shallow_cell_complete",
        "faed_scored": False, "holdout_consumed": False,
        "true_pair_index": true_pair_index,
        "true_pair": list(ceiling.ALL_PAIRS[true_pair_index]),
        "hypothesis_pair_index": hypothesis_pair_index,
        "hypothesis_pair": list(ceiling.ALL_PAIRS[hypothesis_pair_index]),
        "evaluation_fixture_index": EVAL_FIXTURE_INDEX,
        "fixture_observed_sha256": hashlib.sha256(
            fixture["observed"].encode("ascii")).hexdigest(),
        "depth": DEPTH,
        "path_count": math.prod(range(WIDTH - DEPTH + 1, WIDTH + 1)),
        "budgets": {"restarts": RESTARTS, "iterations": ITERATIONS,
                    "seed": BOARD_SEED},
    }


def validate_cell(record: dict, true_pair_index: int,
                  hypothesis_pair_index: int) -> dict:
    for key, value in expected_identity(
            true_pair_index, hypothesis_pair_index).items():
        if record.get(key) != value:
            raise RuntimeError(f"Phase-505C checkpoint mismatch: {key}")
    selector = record.get("observable", {}).get("primary_selector")
    if not isinstance(selector, (int, float)) or not math.isfinite(selector):
        raise RuntimeError("Phase-505C checkpoint has invalid selector")
    return record


def rank_row(records: list[dict], true_pair_index: int) -> dict:
    expected = set(range(len(ceiling.ALL_PAIRS)))
    if {record["hypothesis_pair_index"] for record in records} != expected:
        raise RuntimeError("Phase-505C row is incomplete")
    ranked = sorted(records, key=lambda record: (
        -record["observable"]["primary_selector"],
        record["hypothesis_pair_index"]))
    true = next(record for record in ranked
                if record["hypothesis_pair_index"] == true_pair_index)
    wrong = next(record for record in ranked
                 if record["hypothesis_pair_index"] != true_pair_index)
    return {
        "true_pair_index": true_pair_index,
        "true_pair": list(ceiling.ALL_PAIRS[true_pair_index]),
        "true_pair_rank": ranked.index(true) + 1,
        "true_pair_score": true["observable"]["primary_selector"],
        "best_wrong_pair_score": wrong["observable"]["primary_selector"],
        "true_minus_best_wrong": (true["observable"]["primary_selector"] -
                                  wrong["observable"]["primary_selector"]),
        "ranked_pair_indices": [record["hypothesis_pair_index"]
                                for record in ranked],
        "cell_wall_seconds": sum(record["wall_seconds"]
                                 for record in records),
    }


def run_pilot(root: Path = DEFAULT_WORK_DIR) -> dict:
    verify_lock()
    root = Path(root)
    paths = path_universe()
    rows = []
    for true_pair_index in PILOT_TRUE_PAIR_INDICES:
        cells = []
        for hypothesis_pair_index in range(len(ceiling.ALL_PAIRS)):
            path = cell_path(root, true_pair_index, hypothesis_pair_index)
            if path.exists():
                record = validate_cell(json.loads(path.read_text()),
                                       true_pair_index,
                                       hypothesis_pair_index)
            else:
                record = run_cell(true_pair_index, hypothesis_pair_index,
                                  paths)
                atomic_json(path, record)
            cells.append(record)
            atomic_json(root / "progress.json", {
                "phase": "505C", "status": "pilot_in_progress",
                "faed_scored": False, "holdout_consumed": False,
                "completed_cells": sum(
                    cell_path(root, row, hypothesis).is_file()
                    for row in PILOT_TRUE_PAIR_INDICES
                    for hypothesis in range(len(ceiling.ALL_PAIRS))),
                "total_cells": (len(PILOT_TRUE_PAIR_INDICES) *
                                len(ceiling.ALL_PAIRS)),
                "execution_lock_sha256": sha256_file(LOCK_PATH),
            })
        row = rank_row(cells, true_pair_index)
        rows.append(row)
        atomic_json(root / f"true_{true_pair_index:02d}" / "row.json", row)
    result = {
        "phase": "505C", "status": "development_shallow_pilot_complete",
        "faed_scored": False, "holdout_consumed": False,
        "execution_lock_sha256": sha256_file(LOCK_PATH),
        "true_pair_indices": list(PILOT_TRUE_PAIR_INDICES),
        "cell_count": len(PILOT_TRUE_PAIR_INDICES) * len(ceiling.ALL_PAIRS),
        "top1": sum(row["true_pair_rank"] == 1 for row in rows),
        "top3": sum(row["true_pair_rank"] <= 3 for row in rows),
        "rows": rows,
    }
    atomic_json(root / "result.json", result)
    return result


def describe() -> dict:
    return {
        "phase": "505C", "status": "implementation_not_locked",
        "faed_scored": False, "holdout_consumed": False,
        "width": WIDTH, "depth": DEPTH,
        "path_count": math.prod(range(WIDTH - DEPTH + 1, WIDTH + 1)),
        "pilot_true_pair_indices": list(PILOT_TRUE_PAIR_INDICES),
        "pair_count": len(ceiling.ALL_PAIRS),
        "pilot_cells": len(PILOT_TRUE_PAIR_INDICES) * len(ceiling.ALL_PAIRS),
        "budgets": {"restarts": RESTARTS, "iterations": ITERATIONS,
                    "seed": BOARD_SEED},
        "lock_present": LOCK_PATH.is_file(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--describe", action="store_true")
    group.add_argument("--verify-lock", action="store_true")
    group.add_argument("--run-pilot", action="store_true")
    parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK_DIR)
    args = parser.parse_args()
    if args.describe:
        result = describe()
    elif args.verify_lock:
        result = verify_lock()
    else:
        result = run_pilot(args.work_dir)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
