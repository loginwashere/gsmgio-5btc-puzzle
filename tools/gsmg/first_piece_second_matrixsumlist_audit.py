#!/usr/bin/env python3
"""Audit the #383838 count matrix, its [43,25,18] list, and KIT fold.

The footer's independently selected #383838 layer supplies two ordered rows of
11 per-glyph pixel counts.  This module resamples those fixed glyph boxes,
applies the established ``[total,row1,row2]`` matrixsumlist grammar, and then
compares the result with the authenticated ``[23,16,7]`` list.

The proposed componentwise difference is calibrated under row swaps and
direct/reversed reads.  Cross-checks against the first-piece event inventory
are reported, while the additive identity inherited from the two source lists
is explicitly labeled as forced.  No word-list, password, or blob oracle runs.
"""

import argparse
from fractions import Fraction
from itertools import permutations

from PIL import Image

from first_piece_prime_sum_reconstruction import audit as prime_sum_audit
from prime_matrixsum_reconstruction import EXPECTED_PRIME, matrixsumlist
from stage0_footer_palette_layer_audit import (
    ADDRESS,
    ADDRESS_X,
    ADDRESS_Y,
    BANNER,
    BANNER_X,
    BANNER_Y,
    EXPECTED_SHA256,
    IMAGE_PATH,
    TARGET as SHADOW_RGB,
    glyph_histograms,
    render_layer,
    sha256,
)


def matrix_sum_list(rows):
    row_sums = tuple(sum(row) for row in rows)
    return (sum(row_sums), *row_sums)


def a1z26(values):
    if not all(1 <= value <= 26 for value in values):
        return None
    return "".join(chr(64 + value) for value in values)


def sampled_shadow_rows():
    if sha256(IMAGE_PATH) != EXPECTED_SHA256:
        raise AssertionError("Stage-0 image digest drifted")
    image = Image.open(IMAGE_PATH).convert("RGB")
    definitions = (
        ("banner", BANNER, BANNER_X, BANNER_Y),
        ("address", ADDRESS, ADDRESS_X, ADDRESS_Y),
    )
    result = []
    for label, text, boxes, y_box in definitions:
        histograms = glyph_histograms(image, text, boxes, y_box)
        rendered = render_layer(text, histograms, SHADOW_RGB)
        result.append(
            {
                "label": label,
                "selected": rendered["selected"],
                "counts": rendered["counts"],
                "selected_count": rendered["selected_count"],
                "pixel_count": rendered["pixel_count"],
            }
        )
    return tuple(result)


def row_alignment_family(new_list, old_list):
    rows = []
    for new_order, new_tail in (
        ("native", new_list[1:]),
        ("swapped", tuple(reversed(new_list[1:]))),
    ):
        for old_order, old_tail in (
            ("native", old_list[1:]),
            ("swapped", tuple(reversed(old_list[1:]))),
        ):
            aligned_new = (new_list[0], *new_tail)
            aligned_old = (old_list[0], *old_tail)
            difference = tuple(
                new_value - old_value
                for new_value, old_value in zip(aligned_new, aligned_old)
            )
            for traversal, values in (
                ("direct", difference),
                ("reverse", tuple(reversed(difference))),
            ):
                rows.append(
                    {
                        "new_row_order": new_order,
                        "old_row_order": old_order,
                        "traversal": traversal,
                        "difference": difference,
                        "values": values,
                        "a1z26": a1z26(values),
                    }
                )
    return tuple(rows)


