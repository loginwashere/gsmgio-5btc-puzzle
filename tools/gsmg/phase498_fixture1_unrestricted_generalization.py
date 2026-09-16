#!/usr/bin/env python3
"""Checkpointed high-iteration unrestricted proof on dev fixture 1."""
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


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
PROTOCOL = (REPO_ROOT / "doc" / "Brainstorms" /
            "2026-09-13 - Phase 498 Fixture1 Unrestricted Generalization.md")
DEFAULT_WORK_DIR = REPO_ROOT / "_work" / "phase498" / "i1_s3"
FIXTURE_INDEX, SWAP_COUNT = 1, 3
EARLY_SCHEDULE = dict(continuation.SCHEDULE)
LATE_SCHEDULE = dict(phase497.ENHANCED_SCHEDULE)


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


def marker_payload() -> dict:
    fixture = variants.make_variant(FIXTURE_INDEX, SWAP_COUNT)
    return {
        "phase": 498,
        "status": "development_checkpoint_marker",
        "fixture_index": FIXTURE_INDEX,
        "swap_count": SWAP_COUNT,
        "normalized_quadgram": fixture["normalized_quadgram"],
        "fixture_raw_sha256": fixture["raw_sha256"],
        "fixture_plaintext_sha256": hashlib.sha256(
            fixture["plaintext"].encode("ascii")).hexdigest(),
        "protocol_sha256": sha256_file(PROTOCOL),
        "script_sha256": sha256_file(Path(__file__)),
        "files_sha256": {
            str(Path(module.__file__).relative_to(REPO_ROOT)): sha256_file(
                Path(module.__file__))
            for module in (front, continuation, variants, phase497)
        },
        "unrestricted_binary_sha256": sha256_file(variants.UNRESTRICTED_BINARY),
        "front_schedule_sha256": front.schedule_sha256(),
        "early_schedule_sha256": canonical_hash(EARLY_SCHEDULE),
        "late_schedule_sha256": canonical_hash(LATE_SCHEDULE),
    }


def ensure_marker(work_dir: Path) -> None:
    marker = work_dir / "objective_marker.json"
    expected = marker_payload()
    if marker.exists():
        if json.loads(marker.read_text()) != expected:
            raise RuntimeError("Phase-498 marker mismatch")
    else:
        atomic_json(marker, expected)


def validated_front(work_dir: Path) -> Path | None:
    record_path = work_dir / "result.json"
    checkpoint = work_dir / "depth7_refined.npz"
    if not record_path.exists() and not checkpoint.exists():
        return None
    if not record_path.exists() or not checkpoint.exists():
        raise RuntimeError("partial Phase-498 front checkpoint")
    record = json.loads(record_path.read_text())
    expected = {
        "fixture_index": FIXTURE_INDEX,
        "split": "dev",
        "schedule_sha256": front.schedule_sha256(),
        "checkpoint": str(checkpoint),
    }
    for key, value in expected.items():
        if record.get(key) != value:
            raise RuntimeError(f"Phase-498 front has wrong {key}")
    return checkpoint


def run(work_dir: Path = DEFAULT_WORK_DIR) -> dict:
    work_dir = Path(work_dir)
    output = work_dir / "phase498_complete_result.json"
    if output.exists():
        raise FileExistsError("refusing to overwrite completed Phase 498")
    ensure_marker(work_dir)
    fixture = variants.make_variant(FIXTURE_INDEX, SWAP_COUNT)
    models = exact.train_profile_models()
    original_factory = exact.make_fixture
    original_trainer = exact.train_profile_models
    original_scorer = front.constrained_multistart
    original_schedule = continuation.SCHEDULE

    def supply(fixture_index=0, split="dev"):
        if fixture_index == FIXTURE_INDEX and split == "dev":
            return fixture
        raise RuntimeError("unexpected fixture request in Phase 498")

    def unrestricted(paths, blocks, pair, quad, restarts, iterations,
                     binary=variants.UNRESTRICTED_BINARY,
                     seed=front.BOARD_SEED):
        return original_scorer(
            paths, blocks, pair, quad, restarts, iterations,
            binary=variants.UNRESTRICTED_BINARY, seed=seed)

    exact.make_fixture = supply
    exact.train_profile_models = lambda: models
    front.constrained_multistart = unrestricted
    try:
        source = validated_front(work_dir)
        if source is None:
            front.run_front(FIXTURE_INDEX, "dev", work_dir,
                            board_binary=variants.UNRESTRICTED_BINARY)
            source = validated_front(work_dir)

        continuation.SCHEDULE = EARLY_SCHEDULE
        depth8 = continuation.lane_a_depth8(
            source, FIXTURE_INDEX, "dev", work_dir)
        depth9 = continuation.global_depth(
            depth8, 9, EARLY_SCHEDULE["lane_a_depth8_keep"], FIXTURE_INDEX,
            "dev", work_dir, "depth9")

        continuation.SCHEDULE = LATE_SCHEDULE
        current = continuation.global_depth(
            depth9, 10, LATE_SCHEDULE["lane_a_depth8_keep"], FIXTURE_INDEX,
            "dev", work_dir, "depth10")
        current = continuation.bridge_depth(
            current, 11, LATE_SCHEDULE["lane_a_bridge_parent_keep"],
            LATE_SCHEDULE["lane_a_bridge_children_per_parent"],
            (LATE_SCHEDULE["lane_a_bridge_parent_keep"] *
             LATE_SCHEDULE["lane_a_bridge_children_per_parent"]),
            FIXTURE_INDEX, "dev", work_dir, "depth11_bridge")
        for depth in range(12, 20):
            keep = (LATE_SCHEDULE["depth13_16_keep"] if depth <= 16
                    else LATE_SCHEDULE["depth17_19_keep"])
            current = continuation.global_depth(
                current, depth, keep, FIXTURE_INDEX, "dev", work_dir,
                f"depth{depth}")
        result = continuation.final_resolve(
            current, FIXTURE_INDEX, "dev", work_dir)
    finally:
        continuation.SCHEDULE = original_schedule
        front.constrained_multistart = original_scorer
        exact.train_profile_models = original_trainer
        exact.make_fixture = original_factory

    summary = {
        "phase": 498,
        "status": "development_generalization_complete",
        "faed_scored": False,
        "holdout_consumed": False,
        "fixture_index": FIXTURE_INDEX,
        "swap_count": SWAP_COUNT,
        "marker_sha256": sha256_file(work_dir / "objective_marker.json"),
        "top1_exact_order": result["top1_exact_order"],
        "top1_plaintext_accuracy": result["top1_plaintext_accuracy"],
        "exact_order_final_rank": result["exact_order_final_rank"],
        "final_candidates": result["final_candidates"],
    }
    atomic_json(output, summary)
    return summary


def self_test() -> dict:
    marker = marker_payload()
    if marker["normalized_quadgram"] >= -4.6236189175065805:
        raise AssertionError("fixture 1 is not harder than Phase-497 fixture 3")
    if EARLY_SCHEDULE["coarse_iterations"] != 2000:
        raise AssertionError("early schedule changed")
    if LATE_SCHEDULE["coarse_iterations"] != 10000:
        raise AssertionError("late schedule changed")
    return {"faed_scored": False, "fixture_index": FIXTURE_INDEX,
            "normalized_quadgram": marker["normalized_quadgram"]}


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
