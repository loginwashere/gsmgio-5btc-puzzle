#!/usr/bin/env python3
"""Audit whether Phase 48's two residual events cross the real page boundary.

The normalized SalPhaseIon stream begins with:

    DBBI (91 symbols) + abba("matrixsumlist") (104 symbols) + FAED ...

Phase 48's 25-event walk fits 23 events inside DBBI. Its final two adjusted
positions are 97 and 105, so they do not point into empty space in the actual
page: they point to local offsets 6 and 14 of the immediately following
binary-ASCII matrix instruction. Both offsets are bit 6 of consecutive bytes,
the letters ``m`` and ``a``. Under the established binary encoding
``a -> 0`` / ``b -> 1``, those bits are ``b,a`` = ``1,0``, matching the final
blue/yellow event values.

The bit match has an ordinary exact profile-preserving rate (~0.251) and was
noticed after the boundary was inspected. This is therefore a structural
transition checkpoint, not statistical confirmation and not a password lead.
"""

import argparse
from collections import Counter
from fractions import Fraction

from data import DBBI, FAED, SALPHASEION_BLOB_B64
from first_piece_color_reconstruction import DEFAULT_IMAGE
from flo_prime_walk_provenance_audit import audit as prime_walk_audit
from page_structure_audit import (
    DECIMAL_INSTRUCTIONS,
    ENTER_INSTRUCTION,
    HASH_PREFIX,
    HASH_SUFFIX,
    MATRIX_INSTRUCTION,
    binary_ascii,
    decimal_transport,
    segment_salphaseion,
)


def exact_two_bit_profile_rate(bits, first, second):
    counts = Counter(bits)
    if first == second:
        return Fraction(counts[first] * (counts[first] - 1), len(bits) * (len(bits) - 1))
    return Fraction(counts[first] * counts[second], len(bits) * (len(bits) - 1))


def audit(image_path=DEFAULT_IMAGE):
    matrix_bits = binary_ascii(MATRIX_INSTRUCTION)
    logical_prefix = DBBI + matrix_bits
    segments = segment_salphaseion(
        logical_prefix
        + FAED
        + "z"
        + decimal_transport(DECIMAL_INSTRUCTIONS[0])
        + "z"
        + decimal_transport(DECIMAL_INSTRUCTIONS[1])
        + "z"
        + HASH_PREFIX
        + SALPHASEION_BLOB_B64[:64]
        + binary_ascii(ENTER_INSTRUCTION)
        + SALPHASEION_BLOB_B64[64:]
        + HASH_SUFFIX
    )
    matrix_segment = next(segment for segment in segments if segment.name == "abba_matrix_instruction")

    prime_walk = prime_walk_audit(image_path=image_path)
    residual = prime_walk["spatial_walk"][len(prime_walk["fitted_spatial_walk"]):]
    records = []
    expected_binary = {"B": "b", "Y": "a"}
    for record in residual:
        global_position = record["raw_position"]
        local_offset = global_position - matrix_segment.start
        zero_index = local_offset - 1
        actual = logical_prefix[global_position - 1]
        byte_ordinal, bit_zero = divmod(zero_index, 8)
        records.append(
            {
                "event": record["ordinal"],
                "type": record["color"],
                "prime": record["prime"],
                "global_position": global_position,
                "matrix_offset_1": local_offset,
                "matrix_byte_1": byte_ordinal + 1,
                "matrix_character": MATRIX_INSTRUCTION[byte_ordinal],
                "bit_1": bit_zero + 1,
                "expected": expected_binary[record["color"]],
                "actual": actual,
                "matches": actual == expected_binary[record["color"]],
            }
        )

    observed = "".join(record["actual"] for record in records)
    expected = "".join(record["expected"] for record in records)
    rate = exact_two_bit_profile_rate(matrix_bits, expected[0], expected[1])
    return {
        "dbbi_length": len(DBBI),
        "matrix_segment_start_0": matrix_segment.start,
        "matrix_segment_end_0": matrix_segment.end,
        "matrix_bits_length": len(matrix_bits),
        "matrix_bit_counts": Counter(matrix_bits),
        "records": tuple(records),
        "observed_bits": observed,
        "expected_bits": expected,
        "all_match": all(record["matches"] for record in records),
        "containing_characters": "".join(record["matrix_character"] for record in records),
        "profile_rate": rate,
    }


def self_test(image_path=DEFAULT_IMAGE):
    assert exact_two_bit_profile_rate("aabb", "a", "b") == Fraction(1, 3)
    assert exact_two_bit_profile_rate("aabb", "a", "a") == Fraction(1, 6)

    report = audit(image_path)
    assert report["dbbi_length"] == 91
    assert report["matrix_segment_start_0"] == 91
    assert report["matrix_segment_end_0"] == 195
    assert report["matrix_bits_length"] == 104
    assert report["matrix_bit_counts"] == Counter({"b": 56, "a": 48})
    assert report["records"] == (
        {
            "event": 24,
            "type": "B",
            "prime": 89,
            "global_position": 97,
            "matrix_offset_1": 6,
            "matrix_byte_1": 1,
            "matrix_character": "m",
            "bit_1": 6,
            "expected": "b",
            "actual": "b",
            "matches": True,
        },
        {
            "event": 25,
            "type": "Y",
            "prime": 97,
            "global_position": 105,
            "matrix_offset_1": 14,
            "matrix_byte_1": 2,
            "matrix_character": "a",
            "bit_1": 6,
            "expected": "a",
            "actual": "a",
            "matches": True,
        },
    )
    assert report["observed_bits"] == report["expected_bits"] == "ba"
    assert report["containing_characters"] == "ma"
    assert report["profile_rate"] == Fraction(336, 1339)
    print(
        "[*] self-test OK: residual events cross into matrixsumlist at "
        "offsets 6/14, select bit 6 of 'm'/'a', and match B/Y as b/a"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", default=DEFAULT_IMAGE)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    self_test(args.image)
    if args.self_test:
        return

    report = audit(args.image)
    print(
        f"[*] logical boundary: DBBI 0:{report['dbbi_length']}, "
        f"matrixsumlist bits {report['matrix_segment_start_0']}:{report['matrix_segment_end_0']}"
    )
    for record in report["records"]:
        print(
            f"[*] event {record['event']} ({record['type']}): prime={record['prime']} "
            f"global={record['global_position']} matrix_offset={record['matrix_offset_1']} "
            f"byte={record['matrix_byte_1']} {record['matrix_character']!r} "
            f"bit={record['bit_1']} expected={record['expected']} "
            f"actual={record['actual']} match={record['matches']}"
        )
    rate = report["profile_rate"]
    print(
        f"[*] exact two-bit profile rate: {rate.numerator}/{rate.denominator} "
        f"= {float(rate):.6f}"
    )
    print(
        "[*] verdict: the two residual events point into the immediately "
        "following matrixsumlist segment and match its binary bits, but the "
        "~25% base rate is ordinary. Record as a clue-order boundary checkpoint, "
        "not confirmation or a cipher candidate."
    )


if __name__ == "__main__":
    main()
