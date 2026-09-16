#!/usr/bin/env python3
"""Phase 506B: checkpointed full width-19 runs for Phase-506A's top five."""
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
import phase493_partial_unrestricted_board_diagnostic as variants
import phase499_unrestricted_width19_holdout as phase499
import phase503_repaired_holdout_replacement as phase503
import phase506a_faed_depth6_pair_rank as ranker


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
PROTOCOL = (REPO_ROOT / "doc" / "Brainstorms" /
            "2026-09-14 - Phase 506B Top-Five Full Width19 Runs.md")
LOCK = SCRIPT_DIR / "phase506b_execution_lock.json"
WORK_ROOT = REPO_ROOT / "_work" / "phase506b"
PHASE503_RESULT = REPO_ROOT / "_work/phase503/i5_s3/phase503_complete_result.json"
WIDTH, ROWS = 19, 30
EARLY, BASE, BRIDGE = dict(phase503.EARLY), dict(phase503.BASE), dict(phase503.BRIDGE)
SOURCE_MODULES = (base, invariant, joint, exact, front, continuation, variants,
                  phase499, phase503, ranker)
BINARY_PATHS = (Path(invariant.DEFAULT_BINARY), Path(variants.UNRESTRICTED_BINARY),
                Path(joint.FULL_BINARY))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def chash(value):
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def atomic(path, value):
    phase499.atomic_json(Path(path), value)


def ranking_result():
    ranker.verify_lock()
    if not ranker.RESULT.is_file():
        raise RuntimeError("Phase-506A result is absent")
    result = json.loads(ranker.RESULT.read_text())
    if result.get("status") != "real_faed_pair_ranking_complete":
        raise RuntimeError("Phase-506A result is incomplete")
    selected = result.get("selected_for_phase506b")
    if not isinstance(selected, list) or len(selected) != 5:
        raise RuntimeError("Phase-506A selected set is invalid")
    indices = [row.get("pair_index") for row in selected]
    if len(set(indices)) != 5 or ranker.ceiling.ALL_PAIRS.index(("g", "i")) in indices:
        raise RuntimeError("Phase-506A selected indices are invalid")
    for row in selected:
        if list(ranker.ceiling.ALL_PAIRS[row["pair_index"]]) != row.get("pair"):
            raise RuntimeError("Phase-506A selected pair mismatch")
    return result


def qualified_result():
    phase503.verify_lock()
    if not PHASE503_RESULT.is_file():
        raise RuntimeError("Phase-503 result absent")
    result = json.loads(PHASE503_RESULT.read_text())
    if not result.get("gate_passed") or result.get("combined_exact_top1") != 2:
        raise RuntimeError("Phase-503 gate is not the reviewed pass")
    return result


def lock_payload():
    ranked = ranking_result()
    qualified_result()
    sources = {}
    for path in (Path(__file__), PROTOCOL, SCRIPT_DIR / "data.py",
                 base.CORPUS_FILE, base.QUADGRAM_FILE):
        sources[str(Path(path).relative_to(REPO_ROOT))] = sha(path)
    for module in SOURCE_MODULES:
        path = Path(module.__file__)
        sources[str(path.relative_to(REPO_ROOT))] = sha(path)
    selected = ranked["selected_for_phase506b"]
    return {
        "phase": "506B", "status": "real_execution_lock",
        "phase506a_lock_sha256": sha(ranker.LOCK),
        "phase506a_result_sha256": sha(ranker.RESULT),
        "selected_pairs": selected,
        "allowed_pair_indices": [row["pair_index"] for row in selected],
        "sources_sha256": sources,
        "binaries_sha256": {str(path.relative_to(REPO_ROOT)): sha(path)
                            for path in BINARY_PATHS},
        "phase503_lock_sha256": sha(phase503.LOCK_PATH),
        "phase503_result_sha256": sha(PHASE503_RESULT),
        "early_schedule_sha256": chash(EARLY),
        "base_schedule_sha256": chash(BASE),
        "bridge_schedule_sha256": chash(BRIDGE),
        "board_seed": front.BOARD_SEED,
        "width": WIDTH, "rows": ROWS,
        "direction": "model_b_columnar_raw_digits",
        "run_order": "ascending Phase-506A rank",
        "checkpoint_policy": "atomic_npz_plus_json_per_stage_per_pair",
        "decision_rule": "manual_readability_review_of_every_valid_final_candidate",
        "stop_rule": "stop after all five unreadable; do not run a sixth pair",
    }


def verify_lock():
    if not LOCK.is_file():
        raise RuntimeError("Phase-506B execution lock is absent")
    actual = json.loads(LOCK.read_text())
    if actual != lock_payload():
        raise RuntimeError("Phase-506B execution lock mismatch")
    return actual


