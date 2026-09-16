#!/usr/bin/env python3
"""Continue Phase 496 through width 19 with deeper unrestricted annealing."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import phase484x_exact_faed_profile_power_probe as exact
import phase490_width19_dual_lane_dev as front
import phase490_width19_checkpointed_dual_lane as continuation
import phase493_partial_unrestricted_board_diagnostic as variants
import phase494_unrestricted_board_full_pipeline as phase494
import phase496_depth10_iteration_rescore as phase496


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
PROTOCOL = (REPO_ROOT / "doc" / "Brainstorms" /
            "2026-09-13 - Phase 497 High-Iteration Unrestricted Continuation.md")
SOURCE = phase496.DEFAULT_WORK_DIR / "depth10_selected.npz"
PHASE496_RESULT = phase496.DEFAULT_WORK_DIR / "result.json"
EXPECTED_PHASE496_SHA256 = \
    "319f84230e6b7b258f9235655fde1e06d8e58ebed4bd952eb127435deb592b96"
DEFAULT_WORK_DIR = REPO_ROOT / "_work" / "phase497" / "i3_s3"
ENHANCED_SCHEDULE = {**continuation.SCHEDULE, "coarse_iterations": 10000}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical_hash(value) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def verify_inputs() -> dict:
    phase496.verify_inputs()
    result_hash = sha256_file(PHASE496_RESULT)
    if result_hash != EXPECTED_PHASE496_SHA256:
        raise RuntimeError("Phase-496 result changed")
    record = json.loads(PHASE496_RESULT.read_text())
    if not record["gate_passed"] or record["after_selection"]["best_true_rank"] != 1:
        raise RuntimeError("Phase-496 gate is not the reviewed pass")
    if record["checkpoint_sha256"] != sha256_file(SOURCE):
        raise RuntimeError("Phase-496 checkpoint changed")
    return record


def marker_payload() -> dict:
    record = verify_inputs()
    return {
        "phase": 497,
        "status": "development_checkpoint_marker",
        "fixture_index": phase494.FIXTURE_INDEX,
        "swap_count": phase494.SWAP_COUNT,
        "phase496_result_sha256": sha256_file(PHASE496_RESULT),
        "source_sha256": record["checkpoint_sha256"],
        "protocol_sha256": sha256_file(PROTOCOL),
        "script_sha256": sha256_file(Path(__file__)),
        "unrestricted_binary_sha256": sha256_file(variants.UNRESTRICTED_BINARY),
        "enhanced_schedule": ENHANCED_SCHEDULE,
        "enhanced_schedule_sha256": canonical_hash(ENHANCED_SCHEDULE),
    }


def ensure_marker(work_dir: Path) -> None:
    path = work_dir / "objective_marker.json"
    expected = marker_payload()
    if path.exists():
        if json.loads(path.read_text()) != expected:
            raise RuntimeError("Phase-497 marker mismatch")
    else:
        atomic_json(path, expected)


def run(work_dir: Path = DEFAULT_WORK_DIR) -> dict:
    work_dir = Path(work_dir)
    output = work_dir / "phase497_complete_result.json"
    if output.exists():
        raise FileExistsError("refusing to overwrite completed Phase 497")
    ensure_marker(work_dir)
    fixture = variants.make_variant(phase494.FIXTURE_INDEX,
                                    phase494.SWAP_COUNT)
    original_factory = exact.make_fixture
    original_scorer = front.constrained_multistart
    original_schedule = continuation.SCHEDULE

    def supply(fixture_index=0, split="dev"):
        if fixture_index == phase494.FIXTURE_INDEX and split == "dev":
            return fixture
        raise RuntimeError("unexpected fixture request in Phase 497")

    def unrestricted(paths, blocks, pair, quad, restarts, iterations,
                     binary=variants.UNRESTRICTED_BINARY,
                     seed=front.BOARD_SEED):
        return original_scorer(
            paths, blocks, pair, quad, restarts, iterations,
            binary=variants.UNRESTRICTED_BINARY, seed=seed)

    exact.make_fixture = supply
    front.constrained_multistart = unrestricted
    continuation.SCHEDULE = ENHANCED_SCHEDULE
    try:
        current = continuation.bridge_depth(
            SOURCE, 11, ENHANCED_SCHEDULE["lane_a_bridge_parent_keep"],
            ENHANCED_SCHEDULE["lane_a_bridge_children_per_parent"],
            (ENHANCED_SCHEDULE["lane_a_bridge_parent_keep"] *
             ENHANCED_SCHEDULE["lane_a_bridge_children_per_parent"]),
            phase494.FIXTURE_INDEX, "dev", work_dir, "depth11_bridge")
        for depth in range(12, 20):
            keep = (ENHANCED_SCHEDULE["depth13_16_keep"] if depth <= 16
                    else ENHANCED_SCHEDULE["depth17_19_keep"])
            current = continuation.global_depth(
                current, depth, keep, phase494.FIXTURE_INDEX, "dev",
                work_dir, f"depth{depth}")
        result = continuation.final_resolve(
            current, phase494.FIXTURE_INDEX, "dev", work_dir)
    finally:
        continuation.SCHEDULE = original_schedule
        front.constrained_multistart = original_scorer
        exact.make_fixture = original_factory

    summary = {
        "phase": 497,
        "status": "development_proof_complete",
        "faed_scored": False,
        "holdout_consumed": False,
        "fixture_index": phase494.FIXTURE_INDEX,
        "swap_count": phase494.SWAP_COUNT,
        "marker_sha256": sha256_file(work_dir / "objective_marker.json"),
        "top1_exact_order": result["top1_exact_order"],
        "top1_plaintext_accuracy": result["top1_plaintext_accuracy"],
        "exact_order_final_rank": result["exact_order_final_rank"],
        "final_candidates": result["final_candidates"],
    }
    atomic_json(output, summary)
    return summary


def self_test() -> dict:
    record = verify_inputs()
    if ENHANCED_SCHEDULE["coarse_restarts"] != 3:
        raise AssertionError("restart count changed")
    if ENHANCED_SCHEDULE["coarse_iterations"] != 10000:
        raise AssertionError("iteration count changed")
    return {"faed_scored": False, "inputs_verified": True,
            "source_sha256": record["checkpoint_sha256"],
            "schedule_sha256": canonical_hash(ENHANCED_SCHEDULE)}


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
