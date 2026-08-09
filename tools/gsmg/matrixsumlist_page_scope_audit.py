#!/usr/bin/env python3
"""Test whether SalPhaseIon page syntax fixes ``matrixsumlist`` operand scope.

The only tempting source-native reduction is the visual parallel

    DBBI [binary ASCII matrixsumlist] FAED
    AES64 [binary ASCII enter] AES64

This audit records exactly where that parallel holds and where it stops.  It
does not execute a matrix transform or use an AES oracle to select a reading.
"""

import argparse
from pathlib import Path

from page_structure_audit import DEFAULT_HTML, audit as audit_page
from salphaseion_operand_binding_audit import audit as audit_bindings
from telegram_guide_neighborhood_audit import audit as audit_guide
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


def audit(html_path=DEFAULT_HTML, export_dir=DEFAULT_EXPORT_DIR):
    page = audit_page(html_path)
    salph = page["salphaseion"]
    segments = salph["segments"]
    by_name = {segment["name"]: segment for segment in segments}
    order = tuple(segment["name"] for segment in segments)
    if order != EXPECTED_ORDER:
        raise AssertionError("SalPhaseIon segment order changed")

    binary_instruction_names = tuple(
        segment["name"]
        for segment in segments
        if segment["alphabet"] == "ab" and segment["decoded"]
    )
    binary_islands = tuple(
        {
            "name": name,
            "decoded": by_name[name]["decoded"],
            "left": order[order.index(name) - 1],
            "right": order[order.index(name) + 1],
            "left_length": by_name[order[order.index(name) - 1]]["length"],
            "right_length": by_name[order[order.index(name) + 1]]["length"],
        }
        for name in binary_instruction_names
    )

    bindings = audit_bindings(html_path)
    guide = audit_guide(Path(export_dir))
    roles = {
        "postfix_to_dbbi": {
            "page_support": "matrixsumlist immediately follows DBBI",
            "external_support": (
                "the community guide applies a matrix/row-sum operation to DBBI"
            ),
            "limitation": (
                "the guide predates the selected 31 characters, was fitted to "
                "prime positions, and has no authenticated output"
            ),
        },
        "prefix_to_faed": {
            "page_support": "matrixsumlist immediately precedes FAED",
            "external_support": "none",
            "limitation": "the guide author explicitly reports no FAED pattern",
        },
        "infix_dbbi_faed": {
            "page_support": (
                "matrixsumlist is a binary-ASCII island between two a-i streams, "
                "parallel in shape to enter between two Base64 streams"
            ),
            "external_support": "none selecting a relationship operation",
            "limitation": (
                "unlike the AES halves, DBBI and FAED have unequal lengths and no "
                "independently validated join operation"
            ),
        },
    }

    return {
        "source": str(html_path),
        "segment_order": order,
        "binary_instruction_names": binary_instruction_names,
        "binary_islands": binary_islands,
        "aes_join": {
            "half_lengths": tuple(salph["embedded_enter_aes_half_lengths"]),
            "decoded_bytes": salph["aes_decoded_bytes"],
            "independently_structured": True,
        },
        "matrix_neighbors": {
            "left_length": by_name["dbbi"]["length"],
            "right_length": by_name["faed"]["length"],
            "equal_lengths": by_name["dbbi"]["length"] == by_name["faed"]["length"],
            "validated_join": False,
        },
        "page_uses_mixed_instruction_positions": {
            "between": ("matrixsumlist", "enter"),
            "after_payload": ("lastwordsbeforearchichoice", "thispassword", "anstoo"),
            "before_payload": ("sha256 our first hint is your last command",),
        },
        "surviving_roles": roles,
        "strictly_supported_binding_models": bindings["strictly_supported_models"],
        "guide_controls": {
            "segmentation_challenge": guide["segmentation_challenge"],
            "segmentation_answer": guide["segmentation_answer"],
            "faed_answer": guide["faed_answer"],
            "no_progress": guide["no_progress"],
        },
        "verdict": (
            "The page-level binary-island parallel is exact, but it does not fix "
            "matrixsumlist scope. Enter has an independently validated equal-half "
            "join; DBBI/FAED do not. Postfix, prefix, and infix readings all remain "
            "syntactically possible, so G3 still fails and no transform is admitted."
        ),
    }


def self_test():
    report = audit()
    assert report["binary_instruction_names"] == (
        "abba_matrix_instruction",
        "abba_enter_instruction",
    )
    assert tuple(item["decoded"] for item in report["binary_islands"]) == (
        "matrixsumlist",
        "enter",
    )
    assert report["aes_join"] == {
        "half_lengths": (64, 64),
        "decoded_bytes": 96,
        "independently_structured": True,
    }
    assert report["matrix_neighbors"] == {
        "left_length": 91,
        "right_length": 570,
        "equal_lengths": False,
        "validated_join": False,
    }
    assert set(report["surviving_roles"]) == {
        "postfix_to_dbbi",
        "prefix_to_faed",
        "infix_dbbi_faed",
    }
    assert report["strictly_supported_binding_models"] == ()
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", type=Path, default=DEFAULT_HTML)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    report = audit(args.html, args.export_dir)
    print(f"[*] binary instruction islands: {report['binary_islands']}")
    print(f"[*] validated AES join: {report['aes_join']}")
    print(f"[*] DBBI/FAED neighbors: {report['matrix_neighbors']}")
    print(f"[*] surviving roles: {tuple(report['surviving_roles'])}")
    print(f"[*] verdict: {report['verdict']}")
    if args.self_test:
        self_test()
        print("[*] self-test OK")


if __name__ == "__main__":
    main()
