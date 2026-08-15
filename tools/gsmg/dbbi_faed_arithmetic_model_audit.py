#!/usr/bin/env python3
"""Exact-rational arithmetic-coding feasibility audit for DBBI -> FAED.

DBBI supplies either a static nine-symbol histogram or a first-order Markov
table (histogram for the first symbol, directed transition counts thereafter).
FAED is interpreted as one base-9 fraction in [0,1).  Because the source gives
neither EOS nor decoded length, only the two source-grounded lengths 91 and 570
are declared.

Each decode is re-encoded as the shortest lexicographically first base-9
cylinder wholly contained in its final arithmetic interval.  This canonical
codeword provides a mechanical exact-round-trip test.  Merely finding that the
original code point lies in the interval is tautological and is not a hit.
"""

import argparse
import json
import math
from collections import Counter
from fractions import Fraction

from data import DBBI, FAED


ALPHABET = "abcdefghi"
MODELS = ("static_histogram", "first_order_markov")
OUTPUT_LENGTHS = (len(DBBI), len(FAED))


def base9_fraction(stream):
    numerator = 0
    for symbol in stream:
        digit = ord(symbol) - ord("a")
        if not 0 <= digit < 9:
            raise ValueError(f"symbol outside a-i: {symbol!r}")
        numerator = numerator * 9 + digit
    return Fraction(numerator, 9 ** len(stream))


def static_counts(stream):
    counts = Counter(stream)
    return tuple(counts[symbol] for symbol in ALPHABET)


def transition_counts(stream):
    rows = [[0] * 9 for _ in range(9)]
    for left, right in zip(stream, stream[1:]):
        rows[ord(left) - 97][ord(right) - 97] += 1
    return tuple(tuple(row) for row in rows)


def select_symbol(relative, counts):
    total = sum(counts)
    if total <= 0:
        raise ValueError("probability row has zero total")
    cumulative = 0
    for index, count in enumerate(counts):
        if count == 0:
            continue
        upper = Fraction(cumulative + count, total)
        if relative < upper:
            return index, cumulative, count, total
        cumulative += count
    raise AssertionError("relative arithmetic code point escaped [0,1)")


def arithmetic_decode(code, length, model, histogram, transitions):
    if not 0 <= code < 1:
        raise ValueError("arithmetic code must lie in [0,1)")
    low = Fraction(0)
    high = Fraction(1)
    output = []
    for position in range(length):
        counts = histogram if position == 0 or model == "static_histogram" else (
            transitions[output[-1]]
        )
        width = high - low
        relative = (code - low) / width
        symbol, cumulative, count, total = select_symbol(relative, counts)
        old_low = low
        low = old_low + width * Fraction(cumulative, total)
        high = old_low + width * Fraction(cumulative + count, total)
        output.append(symbol)
    return tuple(output), (low, high)


