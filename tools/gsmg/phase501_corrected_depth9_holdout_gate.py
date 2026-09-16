#!/usr/bin/env python3
"""Checkpointed three-fixture holdout gate with the corrected depth-9 budget.

Phase 499 raised unrestricted board-anneal coarse iterations from 2,000 to
10,000 only starting at depth 10. Holdout fixture 0 failed that gate: its
truth collapsed to rank 45,203/31,532 at depth 9 under the 2,000-iteration
budget, and the gate closed per its own first-failure stop rule without
spending fixtures 1 or 2. Phase 500 showed the same fixture's depth-9 step
recovers to rank 1 at 10,000 iterations, diagnosing this as the same
under-annealing failure mode already fixed at depth 10 in Phase 495/496.

This phase evaluates the corrected schedule -- 10,000 coarse iterations
starting at depth 9 instead of depth 10 -- on three holdout fixtures never
used to diagnose or tune that fix: 2 (reserved but unspent by Phase 499),
and 3 and 5 (fresh, previously untouched holdout indices). Fixture 0 is
deliberately excluded: re-passing it would only confirm the fix against the
instance that motivated it. Fixtures 1 and 4 independently fail the frozen
construction-time language gate under this three-swap variant and are
skipped for that reason, not for difficulty or solver behavior.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

import phase484a_raw_symbol_vic_solver as base
import phase484x_exact_faed_profile_power_probe as exact
import phase490_width19_dual_lane_dev as front
import phase490_width19_checkpointed_dual_lane as continuation
import phase491_raw_histogram_fixture as rawonly
import phase493_partial_unrestricted_board_diagnostic as variants
import phase497_high_iteration_unrestricted_continuation as phase497


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
PROTOCOL = (REPO_ROOT / "doc" / "Brainstorms" /
            "2026-09-13 - Phase 501 Corrected Depth9 Holdout Gate.md")
LOCK_PATH = SCRIPT_DIR / "phase501_execution_lock.json"
DEFAULT_WORK_ROOT = REPO_ROOT / "_work" / "phase501"
FIXTURE_INDICES = (2, 3, 5)
SPLIT = "holdout"
SWAP_COUNT = 3
EARLY_SCHEDULE = dict(continuation.SCHEDULE)
LATE_SCHEDULE = dict(phase497.ENHANCED_SCHEDULE)
DEPENDENCIES = (base, exact, front, continuation, rawonly, variants, phase497)


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


def make_holdout_variant(fixture_index: int) -> dict:
    if fixture_index not in FIXTURE_INDICES:
        raise ValueError("fixture index is outside the frozen holdout set")
    original = rawonly.make_fixture(fixture_index, SPLIT)
    profile = rawonly.sampled_token_profile(fixture_index, SPLIT)
    swaps = variants.selected_swaps(original, SWAP_COUNT)
    board = dict(original["letter_to_code"])
    for left, right in swaps:
        board[left], board[right] = board[right], board[left]
    target = {letter: profile["token_counts"][code]
              for letter, code in board.items()}
    quad, _ = base.load_language_model()
    plaintext, edits = rawonly.minimum_edit_plaintext(
        original["source_plaintext"], target, quad)
    raw = base.encode_plaintext(plaintext, board)
    observed = base.Geometry(len(raw), 19).encrypt(raw, original["order"])
    indices = np.asarray([base.LETTER_ALPHABET.index(x) for x in plaintext])
    normalized = base.score_indices(indices, quad) / max(1, len(indices) - 3)
    fixture = {
        **original,
        "board_mode": "raw_histogram_partition_violation_holdout",
        "partition_swap_count": SWAP_COUNT,
        "partition_swaps": [list(pair) for pair in swaps],
        "letter_to_code": board,
        "plaintext": plaintext,
        "plaintext_length": len(plaintext),
        "minimum_edit_count": edits,
        "edit_fraction": edits / len(plaintext),
        "normalized_quadgram": normalized,
        "raw": raw,
        "observed": observed,
        "raw_sha256": hashlib.sha256(raw.encode("ascii")).hexdigest(),
    }
    base.verify_fixture(fixture)
    import collections
    if collections.Counter(raw) != collections.Counter(rawonly.RAW_COUNTS):
        raise AssertionError("holdout variant changed the raw histogram")
    if fixture["edit_fraction"] > rawonly.MAX_EDIT_FRACTION:
        raise AssertionError("holdout variant exceeds the edit gate")
    if normalized < rawonly.MIN_NORMALIZED_QUADGRAM:
        raise AssertionError("holdout variant exceeds the language gate")
    common, _ = rawonly.training_groups()
    singles = {letter for letter, code in board.items() if len(code) == 1}
    if len(set(common) - singles) != SWAP_COUNT:
        raise AssertionError("holdout board has the wrong partition distance")
    return fixture


def expected_lock_payload() -> dict:
    return {
        "phase": 501,
        "status": "execution_lock",
        "fixture_indices": list(FIXTURE_INDICES),
        "split": SPLIT,
        "swap_count": SWAP_COUNT,
        "pass_rule": "3_of_3_exact_top1",
        "corrected_budget_start_depth": 9,
        "protocol_sha256": sha256_file(PROTOCOL),
        "script_sha256": sha256_file(Path(__file__)),
        "dependencies_sha256": {
            str(Path(module.__file__).relative_to(REPO_ROOT)): sha256_file(
                Path(module.__file__)) for module in DEPENDENCIES
        },
        "binaries_sha256": {
            str(path.relative_to(REPO_ROOT)): sha256_file(path)
            for path in (variants.UNRESTRICTED_BINARY,
                         front.invariant.DEFAULT_BINARY)
        },
        "front_schedule_sha256": front.schedule_sha256(),
        "early_schedule_sha256": canonical_hash(EARLY_SCHEDULE),
        "late_schedule_sha256": canonical_hash(LATE_SCHEDULE),
    }


def verify_lock() -> dict:
    if not LOCK_PATH.is_file():
        raise RuntimeError("Phase-501 execution lock is absent")
    actual = json.loads(LOCK_PATH.read_text())
    expected = expected_lock_payload()
    if actual != expected:
        raise RuntimeError("Phase-501 execution lock mismatch")
    return actual


def marker_payload(fixture_index: int) -> dict:
    lock = verify_lock()
    fixture = make_holdout_variant(fixture_index)
    return {
        "phase": 501,
        "status": "holdout_checkpoint_marker",
        "fixture_index": fixture_index,
        "split": SPLIT,
        "swap_count": SWAP_COUNT,
        "partition_swaps": fixture["partition_swaps"],
        "fixture_raw_sha256": fixture["raw_sha256"],
        "fixture_plaintext_sha256": hashlib.sha256(
            fixture["plaintext"].encode("ascii")).hexdigest(),
        "execution_lock_sha256": sha256_file(LOCK_PATH),
        "locked_protocol_sha256": lock["protocol_sha256"],
        "early_schedule_sha256": canonical_hash(EARLY_SCHEDULE),
        "late_schedule_sha256": canonical_hash(LATE_SCHEDULE),
    }


def ensure_marker(work_dir: Path, fixture_index: int) -> None:
    marker = work_dir / "objective_marker.json"
    expected = marker_payload(fixture_index)
    if marker.exists():
        if json.loads(marker.read_text()) != expected:
            raise RuntimeError("Phase-501 marker mismatch")
    else:
        atomic_json(marker, expected)


def validated_front(work_dir: Path, fixture_index: int) -> Path | None:
    record_path = work_dir / "result.json"
    checkpoint = work_dir / "depth7_refined.npz"
    if not record_path.exists() and not checkpoint.exists():
        return None
    if not record_path.exists() or not checkpoint.exists():
        raise RuntimeError("partial Phase-501 front checkpoint")
    record = json.loads(record_path.read_text())
    expected = {
        "fixture_index": fixture_index,
        "split": SPLIT,
        "schedule_sha256": front.schedule_sha256(),
        "checkpoint": str(checkpoint),
    }
    for key, value in expected.items():
        if record.get(key) != value:
            raise RuntimeError(f"Phase-501 front has wrong {key}")
    return checkpoint


def run_fixture(fixture_index: int, work_root: Path = DEFAULT_WORK_ROOT) -> dict:
    verify_lock()
    if fixture_index not in FIXTURE_INDICES:
        raise ValueError("fixture index is outside the frozen holdout set")
    work_dir = Path(work_root) / f"i{fixture_index}_s{SWAP_COUNT}"
    output = work_dir / "phase501_complete_result.json"
    if output.exists():
        return json.loads(output.read_text())
    ensure_marker(work_dir, fixture_index)
    fixture = make_holdout_variant(fixture_index)
    models = exact.train_profile_models()
    original_factory = exact.make_fixture
    original_trainer = exact.train_profile_models
    original_scorer = front.constrained_multistart
    original_schedule = continuation.SCHEDULE

    def supply(requested_index=0, split="dev"):
        if requested_index == fixture_index and split == SPLIT:
            return fixture
        raise RuntimeError("unexpected fixture request in Phase 501")

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
        source = validated_front(work_dir, fixture_index)
        if source is None:
            front.run_front(fixture_index, SPLIT, work_dir,
                            board_binary=variants.UNRESTRICTED_BINARY)
            source = validated_front(work_dir, fixture_index)

        continuation.SCHEDULE = EARLY_SCHEDULE
        depth8 = continuation.lane_a_depth8(
            source, fixture_index, SPLIT, work_dir)

        # Corrected budget: 10,000-iteration unrestricted annealing starts at
        # depth 9 (Phase 499 started it at depth 10). See Phase 500.
        continuation.SCHEDULE = LATE_SCHEDULE
        current = continuation.global_depth(
            depth8, 9, LATE_SCHEDULE["lane_a_depth8_keep"], fixture_index,
            SPLIT, work_dir, "depth9")
        current = continuation.global_depth(
            current, 10, LATE_SCHEDULE["lane_a_depth8_keep"], fixture_index,
            SPLIT, work_dir, "depth10")
        current = continuation.bridge_depth(
            current, 11, LATE_SCHEDULE["lane_a_bridge_parent_keep"],
            LATE_SCHEDULE["lane_a_bridge_children_per_parent"],
            (LATE_SCHEDULE["lane_a_bridge_parent_keep"] *
             LATE_SCHEDULE["lane_a_bridge_children_per_parent"]),
            fixture_index, SPLIT, work_dir, "depth11_bridge")
        for depth in range(12, 20):
            keep = (LATE_SCHEDULE["depth13_16_keep"] if depth <= 16
                    else LATE_SCHEDULE["depth17_19_keep"])
            current = continuation.global_depth(
                current, depth, keep, fixture_index, SPLIT, work_dir,
                f"depth{depth}")
        result = continuation.final_resolve(
            current, fixture_index, SPLIT, work_dir)
    finally:
        continuation.SCHEDULE = original_schedule
        front.constrained_multistart = original_scorer
        exact.train_profile_models = original_trainer
        exact.make_fixture = original_factory

    summary = {
        "phase": 501,
        "status": "holdout_fixture_complete",
        "faed_scored": False,
        "holdout_consumed": True,
        "fixture_index": fixture_index,
        "swap_count": SWAP_COUNT,
        "marker_sha256": sha256_file(work_dir / "objective_marker.json"),
        "top1_exact_order": result["top1_exact_order"],
        "top1_plaintext_accuracy": result["top1_plaintext_accuracy"],
        "exact_order_final_rank": result["exact_order_final_rank"],
        "final_candidates": result["final_candidates"],
    }
    atomic_json(output, summary)
    return summary


def aggregate(work_root: Path = DEFAULT_WORK_ROOT) -> dict:
    verify_lock()
    records = []
    for fixture_index in FIXTURE_INDICES:
        work_dir = Path(work_root) / f"i{fixture_index}_s{SWAP_COUNT}"
        path = work_dir / "phase501_complete_result.json"
        if not path.is_file():
            raise RuntimeError(f"fixture {fixture_index} is incomplete")
        record = json.loads(path.read_text())
        if (record.get("fixture_index") != fixture_index or
                record.get("marker_sha256") != sha256_file(
                    work_dir / "objective_marker.json")):
            raise RuntimeError(f"fixture {fixture_index} result mismatch")
        records.append(record)
    exact_count = sum(record["top1_exact_order"] for record in records)
    result = {
        "phase": 501,
        "status": "holdout_gate_complete",
        "faed_scored": False,
        "fixtures": list(FIXTURE_INDICES),
        "exact_top1": exact_count,
        "gate_passed": exact_count == len(FIXTURE_INDICES),
        "records": [{key: record[key] for key in (
            "fixture_index", "top1_exact_order", "top1_plaintext_accuracy",
            "exact_order_final_rank", "marker_sha256")} for record in records],
    }
    atomic_json(Path(work_root) / "phase501_holdout_result.json", result)
    return result


def self_test() -> dict:
    fixture = make_holdout_variant(FIXTURE_INDICES[0])
    if fixture["split"] != SPLIT or fixture["partition_swap_count"] != 3:
        raise AssertionError("holdout fixture identity changed")
    if EARLY_SCHEDULE["coarse_iterations"] != 2000:
        raise AssertionError("early schedule changed")
    if LATE_SCHEDULE["coarse_iterations"] != 10000:
        raise AssertionError("late schedule changed")
    if 0 in FIXTURE_INDICES:
        raise AssertionError("tuning-tainted fixture 0 must be excluded")
    import ast
    tree = ast.parse(Path(__file__).read_text())
    imports = {
        alias.name for node in ast.walk(tree)
        if isinstance(node, ast.Import) for alias in node.names
    } | {
        node.module for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    if "data" in imports:
        raise AssertionError("Phase 501 imports puzzle data")
    return {"faed_scored": False, "fixtures": list(FIXTURE_INDICES),
            "split": SPLIT, "swap_count": SWAP_COUNT}


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--verify-lock", action="store_true")
    group.add_argument("--run-fixture", type=int, choices=FIXTURE_INDICES)
    group.add_argument("--aggregate", action="store_true")
    parser.add_argument("--work-root", type=Path, default=DEFAULT_WORK_ROOT)
    args = parser.parse_args()
    if args.self_test:
        result = self_test()
    elif args.verify_lock:
        result = verify_lock()
    elif args.aggregate:
        result = aggregate(args.work_root)
    else:
        result = run_fixture(args.run_fixture, args.work_root)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
