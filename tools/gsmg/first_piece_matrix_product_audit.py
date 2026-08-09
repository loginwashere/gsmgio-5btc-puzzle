#!/usr/bin/env python3
"""Audit Point 1's ``matrix @ sum-list -> [255,103]`` convergence.

The authenticated color prime 574061 is reconstructed elsewhere as the
row-major 2x3 decimal-digit matrix ``[[5,7,4],[0,6,1]]``.  Its total followed
by its row sums is the independently established list ``[23,16,7]``.  This
module verifies the proposed matrix-vector product and calibrates it under:

* all six orders of the fixed sum-list against the fixed matrix;
* four rectangle symmetries crossed with those six orders; and
* a deliberately broader control allowing arbitrary reassignment of the six
  distinct digits, quotiented by simultaneous column relabeling.

The audit does not try FF67 as a password, salt, key prefix, or blob oracle.
Those are additional semantics not selected by the matrixsumlist instruction.
"""

import argparse
from fractions import Fraction
from itertools import permutations
from math import factorial

from first_piece_color_reconstruction import TARGET
from prime_matrixsum_reconstruction import (
    EXPECTED_PRIME,
    EXPECTED_SUM_LIST,
    matrixsumlist,
)


def multiply(matrix, vector):
    if not matrix or any(len(row) != len(vector) for row in matrix):
        raise ValueError("matrix width and vector length must agree")
    return tuple(
        sum(value * coefficient for value, coefficient in zip(row, vector))
        for row in matrix
    )


def horizontal_flip(matrix):
    return tuple(tuple(reversed(row)) for row in matrix)


def vertical_flip(matrix):
    return tuple(reversed(matrix))


def rectangle_orientations(matrix):
    matrix = tuple(tuple(row) for row in matrix)
    return (
        ("identity", matrix),
        ("horizontal_flip", horizontal_flip(matrix)),
        ("vertical_flip", vertical_flip(matrix)),
        ("rotate_180", vertical_flip(horizontal_flip(matrix))),
    )


def is_ascii_letter(value):
    return 65 <= value <= 90 or 97 <= value <= 122


def output_properties(output):
    other_values = tuple(value for value in output if value != 255)
    return {
        "exact_255_103": output == (255, 103),
        "either_order_255_103": tuple(sorted(output)) == (103, 255),
        "contains_255": 255 in output,
        "contains_103": 103 in output,
        "ff_plus_printable": (
            255 in output and any(32 <= value <= 126 for value in other_values)
        ),
        "ff_plus_ascii_letter": (
            255 in output and any(is_ascii_letter(value) for value in other_values)
        ),
        "both_unsigned_bytes": all(0 <= value <= 255 for value in output),
        "both_printable_ascii": all(32 <= value <= 126 for value in output),
    }


def count_properties(rows):
    keys = output_properties((255, 103))
    return {
        key: sum(output_properties(row["output"])[key] for row in rows)
        for key in keys
    }


def audit():
    matrix_list, sum_list = matrixsumlist(EXPECTED_PRIME)
    matrix = tuple(tuple(row) for row in matrix_list)
    vector = tuple(sum_list)
    fixed_output = multiply(matrix, vector)

    fixed_matrix_rows = tuple(
        {
            "vector": ordered_vector,
            "output": multiply(matrix, ordered_vector),
        }
        for ordered_vector in permutations(vector)
    )

    geometric_rows = tuple(
        {
            "orientation": orientation,
            "matrix": oriented_matrix,
            "vector": ordered_vector,
            "output": multiply(oriented_matrix, ordered_vector),
        }
        for orientation, oriented_matrix in rectangle_orientations(matrix)
        for ordered_vector in permutations(vector)
    )
    geometric_ordered_outputs = tuple(sorted({row["output"] for row in geometric_rows}))
    geometric_unordered_outputs = tuple(
        sorted({tuple(sorted(row["output"])) for row in geometric_rows})
    )

    digits = tuple(int(character) for character in str(EXPECTED_PRIME))
    expanded_rows = tuple(
        {
            "digits": ordered_digits,
            "vector": ordered_vector,
            "output": multiply(
                (ordered_digits[:3], ordered_digits[3:]), ordered_vector
            ),
        }
        for ordered_digits in permutations(digits)
        for ordered_vector in permutations(vector)
    )
    expanded_raw_counts = count_properties(expanded_rows)
    simultaneous_column_relabelings = factorial(3)
    assert all(
        count % simultaneous_column_relabelings == 0
        for count in expanded_raw_counts.values()
    )
    expanded_class_counts = {
        key: count // simultaneous_column_relabelings
        for key, count in expanded_raw_counts.items()
    }
    expanded_class_size = len(expanded_rows) // simultaneous_column_relabelings

    return {
        "source": {
            "prime": EXPECTED_PRIME,
            "digits": digits,
            "matrix": matrix,
            "sum_list": vector,
            "sum_list_definition": ("total", "row_1_sum", "row_2_sum"),
            "target_first_character": TARGET[0],
            "target_first_character_ascii": ord(TARGET[0]),
        },
        "fixed_operation": {
            "output": fixed_output,
            "first_as_hex_byte": f"{fixed_output[0]:02X}",
            "second_as_ascii": chr(fixed_output[1]),
            "serialized_hex_if_bytes": bytes(fixed_output).hex().upper(),
            "properties": output_properties(fixed_output),
        },
        "fixed_matrix_vector_permutations": {
            "rows": fixed_matrix_rows,
            "family_size": len(fixed_matrix_rows),
            "property_counts": count_properties(fixed_matrix_rows),
        },
        "geometric_family": {
            "rows": geometric_rows,
            "raw_family_size": len(geometric_rows),
            "raw_property_counts": count_properties(geometric_rows),
            "distinct_ordered_outputs": geometric_ordered_outputs,
            "distinct_ordered_output_count": len(geometric_ordered_outputs),
            "distinct_unordered_outputs": geometric_unordered_outputs,
            "distinct_unordered_output_count": len(geometric_unordered_outputs),
            "target_unordered_output_rank_size": Fraction(
                int((103, 255) in geometric_unordered_outputs),
                len(geometric_unordered_outputs),
            ),
            "symmetry_note": (
                "simultaneously reversing matrix columns and vector order "
                "preserves the dot products; reversing rows only swaps outputs"
            ),
        },
        "expanded_digit_assignment_control": {
            "raw_family_size": len(expanded_rows),
            "simultaneous_column_relabelings_per_class": simultaneous_column_relabelings,
            "operation_class_count": expanded_class_size,
            "raw_property_counts": expanded_raw_counts,
            "operation_class_property_counts": expanded_class_counts,
            "exact_ordered_rate": Fraction(
                expanded_class_counts["exact_255_103"], expanded_class_size
            ),
            "either_order_rate": Fraction(
                expanded_class_counts["either_order_255_103"], expanded_class_size
            ),
            "ff_plus_letter_rate": Fraction(
                expanded_class_counts["ff_plus_ascii_letter"], expanded_class_size
            ),
            "primary_null": False,
        },
        "assumption_ledger": (
            "reuse matrixsumlist's output as a new column vector",
            "choose multiplication rather than the instructed sum operation",
            "align total,row1,row2 with matrix columns despite unlike dimensions",
            "interpret 255 as hexadecimal FF / white rather than decimal data",
            "interpret 103 as ASCII rather than another number",
            "serialize the pair as bytes in big listed order to obtain FF67",
        ),
        "oracle_run": False,
    }


