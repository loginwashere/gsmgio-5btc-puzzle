#!/usr/bin/env python3
"""Audit the proposed first-piece Hamming/control-language synthesis.

This composes three already-authenticated image extractions:

* the complementary 24-bit yellow/blue masks from the rabbit grid;
* the unique FEFEFE grid cell; and
* the externally selected #383838 Stage-0 footer shadow layer.

It separates exact consequences from evidentiary weight.  In particular,
the 9/15 weights of the complementary color masks are forced by their source
labels, while the nibble-weight staircase and the repeated-gray coincidences
are descriptive observations recognized after extraction.  No password,
cipher, or Bitcoin-address oracle is run here.
"""

import argparse
from fractions import Fraction
from math import comb, prod

from first_piece_color_reconstruction import DEFAULT_IMAGE, TARGET, reconstruct
from stage0_footer_palette_layer_audit import TARGET as SHADOW_RGB


def popcount(value):
    return int(value).bit_count()


def byte_popcounts(data):
    return tuple(popcount(value) for value in data)


def nibble_popcounts(data):
    return tuple(
        weight
        for value in data
        for weight in (popcount(value >> 4), popcount(value & 0x0F))
    )


def reshape(values, rows, columns):
    assert len(values) == rows * columns
    return tuple(
        tuple(values[row * columns : (row + 1) * columns])
        for row in range(rows)
    )


def matrix_sums(matrix):
    return {
        "rows": tuple(sum(row) for row in matrix),
        "columns": tuple(sum(row[column] for row in matrix) for column in range(len(matrix[0]))),
        "total": sum(sum(row) for row in matrix),
    }


def exact_nibble_profile_count(profile):
    """Number of 24-bit strings having this ordered six-nibble weight profile."""
    return prod(comb(4, weight) for weight in profile)


def audit(image_path=DEFAULT_IMAGE):
    first_piece = reconstruct(image_path)
    prime = bytes.fromhex(first_piece["prime_hex"])
    rose = bytes.fromhex(first_piece["rose_hex"])
    assert len(prime) == len(rose) == 3

    prime_nibbles = nibble_popcounts(prime)
    rose_nibbles = nibble_popcounts(rose)
    prime_matrix = reshape(prime_nibbles, 2, 3)
    rose_matrix = reshape(rose_nibbles, 2, 3)
    profile_count = exact_nibble_profile_count(prime_nibbles)

    shadow_byte = SHADOW_RGB[0]
    assert SHADOW_RGB == (shadow_byte,) * 3
    shadow = bytes((shadow_byte,) * 3)
    shadow_complement = bytes(value ^ 0xFF for value in shadow)
    fefe = bytes((0xFE,) * 3)

    cleared_prime = bytes(value & 0xFE for value in prime)
    cleared_rose = bytes(value & 0xFE for value in rose)
    restored_white = bytes(value | 0x01 for value in fefe)

    flat_tuple = "".join(TARGET[position - 1] for position in (1, 4, 21))
    residual_bit_count = len(TARGET) * 7

    return {
        "source": {
            "target": TARGET,
            "color_sequence": first_piece["color_sequence"],
            "blue_count": first_piece["blue_count"],
            "yellow_count": first_piece["yellow_count"],
            "rose_hex": first_piece["rose_hex"],
            "prime_hex": first_piece["prime_hex"],
            "prime_value": first_piece["prime_value"],
            "fefe": first_piece["fefe"],
            "shadow_rgb": SHADOW_RGB,
        },
        "color_masks": {
            "prime_popcount": sum(byte_popcounts(prime)),
            "rose_popcount": sum(byte_popcounts(rose)),
            "xor_hex": bytes(a ^ b for a, b in zip(prime, rose)).hex().upper(),
            "integer_sum_hex": f"{int.from_bytes(prime, 'big') + int.from_bytes(rose, 'big'):06X}",
            "prime_nibble_popcounts": prime_nibbles,
            "rose_nibble_popcounts": rose_nibbles,
            "prime_matrix": prime_matrix,
            "rose_matrix": rose_matrix,
            "cellwise_sums": tuple(a + b for a, b in zip(prime_nibbles, rose_nibbles)),
            "prime_matrix_sums": matrix_sums(prime_matrix),
            "rose_matrix_sums": matrix_sums(rose_matrix),
        },
        "gray_controls": {
            "shadow_hex": shadow.hex().upper(),
            "shadow_byte_popcount": popcount(shadow_byte),
            "shadow_popcount": sum(byte_popcounts(shadow)),
            "shadow_complement_hex": shadow_complement.hex().upper(),
            "shadow_complement_popcount": sum(byte_popcounts(shadow_complement)),
            "fefe_popcount": sum(byte_popcounts(fefe)),
            "fefe_zero_count": 24 - sum(byte_popcounts(fefe)),
            "fefe_zero_bit_indices_per_byte": tuple(
                bit for bit in range(8) if not ((0xFE >> bit) & 1)
            ),
            "fefe_and_prime_hex": cleared_prime.hex().upper(),
            "fefe_and_prime_value": int.from_bytes(cleared_prime, "big"),
            "fefe_and_prime_delta": int.from_bytes(prime, "big") - int.from_bytes(cleared_prime, "big"),
            "fefe_and_rose_hex": cleared_rose.hex().upper(),
            "fefe_or_010101_hex": restored_white.hex().upper(),
        },
        "structural_21": {
            "fefe_popcount": sum(byte_popcounts(fefe)),
            "character_position": first_piece["fefe"]["character_1"],
            "character": first_piece["fefe"]["character"],
            "flat_1_4_21": flat_tuple,
            "residual_bit_count_after_lsb_removal": residual_bit_count,
            "residual_byte_count": residual_bit_count // 8,
        },
        "calibration": {
            "ordered_nibble_profile_count": profile_count,
            "all_weight_9_masks": comb(24, 9),
            "profile_rate_conditioned_on_weight_9": Fraction(profile_count, comb(24, 9)),
            "repeated_gray_bytes_with_total_weight_9": comb(8, 3),
            "repeated_gray_bytes_with_total_weight_15": comb(8, 5),
            "repeated_gray_family_size": 256,
            "fefe_like_bytes_with_seven_ones": comb(8, 7),
            "unique_mask_preserving_seven_high_bits_and_clearing_only_lsb": 0xFE,
        },
    }


