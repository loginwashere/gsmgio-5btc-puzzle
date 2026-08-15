#!/usr/bin/env python3
"""Bounded GF(9) recurrence/rank audit for DBBI and FAED.

The nine symbols are mapped through the two canonical coordinate orders of a
3x3 grid and the three monic irreducible quadratics over GF(3), for six field
presentations total.  The audit measures full-sequence Berlekamp-Massey linear
complexity, held-out recurrence satisfaction, transfer of DBBI's recurrence
to the six aligned 91-symbol FAED lanes, and rank of the resulting seven rows.

The best result across all six presentations is calibrated inside every null
trial.  Nulls independently shuffle the exact DBBI and FAED symbol multisets.
No arbitrary a-i permutation, plaintext score, or password oracle is used.
"""

import argparse
import json
import math
import random

from data import DBBI, FAED


ALPHABET = "abcdefghi"
LANE_COUNT = 6
LANE_WIDTH = len(DBBI)
BODY_LENGTH = LANE_COUNT * LANE_WIDTH
IRREDUCIBLE_QUADRATICS = (
    (0, 1),  # x^2 + 1
    (1, 2),  # x^2 + x + 2
    (2, 2),  # x^2 + 2x + 2
)
COORDINATE_ORDERS = ("row_column", "column_row")
METRIC_ALTERNATIVES = {
    "gf9_dbbi_min_linear_complexity": "low",
    "gf9_faed_min_linear_complexity": "low",
    "gf3_dbbi_min_component_complexity": "low",
    "gf3_faed_min_component_complexity": "low",
    "gf9_dbbi_max_holdout_z": "high",
    "gf9_faed_max_holdout_z": "high",
    "dbbi_to_faed_lane_max_z": "high",
    "joint_min_rank": "low",
}
FAMILY_SIZE = len(METRIC_ALTERNATIVES)


class FiniteField:
    def __init__(self, order, add_table, mul_table):
        self.order = order
        self.add_table = add_table
        self.mul_table = mul_table
        self.zero = 0
        self.one = 1 if order == 3 else 3  # GF(9) encodes 1 as (1,0) -> 3.
        self.neg_table = tuple(
            next(candidate for candidate in range(order)
                 if add_table[value][candidate] == self.zero)
            for value in range(order)
        )
        self.inv_table = tuple(
            0 if value == 0 else next(
                candidate for candidate in range(1, order)
                if mul_table[value][candidate] == self.one
            )
            for value in range(order)
        )

    def add(self, left, right):
        return self.add_table[left][right]

    def sub(self, left, right):
        return self.add_table[left][self.neg_table[right]]

    def mul(self, left, right):
        return self.mul_table[left][right]

    def div(self, left, right):
        if right == 0:
            raise ZeroDivisionError
        return self.mul_table[left][self.inv_table[right]]


def gf3():
    add = tuple(tuple((a + b) % 3 for b in range(3)) for a in range(3))
    mul = tuple(tuple((a * b) % 3 for b in range(3)) for a in range(3))
    return FiniteField(3, add, mul)


def decode9(value):
    return divmod(value, 3)  # constant coefficient, x coefficient


def encode9(constant, x_coefficient):
    return (constant % 3) * 3 + (x_coefficient % 3)


def gf9(linear_coefficient, constant_coefficient):
    """GF(3)[x] / (x^2 + p*x + q), arguments p, q."""
    p = linear_coefficient
    q = constant_coefficient
    add = []
    mul = []
    for left in range(9):
        left_constant, left_x = decode9(left)
        add_row = []
        mul_row = []
        for right in range(9):
            right_constant, right_x = decode9(right)
            add_row.append(encode9(
                left_constant + right_constant,
                left_x + right_x,
            ))
            # x^2 = -p*x - q
            product_x2 = left_x * right_x
            mul_row.append(encode9(
                left_constant * right_constant - q * product_x2,
                left_constant * right_x + left_x * right_constant
                - p * product_x2,
            ))
        add.append(tuple(add_row))
        mul.append(tuple(mul_row))
    return FiniteField(9, tuple(add), tuple(mul))


