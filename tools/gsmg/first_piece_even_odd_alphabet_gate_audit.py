#!/usr/bin/env python3
"""Audit the 86420 gate and conditional 13579/a-i permutation claims.

The source values are reconstructed without extrapolating the arithmetic
progression: OCBe atomic numbers, row-local uppercase-G counts, the FEFE base
bit, and the Architect end rail's a-i-filtered ``he``.  A strict promotion gate
then asks whether all five digits have specific, homogeneous provenance and a
selected concatenation rule.

The nine's complement and a-i mappings are still computed exactly, but remain
conditional if the gate fails.  No password/blob oracle is rerun; Phase 191
already closed the direct 86420 oracle negative.
"""

import argparse
from itertools import product

from PIL import Image

from first_piece_color_reconstruction import (
    COLOR_NAMES,
    DEFAULT_IMAGE,
    base_bit,
    reconstruct,
)
from prime_matrixsum_reconstruction import (
    NINE_SYMBOLS,
    bounded_indexings,
    edge_letters,
    load_architect_words,
    matrixsumlist,
    EXPECTED_PRIME,
)
from stage0_footer_palette_layer_audit import (
    ADDRESS,
    ADDRESS_X,
    ADDRESS_Y,
    BANNER,
    BANNER_X,
    BANNER_Y,
    IMAGE_PATH,
)
from stage0_g_shadow_consumer_audit import ELEMENTS, consume_row


def shadow_components():
    image = Image.open(IMAGE_PATH).convert("RGB")
    rows = (
        consume_row(image, "banner", BANNER, BANNER_X, BANNER_Y),
        consume_row(image, "address", ADDRESS, ADDRESS_X, ADDRESS_Y),
    )
    payload = "".join(row["payload"] for row in rows)
    symbols = (payload[0], payload[1], payload[2:])
    return {
        "payload": payload,
        "element_symbols": symbols,
        "atomic_numbers": tuple(ELEMENTS[symbol] for symbol in symbols),
        "g_reference_counts": tuple(row["reference_count"] for row in rows),
    }


def architect_he_route():
    _, sum_list = matrixsumlist(EXPECTED_PRIME)
    tokens, first_after_choice = load_architect_words()
    selected = bounded_indexings(tokens, sum_list)["forward_one"]
    first_edges, last_edges = edge_letters(selected)
    filtered = "".join(character for character in last_edges if character in NINE_SYMBOLS)
    return {
        "selected_words": selected,
        "first_edges": first_edges,
        "last_edges": last_edges,
        "first_word_after_choice": first_after_choice,
        "a_i_filtered_end_rail": filtered,
        "chemical_symbol": filtered.capitalize(),
        "atomic_number": 2 if filtered.capitalize() == "He" else None,
        "requires_case_promotion": filtered != filtered.capitalize(),
    }


def map_digits_to_a_i(digits, base):
    mapped = []
    invalid = []
    for digit in digits:
        index = digit - base
        if 0 <= index < 9:
            mapped.append(chr(ord("a") + index))
        else:
            invalid.append(digit)
    return {
        "base": base,
        "mapped_valid_digits": "".join(mapped),
        "invalid_digits": tuple(invalid),
        "complete_without_drop": not invalid,
    }


def orientation_family(first_rail, second_rail):
    outputs = []
    for order in ((first_rail, second_rail), (second_rail, first_rail)):
        for first_direction, second_direction in product((1, -1), repeat=2):
            outputs.append(order[0][::first_direction] + order[1][::second_direction])
    return tuple(outputs)


def interleave(left, right):
    output = []
    for index in range(max(len(left), len(right))):
        if index < len(left):
            output.append(str(left[index]))
        if index < len(right):
            output.append(str(right[index]))
    return "".join(output)


def audit():
    shadow = shadow_components()
    fefe_report = reconstruct(DEFAULT_IMAGE)["fefe"]
    palette_bits = {
        name: base_bit(color) for color, name in COLOR_NAMES.items()
    }
    fefe_shared = tuple(
        sorted(name for name, value in palette_bits.items() if value == fefe_report["value"])
    )
    architect = architect_he_route()

    atomic = shadow["atomic_numbers"]
    references = shadow["g_reference_counts"]
    overlap = atomic[-1] == references[0]
    even_digits = atomic + references[1:] + (fefe_report["value"],)
    steps = tuple(right - left for left, right in zip(even_digits, even_digits[1:]))
    odd_digits = tuple(9 - digit for digit in even_digits)

    zero_based_even = map_digits_to_a_i(even_digits, base=0)
    zero_based_odd = map_digits_to_a_i(odd_digits, base=0)
    one_based_even = map_digits_to_a_i(even_digits, base=1)
    one_based_odd = map_digits_to_a_i(odd_digits, base=1)

    canonical_even_letters = zero_based_even["mapped_valid_digits"]
    canonical_odd_letters = zero_based_odd["mapped_valid_digits"]
    candidate_family = orientation_family(canonical_even_letters, canonical_odd_letters)

    return {
        "provenance": {
            "shadow": shadow,
            "architect_he_route": architect,
            "fefe_value": fefe_report["value"],
            "fefe_character": fefe_report["character"],
            "fefe_bit_position_1": fefe_report["bit_1"],
            "palette_base_bits": palette_bits,
            "fefe_value_shared_with": fefe_shared,
            "atomic_to_g_overlap": overlap,
        },
        "even_sequence": {
            "digits": even_digits,
            "string": "".join(str(digit) for digit in even_digits),
            "steps": steps,
            "digit_values_measured_without_extrapolation": True,
            "source_types": (
                "atomic_number", "atomic_number", "atomic_number",
                "pixel_count", "binary_class_bit",
            ),
        },
        "strict_gate": {
            "all_five_values_measured": True,
            "same_operation_or_value_type": False,
            "terminal_zero_unique_to_fefe": False,
            "concatenation_selected_by_clue": False,
            "independent_five_digit_recovery": False,
            "pass": False,
        },
        "conditional_nines_complement": {
            "digits": odd_digits,
            "string": "".join(str(digit) for digit in odd_digits),
            "pair_sums": tuple(left + right for left, right in zip(even_digits, odd_digits)),
            "forced_once_even_sequence_and_base10_complement_chosen": True,
            "interleaved": interleave(even_digits, odd_digits),
        },
        "conditional_a_i_mapping": {
            "zero_based_even": zero_based_even,
            "zero_based_odd": zero_based_odd,
            "one_based_even": one_based_even,
            "one_based_odd": one_based_odd,
            "zero_based_join_after_dropping_invalid": (
                zero_based_even["mapped_valid_digits"]
                + zero_based_odd["mapped_valid_digits"]
            ),
            "one_based_join_after_dropping_invalid": (
                one_based_even["mapped_valid_digits"]
                + one_based_odd["mapped_valid_digits"]
            ),
            "orientation_family": candidate_family,
            "orientation_family_size": len(set(candidate_family)),
            "igecabdfh_count": candidate_family.count("igecabdfh"),
            "exact_permutation_is_forced_after_invalid_terminal_drop": True,
            "invalid_terminal_as_delimiter_selected": False,
        },
        "prior_direct_86420_oracle": {
            "phase": 191,
            "result": "zero hits",
            "rerun": False,
        },
        "oracle_run": False,
    }


