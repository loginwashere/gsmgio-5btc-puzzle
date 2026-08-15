#!/usr/bin/env python3
"""Continued-fraction audit against a closed authenticated-number registry."""

import argparse
import hashlib
import json
from decimal import Decimal, localcontext
from fractions import Fraction

from data import DBBI, FAED


SOURCES = {"dbbi": DBBI, "faed": FAED}
INTEGER_TARGETS = {
    "architect_7": 7,
    "architect_16": 16,
    "architect_23": 23,
    "colored_cells_24": 24,
    "prime_walk_chars_31": 31,
    "dbbi_length_91": 91,
    "historical_remaining_140": 140,
    "validation_num_length_149": 149,
    "stage0_cells_196": 196,
    "faed_length_570": 570,
    "salphaseion_raw_chars_2149": 2149,
    "phase3_digits_11110": 11110,
    "stage0_prime_574061": 574061,
}
RATIO_TARGETS = {
    "architect_23_over_16": Fraction(23, 16),
    "architect_16_over_7": Fraction(16, 7),
    "architect_23_over_7": Fraction(23, 7),
    "stream_lengths_91_over_570": Fraction(91, 570),
}
TARGETS = {
    **{name: Fraction(value, 1) for name, value in INTEGER_TARGETS.items()},
    **RATIO_TARGETS,
}
NEAR_THRESHOLD = Fraction(1, 10**12)


def digit_maps():
    direct = tuple(range(1, 10))
    transpose = tuple((index % 3) * 3 + index // 3 + 1 for index in range(9))
    mirror = tuple(reversed(direct))
    return {
        "direct_1_to_9": direct,
        "transpose_3x3_plus_1": transpose,
        "mirror9_positive": mirror,
    }


MAPS = digit_maps()


def partial_quotients(stream, mapping):
    return tuple(mapping[ord(symbol) - ord("a")] for symbol in stream)


def convergent(quotients):
    p_minus_2, p_minus_1 = 0, 1
    q_minus_2, q_minus_1 = 1, 0
    for quotient in quotients:
        if quotient <= 0:
            raise ValueError("continued-fraction quotients must be positive")
        numerator = quotient * p_minus_1 + p_minus_2
        denominator = quotient * q_minus_1 + q_minus_2
        p_minus_2, p_minus_1 = p_minus_1, numerator
        q_minus_2, q_minus_1 = q_minus_1, denominator
    return Fraction(p_minus_1, q_minus_1)


def decimal_prefix(value, digits=30):
    with localcontext() as context:
        context.prec = digits + 8
        decimal = Decimal(value.numerator) / Decimal(value.denominator)
        return format(decimal, f".{digits}f")


def digest_integer(value):
    return hashlib.sha256(str(value).encode("ascii")).hexdigest()


def compare(value):
    deltas = {name: abs(value - target) for name, target in TARGETS.items()}
    exact = tuple(sorted(name for name, delta in deltas.items() if delta == 0))
    near = tuple(sorted(
        name for name, delta in deltas.items()
        if 0 < delta <= NEAR_THRESHOLD
    ))
    nearest_name = min(deltas, key=lambda name: deltas[name])
    nearest_delta = deltas[nearest_name]
    integer_values = set(INTEGER_TARGETS.values())
    return {
        "exact_value_hits": exact,
        "near_value_hits": near,
        "nearest_target": nearest_name,
        "nearest_delta_numerator": nearest_delta.numerator,
        "nearest_delta_denominator": nearest_delta.denominator,
        "nearest_delta_decimal": decimal_prefix(nearest_delta, 18),
        "numerator_constant_hits": tuple(sorted(
            name for name, target in INTEGER_TARGETS.items()
            if value.numerator == target
        )),
        "denominator_constant_hits": tuple(sorted(
            name for name, target in INTEGER_TARGETS.items()
            if value.denominator == target
        )),
        "numerator_is_registered_integer": value.numerator in integer_values,
        "denominator_is_registered_integer": value.denominator in integer_values,
    }


def audit():
    rows = []
    for source_name, stream in SOURCES.items():
        for map_name, mapping in MAPS.items():
            quotients = partial_quotients(stream, mapping)
            value = convergent(quotients)
            row = {
                "source": source_name,
                "map": map_name,
                "mapping": mapping,
                "quotient_count": len(quotients),
                "integer_part": value.numerator // value.denominator,
                "decimal_prefix": decimal_prefix(value),
                "numerator_digits": len(str(value.numerator)),
                "denominator_digits": len(str(value.denominator)),
                "numerator_sha256": digest_integer(value.numerator),
                "denominator_sha256": digest_integer(value.denominator),
                **compare(value),
            }
            rows.append(row)
    exact_hits = tuple(
        (row["source"], row["map"], row["exact_value_hits"])
        for row in rows if row["exact_value_hits"]
    )
    near_hits = tuple(
        (row["source"], row["map"], row["near_value_hits"])
        for row in rows if row["near_value_hits"]
    )
    component_hits = tuple(
        (row["source"], row["map"],
         row["numerator_constant_hits"], row["denominator_constant_hits"])
        for row in rows
        if row["numerator_constant_hits"] or row["denominator_constant_hits"]
    )
    return {
        "maps": MAPS,
        "target_registry": {
            "integers": INTEGER_TARGETS,
            "ratios": {
                name: f"{value.numerator}/{value.denominator}"
                for name, value in RATIO_TARGETS.items()
            },
            "count": len(TARGETS),
            "near_threshold": "1e-12 absolute",
        },
        "rows": tuple(rows),
        "exact_value_hits": exact_hits,
        "near_value_hits": near_hits,
        "numerator_or_denominator_hits": component_hits,
        "promotion": bool(exact_hits or near_hits or component_hits),
        "decimal_substring_search_run": False,
        "candidate_text_generated": False,
        "password_oracle_run": False,
    }


def self_test():
    assert MAPS["direct_1_to_9"] == (1, 2, 3, 4, 5, 6, 7, 8, 9)
    assert MAPS["transpose_3x3_plus_1"] == (1, 4, 7, 2, 5, 8, 3, 6, 9)
    assert MAPS["mirror9_positive"] == (9, 8, 7, 6, 5, 4, 3, 2, 1)
    assert convergent((1, 2)) == Fraction(3, 2)
    assert convergent((3, 7, 16)) == Fraction(355, 113)
    synthetic = compare(Fraction(23, 16))
    assert synthetic["exact_value_hits"] == ("architect_23_over_16",)
    report = audit()
    assert len(report["rows"]) == 6
    assert report["target_registry"]["count"] == 17
    assert not report["decimal_substring_search_run"]
    assert not report["candidate_text_generated"]
    print("[*] self-test OK: three maps, convergents, and closed registry verified")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = self_test() if args.self_test else audit()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    print("[*] target registry:", report["target_registry"])
    for row in report["rows"]:
        print(
            f"[*] {row['source']}/{row['map']}: value={row['decimal_prefix']} "
            f"digits={row['numerator_digits']}/{row['denominator_digits']} "
            f"nearest={row['nearest_target']} "
            f"delta={row['nearest_delta_decimal']}"
        )
    print("[*] exact value hits:", report["exact_value_hits"])
    print("[*] near value hits:", report["near_value_hits"])
    print("[*] numerator/denominator hits:", report["numerator_or_denominator_hits"])
    print("[*] no substring, candidate-text, or password search was used")


if __name__ == "__main__":
    main()
