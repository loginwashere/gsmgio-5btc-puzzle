#!/usr/bin/env python3
"""Phase 470 deterministic frontier-actionability audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent.parent
RESULT_PATH = SCRIPT_DIR / "phase470_result.json"

SOURCE_ANCHORS = {
    "doc/GSMG_PHASE467_CLOSED_SYSTEM_CONSTRAINT_CLOSURE.md": (
        "Four variables differ across the maximum assignments:",
        "The Architect relation has the greatest dependency leverage",
    ),
    "doc/GSMG_P456_SEED1_UNRESOLVED_RULE_TRANSFER.md": (
        "Architect edges/mirror | not applicable",
        "all_three_insufficient_comparable_boundaries",
        "Re-running against the same three",
    ),
    "doc/GSMG_P455_THISPASSWORD_TYPED_SEMANTIC_CHECKSUM.md": (
        "all_roles_survive",
    ),
    "doc/GSMG_P449_G_ESC_PAIR_DISCRIMINATION.md": (
        "working prior",
        "remain_unreconciled_with_gi_as_working_prior",
    ),
    "doc/GSMG_TOPOLOGY_AUDIT.md": (
        "Phase 373 asked whether the three `thispassword` roles could be *scored*",
        "Phases 376-377 asked a different question",
    ),
}

SELECTORS = (
    {
        "id": "dbbi_faed_topology",
        "alternatives": ("independent", "symmetric", "dbbi_to_faed"),
        "conditional_downstream_selectors": (),
        "completed_tests": (
            "Phase 371 independent-consumer/page-structure audit",
            "Phase 451 BTCSEED topology synthesis",
            "Phase 467 global constraint closure",
        ),
        "proposed_action": "rescore or re-enumerate existing DBBI/FAED relationships",
        "classification": "duplicate",
        "executable_now": False,
        "heldout_existing_input": False,
        "minimum_new_evidence": "creator evidence or a structurally forced unseen consumer that fixes whether/how the streams interact",
    },
    {
        "id": "faed_escape_pair",
        "alternatives": ("GI", "HE"),
        "conditional_downstream_selectors": (),
        "completed_tests": (
            "Phase 449 pair discrimination",
            "Phases 243/244/249 page-boundary closure",
            "Phase 468 post-observation FF67 conditional calibration",
        ),
        "proposed_action": "reuse FF67 or rescore the same two pairs",
        "classification": "selection_biased_reuse",
        "executable_now": False,
        "heldout_existing_input": False,
        "minimum_new_evidence": "pair-independent validator, genuinely new page variant, or external primary source selecting one pair",
    },
    {
        "id": "thispassword_role",
        "alternatives": ("password_for_faed", "faed_answer_is_password", "password_for_salph_blob"),
        "conditional_downstream_selectors": (),
        "completed_tests": (
            "Phase 373 model-dependent role scoring",
            "Phases 376-377 direct-witness/identifiability audit",
            "Phase 455 typed semantic checksum",
        ),
        "proposed_action": "rescore the same DOM/grammar/creator-reply evidence",
        "classification": "duplicate",
        "executable_now": False,
        "heldout_existing_input": False,
        "minimum_new_evidence": "new attachment marker, consumer, or solved boundary with the same postpositive role grammar",
    },
    {
        "id": "architect_edge_mirror_relation",
        "alternatives": ("not_authenticated", "authenticated"),
        "conditional_downstream_selectors": ("dbbi_faed_topology=dbbi_to_faed", "faed_escape_pair=HE"),
        "completed_tests": (
            "Phases 247-248 and 458 creator/media/selector sweeps",
            "Phase 456 exact transfer to solved Phases 2/3/3.2",
            "Phase 467 global constraint closure",
        ),
        "proposed_action": "test solved/checksum boundaries for an edge/mirror prediction",
        "classification": "duplicate",
        "duplicate_of": "Phase 456",
        "executable_now": False,
        "heldout_existing_input": False,
        "minimum_new_evidence": "new solved boundary with native edge inputs, local mirror instruction, and comparable output role; or independent pre-discovery artifact/consumer",
    },
)


def verify_sources() -> None:
    for relative, anchors in SOURCE_ANCHORS.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        for anchor in anchors:
            if anchor not in text:
                raise AssertionError(f"source anchor drifted: {relative}: {anchor}")


def build_report() -> dict:
    verify_sources()
    rows = [dict(row) for row in SELECTORS]
    executable = [row["id"] for row in rows if row["executable_now"]]
    return {
        "phase": 470,
        "selector_count": len(rows),
        "selectors": rows,
        "executable_current_internal_tests": executable,
        "executable_current_internal_test_count": len(executable),
        "highest_conditional_leverage": "architect_edge_mirror_relation",
        "highest_conditional_leverage_downstream_count": 2,
        "highest_executable_leverage": None,
        "stale_registry_action": {
            "gate": "G-ARCH-001",
            "action": "test already-authenticated solved/checksum boundaries for an edge/mirror prediction",
            "classification": "duplicate_of_phase456",
            "required_correction": "do not repeat Phase 456; wait for a genuinely new eligible boundary or independent artifact",
        },
        "lane_a_blind_followup": {
            "same_ff67_endpoint": "selection_biased_reuse",
            "new_seed_or_null_only": "not_blind",
            "required_input": "independent unseen construction with prediction frozen before inspection",
            "available_now": False,
        },
        "frontier_disposition": "no_currently_executable_internal_selector_test",
        "password_materials_generated": 0,
        "hash_candidates_generated": 0,
        "decryptions_attempted": 0,
        "oracle_calls": 0,
        "rescans_performed": 0,
    }


def structural_self_test() -> None:
    assert len(SELECTORS) == 4
    assert {row["id"] for row in SELECTORS} == {
        "dbbi_faed_topology", "faed_escape_pair", "thispassword_role", "architect_edge_mirror_relation"
    }
    architect = next(row for row in SELECTORS if row["id"] == "architect_edge_mirror_relation")
    assert len(architect["conditional_downstream_selectors"]) == 2
    assert architect["duplicate_of"] == "Phase 456"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=RESULT_PATH)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    structural_self_test()
    report = build_report()
    if args.self_test:
        print("[*] Phase 470 structural/source-anchor self-test OK")
        return
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "selectors": report["selector_count"],
        "executable_now": report["executable_current_internal_test_count"],
        "highest_conditional_leverage": report["highest_conditional_leverage"],
        "stale_action": report["stale_registry_action"]["classification"],
        "disposition": report["frontier_disposition"],
    }, indent=2))


if __name__ == "__main__":
    main()