def ceil_fraction(value):
    return -(-value.numerator // value.denominator)


def integer_to_base9(value, width):
    digits = [0] * width
    for index in range(width - 1, -1, -1):
        value, digit = divmod(value, 9)
        digits[index] = digit
    if value:
        raise ValueError("integer does not fit declared base-9 width")
    return "".join(chr(97 + digit) for digit in digits)


def canonical_codeword(interval, maximum_digits=5000):
    """Shortest, then lexicographically first, base-9 cylinder inside interval."""
    low, high = interval
    scale = 1
    for width in range(1, maximum_digits + 1):
        scale *= 9
        first_cell = ceil_fraction(low * scale)
        if first_cell < scale and Fraction(first_cell + 1, scale) <= high:
            return integer_to_base9(first_cell, width)
    raise RuntimeError("canonical base-9 codeword exceeded search bound")


def interval_information_bits(interval):
    width = interval[1] - interval[0]
    return math.log2(width.denominator) - math.log2(width.numerator)


def row_for(model, output_length, code, histogram, transitions):
    decoded, interval = arithmetic_decode(
        code, output_length, model, histogram, transitions
    )
    decoded_text = "".join(chr(97 + value) for value in decoded)
    canonical = canonical_codeword(interval)
    expected = DBBI if output_length == len(DBBI) else FAED
    return {
        "model": model,
        "output_length": output_length,
        "decoded_text": decoded_text,
        "decoded_prefix": decoded_text[:120],
        "decoded_equals_same_length_source": decoded_text == expected,
        "input_codepoint_inside_final_interval": interval[0] <= code < interval[1],
        "final_interval_information_bits": interval_information_bits(interval),
        "canonical_codeword": canonical,
        "canonical_codeword_length": len(canonical),
        "canonical_codeword_prefix": canonical[:120],
        "canonical_equals_faed": canonical == FAED,
        "canonical_is_faed_prefix": FAED.startswith(canonical),
        "faed_is_canonical_prefix": canonical.startswith(FAED),
        "termination_supplied_by_source": False,
        "exact_self_describing_roundtrip": False,
    }


def audit():
    histogram = static_counts(DBBI)
    transitions = transition_counts(DBBI)
    if any(sum(row) == 0 for row in transitions):
        raise AssertionError("DBBI transition model contains an unusable empty row")
    code = base9_fraction(FAED)
    rows = tuple(
        row_for(model, length, code, histogram, transitions)
        for model in MODELS
        for length in OUTPUT_LENGTHS
    )
    exact_canonical_hits = tuple(
        (row["model"], row["output_length"])
        for row in rows if row["canonical_equals_faed"]
    )
    source_plaintext_hits = tuple(
        (row["model"], row["output_length"])
        for row in rows if row["decoded_equals_same_length_source"]
    )
    return {
        "prior_repository_coverage": {
            "dbbi_probability_model_faed_arithmetic_decode_before_this": 0,
        },
        "source_lengths": {"DBBI": len(DBBI), "FAED": len(FAED)},
        "input_interpretation": "FAED as exact forward base-9 fraction 0.<digits>",
        "models": MODELS,
        "output_lengths": OUTPUT_LENGTHS,
        "declaration_count": len(rows),
        "dbbi_histogram": histogram,
        "dbbi_transition_row_sums": tuple(map(sum, transitions)),
        "missing_required_source_fields": {
            "termination_or_eos": True,
            "decoded_output_length": True,
            "arithmetic_coder_normalization_and_emission_convention": True,
        },
        "canonical_convention": "shortest then lexicographically first base-9 cylinder wholly inside final interval",
        "rows": rows,
        "exact_canonical_hits": exact_canonical_hits,
        "source_plaintext_hits": source_plaintext_hits,
        "promotion": {
            "required": "source termination plus exact canonical FAED roundtrip or authenticated decoded target",
            "promoted": False,
        },
        "candidate_text_generated": False,
        "password_oracle_run": False,
    }


def self_test():
    histogram = (1, 1) + (0,) * 7
    transitions = tuple((1, 1) + (0,) * 7 for _ in range(9))
    plaintext = (0, 1, 0, 1)
    # Build the exact interval by decoding any known interior point selected
    # from a direct encoder walk, then verify canonical decode/encode recovery.
    low, high = Fraction(0), Fraction(1)
    for symbol in plaintext:
        width = high - low
        old_low = low
        low = old_low + width * Fraction(symbol, 2)
        high = old_low + width * Fraction(symbol + 1, 2)
    canonical = canonical_codeword((low, high))
    decoded, decoded_interval = arithmetic_decode(
        base9_fraction(canonical), len(plaintext), "static_histogram",
        histogram, transitions,
    )
    assert decoded == plaintext
    assert canonical_codeword(decoded_interval) == canonical
    report = audit()
    assert report["declaration_count"] == 4
    assert all(row["input_codepoint_inside_final_interval"] for row in report["rows"])
    assert not report["promotion"]["promoted"]
    assert not report["password_oracle_run"]
    print("[*] self-test OK: exact fraction decode, canonical interval codeword, and four declarations verified")
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
    print("[*] missing source fields:", report["missing_required_source_fields"])
    for row in report["rows"]:
        print(
            f"[*] {row['model']}/n={row['output_length']}: "
            f"decoded={row['decoded_prefix']!r} "
            f"canonical_len={row['canonical_codeword_length']} "
            f"canonical_equals_faed={row['canonical_equals_faed']} "
            f"decoded_source_hit={row['decoded_equals_same_length_source']}"
        )
    print("[*] exact canonical hits:", report["exact_canonical_hits"])
    print("[*] source plaintext hits:", report["source_plaintext_hits"])
    print("[*] no candidate text or password oracle was used")


if __name__ == "__main__":
    main()
