#!/usr/bin/env python3
"""Calibrate the hindsight-sensitive ``{1,4,21} -> ggn`` extraction.

The tuple is independently authenticated as a hierarchical descriptor of the
unique FEFE cell: one cell, one-based bit position four, one-based character
position 21.  Flattening those three quantities into peer character indices
is an additional interpretation.  This audit verifies that flat extraction,
enumerates every increasing three-position selection from the same 24-byte
URL, and reports both exact-string and broader structural nulls.

No word list, curve-symbol vocabulary, password oracle, or Bitcoin-address
oracle is used.  In particular, the exact ``ggn`` rate is labeled as valid
only for a predeclared target; it is not used as a post-hoc discovery rate.
"""

import argparse
from collections import Counter
from fractions import Fraction
from itertools import combinations
from math import comb

from first_piece_color_reconstruction import DEFAULT_IMAGE, TARGET, reconstruct

TUPLE = (1, 4, 21)


def extract(source, indices, base):
    if base not in (0, 1):
        raise ValueError("base must be zero or one")
    positions = tuple(index - base for index in indices)
    if any(position < 0 or position >= len(source) for position in positions):
        raise IndexError("tuple falls outside source under requested convention")
    return "".join(source[position] for position in positions)


def triple_inventory(source):
    rows = tuple(
        {
            "indices_1": tuple(position + 1 for position in positions),
            "text": "".join(source[position] for position in positions),
        }
        for positions in combinations(range(len(source)), 3)
    )
    multiplicities = Counter(row["text"] for row in rows)
    character_counts = Counter(source)

    first_pair_equal = tuple(
        row for row in rows
        if row["text"][0] == row["text"][1] != row["text"][2]
    )
    exactly_two_equal = tuple(
        row for row in rows if len(set(row["text"])) == 2
    )
    all_equal = tuple(
        row for row in rows if len(set(row["text"])) == 1
    )
    first_pair_equal_unique_third = tuple(
        row for row in first_pair_equal if character_counts[row["text"][2]] == 1
    )
    uniquely_emitted_rows = tuple(
        row for row in rows if multiplicities[row["text"]] == 1
    )

    return {
        "rows": rows,
        "family_size": len(rows),
        "distinct_outputs": len(multiplicities),
        "output_multiplicities": multiplicities,
        "unique_output_strings": sum(count == 1 for count in multiplicities.values()),
        "uniquely_emitted_rows": len(uniquely_emitted_rows),
        "first_pair_equal_then_distinct": len(first_pair_equal),
        "exactly_two_equal": len(exactly_two_equal),
        "all_equal": len(all_equal),
        "first_pair_equal_unique_third": len(first_pair_equal_unique_third),
        "rates": {
            "uniquely_emitted": Fraction(len(uniquely_emitted_rows), len(rows)),
            "first_pair_equal_then_distinct": Fraction(len(first_pair_equal), len(rows)),
            "exactly_two_equal": Fraction(len(exactly_two_equal), len(rows)),
            "first_pair_equal_unique_third": Fraction(
                len(first_pair_equal_unique_third), len(rows)
            ),
        },
    }


