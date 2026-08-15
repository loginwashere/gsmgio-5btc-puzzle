#!/usr/bin/env python3
"""Test the exact FAED = 6 * len(DBBI) + 24 structural hypothesis.

This audit deliberately stops before plaintext generation.  It compares six
non-overlapping 91-symbol FAED lanes with DBBI using pre-registered,
alphabet-independent structure measures plus one canonical mod-9 residual
measure.  Significance is calibrated by independently shuffling the exact
DBBI and FAED symbol multisets.  The eight body measures are corrected as one
family with a conservative Bonferroni bound.

The 24-symbol tail is kept separate.  Its sole first-pass question is whether
one consistent mapping from each a-i symbol to blue/yellow can reproduce the
authenticated 24-endpoint colour mask.  The best mapping is compared with
shuffles of that mask preserving its exact 15-blue/9-yellow profile.

No language model, password oracle, padding, lane permutation, or adaptive
selector is used.
"""

import argparse
import json
import random
from collections import Counter
from itertools import combinations

from data import DBBI, FAED
from first_piece_color_reconstruction import DEFAULT_IMAGE, reconstruct


LANE_COUNT = 6
LANE_WIDTH = 91
TAIL_LENGTH = 24
ALPHABET = "abcdefghi"
BODY_METRIC_NAMES = (
    "max_lane_match",
    "max_lane_match_run",
    "any_lane_match_columns",
    "unique_mode_matches",
    "max_residual_bin",
    "column_collision_excess",
    "max_lane_pair_matches",
    "max_lane_pair_match_run",
)


def longest_true_run(bits):
    best = current = 0
    for bit in bits:
        if bit:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def split_faed(faed=FAED):
    expected = LANE_COUNT * LANE_WIDTH + TAIL_LENGTH
    if len(faed) != expected:
        raise AssertionError(f"FAED length changed: {len(faed)} != {expected}")
    body = faed[:LANE_COUNT * LANE_WIDTH]
    lanes = tuple(
        body[index * LANE_WIDTH:(index + 1) * LANE_WIDTH]
        for index in range(LANE_COUNT)
    )
    tail = faed[len(body):]
    return lanes, tail


def residual_histogram(reference, lane):
    values = {symbol: index for index, symbol in enumerate(ALPHABET)}
    return tuple(Counter(
        (values[right] - values[left]) % len(ALPHABET)
        for left, right in zip(reference, lane)
    )[residue] for residue in range(len(ALPHABET)))


def body_observation(dbbi, lanes):
    if len(dbbi) != LANE_WIDTH:
        raise AssertionError(f"DBBI length changed: {len(dbbi)}")
    if len(lanes) != LANE_COUNT or any(len(lane) != LANE_WIDTH for lane in lanes):
        raise AssertionError("lane geometry changed")

    equality_masks = tuple(
        tuple(left == right for left, right in zip(dbbi, lane))
        for lane in lanes
    )
    lane_match_counts = tuple(sum(mask) for mask in equality_masks)
    lane_match_runs = tuple(longest_true_run(mask) for mask in equality_masks)
    residual_histograms = tuple(
        residual_histogram(dbbi, lane) for lane in lanes
    )

    columns = tuple(zip(*lanes))
    any_lane_match_columns = sum(
        reference in column for reference, column in zip(dbbi, columns)
    )
    unique_mode_columns = 0
    unique_mode_matches = 0
    distinct_symbol_counts = []
    for reference, column in zip(dbbi, columns):
        counts = Counter(column)
        distinct_symbol_counts.append(len(counts))
        top_count = max(counts.values())
        modes = tuple(symbol for symbol, count in counts.items() if count == top_count)
        if len(modes) == 1:
            unique_mode_columns += 1
            unique_mode_matches += modes[0] == reference

    pair_rows = []
    for left_index, right_index in combinations(range(LANE_COUNT), 2):
        mask = tuple(
            left == right
            for left, right in zip(lanes[left_index], lanes[right_index])
        )
        pair_rows.append({
            "lanes_1": (left_index + 1, right_index + 1),
            "matches": sum(mask),
            "longest_run": longest_true_run(mask),
        })

    metrics = {
        "max_lane_match": max(lane_match_counts),
        "max_lane_match_run": max(lane_match_runs),
        "any_lane_match_columns": any_lane_match_columns,
        "unique_mode_matches": unique_mode_matches,
        "max_residual_bin": max(max(row) for row in residual_histograms),
        "column_collision_excess": sum(
            LANE_COUNT - count for count in distinct_symbol_counts
        ),
        "max_lane_pair_matches": max(row["matches"] for row in pair_rows),
        "max_lane_pair_match_run": max(row["longest_run"] for row in pair_rows),
    }
    if tuple(metrics) != BODY_METRIC_NAMES:
        raise AssertionError("body metric registry/order drifted")

    return {
        "metrics": metrics,
        "lane_match_counts": lane_match_counts,
        "lane_match_longest_runs": lane_match_runs,
        "equality_masks": tuple(
            "".join("1" if bit else "0" for bit in mask)
            for mask in equality_masks
        ),
        "residual_histograms_0_to_8": residual_histograms,
        "unique_mode_columns": unique_mode_columns,
        "distinct_symbols_per_column_histogram": dict(sorted(Counter(
            distinct_symbol_counts
        ).items())),
        "lane_pair_rows": tuple(pair_rows),
    }


