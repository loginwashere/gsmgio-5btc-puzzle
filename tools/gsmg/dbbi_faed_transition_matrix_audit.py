#!/usr/bin/env python3
"""Test DBBI/FAED as canonical 9x9 directed-transition matrices.

Each adjacent a-i pair increments one matrix cell.  This creates a unique
9x9 object without choosing a width, padding, or route.  Nine pre-registered
adjacency statistics are calibrated against independent sequence shuffles
that preserve each stream's exact unigram profile.  A tenth statistic tests
the literal row-sum-plus-column-sum (total-degree) lists under every one of
9! FAED alphabet relabellings.

No matrix entry, sum, ordering, or apparent fragment is promoted into a
password.  The audit stops at structural evidence.
"""

import argparse
import itertools
import json
import math
import random

from data import DBBI, FAED


ALPHABET = "abcdefghi"
SIZE = len(ALPHABET)
TRANSFORMS = ("identity", "transpose", "reverse", "reverse_transpose")
SEQUENCE_METRIC_ALTERNATIVES = {
    "dbbi_mutual_information": "high",
    "faed_mutual_information": "high",
    "dbbi_residual_energy": "high",
    "faed_residual_energy": "high",
    "dbbi_asymmetry": "two_sided",
    "faed_asymmetry": "two_sided",
    "dbbi_self_transitions": "two_sided",
    "faed_self_transitions": "two_sided",
    "cross_max_abs_residual_correlation": "high",
}
PROFILE_METRIC_NAME = "degree_profile_max_abs_correlation"
FAMILY_SIZE = len(SEQUENCE_METRIC_ALTERNATIVES) + 1


def transition_matrix(stream):
    invalid = sorted(set(stream) - set(ALPHABET))
    if invalid:
        raise ValueError(f"symbols outside a-i: {invalid}")
    matrix = [[0] * SIZE for _ in range(SIZE)]
    for left, right in zip(stream, stream[1:]):
        matrix[ord(left) - ord("a")][ord(right) - ord("a")] += 1
    return tuple(tuple(row) for row in matrix)


def row_sums(matrix):
    return tuple(sum(row) for row in matrix)


def column_sums(matrix):
    return tuple(sum(matrix[row][column] for row in range(SIZE))
                 for column in range(SIZE))


def expected_matrix(stream):
    """Expected directed-adjacency counts under a random fixed-multiset order."""
    counts = tuple(stream.count(symbol) for symbol in ALPHABET)
    length = len(stream)
    return tuple(tuple(
        counts[left] * (counts[right] - (left == right)) / length
        for right in range(SIZE)
    ) for left in range(SIZE))


def flatten(matrix):
    return tuple(value for row in matrix for value in row)


def pearson_correlation(left, right):
    if len(left) != len(right) or not left:
        raise ValueError("correlation vectors must have equal nonzero length")
    left_mean = sum(left) / len(left)
    right_mean = sum(right) / len(right)
    left_centered = tuple(value - left_mean for value in left)
    right_centered = tuple(value - right_mean for value in right)
    numerator = sum(a * b for a, b in zip(left_centered, right_centered))
    denominator = math.sqrt(
        sum(value * value for value in left_centered)
        * sum(value * value for value in right_centered)
    )
    return 0.0 if denominator == 0 else numerator / denominator


def transform_matrix(matrix, transform):
    if transform not in TRANSFORMS:
        raise ValueError(f"unknown transform: {transform}")
    output = []
    for row in range(SIZE):
        output_row = []
        for column in range(SIZE):
            source_row, source_column = row, column
            if "reverse" in transform:
                source_row = SIZE - 1 - source_row
                source_column = SIZE - 1 - source_column
            if "transpose" in transform:
                source_row, source_column = source_column, source_row
            output_row.append(matrix[source_row][source_column])
        output.append(tuple(output_row))
    return tuple(output)


