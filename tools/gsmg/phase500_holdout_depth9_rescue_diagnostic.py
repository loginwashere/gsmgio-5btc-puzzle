#!/usr/bin/env python3
"""Diagnose Phase 499 holdout fixture 0's depth-9 collapse.

Phase 499 froze a schedule that runs depths 8-9 at the original Phase-490
budget (3 x 2,000 unrestricted board-anneal iterations) and only raises the
budget to 3 x 10,000 starting at depth 10. Holdout fixture 0 already failed
the gate: its true completion held rank 1 at depth 8, then collapsed to rank
45,203 (before selection) / 31,532 (after) at depth 9 under the 2,000-
iteration budget, and the stronger depth-10 budget never recovered it.

This is a diagnostic-only re-analysis of the already-consumed, already-failed
fixture 0. It does not spend holdout fixtures 1 or 2 (the gate's stop rule
forbids that after a first failure) and it does not touch FAED. It answers
one question: was the depth-9 collapse caused by an under-annealed depth-9
score (the same failure mode Phase 495/496 diagnosed and fixed at depth 10),
or does the true completion lose to competitors even at the stronger budget?
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np

import phase484a_raw_symbol_vic_solver as base
import phase484j_constructive_prefix_beam_probe as prefix
import phase490_width19_dual_lane_dev as front
import phase490_width19_checkpointed_dual_lane as continuation
import phase493_partial_unrestricted_board_diagnostic as variants
import phase497_high_iteration_unrestricted_continuation as phase497
import phase499_unrestricted_width19_holdout as phase499


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
FIXTURE_INDEX = 0
SPLIT = "holdout"
SWAP_COUNT = 3
SOURCE_WORK_DIR = REPO_ROOT / "_work" / "phase499" / "i0_s3"
DEPTH8_CHECKPOINT = SOURCE_WORK_DIR / "continuation" / "lane_a_depth8.npz"
DEPTH8_RECORD = SOURCE_WORK_DIR / "continuation" / "lane_a_depth8.json"
DEFAULT_WORK_DIR = REPO_ROOT / "_work" / "phase500" / "i0_s3_depth9_rescue"
RESTARTS, ITERATIONS = 3, 10000
KEEP = phase497.ENHANCED_SCHEDULE["lane_a_depth8_keep"]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def verify_inputs() -> dict:
    phase499.verify_lock()
    if not DEPTH8_CHECKPOINT.is_file() or not DEPTH8_RECORD.is_file():
        raise RuntimeError("Phase-499 fixture-0 depth-8 checkpoint is missing")
    record = json.loads(DEPTH8_RECORD.read_text())
    if record.get("output_sha256") != sha256_file(DEPTH8_CHECKPOINT):
        raise RuntimeError("depth-8 checkpoint hash does not match its record")
    if (record.get("fixture_index") != FIXTURE_INDEX or
            record.get("split") != SPLIT):
        raise RuntimeError("depth-8 checkpoint identity mismatch")
    result_path = SOURCE_WORK_DIR / "phase499_complete_result.json"
    result = json.loads(result_path.read_text())
    if result.get("top1_exact_order") is not False:
        raise RuntimeError("fixture 0 is not a recorded failure; refusing to run")
    return record


def run(work_dir: Path = DEFAULT_WORK_DIR) -> dict:
    work_dir = Path(work_dir)
    output = work_dir / "result.json"
    if output.exists():
        return json.loads(output.read_text())
    verify_inputs()
    fixture = phase499.make_holdout_variant(FIXTURE_INDEX)
    blocks = prefix.blocks_from_observed(fixture)
    pair = tuple(fixture["pair"])
    truth = prefix.order_to_sequence(fixture["order"])
    quad, _ = base.load_language_model()

    began = time.monotonic()
    with np.load(DEPTH8_CHECKPOINT) as saved:
        parents = np.asarray(saved["paths"], dtype=np.uint8)
    if parents.shape[1] != 8:
        raise ValueError("expected a depth-8 population")
    children = front.expand_bidirectional(parents)
    scores = front.constrained_multistart(
        children, blocks, pair, quad, RESTARTS, ITERATIONS,
        binary=variants.UNRESTRICTED_BINARY,
        seed=continuation.SCHEDULE["board_seed"])
    before = continuation.recovery(children, scores, truth, 9)
    selected, selected_scores, unique = front.select_diverse(
        children, scores, KEEP)
    after = continuation.recovery(selected, selected_scores, truth, 9)
    checkpoint = work_dir / "depth9_rescue_selected.npz"
    continuation.atomic_population(checkpoint, selected, selected_scores)
    result = {
        "phase": 500,
        "status": "diagnostic_complete",
        "diagnostic_only": True,
        "faed_scored": False,
        "holdout_consumed": False,
        "note": "re-analysis of already-failed, already-consumed fixture 0; "
                "spends no new holdout fixture",
        "fixture_index": FIXTURE_INDEX,
        "swap_count": SWAP_COUNT,
        "source": str(DEPTH8_CHECKPOINT),
        "source_sha256": sha256_file(DEPTH8_CHECKPOINT),
        "unrestricted_binary_sha256": sha256_file(variants.UNRESTRICTED_BINARY),
        "restarts": RESTARTS,
        "iterations": ITERATIONS,
        "generated": len(children),
        "generated_unique": unique,
        "keep": len(selected),
        "original_depth9_before_selection_rank": 45203,
        "original_depth9_after_selection_rank": 31532,
        "before_selection": before,
        "after_selection": after,
        "rescued": after["true_segments"] > 0 and after["best_true_rank"] <= 1000,
        "checkpoint": str(checkpoint),
        "checkpoint_sha256": sha256_file(checkpoint),
        "wall_seconds": time.monotonic() - began,
    }
    atomic_json(output, result)
    return result


def self_test() -> dict:
    verify_inputs()
    if RESTARTS != 3 or ITERATIONS != 10000 or KEEP != 262144:
        raise AssertionError("Phase-500 schedule changed")
    return {"faed_scored": False, "diagnostic_only": True,
            "fixture_index": FIXTURE_INDEX, "restarts": RESTARTS,
            "iterations": ITERATIONS}


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--run", action="store_true")
    parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK_DIR)
    args = parser.parse_args()
    result = self_test() if args.self_test else run(args.work_dir)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
