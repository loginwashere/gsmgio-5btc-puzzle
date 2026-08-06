#!/usr/bin/env python3
"""Audit bounded operations suggested by the unconfirmed Looking Forward lead."""

import argparse
from pathlib import Path

from first_piece_color_reconstruction import DEFAULT_IMAGE, TARGET, reconstruct

EXPECTED_TRUE_CHARACTERS = "gsmgio/eseeisae"
EXPECTED_FALSE_CHARACTERS = ".thdplntd"
EXPECTED_BYTE_ALIGNED_FORWARD = "ted"


def packed_bytes(bits):
    return bytes(
        int(bits[offset : offset + 8], 2)
        for offset in range(0, len(bits) - 7, 8)
    )


def audit(image_path):
    result = reconstruct(image_path)
    marker = result["fefe"]
    bits = "".join(f"{ord(character):08b}" for character in TARGET)

    true_characters = "".join(
        item["character"] for item in result["objects"] if item["blue_1_bit"]
    )
    false_characters = "".join(
        item["character"] for item in result["objects"] if item["yellow_1_bit"]
    )
    if true_characters != EXPECTED_TRUE_CHARACTERS:
        raise AssertionError(f"unexpected true-LSB selection: {true_characters!r}")
    if false_characters != EXPECTED_FALSE_CHARACTERS:
        raise AssertionError(f"unexpected false-LSB selection: {false_characters!r}")

    exact_forward = packed_bytes(bits[marker["spiral_0"] :])
    after_marker = packed_bytes(bits[marker["spiral_0"] + 1 :])
    next_byte_offset = (marker["character_0"] + 1) * 8
    byte_aligned_forward = packed_bytes(bits[next_byte_offset:]).decode("ascii")
    if byte_aligned_forward != EXPECTED_BYTE_ALIGNED_FORWARD:
        raise AssertionError(
            f"unexpected byte-aligned forward suffix: {byte_aligned_forward!r}"
        )

    return {
        "marker": marker,
        "true_bits": result["blue_one_bits"],
        "false_bits": result["yellow_one_bits"],
        "true_value_hex": result["rose_hex"],
        "false_value": result["prime_value"],
        "true_characters": true_characters,
        "false_characters": false_characters,
        "exact_forward_hex": exact_forward.hex(),
        "after_marker_hex": after_marker.hex(),
        "byte_aligned_forward": byte_aligned_forward,
    }


def print_report(report):
    print("last/true-false interpretations:")
    print(
        f"  true LSBs -> 0x{report['true_value_hex']} "
        f"characters={report['true_characters']!r}"
    )
    print(
        f"  false LSBs -> {report['false_value']} "
        f"characters={report['false_characters']!r}"
    )
    print("forward-from-FEFE interpretations:")
    print(f"  exact marked bit -> hex={report['exact_forward_hex']}")
    print(f"  bit after marker -> hex={report['after_marker_hex']}")
    print(f"  next byte -> {report['byte_aligned_forward']!r}")
    print(
        "verdict: these bounded readings reproduce known outputs, select "
        "non-language, or expose only the existing URL suffix; no new "
        "transition is obtained."
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, default=DEFAULT_IMAGE)
    args = parser.parse_args()
    print_report(audit(args.image))


if __name__ == "__main__":
    main()
