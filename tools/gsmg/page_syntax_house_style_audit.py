#!/usr/bin/env python3
"""Phase 238: test whether SalPhaseIon has a reusable operator house style.

This is a structural comparison, not a transform or oracle.  It combines the
byte-exact page segmentation, the one independently fixed local formatting
operator (``enter``), the Phase-101 grammar family, and Phase-236's default
macro model.  The question is deliberately falsification-first: does position,
transport encoding, or nearest-neighbor adjacency predict operator scope well
enough to bind ``matrixsumlist`` or ``thispassword``?
"""

import argparse
import json
from pathlib import Path

import macro_model_disposition_audit
import matrixsumlist_page_scope_audit
import salphaseion_operand_binding_audit
import salphaseion_presentation_binding_audit
from page_structure_audit import DEFAULT_HTML, audit as audit_page
from telegram_export_manifest import DEFAULT_EXPORT_DIR


EXPECTED_ORDER = salphaseion_operand_binding_audit.EXPECTED_SEGMENTS
INSTRUCTION_SEGMENTS = (
    "abba_matrix_instruction",
    "decimal_instruction_1",
    "decimal_instruction_2",
    "hash_prefix",
    "abba_enter_instruction",
    "hash_suffix",
)


def transport(segment_name):
    if segment_name.startswith("abba_"):
        return "binary_ascii"
    if segment_name.startswith("decimal_"):
        return "decimal_transport"
    return "raw_mixed_text"


def slot_inventory(page_report):
    segments = page_report["salphaseion"]["segments"]
    order = tuple(segment["name"] for segment in segments)
    if order != EXPECTED_ORDER:
        raise AssertionError("authenticated SalPhaseIon segment order changed")
    by_name = {segment["name"]: segment for segment in segments}
    rows = []
    for name in INSTRUCTION_SEGMENTS:
        index = order.index(name)
        segment = by_name[name]
        rows.append(
            {
                "name": name,
                "decoded": segment["decoded"],
                "transport": transport(name),
                "left_neighbor": order[index - 1] if index else None,
                "right_neighbor": order[index + 1] if index + 1 < len(order) else None,
                "start": segment["start"],
                "end": segment["end"],
            }
        )
    return tuple(rows)


def role_inventory(page_report, macro_report, matrix_scope):
    model = macro_report["model_comparison"]
    if model["default_working_model"] != "B_six_digit_prime":
        raise AssertionError("Phase-236 default macro model changed")
    if not matrix_scope["aes_join"]["independently_structured"]:
        raise AssertionError("ENTER/AES control lost its independent structure")
    return {
        "matrixsumlist": {
            "status": "default_external_macro_step_but_not_fully_authored",
            "best_current_role": "574061 -> decimal matrix -> [23,16,7]",
            "remaining_judgment_calls": model["models"]["B_six_digit_prime"][
                "remaining_judgment_calls"
            ],
            "local_page_direction_fixed": False,
        },
        "lastwordsbeforearchichoice": {
            "status": "default_external_semantic_selector_but_not_fully_authored",
            "best_current_role": (
                "[23,16,7] indexes the external Architect passage and reaches BUT/HYE"
            ),
            "immediate_page_neighbors_are_operand": False,
            "local_page_direction_fixed": False,
        },
        "thispassword": {
            "status": "deictic_label_unresolved",
            "candidate_roles": (
                "password_for_faed",
                "faed_answer_is_password",
                "password_for_salph_blob",
            ),
            "local_page_direction_fixed": False,
        },
        "sha256_prefix": {
            "status": "algorithm_fixed_operand_referent_unresolved",
            "fixed": "SHA-256 is named and the phrase is immediately before SALPH",
            "unresolved": (
                "what 'our first hint' denotes",
                "what 'your last command' denotes",
                "whether the equality phrase supplies bytes or describes control flow",
            ),
            "local_page_direction_fixed": False,
        },
        "enter": {
            "status": "fixed_infix_formatting_join",
            "best_current_role": (
                "remove binary-ASCII ENTER between two 64-character halves to "
                "reconstitute the authenticated 128-character SALPH Base64 blob"
            ),
            "left_length": matrix_scope["aes_join"]["half_lengths"][0],
            "right_length": matrix_scope["aes_join"]["half_lengths"][1],
            "local_page_direction_fixed": True,
        },
        "sha256_suffix": {
            "status": "sha_marker_fixed_tail_unresolved",
            "fixed": "shabef mechanically denotes sha256",
            "unresolved": "literal anstoo",
            "local_page_direction_fixed": False,
        },
    }


def direction_rules(roles):
    return {
        "all_instructions_are_prefix": {
            "survives": False,
            "counterexample": "ENTER is a fixed infix join",
        },
        "all_instructions_are_postfix": {
            "survives": False,
            "counterexample": "the SHA phrase precedes SALPH and ENTER is infix",
        },
        "between_payloads_means_join": {
            "survives": False,
            "counterexample": (
                "ENTER has an authenticated equal-half join; matrixsumlist sits "
                "between unequal DBBI/FAED streams with no validated join"
            ),
        },
        "transport_encoding_fixes_role": {
            "survives": False,
            "counterexample": (
                "binary ASCII carries both fixed formatting ENTER and unresolved "
                "matrixsumlist; raw SHA markers occur on opposite sides of SALPH"
            ),
        },
        "nearest_page_neighbor_is_operand": {
            "survives": False,
            "counterexample": (
                "the best current lastwords reading selects an external Architect "
                "passage, not either immediate page neighbor"
            ),
        },
        "sha_prefix_and_suffix_form_a_complete_bracket": {
            "survives": False,
            "counterexample": (
                "only the SHA marker is common; the prefix operand referents and "
                "literal suffix anstoo are unresolved"
            ),
        },
    }


