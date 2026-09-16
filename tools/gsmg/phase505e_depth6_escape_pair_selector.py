#!/usr/bin/env python3
"""Phase 505E: depth-6-only blind escape-pair selector development lane."""
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
import phase505b_blind_escape_pair_selector as deep


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
PROTOCOL = (REPO_ROOT / "doc" / "Brainstorms" /
            "2026-09-14 - Phase 505E Depth6 Escape-Pair Selector Protocol.md")
TIMING_LOCK = SCRIPT_DIR / "phase505e_timing_lock.json"
PILOT_LOCK = SCRIPT_DIR / "phase505e_pilot_lock.json"
DEFAULT_WORK_DIR = REPO_ROOT / "_work" / "phase505e"
TIMING_CELL = (0, 0)
PILOT_TRUE_PAIR_INDICES = (0, 17, 35)
MAX_PILOT_PROJECTED_SECONDS = 2 * 60 * 60
TOP_PATHS_RECORDED = 32


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_json(path: Path, value: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def model_payload(models: dict) -> dict:
    return deep.model_payload(models)


def model_sha256(models: dict) -> str:
    return hashlib.sha256(json.dumps(
        model_payload(models), sort_keys=True, separators=(",", ":")
    ).encode("ascii")).hexdigest()


def common_lock_payload() -> dict:
    dependencies = (base, prefix, front, variants, ceiling, deep)
    return {
        "protocol_sha256": sha256_file(PROTOCOL),
        "script_sha256": sha256_file(Path(__file__)),
        "dependencies_sha256": {
            str(Path(module.__file__).relative_to(REPO_ROOT)):
                sha256_file(Path(module.__file__)) for module in dependencies
        },
        "phase505_fixture_manifest_sha256": sha256_file(
            ceiling.DEFAULT_MANIFEST),
        "phase505a_result_sha256": sha256_file(
            REPO_ROOT / "_work" / "phase505" / "ceiling_result.json"),
        "phase505b_first_cell_sha256": sha256_file(
            REPO_ROOT / "_work" / "phase505b" / "development" /
            "true_00" / "hypothesis_00.json"),
        "phase505d_result_sha256": sha256_file(
            REPO_ROOT / "_work" / "phase505d" / "result.json"),
        "unrestricted_board_binary_sha256": sha256_file(
            variants.UNRESTRICTED_BINARY),
        "width": front.WIDTH,
        "depth": deep.SCREEN_SCHEDULE["switch_depth"],
        "training_fixture_index": deep.TRAIN_FIXTURE_INDEX,
        "evaluation_fixture_index": deep.EVAL_FIXTURE_INDEX,
        "training_seed": deep.TRAIN_SEED,
        "negative_ratio": deep.NEGATIVE_RATIO,
        "front_schedule": deep.SCREEN_SCHEDULE,
        "primary_selector":
            "maximum depth-6 unrestricted-board normalized score",
        "faed_scored": False, "holdout_consumed": False,
    }


def expected_timing_lock() -> dict:
    return {
        "phase": "505E-timing", "status": "execution_lock",
        **common_lock_payload(),
        "true_pair_index": TIMING_CELL[0],
        "hypothesis_pair_index": TIMING_CELL[1],
        "cell_count": 1,
    }


def expected_pilot_lock(work_dir: Path = DEFAULT_WORK_DIR) -> dict:
    timing = Path(work_dir) / "timing_cell.json"
    if not timing.is_file():
        raise RuntimeError("Phase-505E timing result is absent")
    record = json.loads(timing.read_text())
    projected = record.get("projected_pilot_seconds")
    if not isinstance(projected, (int, float)) or not math.isfinite(projected):
        raise RuntimeError("Phase-505E timing projection is invalid")
    if projected > MAX_PILOT_PROJECTED_SECONDS:
        raise RuntimeError("Phase-505E timing projection exceeds cost gate")
    return {
        "phase": "505E-pilot", "status": "execution_lock",
        **common_lock_payload(),
        "timing_lock_sha256": sha256_file(TIMING_LOCK),
        "timing_result_sha256": sha256_file(timing),
        "maximum_projected_seconds": MAX_PILOT_PROJECTED_SECONDS,
        "true_pair_indices": list(PILOT_TRUE_PAIR_INDICES),
        "hypothesis_pair_indices": list(range(len(ceiling.ALL_PAIRS))),
        "cell_count": (len(PILOT_TRUE_PAIR_INDICES) *
                       len(ceiling.ALL_PAIRS)),
    }


def verify_exact_lock(path: Path, expected: dict, label: str) -> dict:
    if not Path(path).is_file():
        raise RuntimeError(f"Phase-505E {label} execution lock is absent")
    actual = json.loads(Path(path).read_text())
    if actual != expected:
        raise RuntimeError(f"Phase-505E {label} execution lock mismatch")
    return actual


def verify_timing_lock() -> dict:
    return verify_exact_lock(TIMING_LOCK, expected_timing_lock(), "timing")


def verify_pilot_lock(work_dir: Path = DEFAULT_WORK_DIR) -> dict:
    verify_timing_lock()
    return verify_exact_lock(PILOT_LOCK, expected_pilot_lock(work_dir), "pilot")


def invariant_to_depth6(fixture: dict, hypothesis_pair_index: int,
                        models: dict):
    blocks = prefix.blocks_from_observed(fixture)
    pair = ceiling.ALL_PAIRS[hypothesis_pair_index]
    paths = front.initial_paths()
    scores = front.score_invariant(paths, blocks, pair,
                                   models[prefix.START_DEPTH])
    stages = []
    for depth in range(prefix.START_DEPTH,
                       deep.SCREEN_SCHEDULE["switch_depth"] + 1):
        capacity = (deep.SCREEN_SCHEDULE["keep_preboard"]
                    if depth == deep.SCREEN_SCHEDULE["switch_depth"]
                    else deep.SCREEN_SCHEDULE["keep_penultimate"]
                    if depth == deep.SCREEN_SCHEDULE["switch_depth"] - 1
                    else deep.SCREEN_SCHEDULE["keep_early"])
        before = deep.score_summary(scores)
        paths, scores, unique = front.select_diverse(paths, scores, capacity)
        stages.append({"depth": depth, "generated_unique": unique,
                       "observable_before_selection": before,
                       "observable_after_selection": deep.score_summary(scores)})
        if depth < deep.SCREEN_SCHEDULE["switch_depth"]:
            paths = front.expand_bidirectional(paths)
            scores = front.score_invariant(paths, blocks, pair,
                                           models[depth + 1])
    return paths, blocks, pair, stages


def best_path_window_count(blocks, pair, path) -> int:
    rows = front.canonical_token_rows(blocks, pair, path)
    return sum(max(0, len(row) - 3) for row in rows)


def run_cell(true_pair_index: int, hypothesis_pair_index: int,
             models: dict) -> dict:
    fixture = ceiling.make_fixture(true_pair_index, deep.EVAL_FIXTURE_INDEX)
    began = time.monotonic()
    paths, blocks, pair, stages = invariant_to_depth6(
        fixture, hypothesis_pair_index, models)
    quad, _ = base.load_language_model()
    scores = front.constrained_multistart(
        paths, blocks, pair, quad,
        deep.SCREEN_SCHEDULE["coarse_restarts"],
        deep.SCREEN_SCHEDULE["coarse_iterations"],
        binary=variants.UNRESTRICTED_BINARY, seed=deep.BOARD_SEED)
    ranked = front.ranked_indices(paths, scores)
    top = ranked[:TOP_PATHS_RECORDED]
    truth = prefix.order_to_sequence(fixture["order"])
    return {
        "phase": "505E", "status": "development_depth6_cell_complete",
        "faed_scored": False, "holdout_consumed": False,
        "true_pair_index": true_pair_index,
        "true_pair": list(ceiling.ALL_PAIRS[true_pair_index]),
        "hypothesis_pair_index": hypothesis_pair_index,
        "hypothesis_pair": list(pair),
        "fixture_observed_sha256": hashlib.sha256(
            fixture["observed"].encode("ascii")).hexdigest(),
        "model_sha256": model_sha256(models),
        "invariant_stages": stages,
        "observable": {
            "primary_selector": float(scores[ranked[0]]),
            "primary_selector_definition":
                "maximum depth-6 unrestricted-board normalized score",
            "score_distribution": deep.score_summary(scores),
            "best_path_window_count": best_path_window_count(
                blocks, pair, paths[ranked[0]]),
            "top_paths": [{"path": paths[index].tolist(),
                           "score": float(scores[index]),
                           "quadgram_windows": best_path_window_count(
                               blocks, pair, paths[index])}
                          for index in top],
        },
        "audit_only": {
            "true_pair": true_pair_index == hypothesis_pair_index,
            "true_fragment_recovery": front.true_record(
                paths, scores, truth, 6),
        },
        "wall_seconds": time.monotonic() - began,
    }


def expected_identity(true_pair_index: int, hypothesis_pair_index: int,
                      models: dict) -> dict:
    fixture = ceiling.make_fixture(true_pair_index, deep.EVAL_FIXTURE_INDEX)
    return {
        "phase": "505E", "status": "development_depth6_cell_complete",
        "faed_scored": False, "holdout_consumed": False,
        "true_pair_index": true_pair_index,
        "true_pair": list(ceiling.ALL_PAIRS[true_pair_index]),
        "hypothesis_pair_index": hypothesis_pair_index,
        "hypothesis_pair": list(ceiling.ALL_PAIRS[hypothesis_pair_index]),
        "fixture_observed_sha256": hashlib.sha256(
            fixture["observed"].encode("ascii")).hexdigest(),
        "model_sha256": model_sha256(models),
    }


def validate_cell(record: dict, true_pair_index: int,
                  hypothesis_pair_index: int, models: dict) -> dict:
    for key, value in expected_identity(
            true_pair_index, hypothesis_pair_index, models).items():
        if record.get(key) != value:
            raise RuntimeError(f"Phase-505E checkpoint mismatch: {key}")
    score = record.get("observable", {}).get("primary_selector")
    if not isinstance(score, (int, float)) or not math.isfinite(score):
        raise RuntimeError("Phase-505E checkpoint has invalid selector")
    return record


def cell_path(root: Path, true_pair_index: int,
              hypothesis_pair_index: int) -> Path:
    return Path(root) / "pilot" / f"true_{true_pair_index:02d}" / (
        f"hypothesis_{hypothesis_pair_index:02d}.json")


def rank_row(records: list[dict], true_pair_index: int) -> dict:
    if {record["hypothesis_pair_index"] for record in records} != set(
            range(len(ceiling.ALL_PAIRS))):
        raise RuntimeError("Phase-505E row is incomplete")
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
    }