def self_test():
    report = audit()
    provenance = report["provenance"]
    even = report["even_sequence"]
    gate = report["strict_gate"]
    complement = report["conditional_nines_complement"]
    mapping = report["conditional_a_i_mapping"]

    assert provenance["shadow"] == {
        "payload": "OCBe",
        "element_symbols": ("O", "C", "Be"),
        "atomic_numbers": (8, 6, 4),
        "g_reference_counts": (4, 2),
    }
    assert provenance["architect_he_route"]["first_edges"] == "but"
    assert provenance["architect_he_route"]["last_edges"] == "hye"
    assert provenance["architect_he_route"]["a_i_filtered_end_rail"] == "he"
    assert provenance["architect_he_route"]["chemical_symbol"] == "He"
    assert provenance["architect_he_route"]["atomic_number"] == 2
    assert provenance["fefe_value"] == 0
    assert provenance["fefe_value_shared_with"] == ("fefefe", "white", "yellow")
    assert provenance["atomic_to_g_overlap"] is True
    assert even["digits"] == (8, 6, 4, 2, 0)
    assert even["string"] == "86420"
    assert even["steps"] == (-2, -2, -2, -2)
    assert gate == {
        "all_five_values_measured": True,
        "same_operation_or_value_type": False,
        "terminal_zero_unique_to_fefe": False,
        "concatenation_selected_by_clue": False,
        "independent_five_digit_recovery": False,
        "pass": False,
    }
    assert complement["digits"] == (1, 3, 5, 7, 9)
    assert complement["string"] == "13579"
    assert complement["pair_sums"] == (9, 9, 9, 9, 9)
    assert complement["interleaved"] == "8163452709"
    assert mapping["zero_based_even"] == {
        "base": 0, "mapped_valid_digits": "igeca", "invalid_digits": (),
        "complete_without_drop": True,
    }
    assert mapping["zero_based_odd"] == {
        "base": 0, "mapped_valid_digits": "bdfh", "invalid_digits": (9,),
        "complete_without_drop": False,
    }
    assert mapping["one_based_even"] == {
        "base": 1, "mapped_valid_digits": "hfdb", "invalid_digits": (0,),
        "complete_without_drop": False,
    }
    assert mapping["one_based_odd"] == {
        "base": 1, "mapped_valid_digits": "acegi", "invalid_digits": (),
        "complete_without_drop": True,
    }
    assert mapping["zero_based_join_after_dropping_invalid"] == "igecabdfh"
    assert mapping["one_based_join_after_dropping_invalid"] == "hfdbacegi"
    assert mapping["orientation_family"] == (
        "igecabdfh", "igecahfdb", "acegibdfh", "acegihfdb",
        "bdfhigeca", "bdfhacegi", "hfdbigeca", "hfdbacegi",
    )
    assert mapping["orientation_family_size"] == 8
    assert mapping["igecabdfh_count"] == 1
    assert mapping["exact_permutation_is_forced_after_invalid_terminal_drop"] is True
    assert mapping["invalid_terminal_as_delimiter_selected"] is False
    assert report["prior_direct_86420_oracle"]["rerun"] is False
    assert report["oracle_run"] is False
    print("[*] self-test OK: 86420 provenance gate fails; conditional 13579/a-i math reproduces")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    report = audit()
    print(f"[*] even sequence: {report['even_sequence']}")
    print(f"[*] strict gate: {report['strict_gate']}")
    print(f"[*] conditional complement: {report['conditional_nines_complement']}")
    print(f"[*] conditional a-i mapping: {report['conditional_a_i_mapping']}")
    print("[*] verdict: arithmetic is exact, but the independent-recovery gate fails; do not promote 13579 or igecabdfh")
    if args.self_test:
        self_test()


if __name__ == "__main__":
    main()
