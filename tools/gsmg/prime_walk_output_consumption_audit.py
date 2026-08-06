#!/usr/bin/env python3
"""Bounded audit of what can consume the exact Flo/Denis prime-walk output.

Phase 48 fixes a 31-position mask over the aligned 91-character plaintext
and leaves two first-piece events beyond DBBI. This module checks only direct
operations suggested by already-authenticated wording:

* selected characters versus their complement ("yin yang");
* selected positions replaced by zero versus complement positions replaced
  by zero ("characters ... zeroed out");
* the 91-bit selection mask in its exact 7x13 / 13x7 matrix factorizations,
  read by rows or columns and decoded as 13 seven-bit values;
* row/column sum lists for those same two matrix shapes ("matrix sum list");
* blue, yellow, and FEFE rails fixed by the event labels;
* the two image events left after DBBI is exhausted.

No reversals, rotations, arbitrary transpositions, hashes, ciphers, language
hill-climbs, or password generation are included. The purpose is to expose a
literal next instruction if one exists, or document that the exact mask alone
still does not specify a downstream operation.
"""

import argparse

from denis_prime_extraction_audit import SOURCE, TARGET
from first_piece_color_reconstruction import DEFAULT_IMAGE, reconstruct
from flo_prime_walk_provenance_audit import audit as prime_walk_audit

EXPECTED_COMPLEMENT = (
    "iaeoumaetorcktsthepvtekeybelntohfandbtterhlndthelsoedfundoli"
)
EXPECTED_STARTS = "ncsyagcahrasogaeafynesv"
EXPECTED_RAILS = {
    "B": "ncsygcaasogean",
    "Y": "anhirialfayastve",
    "F": "e",
}


def selection_mask(length, selected_positions_1_indexed):
    selected = set(selected_positions_1_indexed)
    return "".join("1" if position in selected else "0" for position in range(1, length + 1))


def matrix_stream(mask, rows, columns, order):
    if rows * columns != len(mask):
        raise ValueError("matrix shape does not fit mask length")
    grid = [
        mask[row * columns:(row + 1) * columns]
        for row in range(rows)
    ]
    if order == "rows":
        return mask
    if order == "columns":
        return "".join(
            grid[row][column]
            for column in range(columns)
            for row in range(rows)
        )
    raise ValueError(f"unknown matrix order: {order!r}")


def decode_7bit(bits):
    if len(bits) % 7:
        raise ValueError("7-bit decode requires a multiple of seven bits")
    values = tuple(int(bits[offset:offset + 7], 2) for offset in range(0, len(bits), 7))
    text = "".join(chr(value) if 32 <= value < 127 else "." for value in values)
    return values, text


def matrix_sums(mask, rows, columns):
    grid = [
        [int(bit) for bit in mask[row * columns:(row + 1) * columns]]
        for row in range(rows)
    ]
    row_sums = tuple(sum(row) for row in grid)
    column_sums = tuple(
        sum(grid[row][column] for row in range(rows))
        for column in range(columns)
    )
    return row_sums, column_sums


def a1z26_sums(values):
    return "".join(chr(64 + value) if 1 <= value <= 26 else "0" for value in values)


def event_rails(report):
    rails = {"B": [], "Y": [], "F": []}
    for record in report["fitted_spatial_walk"]:
        start = record["raw_position"] - 1
        rails[record["color"]].append(SOURCE[start:start + len(record["required"])])
    return {label: "".join(chunks) for label, chunks in rails.items()}