def self_test():
    report = audit()
    source = report["source"]
    fixed = report["fixed_operation"]
    permutations_report = report["fixed_matrix_vector_permutations"]
    geometry = report["geometric_family"]
    expanded = report["expanded_digit_assignment_control"]

    assert source["matrix"] == ((5, 7, 4), (0, 6, 1))
    assert source["sum_list"] == (23, 16, 7)
    assert fixed["output"] == (255, 103)
    assert fixed["first_as_hex_byte"] == "FF"
    assert fixed["second_as_ascii"] == "g"
    assert fixed["serialized_hex_if_bytes"] == "FF67"
    assert permutations_report["family_size"] == 6
    assert permutations_report["property_counts"]["exact_255_103"] == 1
    assert permutations_report["property_counts"]["ff_plus_ascii_letter"] == 1
    assert permutations_report["property_counts"]["both_unsigned_bytes"] == 4
    assert geometry["raw_family_size"] == 24
    assert geometry["raw_property_counts"]["exact_255_103"] == 2
    assert geometry["raw_property_counts"]["either_order_255_103"] == 4
    assert geometry["distinct_ordered_output_count"] == 12
    assert geometry["distinct_unordered_output_count"] == 6
    assert geometry["target_unordered_output_rank_size"] == Fraction(1, 6)
    assert expanded["raw_family_size"] == 4320
    assert expanded["operation_class_count"] == 720
    assert expanded["operation_class_property_counts"]["exact_255_103"] == 1
    assert expanded["operation_class_property_counts"]["either_order_255_103"] == 2
    assert expanded["operation_class_property_counts"]["ff_plus_ascii_letter"] == 6
    assert expanded["exact_ordered_rate"] == Fraction(1, 720)
    assert expanded["either_order_rate"] == Fraction(1, 360)
    assert expanded["ff_plus_letter_rate"] == Fraction(1, 120)
    assert expanded["primary_null"] is False
    assert report["oracle_run"] is False
    print("[*] self-test OK: [255,103] product and bounded calibration reproduce")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    report = audit()
    fixed = report["fixed_operation"]
    permuted = report["fixed_matrix_vector_permutations"]
    geometry = report["geometric_family"]
    expanded = report["expanded_digit_assignment_control"]

    print(
        f"[*] fixed product: {report['source']['matrix']} @ "
        f"{report['source']['sum_list']} = {fixed['output']} -> "
        f"{fixed['first_as_hex_byte']} / {fixed['second_as_ascii']!r}"
    )
    print(
        "[*] fixed matrix, six vector orders: "
        f"{permuted['property_counts']}"
    )
    print(
        "[*] rectangle symmetries x vector orders: "
        f"raw={geometry['raw_family_size']}, "
        f"ordered outputs={geometry['distinct_ordered_output_count']}, "
        f"unordered outputs={geometry['distinct_unordered_output_count']}"
    )
    print(
        "[*] expanded descriptive control after column-relabel quotient: "
        f"exact={expanded['exact_ordered_rate']}, "
        f"either-order={expanded['either_order_rate']}, "
        f"FF+letter={expanded['ff_plus_letter_rate']}"
    )
    print(f"[*] assumption count before FF67 semantics: {len(report['assumption_ledger'])}")
    print(
        "[*] verdict: the arithmetic is exact and uses two authenticated "
        "objects, but the second multiplication and mixed FF/ASCII decoding "
        "are not selected; no blob oracle follows."
    )
    if args.self_test:
        self_test()


if __name__ == "__main__":
    main()
