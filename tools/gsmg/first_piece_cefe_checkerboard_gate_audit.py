#!/usr/bin/env python3
"""Audit Point 16's Ce/Fe arithmetic and Point 18's alphabet-seed chain.

The audit preserves three separate questions:

1. do the proposed Ce/Fe calculations reproduce exactly;
2. is CE an authored, selected source value rather than a rendered gray;
3. do the proposed element fragments determine one 25-letter checkerboard
   alphabet without free fragment order, drop/merge, or tail-order choices?

No checkerboard decode or cryptographic oracle is run if those gates fail.
"""

import argparse
import math
from itertools import permutations

from cb_common import TAIL_FILL_ORDERS, pad25
from first_piece_batch_rebus_gate_audit import ELEMENT_SYMBOLS
from page_structure_audit import MATRIX_INSTRUCTION
from prime_matrixsum_reconstruction import EXPECTED_PRIME
from stage0_g_shadow_consumer_audit import PERIODIC_SYMBOLS
from stage0_repeated_grayscale_audit import audit as grayscale_audit


SECP256K1_N = int(
    "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141",
    16,
)
FRAGMENTS = ("BaTcH", "OCBeHe", "CeFe", "PHV")


def atomic_number(symbol):
    return ELEMENT_SYMBOLS.index(symbol) + 1


def is_prime(number):
    if number < 2:
        return False
    for divisor in range(2, math.isqrt(number) + 1):
        if number % divisor == 0:
            return False
    return True


def dedupe_letters(parts):
    joined = "".join(parts).upper()
    return "".join(dict.fromkeys(joined))


def titlecase_element_candidates(byte_names):
    rows = []
    for byte_name in byte_names:
        symbol = byte_name.capitalize()
        if symbol in PERIODIC_SYMBOLS:
            rows.append(
                {
                    "byte": byte_name,
                    "symbol": symbol,
                    "atomic_number": atomic_number(symbol),
                }
            )
    return tuple(rows)


def checkerboard_family():
    ordered_rows = []
    seeds = set()
    boards = set()
    for order in permutations(FRAGMENTS):
        seed = dedupe_letters(order)
        seeds.add(seed)
        for drop in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            for tail_fill in TAIL_FILL_ORDERS:
                for merge_direction in ("backward", "forward"):
                    board = pad25(seed, drop, tail_fill, merge_direction)
                    boards.add(board)
                    ordered_rows.append(
                        {
                            "fragment_order": order,
                            "seed": seed,
                            "drop": drop,
                            "tail_fill": tail_fill,
                            "merge_direction": merge_direction,
                            "board": board,
                        }
                    )
    native_seed = dedupe_letters(FRAGMENTS)
    fixed_seed_rows = tuple(row for row in ordered_rows if row["seed"] == native_seed)
    return {
        "fragments": FRAGMENTS,
        "native_concatenation": "".join(FRAGMENTS),
        "native_deduped_seed": native_seed,
        "fragment_permutations": math.factorial(len(FRAGMENTS)),
        "unique_deduped_seeds": tuple(sorted(seeds)),
        "parameter_rows": len(ordered_rows),
        "unique_boards": len(boards),
        "fixed_seed_parameter_rows": len(fixed_seed_rows),
        "fixed_seed_unique_boards": len({row["board"] for row in fixed_seed_rows}),
        "classic_j_forward_candidate": pad25(
            native_seed, drop="J", tail_fill="forward", merge_direction="backward"
        ),
        "arbitrary_tail_orders_after_fixed_j_drop": math.factorial(15),
    }