def self_test():
    report = audit()
    masks = report["color_masks"]
    gray = report["gray_controls"]
    structural = report["structural_21"]
    calibration = report["calibration"]

    assert masks["prime_popcount"] == 9
    assert masks["rose_popcount"] == 15
    assert masks["xor_hex"] == "FFFFFF"
    assert masks["integer_sum_hex"] == "FFFFFF"
    assert masks["prime_nibble_popcounts"] == (0, 1, 2, 1, 2, 3)
    assert masks["rose_nibble_popcounts"] == (4, 3, 2, 3, 2, 1)
    assert masks["prime_matrix"] == ((0, 1, 2), (1, 2, 3))
    assert masks["rose_matrix"] == ((4, 3, 2), (3, 2, 1))
    assert masks["cellwise_sums"] == (4, 4, 4, 4, 4, 4)
    assert masks["prime_matrix_sums"] == {"rows": (3, 6), "columns": (1, 3, 5), "total": 9}
    assert masks["rose_matrix_sums"] == {"rows": (9, 6), "columns": (7, 5, 3), "total": 15}

    assert gray["shadow_hex"] == "383838"
    assert gray["shadow_byte_popcount"] == 3
    assert gray["shadow_popcount"] == 9
    assert gray["shadow_complement_hex"] == "C7C7C7"
    assert gray["shadow_complement_popcount"] == 15
    assert gray["fefe_popcount"] == 21
    assert gray["fefe_zero_count"] == 3
    assert gray["fefe_zero_bit_indices_per_byte"] == (0,)
    assert gray["fefe_and_prime_hex"] == "08C26C"
    assert gray["fefe_and_prime_value"] == 574060
    assert gray["fefe_and_prime_delta"] == 1
    assert gray["fefe_and_rose_hex"] == "F63C92"
    assert gray["fefe_or_010101_hex"] == "FFFFFF"

    assert structural == {
        "fefe_popcount": 21,
        "character_position": 21,
        "character": "n",
        "flat_1_4_21": "ggn",
        "residual_bit_count_after_lsb_removal": 168,
        "residual_byte_count": 21,
    }
    assert calibration["ordered_nibble_profile_count"] == 2304
    assert calibration["all_weight_9_masks"] == comb(24, 9)
    assert calibration["profile_rate_conditioned_on_weight_9"] == Fraction(2304, comb(24, 9))
    assert calibration["repeated_gray_bytes_with_total_weight_9"] == 56
    assert calibration["repeated_gray_bytes_with_total_weight_15"] == 56
    assert calibration["fefe_like_bytes_with_seven_ones"] == 8
    assert calibration["unique_mask_preserving_seven_high_bits_and_clearing_only_lsb"] == 0xFE
    print("[*] self-test OK: first-piece Hamming/control identities and calibration reproduce")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    report = audit()
    masks = report["color_masks"]
    gray = report["gray_controls"]
    calibration = report["calibration"]

    print(
        "[*] color masks: "
        f"08C26D weight={masks['prime_popcount']}, "
        f"F73D92 weight={masks['rose_popcount']}, "
        f"xor/sum={masks['xor_hex']}"
    )
    print(
        f"[*] nibble weights: {masks['prime_matrix']} / {masks['rose_matrix']}; "
        f"column sums={masks['prime_matrix_sums']['columns']} / "
        f"{masks['rose_matrix_sums']['columns']}"
    )
    print(
        f"[*] 383838 weight={gray['shadow_popcount']}; "
        f"C7C7C7 weight={gray['shadow_complement_popcount']}; "
        f"FEFEFE weight/zeros={gray['fefe_popcount']}/{gray['fefe_zero_count']}"
    )
    print(
        f"[*] FEFEFE clears byte LSBs: 08C26D -> {gray['fefe_and_prime_hex']} "
        f"({gray['fefe_and_prime_value']}, delta={gray['fefe_and_prime_delta']})"
    )
    print(f"[*] structural 21 report: {report['structural_21']}")
    rate = calibration["profile_rate_conditioned_on_weight_9"]
    print(
        "[*] ordered nibble-weight profile among fixed-weight-9 masks: "
        f"{rate.numerator}/{rate.denominator} = {float(rate):.9f} "
        "(descriptive; profile recognized post hoc)"
    )
    print(
        "[*] repeated grayscale null: 56/256 bytes have weight 3 "
        "(24-bit total 9), and 56/256 have weight 5 (total 15)"
    )
    if args.self_test:
        self_test()


if __name__ == "__main__":
    main()
