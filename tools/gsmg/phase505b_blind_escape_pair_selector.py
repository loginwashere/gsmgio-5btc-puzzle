#!/usr/bin/env python3
"""Phase 505B development implementation: blind escape-pair selector.

The selector is synthetic-only.  It trains one pair-balanced invariant model
from logical fixture 0 for every escape pair and evaluates logical fixture 1
under all 36 assumed pairs.  The planted order and true pair are used only for
post-hoc recovery diagnostics; they never enter candidate scoring or pruning.

The expensive development matrix is deliberately not execution-locked yet.
Run the frozen three-row benchmark first, review its timing and recovery, then
write a separate 505B protocol/lock before consuming a holdout or scoring FAED.
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
DEFAULT_WORK_DIR = REPO_ROOT / "_work" / "phase505b" / "development"
PHASE505_PROTOCOL = (REPO_ROOT / "doc" / "Brainstorms" /
                     "2026-09-14 - Phase 505 Escape-Pair Identifiability Protocol.md")
IMPLEMENTATION_NOTE = (REPO_ROOT / "doc" / "Brainstorms" /
                       "2026-09-14 - Phase 505B Blind Escape-Pair Selector Implementation Note.md")
BENCHMARK_LOCK_PATH = SCRIPT_DIR / "phase505b_benchmark_lock.json"
MATRIX_LOCK_PATH = SCRIPT_DIR / "phase505b_matrix_lock.json"
CEILING_RESULT = REPO_ROOT / "_work" / "phase505" / "ceiling_result.json"

WIDTH = 19
TRAIN_FIXTURE_INDEX = 0
EVAL_FIXTURE_INDEX = 1
TRAIN_SEED = 0x505B001
BOARD_SEED = 0x505B002
NEGATIVE_RATIO = 2
BENCHMARK_TRUE_PAIR_INDICES = (0, 17, 35)

# This is a development schedule, not a locked scientific budget.  It mirrors
# the existing width-19 front stage so the benchmark measures the real cost of
# a cell rather than a toy surrogate.
SCREEN_SCHEDULE = dict(front.FRONT_SCHEDULE)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical_json_sha256(value) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":")
    ).encode("ascii")).hexdigest()


def atomic_json(path: Path, value: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def schedule_sha256() -> str:
    return canonical_json_sha256(SCREEN_SCHEDULE)


def common_lock_payload() -> dict:
    dependencies = (base, prefix, front, variants, ceiling)
    return {
        "script_sha256": sha256_file(Path(__file__)),
        "phase505_protocol_sha256": sha256_file(PHASE505_PROTOCOL),
        "implementation_note_sha256": sha256_file(IMPLEMENTATION_NOTE),
        "dependencies_sha256": {
            str(Path(module.__file__).relative_to(REPO_ROOT)):
                sha256_file(Path(module.__file__))
            for module in dependencies
        },
        "phase505_fixture_manifest_sha256": sha256_file(
            ceiling.DEFAULT_MANIFEST),
        "phase505a_ceiling_result_sha256": sha256_file(CEILING_RESULT),
        "unrestricted_board_binary_sha256": sha256_file(
            variants.UNRESTRICTED_BINARY),
        "pair_count": len(ceiling.ALL_PAIRS),
        "training_fixture_index": TRAIN_FIXTURE_INDEX,
        "evaluation_fixture_index": EVAL_FIXTURE_INDEX,
        "training_seed": TRAIN_SEED,
        "board_seed": BOARD_SEED,
        "negative_ratio": NEGATIVE_RATIO,
        "schedule": SCREEN_SCHEDULE,
        "schedule_sha256": schedule_sha256(),
        "primary_selector":
            "maximum refined depth-7 unrestricted-board normalized score",
        "faed_scored": False,
        "holdout_consumed": False,
    }


def expected_benchmark_lock_payload() -> dict:
    return {
        "phase": "505B-benchmark",
        "status": "execution_lock",
        **common_lock_payload(),
        "true_pair_indices": list(BENCHMARK_TRUE_PAIR_INDICES),
        "cell_count": (len(BENCHMARK_TRUE_PAIR_INDICES) *
                       len(ceiling.ALL_PAIRS)),
    }


def expected_matrix_lock_payload(work_dir: Path = DEFAULT_WORK_DIR) -> dict:
    benchmark = Path(work_dir) / "benchmark_summary.json"
    if not benchmark.is_file():
        raise RuntimeError(
            "Phase-505B benchmark summary is absent; matrix lock is premature")
    return {
        "phase": "505B-development-matrix",
        "status": "execution_lock",
        **common_lock_payload(),
        "benchmark_lock_sha256": sha256_file(BENCHMARK_LOCK_PATH),
        "benchmark_summary_sha256": sha256_file(benchmark),
        "true_pair_indices": list(range(len(ceiling.ALL_PAIRS))),
        "cell_count": len(ceiling.ALL_PAIRS) ** 2,
    }


def verify_exact_lock(path: Path, expected: dict, label: str) -> dict:
    if not Path(path).is_file():
        raise RuntimeError(f"Phase-505B {label} execution lock is absent")
    actual = json.loads(Path(path).read_text())
    if actual != expected:
        raise RuntimeError(f"Phase-505B {label} execution lock mismatch")
    return actual


def verify_benchmark_lock() -> dict:
    return verify_exact_lock(BENCHMARK_LOCK_PATH,
                             expected_benchmark_lock_payload(), "benchmark")


def verify_matrix_lock(work_dir: Path = DEFAULT_WORK_DIR) -> dict:
    # The final matrix is downstream of the exact benchmark lock as well as
    # its result; verify both rather than merely hashing an untrusted file.
    verify_benchmark_lock()
    return verify_exact_lock(
        MATRIX_LOCK_PATH, expected_matrix_lock_payload(work_dir), "matrix")


def model_payload(models: dict) -> dict:
    records = {}
    for depth, model in sorted(models.items()):
        records[str(depth)] = {
            "mean": np.asarray(model.mean, dtype=np.float64).tolist(),
            "scale": np.asarray(model.scale, dtype=np.float64).tolist(),
            "weight": np.asarray(model.weight, dtype=np.float64).tolist(),
            "intercept": float(model.intercept),
        }
    return {
        "kind": "pair_balanced_centroid_prefix_models",
        "width": WIDTH,
        "depths": sorted(models),
        "true_pair_indices": list(range(len(ceiling.ALL_PAIRS))),
        "training_fixture_index": TRAIN_FIXTURE_INDEX,
        "negative_ratio": NEGATIVE_RATIO,
        "seed": TRAIN_SEED,
        "models": records,
    }


def train_pair_balanced_models() -> dict:
    """Fit one shared model per depth with equal input from every pair."""
    fixtures = [ceiling.make_fixture(pair_index, TRAIN_FIXTURE_INDEX)
                for pair_index in range(len(ceiling.ALL_PAIRS))]
    models = {}
    for depth in range(prefix.START_DEPTH,
                       SCREEN_SCHEDULE["switch_depth"] + 1):
        positives, negatives = [], []
        for pair_index, fixture in enumerate(fixtures):
            blocks = prefix.blocks_from_observed(fixture)
            pair = tuple(fixture["pair"])
            truth = prefix.order_to_sequence(fixture["order"])
            true_paths = {
                tuple(truth[start:start + depth])
                for start in range(WIDTH - depth + 1)
            }
            positives.extend(prefix.prefix_features(blocks, path, pair)
                             for path in sorted(true_paths))
            rng = base.PCG32(base.derive_seed(
                TRAIN_SEED, pair_index, depth, TRAIN_FIXTURE_INDEX))
            made = set()
            target = NEGATIVE_RATIO * len(true_paths)
            while len(made) < target:
                path = tuple(rng.permutation(WIDTH)[:depth])
                if path not in true_paths:
                    made.add(path)
            negatives.extend(prefix.prefix_features(blocks, path, pair)
                             for path in sorted(made))
        models[depth] = prefix.fit_centroid(positives, negatives)
    return models


def true_diagnostic(paths, scores, fixture: dict, depth: int) -> dict:
    truth = prefix.order_to_sequence(fixture["order"])
    return front.true_record(paths, scores, truth, depth)


def score_summary(scores) -> dict:
    values = np.asarray(scores, dtype=np.float64)
    finite = values[np.isfinite(values)]
    if not len(finite):
        return {
            "count": len(values), "finite": 0, "best": None,
            "mean": None, "standard_deviation": None,
            "quantiles": None, "best_minus_q99": None,
        }
    quantiles = np.quantile(finite, (0.5, 0.9, 0.99, 0.999))
    best = float(np.max(finite))
    return {
        "count": len(values),
        "finite": len(finite),
        "best": best,
        "mean": float(np.mean(finite)),
        "standard_deviation": float(np.std(finite)),
        "quantiles": {
            "q50": float(quantiles[0]), "q90": float(quantiles[1]),
            "q99": float(quantiles[2]), "q999": float(quantiles[3]),
        },
        "best_minus_q99": best - float(quantiles[2]),
    }


def score_unrestricted(paths, blocks, pair, quad, restarts, iterations):
    return front.constrained_multistart(
        paths, blocks, pair, quad, restarts, iterations,
        binary=variants.UNRESTRICTED_BINARY, seed=BOARD_SEED)


def run_blind_cell(true_pair_index: int, hypothesis_pair_index: int,
                   models: dict, model_manifest_sha256: str) -> dict:
    """Run one blind matrix cell and return observable plus audit fields."""
    if not 0 <= true_pair_index < len(ceiling.ALL_PAIRS):
        raise ValueError("true-pair index out of range")
    if not 0 <= hypothesis_pair_index < len(ceiling.ALL_PAIRS):
        raise ValueError("hypothesis-pair index out of range")
    fixture = ceiling.make_fixture(true_pair_index, EVAL_FIXTURE_INDEX)
    pair = ceiling.ALL_PAIRS[hypothesis_pair_index]
    blocks = prefix.blocks_from_observed(fixture)
    quad, _ = base.load_language_model()
    began = time.monotonic()
    invariant_stages = []

    paths = front.initial_paths()
    scores = front.score_invariant(paths, blocks, pair,
                                   models[prefix.START_DEPTH])
    for depth in range(prefix.START_DEPTH,
                       SCREEN_SCHEDULE["switch_depth"] + 1):
        capacity = (SCREEN_SCHEDULE["keep_preboard"]
                    if depth == SCREEN_SCHEDULE["switch_depth"]
                    else SCREEN_SCHEDULE["keep_penultimate"]
                    if depth == SCREEN_SCHEDULE["switch_depth"] - 1
                    else SCREEN_SCHEDULE["keep_early"])
        before = score_summary(scores)
        diagnostic_before = true_diagnostic(paths, scores, fixture, depth)
        paths, scores, unique = front.select_diverse(paths, scores, capacity)
        invariant_stages.append({
            "depth": depth, "generated_unique": unique,
            "observable_before_selection": before,
            "observable_after_selection": score_summary(scores),
            "audit_true_before_selection": diagnostic_before,
            "audit_true_after_selection": true_diagnostic(
                paths, scores, fixture, depth),
        })
        if depth < SCREEN_SCHEDULE["switch_depth"]:
            paths = front.expand_bidirectional(paths)
            scores = front.score_invariant(
                paths, blocks, pair, models[depth + 1])

    board6 = score_unrestricted(
        paths, blocks, pair, quad, SCREEN_SCHEDULE["coarse_restarts"],
        SCREEN_SCHEDULE["coarse_iterations"])
    board6_observable_before = score_summary(board6)
    board6_audit_before = true_diagnostic(paths, board6, fixture, 6)
    paths, board6, unique6 = front.select_diverse(
        paths, board6, SCREEN_SCHEDULE["keep_board"])
    board6_observable_after = score_summary(board6)
    board6_audit_after = true_diagnostic(paths, board6, fixture, 6)

    paths7 = front.expand_bidirectional(paths)
    coarse7 = score_unrestricted(
        paths7, blocks, pair, quad, SCREEN_SCHEDULE["coarse_restarts"],
        SCREEN_SCHEDULE["coarse_iterations"])
    coarse7_observable_before = score_summary(coarse7)
    coarse7_audit_before = true_diagnostic(paths7, coarse7, fixture, 7)
    paths7, coarse7, unique7 = front.select_diverse(
        paths7, coarse7, SCREEN_SCHEDULE["depth7_coarse_keep"])
    coarse7_observable_after = score_summary(coarse7)
    coarse7_audit_after = true_diagnostic(paths7, coarse7, fixture, 7)

    refined7 = score_unrestricted(
        paths7, blocks, pair, quad, SCREEN_SCHEDULE["refine_restarts"],
        SCREEN_SCHEDULE["refine_iterations"])
    refine_observable_before = score_summary(refined7)
    refine_audit_before = true_diagnostic(paths7, refined7, fixture, 7)
    paths7, refined7, refine_unique = front.select_diverse(
        paths7, refined7, SCREEN_SCHEDULE["depth7_refine_keep"])
    refine_observable_after = score_summary(refined7)
    refine_audit_after = true_diagnostic(paths7, refined7, fixture, 7)
    observable = {
        "primary_selector": float(np.max(refined7)),
        "primary_selector_definition":
            "maximum refined depth-7 unrestricted-board normalized score",
        "depth6_before_selection": board6_observable_before,
        "depth6_after_selection": board6_observable_after,
        "depth7_coarse_before_selection": coarse7_observable_before,
        "depth7_coarse_after_selection": coarse7_observable_after,
        "depth7_refine_before_selection": refine_observable_before,
        "depth7_refine_after_selection": refine_observable_after,
    }
    audit = {
        "true_pair": true_pair_index == hypothesis_pair_index,
        "invariant_stages": invariant_stages,
        "depth6_before_selection": board6_audit_before,
        "depth6_after_selection": board6_audit_after,
        "depth7_coarse_before_selection": coarse7_audit_before,
        "depth7_coarse_after_selection": coarse7_audit_after,
        "depth7_refine_before_selection": refine_audit_before,
        "depth7_refine_after_selection": refine_audit_after,
    }
    return {
        "phase": "505B",
        "status": "development_blind_cell_complete",
        "faed_scored": False,
        "holdout_consumed": False,
        "true_pair_index": true_pair_index,
        "true_pair": list(ceiling.ALL_PAIRS[true_pair_index]),
        "hypothesis_pair_index": hypothesis_pair_index,
        "hypothesis_pair": list(pair),
        "evaluation_fixture_index": EVAL_FIXTURE_INDEX,
        "fixture_observed_sha256": hashlib.sha256(
            fixture["observed"].encode("ascii")).hexdigest(),
        "model_manifest_sha256": model_manifest_sha256,
        "schedule_sha256": schedule_sha256(),
        "generated_unique": {
            "depth6_board": unique6, "depth7_coarse": unique7,
            "depth7_refine": refine_unique,
        },
        "observable": observable,
        "audit_only": audit,
        "wall_seconds": time.monotonic() - began,
    }


def expected_cell_identity(true_pair_index: int, hypothesis_pair_index: int,
                           model_manifest_sha256: str) -> dict:
    fixture = ceiling.make_fixture(true_pair_index, EVAL_FIXTURE_INDEX)
    return {
        "phase": "505B", "status": "development_blind_cell_complete",
        "faed_scored": False, "holdout_consumed": False,
        "true_pair_index": true_pair_index,
        "true_pair": list(ceiling.ALL_PAIRS[true_pair_index]),
        "hypothesis_pair_index": hypothesis_pair_index,
        "hypothesis_pair": list(ceiling.ALL_PAIRS[hypothesis_pair_index]),
        "evaluation_fixture_index": EVAL_FIXTURE_INDEX,
        "fixture_observed_sha256": hashlib.sha256(
            fixture["observed"].encode("ascii")).hexdigest(),
        "model_manifest_sha256": model_manifest_sha256,
        "schedule_sha256": schedule_sha256(),
    }


def validate_cell(record: dict, true_pair_index: int,
                  hypothesis_pair_index: int,
                  model_manifest_sha256: str) -> dict:
    expected = expected_cell_identity(
        true_pair_index, hypothesis_pair_index, model_manifest_sha256)
    for key, value in expected.items():
        if record.get(key) != value:
            raise RuntimeError(f"Phase-505B cell mismatch: {key}")
    selector = record.get("observable", {}).get("primary_selector")
    if not isinstance(selector, (int, float)) or not math.isfinite(selector):
        raise RuntimeError("Phase-505B cell has invalid primary selector")
    return record


def cell_path(root: Path, true_pair_index: int,
              hypothesis_pair_index: int) -> Path:
    return Path(root) / f"true_{true_pair_index:02d}" / (
        f"hypothesis_{hypothesis_pair_index:02d}.json")


def run_or_resume_cell(root: Path, true_pair_index: int,
                       hypothesis_pair_index: int, models: dict,
                       model_manifest_sha256: str) -> dict:
    path = cell_path(root, true_pair_index, hypothesis_pair_index)
    if path.exists():
        return validate_cell(json.loads(path.read_text()), true_pair_index,
                             hypothesis_pair_index, model_manifest_sha256)
    record = run_blind_cell(true_pair_index, hypothesis_pair_index, models,
                            model_manifest_sha256)
    atomic_json(path, record)
    return validate_cell(record, true_pair_index, hypothesis_pair_index,
                         model_manifest_sha256)


def rank_row(records: list[dict], true_pair_index: int) -> dict:
    if {r["hypothesis_pair_index"] for r in records} != set(
            range(len(ceiling.ALL_PAIRS))):
        raise RuntimeError("Phase-505B row does not contain all 36 pairs")
    ranked = sorted(records, key=lambda record: (
        -record["observable"]["primary_selector"],
        record["hypothesis_pair_index"]))
    true_rank = next(index for index, record in enumerate(ranked, 1)
                     if record["hypothesis_pair_index"] == true_pair_index)
    true_score = next(record["observable"]["primary_selector"]
                      for record in ranked
                      if record["hypothesis_pair_index"] == true_pair_index)
    best_wrong = next(record["observable"]["primary_selector"]
                      for record in ranked
                      if record["hypothesis_pair_index"] != true_pair_index)
    return {
        "true_pair_index": true_pair_index,
        "true_pair": list(ceiling.ALL_PAIRS[true_pair_index]),
        "true_pair_rank": true_rank,
        "true_pair_score": true_score,
        "best_wrong_pair_score": best_wrong,
        "true_minus_best_wrong": true_score - best_wrong,
        "ranked_pair_indices": [r["hypothesis_pair_index"] for r in ranked],
        "cell_wall_seconds": sum(r["wall_seconds"] for r in records),
    }


def run_rows(true_pair_indices, root: Path = DEFAULT_WORK_DIR,
             summary_name: str = "summary.json") -> dict:
    true_pair_indices = tuple(int(index) for index in true_pair_indices)
    if len(set(true_pair_indices)) != len(true_pair_indices):
        raise ValueError("true-pair rows must be unique")
    if any(not 0 <= index < len(ceiling.ALL_PAIRS)
           for index in true_pair_indices):
        raise ValueError("true-pair row outside pair universe")
    root = Path(root)
    models = train_pair_balanced_models()
    payload = model_payload(models)
    model_path = root / "model_manifest.json"
    if model_path.exists():
        if json.loads(model_path.read_text()) != payload:
            raise RuntimeError("Phase-505B model manifest mismatch")
    else:
        atomic_json(model_path, payload)
    model_manifest_sha256 = sha256_file(model_path)
    rows = []
    for true_pair_index in true_pair_indices:
        records = []
        for hypothesis_pair_index in range(len(ceiling.ALL_PAIRS)):
            records.append(run_or_resume_cell(
                root, true_pair_index, hypothesis_pair_index, models,
                model_manifest_sha256))
            atomic_json(root / "progress.json", {
                "phase": "505B", "status": "development_in_progress",
                "faed_scored": False, "holdout_consumed": False,
                "requested_true_pair_indices": list(true_pair_indices),
                "completed_cells": sum(
                    cell_path(root, row, hypothesis).is_file()
                    for row in true_pair_indices
                    for hypothesis in range(len(ceiling.ALL_PAIRS))),
                "total_cells": len(true_pair_indices) * len(ceiling.ALL_PAIRS),
                "model_manifest_sha256": model_manifest_sha256,
                "schedule_sha256": schedule_sha256(),
            })
        row = rank_row(records, true_pair_index)
        rows.append(row)
        atomic_json(root / f"true_{true_pair_index:02d}" / "row.json", row)
    summary = {
        "phase": "505B",
        "status": "development_blind_rows_complete",
        "faed_scored": False,
        "holdout_consumed": False,
        "requested_true_pair_indices": list(true_pair_indices),
        "cell_count": len(true_pair_indices) * len(ceiling.ALL_PAIRS),
        "model_manifest_sha256": model_manifest_sha256,
        "schedule": SCREEN_SCHEDULE,
        "schedule_sha256": schedule_sha256(),
        "top1": sum(row["true_pair_rank"] == 1 for row in rows),
        "top3": sum(row["true_pair_rank"] <= 3 for row in rows),
        "rows": rows,
    }
    atomic_json(root / summary_name, summary)
    return summary


def run_benchmark(root: Path = DEFAULT_WORK_DIR) -> dict:
    verify_benchmark_lock()
    return run_rows(BENCHMARK_TRUE_PAIR_INDICES, root,
                    summary_name="benchmark_summary.json")


def run_development_matrix(root: Path = DEFAULT_WORK_DIR) -> dict:
    verify_matrix_lock(root)
    return run_rows(range(len(ceiling.ALL_PAIRS)), root,
                    summary_name="development_matrix_summary.json")


def describe() -> dict:
    return {
        "phase": "505B",
        "status": "development_implementation_tested_not_locked",
        "faed_scored": False,
        "holdout_consumed": False,
        "training": {
            "pair_count": len(ceiling.ALL_PAIRS),
            "fixture_index": TRAIN_FIXTURE_INDEX,
            "negative_ratio": NEGATIVE_RATIO,
            "depths": list(range(prefix.START_DEPTH,
                                 SCREEN_SCHEDULE["switch_depth"] + 1)),
        },
        "evaluation_fixture_index": EVAL_FIXTURE_INDEX,
        "benchmark_true_pair_indices": list(BENCHMARK_TRUE_PAIR_INDICES),
        "benchmark_cells": (len(BENCHMARK_TRUE_PAIR_INDICES) *
                            len(ceiling.ALL_PAIRS)),
        "full_development_cells": len(ceiling.ALL_PAIRS) ** 2,
        "primary_selector":
            "maximum refined depth-7 unrestricted-board normalized score",
        "schedule": SCREEN_SCHEDULE,
        "schedule_sha256": schedule_sha256(),
        "checkpoint_granularity": "one atomic JSON per matrix cell",
        "execution_lock_issued": False,
        "benchmark_lock_present": BENCHMARK_LOCK_PATH.is_file(),
        "matrix_lock_present": MATRIX_LOCK_PATH.is_file(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--describe", action="store_true")
    group.add_argument("--verify-benchmark-lock", action="store_true")
    group.add_argument("--verify-matrix-lock", action="store_true")
    group.add_argument("--benchmark", action="store_true")
    group.add_argument("--run-development-matrix", action="store_true")
    parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK_DIR)
    args = parser.parse_args()
    if args.describe:
        result = describe()
    elif args.verify_benchmark_lock:
        result = verify_benchmark_lock()
    elif args.verify_matrix_lock:
        result = verify_matrix_lock(args.work_dir)
    elif args.benchmark:
        result = run_benchmark(args.work_dir)
    else:
        result = run_development_matrix(args.work_dir)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
