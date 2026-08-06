#!/usr/bin/env python3
"""Dual-channel consistency audit over the seven authored "dual" artifacts.

The bird-view document lists seven pairs it calls dual artifacts (yellow/
blue, the two matrix rows, `16+7`, `BUT`/`HYE`, the two SALPH Base64 halves,
"half and better half", and the two textareas) and asks whether one
consistent left/right or beginning/end assignment survives the entire
chain, or whether assignments must be swapped independently at each step.

This module does not run any new cipher, transform, or password sweep. For
each pair it re-derives the two poles from already-verified code or the
archived page/export, then checks -- using only citations to established
FINDINGS.md phases, never an invented connection -- whether any other pair
in the list is actually chained to it. The honest possibility this audit is
built to detect is that most of these pairs were never chained together at
all: they are independently-discovered dualities that share a theme, not a
demonstrated common polarity, and forcing them into one chain would repeat
the exact apophenia pattern this project has already caught and corrected
more than once (Phase 13, the "matrixsumlist triangle").
"""

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from first_piece_color_reconstruction import (  # noqa: E402
    DEFAULT_IMAGE,
    reconstruct,
)
from page_structure_audit import DEFAULT_HTML, audit as audit_page  # noqa: E402
from prime_matrixsum_reconstruction import (  # noqa: E402
    EXPECTED_SUM_LIST,
    bounded_indexings,
    edge_letters,
    load_architect_words,
    matrixsumlist,
    mirror9,
)


def yellow_blue_values():
    """Pair: the two complementary first-piece color-bit assignments."""
    color_result = reconstruct(DEFAULT_IMAGE)
    if color_result["prime_value"] != 574061:
        raise AssertionError("yellow-one polarity no longer gives prime 574061")
    if color_result["rose_hex"] != "F73D92":
        raise AssertionError("blue-one polarity no longer gives rose F73D92")
    return {
        "pair": "blue-one rose F73D92 / yellow-one prime 574061",
        "basis": "first_piece_color_reconstruction, re-derived fresh",
        "color_result": color_result,
        "note": (
            "Only the yellow-one pole is consumed by the established next "
            "step: 574061 feeds matrixsumlist. The complementary rose value "
            "has no established downstream consumer, so polarity is already "
            "asymmetric at this edge."
        ),
    }


def textarea_order(page_report):
    """Pair: SalPhaseIon vs Cosmic Duality textarea."""
    order = page_report["dom_order"]
    if order != ["SalPhaseIon", "Cosmic Duality"]:
        raise AssertionError(f"unexpected DOM order: {order}")
    return {
        "pair": "SalPhaseIon (first) / Cosmic Duality (second)",
        "basis": "page_structure_audit DOM order",
        "note": (
            "dbbi and faed are both components of the FIRST textarea "
            "(SalPhaseIon); Cosmic Duality contains neither. This pair is "
            "a different structural level from the dbbi/faed pair, not the "
            "same axis relabeled."
        ),
    }


def salph_halves(page_report):
    """Pair: the two 64-character SALPH Base64 halves around `enter`."""
    segments = {
        segment["name"]: segment
        for segment in page_report["salphaseion"]["segments"]
    }
    prefix = segments["salphaseion_aes_prefix"]
    suffix = segments["salphaseion_aes_suffix"]
    if prefix["length"] != 64 or suffix["length"] != 64:
        raise AssertionError("SALPH halves are no longer 64/64 characters")
    return {
        "pair": "aes_prefix (first) / aes_suffix (second)",
        "basis": "page_structure_audit segment lengths, both 64",
        "note": (
            "No established link to dbbi/faed or to any other pair: these "
            "are the two halves of one already-tracked ciphertext, not "
            "independently meaningful plaintext."
        ),
    }


def matrix_rows_and_indices(color_result):
    """Reconstruct the two matrix rows, row sums, and Architect rails."""
    matrix, sum_list = matrixsumlist(color_result["prime_value"])
    if sum_list != EXPECTED_SUM_LIST:
        raise AssertionError(f"unexpected sum list: {sum_list}")
    architect_words, first_word_after_choice = load_architect_words()
    selected = bounded_indexings(architect_words, sum_list)["forward_one"]
    first_edges, last_edges = edge_letters(selected)
    return {
        "matrix": matrix,
        "basis": "prime_matrixsum_reconstruction, re-derived fresh",
        "note": (
            "16 and 7 are used together with 23 as three word POSITIONS "
            f"({sum_list}), selecting {selected} as one ordered triple, not "
            "as two independent channels. BUT and HYE both draw one letter "
            "from each of the three selected words -- so this pair does not "
            "split along a first/second-channel axis the way dbbi/faed or "
            "aes_prefix/aes_suffix do; it is a position triple, not a "
            "two-pole duality, despite superficially looking like one."
        ),
        "selected_words": selected,
        "first_edges": first_edges,
        "last_edges": last_edges,
    }