def run_timing(work_dir: Path = DEFAULT_WORK_DIR) -> dict:
    verify_timing_lock()
    output = Path(work_dir) / "timing_cell.json"
    if output.exists():
        raise FileExistsError("refusing to overwrite Phase-505E timing cell")
    models = deep.train_pair_balanced_models()
    cell = run_cell(*TIMING_CELL, models)
    result = {**cell,
              "status": "development_depth6_timing_complete",
              "projected_pilot_seconds": cell["wall_seconds"] * 108,
              "cost_gate_seconds": MAX_PILOT_PROJECTED_SECONDS,
              "cost_gate_passed": (cell["wall_seconds"] * 108 <=
                                   MAX_PILOT_PROJECTED_SECONDS)}
    atomic_json(output, result)
    return result


def run_pilot(work_dir: Path = DEFAULT_WORK_DIR) -> dict:
    verify_pilot_lock(work_dir)
    root = Path(work_dir)
    models = deep.train_pair_balanced_models()
    rows = []
    for true_pair_index in PILOT_TRUE_PAIR_INDICES:
        cells = []
        for hypothesis_pair_index in range(len(ceiling.ALL_PAIRS)):
            path = cell_path(root, true_pair_index, hypothesis_pair_index)
            if path.exists():
                record = validate_cell(json.loads(path.read_text()),
                                       true_pair_index,
                                       hypothesis_pair_index, models)
            elif (true_pair_index, hypothesis_pair_index) == TIMING_CELL:
                timing = json.loads((root / "timing_cell.json").read_text())
                timing["status"] = "development_depth6_cell_complete"
                record = validate_cell(timing, true_pair_index,
                                       hypothesis_pair_index, models)
                atomic_json(path, record)
            else:
                record = run_cell(true_pair_index, hypothesis_pair_index,
                                  models)
                atomic_json(path, record)
            cells.append(record)
            atomic_json(root / "pilot_progress.json", {
                "phase": "505E", "status": "pilot_in_progress",
                "completed_cells": sum(
                    cell_path(root, row, hypothesis).is_file()
                    for row in PILOT_TRUE_PAIR_INDICES
                    for hypothesis in range(len(ceiling.ALL_PAIRS))),
                "total_cells": 108,
                "execution_lock_sha256": sha256_file(PILOT_LOCK),
            })
        row = rank_row(cells, true_pair_index)
        rows.append(row)
        atomic_json(root / "pilot" / f"true_{true_pair_index:02d}" /
                    "row.json", row)
    result = {
        "phase": "505E", "status": "development_depth6_pilot_complete",
        "faed_scored": False, "holdout_consumed": False,
        "execution_lock_sha256": sha256_file(PILOT_LOCK),
        "top1": sum(row["true_pair_rank"] == 1 for row in rows),
        "top3": sum(row["true_pair_rank"] <= 3 for row in rows),
        "rows": rows,
    }
    atomic_json(root / "pilot_result.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--verify-timing-lock", action="store_true")
    group.add_argument("--verify-pilot-lock", action="store_true")
    group.add_argument("--run-timing", action="store_true")
    group.add_argument("--run-pilot", action="store_true")
    parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK_DIR)
    args = parser.parse_args()
    if args.verify_timing_lock:
        result = verify_timing_lock()
    elif args.verify_pilot_lock:
        result = verify_pilot_lock(args.work_dir)
    elif args.run_timing:
        result = run_timing(args.work_dir)
    else:
        result = run_pilot(args.work_dir)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
