#!/usr/bin/env python3
"""Audit Point 17's two aligned #383838 shadow rails column by column.

Only the predeclared operations are included: larger/smaller count selection,
explicit tie handling, equality/comparison masks, column sums, and signed or
absolute differences.  The lower count multiset is also reassigned over the
fixed upper columns to calibrate recognized aggregate profiles.  No cipher,
word-list, element parser, or cryptographic oracle is run.
"""

import argparse
from collections import Counter
from fractions import Fraction

from PIL import Image

from first_piece_second_matrixsumlist_audit import sampled_shadow_rows
from stage0_footer_palette_layer_audit import (
    ADDRESS,
    ADDRESS_X,
    ADDRESS_Y,
    BANNER,
    BANNER_X,
    BANNER_Y,
    IMAGE_PATH,
    TARGET,
    glyph_histograms,
)


def multiset_permutations(values):
    counts = Counter(values)
    ordered = tuple(sorted(counts))
    output = [None] * len(values)

    def walk(index):
        if index == len(output):
            yield tuple(output)
            return
        for value in ordered:
            if not counts[value]:
                continue
            counts[value] -= 1
            output[index] = value
            yield from walk(index + 1)
            counts[value] += 1

    yield from walk(0)


def a1z26(values):
    if not all(1 <= value <= 26 for value in values):
        return None
    return "".join(chr(64 + value) for value in values)


def choose_by_count(upper_text, lower_text, upper_counts, lower_counts, larger):
    strict = []
    template = []
    ties = []
    for column, (upper_char, lower_char, upper, lower) in enumerate(
        zip(upper_text, lower_text, upper_counts, lower_counts), start=1
    ):
        if upper == lower:
            template.append("=")
            ties.append(
                {
                    "column_1": column,
                    "upper_character": upper_char,
                    "lower_character": lower_char,
                    "count": upper,
                }
            )
            continue
        choose_upper = upper > lower if larger else upper < lower
        chosen = upper_char if choose_upper else lower_char
        strict.append(chosen)
        template.append(chosen)

    candidates = []
    for selector in range(1 << len(ties)):
        characters = list(template)
        tie_choices = []
        for tie_index, tie in enumerate(ties):
            choose_lower = bool(selector & (1 << tie_index))
            character = (
                tie["lower_character"] if choose_lower else tie["upper_character"]
            )
            characters[tie["column_1"] - 1] = character
            tie_choices.append("lower" if choose_lower else "upper")
        candidates.append(
            {
                "tie_choices": tuple(tie_choices),
                "text": "".join(characters),
            }
        )
    return {
        "strict_unequal_text": "".join(strict),
        "tie_template": "".join(template),
        "ties": tuple(ties),
        "tie_resolved_candidates": tuple(candidates),
    }


def numeric_profile(upper_counts, lower_counts):
    signed = tuple(upper - lower for upper, lower in zip(upper_counts, lower_counts))
    absolute = tuple(abs(value) for value in signed)
    sums = tuple(upper + lower for upper, lower in zip(upper_counts, lower_counts))
    equality = tuple(int(value == 0) for value in signed)
    upper_wins = tuple(int(value > 0) for value in signed)
    lower_wins = tuple(int(value < 0) for value in signed)
    signs = "".join("+" if value > 0 else "-" if value < 0 else "0" for value in signed)
    return {
        "column_sums": sums,
        "column_sum_digits": "".join(str(value) for value in sums),
        "column_sums_a1z26": a1z26(sums),
        "signed_differences": signed,
        "comparison_signs": signs,
        "absolute_differences": absolute,
        "absolute_difference_digits": "".join(str(value) for value in absolute),
        "equality_mask": equality,
        "equality_mask_bits": "".join(str(value) for value in equality),
        "equality_mask_integer": int("".join(str(value) for value in equality), 2),
        "upper_win_mask": upper_wins,
        "lower_win_mask": lower_wins,
        "upper_win_count": sum(upper_wins),
        "lower_win_count": sum(lower_wins),
        "tie_count": sum(equality),
        "sum_total": sum(sums),
        "signed_difference_total": sum(signed),
        "absolute_difference_total": sum(absolute),
    }


