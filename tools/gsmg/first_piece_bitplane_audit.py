#!/usr/bin/env python3
"""Audit the complete eight-plane transpose of the authenticated Stage-0 URL.

The 24 colored endpoints are already proven to be the LSB of each decoded URL
byte.  This module transposes all 192 URL bits into eight ordered 24-bit planes,
checks the colored plane against the image extraction, inventories every plane
and its complement, and packs the remaining 7x24 matrix under its two natural
traversals (plane-major and character-major).

The 21-byte residual length is an exact arithmetic consequence of 24 seven-bit
columns.  It is not treated as an independent p-value or as recovered text.
No reversal, rotation, cipher, hash, or password oracle is included.
"""

import argparse

from first_piece_color_reconstruction import DEFAULT_IMAGE, TARGET, is_prime, reconstruct

FULL_24_MASK = (1 << 24) - 1


def bits_to_bytes(bits):
    if len(bits) % 8:
        raise ValueError("bit length must be divisible by eight")
    return bytes(
        int(bits[offset:offset + 8], 2)
        for offset in range(0, len(bits), 8)
    )


def printable_report(data):
    printable = sum(32 <= value < 127 for value in data)
    longest = 0
    running = 0
    for value in data:
        if 32 <= value < 127:
            running += 1
            longest = max(longest, running)
        else:
            running = 0
    return {
        "printable_count": printable,
        "length": len(data),
        "printable_ratio": printable / len(data) if data else 0.0,
        "longest_printable_run": longest,
    }


def nibble_popcounts(value):
    return tuple(int(character, 16).bit_count() for character in f"{value:06X}")


def unit_staircase(profile):
    """Recognize a 2x3 additive plane with unit steps in both axes."""
    top = profile[:3]
    bottom = profile[3:]
    horizontal = top[1] - top[0]
    return (
        abs(horizontal) == 1
        and top[2] - top[1] == horizontal
        and all(bottom[column] - top[column] == horizontal for column in range(3))
    )


def plane_inventory(source):
    rows = []
    for bit_index in range(7, -1, -1):
        bits = "".join(str((value >> bit_index) & 1) for value in source)
        value = int(bits, 2)
        complement = value ^ FULL_24_MASK
        rows.append(
            {
                "bit_index": bit_index,
                "bits": bits,
                "hex": f"{value:06X}",
                "value": value,
                "weight": bits.count("1"),
                "prime": is_prime(value),
                "nibble_popcounts": nibble_popcounts(value),
                "unit_staircase": unit_staircase(nibble_popcounts(value)),
                "complement_hex": f"{complement:06X}",
                "complement_value": complement,
                "complement_weight": 24 - bits.count("1"),
                "complement_prime": is_prime(complement),
                "complement_nibble_popcounts": nibble_popcounts(complement),
                "complement_unit_staircase": unit_staircase(nibble_popcounts(complement)),
            }
        )
    return tuple(rows)


def reconstruct_from_planes(rows):
    return bytes(
        sum(int(next(row for row in rows if row["bit_index"] == bit)["bits"][column]) << bit for bit in range(8))
        for column in range(24)
    )


def reconstruct_from_charwise_residual(residual_bits, lsb_bits):
    if len(residual_bits) != 7 * len(lsb_bits):
        raise ValueError("residual/LSB dimensions do not match")
    return bytes(
        (int(residual_bits[index * 7:(index + 1) * 7], 2) << 1) | int(lsb_bits[index])
        for index in range(len(lsb_bits))
    )


