#!/usr/bin/env python3
"""Checkpointed unrestricted-board Phase-490 proof on one synthetic fixture."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import phase484x_exact_faed_profile_power_probe as old_profile
import phase490_width19_dual_lane_dev as front
import phase490_width19_checkpointed_dual_lane as continuation
import phase493_partial_unrestricted_board_diagnostic as variants


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
PROTOCOL = (REPO_ROOT / "doc" / "Brainstorms" /
            "2026-09-13 - Phase 494 Unrestricted Board Full-Pipeline Proof.md")
DEFAULT_WORK_DIR = REPO_ROOT / "_work" / "phase494" / "i3_s3"
FIXTURE_INDEX, SWAP_COUNT = 3, 3
UNRESTRICTED_BINARY = variants.UNRESTRICTED_BINARY


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def marker_payload() -> dict:
    fixture = variants.make_variant(FIXTURE_INDEX, SWAP_COUNT)
    files = (Path(__file__), PROTOCOL, Path(front.__file__),
             Path(continuation.__file__), Path(variants.__file__),
             UNRESTRICTED_BINARY)
    return {
        "phase": 494, "status": "development_objective_checkpoint_marker",
        "fixture_index": FIXTURE_INDEX, "swap_count": SWAP_COUNT,
        "fixture_raw_sha256": fixture["raw_sha256"],
        "fixture_plaintext_sha256": hashlib.sha256(
            fixture["plaintext"].encode("ascii")).hexdigest(),
        "front_schedule_sha256": front.schedule_sha256(),
        "continuation_schedule_sha256": continuation.schedule_sha256(),
        "objective": "unrestricted_25_slot_board_annealing_at_every_partial_depth",
        "files_sha256": {str(path.relative_to(REPO_ROOT)): sha256_file(path)
                         for path in files},
    }


def ensure_marker(work_dir: Path) -> None:
    path = work_dir / "objective_marker.json"
    expected = marker_payload()
    if path.exists():
        if json.loads(path.read_text()) != expected:
            raise RuntimeError("Phase 494 checkpoint objective marker mismatch")
    else:
        atomic_json(path, expected)


def run(work_dir: Path = DEFAULT_WORK_DIR) -> dict:
    work_dir = Path(work_dir)
    output = work_dir / "phase494_complete_result.json"
    if output.exists():
        raise FileExistsError("refusing to overwrite completed proof")
    ensure_marker(work_dir)
    fixture = variants.make_variant(FIXTURE_INDEX, SWAP_COUNT)
    models = old_profile.train_profile_models()
    original_factory = old_profile.make_fixture
    original_trainer = old_profile.train_profile_models
    original_scorer = front.constrained_multistart

    def supply(fixture_index=0, split="dev"):
        if fixture_index == FIXTURE_INDEX and split == "dev":
            return fixture
        raise RuntimeError("unexpected fixture request in Phase 494")

    def unrestricted(paths, blocks, pair, quad, restarts, iterations,
                     binary=UNRESTRICTED_BINARY, seed=front.BOARD_SEED):
        return original_scorer(paths, blocks, pair, quad, restarts, iterations,
                               binary=UNRESTRICTED_BINARY, seed=seed)

    old_profile.make_fixture = supply
    old_profile.train_profile_models = lambda: models
    front.constrained_multistart = unrestricted
    try:
        if not (work_dir / "result.json").exists():
            front.run_front(FIXTURE_INDEX, "dev", work_dir,
                            board_binary=UNRESTRICTED_BINARY)
        result = continuation.run(FIXTURE_INDEX, "dev", work_dir)
    finally:
        front.constrained_multistart = original_scorer
        old_profile.train_profile_models = original_trainer
        old_profile.make_fixture = original_factory
    summary = {
        "phase": 494, "status": "development_proof_complete",
        "faed_scored": False, "holdout_consumed": False,
        "fixture_index": FIXTURE_INDEX, "swap_count": SWAP_COUNT,
        "objective_marker_sha256": sha256_file(work_dir / "objective_marker.json"),
        "top1_exact_order": result["top1_exact_order"],
        "top1_plaintext_accuracy": result["top1_plaintext_accuracy"],
        "exact_order_final_rank": result["exact_order_final_rank"],
        "final_candidates": result["final_candidates"],
    }
    atomic_json(output, summary)
    return summary


def self_test() -> dict:
    marker = marker_payload()
    if not UNRESTRICTED_BINARY.is_file():
        raise FileNotFoundError(UNRESTRICTED_BINARY)
    if marker["fixture_index"] != 3 or marker["swap_count"] != 3:
        raise AssertionError("proof fixture changed")
    return {"faed_scored": False,
            "unrestricted_binary_sha256": sha256_file(UNRESTRICTED_BINARY),
            "fixture_raw_sha256": marker["fixture_raw_sha256"]}


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