def alignment_calibration(upper_counts, lower_counts, observed):
    distribution = Counter()
    family_size = 0
    for permuted_lower in multiset_permutations(lower_counts):
        profile = numeric_profile(upper_counts, permuted_lower)
        key = (
            profile["absolute_difference_total"],
            profile["tie_count"],
            profile["upper_win_count"],
            profile["lower_win_count"],
        )
        distribution[key] += 1
        family_size += 1
    observed_key = (
        observed["absolute_difference_total"],
        observed["tie_count"],
        observed["upper_win_count"],
        observed["lower_win_count"],
    )
    abs_total_count = sum(
        count for key, count in distribution.items() if key[0] == observed_key[0]
    )
    tie_count = sum(
        count for key, count in distribution.items() if key[1] == observed_key[1]
    )
    abs_and_tie_count = sum(
        count for key, count in distribution.items() if key[:2] == observed_key[:2]
    )
    full_profile_count = distribution[observed_key]
    return {
        "family_size": family_size,
        "observed_profile": observed_key,
        "absolute_total_count": abs_total_count,
        "absolute_total_rate": Fraction(abs_total_count, family_size),
        "tie_count_count": tie_count,
        "tie_count_rate": Fraction(tie_count, family_size),
        "absolute_and_tie_count": abs_and_tie_count,
        "absolute_and_tie_rate": Fraction(abs_and_tie_count, family_size),
        "full_profile_count": full_profile_count,
        "full_profile_rate": Fraction(full_profile_count, family_size),
        "posthoc_valid_p_value": False,
    }


def selected_geometry(image, text, boxes, y_box):
    histograms = glyph_histograms(image, text, boxes, y_box)
    return tuple(
        {
            "source_glyph_ordinal_1": ordinal,
            "character": character,
            "count": histogram[TARGET],
            "x_box": box,
            "x_center": (box[0] + box[1]) / 2,
        }
        for ordinal, (character, box, histogram) in enumerate(
            zip(text, boxes, histograms), start=1
        )
        if histogram[TARGET]
    )


def spatial_alignment():
    image = Image.open(IMAGE_PATH).convert("RGB")
    upper = selected_geometry(image, BANNER, BANNER_X, BANNER_Y)
    lower = selected_geometry(image, ADDRESS, ADDRESS_X, ADDRESS_Y)
    center_deltas = tuple(
        lower_row["x_center"] - upper_row["x_center"]
        for upper_row, lower_row in zip(upper, lower)
    )
    overlap_count = sum(
        max(upper_row["x_box"][0], lower_row["x_box"][0])
        < min(upper_row["x_box"][1], lower_row["x_box"][1])
        for upper_row, lower_row in zip(upper, lower)
    )
    return {
        "upper": upper,
        "lower": lower,
        "ordinal_pair_x_center_deltas": center_deltas,
        "ordinal_pair_x_overlap_count": overlap_count,
        "constant_x_offset": len(set(center_deltas)) == 1,
        "physical_vertical_columns": overlap_count == len(upper),
        "alignment_basis": "selected-glyph ordinal only",
    }


def audit():
    rows = sampled_shadow_rows()
    upper, lower = rows
    upper_text, lower_text = upper["selected"], lower["selected"]
    upper_counts, lower_counts = upper["counts"], lower["counts"]
    if not (
        len(upper_text) == len(lower_text) == len(upper_counts) == len(lower_counts) == 11
    ):
        raise AssertionError("shadow rails are no longer aligned 11-column rows")

    numeric = numeric_profile(upper_counts, lower_counts)
    larger = choose_by_count(
        upper_text, lower_text, upper_counts, lower_counts, larger=True
    )
    smaller = choose_by_count(
        upper_text, lower_text, upper_counts, lower_counts, larger=False
    )
    calibration = alignment_calibration(upper_counts, lower_counts, numeric)
    geometry = spatial_alignment()

    return {
        "source": {
            "upper_text": upper_text,
            "lower_text": lower_text,
            "upper_counts": upper_counts,
            "lower_counts": lower_counts,
            "column_count": len(upper_text),
            "upper_total": sum(upper_counts),
            "lower_total": sum(lower_counts),
        },
        "larger_count_selection": larger,
        "smaller_count_selection": smaller,
        "numeric_operations": numeric,
        "alignment_calibration": calibration,
        "spatial_alignment": geometry,
        "cross_checks": {
            "sum_total_is_shadow_total_43": numeric["sum_total"] == 43,
            "signed_total_is_row_difference_7": numeric["signed_difference_total"] == 7,
            "absolute_total_matches_prior_residue_count_13": numeric["absolute_difference_total"] == 13,
            "sum_and_signed_totals_forced_by_row_totals": True,
            "absolute_total_forced_by_row_totals": False,
        },
        "verdict": {
            "larger_selection_is_plaintext": False,
            "smaller_selection_is_plaintext": False,
            "numeric_lists_are_plaintext": False,
            "column_alignment_yields_selected_consumer": False,
        },
        "oracle_run": False,
    }