def audit(image_path=DEFAULT_IMAGE):
    image_result = reconstruct(image_path)
    source = TARGET.encode("ascii")
    rows = plane_inventory(source)
    by_bit = {row["bit_index"]: row for row in rows}
    lsb = by_bit[0]

    residual_plane_bits = "".join(by_bit[bit]["bits"] for bit in range(7, 0, -1))
    residual_character_bits = "".join(f"{value:08b}"[:7] for value in source)
    plane_major = bits_to_bytes(residual_plane_bits)
    character_major = bits_to_bytes(residual_character_bits)

    weight_9_members = tuple(
        (row["bit_index"], polarity)
        for row in rows
        for polarity, weight in (
            ("direct", row["weight"]),
            ("complement", row["complement_weight"]),
        )
        if weight == 9
    )
    weight_15_members = tuple(
        (row["bit_index"], polarity)
        for row in rows
        for polarity, weight in (
            ("direct", row["weight"]),
            ("complement", row["complement_weight"]),
        )
        if weight == 15
    )
    prime_members = tuple(
        (row["bit_index"], polarity, value)
        for row in rows
        for polarity, value, prime in (
            ("direct", row["value"], row["prime"]),
            ("complement", row["complement_value"], row["complement_prime"]),
        )
        if prime
    )
    staircase_members = tuple(
        (row["bit_index"], polarity, profile)
        for row in rows
        for polarity, passed, profile in (
            ("direct", row["unit_staircase"], row["nibble_popcounts"]),
            ("complement", row["complement_unit_staircase"], row["complement_nibble_popcounts"]),
        )
        if passed
    )

    return {
        "source": TARGET,
        "source_byte_count": len(source),
        "source_bit_count": len(source) * 8,
        "planes": rows,
        "lsb_matches_image_blue_one": lsb["bits"] == image_result["blue_one_bits"],
        "lsb_hex": lsb["hex"],
        "lsb_complement_hex": lsb["complement_hex"],
        "residual_dimensions": (7, 24),
        "residual_bit_count": len(residual_plane_bits),
        "residual_byte_count": len(plane_major),
        "plane_major_hex": plane_major.hex().upper(),
        "character_major_hex": character_major.hex().upper(),
        "plane_major_printable": printable_report(plane_major),
        "character_major_printable": printable_report(character_major),
        "plane_reconstruction": reconstruct_from_planes(rows).decode("ascii"),
        "character_major_reconstruction": reconstruct_from_charwise_residual(
            residual_character_bits, lsb["bits"]
        ).decode("ascii"),
        "weight_9_members": weight_9_members,
        "weight_15_members": weight_15_members,
        "prime_members": prime_members,
        "staircase_members": staircase_members,
        "integral_residual_lengths_1_to_64": tuple(
            length for length in range(1, 65) if (7 * length) % 8 == 0
        ),
        "length_producing_21_bytes": 21 * 8 // 7,
    }


def self_test():
    report = audit()
    assert report["source_byte_count"] == 24
    assert report["source_bit_count"] == 192
    assert report["lsb_matches_image_blue_one"] is True
    assert report["lsb_hex"] == "F73D92"
    assert report["lsb_complement_hex"] == "08C26D"
    assert tuple(
        (row["bit_index"], row["hex"], row["weight"])
        for row in report["planes"]
    ) == (
        (7, "000000", 0),
        (6, "F6FFFF", 22),
        (5, "FFFFFF", 24),
        (4, "4090C4", 6),
        (3, "2F4128", 9),
        (2, "BBAE2F", 16),
        (1, "DB1088", 9),
        (0, "F73D92", 15),
    )
    assert report["residual_dimensions"] == (7, 24)
    assert report["residual_bit_count"] == 168
    assert report["residual_byte_count"] == 21
    assert report["plane_major_hex"] == "000000F6FFFFFFFFFF4090C42F4128BBAE2FDB1088"
    assert report["character_major_hex"] == "66E5B332ED1B9774D193964C993472E1B306EE9932"
    assert report["plane_reconstruction"] == TARGET
    assert report["character_major_reconstruction"] == TARGET
    assert report["weight_9_members"] == (
        (3, "direct"),
        (1, "direct"),
        (0, "complement"),
    )
    assert report["weight_15_members"] == (
        (3, "complement"),
        (1, "complement"),
        (0, "direct"),
    )
    assert report["prime_members"] == ((0, "complement", 574061),)
    assert report["staircase_members"] == (
        (0, "direct", (4, 3, 2, 3, 2, 1)),
        (0, "complement", (0, 1, 2, 1, 2, 3)),
    )
    assert report["integral_residual_lengths_1_to_64"] == tuple(range(8, 65, 8))
    assert report["length_producing_21_bytes"] == 24
    print("[*] self-test OK: complete URL bit-plane transpose and residual inventory reproduce")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    report = audit()
    print("[*] bit planes (MSB to LSB):")
    for row in report["planes"]:
        print(
            f"    bit {row['bit_index']}: {row['hex']} weight={row['weight']} "
            f"complement={row['complement_hex']} "
            f"prime={row['prime']}/{row['complement_prime']}"
        )
    print(
        f"[*] residual: {report['residual_dimensions'][0]}x"
        f"{report['residual_dimensions'][1]}={report['residual_bit_count']} bits="
        f"{report['residual_byte_count']} bytes"
    )
    print(f"[*] plane-major:     {report['plane_major_hex']} {report['plane_major_printable']}")
    print(f"[*] character-major: {report['character_major_hex']} {report['character_major_printable']}")
    print(f"[*] weight-9 members: {report['weight_9_members']}")
    print(f"[*] prime members: {report['prime_members']}")
    print(f"[*] staircase members: {report['staircase_members']}")
    print(
        "[*] verdict: the 21-byte residual and lossless reconstruction are "
        "exact but length-forced. Neither natural traversal is plaintext. "
        "Only the colored LSB polarity supplies a prime, and only that plane "
        "supplies the unit nibble staircase; weight 9 alone is not unique."
    )
    if args.self_test:
        self_test()


if __name__ == "__main__":
    main()