def stream_observation(stream):
    matrix = transition_matrix(stream)
    expected = expected_matrix(stream)
    residual = tuple(tuple(
        matrix[row][column] - expected[row][column]
        for column in range(SIZE)
    ) for row in range(SIZE))
    rows = row_sums(matrix)
    columns = column_sums(matrix)
    transitions = len(stream) - 1

    mutual_information = 0.0
    for row in range(SIZE):
        for column in range(SIZE):
            observed = matrix[row][column]
            if not observed or not rows[row] or not columns[column]:
                continue
            joint = observed / transitions
            mutual_information += joint * math.log2(
                joint / ((rows[row] / transitions) *
                         (columns[column] / transitions))
            )

    residual_energy = sum(
        (matrix[row][column] - expected[row][column]) ** 2
        / expected[row][column]
        for row in range(SIZE)
        for column in range(SIZE)
        if expected[row][column] > 0
    )
    asymmetry = sum(
        abs(matrix[row][column] - matrix[column][row])
        for row in range(SIZE)
        for column in range(row + 1, SIZE)
    )
    return {
        "matrix": matrix,
        "expected": expected,
        "residual": residual,
        "row_sums": rows,
        "column_sums": columns,
        "degree_sums": tuple(a + b for a, b in zip(rows, columns)),
        "mutual_information": mutual_information,
        "residual_energy": residual_energy,
        "asymmetry": asymmetry,
        "self_transitions": sum(matrix[index][index] for index in range(SIZE)),
    }


def cross_residual_correlations(dbbi_observation, faed_observation):
    left = flatten(dbbi_observation["residual"])
    rows = {}
    for transform in TRANSFORMS:
        transformed = transform_matrix(faed_observation["residual"], transform)
        rows[transform] = pearson_correlation(left, flatten(transformed))
    return rows


def combined_sequence_metrics(dbbi_observation, faed_observation):
    cross = cross_residual_correlations(dbbi_observation, faed_observation)
    return {
        "dbbi_mutual_information": dbbi_observation["mutual_information"],
        "faed_mutual_information": faed_observation["mutual_information"],
        "dbbi_residual_energy": dbbi_observation["residual_energy"],
        "faed_residual_energy": faed_observation["residual_energy"],
        "dbbi_asymmetry": dbbi_observation["asymmetry"],
        "faed_asymmetry": faed_observation["asymmetry"],
        "dbbi_self_transitions": dbbi_observation["self_transitions"],
        "faed_self_transitions": faed_observation["self_transitions"],
        "cross_max_abs_residual_correlation": max(map(abs, cross.values())),
    }


def empirical_p(observed, null_values, alternative):
    if alternative == "high":
        return (1 + sum(value >= observed for value in null_values)) / (
            len(null_values) + 1
        )
    if alternative == "two_sided":
        lower = (1 + sum(value <= observed for value in null_values)) / (
            len(null_values) + 1
        )
        upper = (1 + sum(value >= observed for value in null_values)) / (
            len(null_values) + 1
        )
        return min(1.0, 2 * min(lower, upper))
    raise ValueError(f"unknown alternative: {alternative}")


