#!/usr/bin/env python3
"""Exploratory corrected {g,i} FAED rerun after exact-profile calibration."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path

from data import FAED
import phase484a_raw_symbol_vic_solver as base
import phase484q_blind_joint_width19_solver as solver
import phase484x_exact_faed_profile_power_probe as exact

SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT = SCRIPT_DIR / "phase484x_corrected_faed_gi_result.json"
FAED_SHA256 = "066191b4aafc114fbca7f0d168382f40129c4ff18490375b689741081d5ef3c2"


def self_test():
    if hashlib.sha256(FAED.encode("ascii")).hexdigest() != FAED_SHA256:
        raise AssertionError("FAED input hash changed")
    tokens = base.segment_raw(FAED, exact.PAIR)
    if collections.Counter(tokens) != collections.Counter(
            exact.TARGET_TOKEN_COUNTS):
        raise AssertionError("FAED token histogram differs from calibration target")
    if collections.Counter(FAED) != collections.Counter(exact.TARGET_RAW_COUNTS):
        raise AssertionError("FAED raw histogram differs from calibration target")
    if len(tokens) != 436:
        raise AssertionError("FAED {g,i} token length changed")
    return {"faed_sha256": FAED_SHA256, "tokens": len(tokens),
            "single_slots": sum(len(token) == 1 for token in tokens)}


def run():
    checks = self_test()
    models = exact.train_profile_models()
    result = solver.screen_observed(
        FAED,
        exact.PAIR_INDEX,
        keep=262144,
        refine_keep=8192,
        extend_seed_count=256,
        extend_workers=8,
        extension_backend="persistent",
        shortlist_models=models,
        shortlist_final_keep=exact.FINAL_SHORTLIST_KEEP,
    )
    result["phase"] = "484X"
    result["status"] = "exploratory_profile_corrected_faed_gi_complete"
    result["inference_scope"] = (
        "post-miss diagnostic; readable hits are confirmable, misses are non-closing")
    result["input_checks"] = checks
    result["profile_training_indices"] = list(exact.PROFILE_TRAIN_INDICES)
    result["depth8_final_keep"] = exact.FINAL_SHORTLIST_KEEP
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), indent=2))
        return 0
    if not args.run:
        parser.error("use --self-test or --run")
    result = run()
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print("best score", result["top1_final_normalized_score"])
    print("best plaintext", result["final_candidates"][0]["plaintext"])
    print("wrote", args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
