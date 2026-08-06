#!/usr/bin/env python3
"""Audit the two strongest leads absent locally but surfaced by external mirrors.

This deliberately separates mechanical reproduction from provenance and
interpretation:

* ``YOUWON`` is reproduced from DBBI minus the solved 91-character VIC text,
  and calibrated under uniform shuffles of DBBI's exact symbol multiset.
* the colored-cell prime indices are derived from the pixel-verified genesis
  reconstruction and identified as primes congruent to 7 modulo 8.

The external catalog describes three signals at the ``YOUWON`` offset as
independent. They are not: the six-letter hit itself forces six consecutive
underflow bits, and its only feasible alignment under DBBI's a-i alphabet is
the start of the VIC-width run. This script asserts those dependencies so the
result cannot later be promoted as three independent confirmations.
"""

from collections import Counter
from fractions import Fraction
from math import prod

from data import ALPHA_322, DBBI, VALIDATION_ANSWER
from first_piece_color_reconstruction import DEFAULT_IMAGE, reconstruct

TARGET_WORD = "YOUWON"
EXPECTED_OUTPUT = (
    "VOZIJBDTIQBRGVEOMZNBCYOUWON"
    "XCPKWGBNAXDGJGDUNNVMPABTAFPAAXMJYLZBUWERDNXYDESKUOBXCAMVDJLQTSGA"
)
EXPECTED_PRIME_INDICES = {
    "blue": (7, 23, 31, 47, 103, 127),
    "yellow": (71, 79, 151, 167, 191),
}


def is_prime(value):
    if value < 2:
        return False
    divisor = 2
    while divisor * divisor <= value:
        if value % divisor == 0:
            return False
        divisor += 1
    return True


def subtract_mod26(left, right):
    return "".join(
        chr(((ord(a) - ord("a")) - (ord(b) - ord("a"))) % 26 + ord("A"))
        for a, b in zip(left, right.lower())
    )


def runs(bits, value=1):
    result = []
    start = 0
    while start < len(bits):
        end = start + 1
        while end < len(bits) and bits[end] == bits[start]:
            end += 1
        if bits[start] == value:
            result.append((start, end - start))
        start = end
    return result


def youwon_shuffle_expectation():
    """Return exact expected hit count under DBBI-multiset permutations.

    For each of the 86 possible starts, the fixed VIC plaintext and requested
    output determine six required DBBI values. Only feasible windows
    contribute. The events need not be independent, so this is an expected
    count rather than an exact family-wise probability. Here only one window
    is feasible, making the two quantities identical.
    """
    plaintext = VALIDATION_ANSWER.lower()
    counts = Counter(ord(character) - ord("a") for character in DBBI)
    target = [ord(character) - ord("A") for character in TARGET_WORD]
    denominator = prod(range(len(DBBI) - len(target) + 1, len(DBBI) + 1))
    feasible = []
    for start in range(len(DBBI) - len(target) + 1):
        required = tuple(
            (target[offset] + ord(plaintext[start + offset]) - ord("a")) % 26
            for offset in range(len(target))
        )
        needed = Counter(required)
        if any(value not in counts or amount > counts[value] for value, amount in needed.items()):
            continue
        numerator = 1
        for value, amount in needed.items():
            numerator *= prod(range(counts[value] - amount + 1, counts[value] + 1))
        feasible.append((start, required, Fraction(numerator, denominator)))
    return feasible


def color_prime_indices():
    result = reconstruct(DEFAULT_IMAGE)
    by_color = {"blue": [], "yellow": []}
    for item in result["objects"]:
        index = item["spiral_0"]
        if is_prime(index):
            by_color[item["color"]].append(index)
    return {color: tuple(values) for color, values in by_color.items()}


def audit():
    plaintext = VALIDATION_ANSWER.lower()
    output = subtract_mod26(DBBI, plaintext)
    hit_start = output.index(TARGET_WORD)

    underflow = [
        int(ord(dbbi_character) - ord("a") < ord(plain_character) - ord("a"))
        for dbbi_character, plain_character in zip(DBBI, plaintext)
    ]
    underflow_runs = sorted(runs(underflow), key=lambda item: item[1], reverse=True)

    top_row = set(ALPHA_322.split(".")[0].lower())
    width_bits = [0 if character in top_row else 1 for character in plaintext]
    width_runs = sorted(runs(width_bits), key=lambda item: item[1], reverse=True)

    feasible = youwon_shuffle_expectation()
    prime_indices = color_prime_indices()

    assert output == EXPECTED_OUTPUT
    assert hit_start == 21
    assert underflow[hit_start : hit_start + len(TARGET_WORD)] == [1] * 6
    assert underflow_runs[0] == (21, 7)
    assert width_runs[0] == (21, 9)
    assert len(feasible) == 1 and feasible[0][0] == hit_start
    assert prime_indices == EXPECTED_PRIME_INDICES
    assert all(
        index % 8 == 7
        for values in prime_indices.values()
        for index in values
    )

    return {
        "output": output,
        "hit_start_0": hit_start,
        "tail_length": len(output) - hit_start - len(TARGET_WORD),
        "underflow_longest": underflow_runs[0],
        "vic_width_longest": width_runs[0],
        "feasible_windows": feasible,
        "prime_indices": prime_indices,
    }


def main():
    result = audit()
    start, required, probability = result["feasible_windows"][0]
    print(f"YOUWON output: {result['output']}")
    print(
        f"YOUWON start: {result['hit_start_0']} (0-based), "
        f"tail: {result['tail_length']} characters"
    )
    print(
        "exact DBBI-multiset shuffle probability: "
        f"{probability.numerator}/{probability.denominator} "
        f"= {float(probability):.9g} (~1 in {1 / float(probability):,.1f})"
    )
    print(
        f"only feasible window: {start}; required DBBI symbols: "
        + "".join(chr(value + ord("a")) for value in required)
    )
    print(
        f"longest underflow run: {result['underflow_longest']}; "
        f"longest VIC-width run: {result['vic_width_longest']}"
    )
    print(f"colored prime indices: {result['prime_indices']}")
    print(
        "interpretation: mechanical findings reproduce, but the two rails are "
        "alignment-dependent and do not provide independent confirmations."
    )


if __name__ == "__main__":
    main()