def self_test():
    report = audit()
    source = report["source"]
    larger = report["larger_count_selection"]
    smaller = report["smaller_count_selection"]
    numeric = report["numeric_operations"]
    calibration = report["alignment_calibration"]
    geometry = report["spatial_alignment"]

    assert source == {
        "upper_text": "GSGO5BCPUCG",
        "lower_text": "GMGC9g2cPBe",
        "upper_counts": (4, 1, 4, 4, 2, 1, 1, 1, 2, 1, 4),
        "lower_counts": (2, 1, 2, 2, 1, 3, 1, 1, 1, 2, 2),
        "column_count": 11,
        "upper_total": 25,
        "lower_total": 18,
    }
    assert larger["strict_unequal_text"] == "GGO5gUBG"
    assert larger["tie_template"] == "G=GO5g==UBG"
    assert tuple(row["text"] for row in larger["tie_resolved_candidates"]) == (
        "GSGO5gCPUBG", "GMGO5gCPUBG", "GSGO5g2PUBG", "GMGO5g2PUBG",
        "GSGO5gCcUBG", "GMGO5gCcUBG", "GSGO5g2cUBG", "GMGO5g2cUBG",
    )
    assert smaller["strict_unequal_text"] == "GGC9BPCe"
    assert smaller["tie_template"] == "G=GC9B==PCe"
    assert numeric["column_sums"] == (6, 2, 6, 6, 3, 4, 2, 2, 3, 3, 6)
    assert numeric["column_sum_digits"] == "62663422336"
    assert numeric["column_sums_a1z26"] == "FBFFCDBBCCF"
    assert numeric["signed_differences"] == (2, 0, 2, 2, 1, -2, 0, 0, 1, -1, 2)
    assert numeric["comparison_signs"] == "+0+++-00+-+"
    assert numeric["absolute_differences"] == (2, 0, 2, 2, 1, 2, 0, 0, 1, 1, 2)
    assert numeric["absolute_difference_digits"] == "20221200112"
    assert numeric["equality_mask_bits"] == "01000011000"
    assert numeric["equality_mask_integer"] == 536
    assert (numeric["upper_win_count"], numeric["lower_win_count"], numeric["tie_count"]) == (6, 2, 3)
    assert (numeric["sum_total"], numeric["signed_difference_total"], numeric["absolute_difference_total"]) == (43, 7, 13)
    assert calibration["family_size"] == 2772
    assert calibration["absolute_total_count"] == 900
    assert calibration["tie_count_count"] == 840
    assert calibration["absolute_and_tie_count"] == 340
    assert calibration["full_profile_count"] == 20
    assert calibration["absolute_total_rate"] == Fraction(25, 77)
    assert calibration["tie_count_rate"] == Fraction(10, 33)
    assert calibration["absolute_and_tie_rate"] == Fraction(85, 693)
    assert calibration["full_profile_rate"] == Fraction(5, 693)
    assert calibration["posthoc_valid_p_value"] is False
    assert tuple(row["source_glyph_ordinal_1"] for row in geometry["upper"]) == (
        1, 2, 4, 6, 7, 8, 10, 11, 12, 17, 24,
    )
    assert tuple(row["source_glyph_ordinal_1"] for row in geometry["lower"]) == (
        2, 4, 5, 8, 9, 19, 21, 23, 26, 33, 34,
    )
    assert geometry["ordinal_pair_x_center_deltas"] == (
        78.0, 97.0, 52.0, 45.0, 21.5, 201.5, 176.0, 172.5, 207.5, 214.0, 35.0,
    )
    assert geometry["ordinal_pair_x_overlap_count"] == 0
    assert geometry["constant_x_offset"] is False
    assert geometry["physical_vertical_columns"] is False
    assert report["oracle_run"] is False
    print("[*] self-test OK: 11-column larger/smaller, masks, sums, and differences reproduce")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    report = audit()
    larger = report["larger_count_selection"]
    smaller = report["smaller_count_selection"]
    numeric = report["numeric_operations"]
    calibration = report["alignment_calibration"]
    geometry = report["spatial_alignment"]

    print(f"[*] larger strict/template: {larger['strict_unequal_text']} / {larger['tie_template']}")
    print(f"[*] smaller strict/template: {smaller['strict_unequal_text']} / {smaller['tie_template']}")
    print(f"[*] sums: {numeric['column_sums']} -> {numeric['column_sum_digits']} -> {numeric['column_sums_a1z26']}")
    print(f"[*] signed/absolute: {numeric['signed_differences']} / {numeric['absolute_difference_digits']}")
    print(f"[*] equality mask: {numeric['equality_mask_bits']} = {numeric['equality_mask_integer']}")
    print(f"[*] spatial alignment: {geometry['alignment_basis']}; overlap={geometry['ordinal_pair_x_overlap_count']}/11; constant offset={geometry['constant_x_offset']}")
    print(f"[*] alignment calibration: {calibration}")
    print("[*] verdict: bounded column operations reproduce exactly but yield no selected plaintext or consumer")
    if args.self_test:
        self_test()


if __name__ == "__main__":
    main()
