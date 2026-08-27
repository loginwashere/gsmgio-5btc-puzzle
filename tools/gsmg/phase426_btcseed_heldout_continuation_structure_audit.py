#!/usr/bin/env python3
"""Phase 426: conditional held-out structure audit of the BTCSEED tail.

The protocol was frozen before execution in
``doc/Brainstorms/2026-08-27 - Phase 426 BTCSEED Held-Out Continuation Structure Pre-Registration.md``.
Only ``decoded[7:]`` is tested.  The null consists of exact-multiset
permutations of those 563 letters; no decoder variants or downstream oracles
are evaluated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import zlib
from collections import Counter
from pathlib import Path

from phase386_btcseed_bifid_faed_decode_audit import audit as phase386_audit
from phase387_btcseed_kmodest_checkpoint_audit import (
    QUADGRAM_PATH,
    load_quadgrams,
    quadgram_mean,
)

TARGET = "BTCSEED"
DEFAULT_TRIALS = 10_000
DEFAULT_SEED = 0x426
EXPECTED_DECODED_SHA256 = "0c5d984f90e9baefc09f1d3888e62acbd101f9b0194887e2ae88fc6c9967745e"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def raw_deflate_saving(text: str) -> int:
    compressor = zlib.compressobj(level=9, wbits=-15)
    compressed = compressor.compress(text.encode("ascii")) + compressor.flush()
    return len(text) - len(compressed)


def lag1_mutual_information(text: str) -> float:
    """Plug-in I(X_t; X_(t+1)) in bits."""
    if len(text) < 2:
        return 0.0
    left = Counter(text[:-1])
    right = Counter(text[1:])
    pairs = Counter(zip(text[:-1], text[1:]))
    n = len(text) - 1
    result = 0.0
    for (a, b), count in pairs.items():
        result += (count / n) * math.log2((count * n) / (left[a] * right[b]))
    return result


def longest_repeated_substring(text: str) -> int:
    """Return exact LRS length using a linear-size suffix automaton."""
    transitions: list[dict[str, int]] = [{}]
    links = [-1]
    lengths = [0]
    occurrences = [0]
    last = 0

    for ch in text:
        current = len(transitions)
        transitions.append({})
        lengths.append(lengths[last] + 1)
        links.append(0)
        occurrences.append(1)
        p = last
        while p >= 0 and ch not in transitions[p]:
            transitions[p][ch] = current
            p = links[p]
        if p < 0:
            links[current] = 0
        else:
            q = transitions[p][ch]
            if lengths[p] + 1 == lengths[q]:
                links[current] = q
            else:
                clone = len(transitions)
                transitions.append(transitions[q].copy())
                lengths.append(lengths[p] + 1)
                links.append(links[q])
                occurrences.append(0)
                while p >= 0 and transitions[p].get(ch) == q:
                    transitions[p][ch] = clone
                    p = links[p]
                links[q] = links[current] = clone
        last = current

    for state in sorted(range(1, len(transitions)), key=lengths.__getitem__, reverse=True):
        occurrences[links[state]] += occurrences[state]
    return max((lengths[i] for i in range(1, len(transitions)) if occurrences[i] >= 2), default=0)


def brute_force_lrs(text: str) -> int:
    best = 0
    for i in range(len(text)):
        for j in range(i + 1, len(text)):
            k = 0
            while i + k < len(text) and j + k < len(text) and text[i + k] == text[j + k]:
                k += 1
            best = max(best, k)
    return best


def statistics_for(text: str, logs: dict[str, float], floor: float) -> dict[str, float | int]:
    return {
        "english_quadgram_mean": quadgram_mean(text, logs, floor),
        "raw_deflate_saving": raw_deflate_saving(text),
        "lag1_mutual_information_bits": lag1_mutual_information(text),
        "longest_repeated_substring": longest_repeated_substring(text),
    }


def inclusive_upper_tail_fractions(values: list[float | int]) -> list[float]:
    """For each value return count(all values >= value) / len(values)."""
    counts = Counter(values)
    greater_or_equal = 0
    fractions: dict[float | int, float] = {}
    for value in sorted(counts, reverse=True):
        greater_or_equal += counts[value]
        fractions[value] = greater_or_equal / len(values)
    return [fractions[value] for value in values]


def calibrate_family(rows: list[dict[str, float | int]]) -> dict:
    names = tuple(rows[0])
    marginal_p = {
        name: inclusive_upper_tail_fractions([row[name] for row in rows])
        for name in names
    }
    row_min_p = [min(marginal_p[name][i] for name in names) for i in range(len(rows))]
    observed_min = row_min_p[0]
    corrected_count = sum(value <= observed_min for value in row_min_p)
    observed_suppliers = [name for name in names if marginal_p[name][0] == observed_min]
    return {
        "individual_p": {name: marginal_p[name][0] for name in names},
        "observed_min_marginal_p": observed_min,
        "observed_extremeness_suppliers": observed_suppliers,
        "family_tail_count_including_observed": corrected_count,
        "family_corrected_p": corrected_count / len(rows),
    }


def summarize(values: list[float | int]) -> dict:
    ordered = sorted(values)
    n = len(ordered)
    return {
        "min": ordered[0],
        "median": ordered[n // 2],
        "mean": sum(ordered) / n,
        "max": ordered[-1],
    }


def run_audit(trials: int = DEFAULT_TRIALS, seed: int = DEFAULT_SEED) -> dict:
    phase386 = phase386_audit()
    decoded = phase386["decoded"]
    decoded_hash = sha256_bytes(decoded.encode("ascii"))
    if decoded_hash != EXPECTED_DECODED_SHA256 or not decoded.startswith(TARGET):
        raise RuntimeError("Phase-386/425 decoded-stream regression failure")
    tail = decoded[len(TARGET):]
    if len(tail) != 563:
        raise RuntimeError("held-out tail length regression failure")

    logs, floor = load_quadgrams()
    observed = statistics_for(tail, logs, floor)
    rng = random.Random(seed)
    shuffled = list(tail)
    null_rows = []
    for _ in range(trials):
        rng.shuffle(shuffled)
        null_rows.append(statistics_for("".join(shuffled), logs, floor))

    calibration = calibrate_family([observed, *null_rows])
    corrected_p = calibration["family_corrected_p"]
    if corrected_p <= 0.01:
        outcome = "continuation_structure_positive"
    elif corrected_p <= 0.05:
        outcome = "continuation_structure_suggestive_only"
    else:
        outcome = "null_like_continuation"

    return {
        "phase": 426,
        "outcome": outcome,
        "protocol": {
            "tested_slice": "decoded[7:]",
            "tail_length": len(tail),
            "trials": trials,
            "seed": seed,
            "null": "exact_multiset_permutations_of_563_character_tail",
            "statistics": list(observed),
            "family_correction": "inclusive_upper_tail_rank_max_permutation",
            "oracle_calls": 0,
        },
        "provenance": {
            "decoded_sha256": decoded_hash,
            "tail_sha256": sha256_bytes(tail.encode("ascii")),
            "quadgram_table_sha256": sha256_bytes(QUADGRAM_PATH.read_bytes()),
            "decoded_prefix": decoded[:32],
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
            "This tests only ordering structure in the fixed 563-character continuation, "
            "conditional on its exact letter multiset and excluding BTCSEED. It does not "
            "search decoder variants or promote plaintext, KMODEST, or a downstream consumer."
        ),
    }


def self_test() -> None:
    samples = ("", "A", "AAAA", "BANANA", "ABCABXABC", "MISSISSIPPI")
    for sample in samples:
        assert longest_repeated_substring(sample) == brute_force_lrs(sample)
    assert lag1_mutual_information("ABABABABAB") >= 0.0
    assert lag1_mutual_information("ABCDEFGH") >= -1e-12

    logs, floor = load_quadgrams()
    english = "THISISAREPEATEDENGLISHSENTENCETHISISAREPEATEDENGLISHSENTENCE"
    shuffled = "".join(sorted(english))
    assert quadgram_mean(english, logs, floor) > quadgram_mean(shuffled, logs, floor)
    repeated = "ABCDE" * 100
    assert raw_deflate_saving(repeated) > raw_deflate_saving("".join(sorted(repeated)))
    assert longest_repeated_substring(repeated) >= 490


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
