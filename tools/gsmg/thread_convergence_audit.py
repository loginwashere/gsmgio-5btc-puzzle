#!/usr/bin/env python3
"""Audit bounded intersections between the color-prime and FEFE clue chains."""

import math
import itertools

from first_piece_color_reconstruction import (
    DEFAULT_IMAGE,
    reconstruct,
    spiral_top_left_counterclockwise,
)
from prime_matrixsum_reconstruction import matrixsumlist

EXPECTED_PRIME = 574061
EXPECTED_MATRIX = [[5, 7, 4], [0, 6, 1]]
EXPECTED_SUM_LIST = (23, 16, 7)
GRID_SIZE = 14
COLORED_BOUNDARY_COUNT = 24
RAILS = ("but", "hye", "hey", "eol")
FROZEN_ARITHMETIC_TARGETS = {
    2,  # B in A1Z26; matrix height
    3,  # matrix width
    4,  # FEFE bit ordinal; matrix digit
    5,  # E in A1Z26; matrix digit
    6,  # matrix size/digit
    7,  # matrix digit and sum-list value
    8,  # H in A1Z26
    16,
    21,
    23,
}


def directed_matrix_adjacencies(matrix):
    pairs = set()
    rows = len(matrix)
    columns = len(matrix[0])
    for row in range(rows):
        for column in range(columns):
            if column + 1 < columns:
                left = matrix[row][column]
                right = matrix[row][column + 1]
                pairs.add((left, right))
                pairs.add((right, left))
            if row + 1 < rows:
                top = matrix[row][column]
                bottom = matrix[row + 1][column]
                pairs.add((top, bottom))
                pairs.add((bottom, top))
    return pairs


def concatenation_family(sum_list, matrix):
    dimensions = {len(matrix), len(matrix[0]), len(matrix) * len(matrix[0])}
    values = set()
    labels = {}
    for value in sum_list:
        for dimension in dimensions:
            for left, right in ((value, dimension), (dimension, value)):
                combined = int(f"{left}{right}")
                if combined < GRID_SIZE * GRID_SIZE:
                    values.add(combined)
                    labels.setdefault(combined, []).append(f"{left}||{right}")
    return values, labels


def cell_null(result, coordinate_family, index_family):
    colored_coordinates = {
        (item["row_0"], item["column_0"])
        for item in result["objects"]
    }
    eligible = []
    for spiral_index, (row, column) in enumerate(
        spiral_top_left_counterclockwise()
    ):
        if (row, column) not in colored_coordinates:
            eligible.append((spiral_index, row, column))

    if len(eligible) != GRID_SIZE * GRID_SIZE - COLORED_BOUNDARY_COUNT:
        raise AssertionError(f"unexpected null profile size: {len(eligible)}")

    coordinate_hits = [
        item for item in eligible if (item[1], item[2]) in coordinate_family
    ]
    index_hits = [item for item in eligible if item[0] in index_family]
    joint_hits = [
        item
        for item in eligible
        if (item[1], item[2]) in coordinate_family and item[0] in index_family
    ]
    return {
        "eligible": eligible,
        "coordinate": coordinate_hits,
        "index": index_hits,
        "joint": joint_hits,
    }


def direct_rail_selectors():
    selectors = (1, 4, 21, 163)
    return {
        rail: {
            selector: rail[selector - 1]
            for selector in selectors
            if 1 <= selector <= len(rail)
        }
        for rail in RAILS
    }


def arithmetic_relations(value, sum_list):
    results = {}
    for item in sum_list:
        results[f"{value}-{item}"] = value - item
        results[f"{value}%{item}"] = value % item
        results[f"gcd({value},{item})"] = math.gcd(value, item)
    results[f"digit_sum({value})"] = sum(int(digit) for digit in str(value))
    results[f"{value}%sum{sum_list}"] = value % sum(sum_list)
    return results


def arithmetic_hits(value, sum_list):
    return {
        label: result
        for label, result in arithmetic_relations(value, sum_list).items()
        if result in FROZEN_ARITHMETIC_TARGETS
    }


def row_list_addresses(matrix):
    spiral_coordinates = spiral_top_left_counterclockwise()
    coordinate_to_index = {
        coordinate: index
        for index, coordinate in enumerate(spiral_coordinates)
    }
    addresses = []
    for row_index, row in enumerate(matrix):
        coordinate = tuple(row[-2:])
        derived_index = int(f"{sum(row)}{len(row)}")
        actual_index = coordinate_to_index[coordinate]
        addresses.append(
            {
                "row": row_index,
                "list": tuple(row),
                "coordinate": coordinate,
                "derived_index": derived_index,
                "actual_index": actual_index,
                "self_consistent": derived_index == actual_index,
            }
        )
    return addresses


