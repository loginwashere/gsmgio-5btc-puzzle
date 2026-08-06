#!/usr/bin/env python3
"""Audit the four unconsumed first-piece "rabbit nest" bits.

The recovered 2020 diagram identifies the central 2x2 box as the rabbit nest.
Those cells are exactly spiral positions 192-195, immediately after the
24-byte ``gsmg.io/theseedisplanted`` decode.  This audit reads the four bits
under the already-validated black/blue=1 polarity and its complement, then
tests the narrow operation suggested by their value: clear the fourth
one-based bit of every character selected by the exact 31-position mask.

No alternative bit planes, rotations, nibble orders, ciphers, hashes, or AES
escalation are included.

Corrected 2026-07-28 (Phase 127): the nest nibble was originally read as
``0100`` because ``grid_spiral.load_grid``/``first_piece_color_reconstruction.
load_grid`` sampled a single center pixel per cell, and the overlaid rabbit
line-art happens to cross exactly that point in cell (row 8, column 7,
1-indexed) -- a cell that is 76% white background by pixel area. Both loaders
now classify by majority color per cell instead. All four nest cells are
genuinely white; the true nibble is the trivial all-zero value ``0000``.
"""

import argparse

from denis_prime_extraction_audit import SOURCE
from first_piece_color_reconstruction import DEFAULT_IMAGE, reconstruct
from flo_prime_walk_provenance_audit import audit as prime_walk_audit
from grid_spiral import bitval, load_grid, spiral_tl_ccw

EXPECTED_NEST_BITS = "0000"
EXPECTED_COMPLEMENT_BITS = "1111"
EXPECTED_SELECTED_BIT4_ZEROED = "ncciangcahibiacogaleafaianecdfe"
EXPECTED_FULL_BIT4_ZEROED = (
    "incaceioumanagetocrackthisthepbivatekeycbelongtohalfandbetterhalfand"
    "theialsoneedfundcdolife"
)
CLUE_WORDS = ("yin", "yang", "seed", "key", "matrix", "sum", "list", "zero")


def clear_fourth_bit(character):
    """Clear one-based bit 4 from the MSB side: ASCII weight 0x10."""
    return chr(ord(character) & ~0x10)


def audit(image_path=DEFAULT_IMAGE):
    grid = load_grid(image_path)
    coords = spiral_tl_ccw()
    bits = "".join(str(bitval(grid[row][column])) for row, column in coords)
    nest_bits = bits[192:]
    complement_bits = "".join("0" if bit == "1" else "1" for bit in nest_bits)

    prime_walk = prime_walk_audit(image_path=image_path)
    selected_positions = set(prime_walk["flo_positions"])
    selected_zeroed = "".join(
        clear_fourth_bit(character)
        for position, character in enumerate(SOURCE, start=1)
        if position in selected_positions
    )
    full_zeroed = "".join(
        clear_fourth_bit(character)
        if position in selected_positions
        else character
        for position, character in enumerate(SOURCE, start=1)
    )
    changed = tuple(
        (position, character, clear_fourth_bit(character))
        for position, character in enumerate(SOURCE, start=1)
        if position in selected_positions
        and character != clear_fourth_bit(character)
    )

    reconstruction = reconstruct(image_path)
    fefe = reconstruction["fefe"]
    literal_hits = {
        output: tuple(
            word
            for word in CLUE_WORDS
            if word in text.lower()
        )
        for output, text in (
            ("selected_bit4_zeroed", selected_zeroed),
            ("full_bit4_zeroed", full_zeroed),
        )
    }
    novel_literal_hits = {
        output: tuple(word for word in words if word not in SOURCE.lower())
        for output, words in literal_hits.items()
    }
    return {
        "nest_coordinates_0": tuple(coords[192:]),
        "nest_bits": nest_bits,
        "nest_value": int(nest_bits, 2),
        "nest_hex": format(int(nest_bits, 2), "X"),
        "complement_bits": complement_bits,
        "complement_value": int(complement_bits, 2),
        "complement_hex": format(int(complement_bits, 2), "X"),
        "complement_pair_rate": 1 / 8,
        "fefe_bit_in_character_0": fefe["bit_0"],
        "fefe_bit_in_character_1": fefe["bit_1"],
        "fefe_value": fefe["value"],
        "selected_bit4_zeroed": selected_zeroed,
        "full_bit4_zeroed": full_zeroed,
        "changed_characters": changed,
        "literal_hits": literal_hits,
        "novel_literal_hits": novel_literal_hits,
    }


def self_test(image_path=DEFAULT_IMAGE):
    report = audit(image_path)
    assert report["nest_bits"] == EXPECTED_NEST_BITS
    assert report["nest_value"] == 0
    assert report["nest_hex"] == "0"
    assert report["complement_bits"] == EXPECTED_COMPLEMENT_BITS
    assert report["complement_value"] == 15
    assert report["complement_hex"] == "F"
    assert report["fefe_bit_in_character_0"] == 3
    assert report["fefe_bit_in_character_1"] == 4
    assert report["fefe_value"] == 0
    assert report["selected_bit4_zeroed"] == EXPECTED_SELECTED_BIT4_ZEROED
    assert report["full_bit4_zeroed"] == EXPECTED_FULL_BIT4_ZEROED
    assert report["literal_hits"] == {
        "selected_bit4_zeroed": (),
        "full_bit4_zeroed": ("key",),
    }
    assert not any(report["novel_literal_hits"].values())
    print(
        "[*] self-test OK: nest nibble 0000=0 / complement 1111=F (corrected: "
        "all 4 nest cells are genuinely white background), FEFE one-based bit "
        "4, and exact-mask bit-4 zeroing outputs verified"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", default=DEFAULT_IMAGE)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    report = audit(args.image)
    print(
        f"[*] rabbit nest: {report['nest_bits']} = {report['nest_value']} "
        f"(hex {report['nest_hex']}); complement "
        f"{report['complement_bits']} = {report['complement_value']} "
        f"(hex {report['complement_hex']})"
    )
    print(
        f"[*] FEFE marker: one-based bit "
        f"{report['fefe_bit_in_character_1']} = {report['fefe_value']}"
    )
    print(f"[*] selected bit-4-zeroed: {report['selected_bit4_zeroed']!r}")
    print(f"[*] full bit-4-zeroed: {report['full_bit4_zeroed']!r}")
    print(f"[*] changed characters: {report['changed_characters']}")
    print(f"[*] literal clue hits: {report['literal_hits']}")
    print(f"[*] novel literal clue hits: {report['novel_literal_hits']}")
    print(
        "[*] verdict: corrected 2026-07-28 (Phase 127) -- the nest nibble is "
        "the trivial all-zero value 0000/F, since all 4 nest cells are "
        "genuinely white background (a single-pixel sampler previously "
        "misread one as black due to overlaid rabbit ink). It carries no "
        "signal and is not a checksum; this line of investigation is closed. "
        "The direct exact-mask bit-4 zeroing operation is non-language, so "
        "do not expand to other bit planes or cipher escalation without a "
        "new clue."
    )
    if args.self_test:
        self_test(args.image)


if __name__ == "__main__":
    main()
