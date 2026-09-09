#!/usr/bin/env python3
"""Fixed-total-budget ensemble probe for the exact-profile shortlist."""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import phase484j_constructive_prefix_beam_probe as prefix
import phase484k_bidirectional_segment_assembly_probe as bidi
import phase484q_blind_joint_width19_solver as solver
import phase484x_exact_faed_profile_power_probe as exact

SCRIPT_DIR = Path(__file__).resolve().parent
MODEL_GROUPS = (tuple(range(3, 8)), tuple(range(8, 13)))
TOTAL_KEEP = 262144


def path_set_sha256(paths):
    payload = "\n".join(",".join(map(str, path)) for path in sorted(paths))
    return hashlib.sha256(payload.encode("ascii")).hexdigest()


def run(fixture_index=14, total_keep=TOTAL_KEEP):
    if total_keep % len(MODEL_GROUPS):
        raise ValueError("total keep must divide evenly across model groups")
    fixture = exact.make_fixture(fixture_index)
    truth = prefix.order_to_sequence(fixture["order"])
    truth_windows = bidi.true_windows(truth, solver.DEPTH)
    per_model_keep = total_keep // len(MODEL_GROUPS)
    records = []
    union = set()
    began = time.monotonic()
    for group in MODEL_GROUPS:
        models = exact.train_profile_models(group)
        beam = solver.build_depth8_shortlist(
            fixture, keep=per_model_keep, models=models)
        paths = {path for _, path in beam}
        retained = sorted(paths & truth_windows)
        ranked = {path: rank for rank, (_, path) in enumerate(beam, 1)}
        records.append({
            "train_indices": list(group),
            "keep": per_model_keep,
            "beam_size": len(paths),
            "beam_path_set_sha256": path_set_sha256(paths),
            "true_segment_count_retained": len(retained),
            "best_true_segment_rank": min(
                (ranked[path] for path in retained), default=None),
        })
        union.update(paths)
    union_truth = sorted(union & truth_windows)
    return {
        "phase": "484X",
        "status": "development_fixed_budget_shortlist_ensemble_probe",
        "fixture_index": fixture_index,
        "total_keep": total_keep,
        "model_count": len(MODEL_GROUPS),
        "models": records,
        "union_size": len(union),
        "union_path_set_sha256": path_set_sha256(union),
        "union_true_segment_count_retained": len(union_truth),
        "union_retains_truth": bool(union_truth),
        "wall_seconds": time.monotonic() - began,
    }


def self_test():
    if set(MODEL_GROUPS[0]) & set(MODEL_GROUPS[1]):
        raise AssertionError("ensemble training groups overlap")
    if 14 in set().union(*map(set, MODEL_GROUPS)):
        raise AssertionError("diagnostic fixture leaks into training")
    sample = {(0, 1), (1, 0)}
    if path_set_sha256(sample) != path_set_sha256(reversed(sorted(sample))):
        raise AssertionError("path-set digest is order-dependent")
    return {"groups": [list(group) for group in MODEL_GROUPS],
            "total_keep": TOTAL_KEEP}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--fixture-index", type=int, default=14)
    parser.add_argument("--total-keep", type=int, default=TOTAL_KEEP)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), indent=2))
        return 0
    if not args.run:
        parser.error("use --self-test or --run")
    result = run(args.fixture_index, args.total_keep)
    output = args.output or SCRIPT_DIR / (
        f"phase484x_ensemble_i{args.fixture_index}_k{args.total_keep}.json")
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    print("wrote", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
