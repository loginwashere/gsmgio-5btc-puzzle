#!/usr/bin/env python3
"""Audit Denis Golovkin's rabbit-half-plus-three DBBI mask relation.

Messages 60575, 67215, and 68819 propose that the 24-bit first-piece color
mask is halved and then incremented by Trinity (3) to obtain the 23-bit DBBI
prime-endpoint color mask.  The arithmetic is exact.  This module also makes
its evidentiary boundary explicit: the equality is algebraically equivalent
to the already-known 20-bit common prefix plus the two fixed three-bit tails,
so it is not an independent confirmation of the fitted DBBI segmentation.
"""

from first_piece_color_reconstruction import EXPECTED_COLOR_SEQUENCE
from telegram_yellow_blue_guide_audit import EXPECTED_PRIME_COLORS


def bits(colors: str) -> str:
    return "".join("1" if color == "B" else "0" for color in colors)


def audit():
    rabbit_bits = bits(EXPECTED_COLOR_SEQUENCE)
    dbbi_bits = bits(EXPECTED_PRIME_COLORS)
    rabbit_value = int(rabbit_bits, 2)
    dbbi_value = int(dbbi_bits, 2)
    halved = rabbit_value // 2
    shifted_rabbit_bits = rabbit_bits[:-1]
    common_prefix_length = 0
    for left, right in zip(shifted_rabbit_bits, dbbi_bits):
        if left != right:
            break
        common_prefix_length += 1
    mismatches = tuple(
        index + 1
        for index, (left, right) in enumerate(zip(shifted_rabbit_bits, dbbi_bits))
        if left != right
    )
    prefix = shifted_rabbit_bits[:common_prefix_length]
    rabbit_tail = shifted_rabbit_bits[common_prefix_length:]
    dbbi_tail = dbbi_bits[common_prefix_length:]
    delta = dbbi_value - halved
    return {
        "rabbit_colors_24": EXPECTED_COLOR_SEQUENCE,
        "rabbit_bits_24": rabbit_bits,
        "rabbit_hex": f"{rabbit_value:06X}",
        "dbbi_prime_colors_23": EXPECTED_PRIME_COLORS,
        "dbbi_bits_23": dbbi_bits,
        "dbbi_hex": f"{dbbi_value:X}",
        "rabbit_floor_half_hex": f"{halved:X}",
        "delta": delta,
        "identity_holds": halved + 3 == dbbi_value,
        "common_prefix_length": common_prefix_length,
        "common_prefix": prefix,
        "shifted_rabbit_tail": rabbit_tail,
        "dbbi_tail": dbbi_tail,
        "mismatch_positions_1_indexed": mismatches,
        "tail_values": {
            "shifted_rabbit": int(rabbit_tail, 2),
            "dbbi": int(dbbi_tail, 2),
            "difference": int(dbbi_tail, 2) - int(rabbit_tail, 2),
        },
        "evidence_boundary": (
            "F73D92//2 + 3 = 7B9ECC is exact, but after the shared 20-bit "
            "prefix is fixed it merely states that the remaining tail changes "
            "from 001 (1) to 100 (4), whose difference is necessarily 3."
        ),
    }


def self_test():
    report = audit()
    assert report["rabbit_hex"] == "F73D92"
    assert report["rabbit_floor_half_hex"] == "7B9EC9"
    assert report["dbbi_hex"] == "7B9ECC"
    assert report["delta"] == 3 and report["identity_holds"]
    assert report["common_prefix_length"] == 20
    assert report["shifted_rabbit_tail"] == "001"
    assert report["dbbi_tail"] == "100"
    assert report["mismatch_positions_1_indexed"] == (21, 23)
    assert report["tail_values"] == {"shifted_rabbit": 1, "dbbi": 4, "difference": 3}
    print(
        "[*] self-test OK: F73D92//2 + 3 = 7B9ECC; 20-bit prefix and "
        "001->100 tail equivalence pinned"
    )


if __name__ == "__main__":
    self_test()
    for key, value in audit().items():
        print(f"{key}: {value}")
