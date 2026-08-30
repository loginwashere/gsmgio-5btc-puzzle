#!/usr/bin/env python3
"""Phase 456 Seed-1 transfer audit for three unresolved rules.

The audit replays each rule on its source boundary, then applies the frozen
native-input/local-license/comparable-output gates to Phase 341's three solved
AES boundaries. No new password candidate or oracle query is produced.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import architect_hye_bye_audit
import first_piece_matrix_product_audit
import roman_rail_prime_sum_audit
import solved_boundary_rule_audit


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent.parent
MANIFEST_PATH = SCRIPT_DIR / "phase456_seed1_transfer_manifest.json"
RESULT_PATH = SCRIPT_DIR / "phase456_result.json"
EXPECTED_MANIFEST_SHA256 = (
    "3cee27de78483877025a48ba4c2bb5cd537f461ee45730f342306fbc9c8cd9dc"
)

RULES = (
    "roman_title_c",
    "architect_edges_mirror",
    "matrix_product_ff67",
)
BOUNDARIES = ("phase2", "phase3", "phase3_2")
GATES = (
    "native_input_type",
    "local_operation_license",
    "comparable_output_type",
)
OUTCOMES = (
    "seed1_transfer_supported",
    "seed1_transfer_rejected",
    "insufficient_comparable_boundaries",
    "protocol_invalidated_by_new_precedent",
)


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest() -> dict:
    if sha256_path(MANIFEST_PATH) != EXPECTED_MANIFEST_SHA256:
        raise AssertionError("Phase 456 manifest digest drifted")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest["phase"] == 456
    assert tuple(manifest["rules"]) == RULES
    assert tuple(manifest["boundaries"]) == BOUNDARIES
    assert tuple(manifest["applicability_gates"]) == GATES
    assert tuple(manifest["outcome_vocabulary"]) == OUTCOMES
    protocol = manifest["protocol"]
    if sha256_path(ROOT / protocol["path"]) != protocol["sha256"]:
        raise AssertionError("frozen protocol drifted")
    for row in manifest["inputs"]:
        if sha256_path(ROOT / row["path"]) != row["sha256"]:
            raise AssertionError(f"pinned input drifted: {row['path']}")
    if not all(manifest["prohibitions"].values()):
        raise AssertionError("a required prohibition was disabled")
    return manifest


def source_replays() -> dict:
    roman = roman_rail_prime_sum_audit.audit()
    roman_match = roman["rail_match_rows"]
    if len(roman_match) != 1:
        raise AssertionError("Roman source replay no longer has one rail hit")
    roman_row = roman_match[0]

    architect = architect_hye_bye_audit.structural_audit()
    arch_fixed = architect["fixed"]
    arch_permutations = architect["fixed_word_permutations"]

    matrix = first_piece_matrix_product_audit.audit()
    matrix_fixed = matrix["fixed_operation"]
    matrix_orders = matrix["fixed_matrix_vector_permutations"]

    return {
        "roman_title_c": {
            "reproduced": (
                (roman_row["blue_numeral"], roman_row["yellow_numeral"])
                == ("CDI", "CD")
                and (roman_row["blue_value"], roman_row["yellow_value"])
                == (401, 400)
            ),
            "output": [roman_row["blue_numeral"], roman_row["yellow_numeral"]],
            "values": [roman_row["blue_value"], roman_row["yellow_value"]],
            "branching_factor": len(roman["rail_rows"]),
            "exact_rows": len(roman_match),
            "tie_count": 0,
            "controls": {
                "disclosed_token_pair_rows": len(roman["control_rows"]),
                "disclosed_token_pair_hits": len(roman["control_match_rows"]),
            },
        },
        "architect_edges_mirror": {
            "reproduced": (
                arch_fixed["tokens"] == ("both", "ultimately", "the")
                and arch_fixed["initials"] == "but"
                and arch_fixed["finals"] == "hye"
                and arch_fixed["partial_mirror_finals"] == "bye"
            ),
            "selected_words": list(arch_fixed["tokens"]),
            "rails": [arch_fixed["initials"], arch_fixed["finals"]],
            "output": arch_fixed["partial_mirror_finals"],
            "branching_factor": len(arch_permutations),
            "exact_rows": sum(
                row["partial_mirror_finals"] == "bye"
                for row in arch_permutations
            ),
            "tie_count": sum(
                row["dictionary_output"] for row in arch_permutations
            ) - 1,
            "controls": architect["controls"],
        },
        "matrix_product_ff67": {
            "reproduced": (
                matrix_fixed["output"] == (255, 103)
                and matrix_fixed["serialized_hex_if_bytes"] == "FF67"
            ),
            "output": list(matrix_fixed["output"]),
            "serialized_hex": matrix_fixed["serialized_hex_if_bytes"],
            "branching_factor": matrix_orders["family_size"],
            "exact_rows": matrix_orders["property_counts"]["exact_255_103"],
            "tie_count": 0,
            "controls": {
                "geometric_family_size": matrix["geometric_family"][
                    "raw_family_size"
                ],
                "expanded_operation_classes": matrix[
                    "expanded_digit_assignment_control"
                ]["operation_class_count"],
            },
        },
    }


def solved_boundary_inventory() -> dict:
    baseline = solved_boundary_rule_audit.run()
    if not baseline["promotion_gate_passed"]:
        raise AssertionError("Phase 341 calibration baseline stopped passing")
    by_name = {row["boundary"]: row for row in baseline["boundaries"]}
    if tuple(by_name) != BOUNDARIES:
        raise AssertionError("solved-boundary set drifted")

    components = {
        "phase2": ["causality"],
        "phase3": [
            *solved_boundary_rule_audit.PHASE3_PARTS_FIXED,
            solved_boundary_rule_audit.PHASE3_HEX_PART,
            solved_boundary_rule_audit.PHASE3_FEN_PART,
        ],
        "phase3_2": [
            "jacquefresco",
            "giveitjustonesecond",
            "heisenbergsuncertaintyprinciple",
        ],
    }
    local_operations = {
        "phase2": ["single_component_identity"],
        "phase3": [
            "ordered_concatenation",
            "component_case",
            "component_whitespace",
            "sha256",
        ],
        "phase3_2": [
            "ordered_concatenation",
            "force_lowercase",
            "connected",
            "literal_giveit_prefix",
        ],
    }
    return {
        boundary: {
            "component_count": len(components[boundary]),
            "components": components[boundary],
            "local_operations": local_operations[boundary],
            "phase341_exact_rank": by_name[boundary]["rank"],
            "phase341_candidate_count": by_name[boundary][
                "total_unique_candidates"
            ],
            "phase341_shuffled_hit": by_name[boundary][
                "shuffled_control_found_match"
            ],
        }
        for boundary in BOUNDARIES
    }


def derive_gate_matrix(inventory: dict) -> dict:
    matrix = {}
    for rule in RULES:
        matrix[rule] = {}
        for boundary in BOUNDARIES:
            row = inventory[boundary]
            if rule == "roman_title_c":
                native_input = all(
                    isinstance(component, str) and component
                    for component in row["components"]
                )
            elif rule == "architect_edges_mirror":
                native_input = row["component_count"] >= 3
            elif rule == "matrix_product_ff67":
                native_input = any(
                    component.isdecimal() and len(component) == 6
                    for component in row["components"]
                )
            else:
                raise ValueError(rule)

            # The Phase-341 inventory is exhaustive for the locally licensed
            # construction operations on these three boundaries. None names
            # any Phase-456 candidate operation.
            forbidden_local_ops = {
                "roman_projection",
                "title_c_prefix",
                "three_index_word_selection",
                "beginnings_endings",
                "mirror9",
                "matrix_2x3",
                "matrix_multiply",
                "unsigned_byte_serialization",
            }
            local_license = bool(
                forbidden_local_ops.intersection(row["local_operations"])
            )
            comparable_output = False
            gates = {
                "native_input_type": native_input,
                "local_operation_license": local_license,
                "comparable_output_type": comparable_output,
            }
            failed = [name for name in GATES if not gates[name]]
            matrix[rule][boundary] = {
                "gates": gates,
                "failed_gates": failed,
                "status": "applicable" if not failed else "not_applicable",
                "candidate_count": 0,
                "exact_recovery": False,
                "rank": None,
                "branching_factor": 0,
                "tie_count": 0,
                "shuffled_control": "not_run_no_eligible_main",
                "order_preserving_control": "not_run_no_eligible_main",
            }
    return matrix


def classify_rule(rows: dict, manifest: dict) -> str:
    applicable = [row for row in rows.values() if row["status"] == "applicable"]
    minimum = manifest["phase341_gate"][
        "minimum_applicable_boundaries_for_rule_outcome"
    ]
    if len(applicable) < minimum:
        return "insufficient_comparable_boundaries"
    passed = all(
        row["exact_recovery"]
        and row["rank"] <= manifest["phase341_gate"]["maximum_rank"]
        and row["candidate_count"]
        <= manifest["phase341_gate"]["maximum_candidates_per_boundary"]
        for row in applicable
    )
    return "seed1_transfer_supported" if passed else "seed1_transfer_rejected"


def build_report(manifest: dict) -> dict:
    replays = source_replays()
    if not all(row["reproduced"] for row in replays.values()):
        raise AssertionError("a source replay failed")
    inventory = solved_boundary_inventory()
    gate_matrix = derive_gate_matrix(inventory)
    observed_gate_matrix = {
        rule: {
            boundary: [
                gate_matrix[rule][boundary]["gates"][gate] for gate in GATES
            ]
            for boundary in BOUNDARIES
        }
        for rule in RULES
    }
    if observed_gate_matrix != manifest["expected_gate_matrix"]:
        raise AssertionError(
            "applicability matrix differs from pre-registration; protocol invalid"
        )

    applicable_cells = sum(
        row["status"] == "applicable"
        for rule in gate_matrix.values()
        for row in rule.values()
    )
    if applicable_cells != manifest["expected_applicable_cells"]:
        raise AssertionError("applicable-cell count drifted")
    outcomes = {
        rule: classify_rule(gate_matrix[rule], manifest) for rule in RULES
    }
    return {
        "phase": 456,
        "date": manifest["date"],
        "manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "source_replays": replays,
        "solved_boundary_inventory": inventory,
        "transfer_matrix": gate_matrix,
        "applicable_cells": applicable_cells,
        "total_cells": len(RULES) * len(BOUNDARIES),
        "rule_outcomes": outcomes,
        "overall_verdict": "all_three_insufficient_comparable_boundaries",
        "seed1_support_added": False,
        "rules_rejected": False,
        "gap_closures": 0,
        "new_password_candidates": 0,
        "oracle_calls": 0,
        "decryptions_attempted": 0,
        "disposition": "calibration_not_applicable_output_and_instruction_mismatch",
    }


def self_test(manifest: dict) -> None:
    report = build_report(manifest)
    assert report["applicable_cells"] == 0
    assert report["total_cells"] == 9
    assert set(report["rule_outcomes"].values()) == {
        "insufficient_comparable_boundaries"
    }
    assert report["overall_verdict"] == (
        "all_three_insufficient_comparable_boundaries"
    )
    assert report["seed1_support_added"] is False
    assert report["rules_rejected"] is False
    for rule in RULES:
        assert report["source_replays"][rule]["reproduced"] is True
        for boundary in BOUNDARIES:
            row = report["transfer_matrix"][rule][boundary]
            assert row["status"] == "not_applicable"
            assert row["candidate_count"] == 0
            assert row["rank"] is None
            assert row["branching_factor"] == 0
            assert row["tie_count"] == 0
    assert report["gap_closures"] == 0
    assert report["new_password_candidates"] == 0
    assert report["oracle_calls"] == 0
    assert report["decryptions_attempted"] == 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    manifest = load_manifest()
    if args.self_test:
        self_test(manifest)
        print("Phase 456 self-test: PASS")
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