def audit(image_path=DEFAULT_IMAGE):
    first_piece = reconstruct(image_path)
    colors = "".join(
        "B" if item["color"] == "blue" else "Y"
        for item in first_piece["objects"]
    )
    inventory = triple_inventory(TARGET)
    exact = tuple(
        row for row in inventory["rows"] if row["text"] == "ggn"
    )

    one_based_text = extract(TARGET, TUPLE, base=1)
    zero_based_text = extract(TARGET, TUPLE, base=0)
    one_based_colors = extract(colors, TUPLE, base=1)
    zero_based_colors = extract(colors, TUPLE, base=0)
    color_inventory = triple_inventory(colors)

    return {
        "source": TARGET,
        "source_length": len(TARGET),
        "tuple": TUPLE,
        "tuple_provenance": {
            "fefe_cell_count": 1,
            "fefe_bit_position_1": first_piece["fefe"]["bit_1"],
            "fefe_character_position_1": first_piece["fefe"]["character_1"],
            "hierarchical_match": (
                1,
                first_piece["fefe"]["bit_1"],
                first_piece["fefe"]["character_1"],
            ) == TUPLE,
        },
        "flat_extractions": {
            "one_based_text": one_based_text,
            "zero_based_text": zero_based_text,
            "one_based_colors": one_based_colors,
            "zero_based_colors": zero_based_colors,
            "one_based_blue_bits": "".join("1" if value == "B" else "0" for value in one_based_colors),
            "zero_based_blue_bits": "".join("1" if value == "B" else "0" for value in zero_based_colors),
        },
        "text_triple_family": {
            key: value for key, value in inventory.items() if key != "rows"
        },
        "exact_ggn": {
            "occurrences": len(exact),
            "indices_1": tuple(row["indices_1"] for row in exact),
            "fixed_target_rate": Fraction(len(exact), inventory["family_size"]),
            "posthoc_valid_p_value": False,
        },
        "color_triple_family": {
            "family_size": color_inventory["family_size"],
            "pattern_counts": dict(sorted(color_inventory["output_multiplicities"].items())),
            "one_based_pattern_occurrences": color_inventory["output_multiplicities"][one_based_colors],
            "zero_based_pattern_occurrences": color_inventory["output_multiplicities"][zero_based_colors],
        },
        "semantic_assumptions": (
            "flatten the hierarchical FEFE descriptor into three peer URL indices",
            "choose one-based rather than zero-based indexing",
            "promote lowercase g to conventional uppercase curve symbol G",
            "parse the two g characters as two group operations rather than repetition",
            "parse n specifically as the generator order",
            "introduce a scalar k that is absent from ggn",
            "choose secp256k1 rather than the generic cyclic-group identity",
        ),
        "curve_identity_scope": {
            "relation": "(n-k)G = -kG when G has order n",
            "requires_symbols_absent_from_ggn": ("k", "minus"),
            "secp256k1_specific": False,
        },
    }


def self_test():
    report = audit()
    flat = report["flat_extractions"]
    family = report["text_triple_family"]
    exact = report["exact_ggn"]

    assert report["source_length"] == 24
    assert report["tuple_provenance"]["hierarchical_match"] is True
    assert flat == {
        "one_based_text": "ggn",
        "zero_based_text": "s.t",
        "one_based_colors": "BBY",
        "zero_based_colors": "BYY",
        "one_based_blue_bits": "110",
        "zero_based_blue_bits": "100",
    }
    assert family["family_size"] == comb(24, 3) == 2024
    assert family["distinct_outputs"] == 988
    assert family["unique_output_strings"] == 519
    assert family["uniquely_emitted_rows"] == 519
    assert family["first_pair_equal_then_distinct"] == 85
    assert family["exactly_two_equal"] == 271
    assert family["all_equal"] == 5
    assert family["first_pair_equal_unique_third"] == 36
    assert exact["occurrences"] == 1
    assert exact["indices_1"] == (TUPLE,)
    assert exact["fixed_target_rate"] == Fraction(1, 2024)
    assert exact["posthoc_valid_p_value"] is False
    assert report["color_triple_family"]["one_based_pattern_occurrences"] == 546
    assert report["color_triple_family"]["zero_based_pattern_occurrences"] == 311
    assert report["curve_identity_scope"]["secp256k1_specific"] is False
    print("[*] self-test OK: ggn extraction and bounded triple calibration reproduce")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    report = audit()
    flat = report["flat_extractions"]
    family = report["text_triple_family"]
    exact = report["exact_ggn"]

    print(f"[*] tuple provenance: {report['tuple_provenance']}")
    print(f"[*] one-based/zero-based text: {flat['one_based_text']} / {flat['zero_based_text']}")
    print(f"[*] one-based/zero-based colors: {flat['one_based_colors']} / {flat['zero_based_colors']}")
    print(
        "[*] all increasing triples: "
        f"{family['family_size']}; distinct outputs={family['distinct_outputs']}; "
        f"uniquely emitted={family['uniquely_emitted_rows']}"
    )
    print(
        "[*] structural counts: first-pair-equal/distinct-third="
        f"{family['first_pair_equal_then_distinct']}; exactly-two-equal="
        f"{family['exactly_two_equal']}; first-pair-equal/unique-third="
        f"{family['first_pair_equal_unique_third']}"
    )
    print(
        f"[*] exact predeclared ggn rate: {exact['fixed_target_rate']} "
        "(not a valid post-hoc discovery p-value)"
    )
    print(f"[*] semantic assumptions: {len(report['semantic_assumptions'])}")
    print(
        "[*] verdict: ggn is exact and uniquely located, but exact-output "
        "uniqueness is common enough in this source and the curve reading "
        "requires unforced indexing, case, parsing, scalar, and curve choices."
    )
    if args.self_test:
        self_test()


if __name__ == "__main__":
    main()
