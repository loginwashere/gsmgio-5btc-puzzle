#!/usr/bin/env python3
"""Two-fixture locked holdout gate for the repaired unrestricted solver."""
from __future__ import annotations

import argparse
import collections
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
import phase499_unrestricted_width19_holdout as phase499
import phase501_holdout0_depth11_repair as phase501


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
PROTOCOL = (REPO_ROOT / "doc" / "Brainstorms" /
            "2026-09-13 - Phase 502 Repaired Unrestricted Width19 Holdout Gate.md")
LOCK_PATH = SCRIPT_DIR / "phase502_execution_lock.json"
DEFAULT_WORK_ROOT = REPO_ROOT / "_work/phase502"
FIXTURE_INDICES = (3, 4)
SPLIT, SWAP_COUNT = "holdout", 3
EARLY_SCHEDULE = dict(continuation.SCHEDULE)
BASE_SCHEDULE = dict(phase497.ENHANCED_SCHEDULE)
BRIDGE_SCHEDULE = dict(phase501.BRIDGE_SCHEDULE)
DEPENDENCIES = (base, exact, front, continuation, rawonly, variants,
                phase497, phase499, phase501)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical_hash(value) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def make_variant(fixture_index: int) -> dict:
    if fixture_index not in FIXTURE_INDICES:
        raise ValueError("fixture index is outside the frozen Phase-502 set")
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
    normalized = base.score_indices(indices, quad) / max(1, len(indices)-3)
    fixture = {
        **original,
        "board_mode": "raw_histogram_partition_violation_holdout",
        "partition_swap_count": SWAP_COUNT,
        "partition_swaps": [list(pair) for pair in swaps],
        "letter_to_code": board, "plaintext": plaintext,
        "plaintext_length": len(plaintext), "minimum_edit_count": edits,
        "edit_fraction": edits/len(plaintext),
        "normalized_quadgram": normalized, "raw": raw, "observed": observed,
        "raw_sha256": hashlib.sha256(raw.encode("ascii")).hexdigest(),
    }
    base.verify_fixture(fixture)
    if collections.Counter(raw) != collections.Counter(rawonly.RAW_COUNTS):
        raise AssertionError("fixture changed the raw histogram")
    if fixture["edit_fraction"] > rawonly.MAX_EDIT_FRACTION:
        raise AssertionError("fixture exceeds the edit gate")
    if normalized < rawonly.MIN_NORMALIZED_QUADGRAM:
        raise AssertionError("fixture exceeds the language gate")
    common, _ = rawonly.training_groups()
    singles = {letter for letter, code in board.items() if len(code) == 1}
    if len(set(common)-singles) != SWAP_COUNT:
        raise AssertionError("fixture has the wrong partition distance")
    return fixture


def expected_lock_payload() -> dict:
    return {
        "phase": 502, "status": "execution_lock",
        "fixture_indices": list(FIXTURE_INDICES), "split": SPLIT,
        "swap_count": SWAP_COUNT, "pass_rule": "2_of_2_exact_top1",
        "protocol_sha256": sha256_file(PROTOCOL),
        "script_sha256": sha256_file(Path(__file__)),
        "dependencies_sha256": {
            str(Path(m.__file__).relative_to(REPO_ROOT)): sha256_file(Path(m.__file__))
            for m in DEPENDENCIES},
        "binaries_sha256": {
            str(path.relative_to(REPO_ROOT)): sha256_file(path)
            for path in (variants.UNRESTRICTED_BINARY,
                         front.invariant.DEFAULT_BINARY)},
        "early_schedule_sha256": canonical_hash(EARLY_SCHEDULE),
        "base_schedule_sha256": canonical_hash(BASE_SCHEDULE),
        "bridge_schedule_sha256": canonical_hash(BRIDGE_SCHEDULE),
    }


def verify_lock() -> dict:
    if not LOCK_PATH.is_file():
        raise RuntimeError("Phase-502 execution lock is absent")
    actual = json.loads(LOCK_PATH.read_text())
    if actual != expected_lock_payload():
        raise RuntimeError("Phase-502 execution lock mismatch")
    return actual