def sequence_null_calibration(observed_metrics, trials, seed):
    rng = random.Random(seed)
    shuffled_dbbi = list(DBBI)
    shuffled_faed = list(FAED)
    nulls = {name: [] for name in SEQUENCE_METRIC_ALTERNATIVES}
    for _ in range(trials):
        rng.shuffle(shuffled_dbbi)
        rng.shuffle(shuffled_faed)
        dbbi_observation = stream_observation("".join(shuffled_dbbi))
        faed_observation = stream_observation("".join(shuffled_faed))
        metrics = combined_sequence_metrics(dbbi_observation, faed_observation)
        for name in nulls:
            nulls[name].append(metrics[name])

    rows = {}
    for name, alternative in SEQUENCE_METRIC_ALTERNATIVES.items():
        values = sorted(nulls[name])
        raw_p = empirical_p(observed_metrics[name], values, alternative)
        rows[name] = {
            "observed": observed_metrics[name],
            "alternative": alternative,
            "null_median": values[len(values) // 2],
            "null_5th_percentile": values[(5 * len(values)) // 100],
            "null_95th_percentile": values[(95 * len(values)) // 100],
            "empirical_p": raw_p,
            "family_bonferroni_p": min(1.0, raw_p * FAMILY_SIZE),
        }
    return rows


def degree_profile_test(dbbi_observation, faed_observation):
    left = dbbi_observation["degree_sums"]
    right = faed_observation["degree_sums"]

    def statistic(permutation):
        permuted = tuple(right[index] for index in permutation)
        reversed_permuted = permuted[::-1]
        return max(
            abs(pearson_correlation(left, permuted)),
            abs(pearson_correlation(left, reversed_permuted)),
        )

    identity = tuple(range(SIZE))
    observed = statistic(identity)
    as_large = 0
    total = math.factorial(SIZE)
    for permutation in itertools.permutations(range(SIZE)):
        as_large += statistic(permutation) >= observed - 1e-15
    exact_p = as_large / total
    return {
        "name": PROFILE_METRIC_NAME,
        "dbbi_degree_sums": left,
        "faed_degree_sums": right,
        "orientations": ("identity", "reversed_alphabet"),
        "observed_max_abs_correlation": observed,
        "null_model": "all 9! FAED alphabet relabellings, best of identity/reversal",
        "permutation_count": total,
        "as_large_count": as_large,
        "exact_p": exact_p,
        "family_bonferroni_p": min(1.0, exact_p * FAMILY_SIZE),
    }


def audit(trials=20_000, seed=20260814):
    if trials < 1:
        raise ValueError("trials must be positive")
    dbbi_observation = stream_observation(DBBI)
    faed_observation = stream_observation(FAED)
    observed_metrics = combined_sequence_metrics(dbbi_observation, faed_observation)
    sequence_rows = sequence_null_calibration(observed_metrics, trials, seed)
    profile = degree_profile_test(dbbi_observation, faed_observation)
    corrected = tuple(
        row["family_bonferroni_p"] for row in sequence_rows.values()
    ) + (profile["family_bonferroni_p"],)
    family_p = min(corrected)
    threshold = 0.01
    return {
        "source_lengths": {"DBBI": len(DBBI), "FAED": len(FAED)},
        "alphabet": ALPHABET,
        "matrix_shape": (SIZE, SIZE),
        "transition_totals": {"DBBI": len(DBBI) - 1, "FAED": len(FAED) - 1},
        "DBBI": {
            key: value for key, value in dbbi_observation.items()
            if key != "expected" and key != "residual"
        },
        "FAED": {
            key: value for key, value in faed_observation.items()
            if key != "expected" and key != "residual"
        },
        "cross_residual_correlations": cross_residual_correlations(
            dbbi_observation, faed_observation
        ),
        "sequence_calibration": {
            "trials": trials,
            "seed": seed,
            "null_model": "independent sequence shuffles preserving exact unigram profiles",
            "rows": sequence_rows,
        },
        "degree_profile_test": profile,
        "family": {
            "metric_count": FAMILY_SIZE,
            "bonferroni_p_bound": family_p,
            "promotion_threshold": threshold,
            "promoted": family_p < threshold,
        },
        "candidate_text_generated": False,
        "password_oracle_run": False,
    }


def self_test():
    matrix = transition_matrix("abaca")
    assert sum(map(sum, matrix)) == 4
    assert row_sums(matrix) == (2, 1, 1, 0, 0, 0, 0, 0, 0)
    assert column_sums(matrix) == (2, 1, 1, 0, 0, 0, 0, 0, 0)
    assert transform_matrix(matrix, "transpose")[1][0] == matrix[0][1]
    report = audit(trials=25)
    assert report["matrix_shape"] == (9, 9)
    assert report["transition_totals"] == {"DBBI": 90, "FAED": 569}
    assert report["degree_profile_test"]["permutation_count"] == 362_880
    assert not report["candidate_text_generated"]
    assert not report["password_oracle_run"]
    print("[*] self-test OK: canonical transition matrices and both null models verified")
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
    print("[*] matrices: DBBI 9x9/90 transitions; FAED 9x9/569 transitions")
    print("[*] DBBI row sums:", report["DBBI"]["row_sums"])
    print("[*] DBBI column sums:", report["DBBI"]["column_sums"])
    print("[*] FAED row sums:", report["FAED"]["row_sums"])
    print("[*] FAED column sums:", report["FAED"]["column_sums"])
    for name, row in report["sequence_calibration"]["rows"].items():
        print(
            f"    {name}: observed={row['observed']:.9g} "
            f"null_median={row['null_median']:.9g} "
            f"raw_p={row['empirical_p']:.6g} "
            f"corrected_p={row['family_bonferroni_p']:.6g}"
        )
    profile = report["degree_profile_test"]
    print(
        f"    {PROFILE_METRIC_NAME}: "
        f"observed={profile['observed_max_abs_correlation']:.9g} "
        f"exact_p={profile['exact_p']:.6g} "
        f"corrected_p={profile['family_bonferroni_p']:.6g}"
    )
    print(
        "[*] family p-bound:",
        f"{report['family']['bonferroni_p_bound']:.6g}",
        "promoted=" + str(report["family"]["promoted"]),
    )
    print("[*] no candidate text or password oracle was used")


if __name__ == "__main__":
    main()

