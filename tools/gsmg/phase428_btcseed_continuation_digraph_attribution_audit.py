#!/usr/bin/env python3
"""Phase 428: intact-digraph attribution control for the BTCSEED tail."""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path

from phase386_btcseed_bifid_faed_decode_audit import audit as phase386_audit
from phase387_btcseed_kmodest_checkpoint_audit import load_quadgrams
from phase426_btcseed_heldout_continuation_structure_audit import (
    DEFAULT_SEED,
    DEFAULT_TRIALS,
    EXPECTED_DECODED_SHA256,
    TARGET,
    calibrate_family,
    self_test as phase426_self_test,
    sha256_bytes,
    statistics_for,
    summarize,
)


def split_tail(tail: str) -> tuple[str, list[str]]:
    singleton = tail[0]
    digraphs = [tail[i : i + 2] for i in range(1, len(tail), 2)]
    assert all(len(block) == 2 for block in digraphs)
    return singleton, digraphs


def join_tail(singleton: str, digraphs: list[str]) -> str:
    return singleton + "".join(digraphs)


def run_audit(trials: int = DEFAULT_TRIALS, seed: int = DEFAULT_SEED) -> dict:
    decoded = phase386_audit()["decoded"]
    if sha256_bytes(decoded.encode("ascii")) != EXPECTED_DECODED_SHA256:
        raise RuntimeError("decoded-stream regression failure")
    tail = decoded[len(TARGET):]
    singleton, original_digraphs = split_tail(tail)
    digraph_multiset = Counter(original_digraphs)
    tail_multiset = Counter(tail)
    logs, floor = load_quadgrams()
    observed = statistics_for(tail, logs, floor)

    rng = random.Random(seed)
    digraphs = original_digraphs.copy()
    null_rows = []
    for _ in range(trials):
        rng.shuffle(digraphs)
        shuffled = join_tail(singleton, digraphs)
        assert shuffled[0] == singleton
        assert len(shuffled) == len(tail)
        assert Counter(shuffled) == tail_multiset
        assert Counter(split_tail(shuffled)[1]) == digraph_multiset
        null_rows.append(statistics_for(shuffled, logs, floor))

    calibration = calibrate_family([observed, *null_rows])
    corrected_p = calibration["family_corrected_p"]
    if corrected_p <= 0.01:
        outcome = "beyond_digraph_residual_positive"
    elif corrected_p <= 0.05:
        outcome = "beyond_digraph_residual_suggestive_only"
    else:
        outcome = "digraph_mechanical_attribution"

    return {
        "phase": 428,
        "outcome": outcome,
        "protocol": {
            "tested_slice": "decoded[7:]",
            "tail_length": len(tail),
            "fixed_leading_singleton": singleton,
            "globally_aligned_digraph_count": len(original_digraphs),
            "trials": trials,
            "seed": seed,
            "null": "permutations_of_281_intact_global_bifid_output_digraphs_after_fixed_singleton",
            "statistics": list(observed),
            "family_correction": "inclusive_upper_tail_rank_max_permutation",
            "oracle_calls": 0,
        },
        "provenance": {
            "decoded_sha256": sha256_bytes(decoded.encode("ascii")),
            "tail_sha256": sha256_bytes(tail.encode("ascii")),
            "digraph_multiset_sha256": sha256_bytes(
                json.dumps(sorted(digraph_multiset.items()), separators=(",", ":")).encode("ascii")
            ),
        },
        "observed": observed,
        "calibration": calibration,
        "null_summaries": {
            name: summarize([row[name] for row in null_rows]) for name in observed
        },
        "null_ties_with_observed": {
            name: sum(row[name] == observed[name] for row in null_rows) for name in observed
        },
        "interpretation": (
            "This attribution control preserves the full-block Bifid transform's aligned "
            "output-digraph coupling and tests only ordering between those digraphs."
        ),
    }


def self_test() -> None:
    phase426_self_test()
    sample = "XABCDEFGH"
    singleton, digraphs = split_tail(sample)
    assert singleton == "X"
    assert digraphs == ["AB", "CD", "EF", "GH"]
    assert join_tail(singleton, digraphs) == sample


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=DEFAULT_TRIALS)
    parser.add_argument("--seed", type=lambda raw: int(raw, 0), default=DEFAULT_SEED)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    self_test()
    if args.self_test:
        print("[*] self-test OK")
        return
    report = run_audit(args.trials, args.seed)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