def audit():
    shadow_rows = sampled_shadow_rows()
    count_matrix = tuple(row["counts"] for row in shadow_rows)
    shadow_list = matrix_sum_list(count_matrix)
    _, prime_list = matrixsumlist(EXPECTED_PRIME)
    prime_list = tuple(prime_list)
    difference = tuple(
        shadow - prime for shadow, prime in zip(shadow_list, prime_list)
    )
    reverse_difference = tuple(reversed(difference))

    event_report = prime_sum_audit()
    event_cross_checks = {
        "events_before_fefe": event_report["fefe_record"]["ordinal"] - 1,
        "yellow_endpoint_count": event_report["event_types"].count("Y"),
        "shadow_row_widths": tuple(row["selected_count"] for row in shadow_rows),
    }
    family = row_alignment_family(shadow_list, prime_list)
    kit_rows = tuple(row for row in family if row["a1z26"] == "KIT")

    delta_permutations = tuple(
        {
            "values": values,
            "a1z26": a1z26(values),
        }
        for values in permutations(difference)
    )

    return {
        "source": {
            "shadow_rgb": SHADOW_RGB,
            "shadow_rows": shadow_rows,
            "count_matrix": count_matrix,
            "shadow_matrixsumlist": shadow_list,
            "prime_matrixsumlist": prime_list,
            "grammar": ("total", "row_1_sum", "row_2_sum"),
        },
        "difference": {
            "direct": difference,
            "direct_a1z26": a1z26(difference),
            "reverse": reverse_difference,
            "reverse_a1z26": a1z26(reverse_difference),
            "additive_checksum": difference[0] == difference[1] + difference[2],
            "additive_checksum_forced": (
                shadow_list[0] == shadow_list[1] + shadow_list[2]
                and prime_list[0] == prime_list[1] + prime_list[2]
            ),
        },
        "event_cross_checks": event_cross_checks,
        "cross_check_match": difference == (
            event_cross_checks["events_before_fefe"],
            event_cross_checks["yellow_endpoint_count"],
            event_cross_checks["shadow_row_widths"][0],
        ),
        "row_alignment_traversal_family": {
            "rows": family,
            "family_size": len(family),
            "kit_count": len(kit_rows),
            "kit_rate_fixed_target": Fraction(len(kit_rows), len(family)),
            "posthoc_valid_p_value": False,
        },
        "all_delta_permutations": {
            "rows": delta_permutations,
            "family_size": len(delta_permutations),
            "kit_count": sum(row["a1z26"] == "KIT" for row in delta_permutations),
        },
        "semantic_notes": {
            "kit_is_young_rabbit_term": True,
            "reversal_locally_forced": False,
            "subtraction_locally_forced": False,
            "a1z26_locally_forced": False,
        },
        "oracle_run": False,
    }


def self_test():
    report = audit()
    source = report["source"]
    delta = report["difference"]
    family = report["row_alignment_traversal_family"]

    assert source["count_matrix"] == (
        (4, 1, 4, 4, 2, 1, 1, 1, 2, 1, 4),
        (2, 1, 2, 2, 1, 3, 1, 1, 1, 2, 2),
    )
    assert source["shadow_matrixsumlist"] == (43, 25, 18)
    assert source["prime_matrixsumlist"] == (23, 16, 7)
    assert delta["direct"] == (20, 9, 11)
    assert delta["direct_a1z26"] == "TIK"
    assert delta["reverse"] == (11, 9, 20)
    assert delta["reverse_a1z26"] == "KIT"
    assert delta["additive_checksum"] is True
    assert delta["additive_checksum_forced"] is True
    assert report["event_cross_checks"] == {
        "events_before_fefe": 20,
        "yellow_endpoint_count": 9,
        "shadow_row_widths": (11, 11),
    }
    assert report["cross_check_match"] is True
    assert family["family_size"] == 8
    assert family["kit_count"] == 1
    assert family["kit_rate_fixed_target"] == Fraction(1, 8)
    assert family["posthoc_valid_p_value"] is False
    assert report["all_delta_permutations"]["family_size"] == 6
    assert report["all_delta_permutations"]["kit_count"] == 1
    assert report["semantic_notes"]["reversal_locally_forced"] is False
    assert report["oracle_run"] is False
    print("[*] self-test OK: [43,25,18] - [23,16,7] -> TIK/KIT reproduces")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    report = audit()
    source = report["source"]
    delta = report["difference"]
    family = report["row_alignment_traversal_family"]

    print(f"[*] #383838 count matrix: {source['count_matrix']}")
    print(f"[*] shadow matrixsumlist: {source['shadow_matrixsumlist']}")
    print(f"[*] prime matrixsumlist:  {source['prime_matrixsumlist']}")
    print(
        f"[*] difference: {delta['direct']} -> {delta['direct_a1z26']}; "
        f"reverse={delta['reverse']} -> {delta['reverse_a1z26']}"
    )
    print(f"[*] event cross-checks: {report['event_cross_checks']}")
    print(
        f"[*] row-order/traversal family: KIT {family['kit_count']}/"
        f"{family['family_size']} (descriptive, post hoc)"
    )
    print(
        "[*] verdict: [43,25,18] and the [20,9,11] subtraction are exact; "
        "KIT is thematic but needs unselected subtraction, A1Z26, and reversal."
    )
    if args.self_test:
        self_test()


if __name__ == "__main__":
    main()
