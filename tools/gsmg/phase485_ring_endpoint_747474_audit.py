#!/usr/bin/env python3
"""Phase 485: six spiral-ring endpoints + 747474 -> ASCII multiplication.

This is a retrospective structural verification.  The 14x14 grid, its
top-left counter-clockwise spiral, and its MSB-first ASCII decoding are already
authenticated by the solved first piece.  The literal selector ``747474`` is
user-supplied but is not pinned to a repository source, so the multiplication
selection remains explicitly conditional on that provenance.

No password, ciphertext, address, network, or external-source oracle is used.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from first_piece_color_reconstruction import (
    COLOR_NAMES,
    DEFAULT_IMAGE,
    N,
    TARGET,
    base_bit,
    load_grid,
    spiral_top_left_counterclockwise,
)
from first_piece_matrix_product_audit import audit as matrix_product_audit

SCRIPT_DIR = Path(__file__).resolve().parent
RESULT_PATH = SCRIPT_DIR / "phase485_result.json"
EXPECTED_IMAGE_SHA256 = "5e8d84b88f8f829428df5d2a8bf36c7268346f169b799ac7570b6223990d204f"
SELECTOR = "747474"


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bits_and_text(image_path: Path = DEFAULT_IMAGE) -> tuple[str, str]:
    if sha256_path(image_path) != EXPECTED_IMAGE_SHA256:
        raise AssertionError("first-piece image digest drifted")
    grid = load_grid(image_path)
    coordinates = spiral_top_left_counterclockwise()
    bits = "".join(str(base_bit(grid[row][column])) for row, column in coordinates)
    text = "".join(chr(int(bits[offset:offset + 8], 2)) for offset in range(0, 192, 8))
    if text != TARGET:
        raise AssertionError(f"authenticated spiral text drifted: {text!r}")
    return bits, text


def ring_rows(image_path: Path = DEFAULT_IMAGE) -> tuple[dict, ...]:
    bits, text = bits_and_text(image_path)
    grid = load_grid(image_path)
    coordinates = spiral_top_left_counterclockwise()
    rows = []
    start = 0
    for ordinal, size in enumerate(range(N, 0, -2), start=1):
        length = 4 * (size - 1) if size > 1 else 1
        end = start + length - 1
        row, column = coordinates[end]
        rows.append({
            "ordinal": ordinal,
            "size": size,
            "length": length,
            "start_spiral_0": start,
            "end_spiral_0": end,
            "end_row_1": row + 1,
            "end_column_1": column + 1,
            "end_bit_offset_0": end % 8,
            "end_bit_value": int(bits[end]),
            "end_color": COLOR_NAMES[grid[row][column]],
            "text_bearing": end < 192,
            "landing_character": text[end // 8] if end < 192 else None,
        })
        start += length
    if start != N * N:
        raise AssertionError("ring decomposition did not consume 196 cells")
    return tuple(rows)


def extract_selector_bits(characters: str, selector: str, *, index_base: int = 0) -> dict:
    if len(characters) != len(selector):
        raise ValueError("one selector digit is required per character")
    offsets = tuple(int(value) - index_base for value in selector)
    if not all(0 <= offset < 8 for offset in offsets):
        raise ValueError("selector digit is outside the selected bit-index base")
    byte_bits = tuple(format(ord(character), "08b") for character in characters)
    selected = "".join(bits[offset] for bits, offset in zip(byte_bits, offsets))
    value = int(selected, 2)
    return {
        "characters": characters,
        "selector": selector,
        "index_base": index_base,
        "byte_bits": byte_bits,
        "selected_bits": selected,
        "value": value,
        "ascii_if_printable": chr(value) if 32 <= value <= 126 else None,
    }


def audit(image_path: Path = DEFAULT_IMAGE) -> dict:
    rings = ring_rows(image_path)
    text_rings = tuple(row for row in rings if row["text_bearing"])
    landing = "".join(row["landing_character"] for row in text_rings)
    primary = extract_selector_bits(landing, SELECTOR, index_base=0)
    opposite = extract_selector_bits(landing, SELECTOR[::-1], index_base=0)
    one_based = extract_selector_bits(landing, SELECTOR, index_base=1)
    reversed_rings = extract_selector_bits(landing[::-1], SELECTOR, index_base=0)
    product = matrix_product_audit()
    fixed = product["fixed_operation"]

    return {
        "phase": 485,
        "status": "retrospective_structural_audit",
        "source": {
            "image": str(image_path),
            "image_sha256": sha256_path(image_path),
            "spiral": "top_left_counterclockwise_inward",
            "ascii_bit_order": "MSB_first",
            "decoded_text": TARGET,
        },
        "rings": list(rings),
        "ring_count": len(rings),
        "text_bearing_ring_count": len(text_rings),
        "center_tail_bits": bits_and_text(image_path)[0][192:],
        "landing_characters": landing,
        "ring_endpoint_rule": {
            "rule": "last character touched by each completed text-bearing ring",
            "motivation": "user-proposed last/arch structural reading",
            "status": "retrospective_semantic_choice",
            "authenticated": False,
        },
        "selector_provenance": {
            "literal": SELECTOR,
            "status": "user_supplied_unpinned_in_repository",
            "authenticated": False,
        },
        "primary_extraction": primary,
        "controls": {
            "opposite_phase_474747": opposite,
            "one_based_747474": one_based,
            "reversed_ring_order_747474": reversed_rings,
        },
        "operation_bridge": {
            "selected_ascii": primary["ascii_if_printable"],
            "is_multiplication_operator": primary["ascii_if_printable"] == "*",
            "canonical_matrix": product["source"]["matrix"],
            "canonical_sum_list": product["source"]["sum_list"],
            "canonical_product": fixed["output"],
            "canonical_serialized_hex_if_bytes": fixed["serialized_hex_if_bytes"],
            "multiplication_selected_if_selector_authenticated": primary["ascii_if_printable"] == "*",
            "byte_consumer_selected": False,
        },
        "disposition": {
            "structural_derivation_verified": primary["selected_bits"] == "101010",
            "conditional_operation_selector": primary["ascii_if_printable"] == "*",
            "ring_endpoint_rule_authenticated": False,
            "operation_selector_authenticated": False,
            "matrix_product_gap_closed": False,
            "reason": "ring-endpoint reading and 747474 provenance are unpinned; no byte consumer is selected",
        },
        "oracle_run": False,
    }


def self_test() -> None:
    report = audit()
    assert report["ring_count"] == 7
    assert report["text_bearing_ring_count"] == 6
    assert tuple(row["size"] for row in report["rings"]) == (14, 12, 10, 8, 6, 4, 2)
    assert tuple(row["length"] for row in report["rings"]) == (52, 44, 36, 28, 20, 12, 4)
    assert tuple(row["end_spiral_0"] for row in report["rings"]) == (51, 95, 131, 159, 179, 191, 195)
    assert tuple(row["end_bit_offset_0"] for row in report["rings"][:6]) == (3, 7, 3, 7, 3, 7)
    assert report["landing_characters"] == "ossaed"
    assert report["center_tail_bits"] == "0000"
    assert report["primary_extraction"]["selected_bits"] == "101010"
    assert report["primary_extraction"]["value"] == 42
    assert report["primary_extraction"]["ascii_if_printable"] == "*"
    assert report["controls"]["opposite_phase_474747"]["selected_bits"] == "110100"
    assert report["controls"]["opposite_phase_474747"]["ascii_if_printable"] == "4"
    assert report["controls"]["one_based_747474"]["selected_bits"] == "111000"
    assert report["controls"]["one_based_747474"]["ascii_if_printable"] == "8"
    assert report["controls"]["reversed_ring_order_747474"]["ascii_if_printable"] is None
    assert report["operation_bridge"]["canonical_product"] == (255, 103)
    assert report["operation_bridge"]["canonical_serialized_hex_if_bytes"] == "FF67"
    assert report["operation_bridge"]["is_multiplication_operator"]
    assert not report["operation_bridge"]["byte_consumer_selected"]
    assert not report["disposition"]["operation_selector_authenticated"]
    assert not report["disposition"]["ring_endpoint_rule_authenticated"]
    assert not report["disposition"]["matrix_product_gap_closed"]
    assert not report["oracle_run"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write-result", action="store_true")
    args = parser.parse_args()
    report = audit()
    if args.self_test:
        self_test()
        print("self-test: ok")
    print(
        f"rings={report['ring_count']} text_rings={report['text_bearing_ring_count']} "
        f"landing={report['landing_characters']!r} selector={SELECTOR} "
        f"bits={report['primary_extraction']['selected_bits']} "
        f"value={report['primary_extraction']['value']} "
        f"ascii={report['primary_extraction']['ascii_if_printable']!r}"
    )
    print(
        "conditional bridge: '*' selects canonical multiplication -> "
        f"{report['operation_bridge']['canonical_product']} / "
        f"{report['operation_bridge']['canonical_serialized_hex_if_bytes']}; "
        "consumer remains unselected"
    )
    if args.write_result:
        RESULT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {RESULT_PATH}")


if __name__ == "__main__":
    main()