def row_list_address_family(matrix):
    coordinate_to_index = {
        coordinate: index
        for index, coordinate in enumerate(spiral_top_left_counterclockwise())
    }
    addresses = []
    for row_index, row in enumerate(matrix):
        for slice_name, pair in (("head", row[:2]), ("tail", row[-2:])):
            for coordinate_order, coordinate in (
                ("forward", tuple(pair)),
                ("reverse", tuple(reversed(pair))),
            ):
                for concat_order, derived_index in (
                    ("sum_len", int(f"{sum(row)}{len(row)}")),
                    ("len_sum", int(f"{len(row)}{sum(row)}")),
                ):
                    addresses.append(
                        {
                            "row": row_index,
                            "slice": slice_name,
                            "coordinate_order": coordinate_order,
                            "concat_order": concat_order,
                            "coordinate": coordinate,
                            "derived_index": derived_index,
                            "actual_index": coordinate_to_index[coordinate],
                            "self_consistent": (
                                derived_index == coordinate_to_index[coordinate]
                            ),
                        }
                    )
    return addresses


def row_list_permutation_null(matrix, fefe):
    digits = tuple(value for row in matrix for value in row)
    total = 0
    self_consistent = 0
    fefe_hits = 0
    for permutation in itertools.permutations(digits):
        candidate = [list(permutation[:3]), list(permutation[3:])]
        addresses = row_list_addresses(candidate)
        total += 1
        self_consistent += any(item["self_consistent"] for item in addresses)
        fefe_hits += any(
            item["self_consistent"]
            and item["coordinate"] == (fefe["row_1"] - 1, fefe["column_1"] - 1)
            and item["derived_index"] == fefe["spiral_0"]
            for item in addresses
        )
    return total, self_consistent, fefe_hits


def row_list_family_permutation_null(matrix, fefe):
    digits = tuple(value for row in matrix for value in row)
    total = 0
    self_consistent = 0
    fefe_hits = 0
    for permutation in itertools.permutations(digits):
        candidate = [list(permutation[:3]), list(permutation[3:])]
        addresses = row_list_address_family(candidate)
        total += 1
        self_consistent += any(item["self_consistent"] for item in addresses)
        fefe_hits += any(
            item["self_consistent"]
            and item["coordinate"] == (fefe["row_1"] - 1, fefe["column_1"] - 1)
            and item["derived_index"] == fefe["spiral_0"]
            for item in addresses
        )
    return total, self_consistent, fefe_hits


