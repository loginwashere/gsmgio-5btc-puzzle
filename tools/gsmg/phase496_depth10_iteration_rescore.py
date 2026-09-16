#!/usr/bin/env python3
"""Full-population depth-10 unrestricted rescore at 3 x 10,000."""
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
import phase494_unrestricted_board_full_pipeline as phase494
import phase495_depth10_objective_diagnostic as phase495


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
PROTOCOL = (REPO_ROOT / "doc" / "Brainstorms" /
            "2026-09-13 - Phase 496 Depth10 Iteration Rescore.md")
SOURCE = phase495.DEFAULT_SOURCE
PHASE495_RESULT = (REPO_ROOT / "_work" / "phase495" /
                   "depth10_objective_diagnostic.json")
EXPECTED_PHASE495_SHA256 = \
    "58b59afbd87435f3c01a69e2e218c34f750e3cc10b3a5271309719336963ff9b"
DEFAULT_WORK_DIR = REPO_ROOT / "_work" / "phase496" / "depth10_r3_n10000"
RESTARTS, ITERATIONS = 3, 10000
KEEP = continuation.SCHEDULE["lane_a_depth8_keep"]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def verify_inputs() -> dict:
    phase494_data = phase495.verify_phase494_marker()
    if sha256_file(PHASE495_RESULT) != EXPECTED_PHASE495_SHA256:
        raise RuntimeError("Phase-495 diagnostic result changed")
    diagnostic = json.loads(PHASE495_RESULT.read_text())
    if diagnostic["full_population"]["unrestricted"]["best_true_rank"] != 1392757:
        raise RuntimeError("Phase-495 diagnosis differs from reviewed result")
    if diagnostic["phase494_source_sha256"] != sha256_file(SOURCE):
        raise RuntimeError("depth-9 source differs from Phase 495")
    return phase494_data


def run(work_dir: Path = DEFAULT_WORK_DIR) -> dict:
    work_dir = Path(work_dir)
    output = work_dir / "result.json"
    checkpoint = work_dir / "depth10_selected.npz"
    if output.exists() or checkpoint.exists():
        raise FileExistsError("refusing to overwrite Phase-496 output")
    verify_inputs()
    began = time.monotonic()
    with np.load(SOURCE) as saved:
        parents = np.asarray(saved["paths"], dtype=np.uint8)
    children = front.expand_bidirectional(parents)
    fixture = variants.make_variant(phase494.FIXTURE_INDEX,
                                    phase494.SWAP_COUNT)
    blocks = prefix.blocks_from_observed(fixture)
    pair = tuple(fixture["pair"])
    truth = prefix.order_to_sequence(fixture["order"])
    quad, _ = base.load_language_model()
    scores = front.constrained_multistart(
        children, blocks, pair, quad, RESTARTS, ITERATIONS,
        binary=variants.UNRESTRICTED_BINARY,
        seed=continuation.SCHEDULE["board_seed"])
    before = continuation.recovery(children, scores, truth, 10)
    selected, selected_scores, unique = front.select_diverse(
        children, scores, KEEP)
    after = continuation.recovery(selected, selected_scores, truth, 10)
    continuation.atomic_population(checkpoint, selected, selected_scores)
    result = {
        "phase": 496,
        "status": "development_gate_complete",
        "faed_scored": False,
        "holdout_consumed": False,
        "fixture_index": phase494.FIXTURE_INDEX,
        "swap_count": phase494.SWAP_COUNT,
        "source": str(SOURCE),
        "source_sha256": sha256_file(SOURCE),
        "phase495_result_sha256": sha256_file(PHASE495_RESULT),
        "protocol_sha256": sha256_file(PROTOCOL),
        "unrestricted_binary_sha256": sha256_file(variants.UNRESTRICTED_BINARY),
        "restarts": RESTARTS,
        "iterations": ITERATIONS,
        "generated": len(children),
        "generated_unique": unique,
        "keep": len(selected),
        "before_selection": before,
        "after_selection": after,
        "gate_passed": after["true_segments"] > 0,
        "checkpoint": str(checkpoint),
        "checkpoint_sha256": sha256_file(checkpoint),
        "wall_seconds": time.monotonic() - began,
    }
    atomic_json(output, result)
    return result


def self_test() -> dict:
    verify_inputs()
    if RESTARTS != 3 or ITERATIONS != 10000 or KEEP != 262144:
        raise AssertionError("Phase-496 schedule changed")
    return {"faed_scored": False, "inputs_verified": True,
            "restarts": RESTARTS, "iterations": ITERATIONS, "keep": KEEP}


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