def empirical_upper_p(observed, null_values):
    return (1 + sum(value >= observed for value in null_values)) / (
        len(null_values) + 1
    )


def body_null_calibration(dbbi, faed_body, observed, trials, seed):
    rng = random.Random(seed)
    shuffled_dbbi = list(dbbi)
    shuffled_body = list(faed_body)
    nulls = {name: [] for name in BODY_METRIC_NAMES}
    for _ in range(trials):
        rng.shuffle(shuffled_dbbi)
        rng.shuffle(shuffled_body)
        lanes = tuple(
            "".join(shuffled_body[index * LANE_WIDTH:(index + 1) * LANE_WIDTH])
            for index in range(LANE_COUNT)
        )
        row = body_observation("".join(shuffled_dbbi), lanes)["metrics"]
        for name in BODY_METRIC_NAMES:
            nulls[name].append(row[name])

    rows = {}
    for name in BODY_METRIC_NAMES:
        values = sorted(nulls[name])
        raw_p = empirical_upper_p(observed["metrics"][name], values)
        rows[name] = {
            "observed": observed["metrics"][name],
            "null_median": values[len(values) // 2],
            "null_95th_percentile": values[(95 * len(values)) // 100],
            "empirical_upper_p": raw_p,
            "bonferroni_p": min(1.0, raw_p * len(BODY_METRIC_NAMES)),
        }
    family_p = min(row["bonferroni_p"] for row in rows.values())
    return {
        "trials": trials,
        "seed": seed,
        "null_model": "independent shuffles preserving exact DBBI and FAED-body multisets",
        "metric_count": len(BODY_METRIC_NAMES),
        "rows": rows,
        "family_p_bound": family_p,
        "promotion_threshold": 0.01,
        "promoted": family_p < 0.01,
    }


def best_binary_projection(tail, endpoint_mask):
    if len(tail) != TAIL_LENGTH or len(endpoint_mask) != TAIL_LENGTH:
        raise AssertionError("tail/endpoint length changed")
    mapping = {}
    matches = 0
    conflicts = {}
    for symbol in ALPHABET:
        paired = Counter(
            endpoint_mask[index]
            for index, actual in enumerate(tail)
            if actual == symbol
        )
        if not paired:
            continue
        selected = max("BY", key=lambda color: (paired[color], color == "B"))
        mapping[symbol] = selected
        matches += paired[selected]
        conflicts[symbol] = dict(sorted(paired.items()))
    projected = "".join(mapping[symbol] for symbol in tail)
    return {
        "best_matches": matches,
        "mismatches": TAIL_LENGTH - matches,
        "exact_consistent_mapping": matches == TAIL_LENGTH,
        "mapping": mapping,
        "per_symbol_endpoint_counts": conflicts,
        "projected_mask": projected,
    }


def tail_null_calibration(tail, endpoint_mask, observed, trials, seed):
    rng = random.Random(seed)
    shuffled_mask = list(endpoint_mask)
    null_values = []
    for _ in range(trials):
        rng.shuffle(shuffled_mask)
        row = best_binary_projection(tail, "".join(shuffled_mask))
        null_values.append(row["best_matches"])
    null_values.sort()
    raw_p = empirical_upper_p(observed["best_matches"], null_values)
    return {
        "trials": trials,
        "seed": seed,
        "null_model": "endpoint-mask shuffles preserving exact 15B/9Y profile",
        "observed_best_matches": observed["best_matches"],
        "null_median": null_values[len(null_values) // 2],
        "null_95th_percentile": null_values[(95 * len(null_values)) // 100],
        "empirical_upper_p": raw_p,
        "promotion_threshold": 0.01,
        "promoted": raw_p < 0.01,
    }


def authenticated_endpoint_mask():
    report = reconstruct(DEFAULT_IMAGE)
    mask = report["color_sequence"]
    if len(mask) != TAIL_LENGTH or Counter(mask) != Counter({"B": 15, "Y": 9}):
        raise AssertionError("authenticated endpoint mask changed")
    return mask


def audit(trials=20_000, seed=20260814, endpoint_mask=None):
    if trials < 1:
        raise ValueError("trials must be positive")
    lanes, tail = split_faed()
    body = FAED[:LANE_COUNT * LANE_WIDTH]
    endpoint_mask = endpoint_mask or authenticated_endpoint_mask()
    observed_body = body_observation(DBBI, lanes)
    observed_tail = best_binary_projection(tail, endpoint_mask)
    body_calibration = body_null_calibration(
        DBBI, body, observed_body, trials, seed
    )
    tail_calibration = tail_null_calibration(
        tail, endpoint_mask, observed_tail, trials, seed + 1
    )
    return {
        "geometry": {
            "dbbi_length": len(DBBI),
            "faed_length": len(FAED),
            "lane_count": len(lanes),
            "lane_width": LANE_WIDTH,
            "body_length": len(body),
            "tail_length": len(tail),
            "identity": "570 = 6 * 91 + 24",
        },
        "body": observed_body,
        "body_calibration": body_calibration,
        "tail": {
            "symbols": tail,
            "endpoint_mask": endpoint_mask,
            **observed_tail,
        },
        "tail_calibration": tail_calibration,
        "promotion": {
            "body": body_calibration["promoted"],
            "tail": tail_calibration["promoted"],
            "any": body_calibration["promoted"] or tail_calibration["promoted"],
        },
        "plaintext_or_password_oracle_run": False,
    }


def self_test():
    lanes, tail = split_faed()
    assert len(lanes) == 6
    assert tuple(map(len, lanes)) == (91,) * 6
    assert len(tail) == 24
    synthetic_lanes = (DBBI,) + tuple("a" * LANE_WIDTH for _ in range(5))
    synthetic = body_observation(DBBI, synthetic_lanes)
    assert synthetic["lane_match_counts"][0] == 91
    assert synthetic["lane_match_longest_runs"][0] == 91
    assert synthetic["metrics"]["max_lane_match"] == 91
    exact_tail = best_binary_projection("abcdefghiabcdefghiabcdef", "BYBYBYBYBBYBYBYBYBBYBYBY")
    assert exact_tail["exact_consistent_mapping"]
    report = audit(trials=100)
    assert report["geometry"]["identity"] == "570 = 6 * 91 + 24"
    assert report["plaintext_or_password_oracle_run"] is False
    assert report["promotion"]["any"] is False
    print("[*] self-test OK: exact six-lane geometry and independent tail oracle verified")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=20_000)
    parser.add_argument("--seed", type=int, default=20260814)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = self_test() if args.self_test else audit(args.trials, args.seed)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    print(f"[*] geometry: {report['geometry']['identity']}")
    print("[*] lane matches:", report["body"]["lane_match_counts"])
    for name, row in report["body_calibration"]["rows"].items():
        print(
            f"    {name}: observed={row['observed']} "
            f"null_median={row['null_median']} "
            f"raw_p={row['empirical_upper_p']:.6g} "
            f"corrected_p={row['bonferroni_p']:.6g}"
        )
    print("[*] body family p-bound:",
          f"{report['body_calibration']['family_p_bound']:.6g}",
          "promoted=" + str(report["body_calibration"]["promoted"]))
    print("[*] tail projection:",
          f"{report['tail']['best_matches']}/24",
          f"p={report['tail_calibration']['empirical_upper_p']:.6g}",
          "promoted=" + str(report["tail_calibration"]["promoted"]))
    print("[*] no plaintext/password oracle was run")


if __name__ == "__main__":
    main()
