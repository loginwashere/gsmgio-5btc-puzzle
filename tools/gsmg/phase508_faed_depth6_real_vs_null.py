#!/usr/bin/env python3
"""Phase 508: exact-multiset null diagnostic for Phase-506A's proxy."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import sys
from unittest import mock
from pathlib import Path

from data import FAED
import phase484a_raw_symbol_vic_solver as base
import phase493_partial_unrestricted_board_diagnostic as variants
import phase505_escape_pair_identifiability as ceiling
import phase505b_blind_escape_pair_selector as deep
import phase505e_depth6_escape_pair_selector as selector
import phase506a_faed_depth6_pair_rank as realrank


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
PROTOCOL = (REPO_ROOT / "doc" / "Brainstorms" /
            "2026-09-15 - Phase 508 FAED Depth6 Real-vs-Null Diagnostic.md")
LOCK = SCRIPT_DIR / "phase508_execution_lock.json"
WORK_DIR = REPO_ROOT / "_work" / "phase508"
RESULT = WORK_DIR / "result.json"
NULL_SEED = 0x508A11
TRIALS = 200


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic(path: Path, value: dict) -> None:
    selector.atomic_json(Path(path), value)


def real_result() -> dict:
    realrank.verify_lock()
    if not realrank.RESULT.is_file():
        raise RuntimeError("Phase-506A result is absent")
    result = json.loads(realrank.RESULT.read_text())
    ranking = result.get("ranking")
    if (result.get("status") != "real_faed_pair_ranking_complete" or
            not isinstance(ranking, list) or len(ranking) != 36):
        raise RuntimeError("Phase-506A result is invalid")
    if ranking != sorted(ranking, key=lambda row: (-row["score"], row["pair_index"])):
        raise RuntimeError("Phase-506A ranking order is invalid")
    return result


def real_maximum() -> float:
    value = real_result()["ranking"][0]["score"]
    if not isinstance(value, (int, float)) or not math.isfinite(value):
        raise RuntimeError("Phase-506A maximum is invalid")
    return float(value)


def shuffled_faed(trial_index: int) -> str:
    if not 0 <= trial_index < TRIALS:
        raise ValueError("trial index outside frozen range")
    values = list(FAED)
    rng = base.PCG32(base.derive_seed(NULL_SEED, trial_index))
    rng.shuffle(values)
    shuffled = "".join(values)
    if collections.Counter(shuffled) != collections.Counter(FAED):
        raise AssertionError("null changed FAED's symbol multiset")
    if shuffled == FAED:
        raise AssertionError("null shuffle reproduced FAED exactly")
    return shuffled


def lock_payload() -> dict:
    modules = (base, variants, ceiling, deep, selector, realrank)
    real = real_result()
    return {
        "phase": 508,
        "status": "locked_before_null_execution",
        "protocol_sha256": sha(PROTOCOL),
        "script_sha256": sha(Path(__file__)),
        "dependencies_sha256": {
            str(Path(module.__file__).relative_to(REPO_ROOT)):
                sha(Path(module.__file__)) for module in modules
        },
        "phase506a_lock_sha256": sha(realrank.LOCK),
        "phase506a_result_sha256": sha(realrank.RESULT),
        "real_family_maximum": real_maximum(),
        "real_winning_pair_index": real["ranking"][0]["pair_index"],
        "faed_ascii_sha256": realrank.FAED_SHA256,
        "null": "exact raw-symbol-multiset Fisher-Yates shuffle",
        "rng": "PCG32",
        "null_seed": NULL_SEED,
        "trial_indices": {"start": 0, "stop_exclusive": TRIALS},
        "pair_indices_per_trial": {
            "start": 0, "stop_exclusive": len(ceiling.ALL_PAIRS)},
        "primary_statistic": "maximum Phase-505E depth-6 unrestricted-board score across all 36 pairs",
        "ties_are_exceedances": True,
        "futility_stop": "stop immediately at first null maximum >= real maximum",
        "maximum_trials": TRIALS,
        "maximum_pair_cells": TRIALS * len(ceiling.ALL_PAIRS),
        "interpretation": "diagnostic of shallow proxy, not a test of Model B",
        "faed_already_observed": True,
        "unrestricted_board_binary_sha256": sha(variants.UNRESTRICTED_BINARY),
        "model_sha256": selector.model_sha256(deep.train_pair_balanced_models()),
    }


def verify_lock() -> dict:
    if not LOCK.is_file():
        raise RuntimeError("Phase-508 execution lock is absent")
    actual = json.loads(LOCK.read_text())
    if actual != lock_payload():
        raise RuntimeError("Phase-508 execution lock mismatch")
    return actual


def cell_path(trial_index: int, pair_index: int) -> Path:
    return WORK_DIR / f"null_{trial_index:03d}" / f"pair_{pair_index:02d}.json"


def run_cell(trial_index: int, pair_index: int, observed: str,
             models: dict) -> dict:
    fixture = {"observed": observed, "width": 19,
               "board_mode": "null_unrestricted"}
    paths, blocks, pair, stages = selector.invariant_to_depth6(
        fixture, pair_index, models)
    quad, _ = base.load_language_model()
    scores = selector.front.constrained_multistart(
        paths, blocks, pair, quad,
        deep.SCREEN_SCHEDULE["coarse_restarts"],
        deep.SCREEN_SCHEDULE["coarse_iterations"],
        binary=variants.UNRESTRICTED_BINARY, seed=deep.BOARD_SEED)
    ranked = selector.front.ranked_indices(paths, scores)
    return {
        "phase": 508,
        "status": "null_pair_cell_complete",
        "faed_scored": False,
        "null_trial_index": trial_index,
        "null_observed_sha256": hashlib.sha256(observed.encode("ascii")).hexdigest(),
        "execution_lock_sha256": sha(LOCK),
        "model_sha256": selector.model_sha256(models),
        "hypothesis_pair_index": pair_index,
        "hypothesis_pair": list(pair),
        "invariant_stages": stages,
        "observable": {
            "primary_selector": float(scores[ranked[0]]),
            "score_distribution": deep.score_summary(scores),
            "best_path": paths[ranked[0]].tolist(),
            "best_path_window_count": selector.best_path_window_count(
                blocks, pair, paths[ranked[0]]),
        },
    }


def validate_cell(record: dict, trial_index: int, pair_index: int,
                  observed: str, models: dict) -> dict:
    expected = {
        "phase": 508,
        "status": "null_pair_cell_complete",
        "faed_scored": False,
        "null_trial_index": trial_index,
        "null_observed_sha256": hashlib.sha256(observed.encode("ascii")).hexdigest(),
        "execution_lock_sha256": sha(LOCK),
        "model_sha256": selector.model_sha256(models),
        "hypothesis_pair_index": pair_index,
        "hypothesis_pair": list(ceiling.ALL_PAIRS[pair_index]),
    }
    for key, value in expected.items():
        if record.get(key) != value:
            raise RuntimeError(f"Phase-508 checkpoint mismatch: {key}")
    score = record.get("observable", {}).get("primary_selector")
    if not isinstance(score, (int, float)) or not math.isfinite(score):
        raise RuntimeError("Phase-508 checkpoint has invalid score")
    return record


def trial_path(trial_index: int) -> Path:
    return WORK_DIR / f"null_{trial_index:03d}" / "trial.json"


def summarize_trial(trial_index: int, records: list[dict], *,
                    real_score: float | None = None,
                    lock_sha256: str | None = None) -> dict:
    if {record["hypothesis_pair_index"] for record in records} != set(range(36)):
        raise RuntimeError("Phase-508 null trial is incomplete")
    ranked = sorted(records, key=lambda record: (
        -record["observable"]["primary_selector"],
        record["hypothesis_pair_index"]))
    maximum = ranked[0]["observable"]["primary_selector"]
    if real_score is None:
        real_score = real_maximum()
    if lock_sha256 is None:
        lock_sha256 = sha(LOCK)
    return {
        "phase": 508,
        "status": "null_trial_complete",
        "trial_index": trial_index,
        "execution_lock_sha256": lock_sha256,
        "null_observed_sha256": ranked[0]["null_observed_sha256"],
        "family_maximum": maximum,
        "winning_pair_index": ranked[0]["hypothesis_pair_index"],
        "winning_pair": ranked[0]["hypothesis_pair"],
        "real_family_maximum": real_score,
        "tie_inclusive_exceedance": maximum >= real_score,
    }


def load_completed_trial(trial_index: int, observed: str,
                         models: dict) -> dict:
    records = []
    for pair_index in range(len(ceiling.ALL_PAIRS)):
        path = cell_path(trial_index, pair_index)
        if not path.is_file():
            raise RuntimeError(
                "Phase-508 completed trial is missing a pair checkpoint")
        records.append(validate_cell(json.loads(path.read_text()),
                                     trial_index, pair_index, observed, models))
    expected = summarize_trial(trial_index, records)
    actual = json.loads(trial_path(trial_index).read_text())
    if actual != expected:
        raise RuntimeError("Phase-508 completed trial does not match its cells")
    return actual


def run() -> dict:
    locked = verify_lock()
    if RESULT.exists():
        raise FileExistsError("refusing to overwrite Phase-508 result")
    models = deep.train_pair_balanced_models()
    trials = []
    for trial_index in range(TRIALS):
        observed = shuffled_faed(trial_index)
        completed = trial_path(trial_index)
        if completed.exists():
            trial = load_completed_trial(trial_index, observed, models)
        else:
            records = []
            for pair_index in range(len(ceiling.ALL_PAIRS)):
                path = cell_path(trial_index, pair_index)
                if path.exists():
                    record = validate_cell(json.loads(path.read_text()),
                                           trial_index, pair_index, observed,
                                           models)
                else:
                    record = run_cell(trial_index, pair_index, observed, models)
                    atomic(path, record)
                records.append(record)
                atomic(WORK_DIR / "progress.json", {
                    "phase": 508, "status": "null_execution_in_progress",
                    "trial_index": trial_index,
                    "completed_pairs_this_trial": len(records),
                    "total_pairs_this_trial": 36,
                    "completed_trials": len(trials),
                    "maximum_trials": TRIALS,
                    "execution_lock_sha256": sha(LOCK),
                })
            trial = summarize_trial(trial_index, records)
            atomic(completed, trial)
        trials.append(trial)
        if trial["tie_inclusive_exceedance"]:
            break
    exceedances = sum(trial["tie_inclusive_exceedance"] for trial in trials)
    stopped = exceedances > 0
    result = {
        "phase": 508,
        "status": "futility_stop" if stopped else "maximum_trials_complete",
        "faed_scored": False,
        "execution_lock_sha256": sha(LOCK),
        "real_family_maximum": locked["real_family_maximum"],
        "completed_trials": len(trials),
        "maximum_trials": TRIALS,
        "exceedances": exceedances,
        "trials": trials,
        "add_one_p_if_stopped_now": (exceedances + 1) / (len(trials) + 1),
        "best_possible_fixed_200_p": (exceedances + 1) / (TRIALS + 1),
        "verdict": ("shallow_proxy_fails_real_vs_null_diagnostic" if stopped
                    else "shallow_proxy_separates_in_post_observation_diagnostic"),
        "model_b_disposition": "not tested by this proxy diagnostic",
    }
    atomic(RESULT, result)
    return result


def self_test() -> dict:
    shuffled0 = shuffled_faed(0)
    shuffled1 = shuffled_faed(1)
    if shuffled0 == shuffled1:
        raise AssertionError("distinct null trials collided")
    if collections.Counter(shuffled0) != collections.Counter(FAED):
        raise AssertionError("null multiset test failed")
    fake = []
    for index, pair in enumerate(ceiling.ALL_PAIRS):
        fake.append({"hypothesis_pair_index": index,
                     "hypothesis_pair": list(pair),
                     "null_observed_sha256": "x",
                     "observable": {"primary_selector": float(index)}})
    module = sys.modules[__name__]
    with mock.patch.object(module, "sha", return_value="lock"), \
            mock.patch.object(module, "real_maximum", return_value=35.0):
        summary = summarize_trial(0, fake)
    if not summary["tie_inclusive_exceedance"] or summary["winning_pair_index"] != 35:
        raise AssertionError("inclusive exceedance test failed")
    return {"self_test": "pass", "trials": TRIALS, "pair_count": 36,
            "null0_sha256": hashlib.sha256(shuffled0.encode("ascii")).hexdigest(),
            "real_family_maximum": real_maximum()}


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
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
