#!/usr/bin/env python3
"""Phase 506A: locked depth-6 ranking of all escape pairs on real FAED."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
from pathlib import Path

from data import FAED
import phase484a_raw_symbol_vic_solver as base
import phase493_partial_unrestricted_board_diagnostic as variants
import phase505_escape_pair_identifiability as ceiling
import phase505b_blind_escape_pair_selector as deep
import phase505e_depth6_escape_pair_selector as selector


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
PROTOCOL = (REPO_ROOT / "doc" / "Brainstorms" /
            "2026-09-14 - Phase 506 FAED Top-Five Escape-Pair Gamble.md")
LOCK = SCRIPT_DIR / "phase506a_execution_lock.json"
WORK_DIR = REPO_ROOT / "_work" / "phase506a"
RESULT = WORK_DIR / "result.json"
FAED_SHA256 = "066191b4aafc114fbca7f0d168382f40129c4ff18490375b689741081d5ef3c2"
EXCLUDED_PAIR = ("g", "i")
SELECT_COUNT = 5


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic(path: Path, value: dict) -> None:
    selector.atomic_json(Path(path), value)


def faed_identity() -> dict:
    digest = hashlib.sha256(FAED.encode("ascii")).hexdigest()
    if digest != FAED_SHA256 or len(FAED) != 570:
        raise AssertionError("FAED identity changed")
    return {
        "ascii_sha256": digest,
        "raw_length": len(FAED),
        "raw_counts": dict(sorted(collections.Counter(FAED).items())),
    }


def lock_payload() -> dict:
    modules = (base, variants, ceiling, deep, selector)
    return {
        "phase": "506A",
        "status": "real_execution_lock",
        "protocol_sha256": sha(PROTOCOL),
        "script_sha256": sha(Path(__file__)),
        "dependencies_sha256": {
            str(Path(module.__file__).relative_to(REPO_ROOT)):
                sha(Path(module.__file__)) for module in modules
        },
        "phase505e_pilot_lock_sha256": sha(selector.PILOT_LOCK),
        "phase505e_pilot_result_sha256": sha(
            selector.DEFAULT_WORK_DIR / "pilot_result.json"),
        "unrestricted_board_binary_sha256": sha(variants.UNRESTRICTED_BINARY),
        "faed": faed_identity(),
        "width": 19,
        "pair_indices": list(range(len(ceiling.ALL_PAIRS))),
        "primary_selector":
            "maximum depth-6 unrestricted-board normalized score",
        "excluded_after_ranking": list(EXCLUDED_PAIR),
        "selection_count": SELECT_COUNT,
        "tie_break": "ascending pair index",
        "checkpoint_policy": "one atomic JSON file per pair",
        "faed_run_count": 1,
    }


def verify_lock() -> dict:
    if not LOCK.is_file():
        raise RuntimeError("Phase-506A execution lock is absent")
    actual = json.loads(LOCK.read_text())
    if actual != lock_payload():
        raise RuntimeError("Phase-506A execution lock mismatch")
    return actual


def real_fixture() -> dict:
    return {"observed": FAED, "width": 19,
            "board_mode": "unknown_real_unrestricted"}


def cell_path(pair_index: int) -> Path:
    return WORK_DIR / "cells" / f"pair_{pair_index:02d}.json"


def run_cell(pair_index: int, models: dict) -> dict:
    paths, blocks, pair, stages = selector.invariant_to_depth6(
        real_fixture(), pair_index, models)
    quad, _ = base.load_language_model()
    scores = selector.front.constrained_multistart(
        paths, blocks, pair, quad,
        deep.SCREEN_SCHEDULE["coarse_restarts"],
        deep.SCREEN_SCHEDULE["coarse_iterations"],
        binary=variants.UNRESTRICTED_BINARY, seed=deep.BOARD_SEED)
    ranked = selector.front.ranked_indices(paths, scores)
    top = ranked[:selector.TOP_PATHS_RECORDED]
    return {
        "phase": "506A", "status": "real_faed_depth6_pair_cell_complete",
        "faed_scored": True, "holdout_consumed": False,
        "execution_lock_sha256": sha(LOCK),
        "faed_ascii_sha256": FAED_SHA256,
        "model_sha256": selector.model_sha256(models),
        "hypothesis_pair_index": pair_index,
        "hypothesis_pair": list(pair),
        "invariant_stages": stages,
        "observable": {
            "primary_selector": float(scores[ranked[0]]),
            "score_distribution": deep.score_summary(scores),
            "best_path_window_count": selector.best_path_window_count(
                blocks, pair, paths[ranked[0]]),
            "top_paths": [
                {"path": paths[index].tolist(),
                 "score": float(scores[index]),
                 "quadgram_windows": selector.best_path_window_count(
                     blocks, pair, paths[index])}
                for index in top],
        },
    }


def validate_cell(record: dict, pair_index: int, models: dict) -> dict:
    expected = {
        "phase": "506A",
        "status": "real_faed_depth6_pair_cell_complete",
        "faed_scored": True,
        "holdout_consumed": False,
        "execution_lock_sha256": sha(LOCK),
        "faed_ascii_sha256": FAED_SHA256,
        "model_sha256": selector.model_sha256(models),
        "hypothesis_pair_index": pair_index,
        "hypothesis_pair": list(ceiling.ALL_PAIRS[pair_index]),
    }
    for key, value in expected.items():
        if record.get(key) != value:
            raise RuntimeError(f"Phase-506A checkpoint mismatch: {key}")
    score = record.get("observable", {}).get("primary_selector")
    if not isinstance(score, (int, float)) or not math.isfinite(score):
        raise RuntimeError("Phase-506A checkpoint has invalid selector")
    return record


def rank_records(records: list[dict]) -> tuple[list[dict], list[dict]]:
    if {r["hypothesis_pair_index"] for r in records} != set(range(36)):
        raise RuntimeError("Phase-506A pair matrix is incomplete")
    ranked = sorted(records, key=lambda r: (
        -r["observable"]["primary_selector"],
        r["hypothesis_pair_index"]))
    table = [{
        "rank": rank,
        "pair_index": record["hypothesis_pair_index"],
        "pair": record["hypothesis_pair"],
        "score": record["observable"]["primary_selector"],
    } for rank, record in enumerate(ranked, 1)]
    selected = [row for row in table if tuple(row["pair"]) != EXCLUDED_PAIR][
        :SELECT_COUNT]
    if len(selected) != SELECT_COUNT:
        raise RuntimeError("Phase-506A could not select five pairs")
    return table, selected


def run() -> dict:
    verify_lock()
    if RESULT.exists():
        raise FileExistsError("refusing to overwrite Phase-506A result")
    models = deep.train_pair_balanced_models()
    records = []
    for pair_index in range(len(ceiling.ALL_PAIRS)):
        path = cell_path(pair_index)
        if path.exists():
            record = validate_cell(json.loads(path.read_text()), pair_index,
                                   models)
        else:
            record = run_cell(pair_index, models)
            atomic(path, record)
        records.append(record)
        atomic(WORK_DIR / "progress.json", {
            "phase": "506A", "status": "real_pair_ranking_in_progress",
            "completed_cells": len(records), "total_cells": 36,
            "execution_lock_sha256": sha(LOCK),
        })
    ranking, selected = rank_records(records)
    result = {
        "phase": "506A", "status": "real_faed_pair_ranking_complete",
        "faed_scored": True, "holdout_consumed": False,
        "execution_lock_sha256": sha(LOCK),
        "primary_selector": lock_payload()["primary_selector"],
        "ranking": ranking, "selected_for_phase506b": selected,
        "calibration_disposition":
            "bounded gamble; ranking is not a powered identification claim",
    }
    atomic(RESULT, result)
    return result


def self_test() -> dict:
    identity = faed_identity()
    if len(ceiling.ALL_PAIRS) != 36:
        raise AssertionError("pair universe changed")
    if EXCLUDED_PAIR not in ceiling.ALL_PAIRS:
        raise AssertionError("excluded pair missing")
    fake = [{"hypothesis_pair_index": i,
             "hypothesis_pair": list(ceiling.ALL_PAIRS[i]),
             "observable": {"primary_selector": float(i)}}
            for i in range(36)]
    ranking, selected = rank_records(fake)
    if len(ranking) != 36 or len(selected) != 5:
        raise AssertionError("ranking cardinality failed")
    if any(tuple(row["pair"]) == EXCLUDED_PAIR for row in selected):
        raise AssertionError("excluded pair selected")
    return {"self_test": "pass", "faed": identity,
            "pair_count": 36, "excluded_pair_index":
                ceiling.ALL_PAIRS.index(EXCLUDED_PAIR)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--print-lock", action="store_true")
    group.add_argument("--verify-lock", action="store_true")
    group.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        result = self_test()
    elif args.print_lock:
        result = lock_payload()
    elif args.verify_lock:
        result = verify_lock()
    else:
        result = run()
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
