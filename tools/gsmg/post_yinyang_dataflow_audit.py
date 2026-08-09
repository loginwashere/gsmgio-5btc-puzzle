#!/usr/bin/env python3
"""Audit what can supply ``thispassword`` after the BUT/HYE checkpoint.

This audit assumes only the corrected Phase-217 working hypothesis: the
six-digit prime route consumes ``matrixsumlist`` and
``lastwordsbeforearchichoice`` and reaches the BUT/HYE yin-yang recognition
state.  It then applies page order and existing negative coverage to rank the
remaining operand roles.  It does not invent a FAED decoder or select a
password by AES outcome.
"""

import argparse
from pathlib import Path

import architect_choice_literal_password_audit
import binary_hint_operand_audit
from cb_common import BLOBS, QUARANTINED_BLOBS
from minimal_macro_chain_audit import MACRO_PREFIX, audit as audit_macro
from page_structure_audit import DEFAULT_HTML, audit as audit_page
from telegram_export_manifest import DEFAULT_EXPORT_DIR


EXPECTED_ORDER = (
    "dbbi",
    "abba_matrix_instruction",
    "faed",
    "z_separator_1",
    "decimal_instruction_1",
    "z_separator_2",
    "decimal_instruction_2",
    "z_separator_3",
    "hash_prefix",
    "salphaseion_aes_prefix",
    "abba_enter_instruction",
    "salphaseion_aes_suffix",
    "hash_suffix",
)

# Phase 33's already-completed direct family.  This is carried forward as a
# frozen historical result and is deliberately not rerun by this audit.
PRIOR_RAIL_DIRECT_NEGATIVE = {
    "scope": "12 selected-word/rail/EOL forms",
    "cbc_keystrings": 216,
    "keywrap_attempts": 306,
    "blob_count": 4,
    "hits": 0,
    "source": "FINDINGS.md Phase 33 / GSMG_MATRIXSUMLIST_CHECKPOINT.md",
}


def audit(export_path, html_path=DEFAULT_HTML):
    macro = audit_macro(Path(export_path))
    if macro["edge_rails"] != ("but", "hye"):
        raise AssertionError("corrected macro checkpoint changed")

    page = audit_page(Path(html_path))
    segments = page["salphaseion"]["segments"]
    order = tuple(segment["name"] for segment in segments)
    if order != EXPECTED_ORDER:
        raise AssertionError("authenticated SalPhaseIon order changed")
    by_name = {segment["name"]: segment for segment in segments}

    macro_remainder = macro_text_remainder(Path(export_path))
    hint_operands = binary_hint_operand_audit.source_operands(
        Path(export_path).parent
    )
    hint_materials = binary_hint_operand_audit.operand_materials(hint_operands)
    literal_boundary_candidates = (
        architect_choice_literal_password_audit.candidates()
    )

    routes = {
        "recognition_output_is_password": {
            "page_support": (
                "lastwordsbeforearchichoice is immediately followed by thispassword"
            ),
            "status": "closed_for_direct_literal_forms_only",
            "basis": PRIOR_RAIL_DIRECT_NEGATIVE,
            "limitation": (
                "does not rule out a separately specified operation on BUT/HYE; "
                "no such operation is presently selected"
            ),
        },
        "literal_seven_words_are_password": {
            "candidates": literal_boundary_candidates,
            "status": "closed_direct_negative",
            "basis": "Phase 216: 36 current keystrings, 4 blobs, 0 hits",
        },
        "first_hint_or_last_command_is_password": {
            "source_operand_count": len(hint_operands),
            "unique_material_count": len(hint_materials),
            "status": "closed_bounded_direct_negative",
            "basis": "fresh rerun: 162 exact materials, 4 blobs, 0 hits",
            "limitation": (
                "the prose still does not uniquely define what 'our' or "
                "'last command' denotes outside the bounded source-grounded set"
            ),
        },
        "faed_plaintext_is_password": {
            "page_support": (
                "FAED is the nearest preceding undecoded payload once the two "
                "macro instructions are consumed by the prime route"
            ),
            "status": "live_but_decoder_unknown",
            "missing": (
                "FAED segmentation/escape binding",
                "alphabet or other decoding rule",
                "proof that the resulting plaintext is the password",
            ),
        },
        "dbbi_faed_joint_result_is_password": {
            "page_support": (
                "both a-i streams occur before thispassword and yin-yang can "
                "describe a relationship rather than a literal key"
            ),
            "status": "live_but_operator_unknown",
            "missing": (
                "relationship/alignment operation",
                "output serialization",
                "independent result check",
            ),
        },
    }

    return {
        "macro_prefix": MACRO_PREFIX,
        "macro_checkpoint": {
            "sum_list": macro["sum_list"],
            "selected_words": macro["selected_words"],
            "edge_rails": macro["edge_rails"],
            "mirror_state": macro["mirror_state"],
        },
        "macro_remainder": macro_remainder,
        "page_order": order,
        "local_offsets": {
            name: (by_name[name]["start"], by_name[name]["end"])
            for name in (
                "faed",
                "decimal_instruction_1",
                "decimal_instruction_2",
                "hash_prefix",
                "salphaseion_aes_prefix",
                "abba_enter_instruction",
                "salphaseion_aes_suffix",
            )
        },
        "routes": routes,
        "excluded_anchors": {
            "h_ye_but": "circular initial-letter selection removed in Phase 217",
            "vat_salvation": "post-hoc and direct-oracle negative in Phase 96",
        },
        "most_local_live_role": "faed_plaintext_is_password",
        "unresolved_even_under_that_role": (
            "how BUT/HYE or yin-yang selects a FAED decoder",
            "whether DBBI participates in that decoder",
            "whether sha256 consumes the FAED result or its own explicit phrase",
            "literal meaning of trailing anstoo",
        ),
        "verdict": (
            "After carrying forward the direct negatives, the page does not "
            "supply a working literal password. The most local live dataflow is "
            "FAED -> decoded result -> thispassword -> the adjacent SHA/SALPH "
            "region, with DBBI/FAED joint output a less-local alternative. This "
            "is a role assignment, not a decoder: no authenticated operation "
            "currently connects BUT/HYE to FAED, fixes DBBI participation, or "
            "settles SHA operand scope. Further password variants are therefore "
            "not admitted; the next useful evidence must constrain the FAED or "
            "DBBI/FAED decoding relationship."
        ),
    }