def marker_payload(fixture_index: int) -> dict:
    verify_lock()
    fixture = make_variant(fixture_index)
    return {
        "phase": 502, "status": "holdout_checkpoint_marker",
        "fixture_index": fixture_index, "split": SPLIT,
        "partition_swaps": fixture["partition_swaps"],
        "fixture_raw_sha256": fixture["raw_sha256"],
        "fixture_plaintext_sha256": hashlib.sha256(
            fixture["plaintext"].encode("ascii")).hexdigest(),
        "execution_lock_sha256": sha256_file(LOCK_PATH),
        "early_schedule_sha256": canonical_hash(EARLY_SCHEDULE),
        "base_schedule_sha256": canonical_hash(BASE_SCHEDULE),
        "bridge_schedule_sha256": canonical_hash(BRIDGE_SCHEDULE),
    }


def ensure_marker(work_dir: Path, fixture_index: int) -> None:
    marker = Path(work_dir) / "objective_marker.json"
    expected = marker_payload(fixture_index)
    if marker.exists():
        if json.loads(marker.read_text()) != expected:
            raise RuntimeError("Phase-502 marker mismatch")
    else:
        phase499.atomic_json(marker, expected)


def validated_front(work_dir: Path, fixture_index: int) -> Path | None:
    result, checkpoint = work_dir/"result.json", work_dir/"depth7_refined.npz"
    if not result.exists() and not checkpoint.exists():
        return None
    if not result.exists() or not checkpoint.exists():
        raise RuntimeError("partial Phase-502 front checkpoint")
    record = json.loads(result.read_text())
    expected = {"fixture_index": fixture_index, "split": SPLIT,
                "schedule_sha256": front.schedule_sha256(),
                "checkpoint": str(checkpoint)}
    for key, value in expected.items():
        if record.get(key) != value:
            raise RuntimeError(f"Phase-502 front has wrong {key}")
    return checkpoint


def run_fixture(fixture_index: int, work_root: Path = DEFAULT_WORK_ROOT) -> dict:
    verify_lock()
    if fixture_index not in FIXTURE_INDICES:
        raise ValueError("fixture index is outside the frozen Phase-502 set")
    work_dir = Path(work_root)/f"i{fixture_index}_s{SWAP_COUNT}"
    output = work_dir/"phase502_complete_result.json"
    if output.exists():
        return json.loads(output.read_text())
    ensure_marker(work_dir, fixture_index)
    fixture = make_variant(fixture_index)
    models = exact.train_profile_models()
    original_factory, original_trainer = exact.make_fixture, exact.train_profile_models
    original_scorer, original_schedule = front.constrained_multistart, continuation.SCHEDULE

    def supply(requested_index=0, split="dev"):
        if requested_index == fixture_index and split == SPLIT:
            return fixture
        raise RuntimeError("unexpected fixture request in Phase 502")

    def unrestricted(paths, blocks, pair, quad, restarts, iterations,
                     binary=variants.UNRESTRICTED_BINARY, seed=front.BOARD_SEED):
        return original_scorer(paths, blocks, pair, quad, restarts, iterations,
                               binary=variants.UNRESTRICTED_BINARY, seed=seed)

    exact.make_fixture, exact.train_profile_models = supply, lambda: models
    front.constrained_multistart = unrestricted
    try:
        source = validated_front(work_dir, fixture_index)
        if source is None:
            front.run_front(fixture_index, SPLIT, work_dir,
                            board_binary=variants.UNRESTRICTED_BINARY)
            source = validated_front(work_dir, fixture_index)
        continuation.SCHEDULE = EARLY_SCHEDULE
        current = continuation.lane_a_depth8(source, fixture_index, SPLIT, work_dir)
        current = continuation.global_depth(
            current, 9, EARLY_SCHEDULE["lane_a_depth8_keep"], fixture_index,
            SPLIT, work_dir, "depth9")
        continuation.SCHEDULE = BASE_SCHEDULE
        current = continuation.global_depth(
            current, 10, BASE_SCHEDULE["lane_a_depth8_keep"], fixture_index,
            SPLIT, work_dir, "depth10")
        continuation.SCHEDULE = BRIDGE_SCHEDULE
        current = continuation.bridge_depth(
            current, 11, BRIDGE_SCHEDULE["lane_a_bridge_parent_keep"],
            BRIDGE_SCHEDULE["lane_a_bridge_children_per_parent"],
            BRIDGE_SCHEDULE["lane_a_bridge_parent_keep"] *
            BRIDGE_SCHEDULE["lane_a_bridge_children_per_parent"],
            fixture_index, SPLIT, work_dir, "depth11_bridge")
        continuation.SCHEDULE = BASE_SCHEDULE
        for depth in range(12, 20):
            keep = (BASE_SCHEDULE["depth13_16_keep"] if depth <= 16
                    else BASE_SCHEDULE["depth17_19_keep"])
            current = continuation.global_depth(
                current, depth, keep, fixture_index, SPLIT, work_dir,
                f"depth{depth}")
        result = continuation.final_resolve(current, fixture_index, SPLIT, work_dir)
    finally:
        continuation.SCHEDULE = original_schedule
        front.constrained_multistart = original_scorer
        exact.train_profile_models, exact.make_fixture = original_trainer, original_factory
    summary = {
        "phase": 502, "status": "holdout_fixture_complete",
        "faed_scored": False, "holdout_consumed": True,
        "fixture_index": fixture_index,
        "marker_sha256": sha256_file(work_dir/"objective_marker.json"),
        "top1_exact_order": result["top1_exact_order"],
        "top1_plaintext_accuracy": result["top1_plaintext_accuracy"],
        "exact_order_final_rank": result["exact_order_final_rank"],
        "final_candidates": result["final_candidates"],
    }
    phase499.atomic_json(output, summary)
    return summary


