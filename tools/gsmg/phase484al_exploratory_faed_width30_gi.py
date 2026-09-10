#!/usr/bin/env python3
"""Locked one-cell exploratory FAED width-30 {g,i} run."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path

from data import FAED
import phase484a_raw_symbol_vic_solver as base
import phase484ai_width30_early_switch_full_solve as full
import phase484ad_width30_parent_reserved_bridge as bridge
import phase484ae_width30_checkpointed_rolling as rolling
import phase484ac_width30_partition_constrained_board_probe as constrained
import phase484ah_width30_early_switch_depth_probe as switch6
import phase484z_width30_early_board_switch_probe as early
import phase484y_width30_feasibility_probe as width30
import phase484y_width30_blind_joint_solver as joint
import phase484x_exact_faed_profile_power_probe as exact

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
PROTOCOL = REPO_ROOT / "doc" / "Brainstorms" / "2026-09-10 - Phase 484AL Exploratory FAED Width30 GI Protocol.md"
LOCK = SCRIPT_DIR / "phase484al_faed_width30_gi_lock.json"
DEFAULT_WORK_DIR = REPO_ROOT / "_work" / "phase484al"
FAED_SHA256 = "066191b4aafc114fbca7f0d168382f40129c4ff18490375b689741081d5ef3c2"
PAIR = ("g", "i")
WIDTH = 30
ROWS = 19
SENTINEL_FIXTURE_INDEX = 484030
FAILED_LAUNCH_LOCK_SHA256 = "d78e29353477481249331d838d8f2a29ba9d72dcea91e233befaf745a9aef43c"
SOURCE_PATHS = (
    Path(__file__).resolve(), PROTOCOL,
    Path(base.__file__).resolve(), Path(full.__file__).resolve(),
    Path(bridge.__file__).resolve(), Path(rolling.__file__).resolve(),
    Path(constrained.__file__).resolve(), Path(switch6.__file__).resolve(),
    Path(early.__file__).resolve(), Path(width30.__file__).resolve(),
    Path(joint.__file__).resolve(), Path(exact.__file__).resolve(),
)
BINARY_PATHS = (Path(width30.DEFAULT_BINARY), Path(constrained.GPU_BINARY))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def input_checks() -> dict:
    digest = hashlib.sha256(FAED.encode("ascii")).hexdigest()
    if digest != FAED_SHA256 or len(FAED) != WIDTH * ROWS:
        raise AssertionError("FAED input identity changed")
    if set(FAED) != set(base.NINE_SYMBOLS):
        raise AssertionError("FAED alphabet changed")
    tokens = base.segment_raw(FAED, PAIR)
    if len(tokens) != 436:
        raise AssertionError("FAED {g,i} token length changed")
    if collections.Counter(tokens) != collections.Counter(exact.TARGET_TOKEN_COUNTS):
        raise AssertionError("FAED token histogram changed")
    if collections.Counter(FAED) != collections.Counter(exact.TARGET_RAW_COUNTS):
        raise AssertionError("FAED raw histogram changed")
    return {
        "faed_ascii_sha256": digest,
        "raw_length": len(FAED),
        "token_length": len(tokens),
        "single_slots": sum(len(token) == 1 for token in tokens),
        "pair": list(PAIR),
        "width": WIDTH,
        "rows": ROWS,
    }


def lock_payload() -> dict:
    checks = input_checks()
    sources = {}
    for path in SOURCE_PATHS:
        if not path.is_file():
            raise FileNotFoundError(path)
        sources[str(path.relative_to(REPO_ROOT))] = sha256_file(path)
    binaries = {}
    for path in BINARY_PATHS:
        if not path.is_file():
            raise FileNotFoundError(path)
        binaries[str(path.relative_to(REPO_ROOT))] = sha256_file(path)
    return {
        "phase": "484AL",
        "status": "exploratory_real_execution_lock",
        "input": checks,
        "schedule": full.SCHEDULE,
        "schedule_sha256": full.schedule_sha256(),
        "sources_sha256": sources,
        "binaries_sha256": binaries,
        "run_count": 1,
        "negative_scope": "nonclosing_without_holdout_power",
        "amendment_history": [{
            "superseded_lock_sha256": FAILED_LAUNCH_LOCK_SHA256,
            "reason": ("first launch failed before FAED scoring because the adapter "
                       "also rejected fixed synthetic training-fixture requests; "
                       "replacement passes those requests to the pinned original provider"),
            "faed_score_observed": False,
        }],
    }


def verify_lock() -> dict:
    if not LOCK.is_file():
        raise RuntimeError("execution lock is missing")
    locked = json.loads(LOCK.read_text())
    actual = lock_payload()
    if locked != actual:
        raise RuntimeError("execution lock mismatch")
    return locked


def real_fixture() -> dict:
    return {
        "fixture_index": SENTINEL_FIXTURE_INDEX,
        "width": WIDTH,
        "pair": list(PAIR),
        "observed": FAED,
        "raw": FAED,
        "order": list(range(WIDTH)),
        "plaintext": "?" * 436,
    }


def run(work_dir: Path = DEFAULT_WORK_DIR) -> dict:
    locked = verify_lock()
    work_dir = Path(work_dir)
    output = work_dir / "result.json"
    pipeline_dir = work_dir / "pipeline"
    if output.exists() or (pipeline_dir / "result.json").exists():
        raise FileExistsError("refusing a second or overwriting FAED run")
    work_dir.mkdir(parents=True, exist_ok=True)

    original_fixture = width30.width30_fixture
    calls = []

    def supply_fixture(fixture_index, split="dev"):
        if fixture_index == SENTINEL_FIXTURE_INDEX and split == "dev":
            calls.append((fixture_index, split))
            return real_fixture()
        if fixture_index in width30.TRAIN_INDICES and split == "dev":
            return original_fixture(fixture_index, split)
        raise RuntimeError("unexpected fixture request during real run")

    width30.width30_fixture = supply_fixture
    try:
        pipeline = full.run_fixture(SENTINEL_FIXTURE_INDEX, pipeline_dir)
    finally:
        width30.width30_fixture = original_fixture

    final = json.loads((pipeline_dir / "stage_final_resolve.json").read_text())
    candidates = []
    for record in final["final_candidates"]:
        candidates.append({key: value for key, value in record.items()
                           if key not in ("is_exact_order", "plaintext_accuracy")})
    result = {
        "phase": "484AL",
        "status": "exploratory_faed_width30_gi_complete",
        "faed_scored": True,
        "holdout_gate_completed": False,
        "inference_scope": "readable hits confirmable; miss nonclosing",
        "input": input_checks(),
        "execution_lock_sha256": sha256_file(LOCK),
        "schedule": locked["schedule"],
        "schedule_sha256": locked["schedule_sha256"],
        "fixture_api_calls": len(calls),
        "sentinel_diagnostics_are_evidential": False,
        "pipeline_wall_seconds": pipeline["wall_seconds"],
        "final_candidates": candidates,
        "top1_normalized_score": candidates[0]["normalized_score"] if candidates else None,
        "top1_plaintext": candidates[0]["plaintext"] if candidates else None,
        "work_dir": str(work_dir),
    }
    full.write_json(output, result)
    return result


def self_test() -> dict:
    checks = input_checks()
    if full.schedule_sha256() != "ed1d840f6e3203e11c35f56383e2310dcffa1b4bc265d2cfb431343e36147e2d":
        raise AssertionError("fixed schedule changed")
    fixture = real_fixture()
    if fixture["observed"] != FAED or tuple(fixture["pair"]) != PAIR:
        raise AssertionError("real fixture adapter mismatch")
    if fixture["plaintext"] != "?" * 436:
        raise AssertionError("sentinel plaintext mismatch")
    return {**checks, "schedule_sha256": full.schedule_sha256()}


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--write-lock", action="store_true")
    group.add_argument("--verify-lock", action="store_true")
    group.add_argument("--run", action="store_true")
    parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK_DIR)
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), indent=2))
    elif args.write_lock:
        if LOCK.exists():
            raise FileExistsError("refusing to overwrite execution lock")
        LOCK.write_text(json.dumps(lock_payload(), indent=2) + "\n")
        print("wrote", LOCK)
    elif args.verify_lock:
        print(json.dumps(verify_lock(), indent=2))
    else:
        result = run(args.work_dir)
        print("top1 score", result["top1_normalized_score"])
        print("top1 plaintext", result["top1_plaintext"])
        print("wrote", args.work_dir / "result.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
