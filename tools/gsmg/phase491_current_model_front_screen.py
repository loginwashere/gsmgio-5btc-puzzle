#!/usr/bin/env python3
"""Ten-fixture Phase-491 front screen using the existing 484X model."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import phase484x_exact_faed_profile_power_probe as old_profile
import phase490_width19_dual_lane_dev as front
import phase491_raw_histogram_fixture as rawonly


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_WORK_DIR = REPO_ROOT / "_work" / "phase491" / "current_model_front"
START, COUNT = 0, 10


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def expected_fixture_record(index: int, fixture: dict, population: Path,
                            result: Path) -> dict:
    return {
        "phase": "491", "status": "current_484x_model_front_complete",
        "faed_scored": False, "holdout_consumed": False,
        "fixture_index": index,
        "latent_profile_sha256": fixture["latent_profile_sha256"],
        "raw_sha256": fixture["raw_sha256"],
        "observed_sha256": hashlib.sha256(
            fixture["observed"].encode("ascii")).hexdigest(),
        "front_schedule_sha256": front.schedule_sha256(),
        "population_sha256": sha256_file(population),
        "front_result_sha256": sha256_file(result),
    }


def validate_completed(index: int, work_dir: Path, fixture: dict):
    population = work_dir / "depth7_refined.npz"
    result = work_dir / "result.json"
    record_path = work_dir / "phase491_front_record.json"
    if not population.exists() and not result.exists() and not record_path.exists():
        return None
    if not population.is_file() or not result.is_file() or not record_path.is_file():
        return None  # front-stage partials are cheap and safely overwritten
    record = json.loads(record_path.read_text())
    if record != expected_fixture_record(index, fixture, population, result):
        raise RuntimeError(f"fixture {index} front checkpoint mismatch")
    return json.loads(result.read_text())


def run_one(index: int, root: Path, models: dict) -> dict:
    fixture = rawonly.make_fixture(index, "dev")
    work_dir = root / f"i{index}"
    completed = validate_completed(index, work_dir, fixture)
    if completed is not None:
        print("resume fixture", index, flush=True)
        return completed

    original_factory = old_profile.make_fixture
    original_trainer = old_profile.train_profile_models
    calls = []

    def fixture_factory(fixture_index=0, split="dev"):
        if fixture_index == index and split == "dev":
            calls.append((fixture_index, split))
            return fixture
        raise RuntimeError("unexpected fixture request in Phase 491 front screen")

    old_profile.make_fixture = fixture_factory
    old_profile.train_profile_models = lambda: models
    try:
        result = front.run_front(index, "dev", work_dir)
    finally:
        old_profile.train_profile_models = original_trainer
        old_profile.make_fixture = original_factory
    if calls != [(index, "dev")]:
        raise RuntimeError("front solver did not request exactly one test fixture")
    population = work_dir / "depth7_refined.npz"
    result_path = work_dir / "result.json"
    record = expected_fixture_record(index, fixture, population, result_path)
    atomic_json(work_dir / "phase491_front_record.json", record)
    return result


def result_summary(index: int, result: dict) -> dict:
    refined = result["depth7_refine"]["after_selection"]
    return {
        "fixture_index": index,
        "true_segments_retained": refined["true_segments"],
        "best_true_rank": refined["best_true_rank"],
        "passed": refined["true_segments"] > 0,
        "wall_seconds": result["wall_seconds"],
        **rawonly.fixture_summary(rawonly.make_fixture(index, "dev")),
    }


def run_batch(root: Path = DEFAULT_WORK_DIR) -> dict:
    root = Path(root)
    # Materialize the historical 484X model before any fixture substitution.
    models = old_profile.train_profile_models()
    records = []
    for index in range(START, START + COUNT):
        result = run_one(index, root, models)
        records.append(result_summary(index, result))
        atomic_json(root / "summary.json", {
            "phase": "491", "status": "in_progress",
            "model": "historical_phase484x_exact_token_profile",
            "completed": len(records), "total": COUNT, "records": records,
        })
    passed = sum(record["passed"] for record in records)
    summary = {
        "phase": "491", "status": "current_model_front_screen_complete",
        "model": "historical_phase484x_exact_token_profile",
        "fixture_indices": list(range(START, START + COUNT)),
        "passed": passed, "total": COUNT,
        "gate": "at_least_8_of_10_retain_truth_at_refined_depth7",
        "gate_passed": passed >= 8,
        "records": records,
    }
    atomic_json(root / "summary.json", summary)
    return summary


def self_test() -> dict:
    fixtures = [rawonly.make_fixture(i) for i in range(2)]
    if fixtures[0]["latent_profile_sha256"] == fixtures[1]["latent_profile_sha256"]:
        raise AssertionError("first two raw-only profiles collide")
    if front.WIDTH != rawonly.WIDTH:
        raise AssertionError("front/generator width mismatch")
    return {"fixtures_checked": 2, "faed_scored": False,
            "front_schedule_sha256": front.schedule_sha256()}


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--run", action="store_true")
    parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK_DIR)
    args = parser.parse_args()
    result = self_test() if args.self_test else run_batch(args.work_dir)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
