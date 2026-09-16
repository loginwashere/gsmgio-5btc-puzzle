#!/usr/bin/env python3
"""Local-sibling postmortem for the failed Phase-499 depth-11 bridge."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

import phase484a_raw_symbol_vic_solver as base
import phase484j_constructive_prefix_beam_probe as prefix
import phase484k_bidirectional_segment_assembly_probe as bidi
import phase490_width19_dual_lane_dev as front
import phase490_width19_checkpointed_dual_lane as continuation
import phase493_partial_unrestricted_board_diagnostic as variants
import phase495_depth10_objective_diagnostic as diagnostic
import phase499_unrestricted_width19_holdout as phase499


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
SOURCE = REPO_ROOT / "_work/phase499/i0_s3/continuation/depth10.npz"
SOURCE_RECORD = REPO_ROOT / "_work/phase499/i0_s3/continuation/depth10.json"
BRIDGE_RECORD = REPO_ROOT / "_work/phase499/i0_s3/continuation/depth11_bridge.json"
DEFAULT_OUTPUT = REPO_ROOT / "_work/phase500/holdout0_depth11_local.json"
ARMS = (("production", 3, 10000), ("high_budget", 8, 20000))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def true_mask(paths: np.ndarray, truth, depth: int) -> np.ndarray:
    mask = np.zeros(len(paths), dtype=bool)
    for target in bidi.true_windows(truth, depth):
        mask |= np.all(paths == np.asarray(target, dtype=np.uint8), axis=1)
    return mask


def local_records(scores, boards, planted, planted_board, is_true) -> list[dict]:
    accuracy = np.mean(boards == planted_board, axis=1)
    records = []
    for index in np.flatnonzero(is_true):
        records.append({
            "child_index": int(index),
            "score": float(scores[index]),
            "local_rank": 1 + int(np.count_nonzero(scores > scores[index])),
            "planted_board_score": float(planted[index]),
            "gap_from_planted": float(scores[index] - planted[index]),
            "board_accuracy": float(accuracy[index]),
        })
    return records


def verify_inputs() -> tuple[np.ndarray, dict]:
    phase499.verify_lock()
    if not all(path.is_file() for path in (SOURCE, SOURCE_RECORD, BRIDGE_RECORD)):
        raise RuntimeError("Phase-499 failed-bridge checkpoints are absent")
    source_record = json.loads(SOURCE_RECORD.read_text())
    bridge_record = json.loads(BRIDGE_RECORD.read_text())
    if source_record.get("output_sha256") != sha256_file(SOURCE):
        raise RuntimeError("Phase-499 depth-10 checkpoint hash mismatch")
    if bridge_record.get("source_sha256") != sha256_file(SOURCE):
        raise RuntimeError("Phase-499 bridge source hash mismatch")
    paths, _, _, _ = continuation.load_population(
        SOURCE, min_depth=10, max_depth=10)
    return paths, bridge_record


def run(output: Path = DEFAULT_OUTPUT) -> dict:
    output = Path(output)
    if output.exists():
        raise FileExistsError("refusing to overwrite Phase-500 result")
    paths, bridge_record = verify_inputs()
    fixture = phase499.make_holdout_variant(0)
    truth = prefix.order_to_sequence(fixture["order"])
    selected_true = true_mask(paths, truth, 10)
    true_parents = paths[selected_true]
    if len(true_parents) != 1:
        raise AssertionError("expected one surviving true depth-10 parent")
    children = front.expand_bidirectional(true_parents)
    is_true = true_mask(children, truth, 11)
    if int(np.count_nonzero(is_true)) != 2:
        raise AssertionError("expected two true depth-11 children")
    blocks = prefix.blocks_from_observed(fixture)
    pair = tuple(fixture["pair"])
    quad, _ = base.load_language_model()
    planted_board = variants.canonical_board(fixture["letter_to_code"])
    planted = variants.score_planted(children, blocks, pair, planted_board, quad)
    arm_results = {}
    for name, restarts, iterations in ARMS:
        _, scores, boards, _ = diagnostic.multistart_panel(
            variants.UNRESTRICTED_BINARY, children, blocks, pair, quad,
            restarts, iterations, seed=continuation.SCHEDULE["board_seed"])
        arm_results[name] = {
            "restarts": restarts,
            "iterations": iterations,
            "true_children": local_records(
                scores, boards, planted, planted_board, is_true),
            "best_false_score": float(np.max(scores[~is_true])),
        }
    planted_true = [{
        "child_index": int(index),
        "score": float(planted[index]),
        "local_rank": 1 + int(np.count_nonzero(planted > planted[index])),
    } for index in np.flatnonzero(is_true)]
    result = {
        "phase": 500,
        "status": "posthoc_failed_holdout_diagnostic",
        "faed_scored": False,
        "phase499_gate_remains_failed": True,
        "fixture_index": 0,
        "source_sha256": sha256_file(SOURCE),
        "source_record_sha256": sha256_file(SOURCE_RECORD),
        "bridge_record_sha256": sha256_file(BRIDGE_RECORD),
        "recorded_bridge_before_selection": bridge_record["before_selection"],
        "recorded_bridge_after_selection": bridge_record["after_selection"],
        "true_parent_count": len(true_parents),
        "sibling_count": len(children),
        "true_child_count": int(np.count_nonzero(is_true)),
        "planted": {"true_children": planted_true},
        "arms": arm_results,
    }
    phase499.atomic_json(output, result)
    return result


def self_test() -> dict:
    sample = np.asarray([[0, 1], [1, 2], [2, 3]], dtype=np.uint8)
    mask = true_mask(sample, (0, 1, 2, 3), 2)
    if mask.tolist() != [True, True, True]:
        raise AssertionError("true-window mask changed")
    if ARMS[0] != ("production", 3, 10000):
        raise AssertionError("production arm changed")
    return {"faed_scored": False, "posthoc": True,
            "phase499_gate_can_be_rescued": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--run", action="store_true")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = self_test() if args.self_test else run(args.output)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