def allowed_pair_indices():
    return lock_payload()["allowed_pair_indices"]


def pair_identity(pair_index):
    pair = tuple(ranker.ceiling.ALL_PAIRS[pair_index])
    tokens = base.segment_raw(FAED, pair)
    return {
        "pair_index": pair_index, "pair": list(pair),
        "faed_ascii_sha256": ranker.FAED_SHA256,
        "raw_length": len(FAED),
        "observed_segmentation_valid": tokens is not None,
        "observed_token_length": len(tokens) if tokens is not None else None,
        "observed_single_count": (sum(len(token) == 1 for token in tokens)
                                  if tokens is not None else None),
        "raw_counts": dict(sorted(collections.Counter(FAED).items())),
    }


def work_dir(pair_index):
    pair = ranker.ceiling.ALL_PAIRS[pair_index]
    return WORK_ROOT / f"ranked_pair_{pair_index:02d}_{''.join(pair)}"


def real_fixture(pair_index):
    pair = ranker.ceiling.ALL_PAIRS[pair_index]
    return {"fixture_index": 506000 + pair_index, "width": WIDTH,
            "pair": list(pair), "board_mode": "unknown_real_unrestricted",
            "split": "dev", "observed": FAED, "raw": FAED,
            # Synthetic truth diagnostics are stripped from every real record.
            # The observed-order token count may be undefined under Model B.
            "order": list(range(WIDTH)), "plaintext": "?" * len(FAED)}


def sanitize(directory):
    for path in (Path(directory) / "continuation").glob("*.json"):
        record = json.loads(path.read_text())
        record.update(status="locked_real_unrestricted_checkpoint",
                      faed_scored=True, holdout_consumed=False,
                      sentinel_diagnostics_are_evidential=False)
        for box in (record, record.get("before_selection", {}),
                    record.get("after_selection", {})):
            if isinstance(box, dict):
                for key in list(box):
                    if key.startswith("true_") or key.startswith("best_true"):
                        box.pop(key)
        if path.name == "final_resolve.json":
            for candidate in record.get("final_candidates", []):
                candidate.pop("is_exact_order", None)
                candidate.pop("plaintext_accuracy", None)
            for key in ("exact_order_final_rank", "top1_exact_order",
                        "top1_plaintext_accuracy"):
                record.pop(key, None)
        atomic(path, record)


def validate_front(directory, pair_index):
    pop = directory / "depth7_refined.npz"
    raw = directory / "result.json"
    marker = directory / "real_front_checkpoint.json"
    if not pop.exists() and not raw.exists() and not marker.exists():
        return None
    if not pop.is_file() or not raw.is_file() or not marker.is_file():
        raise RuntimeError("partial Phase-506B real front")
    expected = {
        "phase": "506B", "stage": "front_depth7_refined",
        "pair_index": pair_index, "faed_scored": True,
        "execution_lock_sha256": sha(LOCK), "population_sha256": sha(pop),
        "front_record_sha256": sha(raw),
        "front_schedule_sha256": front.schedule_sha256(),
    }
    if json.loads(marker.read_text()) != expected:
        raise RuntimeError("Phase-506B front marker mismatch")
    continuation.load_population(pop, min_depth=7, max_depth=7)
    return pop


def mark_front(directory, pair_index):
    pop, raw = directory / "depth7_refined.npz", directory / "result.json"
    record = json.loads(raw.read_text())
    record.update(status="locked_real_unrestricted_front", faed_scored=True,
                  holdout_consumed=False,
                  sentinel_diagnostics_are_evidential=False)
    for section in ("depth6_board", "depth7_coarse", "depth7_refine"):
        for box in (record.get(section, {}).get("before_selection", {}),
                    record.get(section, {}).get("after_selection", {})):
            for key in list(box):
                if key.startswith("true_") or key.startswith("best_true"):
                    box.pop(key)
    atomic(raw, record)
    atomic(directory / "real_front_checkpoint.json", {
        "phase": "506B", "stage": "front_depth7_refined",
        "pair_index": pair_index, "faed_scored": True,
        "execution_lock_sha256": sha(LOCK), "population_sha256": sha(pop),
        "front_record_sha256": sha(raw),
        "front_schedule_sha256": front.schedule_sha256(),
    })


