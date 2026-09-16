#!/usr/bin/env python3
"""Locked, checkpointed one-run FAED {g,i}, width-19 screen.

The synthetic Phase-490 implementation is reused without changing its search
schedule.  Exact-profile training models are materialized before the real
fixture adapter is installed, so no FAED ordering can enter model training.
Synthetic truth fields are never used for selection and are removed from the
authoritative real result.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path

from data import FAED
import phase484a_raw_symbol_vic_solver as base
import phase484n_hybrid_prefix_scorer as invariant
import phase484q_blind_joint_width19_solver as joint
import phase484x_exact_faed_profile_power_probe as exact
import phase490_width19_dual_lane_dev as front
import phase490_width19_checkpointed_dual_lane as continuation


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
PROTOCOL = (REPO_ROOT / "doc" / "Brainstorms" /
            "2026-09-12 - Phase 490 Width19 Dual-Lane Port Protocol.md")
LOCK = SCRIPT_DIR / "phase490_faed_width19_gi_lock.json"
DEFAULT_WORK_DIR = REPO_ROOT / "_work" / "phase490" / "real_gi_w19"
FAED_SHA256 = "066191b4aafc114fbca7f0d168382f40129c4ff18490375b689741081d5ef3c2"
PAIR = ("g", "i")
WIDTH, ROWS = 19, 30
SENTINEL_FIXTURE_INDEX = 490019
BOARD_SEED = front.BOARD_SEED

SOURCE_PATHS = (
    Path(__file__).resolve(), PROTOCOL,
    SCRIPT_DIR / "data.py",
    Path(base.__file__).resolve(),
    Path(invariant.__file__).resolve(),
    Path(joint.__file__).resolve(),
    Path(exact.__file__).resolve(),
    Path(front.__file__).resolve(),
    Path(continuation.__file__).resolve(),
    SCRIPT_DIR / "phase484g_hard_negative_discriminator.py",
    SCRIPT_DIR / "phase484j_constructive_prefix_beam_probe.py",
    SCRIPT_DIR / "phase484k_bidirectional_segment_assembly_probe.py",
    SCRIPT_DIR / "phase484n_gpu_width19_beam_probe.py",
    SCRIPT_DIR / "phase484o_joint_board_order_ceiling.py",
    SCRIPT_DIR / "phase484p_partial_board_recovery_probe.py",
    SCRIPT_DIR / "phase484ac_width30_partition_constrained_board_probe.py",
    SCRIPT_DIR / "phase484z_width30_row_holdout_probe.py",
    base.CORPUS_FILE,
    base.QUADGRAM_FILE,
)
BINARY_PATHS = (
    Path(invariant.DEFAULT_BINARY),
    Path(front.CONSTRAINED_BINARY),
    Path(joint.FULL_BINARY),
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def input_checks() -> dict:
    digest = hashlib.sha256(FAED.encode("ascii")).hexdigest()
    if digest != FAED_SHA256 or len(FAED) != WIDTH * ROWS:
        raise AssertionError("FAED identity or exact-grid geometry changed")
    tokens = base.segment_raw(FAED, PAIR)
    if tokens is None or len(tokens) != 436:
        raise AssertionError("FAED no longer has the frozen {g,i} segmentation")
    if collections.Counter(tokens) != collections.Counter(exact.TARGET_TOKEN_COUNTS):
        raise AssertionError("FAED token histogram changed")
    if collections.Counter(FAED) != collections.Counter(exact.TARGET_RAW_COUNTS):
        raise AssertionError("FAED raw histogram changed")
    return {
        "faed_ascii_sha256": digest,
        "raw_length": len(FAED),
        "token_length_in_observed_order": len(tokens),
        "single_slots_in_observed_order": sum(len(token) == 1 for token in tokens),
        "pair": list(PAIR), "width": WIDTH, "rows": ROWS,
        "direction": "model_b_columnar_raw_digits",
    }


def real_fixture() -> dict:
    return {
        "fixture_index": SENTINEL_FIXTURE_INDEX,
        "width": WIDTH,
        "pair": list(PAIR),
        "board_mode": "unknown_real",
        "split": "dev",
        "observed": FAED,
        "raw": FAED,
        "order": list(range(WIDTH)),
        "plaintext": "?" * 436,
    }


def lock_payload() -> dict:
    sources = {}
    for path in SOURCE_PATHS:
        path = Path(path)
        if not path.is_file():
            raise FileNotFoundError(path)
        sources[str(path.relative_to(REPO_ROOT))] = sha256_file(path)
    binaries = {}
    for path in BINARY_PATHS:
        path = Path(path)
        if not path.is_file():
            raise FileNotFoundError(path)
        binaries[str(path.relative_to(REPO_ROOT))] = sha256_file(path)
    return {
        "phase": "490R",
        "status": "exploratory_real_execution_lock",
        "input": input_checks(),
        "sentinel_fixture_index": SENTINEL_FIXTURE_INDEX,
        "front_schedule": front.FRONT_SCHEDULE,
        "front_schedule_sha256": front.schedule_sha256(),
        "continuation_schedule": continuation.SCHEDULE,
        "continuation_schedule_sha256": continuation.schedule_sha256(),
        "board_seed": BOARD_SEED,
        "sources_sha256": sources,
        "binaries_sha256": binaries,
        "run_count": 1,
        "checkpoint_policy": "atomic_npz_plus_json_per_continuation_stage",
        "decision_rule": ("inspect every valid resolved candidate among the "
                          "eight ranked terminal orders for readable, "
                          "internally coherent plaintext; retain invalid-"
                          "segmentation terminal records too"),
        "negative_scope": "one_seed_exploratory_miss_only",
    }


def verify_lock() -> dict:
    if not LOCK.is_file():
        raise RuntimeError("execution lock is missing")
    locked = json.loads(LOCK.read_text())
    if locked != lock_payload():
        raise RuntimeError("execution lock mismatch")
    return locked


def atomic_json(path: Path, value: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def validate_front_checkpoint(work_dir: Path) -> bool:
    population = work_dir / "depth7_refined.npz"
    record_path = work_dir / "result.json"
    real_record = work_dir / "real_front_checkpoint.json"
    if not population.exists() and not record_path.exists() and not real_record.exists():
        return False
    if not population.is_file() or not record_path.is_file() or not real_record.is_file():
        raise RuntimeError("partial real front checkpoint exists")
    record = json.loads(real_record.read_text())
    expected = {
        "phase": "490R", "stage": "front_depth7_refined",
        "faed_scored": True,
        "sentinel_diagnostics_are_evidential": False,
        "execution_lock_sha256": sha256_file(LOCK),
        "population_sha256": sha256_file(population),
        "front_record_sha256": sha256_file(record_path),
        "front_schedule_sha256": front.schedule_sha256(),
    }
    if record != expected:
        raise RuntimeError("real front checkpoint metadata mismatch")
    continuation.load_population(population, min_depth=7, max_depth=7)
    return True


def mark_front_checkpoint(work_dir: Path) -> None:
    population = work_dir / "depth7_refined.npz"
    record_path = work_dir / "result.json"
    record = json.loads(record_path.read_text())
    if (record.get("fixture_index") != SENTINEL_FIXTURE_INDEX or
            record.get("schedule_sha256") != front.schedule_sha256()):
        raise RuntimeError("front solver returned unexpected metadata")
    # This adapter is the authoritative interpretation of the sentinel run.
    record["status"] = "locked_real_width19_front_complete"
    record["faed_scored"] = True
    record["holdout_consumed"] = False
    record["sentinel_diagnostics_are_evidential"] = False
    atomic_json(record_path, record)
    atomic_json(work_dir / "real_front_checkpoint.json", {
        "phase": "490R", "stage": "front_depth7_refined",
        "faed_scored": True,
        "sentinel_diagnostics_are_evidential": False,
        "execution_lock_sha256": sha256_file(LOCK),
        "population_sha256": sha256_file(population),
        "front_record_sha256": sha256_file(record_path),
        "front_schedule_sha256": front.schedule_sha256(),
    })


def sanitize_stage_records(work_dir: Path) -> None:
    for path in (work_dir / "continuation").glob("*.json"):
        record = json.loads(path.read_text())
        record["status"] = "locked_real_width19_checkpoint_complete"
        record["faed_scored"] = True
        record["holdout_consumed"] = False
        record["sentinel_diagnostics_are_evidential"] = False
        for container in (record, record.get("before_selection", {}),
                          record.get("after_selection", {})):
            if isinstance(container, dict):
                for key in list(container):
                    if key.startswith("true_") or key.startswith("best_true"):
                        container.pop(key)
        if path.name == "final_resolve.json":
            for candidate in record.get("final_candidates", []):
                candidate.pop("is_exact_order", None)
                candidate.pop("plaintext_accuracy", None)
            record.pop("exact_order_final_rank", None)
            record.pop("top1_exact_order", None)
            record.pop("top1_plaintext_accuracy", None)
        atomic_json(path, record)


def run(work_dir: Path = DEFAULT_WORK_DIR) -> dict:
    verify_lock()
    work_dir = Path(work_dir)
    result_path = work_dir / "phase490_real_result.json"
    if result_path.exists():
        raise FileExistsError("refusing a second or overwriting FAED run")
    work_dir.mkdir(parents=True, exist_ok=True)

    # Crucial ordering: cache models from closed synthetic training fixtures
    # before installing the sentinel real-fixture adapter.
    exact.train_profile_models()
    original_make_fixture = exact.make_fixture
    calls = []

    def supply_fixture(fixture_index=0, split="dev"):
        if fixture_index == SENTINEL_FIXTURE_INDEX and split == "dev":
            calls.append((fixture_index, split))
            return real_fixture()
        raise RuntimeError("unexpected fixture request after real adapter installation")

    exact.make_fixture = supply_fixture
    original_commit_stage = continuation.commit_stage

    def real_commit_stage(*args, **kwargs):
        output = original_commit_stage(*args, **kwargs)
        # Make each checkpoint truthful immediately, including if the machine
        # is shut down before the subsequent stage completes.
        sanitize_stage_records(Path(args[0]))
        return output

    continuation.commit_stage = real_commit_stage
    try:
        if not validate_front_checkpoint(work_dir):
            front.run_front(SENTINEL_FIXTURE_INDEX, "dev", work_dir)
            mark_front_checkpoint(work_dir)
        pipeline = continuation.run(SENTINEL_FIXTURE_INDEX, "dev", work_dir)
    finally:
        continuation.commit_stage = original_commit_stage
        exact.make_fixture = original_make_fixture

    sanitize_stage_records(work_dir)
    final = json.loads(
        (work_dir / "continuation" / "final_resolve.json").read_text())
    candidates = final.get("final_candidates", [])
    result = {
        "phase": "490R",
        "status": "exploratory_faed_width19_gi_complete",
        "faed_scored": True,
        "input": input_checks(),
        "execution_lock_sha256": sha256_file(LOCK),
        "front_schedule_sha256": front.schedule_sha256(),
        "continuation_schedule_sha256": continuation.schedule_sha256(),
        "board_seed": BOARD_SEED,
        "fixture_api_calls_this_invocation": len(calls),
        "sentinel_diagnostics_are_evidential": False,
        "pipeline_reported_wall_seconds": pipeline.get("wall_seconds"),
        "terminal_candidates": final.get("terminal_candidates", []),
        "skipped_terminals": final.get("skipped_terminals", []),
        "final_candidates": candidates,
        "top1_normalized_score": (candidates[0]["normalized_score"]
                                  if candidates else None),
        "top1_plaintext": candidates[0]["plaintext"] if candidates else None,
        "disposition": "requires_manual_readability_review",
        "work_dir": str(work_dir),
    }
    atomic_json(result_path, result)
    return result


def self_test() -> dict:
    checks = input_checks()
    if continuation.SCHEDULE["front_schedule_sha256"] != front.schedule_sha256():
        raise AssertionError("front/continuation schedule chain changed")
    fixture = real_fixture()
    if fixture["observed"] != FAED or tuple(fixture["pair"]) != PAIR:
        raise AssertionError("real fixture adapter mismatch")
    if fixture["plaintext"] != "?" * 436:
        raise AssertionError("sentinel plaintext changed")
    if BOARD_SEED != continuation.SCHEDULE["board_seed"]:
        raise AssertionError("board seed chain changed")
    return {
        **checks,
        "front_schedule_sha256": front.schedule_sha256(),
        "continuation_schedule_sha256": continuation.schedule_sha256(),
        "checkpointed": True,
    }


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
        result = self_test()
    elif args.write_lock:
        if LOCK.exists():
            raise FileExistsError("refusing to overwrite execution lock")
        atomic_json(LOCK, lock_payload())
        result = {"wrote": str(LOCK), "lock_sha256": sha256_file(LOCK)}
    elif args.verify_lock:
        result = verify_lock()
    else:
        result = run(args.work_dir)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