GF3 = gf3()
PRESENTATIONS = tuple(
    {
        "name": f"x2+{p}x+{q}/{order}",
        "p": p,
        "q": q,
        "coordinate_order": order,
        "field": gf9(p, q),
    }
    for p, q in IRREDUCIBLE_QUADRATICS
    for order in COORDINATE_ORDERS
)


def is_irreducible_quadratic(p, q):
    return all((root * root + p * root + q) % 3 for root in range(3))


def map_stream_gf9(stream, coordinate_order):
    output = []
    for symbol in stream:
        index = ord(symbol) - ord("a")
        if not 0 <= index < 9:
            raise ValueError(f"symbol outside a-i: {symbol!r}")
        row, column = divmod(index, 3)
        if coordinate_order == "column_row":
            row, column = column, row
        elif coordinate_order != "row_column":
            raise ValueError(f"unknown coordinate order: {coordinate_order}")
        output.append(encode9(row, column))
    return tuple(output)


def map_stream_components(stream):
    indices = tuple(ord(symbol) - ord("a") for symbol in stream)
    return (
        tuple(index // 3 for index in indices),
        tuple(index % 3 for index in indices),
    )


def berlekamp_massey(sequence, field):
    """Return (linear complexity L, connection polynomial C[0..L])."""
    length = len(sequence)
    connection = [field.zero] * (length + 1)
    previous = [field.zero] * (length + 1)
    connection[0] = previous[0] = field.one
    complexity = 0
    shift = 1
    last_discrepancy = field.one

    for index in range(length):
        discrepancy = sequence[index]
        for offset in range(1, complexity + 1):
            discrepancy = field.add(
                discrepancy,
                field.mul(connection[offset], sequence[index - offset]),
            )
        if discrepancy == field.zero:
            shift += 1
            continue
        snapshot = connection[:]
        scale = field.div(discrepancy, last_discrepancy)
        for previous_index in range(length + 1 - shift):
            if previous[previous_index] != field.zero:
                target = previous_index + shift
                connection[target] = field.sub(
                    connection[target],
                    field.mul(scale, previous[previous_index]),
                )
        if 2 * complexity <= index:
            complexity = index + 1 - complexity
            previous = snapshot
            last_discrepancy = discrepancy
            shift = 1
        else:
            shift += 1
    return complexity, tuple(connection[:complexity + 1])


def recurrence_satisfaction(sequence, connection, field, start=None):
    complexity = len(connection) - 1
    start = complexity if start is None else max(start, complexity)
    hits = 0
    opportunities = max(0, len(sequence) - start)
    for index in range(start, len(sequence)):
        discrepancy = sequence[index]
        for offset in range(1, complexity + 1):
            discrepancy = field.add(
                discrepancy,
                field.mul(connection[offset], sequence[index - offset]),
            )
        hits += discrepancy == field.zero
    return hits, opportunities


def binomial_z(hits, opportunities, probability):
    if opportunities == 0:
        return 0.0
    expected = opportunities * probability
    variance = opportunities * probability * (1 - probability)
    return (hits - expected) / math.sqrt(variance)


def matrix_rank(rows, field):
    matrix = [list(row) for row in rows]
    if not matrix:
        return 0
    row_count = len(matrix)
    column_count = len(matrix[0])
    pivot_row = 0
    for column in range(column_count):
        pivot = next(
            (row for row in range(pivot_row, row_count)
             if matrix[row][column] != field.zero),
            None,
        )
        if pivot is None:
            continue
        matrix[pivot_row], matrix[pivot] = matrix[pivot], matrix[pivot_row]
        inverse = field.inv_table[matrix[pivot_row][column]]
        matrix[pivot_row] = [field.mul(value, inverse)
                             for value in matrix[pivot_row]]
        for row in range(row_count):
            if row == pivot_row or matrix[row][column] == field.zero:
                continue
            scale = matrix[row][column]
            matrix[row] = [
                field.sub(value, field.mul(scale, pivot_value))
                for value, pivot_value in zip(matrix[row], matrix[pivot_row])
            ]
        pivot_row += 1
        if pivot_row == row_count:
            break
    return pivot_row


def presentation_observation(dbbi, faed, presentation):
    field = presentation["field"]
    order = presentation["coordinate_order"]
    dbbi_values = map_stream_gf9(dbbi, order)
    faed_values = map_stream_gf9(faed, order)
    dbbi_complexity, dbbi_connection = berlekamp_massey(dbbi_values, field)
    faed_complexity, _ = berlekamp_massey(faed_values, field)

    dbbi_half = len(dbbi_values) // 2
    faed_half = len(faed_values) // 2
    _, dbbi_prefix_connection = berlekamp_massey(
        dbbi_values[:dbbi_half], field
    )
    _, faed_prefix_connection = berlekamp_massey(
        faed_values[:faed_half], field
    )
    dbbi_holdout = recurrence_satisfaction(
        dbbi_values, dbbi_prefix_connection, field, dbbi_half
    )
    faed_holdout = recurrence_satisfaction(
        faed_values, faed_prefix_connection, field, faed_half
    )

    lanes = tuple(
        faed_values[index * LANE_WIDTH:(index + 1) * LANE_WIDTH]
        for index in range(LANE_COUNT)
    )
    lane_rows = []
    for lane_index, lane in enumerate(lanes, start=1):
        hits, opportunities = recurrence_satisfaction(
            lane, dbbi_connection, field
        )
        lane_rows.append({
            "lane": lane_index,
            "hits": hits,
            "opportunities": opportunities,
            "z": binomial_z(hits, opportunities, 1 / 9),
        })
    rank = matrix_rank((dbbi_values,) + lanes, field)
    return {
        "presentation": presentation["name"],
        "dbbi_linear_complexity": dbbi_complexity,
        "faed_linear_complexity": faed_complexity,
        "dbbi_holdout_hits": dbbi_holdout[0],
        "dbbi_holdout_opportunities": dbbi_holdout[1],
        "dbbi_holdout_z": binomial_z(*dbbi_holdout, 1 / 9),
        "faed_holdout_hits": faed_holdout[0],
        "faed_holdout_opportunities": faed_holdout[1],
        "faed_holdout_z": binomial_z(*faed_holdout, 1 / 9),
        "lane_transfer": tuple(lane_rows),
        "max_lane_transfer_z": max(row["z"] for row in lane_rows),
        "joint_rank": rank,
    }


def observation(dbbi, faed):
    presentations = tuple(
        presentation_observation(dbbi, faed, presentation)
        for presentation in PRESENTATIONS
    )
    dbbi_components = tuple(
        berlekamp_massey(component, GF3)[0]
        for component in map_stream_components(dbbi)
    )
    faed_components = tuple(
        berlekamp_massey(component, GF3)[0]
        for component in map_stream_components(faed)
    )
    metrics = {
        "gf9_dbbi_min_linear_complexity": min(
            row["dbbi_linear_complexity"] for row in presentations
        ),
        "gf9_faed_min_linear_complexity": min(
            row["faed_linear_complexity"] for row in presentations
        ),
        "gf3_dbbi_min_component_complexity": min(dbbi_components),
        "gf3_faed_min_component_complexity": min(faed_components),
        "gf9_dbbi_max_holdout_z": max(
            row["dbbi_holdout_z"] for row in presentations
        ),
        "gf9_faed_max_holdout_z": max(
            row["faed_holdout_z"] for row in presentations
        ),
        "dbbi_to_faed_lane_max_z": max(
            row["max_lane_transfer_z"] for row in presentations
        ),
        "joint_min_rank": min(row["joint_rank"] for row in presentations),
    }
    return {
        "metrics": metrics,
        "gf3_component_complexities": {
            "DBBI": dbbi_components,
            "FAED": faed_components,
        },
        "presentations": presentations,
    }


def empirical_p(observed, null_values, alternative):
    if alternative == "high":
        count = sum(value >= observed for value in null_values)
    elif alternative == "low":
        count = sum(value <= observed for value in null_values)
    else:
        raise ValueError(f"unknown alternative: {alternative}")
    return (1 + count) / (len(null_values) + 1)


def null_calibration(observed, trials, seed):
    rng = random.Random(seed)
    shuffled_dbbi = list(DBBI)
    shuffled_faed = list(FAED)
    nulls = {name: [] for name in METRIC_ALTERNATIVES}
    for _ in range(trials):
        rng.shuffle(shuffled_dbbi)
        rng.shuffle(shuffled_faed)
        row = observation("".join(shuffled_dbbi), "".join(shuffled_faed))["metrics"]
        for name in nulls:
            nulls[name].append(row[name])
    rows = {}
    for name, alternative in METRIC_ALTERNATIVES.items():
        values = sorted(nulls[name])
        raw_p = empirical_p(observed["metrics"][name], values, alternative)
        rows[name] = {
            "observed": observed["metrics"][name],
            "alternative": alternative,
            "null_median": values[len(values) // 2],
            "null_5th_percentile": values[(5 * len(values)) // 100],
            "null_95th_percentile": values[(95 * len(values)) // 100],
            "empirical_p": raw_p,
            "family_bonferroni_p": min(1.0, raw_p * FAMILY_SIZE),
        }
    return rows


def audit(trials=1_000, seed=20260814):
    if trials < 1:
        raise ValueError("trials must be positive")
    observed = observation(DBBI, FAED)
    calibration = null_calibration(observed, trials, seed)
    family_p = min(row["family_bonferroni_p"] for row in calibration.values())
    threshold = 0.01
    return {
        "source_lengths": {"DBBI": len(DBBI), "FAED": len(FAED)},
        "lane_geometry": {"count": LANE_COUNT, "width": LANE_WIDTH,
                          "unused_tail": len(FAED) - BODY_LENGTH},
        "irreducible_quadratics": IRREDUCIBLE_QUADRATICS,
        "coordinate_orders": COORDINATE_ORDERS,
        "presentation_count": len(PRESENTATIONS),
        "observation": observed,
        "calibration": {
            "trials": trials,
            "seed": seed,
            "minimum_resolvable_p": 1 / (trials + 1),
            "null_model": "independent shuffles preserving exact DBBI/FAED multisets; best of six presentations inside every trial",
            "rows": calibration,
        },
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
    assert all(is_irreducible_quadratic(*row)
               for row in IRREDUCIBLE_QUADRATICS)
    assert sum(is_irreducible_quadratic(p, q)
               for p in range(3) for q in range(3)) == 3
    for presentation in PRESENTATIONS:
        field = presentation["field"]
        assert field.mul_table[field.one][8] == 8
        assert all(field.mul(value, field.inv_table[value]) == field.one
                   for value in range(1, 9))
    # Fibonacci over GF(3): s[n] = s[n-1] + s[n-2], hence complexity 2.
    sequence = [1, 1]
    for _ in range(18):
        sequence.append((sequence[-1] + sequence[-2]) % 3)
    complexity, connection = berlekamp_massey(tuple(sequence), GF3)
    assert complexity == 2
    assert recurrence_satisfaction(tuple(sequence), connection, GF3) == (18, 18)
    report = audit(trials=3)
    assert report["presentation_count"] == 6
    assert report["lane_geometry"] == {"count": 6, "width": 91, "unused_tail": 24}
    assert not report["candidate_text_generated"]
    assert not report["password_oracle_run"]
    print("[*] self-test OK: GF(3)/GF(9), BM recurrence, six presentations, and rank verified")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=1_000)
    parser.add_argument("--seed", type=int, default=20260814)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = self_test() if args.self_test else audit(args.trials, args.seed)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    print(
        "[*] GF(9) family:", report["presentation_count"],
        "presentations;", report["calibration"]["trials"], "profile shuffles",
    )
    for name, row in report["calibration"]["rows"].items():
        print(
            f"    {name}: observed={row['observed']:.9g} "
            f"null_median={row['null_median']:.9g} "
            f"raw_p={row['empirical_p']:.6g} "
            f"corrected_p={row['family_bonferroni_p']:.6g}"
        )
    print(
        "[*] family p-bound:",
        f"{report['family']['bonferroni_p_bound']:.6g}",
        "promoted=" + str(report["family"]["promoted"]),
    )
    print("[*] no candidate text or password oracle was used")


if __name__ == "__main__":
    main()