def aggregate(work_root: Path = DEFAULT_WORK_ROOT) -> dict:
    verify_lock()
    records = []
    for index in FIXTURE_INDICES:
        root = Path(work_root)/f"i{index}_s{SWAP_COUNT}"
        path = root/"phase502_complete_result.json"
        if not path.is_file():
            raise RuntimeError(f"fixture {index} is incomplete")
        record = json.loads(path.read_text())
        if record.get("marker_sha256") != sha256_file(root/"objective_marker.json"):
            raise RuntimeError(f"fixture {index} marker mismatch")
        records.append(record)
    exact_count = sum(r["top1_exact_order"] for r in records)
    result = {"phase": 502, "status": "holdout_gate_complete",
              "faed_scored": False, "fixtures": list(FIXTURE_INDICES),
              "exact_top1": exact_count, "gate_passed": exact_count == 2,
              "records": [{k: r[k] for k in ("fixture_index",
                  "top1_exact_order", "top1_plaintext_accuracy",
                  "exact_order_final_rank", "marker_sha256")} for r in records]}
    phase499.atomic_json(Path(work_root)/"phase502_holdout_result.json", result)
    return result


def self_test() -> dict:
    fixture = make_variant(3)
    if fixture["split"] != SPLIT or fixture["partition_swap_count"] != 3:
        raise AssertionError("fixture identity changed")
    differing = {k for k in BRIDGE_SCHEDULE
                 if BRIDGE_SCHEDULE[k] != BASE_SCHEDULE[k]}
    if differing != {"coarse_restarts", "coarse_iterations"}:
        raise AssertionError("repair changes unexpected fields")
    return {"faed_scored": False, "fixtures": list(FIXTURE_INDICES),
            "changed_fields": sorted(differing)}


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--verify-lock", action="store_true")
    group.add_argument("--run-fixture", type=int, choices=FIXTURE_INDICES)
    group.add_argument("--aggregate", action="store_true")
    parser.add_argument("--work-root", type=Path, default=DEFAULT_WORK_ROOT)
    args = parser.parse_args()
    if args.self_test: result = self_test()
    elif args.verify_lock: result = verify_lock()
    elif args.aggregate: result = aggregate(args.work_root)
    else: result = run_fixture(args.run_fixture, args.work_root)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

