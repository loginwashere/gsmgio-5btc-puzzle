#!/usr/bin/env python3
"""Audit the final low-priority overlay, DNA, and RGB-vector hypotheses.

Only bounded, predeclared convention families are evaluated.  The overlay
audit counts target/orientation/aperture choices and checks native 14x14
registration.  The DNA audit exhausts distinct blue/yellow-to-base mappings,
directions, and circular codon frames.  The RGB audit computes ordinary vector
quantities and corrects the proposed modulo-letter mapping.

No visual-feature reading, language scoring, password test, or blob oracle is
run when the corresponding selection gate fails.
"""

import argparse
import hashlib
import math
from itertools import permutations
from pathlib import Path

from PIL import Image

from first_piece_color_reconstruction import DEFAULT_IMAGE, reconstruct


REPO_ROOT = Path(__file__).resolve().parents[2]
OVERLAY_TARGETS = (
    REPO_ROOT / "phase2.png",
    REPO_ROOT / "phase3.png",
    REPO_ROOT / "SalPhaselonCosmicDuality.png",
)
GRID_SIZE = 14
ROSE = (247, 61, 146)
FEFE = (254, 254, 254)
SUM_LIST = (23, 16, 7)

GENETIC_CODE = {
    codon: amino
    for amino, codons in {
        "F": ("TTT", "TTC"), "L": ("TTA", "TTG", "CTT", "CTC", "CTA", "CTG"),
        "I": ("ATT", "ATC", "ATA"), "M": ("ATG",),
        "V": ("GTT", "GTC", "GTA", "GTG"),
        "S": ("TCT", "TCC", "TCA", "TCG", "AGT", "AGC"),
        "P": ("CCT", "CCC", "CCA", "CCG"),
        "T": ("ACT", "ACC", "ACA", "ACG"),
        "A": ("GCT", "GCC", "GCA", "GCG"),
        "Y": ("TAT", "TAC"), "*": ("TAA", "TAG", "TGA"),
        "H": ("CAT", "CAC"), "Q": ("CAA", "CAG"),
        "N": ("AAT", "AAC"), "K": ("AAA", "AAG"),
        "D": ("GAT", "GAC"), "E": ("GAA", "GAG"),
        "C": ("TGT", "TGC"), "W": ("TGG",),
        "R": ("CGT", "CGC", "CGA", "CGG", "AGA", "AGG"),
        "G": ("GGT", "GGC", "GGA", "GGG"),
    }.items()
    for codon in codons
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def d4_coordinate(row, column, transform, size=GRID_SIZE):
    if transform >= 4:
        column = size - 1 - column
        transform -= 4
    for _ in range(transform):
        row, column = column, size - 1 - row
    return row, column


def transformed_sets(coordinates):
    return tuple(
        tuple(sorted(d4_coordinate(row, column, transform) for row, column in coordinates))
        for transform in range(8)
    )


def overlay_audit(color_report):
    yellow = tuple(
        (item["row_0"], item["column_0"])
        for item in color_report["objects"]
        if item["color"] == "yellow"
    )
    fefe = ((color_report["fefe"]["row_1"] - 1, color_report["fefe"]["column_1"] - 1),)
    aperture_sets = {"yellow": yellow, "fefe": fefe, "union": yellow + fefe}
    targets = []
    for path in OVERLAY_TARGETS:
        with Image.open(path) as image:
            size = image.size
        width, height = size
        targets.append(
            {
                "path": str(path),
                "sha256": sha256(path),
                "size": size,
                "width_divisible_by_14": width % GRID_SIZE == 0,
                "height_divisible_by_14": height % GRID_SIZE == 0,
                "native_equal_cell_tiling": width % GRID_SIZE == height % GRID_SIZE == 0,
            }
        )
    transformed = {name: transformed_sets(coords) for name, coords in aperture_sets.items()}
    return {
        "yellow_coordinates": yellow,
        "fefe_coordinate": fefe[0],
        "aperture_sizes": {name: len(coords) for name, coords in aperture_sets.items()},
        "unique_d4_masks": {name: len(set(rows)) for name, rows in transformed.items()},
        "targets": tuple(targets),
        "minimum_target_aperture_orientation_family": (
            len(targets) * sum(len(set(rows)) for rows in transformed.values())
        ),
        "registration_rules_counted": 1,
        "registration_rule": "fit full image to 14x14 normalized cells",
        "alternative_crop_contain_cover_offsets_unbounded": True,
        "native_registration_selected": False,
        "visual_feature_decoder_selected": False,
        "pass": False,
    }


def translate(dna):
    return "".join(GENETIC_CODE[dna[index:index + 3]] for index in range(0, len(dna), 3))


def dna_audit(mask):
    rows = []
    for blue_base, yellow_base in permutations("ACGT", 2):
        forward = mask.translate(str.maketrans({"B": blue_base, "Y": yellow_base}))
        for direction, dna in (("forward", forward), ("reverse", forward[::-1])):
            for frame in range(3):
                circular = dna[frame:] + dna[:frame]
                rows.append(
                    {
                        "blue": blue_base,
                        "yellow": yellow_base,
                        "direction": direction,
                        "circular_frame": frame,
                        "dna": circular,
                        "amino": translate(circular),
                    }
                )
    proposed = next(
        row for row in rows
        if (row["blue"], row["yellow"], row["direction"], row["circular_frame"])
        == ("G", "T", "forward", 0)
    )
    return {
        "endpoint_symbols": len(mask),
        "endpoint_palette_states": tuple(sorted(set(mask))),
        "endpoint_information_bits": len(mask),
        "endpoint_packed_bytes": len(mask) // 8,
        "four_state_2bit_packed_bytes": len(mask) * 2 // 8,
        "claimed_twelve_byte_pair_output_correct": False,
        "full_grid_has_fifth_fefe_state": True,
        "base_assignment_count": 12,
        "direction_count": 2,
        "circular_frame_count": 3,
        "family_size": len(rows),
        "unique_dna_sequences": len({row["dna"] for row in rows}),
        "unique_amino_sequences": len({row["amino"] for row in rows}),
        "proposed_mapping": proposed,
        "reverse_complement_adds_independent_mapping_family": False,
        "mapping_selected": False,
        "codon_frame_selected": False,
        "amino_consumer_selected": False,
        "pass": False,
    }


def letters_zero_based(values):
    return "".join(chr(ord("A") + value % 26) for value in values)


def letters_one_based(values):
    return "".join(chr(ord("A") + (value - 1) % 26) for value in values)


def is_prime(number):
    if number < 2:
        return False
    return all(number % divisor for divisor in range(2, math.isqrt(number) + 1))


def rgb_audit():
    difference = tuple(marker - rose for marker, rose in zip(FEFE, ROSE))
    reverse_difference = tuple(-value for value in difference)
    absolute_difference = tuple(abs(value) for value in difference)
    rose_mod26 = tuple(value % 26 for value in ROSE)
    difference_mod26 = tuple(value % 26 for value in difference)
    plus_shifts = tuple((value + shift) % 26 for value, shift in zip(rose_mod26, SUM_LIST))
    minus_shifts = tuple((value - shift) % 26 for value, shift in zip(rose_mod26, SUM_LIST))

    grayscale_rows = []
    for gray in range(256):
        delta = (gray - ROSE[0], gray - ROSE[1], gray - ROSE[2])
        grayscale_rows.append(
            {
                "gray": gray,
                "difference": delta,
                "red_equals_7": delta[0] == 7,
                "green_prime": is_prime(delta[1]),
                "blue_printable_ascii": 32 <= delta[2] <= 126,
            }
        )
    return {
        "rose": ROSE,
        "fefe": FEFE,
        "difference": difference,
        "reverse_difference": reverse_difference,
        "absolute_difference": absolute_difference,
        "difference_sum": sum(difference),
        "difference_squared_norm": sum(value * value for value in difference),
        "difference_norm": math.sqrt(sum(value * value for value in difference)),
        "rose_dot_fefe": sum(left * right for left, right in zip(ROSE, FEFE)),
        "channel_properties": {
            "red_matches_sum_list_7": difference[0] == SUM_LIST[-1],
            "green_is_prime": is_prime(difference[1]),
            "blue_is_printable_ascii": 32 <= difference[2] <= 126,
            "blue_ascii": chr(difference[2]),
        },
        "grayscale_calibration": {
            "family_size": len(grayscale_rows),
            "red_equals_7_count": sum(row["red_equals_7"] for row in grayscale_rows),
            "joint_property_count": sum(
                row["red_equals_7"] and row["green_prime"] and row["blue_printable_ascii"]
                for row in grayscale_rows
            ),
            "posthoc_valid_p_value": False,
        },
        "rose_mod26": rose_mod26,
        "rose_mod26_a0": letters_zero_based(rose_mod26),
        "rose_mod26_a1": letters_one_based(rose_mod26),
        "claimed_niq_consistent": False,
        "difference_mod26": difference_mod26,
        "difference_mod26_a0": letters_zero_based(difference_mod26),
        "difference_mod26_a1": letters_one_based(difference_mod26),
        "plus_sum_list_a0": letters_zero_based(plus_shifts),
        "minus_sum_list_a0": letters_zero_based(minus_shifts),
        "vector_operation_selected": False,
        "alphabet_indexing_selected": False,
        "consumer_selected": False,
        "pass": False,
    }


def audit():
    color_report = reconstruct(DEFAULT_IMAGE)
    return {
        "overlay": overlay_audit(color_report),
        "dna": dna_audit(color_report["color_sequence"]),
        "rgb": rgb_audit(),
        "oracle_run": False,
    }


def self_test():
    report = audit()
    overlay = report["overlay"]
    dna = report["dna"]
    rgb = report["rgb"]

    assert overlay["aperture_sizes"] == {"yellow": 9, "fefe": 1, "union": 10}
    assert overlay["unique_d4_masks"] == {"yellow": 8, "fefe": 8, "union": 8}
    assert tuple(row["size"] for row in overlay["targets"]) == (
        (812, 415), (812, 893), (668, 619)
    )
    assert not any(row["native_equal_cell_tiling"] for row in overlay["targets"])
    assert overlay["minimum_target_aperture_orientation_family"] == 72
    assert overlay["pass"] is False
    assert dna["endpoint_symbols"] == 24
    assert dna["endpoint_palette_states"] == ("B", "Y")
    assert dna["endpoint_packed_bytes"] == 3
    assert dna["four_state_2bit_packed_bytes"] == 6
    assert dna["family_size"] == 72
    assert dna["proposed_mapping"]["dna"] == "GGGGTGGGTTGGGGTGGTTGTTGT"
    assert dna["proposed_mapping"]["amino"] == "GVGWGGCC"
    assert dna["pass"] is False
    assert rgb["difference"] == (7, 193, 108)
    assert rgb["difference_sum"] == 308
    assert rgb["difference_squared_norm"] == 48962
    assert rgb["channel_properties"]["green_is_prime"] is True
    assert rgb["channel_properties"]["blue_ascii"] == "l"
    assert rgb["grayscale_calibration"]["red_equals_7_count"] == 1
    assert rgb["grayscale_calibration"]["joint_property_count"] == 1
    assert rgb["rose_mod26"] == (13, 9, 16)
    assert rgb["rose_mod26_a0"] == "NJQ"
    assert rgb["rose_mod26_a1"] == "MIP"
    assert rgb["claimed_niq_consistent"] is False
    assert rgb["difference_mod26_a0"] == "HLE"
    assert rgb["plus_sum_list_a0"] == "KZX"
    assert rgb["minus_sum_list_a0"] == "QTJ"
    assert rgb["pass"] is False
    assert report["oracle_run"] is False
    print("[*] self-test OK: overlay/DNA/RGB families reproduce; all gates fail")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    report = audit()
    if args.self_test:
        self_test()
        return
    print(report)


if __name__ == "__main__":
    main()
