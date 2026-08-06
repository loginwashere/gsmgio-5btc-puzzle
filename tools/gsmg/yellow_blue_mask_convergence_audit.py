#!/usr/bin/env python3
"""HISTORICAL PHASE-47 MODEL, superseded by Phase 48.

This module remains reproducible for audit history, but its primary
construction is wrong: FEFE is a separate event before color object 21, not
the object to remove. Do not use its distance-2 swap as a current puzzle
conclusion; use ``flo_prime_walk_provenance_audit.py`` instead.

Exact audit of the first-piece color sequence against Denis's DBBI mask.

This combines only previously fixed observations:

* the first piece has the asserted 24-object color sequence (15 blue, 9 yellow);
* FEFE addresses character/object 21, whose color is yellow and whose marked
  bit is zero;
* Denis described blue as ``B`` and yellow as ``BE``;
* his exact 31-character extraction has four possible source-position masks.

The primary construction removes the pre-addressed yellow object 21, then
encodes blue -> ``b`` and yellow -> ``be``.  Its expanded 31-symbol string is
compared with the DBBI symbols selected by all four recovered masks.  The
family-wise statistic is the minimum equal-length Hamming distance across all
four masks.

The exact null conditions on the facts needed to obtain a 31-symbol encoding:
after removing the already-addressed yellow object, the remaining 23 positions
contain 15 blue and 8 yellow objects.  Every one of C(23, 8) arrangements is
enumerated, encoded, and scored against the same four-mask family.

The observed distance is produced by one adjacent swap of the final color
objects 22 and 23 (reduced-sequence positions 21 and 22).  That swap was noticed
after comparison and has no creator-supported operation, so it is reported as
an unresolved discrepancy, not applied inside the primary statistic and not
used to justify cipher/AES escalation.
"""

import argparse
import itertools
from collections import Counter
from math import comb

from data import DBBI
from denis_prime_extraction_audit import SOURCE, TARGET, recover_position_masks
from first_piece_color_reconstruction import DEFAULT_IMAGE, reconstruct

BLUE_TOKEN = "b"
YELLOW_TOKEN = "be"
EXPECTED_REDUCED_COLORS = "BBBBYBBBYYBBBBYBBYYBYBY"
EXPECTED_ENCODED_COLORS = "bbbbbebbbbebebbbbbebbbebebbebbe"
EXPECTED_MASK_COLORS = "BBBBYBBBYYBBBBYBBYYBBYY"
EXPECTED_MASK_PATTERN = "bbbbbebbbbebebbbbbebbbebebbbebe"
EXPECTED_NULL_TOTAL = 490_314
EXPECTED_NULL_AT_LEAST_AS_CLOSE = 90


def encode_colors(colors):
    if any(color not in "BY" for color in colors):
        raise ValueError(f"colors must contain only B/Y: {colors!r}")
    return "".join(BLUE_TOKEN if color == "B" else YELLOW_TOKEN for color in colors)


def decode_be_pattern(pattern):
    """Decode the prefix-free-in-context B->b, Y->be representation."""
    colors = []
    index = 0
    while index < len(pattern):
        if pattern[index] != "b":
            raise ValueError(f"pattern is not a B/BE stream at offset {index}: {pattern!r}")
        if index + 1 < len(pattern) and pattern[index + 1] == "e":
            colors.append("Y")
            index += 2
        else:
            colors.append("B")
            index += 1
    return "".join(colors)


def hamming_distance(left, right):
    if len(left) != len(right):
        raise ValueError(f"Hamming distance requires equal lengths: {len(left)} != {len(right)}")
    return sum(a != b for a, b in zip(left, right))


def recovered_mask_patterns():
    masks = recover_position_masks(SOURCE, TARGET)
    patterns = tuple("".join(DBBI[index] for index in mask) for mask in masks)
    if len(patterns) != 4 or any(len(pattern) != len(TARGET) for pattern in patterns):
        raise AssertionError("unexpected recovered-mask family")
    return masks, patterns


def minimum_family_distance(encoded, patterns):
    distances = tuple(hamming_distance(encoded, pattern) for pattern in patterns)
    return min(distances), distances


def exact_conditioned_null(patterns, observed_distance):
    """Enumerate every 23-position arrangement with 15 B and 8 Y objects."""
    position_count = 23
    yellow_count = 8
    distance_counts = Counter()
    for yellow_positions in itertools.combinations(range(position_count), yellow_count):
        yellow_set = set(yellow_positions)
        colors = "".join(
            "Y" if position in yellow_set else "B"
            for position in range(position_count)
        )
        encoded = encode_colors(colors)
        distance, _ = minimum_family_distance(encoded, patterns)
        distance_counts[distance] += 1

    total = sum(distance_counts.values())
    at_least_as_close = sum(
        count for distance, count in distance_counts.items()
        if distance <= observed_distance
    )
    if total != comb(position_count, yellow_count):
        raise AssertionError(f"null enumeration mismatch: {total}")
    return {
        "total": total,
        "at_least_as_close": at_least_as_close,
        "rate": at_least_as_close / total,
        "distance_counts": dict(sorted(distance_counts.items())),
    }


