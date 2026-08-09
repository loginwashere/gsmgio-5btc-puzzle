#!/usr/bin/env python3
"""Audit the proposed ``56 -> Ba, 43 -> Tc, H -> BaTcH/BATCH`` rebus.

The audit reconstructs the two pixel quantities and the Architect edge rails,
then separates exact arithmetic/orthography from the missing selection rules.
The later exact-case ``OCBe`` extraction is admitted as evidence that element
symbols are native puzzle vocabulary; it is not treated as an instruction to
invert every available integer through the periodic table.

No password, ciphertext, or word-list oracle is run.
"""

import argparse
from fractions import Fraction
from itertools import permutations

from first_piece_even_odd_alphabet_gate_audit import shadow_components
from first_piece_second_matrixsumlist_audit import SHADOW_RGB, sampled_shadow_rows
from page_structure_audit import (
    DECIMAL_INSTRUCTIONS,
    ENTER_INSTRUCTION,
    HASH_PREFIX,
    HASH_SUFFIX,
    MATRIX_INSTRUCTION,
)
from prime_matrixsum_reconstruction import (
    EXPECTED_PRIME,
    add_shifts,
    bounded_indexings,
    edge_letters,
    load_architect_words,
    matrixsumlist,
)


# Atomic-number order, not alphabetical order.  Keeping the complete table
# makes the inverse operation explicit instead of special-casing 43 and 56.
ELEMENT_SYMBOLS = tuple(
    "H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe "
    "Co Ni Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In "
    "Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf "
    "Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am Cm "
    "Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og".split()
)


def element_for_atomic_number(number):
    if not 1 <= number <= len(ELEMENT_SYMBOLS):
        raise ValueError(f"atomic number outside 1..{len(ELEMENT_SYMBOLS)}: {number}")
    return ELEMENT_SYMBOLS[number - 1]


def architect_route():
    _, sum_list = matrixsumlist(EXPECTED_PRIME)
    tokens, first_after_choice = load_architect_words()
    selected = bounded_indexings(tokens, sum_list)["forward_one"]
    first_edges, last_edges = edge_letters(selected)
    return {
        "indices": tuple(sum_list),
        "selected_words": selected,
        "first_edges": first_edges,
        "last_edges": last_edges,
        "first_word_after_choice": first_after_choice,
        "singleton_h": last_edges[0],
        "eol": add_shifts(last_edges, sum_list),
    }


def spelling_family(symbols):
    rows = []
    for ordered in permutations(symbols):
        exact = "".join(ordered)
        rows.append(
            {
                "order": ordered,
                "exact_case": exact,
                "casefolded": exact.casefold(),
                "is_batch": exact.casefold() == "batch",
            }
        )
    return tuple(rows)


