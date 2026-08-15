#!/usr/bin/env python3
"""Indel-tolerant DBBI/FAED alignment with selection-aware null controls.

The declared model is unit-cost global Levenshtein alignment between forward
DBBI and every length-91 FAED window.  It also reports the six non-overlapping
windows from the earlier exact-lane model.  Costs and orientations are fixed;
no gap tuning or post-gap interpretation is performed.
"""

import argparse
import json
import random

from data import DBBI, FAED


WINDOW = len(DBBI)
FIXED_STARTS = tuple(range(0, 6 * WINDOW, WINDOW))
TRIALS = 2_000
SEED = 0xA11C0DE
STAT_SPECS = (
    "minimum_sliding_distance",
    "minimum_fixed_distance",
    "sum_fixed_distances",
)


def levenshtein_bitparallel(pattern, text):
    """Exact unit-cost Levenshtein distance using Myers bit vectors."""
    if not pattern:
        return len(text)
    width = len(pattern)
    mask = (1 << width) - 1
    high_bit = 1 << (width - 1)
    equality = {}
    for index, symbol in enumerate(pattern):
        equality[symbol] = equality.get(symbol, 0) | (1 << index)
    positive = mask
    negative = 0
    score = width
    for symbol in text:
        equal = equality.get(symbol, 0)
        vertical = equal | negative
        horizontal = (((equal & positive) + positive) ^ positive) | equal
        positive_horizontal = negative | ~(horizontal | positive)
        negative_horizontal = positive & horizontal
        if positive_horizontal & high_bit:
            score += 1
        if negative_horizontal & high_bit:
            score -= 1
        positive_horizontal = ((positive_horizontal << 1) | 1) & mask
        negative_horizontal = (negative_horizontal << 1) & mask
        positive = (negative_horizontal | ~(vertical | positive_horizontal)) & mask
        negative = positive_horizontal & vertical
    return score


def distances(pattern=DBBI, carrier=FAED):
    return tuple(
        levenshtein_bitparallel(pattern, carrier[start:start + WINDOW])
        for start in range(len(carrier) - WINDOW + 1)
    )


def statistics(all_distances):
    fixed = tuple(all_distances[start] for start in FIXED_STARTS)
    return {
        "minimum_sliding_distance": min(all_distances),
        "minimum_fixed_distance": min(fixed),
        "sum_fixed_distances": sum(fixed),
    }, fixed


def traceback_alignment(pattern, text):
    """Deterministic NW traceback for the single observed best window."""
    rows = len(pattern) + 1
    cols = len(text) + 1
    table = [[0] * cols for _ in range(rows)]
    for row in range(rows):
        table[row][0] = row
    for col in range(cols):
        table[0][col] = col
    for row in range(1, rows):
        for col in range(1, cols):
            table[row][col] = min(
                table[row - 1][col - 1] + (pattern[row - 1] != text[col - 1]),
                table[row - 1][col] + 1,
                table[row][col - 1] + 1,
            )
    row, col = len(pattern), len(text)
    left = []
    right = []
    operations = []
    while row or col:
        if row and col:
            substitution = pattern[row - 1] != text[col - 1]
            if table[row][col] == table[row - 1][col - 1] + substitution:
                left.append(pattern[row - 1])
                right.append(text[col - 1])
                operations.append("X" if substitution else "=")
                row -= 1
                col -= 1
                continue
        if row and table[row][col] == table[row - 1][col] + 1:
            left.append(pattern[row - 1])
            right.append("-")
            operations.append("D")
            row -= 1
            continue
        left.append("-")
        right.append(text[col - 1])
        operations.append("I")
        col -= 1
    left.reverse()
    right.reverse()
    operations.reverse()
    operation_text = "".join(operations)
    return {
        "pattern": "".join(left),
        "window": "".join(right),
        "operations": operation_text,
        "distance": table[-1][-1],
        "matches": operation_text.count("="),
        "substitutions": operation_text.count("X"),
        "deletions": operation_text.count("D"),
        "insertions": operation_text.count("I"),
    }


def empirical_lower_p(observed, null_values):
    return (1 + sum(value <= observed for value in null_values)) / (
        len(null_values) + 1
    )