def but_hye_rail(matrix_result):
    """Pair: BUT (initials) / HYE (finals), and its real, verified link to
    the dbbi/faed escape-pair mirror hypothesis (Phase 34)."""
    first_edges = matrix_result["first_edges"]
    last_edges = matrix_result["last_edges"]
    if first_edges != "but" or last_edges != "hye":
        raise AssertionError(f"unexpected rails: {first_edges}/{last_edges}")
    nine_symbols_first = "".join(c for c in first_edges if c in "abcdefghi")
    nine_symbols_last = "".join(c for c in last_edges if c in "abcdefghi")
    if nine_symbols_first != "b" or nine_symbols_last != "he":
        raise AssertionError("a-i rail symbols changed")
    if mirror9(nine_symbols_first) != nine_symbols_last[0]:
        raise AssertionError("B/H mirror relationship no longer holds")
    return {
        "pair": "BUT (beginnings) / HYE (endings)",
        "basis": "prime_matrixsum_reconstruction, re-derived fresh",
        "real_link_found": True,
        "linked_to": "dbbi_escape_pair / faed_escape_mirror_hypothesis",
        "note": (
            "This is the one pair with a genuine, already-established, "
            "code-verified cross-link (Phase 34): filtering BUT/HYE to "
            "a-i symbols gives 'b' and 'he'; mirror9('b') == 'h' with 'e' "
            "as the fixed center. 'b' is dbbi's real, decisively-fitted "
            "escape pair {b,e}; 'h' gives faed's mirror-hypothesis escape "
            "pair {h,e} -- not faed's own best-fit pair, which is {g,i}. "
            "So B consistently associates with dbbi and H with faed's "
            "mirror hypothesis specifically, and this does not flip "
            "anywhere in its own derivation."
        ),
    }


def half_better_half():
    """Pair: "half" / "better half" -- flagged as having two incompatible
    prior readings in this project's own history, not one settled pair."""
    return {
        "pair": '"half" / "better half"',
        "basis": "Phase 3.2.2 plaintext + Phase 54/78 FINDINGS.md entries",
        "real_link_found": False,
        "note": (
            "Two incompatible readings already exist in this project's own "
            "history. (1) Phase 78, currently operational in the "
            "binary-key-material sweep machinery: 'half and better half' "
            "describes two 32-byte private keys packed into one 80-byte "
            "decrypted plaintext -- an internal structure of a single blob, "
            "not a pairing between SalPhaseIon and Cosmic Duality. (2) A "
            "community theory (bitkek, message 60359): 'half = phase 3.2.2 "
            "AES / better half = cosmic duality' -- tested directly as an "
            "AES passphrase in Phase 54 and came back negative. This pair "
            "is not settled, and forcing it into the SalPhaseIon/Cosmic "
            "textarea pair specifically would adopt the already-falsified "
            "reading over the currently-operational one."
        ),
    }


def audit(html_path=DEFAULT_HTML):
    page_report = audit_page(html_path)
    yellow_blue = yellow_blue_values()
    textareas = textarea_order(page_report)
    halves = salph_halves(page_report)
    matrix_result = matrix_rows_and_indices(yellow_blue["color_result"])
    rail = but_hye_rail(matrix_result)
    half = half_better_half()

    pairs = {
        "yellow_blue": {
            key: value
            for key, value in yellow_blue.items()
            if key != "color_result"
        },
        "matrix_rows": {
            "pair": f"row 1 {matrix_result['matrix'][0]} / row 2 {matrix_result['matrix'][1]}",
            "basis": matrix_result["basis"],
            "note": (
                "These rows are produced from the yellow-one prime 574061. "
                "This is a real cross-artifact edge, but the complementary "
                "rose value does not produce a second matrix channel."
            ),
        },
        "total_split": {
            "pair": "row sum 16 / row sum 7 (total 23)",
            "basis": matrix_result["basis"],
            "note": matrix_result["note"],
        },
        "but_hye_rail": rail,
        "salph_halves": halves,
        "half_better_half": half,
        "textareas": textareas,
    }
    established_edges = (
        "yellow-one prime 574061 -> matrix rows [5,7,4]/[0,6,1]",
        "matrix rows -> row sums 16/7 and total 23",
        "23/16/7 -> BOTH/ULTIMATELY/THE -> BUT/HYE "
        "(not pole-preserving: both rails use all three positions)",
        "BUT/HYE -> dbbi {b,e} / faed mirror hypothesis {h,e}",
    )
    return {
        "pairs": pairs,
        "established_edges": established_edges,
        "verdict": (
            "No single consistent left/right assignment spans all seven "
            "listed pairs. Contrary to the earlier version of this audit, "
            "several real edges do exist: yellow-one produces the prime, the "
            "prime produces the matrix rows/sums, and 23/16/7 produces both "
            "rails. But this is not a dual-channel mapping: the rose pole is "
            "unused, and BOTH/ULTIMATELY/THE jointly feed both BUT and HYE, "
            "so row-1/row-2 polarity is not preserved into the rails. A "
            "separate real link maps BUT/HYE to dbbi {b,e} and faed's "
            "mirror-hypothesis {h,e}. The "
            "'half and better half' pair is not settled at all -- it has "
            "two incompatible prior readings, and the one that would bridge "
            "it to SalPhaseIon/Cosmic Duality specifically already failed "
            "a direct oracle test (Phase 54). The model as framed -- one "
            "chain spanning all seven pairs -- fails, per the document's "
            "own stated rejection criterion: the established dependency "
            "chain is real, but it is not one conserved two-pole channel."
        ),
    }


def print_report(report):
    for name, pair in report["pairs"].items():
        print(f"[*] {name}: {pair['pair']}")
        print(f"    basis: {pair['basis']}")
        if "note" in pair:
            print(f"    note: {pair['note']}")
    print("[*] established dependency edges:")
    for edge in report["established_edges"]:
        print(f"    {edge}")
    print(f"[*] verdict: {report['verdict']}")


def self_test():
    report = audit()
    assert set(report["pairs"]) == {
        "yellow_blue",
        "matrix_rows",
        "total_split",
        "but_hye_rail",
        "salph_halves",
        "half_better_half",
        "textareas",
    }
    assert len(report["established_edges"]) == 4
    assert "574061" in report["pairs"]["yellow_blue"]["pair"]
    print(
        "[*] self-test OK: all 7 declared pairs covered; real dependency "
        "edges separated from conserved-polarity claims"
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", type=Path, default=DEFAULT_HTML)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()

    report = audit(args.html)
    print_report(report)


if __name__ == "__main__":
    main()
