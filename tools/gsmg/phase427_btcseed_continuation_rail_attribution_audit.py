#!/usr/bin/env python3
"""Phase 427: parity-rail attribution control for Phase 426's tail hit."""

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


def interleave(even: list[str], odd: list[str], length: int) -> str:
    result = [""] * length
    result[0::2] = even
    result[1::2] = odd
    return "".join(result)


def run_audit(trials: int = DEFAULT_TRIALS, seed: int = DEFAULT_SEED) -> dict:
    decoded = phase386_audit()["decoded"]
    if sha256_bytes(decoded.encode("ascii")) != EXPECTED_DECODED_SHA256:
        raise RuntimeError("decoded-stream regression failure")
    tail = decoded[len(TARGET):]
    even_original = list(tail[0::2])
    odd_original = list(tail[1::2])
    even_multiset = Counter(even_original)
    odd_multiset = Counter(odd_original)
    logs, floor = load_quadgrams()
    observed = statistics_for(tail, logs, floor)

    rng = random.Random(seed)
    even = even_original.copy()
    odd = odd_original.copy()
    null_rows = []
    for _ in range(trials):
        rng.shuffle(even)
        rng.shuffle(odd)
        shuffled = interleave(even, odd, len(tail))
        assert Counter(shuffled[0::2]) == even_multiset
        assert Counter(shuffled[1::2]) == odd_multiset
        null_rows.append(statistics_for(shuffled, logs, floor))

    calibration = calibrate_family([observed, *null_rows])
    corrected_p = calibration["family_corrected_p"]
    if corrected_p <= 0.01:
        outcome = "residual_structure_positive"
    elif corrected_p <= 0.05:
        outcome = "residual_structure_suggestive_only"
    else:
        outcome = "rail_mechanical_attribution"

    return {
        "phase": 427,
        "outcome": outcome,
        "protocol": {
            "tested_slice": "decoded[7:]",
            "tail_length": len(tail),
            "trials": trials,
            "seed": seed,
            "null": "independent_exact_multiset_permutations_within_tail_parity_rails",
            "statistics": list(observed),
            "family_correction": "inclusive_upper_tail_rank_max_permutation",
            "oracle_calls": 0,
        },
        "provenance": {
            "decoded_sha256": sha256_bytes(decoded.encode("ascii")),
            "tail_sha256": sha256_bytes(tail.encode("ascii")),
        },
        "rails": {
            "local_even_length": len(even_original),
            "local_odd_length": len(odd_original),
            "local_even_alphabet": "".join(sorted(even_multiset)),
            "local_odd_alphabet": "".join(sorted(odd_multiset)),
            "local_even_counts": dict(sorted(even_multiset.items())),
            "local_odd_counts": dict(sorted(odd_multiset.items())),
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
            "This post-Phase-426 attribution control preserves the known Bifid parity-rail "
            "composition. It tests residual within-rail ordering only and cannot promote plaintext."
        ),
    }


def self_test() -> None:
    phase426_self_test()
    sample = "ABCDEFGHI"
    rebuilt = interleave(list(sample[0::2]), list(sample[1::2]), len(sample))
    assert rebuilt == sample


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