def audit(
    html_path=DEFAULT_HTML,
    export_path=DEFAULT_EXPORT_DIR / "result.json",
):
    page = audit_page(Path(html_path))
    matrix_scope = matrixsumlist_page_scope_audit.audit(
        Path(html_path), Path(export_path).parent
    )
    bindings = salphaseion_operand_binding_audit.audit(Path(html_path))
    presentation = salphaseion_presentation_binding_audit.audit(Path(html_path))
    macro = macro_model_disposition_audit.audit(Path(export_path))
    roles = role_inventory(page, macro, matrix_scope)
    rules = direction_rules(roles)

    # Phase 101's 54 models contain a three-way matrix-direction axis. Under
    # the current *working* Model B, project that axis away without claiming
    # the source authenticated the projection. The unresolved password/SHA/
    # tail axes remain 3 x 3 x 2 = 18.
    projected_models = {
        (model.password_role, model.sha_operand, model.tail_role)
        for model in bindings["models"]
    }
    projected_total = {
        item
        for item in projected_models
        if item[2] == "community_expansion_answer_too"
    }

    return {
        "source": page["source"],
        "segment_order": tuple(
            segment["name"] for segment in page["salphaseion"]["segments"]
        ),
        "slots": slot_inventory(page),
        "roles": roles,
        "directional_rule_controls": rules,
        "rules_tested": len(rules),
        "rules_surviving": tuple(
            name for name, result in rules.items() if result["survives"]
        ),
        "presentation_binding_candidates": presentation[
            "binding_candidates_found"
        ],
        "phase101_model_family": {
            "full_models": len(bindings["models"]),
            "strictly_supported": len(bindings["strictly_supported_models"]),
            "conditional_model_b_projection": len(projected_models),
            "conditionally_total_only_with_answer_too": len(projected_total),
            "projection_is_creator_authenticated": False,
        },
        "gates": {
            "empirical_uniform_house_style_found": bool(
                tuple(name for name, result in rules.items() if result["survives"])
            ),
            "matrixsumlist_local_direction_fixed": roles["matrixsumlist"][
                "local_page_direction_fixed"
            ],
            "thispassword_consumer_fixed": roles["thispassword"][
                "local_page_direction_fixed"
            ],
            "new_transform_or_oracle_authorized": False,
        },
        "verdict": (
            "The page has mixed syntax, not an empirical uniform house style. "
            "ENTER is the only locally fixed operator and works as an infix "
            "formatting join. The best current matrixsumlist/lastwords readings "
            "come from the external creator macro and Architect source, not from "
            "page-neighbor direction. Encoding, position, adjacency, and the SHA "
            "prefix/suffix do not generalize into a rule that binds matrixsumlist "
            "or thispassword. Under working Model B the old 54-model family can "
            "be conditionally projected to 18 residual password/SHA/tail models, "
            "but zero source-strict model emerges and no transform is admitted."
        ),
    }


def self_test(
    html_path=DEFAULT_HTML,
    export_path=DEFAULT_EXPORT_DIR / "result.json",
):
    report = audit(html_path, export_path)
    assert report["segment_order"] == EXPECTED_ORDER
    assert tuple(row["decoded"] for row in report["slots"]) == (
        "matrixsumlist",
        "lastwordsbeforearchichoice",
        "thispassword",
        "sha256 our first hint is your last command",
        "enter",
        "sha256 + unresolved literal anstoo",
    )
    assert report["roles"]["enter"]["local_page_direction_fixed"]
    assert not report["roles"]["matrixsumlist"]["local_page_direction_fixed"]
    assert report["rules_tested"] == 6
    assert report["rules_surviving"] == ()
    assert report["presentation_binding_candidates"] == ()
    assert report["phase101_model_family"] == {
        "full_models": 54,
        "strictly_supported": 0,
        "conditional_model_b_projection": 18,
        "conditionally_total_only_with_answer_too": 9,
        "projection_is_creator_authenticated": False,
    }
    assert not report["gates"]["empirical_uniform_house_style_found"]
    assert not report["gates"]["new_transform_or_oracle_authorized"]
    print(json.dumps(report, indent=2, default=list))
    print("[*] self-test OK: six syntax rules rejected; no local binding promoted")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", type=Path, default=DEFAULT_HTML)
    parser.add_argument(
        "--export",
        type=Path,
        default=DEFAULT_EXPORT_DIR / "result.json",
    )
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = self_test(args.html, args.export) if args.self_test else audit(
        args.html, args.export
    )
    if args.json and not args.self_test:
        print(json.dumps(report, indent=2, default=list))
    elif not args.self_test:
        print(report["verdict"])


if __name__ == "__main__":
    main()