def audit():
    gray = grayscale_audit()
    ce_byte = int(gray["collapsed_claim"][0], 16)
    fe_byte = int(gray["collapsed_claim"][1], 16)
    ce_symbol = gray["collapsed_claim"][0].capitalize()
    fe_symbol = gray["collapsed_claim"][1].capitalize()
    ce_atomic = atomic_number(ce_symbol)
    fe_atomic = atomic_number(fe_symbol)

    atomic_sum_list = (ce_atomic + fe_atomic, ce_atomic, fe_atomic)
    half_sum_list = tuple(value // 2 for value in atomic_sum_list)
    scalar_bytes = (SECP256K1_N.bit_length() + 7) // 8
    prime_minimal_bytes = (EXPECTED_PRIME.bit_length() + 7) // 8

    singleton_candidates = titlecase_element_candidates(gray["logo_single_3x3_bytes"])
    even_candidate_rows = tuple(
        row for row in singleton_candidates
        if row["atomic_number"] % 2 == 0 and fe_atomic % 2 == 0
    )
    favicon = gray["favicon"]

    board = checkerboard_family()
    return {
        "source": {
            "collapsed_claim": gray["collapsed_claim"],
            "ce_pixel_count": gray["ce"]["pixel_count"],
            "fe_pixel_count": gray["fe"]["pixel_count"],
            "logo_single_3x3_bytes": gray["logo_single_3x3_bytes"],
            "titlecase_element_candidates": singleton_candidates,
            "even_with_fe_candidates": even_candidate_rows,
            "favicon_provenance": favicon,
            "ce_absent_from_source_favicon": (
                favicon is not None and favicon["source_ce_count"] == 0
            ),
            "ce_present_after_render": (
                favicon is not None and favicon["rendered_ce_count"] == 9
            ),
        },
        "atomic_arithmetic": {
            "symbols": (ce_symbol, fe_symbol),
            "atomic_numbers": (ce_atomic, fe_atomic),
            "difference": ce_atomic - fe_atomic,
            "atomic_sum_list": atomic_sum_list,
            "half_sum_list": half_sum_list,
            "half_tail_prime": tuple(is_prime(value) for value in half_sum_list[1:]),
            "half_additive_checksum": half_sum_list[0] == sum(half_sum_list[1:]),
            "half_additive_checksum_forced": atomic_sum_list[0] == sum(atomic_sum_list[1:]),
        },
        "role_matches": {
            "secp256k1_order_bit_length": SECP256K1_N.bit_length(),
            "scalar_bytes": scalar_bytes,
            "difference_matches_scalar_bytes": ce_atomic - fe_atomic == scalar_bytes,
            "prime": EXPECTED_PRIME,
            "prime_hex": f"{EXPECTED_PRIME:06X}",
            "prime_minimal_bytes": prime_minimal_bytes,
            "zero_pad_bytes_to_scalar": scalar_bytes - prime_minimal_bytes,
            "ce_half_matches_zero_pad_bytes": ce_atomic // 2 == scalar_bytes - prime_minimal_bytes,
            "matrix_instruction": MATRIX_INSTRUCTION,
            "matrix_instruction_length": len(MATRIX_INSTRUCTION),
            "fe_half_matches_instruction_length": fe_atomic // 2 == len(MATRIX_INSTRUCTION),
            "roles_require_unselected_scalar_serialization": True,
        },
        "byte_identity": {
            "ce": ce_byte,
            "fe": fe_byte,
            "subtraction": fe_byte - ce_byte,
            "xor": fe_byte ^ ce_byte,
            "ascii": chr(fe_byte - ce_byte),
            "ce_bits_subset_of_fe": ce_byte & fe_byte == ce_byte,
            "agreement_forced_by_bit_containment": True,
            "independent_confirmations": 1,
        },
        "point16_gate": {
            "arithmetic_exact": True,
            "chemical_case_promotion_required": True,
            "ce_selected_before_inspecting_arithmetic": False,
            "ce_is_source_native_favicon_pixel": False if favicon is not None else None,
            "difference_and_halving_jointly_selected": False,
            "private_scalar_serialization_selected": False,
            "pass": False,
        },
        "checkerboard_seed": board,
        "fragment_support": {
            "BaTcH": "exact rebus; Phase 205 execution gate failed",
            "OCBe": "exact row-local G consumer",
            "He": "a-i-filtered HYE plus unselected chemical case promotion",
            "CeFe": "exact composite-image grays; Ce is render-generated",
            "PHV": "exact Phase-97 PH-to-V recognition transition",
        },
        "point18_gate": {
            "all_fragments_independently_selected": False,
            "fragment_order_selected": False,
            "deduplication_selected": False,
            "dropped_letter_selected": False,
            "merge_direction_selected": False,
            "unused_tail_order_selected": False,
            "escape_digits_and_topology_selected": False,
            "pass": False,
        },
        "oracle_run": False,
    }


def self_test():
    report = audit()
    source = report["source"]
    arithmetic = report["atomic_arithmetic"]
    roles = report["role_matches"]
    identity = report["byte_identity"]
    board = report["checkerboard_seed"]

    assert source["collapsed_claim"] == ("CE", "FE")
    assert source["logo_single_3x3_bytes"] == (
        "CE", "D3", "D5", "DB", "DF", "E1", "EC", "ED", "F1", "F2"
    )
    assert source["titlecase_element_candidates"] == (
        {"byte": "CE", "symbol": "Ce", "atomic_number": 58},
        {"byte": "DB", "symbol": "Db", "atomic_number": 105},
    )
    if source["favicon_provenance"] is not None:
        assert source["ce_absent_from_source_favicon"] is True
        assert source["ce_present_after_render"] is True
    assert arithmetic["atomic_numbers"] == (58, 26)
    assert arithmetic["difference"] == 32
    assert arithmetic["atomic_sum_list"] == (84, 58, 26)
    assert arithmetic["half_sum_list"] == (42, 29, 13)
    assert arithmetic["half_tail_prime"] == (True, True)
    assert arithmetic["half_additive_checksum"] is True
    assert arithmetic["half_additive_checksum_forced"] is True
    assert roles["scalar_bytes"] == 32
    assert roles["prime_hex"] == "08C26D"
    assert roles["prime_minimal_bytes"] == 3
    assert roles["zero_pad_bytes_to_scalar"] == 29
    assert roles["ce_half_matches_zero_pad_bytes"] is True
    assert roles["matrix_instruction_length"] == 13
    assert roles["fe_half_matches_instruction_length"] is True
    assert identity["subtraction"] == identity["xor"] == 0x30
    assert identity["ascii"] == "0"
    assert identity["ce_bits_subset_of_fe"] is True
    assert identity["independent_confirmations"] == 1
    assert report["point16_gate"]["pass"] is False
    assert board["native_concatenation"] == "BaTcHOCBeHeCeFePHV"
    assert board["native_deduped_seed"] == "BATCHOEFPV"
    assert len(board["unique_deduped_seeds"]) == 24
    assert board["parameter_rows"] == 3744
    assert board["unique_boards"] == 2430
    assert board["fixed_seed_parameter_rows"] == 156
    assert board["fixed_seed_unique_boards"] == 105
    assert board["classic_j_forward_candidate"] == "BATCHOEFPVDGIKLMNQRSUWXYZ"
    assert board["arbitrary_tail_orders_after_fixed_j_drop"] == math.factorial(15)
    assert report["point18_gate"]["pass"] is False
    assert report["oracle_run"] is False
    print("[*] self-test OK: Ce/Fe arithmetic exact; source and board gates fail")


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
