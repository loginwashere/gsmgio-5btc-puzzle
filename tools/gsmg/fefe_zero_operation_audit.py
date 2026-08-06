#!/usr/bin/env python3
"""Audit bounded meanings of zeroing the FEFE-marked character."""

import argparse
from pathlib import Path

from first_piece_color_reconstruction import DEFAULT_IMAGE, FEFE, TARGET, reconstruct

EXPECTED_CHARACTER = "n"
EXPECTED_CHARACTER_ORDINAL = 21
EXPECTED_BIT_ORDINAL = 4
EXPECTED_SPIRAL_INDEX = 163
EXPECTED_DELETION = "gsmg.io/theseedisplated"


def replace_at(text, index, replacement):
    return text[:index] + replacement + text[index + 1 :]


def audit(image_path):
    result = reconstruct(image_path)
    marker = result["fefe"]
    character_index = marker["character_0"]

    if (
        marker["character"],
        marker["character_1"],
        marker["bit_1"],
        marker["spiral_0"],
        marker["value"],
    ) != (
        EXPECTED_CHARACTER,
        EXPECTED_CHARACTER_ORDINAL,
        EXPECTED_BIT_ORDINAL,
        EXPECTED_SPIRAL_INDEX,
        0,
    ):
        raise AssertionError(f"unexpected FEFE marker: {marker}")

    source_byte = ord(marker["character"])
    bit_mask = 1 << (7 - marker["bit_0"])
    if source_byte & bit_mask:
        raise AssertionError("the addressed bit is not already zero")

    operations = {
        "set_marked_bit_to_zero": TARGET,
        "delete_marked_character": replace_at(TARGET, character_index, ""),
        "replace_marked_character_with_literal_zero": replace_at(
            TARGET, character_index, "0"
        ),
        "replace_marked_character_with_nul": (
            TARGET[:character_index].encode()
            + b"\x00"
            + TARGET[character_index + 1 :].encode()
        ),
    }
    if operations["delete_marked_character"] != EXPECTED_DELETION:
        raise AssertionError(
            f"unexpected deletion result: {operations['delete_marked_character']!r}"
        )

    payload = TARGET.rsplit("/", 1)[1]
    payload_start = len(TARGET) - len(payload)
    payload_marker_index = marker["character_0"] - payload_start
    deletion_outcomes = [
        payload[:index] + payload[index + 1 :] for index in range(len(payload))
    ]
    expected_payload = EXPECTED_DELETION.rsplit("/", 1)[1]
    if deletion_outcomes[payload_marker_index] != expected_payload:
        raise AssertionError("payload deletion does not produce the expected phrase")

    color_hex = "".join(f"{channel:02X}" for channel in FEFE)
    color_pairs = tuple(
        color_hex[offset : offset + 2] for offset in range(0, len(color_hex), 2)
    )
    if color_pairs != ("FE", "FE", "FE"):
        raise AssertionError(f"unexpected FEFE decomposition: {color_pairs}")

    fen_channels = tuple(pair + marker["character"].upper() for pair in color_pairs)
    if fen_channels != ("FEN", "FEN", "FEN"):
        raise AssertionError(f"unexpected FE+N decomposition: {fen_channels}")

    return {
        "marker": marker,
        "source_byte": source_byte,
        "source_bits": f"{source_byte:08b}",
        "bit_mask": bit_mask,
        "operations": operations,
        "payload": payload,
        "payload_marker_index": payload_marker_index,
        "deletion_outcomes": deletion_outcomes,
        "color_hex": color_hex,
        "color_pairs": color_pairs,
        "fen_channels": fen_channels,
    }


def print_report(report):
    marker = report["marker"]
    print("addressed source")
    print(f"  text={TARGET}")
    print(
        f"  character={marker['character']!r} ordinal1={marker['character_1']} "
        f"bit1={marker['bit_1']} spiral0={marker['spiral_0']}"
    )
    print(
        f"  byte={report['source_byte']} bits={report['source_bits']} "
        f"addressed_bit={marker['value']}"
    )
    print()
    print("frozen zeroing interpretations")
    for label, value in report["operations"].items():
        print(f"  {label}: {value!r}")
    print()
    print("single deletions of the payload")
    payload = report["payload"]
    for index, value in enumerate(report["deletion_outcomes"]):
        indicator = "*" if index == report["payload_marker_index"] else " "
        print(f" {indicator} delete payload[{index}]={payload[index]!r}: {value}")
    print()
    print("bounded FE readings")
    print(f"  RGB hex={report['color_hex']} pairs={report['color_pairs']}")
    print("  Fe is the chemical symbol for iron; deletion yields 'the seed is plated'.")
    print(
        f"  secondary cross-phase reading: FE + N per channel = "
        f"{report['fen_channels']}"
    )
    print("  no creator-authored metal/plating instruction was found.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, default=DEFAULT_IMAGE)
    args = parser.parse_args()
    print_report(audit(args.image))


if __name__ == "__main__":
    main()
