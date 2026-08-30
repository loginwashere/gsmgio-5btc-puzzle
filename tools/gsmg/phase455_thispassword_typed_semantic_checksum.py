#!/usr/bin/env python3
"""Phase 455 typed semantic checksum for the three `thispassword` roles.

This module re-derives the frozen structural facts and evaluates a
pre-registered compatibility matrix. It generates no password material,
decrypts nothing, performs no oracle calls, and applies no weighted score.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from page_structure_audit import DEFAULT_HTML, audit as audit_page
from salphaseion_operand_binding_audit import (
    EXPECTED_SEGMENTS,
    fixed_local_bindings,
)
from thispassword_role_identifiability_audit import (
    check_literal_stream_markers,
    check_solved_stage_grammar_analog,
)


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent.parent
MANIFEST_PATH = SCRIPT_DIR / "phase455_typed_constraint_manifest.json"
RESULT_PATH = SCRIPT_DIR / "phase455_result.json"
EXPECTED_MANIFEST_SHA256 = (
    "4eaa983c5c1fc1415d4d78de0cea7ed16fbcd6b5cc2ef656d49bd2b3971590dd"
)

ROLES = (
    "password_for_faed",
    "faed_answer_is_password",
    "password_for_salph_blob",
)
AXES = (
    "literal_page_order",
    "input_output_type",
    "enterability",
    "hash_state",
    "result_class",
    "explicit_cardinality_length",
    "object_consumed",
)
CELL_STATES = ("compatible", "unbound", "contradicted")
VERDICTS = (
    "one_role_survives",
    "multiple_roles_survive",
    "all_roles_survive",
    "constraint_system_inconsistent",
)


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest() -> dict:
    if sha256_path(MANIFEST_PATH) != EXPECTED_MANIFEST_SHA256:
        raise AssertionError("Phase 455 manifest digest drifted")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest["phase"] != 455:
        raise AssertionError("wrong manifest phase")
    if tuple(manifest["roles"]) != ROLES:
        raise AssertionError("role list drifted")
    if tuple(manifest["axes"]) != AXES:
        raise AssertionError("constraint axes drifted")
    if tuple(manifest["cell_states"]) != CELL_STATES:
        raise AssertionError("cell-state vocabulary drifted")
    if tuple(manifest["verdict_vocabulary"]) != VERDICTS:
        raise AssertionError("verdict vocabulary drifted")

    protocol = manifest["protocol"]
    if sha256_path(ROOT / protocol["path"]) != protocol["sha256"]:
        raise AssertionError("frozen protocol drifted")
    for row in manifest["inputs"]:
        if sha256_path(ROOT / row["path"]) != row["sha256"]:
            raise AssertionError(f"pinned input drifted: {row['path']}")
    if sha256_path(DEFAULT_HTML) != manifest["authenticated_html_sha256"]:
        raise AssertionError("authenticated SalPhaseIon HTML drifted")
    if not all(manifest["prohibitions"].values()):
        raise AssertionError("a required Phase 455 prohibition was disabled")
    return manifest


def derive_authenticated_facts() -> dict:
    page = audit_page(DEFAULT_HTML)
    segments = page["salphaseion"]["segments"]
    names = tuple(row["name"] for row in segments)
    if names != EXPECTED_SEGMENTS:
        raise AssertionError("literal segment order changed")
    by_name = {row["name"]: row for row in segments}
    bindings = fixed_local_bindings(page)
    marker_check = check_literal_stream_markers(DEFAULT_HTML)
    grammar_check = check_solved_stage_grammar_analog()

    facts = {
        "segment_order": list(names),
        "decoded_local_terms": {
            "last_words": by_name["decimal_instruction_1"]["decoded"],
            "password": by_name["decimal_instruction_2"]["decoded"],
            "sha256": by_name["hash_prefix"]["decoded"],
            "enter": by_name["abba_enter_instruction"]["decoded"],
            "matrix": by_name["abba_matrix_instruction"]["decoded"],
        },
        "fixed_local_bindings": list(bindings),
        "salph_openssl_salted_header": True,
        "salph_decoded_bytes": page["salphaseion"]["aes_decoded_bytes"],
        "enter_split_offsets": page["salphaseion"][
            "embedded_enter_aes_half_lengths"
        ],
        "enter_is_between_salph_halves": (
            by_name["salphaseion_aes_prefix"]["end"]
            == by_name["abba_enter_instruction"]["start"]
            and by_name["abba_enter_instruction"]["end"]
            == by_name["salphaseion_aes_suffix"]["start"]
        ),
        "explicit_attachment_marker_present": marker_check[
            "explicit_attachment_marker_present"
        ],
        "deictic_vocabulary_present": marker_check[
            "deictic_vocabulary_present"
        ],
        "postpositive_solved_grammar_analog_exists": grammar_check[
            "postpositive_label_analog_exists"
        ],
        "explicit_password_length_present": False,
        "explicit_password_target_present": False,
    }
    if facts["decoded_local_terms"] != {
        "last_words": "lastwordsbeforearchichoice",
        "password": "thispassword",
        "sha256": "sha256 our first hint is your last command",
        "enter": "enter",
        "matrix": "matrixsumlist",
    }:
        raise AssertionError("authenticated decoded terms changed")
    if facts["enter_split_offsets"] != [64, 64]:
        raise AssertionError("SALPH enter split changed")
    if not facts["enter_is_between_salph_halves"]:
        raise AssertionError("enter no longer reconstructs the SALPH halves")
    if facts["explicit_attachment_marker_present"]:
        raise AssertionError("new attachment marker requires matrix revision")
    if facts["postpositive_solved_grammar_analog_exists"]:
        raise AssertionError("new solved analog requires matrix revision")
    return facts


def cell(state: str, note: str) -> dict:
    if state not in CELL_STATES:
        raise ValueError(state)
    return {"state": state, "note": note}


def frozen_matrix(facts: dict) -> dict:
    """Return the matrix frozen in the protocol; facts are checked first."""
    if facts["explicit_attachment_marker_present"]:
        raise AssertionError("cannot apply frozen matrix after evidence drift")
    if not facts["salph_openssl_salted_header"]:
        raise AssertionError("SALPH object type drifted")

    return {
        "password_for_faed": {
            "literal_page_order": cell(
                "compatible", "requires an unmarked backward reach across lastwords"
            ),
            "input_output_type": cell(
                "unbound", "password-like input and decoded-FAED output are not fixed"
            ),
            "enterability": cell(
                "unbound", "FAED has no authenticated entry interface"
            ),
            "hash_state": cell(
                "unbound", "the separate SHA instruction does not type this value"
            ),
            "result_class": cell(
                "unbound", "decoded FAED content is not independently fixed"
            ),
            "explicit_cardinality_length": cell(
                "unbound", "no authenticated password length or cardinality"
            ),
            "object_consumed": cell(
                "unbound", "FAED is claimed by the role but attachment is unmarked"
            ),
        },
        "faed_answer_is_password": {
            "literal_page_order": cell(
                "compatible", "requires an unmarked backward label on the prior result"
            ),
            "input_output_type": cell(
                "compatible", "a FAED-derived answer may carry the literal password class"
            ),
            "enterability": cell(
                "unbound", "the eventual consumer of the labeled password is absent"
            ),
            "hash_state": cell(
                "unbound", "the separate SHA instruction does not type this value"
            ),
            "result_class": cell(
                "compatible", "thispassword is compatible with a password result class"
            ),
            "explicit_cardinality_length": cell(
                "unbound", "no authenticated password length or cardinality"
            ),
            "object_consumed": cell(
                "unbound", "the role labels a result but supplies no local consumer"
            ),
        },
        "password_for_salph_blob": {
            "literal_page_order": cell(
                "compatible", "requires an unmarked forward reach to SALPH"
            ),
            "input_output_type": cell(
                "compatible", "a passphrase-like input fits the OpenSSL salted envelope"
            ),
            "enterability": cell(
                "compatible",
                "SALPH consumes a cryptographic passphrase; enter is only reconstruction",
            ),
            "hash_state": cell(
                "unbound", "the separate SHA instruction does not type this value"
            ),
            "result_class": cell(
                "unbound", "the SALPH plaintext class is not independently fixed"
            ),
            "explicit_cardinality_length": cell(
                "unbound", "no authenticated password length or cardinality"
            ),
            "object_consumed": cell(
                "unbound", "SALPH is consumable but thispassword attachment is unmarked"
            ),
        },
    }


def classify(matrix: dict) -> tuple[list[str], str]:
    survivors = [
        role
        for role in ROLES
        if not any(row["state"] == "contradicted" for row in matrix[role].values())
    ]
    if len(survivors) == 3:
        verdict = "all_roles_survive"
    elif len(survivors) == 2:
        verdict = "multiple_roles_survive"
    elif len(survivors) == 1:
        verdict = "one_role_survives"
    else:
        verdict = "constraint_system_inconsistent"
    return survivors, verdict


def build_report(manifest: dict) -> dict:
    facts = derive_authenticated_facts()
    matrix = frozen_matrix(facts)
    for role in ROLES:
        if tuple(matrix[role]) != AXES:
            raise AssertionError(f"axis order drifted for {role}")
    survivors, verdict = classify(matrix)
    contradiction_counts = {
        role: sum(
            row["state"] == "contradicted" for row in matrix[role].values()
        )
        for role in ROLES
    }
    if contradiction_counts != manifest["expected_preexecution_contradictions"]:
        raise AssertionError("contradiction count differs from pre-registration")
    return {
        "phase": 455,
        "date": manifest["date"],
        "manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "facts": facts,
        "matrix": matrix,
        "state_totals": {
            role: dict(Counter(row["state"] for row in matrix[role].values()))
            for role in ROLES
        },
        "contradiction_counts": contradiction_counts,
        "surviving_roles": survivors,
        "verdict": verdict,
        "role_selected": None if len(survivors) != 1 else survivors[0],
        "typed_discriminant_found": len(survivors) == 1,
        "oracle_calls": 0,
        "password_materials_generated": 0,
        "decryptions_attempted": 0,
        "weighted_scores_computed": 0,
        "gap_closures": 0,
        "disposition": "typed_constraints_confirm_underdetermination",
    }


def self_test(manifest: dict) -> None:
    report = build_report(manifest)
    assert report["verdict"] == "all_roles_survive"
    assert report["surviving_roles"] == list(ROLES)
    assert report["role_selected"] is None
    assert report["typed_discriminant_found"] is False
    assert report["contradiction_counts"] == {role: 0 for role in ROLES}
    assert all(set(report["matrix"][role]) == set(AXES) for role in ROLES)
    assert all(
        row["state"] in CELL_STATES
        for role in ROLES
        for row in report["matrix"][role].values()
    )
    assert report["oracle_calls"] == 0
    assert report["password_materials_generated"] == 0
    assert report["decryptions_attempted"] == 0
    assert report["weighted_scores_computed"] == 0
    assert report["gap_closures"] == 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    manifest = load_manifest()
    if args.self_test:
        self_test(manifest)
        print("Phase 455 self-test: PASS")
    if args.run:
        report = build_report(manifest)
        RESULT_PATH.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"wrote {RESULT_PATH}")
    if not args.self_test and not args.run:
        print(json.dumps(build_report(manifest), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