def audit():
    reconstruction = reconstruct(DEFAULT_IMAGE)
    colors = reconstruction["color_sequence"]
    addressed_index = reconstruction["fefe"]["character_0"]
    addressed_object = reconstruction["objects"][addressed_index]

    if addressed_object["ordinal_1"] != 21 or addressed_object["color"] != "yellow":
        raise AssertionError(f"unexpected addressed color object: {addressed_object}")
    if reconstruction["fefe"]["value"] != 0:
        raise AssertionError("FEFE marker is not zero")

    reduced_colors = colors[:addressed_index] + colors[addressed_index + 1:]
    encoded_colors = encode_colors(reduced_colors)
    masks, patterns = recovered_mask_patterns()
    observed_distance, distances = minimum_family_distance(encoded_colors, patterns)

    be_only = [
        index for index, pattern in enumerate(patterns)
        if set(pattern) <= {"b", "e"}
    ]
    if len(be_only) != 1:
        raise AssertionError(f"expected one B/BE-compatible mask, got {be_only}")
    compatible_index = be_only[0]
    compatible_pattern = patterns[compatible_index]
    compatible_colors = decode_be_pattern(compatible_pattern)

    color_differences = [
        (index + 1, real, candidate)
        for index, (real, candidate) in enumerate(
            zip(reduced_colors, compatible_colors)
        )
        if real != candidate
    ]
    swapped_colors = list(reduced_colors)
    swapped_colors[20], swapped_colors[21] = swapped_colors[21], swapped_colors[20]
    adjacent_swap_matches = encode_colors("".join(swapped_colors)) == compatible_pattern

    null = exact_conditioned_null(patterns, observed_distance)
    return {
        "original_colors": colors,
        "addressed_object": addressed_object,
        "reduced_colors": reduced_colors,
        "encoded_colors": encoded_colors,
        "masks": masks,
        "patterns": patterns,
        "pattern_counts": tuple(Counter(pattern) for pattern in patterns),
        "distances": distances,
        "observed_distance": observed_distance,
        "compatible_index": compatible_index,
        "compatible_pattern": compatible_pattern,
        "compatible_colors": compatible_colors,
        "color_differences": color_differences,
        "adjacent_swap_matches": adjacent_swap_matches,
        "null": null,
    }


def self_test():
    for colors in ("B", "Y", "BBYBY", "YBYBBYY"):
        assert decode_be_pattern(encode_colors(colors)) == colors

    result = audit()
    assert result["reduced_colors"] == EXPECTED_REDUCED_COLORS
    assert result["encoded_colors"] == EXPECTED_ENCODED_COLORS
    assert result["compatible_pattern"] == EXPECTED_MASK_PATTERN
    assert result["compatible_colors"] == EXPECTED_MASK_COLORS
    assert result["pattern_counts"][result["compatible_index"]] == Counter({"b": 23, "e": 8})
    assert result["observed_distance"] == 2
    assert result["color_differences"] == [(21, "Y", "B"), (22, "B", "Y")]
    assert result["adjacent_swap_matches"]
    assert result["null"]["total"] == EXPECTED_NULL_TOTAL
    assert result["null"]["at_least_as_close"] == EXPECTED_NULL_AT_LEAST_AS_CLOSE
    assert result["null"]["distance_counts"][0] == 1
    print(
        "[*] self-test OK: unique B/BE mask, distance-2 adjacent-swap "
        "discrepancy, and exact conditioned null verified"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    print(
        "[!] HISTORICAL PHASE-47 MODEL: superseded by FEFE insertion in "
        "flo_prime_walk_provenance_audit.py"
    )
    self_test()
    if args.self_test:
        return

    result = audit()
    addressed = result["addressed_object"]
    print(
        f"[*] first-piece colors: {result['original_colors']} "
        f"(B={result['original_colors'].count('B')}, "
        f"Y={result['original_colors'].count('Y')})"
    )
    print(
        f"[*] addressed object: ordinal={addressed['ordinal_1']} "
        f"character={addressed['character']!r} color={addressed['color']} "
        "(removed before B/BE encoding)"
    )
    print(f"[*] reduced colors: {result['reduced_colors']}")
    print(
        f"[*] B->b, Y->be: {result['encoded_colors']} "
        f"(b={result['encoded_colors'].count('b')}, "
        f"e={result['encoded_colors'].count('e')})"
    )

    print("\n[*] recovered-mask DBBI patterns:")
    for index, (pattern, counts, distance) in enumerate(
        zip(result["patterns"], result["pattern_counts"], result["distances"])
    ):
        compatible = " B/BE-compatible" if index == result["compatible_index"] else ""
        print(
            f"    mask={index} pattern={pattern} counts={dict(counts)} "
            f"hamming={distance}{compatible}"
        )

    print(f"\n[*] compatible mask decoded as colors: {result['compatible_colors']}")
    print(f"[*] color differences (reduced ordinal, real, mask): {result['color_differences']}")
    print(
        "[*] swapping reduced color positions 21/22 "
        "(original objects 22/23) gives an exact match: "
        f"{result['adjacent_swap_matches']}"
    )
    print(
        "    This swap is observed after comparison and remains unsupported; "
        "it is not applied in the primary statistic."
    )

    null = result["null"]
    print("\n[*] exact conditioned 15B/8Y null, minimum across all four masks:")
    print(f"    distance distribution: {null['distance_counts']}")
    print(
        f"    distance <= {result['observed_distance']}: "
        f"{null['at_least_as_close']}/{null['total']} = {null['rate']:.9f}"
    )
    print(
        "    Descriptive family-wise calibration only: the convergence was "
        "noticed after prior puzzle exploration, not pre-registered as a discovery test."
    )
    print("[*] no AES/cipher escalation: the unresolved adjacent swap prevents an exact rule")


if __name__ == "__main__":
    main()