def audit():
    shadow_rows = sampled_shadow_rows()
    shadow_rgb = SHADOW_RGB
    if any(row["selected_count"] != 11 for row in shadow_rows):
        raise AssertionError("selected shadow-row width drifted")
    pixel_count = sum(row["pixel_count"] for row in shadow_rows)
    if shadow_rgb[0] != shadow_rgb[1] or shadow_rgb[1] != shadow_rgb[2]:
        raise AssertionError("selected layer is no longer repeated-byte gray")

    channel_value = shadow_rgb[0]
    pixel_symbols = (
        element_for_atomic_number(channel_value),
        element_for_atomic_number(pixel_count),
    )
    architect = architect_route()
    symbols = (*pixel_symbols, architect["singleton_h"].upper())
    family = spelling_family(symbols)
    batch_rows = tuple(row for row in family if row["is_batch"])
    staged_rows = tuple(row for row in family if row["order"][-1] == "H")

    chemical_context = shadow_components()
    decoded_instruction_vocabulary = (
        MATRIX_INSTRUCTION,
        ENTER_INSTRUCTION,
        *DECIMAL_INSTRUCTIONS,
        HASH_PREFIX,
        HASH_SUFFIX,
    )

    return {
        "source": {
            "shadow_rgb": shadow_rgb,
            "channel_hex": f"{channel_value:02X}",
            "channel_decimal": channel_value,
            "shadow_pixel_count": pixel_count,
            "shadow_row_pixel_counts": tuple(row["pixel_count"] for row in shadow_rows),
            "pixel_atomic_symbols": pixel_symbols,
            "architect": architect,
        },
        "candidate": {
            "symbols": symbols,
            "exact_case": "".join(symbols),
            "casefolded": "".join(symbols).casefold(),
            "reads_batch": "".join(symbols).casefold() == "batch",
        },
        "ordering_calibration": {
            "all_permutations": family,
            "family_size": len(family),
            "batch_count": len(batch_rows),
            "fixed_target_rate": Fraction(len(batch_rows), len(family)),
            "stage_order_h_last_family_size": len(staged_rows),
            "stage_order_h_last_batch_count": sum(row["is_batch"] for row in staged_rows),
            "posthoc_valid_p_value": False,
        },
        "chemical_context": {
            "payload": chemical_context["payload"],
            "element_symbols": chemical_context["element_symbols"],
            "atomic_numbers": chemical_context["atomic_numbers"],
            "element_vocabulary_established": True,
            "inverse_atomic_number_operator_explicitly_instructed": False,
        },
        "semantic_context": {
            "architect_eol": architect["eol"],
            "decoded_instruction_vocabulary": decoded_instruction_vocabulary,
            "enter_present": ENTER_INSTRUCTION in decoded_instruction_vocabulary,
            "batch_literal_present": any(
                "batch" in instruction.casefold()
                for instruction in decoded_instruction_vocabulary
            ),
            "batch_to_enter_is_semantic_association_only": True,
        },
        "strict_gate": {
            "source_quantities_exact": True,
            "element_vocabulary_established_elsewhere": True,
            "inverse_atomic_number_operator_selected": False,
            "value_before_count_order_selected": False,
            "singleton_h_extraction_selected": False,
            "batch_execution_grammar_selected": False,
            "pass": False,
        },
        "oracle_run": False,
    }


def self_test():
    report = audit()
    source = report["source"]
    candidate = report["candidate"]
    calibration = report["ordering_calibration"]

    assert len(ELEMENT_SYMBOLS) == 118
    assert element_for_atomic_number(43) == "Tc"
    assert element_for_atomic_number(56) == "Ba"
    assert source["shadow_rgb"] == (56, 56, 56)
    assert source["channel_hex"] == "38"
    assert source["shadow_pixel_count"] == 43
    assert source["shadow_row_pixel_counts"] == (25, 18)
    assert source["pixel_atomic_symbols"] == ("Ba", "Tc")
    assert source["architect"]["first_edges"] == "but"
    assert source["architect"]["last_edges"] == "hye"
    assert source["architect"]["singleton_h"] == "h"
    assert source["architect"]["eol"] == "eol"
    assert candidate == {
        "symbols": ("Ba", "Tc", "H"),
        "exact_case": "BaTcH",
        "casefolded": "batch",
        "reads_batch": True,
    }
    assert calibration["family_size"] == 6
    assert calibration["batch_count"] == 1
    assert calibration["fixed_target_rate"] == Fraction(1, 6)
    assert calibration["stage_order_h_last_family_size"] == 2
    assert calibration["stage_order_h_last_batch_count"] == 1
    assert report["chemical_context"]["payload"] == "OCBe"
    assert report["chemical_context"]["atomic_numbers"] == (8, 6, 4)
    assert report["semantic_context"]["enter_present"] is True
    assert report["semantic_context"]["batch_literal_present"] is False
    assert report["strict_gate"]["pass"] is False
    assert report["oracle_run"] is False
    print("[*] self-test OK: BaTcH/BATCH exact; element/order/H gates remain open")


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