def macro_text_remainder(export_path):
    from salphaseion_title_rebus_audit import load_macro

    macro = load_macro(Path(export_path))
    if not macro.startswith(MACRO_PREFIX):
        raise AssertionError("creator macro prefix changed")
    return macro[len(MACRO_PREFIX):]


def oracle_confirmation(export_path):
    """Rerun only the two bounded direct families named in the report."""
    blobs = dict(BLOBS, **QUARANTINED_BLOBS)
    hint_operands = binary_hint_operand_audit.source_operands(
        Path(export_path).parent
    )
    hint_materials = binary_hint_operand_audit.operand_materials(hint_operands)
    hint_hits = binary_hint_operand_audit.run_oracle(hint_materials, blobs)
    literal_candidates = architect_choice_literal_password_audit.candidates()
    literal = architect_choice_literal_password_audit.oracle_check(
        literal_candidates, blobs
    )
    return {
        "hint_materials": len(hint_materials),
        "hint_hits": len(hint_hits),
        "literal_keystrings": literal["tested_keystrings"],
        "literal_hits": sum(len(items) for items in literal["hits"].values()),
    }


def self_test(export_path, html_path=DEFAULT_HTML):
    report = audit(export_path, html_path)
    assert report["macro_checkpoint"]["edge_rails"] == ("but", "hye")
    assert report["most_local_live_role"] == "faed_plaintext_is_password"
    assert report["routes"]["first_hint_or_last_command_is_password"][
        "unique_material_count"
    ] == 162
    assert report["routes"]["literal_seven_words_are_password"]["candidates"] == (
        "as you adequately put the problem is",
        "asyouadequatelyputtheproblemis",
    )
    assert set(report["excluded_anchors"]) == {"h_ye_but", "vat_salvation"}
    assert "decoder_unknown" in report["routes"]["faed_plaintext_is_password"]["status"]
    print("[*] self-test OK: corrected macro checkpoint, exact page order, bounded negative scopes, and surviving dataflow roles")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--export",
        type=Path,
        default=DEFAULT_EXPORT_DIR / "result.json",
    )
    parser.add_argument("--html", type=Path, default=DEFAULT_HTML)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--oracle", action="store_true")
    args = parser.parse_args()
    report = self_test(args.export, args.html) if args.self_test else audit(args.export, args.html)
    print(f"[*] most local live role: {report['most_local_live_role']}")
    for name, route in report["routes"].items():
        print(f"    {name}: {route['status']}")
    print("[*] unresolved:")
    for item in report["unresolved_even_under_that_role"]:
        print(f"    - {item}")
    if args.oracle:
        print(f"[*] bounded oracle confirmation: {oracle_confirmation(args.export)}")
    print(f"[*] verdict: {report['verdict']}")


if __name__ == "__main__":
    main()
