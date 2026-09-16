#!/usr/bin/env python3
"""Post-hoc depth-11 repair proof on consumed Phase-499 holdout fixture 0."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import phase484x_exact_faed_profile_power_probe as exact
import phase490_width19_dual_lane_dev as front
import phase490_width19_checkpointed_dual_lane as continuation
import phase493_partial_unrestricted_board_diagnostic as variants
import phase497_high_iteration_unrestricted_continuation as phase497
import phase499_unrestricted_width19_holdout as phase499
import phase500_holdout0_depth11_bridge_postmortem as phase500


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
PROTOCOL = (REPO_ROOT / "doc" / "Brainstorms" /
            "2026-09-13 - Phase 501 Holdout0 Depth11 Repair Proof.md")
SOURCE = phase500.SOURCE
SOURCE_RECORD = phase500.SOURCE_RECORD
PHASE500_RESULT = phase500.DEFAULT_OUTPUT
DEFAULT_WORK_DIR = REPO_ROOT / "_work/phase501/holdout0_repair"
BASE_SCHEDULE = dict(phase497.ENHANCED_SCHEDULE)
BRIDGE_SCHEDULE = {**BASE_SCHEDULE, "coarse_restarts": 8,
                   "coarse_iterations": 20000}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical_hash(value) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def verify_inputs() -> dict:
    phase499.verify_lock()
    phase500.verify_inputs()
    if not PHASE500_RESULT.is_file():
        raise RuntimeError("Phase-500 postmortem result is absent")
    result = json.loads(PHASE500_RESULT.read_text())
    production = result["arms"]["production"]["true_children"]
    high = result["arms"]["high_budget"]["true_children"]
    if ([r["local_rank"] for r in production] != [16, 11] or
            [r["local_rank"] for r in high] != [2, 1]):
        raise RuntimeError("Phase-500 diagnosis is not the reviewed result")
    return result


def marker_payload() -> dict:
    verify_inputs()
    return {
        "phase": 501,
        "status": "posthoc_repair_marker",
        "fixture_index": 0,
        "split": "holdout",
        "already_consumed": True,
        "protocol_sha256": sha256_file(PROTOCOL),
        "script_sha256": sha256_file(Path(__file__)),
        "phase499_lock_sha256": sha256_file(phase499.LOCK_PATH),
        "source_sha256": sha256_file(SOURCE),
        "source_record_sha256": sha256_file(SOURCE_RECORD),
        "phase500_result_sha256": sha256_file(PHASE500_RESULT),
        "base_schedule_sha256": canonical_hash(BASE_SCHEDULE),
        "bridge_schedule_sha256": canonical_hash(BRIDGE_SCHEDULE),
        "unrestricted_binary_sha256": sha256_file(variants.UNRESTRICTED_BINARY),
    }


def ensure_marker(work_dir: Path) -> None:
    marker = Path(work_dir) / "objective_marker.json"
    expected = marker_payload()
    if marker.exists():
        if json.loads(marker.read_text()) != expected:
            raise RuntimeError("Phase-501 marker mismatch")
    else:
        phase499.atomic_json(marker, expected)


def run(work_dir: Path = DEFAULT_WORK_DIR) -> dict:
    work_dir = Path(work_dir)
    output = work_dir / "phase501_complete_result.json"
    if output.exists():
        return json.loads(output.read_text())
    ensure_marker(work_dir)
    fixture = phase499.make_holdout_variant(0)
    original_factory = exact.make_fixture
    original_scorer = front.constrained_multistart
    original_schedule = continuation.SCHEDULE

    def supply(fixture_index=0, split="dev"):
        if fixture_index == 0 and split == "holdout":
            return fixture
        raise RuntimeError("unexpected fixture request in Phase 501")

    def unrestricted(paths, blocks, pair, quad, restarts, iterations,
                     binary=variants.UNRESTRICTED_BINARY,
                     seed=front.BOARD_SEED):
        return original_scorer(
            paths, blocks, pair, quad, restarts, iterations,
            binary=variants.UNRESTRICTED_BINARY, seed=seed)

    exact.make_fixture = supply
    front.constrained_multistart = unrestricted
    try:
        continuation.SCHEDULE = BRIDGE_SCHEDULE
        current = continuation.bridge_depth(
            SOURCE, 11, BRIDGE_SCHEDULE["lane_a_bridge_parent_keep"],
            BRIDGE_SCHEDULE["lane_a_bridge_children_per_parent"],
            (BRIDGE_SCHEDULE["lane_a_bridge_parent_keep"] *
             BRIDGE_SCHEDULE["lane_a_bridge_children_per_parent"]),
            0, "holdout", work_dir, "depth11_bridge")
        continuation.SCHEDULE = BASE_SCHEDULE
        for depth in range(12, 20):
            keep = (BASE_SCHEDULE["depth13_16_keep"] if depth <= 16
                    else BASE_SCHEDULE["depth17_19_keep"])
            current = continuation.global_depth(
                current, depth, keep, 0, "holdout", work_dir,
                f"depth{depth}")
        result = continuation.final_resolve(current, 0, "holdout", work_dir)
    finally:
        continuation.SCHEDULE = original_schedule
        front.constrained_multistart = original_scorer
        exact.make_fixture = original_factory
    summary = {
        "phase": 501,
        "status": "posthoc_repair_complete",
        "faed_scored": False,
        "holdout_gate_repaired": False,
        "fixture_already_consumed": True,
        "fixture_index": 0,
        "marker_sha256": sha256_file(work_dir / "objective_marker.json"),
        "top1_exact_order": result["top1_exact_order"],
        "top1_plaintext_accuracy": result["top1_plaintext_accuracy"],
        "exact_order_final_rank": result["exact_order_final_rank"],
        "final_candidates": result["final_candidates"],
    }
    phase499.atomic_json(output, summary)
    return summary


def self_test() -> dict:
    verify_inputs()
    if BASE_SCHEDULE["coarse_iterations"] != 10000:
        raise AssertionError("base schedule changed")
    if (BRIDGE_SCHEDULE["coarse_restarts"],
            BRIDGE_SCHEDULE["coarse_iterations"]) != (8, 20000):
        raise AssertionError("bridge repair budget changed")
    differing = {key for key in BRIDGE_SCHEDULE
                 if BRIDGE_SCHEDULE[key] != BASE_SCHEDULE[key]}
    if differing != {"coarse_restarts", "coarse_iterations"}:
        raise AssertionError("bridge repair changed another field")
    return {"faed_scored": False, "posthoc": True,
            "holdout_gate_repaired": False,
            "changed_fields": sorted(differing)}


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