def median(values):
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2


def audit(trials=TRIALS, seed=SEED):
    if trials < 1:
        raise ValueError("trials must be positive")
    observed_distances = distances()
    observed, fixed = statistics(observed_distances)
    best_start = min(
        range(len(observed_distances)),
        key=lambda start: (observed_distances[start], start),
    )
    best_window = FAED[best_start:best_start + WINDOW]
    alignment = traceback_alignment(DBBI, best_window)
    assert alignment["distance"] == observed["minimum_sliding_distance"]

    rng = random.Random(seed)
    pattern_profile = list(DBBI)
    carrier_profile = list(FAED)
    null = {name: [] for name in STAT_SPECS}
    for _ in range(trials):
        rng.shuffle(pattern_profile)
        rng.shuffle(carrier_profile)
        trial_distances = distances(
            "".join(pattern_profile), "".join(carrier_profile)
        )
        trial_statistics, _ = statistics(trial_distances)
        for name in STAT_SPECS:
            null[name].append(trial_statistics[name])

    statistic_rows = []
    family_size = len(STAT_SPECS)
    for name in STAT_SPECS:
        raw_p = empirical_lower_p(observed[name], null[name])
        statistic_rows.append({
            "name": name,
            "observed": observed[name],
            "null_median": median(null[name]),
            "raw_p": raw_p,
            "family_p": min(1.0, family_size * raw_p),
        })
    corrected_minimum = min(row["family_p"] for row in statistic_rows)
    return {
        "model": {
            "alignment": "global unit-cost Levenshtein",
            "match_cost": 0,
            "substitution_cost": 1,
            "insertion_cost": 1,
            "deletion_cost": 1,
            "pattern_orientation": "forward DBBI",
            "window_width": WINDOW,
            "sliding_window_count": len(observed_distances),
            "fixed_starts": FIXED_STARTS,
            "alternate_cost_models_tested": 0,
        },
        "fixed_distances": fixed,
        "best_start": best_start,
        "best_window": best_window,
        "best_alignment": alignment,
        "trials": trials,
        "seed": seed,
        "statistic_rows": tuple(statistic_rows),
        "corrected_minimum": corrected_minimum,
        "gate_threshold": 0.01,
        "gate_passed": corrected_minimum < 0.01,
        "gap_positions_interpreted": False,
        "candidate_text_generated": False,
        "password_oracle_run": False,
    }


def self_test():
    pairs = (
        ("", "", 0),
        ("abc", "abc", 0),
        ("abc", "axc", 1),
        ("abc", "abxc", 1),
        ("kitten", "sitting", 3),
    )
    for left, right, expected in pairs:
        assert levenshtein_bitparallel(left, right) == expected
        assert traceback_alignment(left, right)["distance"] == expected
    synthetic = "z" * 20 + DBBI + "z" * 4
    synthetic_distances = distances(DBBI, synthetic)
    assert min(synthetic_distances) == 0
    assert synthetic_distances.index(0) == 20
    report = audit(trials=100)
    assert report["model"]["sliding_window_count"] == 480
    assert len(report["fixed_distances"]) == 6
    assert not report["gap_positions_interpreted"]
    assert not report["candidate_text_generated"]
    print("[*] self-test OK: bit-parallel distances, traceback, and selection controls verified")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=TRIALS)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = self_test() if args.self_test else audit(args.trials, args.seed)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    print("[*] model:", report["model"])
    print("[*] fixed distances:", report["fixed_distances"])
    print(
        "[*] best sliding window:", report["best_start"],
        "distance", report["best_alignment"]["distance"],
        "operations", {
            key: report["best_alignment"][key]
            for key in ("matches", "substitutions", "deletions", "insertions")
        },
    )
    for row in report["statistic_rows"]:
        print(
            f"[*] {row['name']}: observed={row['observed']} "
            f"null_median={row['null_median']} raw_p={row['raw_p']:.6f} "
            f"family_p={row['family_p']:.6f}"
        )
    print("[*] gate passed:", report["gate_passed"])
    print("[*] no gap interpretation, candidate text, or password oracle was used")


if __name__ == "__main__":
    main()