def run_pair(pair_index):
    verify_lock()
    if pair_index not in allowed_pair_indices():
        raise RuntimeError("pair index is outside the locked Phase-506B set")
    directory = work_dir(pair_index)
    result_path = directory / "phase506b_real_result.json"
    if result_path.exists():
        raise FileExistsError("refusing to overwrite Phase-506B result")
    directory.mkdir(parents=True, exist_ok=True)
    models = exact.train_profile_models()
    fixture_index = 506000 + pair_index
    old_make, old_train = exact.make_fixture, exact.train_profile_models
    old_score, old_schedule = front.constrained_multistart, continuation.SCHEDULE
    old_commit = continuation.commit_stage

    def supply(index=0, split="dev"):
        if index == fixture_index and split == "dev":
            return real_fixture(pair_index)
        raise RuntimeError("unexpected fixture request")

    def unrestricted(paths, blocks, pair, quad, restarts, iterations,
                     binary=variants.UNRESTRICTED_BINARY, seed=front.BOARD_SEED):
        return old_score(paths, blocks, pair, quad, restarts, iterations,
                         binary=variants.UNRESTRICTED_BINARY, seed=seed)

    def real_commit(*args, **kwargs):
        output = old_commit(*args, **kwargs)
        sanitize(Path(args[0]))
        return output

    exact.make_fixture, exact.train_profile_models = supply, lambda: models
    front.constrained_multistart = unrestricted
    continuation.commit_stage = real_commit
    try:
        source = validate_front(directory, pair_index)
        if source is None:
            front.run_front(fixture_index, "dev", directory,
                            board_binary=variants.UNRESTRICTED_BINARY)
            mark_front(directory, pair_index)
            source = validate_front(directory, pair_index)
        continuation.SCHEDULE = EARLY
        cur = continuation.lane_a_depth8(source, fixture_index, "dev", directory)
        cur = continuation.global_depth(cur, 9, EARLY["lane_a_depth8_keep"],
                                        fixture_index, "dev", directory, "depth9")
        continuation.SCHEDULE = BASE
        cur = continuation.global_depth(cur, 10, BASE["lane_a_depth8_keep"],
                                        fixture_index, "dev", directory, "depth10")
        continuation.SCHEDULE = BRIDGE
        cur = continuation.bridge_depth(
            cur, 11, BRIDGE["lane_a_bridge_parent_keep"],
            BRIDGE["lane_a_bridge_children_per_parent"],
            BRIDGE["lane_a_bridge_parent_keep"] *
            BRIDGE["lane_a_bridge_children_per_parent"],
            fixture_index, "dev", directory, "depth11_bridge")
        continuation.SCHEDULE = BASE
        for depth in range(12, 20):
            keep = (BASE["depth13_16_keep"] if depth <= 16
                    else BASE["depth17_19_keep"])
            cur = continuation.global_depth(cur, depth, keep, fixture_index,
                                            "dev", directory, f"depth{depth}")
        continuation.final_resolve(cur, fixture_index, "dev", directory)
        sanitize(directory)
    finally:
        continuation.SCHEDULE = old_schedule
        continuation.commit_stage = old_commit
        front.constrained_multistart = old_score
        exact.train_profile_models, exact.make_fixture = old_train, old_make
    final = json.loads((directory / "continuation/final_resolve.json").read_text())
    candidates = final.get("final_candidates", [])
    result = {
        "phase": "506B", "status": "real_faed_width19_pair_complete",
        "faed_scored": True, "holdout_consumed": False,
        "input": pair_identity(pair_index),
        "execution_lock_sha256": sha(LOCK),
        "terminal_candidates": final.get("terminal_candidates", []),
        "skipped_terminals": final.get("skipped_terminals", []),
        "final_candidates": candidates,
        "top1_normalized_score": (candidates[0]["normalized_score"]
                                  if candidates else None),
        "top1_plaintext": candidates[0]["plaintext"] if candidates else None,
        "disposition": "requires_manual_readability_review",
    }
    atomic(result_path, result)
    return result


def self_test():
    if len(ranker.ceiling.ALL_PAIRS) != 36:
        raise AssertionError("pair universe changed")
    if set(BRIDGE) != set(BASE):
        raise AssertionError("schedule keys changed")
    for index in (0, 17, 35):
        fixture = real_fixture(index)
        if fixture["observed"] != FAED or tuple(fixture["pair"]) != ranker.ceiling.ALL_PAIRS[index]:
            raise AssertionError("real adapter mismatch")
    return {"self_test": "pass", "pair_count": 36,
            "faed_ascii_sha256": ranker.FAED_SHA256,
            "checkpointed": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--print-lock", action="store_true")
    group.add_argument("--verify-lock", action="store_true")
    group.add_argument("--run-pair-index", type=int)
    args = parser.parse_args()
    if args.self_test:
        result = self_test()
    elif args.print_lock:
        result = lock_payload()
    elif args.verify_lock:
        result = verify_lock()
    else:
        result = run_pair(args.run_pair_index)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