def audit(image_path=DEFAULT_IMAGE):
    prime_walk = prime_walk_audit(image_path=image_path)
    selected_positions = set(prime_walk["flo_positions"])
    selected = "".join(
        character
        for position, character in enumerate(SOURCE, start=1)
        if position in selected_positions
    )
    complement = "".join(
        character
        for position, character in enumerate(SOURCE, start=1)
        if position not in selected_positions
    )
    selected_zeroed = "".join(
        "0" if position in selected_positions else character
        for position, character in enumerate(SOURCE, start=1)
    )
    complement_zeroed = "".join(
        character if position in selected_positions else "0"
        for position, character in enumerate(SOURCE, start=1)
    )
    starts = "".join(
        SOURCE[record["raw_position"] - 1]
        for record in prime_walk["fitted_spatial_walk"]
    )

    mask = selection_mask(len(SOURCE), prime_walk["flo_positions"])
    seven_bit_reads = {}
    sum_lists = {}
    for rows, columns in ((7, 13), (13, 7)):
        row_sums, column_sums = matrix_sums(mask, rows, columns)
        sum_lists[f"{rows}x{columns}"] = {
            "rows": row_sums,
            "rows_a1z26": a1z26_sums(row_sums),
            "columns": column_sums,
            "columns_a1z26": a1z26_sums(column_sums),
        }
        for order in ("rows", "columns"):
            stream = matrix_stream(mask, rows, columns, order)
            for polarity in ("selected_1", "selected_0"):
                bits = stream if polarity == "selected_1" else "".join(
                    "0" if bit == "1" else "1" for bit in stream
                )
                key = f"{rows}x{columns}/{order}/{polarity}"
                values, text = decode_7bit(bits)
                seven_bit_reads[key] = {"values": values, "text": text}

    reconstruction = reconstruct(image_path)
    last_fitted_spiral = max(
        event["spiral_0"]
        for event in reconstruction["objects"]
        if event["ordinal_1"] == 22
    )
    unused_image_objects = tuple(
        {
            "ordinal": item["ordinal_1"],
            "character": item["character"],
            "color": "B" if item["color"] == "blue" else "Y",
            "spiral_0": item["spiral_0"],
        }
        for item in reconstruction["objects"]
        if item["spiral_0"] > last_fitted_spiral
    )
    remaining_walk = tuple(
        {
            "event": record["ordinal"],
            "prime": record["prime"],
            "raw_position": record["raw_position"],
            "type": record["color"],
        }
        for record in prime_walk["spatial_walk"][len(prime_walk["fitted_spatial_walk"]):]
    )

    return {
        "selected": selected,
        "complement": complement,
        "starts": starts,
        "selected_zeroed": selected_zeroed,
        "complement_zeroed": complement_zeroed,
        "mask": mask,
        "rails": event_rails(prime_walk),
        "seven_bit_reads": seven_bit_reads,
        "sum_lists": sum_lists,
        "unused_image_objects": unused_image_objects,
        "remaining_walk": remaining_walk,
        "literal_hits": {
            value: tuple(
                name
                for name, text in (
                    ("selected", selected),
                    ("complement", complement),
                    ("starts", starts),
                )
                if value in text
            )
            for value in ("yin", "yang", "salvation")
        },
    }


def self_test(image_path=DEFAULT_IMAGE):
    assert selection_mask(4, (1, 3)) == "1010"
    assert matrix_stream("100110", 2, 3, "columns") == "110100"
    assert decode_7bit("1000001") == ((65,), "A")
    assert matrix_sums("100110", 2, 3) == ((1, 2), (2, 1, 0))

    report = audit(image_path)
    assert report["selected"] == TARGET
    assert report["complement"] == EXPECTED_COMPLEMENT
    assert report["starts"] == EXPECTED_STARTS
    assert report["rails"] == EXPECTED_RAILS
    assert len(report["mask"]) == 91
    assert report["mask"].count("1") == 31
    assert report["literal_hits"] == {
        "yin": (),
        "yang": ("selected",),
        "salvation": (),
    }
    assert report["sum_lists"]["7x13"]["rows"] == (6, 5, 3, 5, 3, 4, 5)
    assert report["sum_lists"]["7x13"]["rows_a1z26"] == "FECECDE"
    assert report["sum_lists"]["13x7"]["columns"] == (3, 7, 5, 5, 3, 3, 5)
    assert report["sum_lists"]["13x7"]["columns_a1z26"] == "CGEECCE"
    assert report["unused_image_objects"] == (
        {"ordinal": 23, "character": "e", "color": "B", "spiral_0": 183},
        {"ordinal": 24, "character": "d", "color": "Y", "spiral_0": 191},
    )
    assert report["remaining_walk"] == (
        {"event": 24, "prime": 89, "raw_position": 97, "type": "B"},
        {"event": 25, "prime": 97, "raw_position": 105, "type": "Y"},
    )
    assert not any(
        any(word in item["text"].lower() for word in ("yin", "yang", "seed", "key"))
        for item in report["seven_bit_reads"].values()
    )
    print(
        "[*] self-test OK: selected/complement outputs, fixed rails, zeroing, "
        "matrix reads/sums, and residual ED/BY events verified"
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
    print(f"[*] selected 31:   {report['selected']}")
    print(f"[*] complement 60: {report['complement']}")
    print(f"[*] token starts 23: {report['starts']}")
    print(f"[*] rails: {report['rails']}")
    print(f"[*] literal yin/yang/salvation hits: {report['literal_hits']}")
    print("\n[*] matrix sum lists:")
    for shape, values in report["sum_lists"].items():
        print(
            f"    {shape}: rows={values['rows']} ({values['rows_a1z26']}), "
            f"columns={values['columns']} ({values['columns_a1z26']})"
        )
    print("\n[*] 7-bit mask reads:")
    seen = set()
    for name, item in report["seven_bit_reads"].items():
        signature = item["values"]
        if signature in seen:
            continue
        seen.add(signature)
        print(f"    {name}: {item['text']!r} {item['values']}")
    print(f"\n[*] unused image objects: {report['unused_image_objects']}")
    print(f"[*] corresponding remaining walk events: {report['remaining_walk']}")
    print(
        "[*] verdict: the exact mask exposes no literal downstream instruction "
        "under the frozen zeroing/matrix/rail family. 'yang' remains the sole "
        "literal clue word; the residual evidence is ED / B,Y / primes 89,97 / "
        "raw positions 97,105. None specifies an operation without a new clue."
    )


if __name__ == "__main__":
    main()