def main():
    result = reconstruct(DEFAULT_IMAGE)
    matrix, sum_list = matrixsumlist(EXPECTED_PRIME)
    if matrix != EXPECTED_MATRIX or sum_list != EXPECTED_SUM_LIST:
        raise AssertionError("unexpected prime matrix checkpoint")

    fefe = result["fefe"]
    byte_bits = f"{ord(fefe['character']):08b}"
    color_object = result["objects"][fefe["character_0"]]
    if color_object["ordinal_1"] != 21 or color_object["color"] != "yellow":
        raise AssertionError("FEFE byte does not end at the expected yellow marker")
    if byte_bits[fefe["bit_0"]] != "0" or byte_bits[7] != "0":
        raise AssertionError("FEFE and yellow marker bits are not both zero")

    print("same-byte convergence:")
    print(
        f"  character={fefe['character']!r}",
        f"ordinal={fefe['character_1']}",
        f"bits={byte_bits}",
    )
    print(
        f"  FEFE bit={fefe['bit_1']} value={byte_bits[fefe['bit_0']]}",
        f"LSB color={color_object['color']} value={byte_bits[7]}",
    )
    yellow_count = sum(
        item["color"] == "yellow" for item in result["objects"]
    )
    print(
        "  yellow-byte overlap:",
        f"{yellow_count}/{len(result['objects'])} = "
        f"{yellow_count / len(result['objects']):.6f}",
    )

    coordinate_family = directed_matrix_adjacencies(matrix)
    real_coordinate = (fefe["row_1"] - 1, fefe["column_1"] - 1)
    if real_coordinate != (7, 4) or real_coordinate not in coordinate_family:
        raise AssertionError("FEFE coordinate does not match matrix adjacency family")

    index_family, index_labels = concatenation_family(sum_list, matrix)
    if fefe["spiral_0"] != 163 or 163 not in index_family:
        raise AssertionError("FEFE index does not match concatenation family")

    print("bounded structural intersections:")
    print(
        f"  FEFE coordinate0={real_coordinate}",
        f"matrix-directed-adjacency-match={real_coordinate in coordinate_family}",
    )
    print(
        f"  FEFE spiral0={fefe['spiral_0']}",
        f"sum-list/dimension forms={index_labels[fefe['spiral_0']]}",
    )

    null = cell_null(result, coordinate_family, index_family)
    denominator = len(null["eligible"])
    expected_counts = {"coordinate": 12, "index": 9, "joint": 1}
    print("exact profile-preserving cell null:")
    for label in ("coordinate", "index", "joint"):
        count = len(null[label])
        if count != expected_counts[label]:
            raise AssertionError(f"unexpected {label} null count: {count}")
        print(f"  {label}: {count}/{denominator} = {count / denominator:.6f}")
    print("  joint cells:", null["joint"])

    real_arithmetic_hits = arithmetic_hits(fefe["spiral_0"], sum_list)
    real_score = len(real_arithmetic_hits)
    arithmetic_null = [
        item
        for item in null["eligible"]
        if len(arithmetic_hits(item[0], sum_list)) >= real_score
    ]
    print("closed arithmetic family:")
    print("  targets:", sorted(FROZEN_ARITHMETIC_TARGETS))
    print("  real hits:", real_arithmetic_hits)
    print(
        "  exact max-family null:",
        f"{len(arithmetic_null)}/{denominator} = "
        f"{len(arithmetic_null) / denominator:.6f}",
    )

    print(
        "matrix-to-byte operation:",
        "not run (no unique creator-grounded 6-digit-to-8-bit mapping)",
    )

    addresses = row_list_addresses(matrix)
    expected_addresses = [
        {
            "row": 0,
            "list": (5, 7, 4),
            "coordinate": (7, 4),
            "derived_index": 163,
            "actual_index": 163,
            "self_consistent": True,
        },
        {
            "row": 1,
            "list": (0, 6, 1),
            "coordinate": (6, 1),
            "derived_index": 73,
            "actual_index": 57,
            "self_consistent": False,
        },
    ]
    if addresses != expected_addresses:
        raise AssertionError(f"unexpected row-list addresses: {addresses}")
    print("creator-supported row-list address grammar:")
    for address in addresses:
        print(
            f"  row={address['list']}",
            f"tail_coordinate0={address['coordinate']}",
            f"sum||len={address['derived_index']}",
            f"actual_spiral0={address['actual_index']}",
            f"match={address['self_consistent']}",
        )
    total, self_consistent, fefe_hits = row_list_permutation_null(matrix, fefe)
    if (total, fefe_hits) != (720, 12):
        raise AssertionError(
            f"unexpected row-list permutation null: "
            f"{total}/{self_consistent}/{fefe_hits}"
        )
    print(
        "  exact digit-permutation null:",
        f"any_self_consistent={self_consistent}/{total} "
        f"({self_consistent / total:.6f})",
        f"FEFE_hit={fefe_hits}/{total} ({fefe_hits / total:.6f})",
    )
    family = [
        item
        for item in row_list_address_family(matrix)
        if item["self_consistent"]
    ]
    if family != [
        {
            "row": 0,
            "slice": "tail",
            "coordinate_order": "forward",
            "concat_order": "sum_len",
            "coordinate": (7, 4),
            "derived_index": 163,
            "actual_index": 163,
            "self_consistent": True,
        }
    ]:
        raise AssertionError(f"unexpected real row-list family matches: {family}")
    family_total, family_self_consistent, family_fefe_hits = (
        row_list_family_permutation_null(matrix, fefe)
    )
    print(
        "  eight-variant family-wise null:",
        f"any_self_consistent={family_self_consistent}/{family_total} "
        f"({family_self_consistent / family_total:.6f})",
        f"FEFE_hit={family_fefe_hits}/{family_total} "
        f"({family_fefe_hits / family_total:.6f})",
    )

    rail_results = direct_rail_selectors()
    print("direct selectors on three-character rails:")
    for rail, selected in rail_results.items():
        print(f"  {rail}: {selected}")
    if any(set(selected) - {1} for selected in rail_results.values()):
        raise AssertionError("an unsupported selector unexpectedly fit a rail")

    print("verdict: exact convergence found; no unique downstream operation")


if __name__ == "__main__":
    main()
