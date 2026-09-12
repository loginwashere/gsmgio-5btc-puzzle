#!/usr/bin/env python3
"""Locked FAED width-30 {g,i} run under the Phase 487/488 dual-lane schedule.

Supersedes Phase 484AL (which used the older 484AI schedule alone, before any
holdout gate existed, and closed as a documented gibberish miss). This run
uses the schedule that cleared Phase 488's 10/10 development and 11/12
holdout gates, and adds two checks 484AL never had: agreement across 5
independent board-anneal seeds on the real input, and separation from 5
shuffled-token-order controls that share FAED's exact raw and token
histograms but carry no real transposition signal.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path

from data import FAED
import phase484a_raw_symbol_vic_solver as base
import phase484j_constructive_prefix_beam_probe as prefix
import phase484ai_width30_early_switch_full_solve as full
import phase484ad_width30_parent_reserved_bridge as bridge
import phase484ae_width30_checkpointed_rolling as rolling
import phase484am_width30_root_lineage_beam as lineage
import phase484ac_width30_partition_constrained_board_probe as constrained
import phase484z_width30_early_board_switch_probe as early
import phase484y_width30_feasibility_probe as width30
import phase484y_width30_blind_joint_solver as joint
import phase484q_blind_joint_width19_solver as solver19
import phase484x_exact_faed_profile_power_probe as exact
import phase484an_width30_dual_lane_dev as dual

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
PROTOCOL = REPO_ROOT / "doc" / "Brainstorms" / "2026-09-12 - Phase 484AO Locked FAED Width30 GI Dual-Lane Protocol.md"
LOCK = SCRIPT_DIR / "phase484ao_faed_width30_gi_dual_lane_lock.json"
DEFAULT_WORK_DIR = REPO_ROOT / "_work" / "phase484ao"
FAED_SHA256 = "066191b4aafc114fbca7f0d168382f40129c4ff18490375b689741081d5ef3c2"
PAIR = ("g", "i")
WIDTH = 30
ROWS = 19
RUNS_PER_ARM = 5
REAL_SENTINEL_BASE = 484100
CONTROL_SENTINEL_BASE = 484200
BOARD_SEED_BASE = 0x484A0000
TOKEN_SHUFFLE_BASE = 0x484A0AA0
SOURCE_PATHS = (
    Path(__file__).resolve(), PROTOCOL,
    Path(base.__file__).resolve(), Path(prefix.__file__).resolve(),
    Path(full.__file__).resolve(), Path(bridge.__file__).resolve(),
    Path(rolling.__file__).resolve(), Path(lineage.__file__).resolve(),
    Path(constrained.__file__).resolve(), Path(early.__file__).resolve(),
    Path(width30.__file__).resolve(), Path(joint.__file__).resolve(),
    Path(solver19.__file__).resolve(), Path(exact.__file__).resolve(),
    Path(dual.__file__).resolve(),
)
BINARY_PATHS = (
    Path(width30.DEFAULT_BINARY), Path(constrained.GPU_BINARY),
    Path(joint.FULL_BINARY),
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def real_tokens() -> tuple[str, ...]:
    tokens = base.segment_raw(FAED, PAIR)
    if tokens is None:
        raise AssertionError("FAED does not segment under pair {g,i}")
    return tokens


def shuffled_raw(control_index: int) -> str:
    tokens = real_tokens()
    seed = base.derive_seed(TOKEN_SHUFFLE_BASE, control_index)
    order = base.PCG32(seed).permutation(len(tokens))
    shuffled = "".join(tokens[i] for i in order)
    if base.segment_raw(shuffled, PAIR) != tuple(tokens[i] for i in order):
        raise AssertionError("shuffled control failed to resegment cleanly")
    if len(shuffled) != len(FAED):
        raise AssertionError("shuffled control changed raw length")
    if collections.Counter(shuffled) != collections.Counter(FAED):
        raise AssertionError("shuffled control changed raw histogram")
    return shuffled


def real_board_seed(run_index: int) -> int:
    return base.derive_seed(BOARD_SEED_BASE, 0, run_index)


def control_board_seed(run_index: int) -> int:
    return base.derive_seed(BOARD_SEED_BASE, 1, run_index)


def run_specs() -> list[dict]:
    specs = []
    for i in range(RUNS_PER_ARM):
        specs.append({
            "arm": "real", "run_index": i,
            "sentinel_fixture_index": REAL_SENTINEL_BASE + i,
            "board_seed": real_board_seed(i),
            "raw": FAED,
        })
    for i in range(RUNS_PER_ARM):
        specs.append({
            "arm": "control", "run_index": i,
            "sentinel_fixture_index": CONTROL_SENTINEL_BASE + i,
            "board_seed": control_board_seed(i),
            "raw": shuffled_raw(i),
        })
    return specs


def input_checks() -> dict:
    digest = hashlib.sha256(FAED.encode("ascii")).hexdigest()
    if digest != FAED_SHA256 or len(FAED) != WIDTH * ROWS:
        raise AssertionError("FAED input identity changed")
    if set(FAED) != set(base.NINE_SYMBOLS):
        raise AssertionError("FAED alphabet changed")
    tokens = real_tokens()
    if len(tokens) != 436:
        raise AssertionError("FAED {g,i} token length changed")
    if collections.Counter(tokens) != collections.Counter(exact.TARGET_TOKEN_COUNTS):
        raise AssertionError("FAED {g,i} token histogram changed")
    if collections.Counter(FAED) != collections.Counter(exact.TARGET_RAW_COUNTS):
        raise AssertionError("FAED raw histogram changed")
    return {
        "faed_ascii_sha256": digest,
        "raw_length": len(FAED),
        "token_length": len(tokens),
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
        "phase": "484AO",
        "status": "locked_before_real_run",
        "supersedes": {
            "phase": "484AL",
            "lock_sha256_no_longer_applicable": True,
            "reason": ("484AL used the pre-holdout-gated 484AI schedule alone "
                       "and closed as a documented gibberish miss; this run "
                       "uses the Phase 487/488 dual-lane schedule that "
                       "cleared a 10/10 dev gate and an 11/12 holdout gate"),
        },
        "input": checks,
        "schedule": dual.SCHEDULE,
        "schedule_sha256": dual.schedule_sha256(),
        "sources_sha256": sources,
        "binaries_sha256": binaries,
        "runs_per_arm": RUNS_PER_ARM,
        "run_count": 2 * RUNS_PER_ARM,
        "real_sentinel_base": REAL_SENTINEL_BASE,
        "control_sentinel_base": CONTROL_SENTINEL_BASE,
        "board_seed_base": BOARD_SEED_BASE,
        "token_shuffle_base": TOKEN_SHUFFLE_BASE,
        "run_board_seeds": {
            "real": [real_board_seed(i) for i in range(RUNS_PER_ARM)],
            "control": [control_board_seed(i) for i in range(RUNS_PER_ARM)],
        },
        "control_token_shuffle_seeds": [
            base.derive_seed(TOKEN_SHUFFLE_BASE, i) for i in range(RUNS_PER_ARM)
        ],
        "negative_scope": "nonclosing_without_readable_and_separated_result",
    }


def verify_lock() -> dict:
    if not LOCK.is_file():
        raise RuntimeError("execution lock is missing")
    locked = json.loads(LOCK.read_text())
    actual = lock_payload()
    if locked != actual:
        raise RuntimeError("execution lock mismatch")
    return locked


def sentinel_fixture(raw: str) -> dict:
    return {
        "width": WIDTH,
        "pair": list(PAIR),
        "observed": raw,
        "raw": raw,
        "order": list(range(WIDTH)),
        "plaintext": "?" * 436,
    }


def run_one(spec: dict, work_dir: Path) -> dict:
    output = work_dir / "result.json"
    if output.exists():
        raise FileExistsError(f"refusing a second or overwriting run: {output}")
    work_dir.mkdir(parents=True, exist_ok=True)

    sentinel_index = spec["sentinel_fixture_index"]
    fixture = sentinel_fixture(spec["raw"])
    original_fixture = width30.width30_fixture
    calls = []

    def supply_fixture(fixture_index, split="dev"):
        if fixture_index == sentinel_index and split == "dev":
            calls.append((fixture_index, split))
            return {**fixture, "fixture_index": fixture_index}
        if fixture_index in width30.TRAIN_INDICES and split == "dev":
            return original_fixture(fixture_index, split)
        raise RuntimeError("unexpected fixture request during real run")

    width30.width30_fixture = supply_fixture
    try:
        pipeline = dual.run_fixture(sentinel_index, work_dir / "pipeline",
                                    split="dev", board_seed=spec["board_seed"])
    finally:
        width30.width30_fixture = original_fixture

    final = json.loads((work_dir / "pipeline" / "merged" / "stage_final.json").read_text())
    candidates = []
    for record in final["final_candidates"]:
        candidates.append({key: value for key, value in record.items()
                           if key not in ("is_exact_order", "plaintext_accuracy")})
    result = {
        "phase": "484AO",
        "status": "locked_faed_width30_gi_dual_lane_run_complete",
        "arm": spec["arm"],
        "run_index": spec["run_index"],
        "faed_scored": spec["arm"] == "real",
        "sentinel_diagnostics_are_evidential": False,
        "sentinel_fixture_index": sentinel_index,
        "board_seed": spec["board_seed"],
        "raw_sha256": hashlib.sha256(spec["raw"].encode("ascii")).hexdigest(),
        "execution_lock_sha256": sha256_file(LOCK),
        "schedule_sha256": dual.schedule_sha256(),
        "fixture_api_calls": len(calls),
        "pipeline_wall_seconds": pipeline["wall_seconds"],
        "final_candidates": candidates,
        "top1_normalized_score": candidates[0]["normalized_score"] if candidates else None,
        "top1_plaintext": candidates[0]["plaintext"] if candidates else None,
        "work_dir": str(work_dir),
    }
    full.write_json(output, result)
    return result


def run_all(work_dir: Path = DEFAULT_WORK_DIR) -> dict:
    verify_lock()
    work_dir = Path(work_dir)
    summary_path = work_dir / "summary.json"
    specs = run_specs()
    runs = []
    for spec in specs:
        run_dir = work_dir / f"{spec['arm']}_{spec['run_index']}"
        result_path = run_dir / "result.json"
        if result_path.is_file():
            runs.append(json.loads(result_path.read_text()))
            continue
        runs.append(run_one(spec, run_dir))
        work_dir.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(json.dumps({
            "phase": "484AO",
            "status": "in_progress",
            "completed": len(runs),
            "total": len(specs),
            "runs": runs,
        }, indent=2) + "\n")

    real_scores = [r["top1_normalized_score"] for r in runs if r["arm"] == "real"]
    control_scores = [r["top1_normalized_score"] for r in runs if r["arm"] == "control"]
    best_real = max(range(len(runs)), key=lambda i: (
        runs[i]["arm"] == "real", runs[i]["top1_normalized_score"] or float("-inf")))
    summary = {
        "phase": "484AO",
        "status": "locked_run_complete",
        "runs_per_arm": RUNS_PER_ARM,
        "real_top1_scores": real_scores,
        "control_top1_scores": control_scores,
        "real_min": min(real_scores) if real_scores else None,
        "real_max": max(real_scores) if real_scores else None,
        "control_min": min(control_scores) if control_scores else None,
        "control_max": max(control_scores) if control_scores else None,
        "separation_real_min_minus_control_max": (
            (min(real_scores) - max(control_scores))
            if real_scores and control_scores else None),
        "best_real_run": runs[best_real],
        "runs": runs,
        "disposition": "requires_manual_readability_and_separation_review",
    }
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def self_test() -> dict:
    checks = input_checks()
    if dual.schedule_sha256() != "ca219a6b0dca02e142b80581a097098320869e621bc202296c253e290f028dc9":
        raise AssertionError("dual-lane schedule changed since this protocol was written")
    for i in range(RUNS_PER_ARM):
        control = shuffled_raw(i)
        if control == FAED:
            raise AssertionError("control identical to FAED")
        if collections.Counter(control) != collections.Counter(FAED):
            raise AssertionError("control histogram mismatch")
    fixture = sentinel_fixture(FAED)
    if fixture["observed"] != FAED or tuple(fixture["pair"]) != PAIR:
        raise AssertionError("real fixture adapter mismatch")
    if fixture["plaintext"] != "?" * 436:
        raise AssertionError("sentinel plaintext mismatch")
    seeds = [real_board_seed(i) for i in range(RUNS_PER_ARM)] + \
            [control_board_seed(i) for i in range(RUNS_PER_ARM)]
    if len(set(seeds)) != len(seeds):
        raise AssertionError("board seeds are not pairwise distinct")
    return {**checks, "schedule_sha256": dual.schedule_sha256(),
            "board_seeds": seeds}


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
        result = run_all(args.work_dir)
        print("real scores", result["real_top1_scores"])
        print("control scores", result["control_top1_scores"])
        print("separation", result["separation_real_min_minus_control_max"])
        print("best real plaintext", result["best_real_run"]["top1_plaintext"])
        print("wrote", args.work_dir / "summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
