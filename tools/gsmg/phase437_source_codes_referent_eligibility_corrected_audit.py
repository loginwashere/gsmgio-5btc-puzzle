#!/usr/bin/env python3
"""Phase 437: corrected execution of the Phase 436 SOURCE CODES gate."""

import argparse
import json
from pathlib import Path

from findings_store import read_findings
import phase436_source_codes_referent_eligibility_audit as phase436
import p32_sibling_password_audit as phase270
from data import VALIDATION_NUM


REPO_ROOT = Path(__file__).resolve().parents[2]
PHASE418_PROTOCOL = REPO_ROOT / "doc" / "Brainstorms" / "2026-08-26 - Phase 418 P32TRAILING Solution-Complete Blinded Reconstruction Pre-Registration.md"
REQUIRED_COMPLETED_PHASES = (118, 265, 268, 269, 270, 370, 416, 417, 421, 423)


def audit():
    derived = phase270.derive_sibling_outputs()
    components = derived["components"]
    live = {
        "phase32_plaintext": phase436.digest_record(derived["phase32_plaintext"]),
        "encoded_321": phase436.digest_record(components["encoded_321"]),
        "cipher_321": phase436.digest_record(derived["cipher_321"]),
        "answer_321": phase436.digest_record(derived["answer_321"]),
        "validation_num": phase436.digest_record(components["validation_num"]),
        "answer_322": phase436.digest_record(derived["answer_322"]),
    }
    for name, (length, digest) in phase436.EXPECTED.items():
        if live[name] != {"length": length, "sha256": digest}:
            raise AssertionError(f"authenticated source drifted: {name} -> {live[name]}")
    if components["validation_num"] != VALIDATION_NUM.encode("ascii"):
        raise AssertionError("live validation number differs from data.py")

    candidates, _ = phase270.build_candidates(
        derived["answer_321"], derived["answer_322"],
        derived["phase32_plaintext"], components["offsets"]["p32_start"],
    )
    materials = phase270.password_materials(candidates)
    base_values = {row["value"] for row in candidates}
    material_values = {row["material"] for row in materials}
    if (len(base_values), len(material_values)) != (25, 50):
        raise AssertionError("Phase 270 inventory drifted from 25 bases / 50 materials")

    raw_sources = {
        "raw_encoded_321": components["encoded_321"],
        "cp1141_beaufort_ciphertext": derived["cipher_321"].encode("ascii"),
    }
    for label, value in raw_sources.items():
        if value in base_values or value in material_values:
            raise AssertionError(f"{label} unexpectedly entered Phase 270 inventory")

    findings = read_findings()
    missing_completed = tuple(
        phase for phase in REQUIRED_COMPLETED_PHASES
        if f"## Phase {phase} --" not in findings
    )
    if missing_completed:
        raise AssertionError(f"required completed findings missing: {missing_completed}")
    if not PHASE418_PROTOCOL.is_file():
        raise AssertionError("Phase 418 preregistration artifact missing")
    if "## Phase 418 --" in findings:
        raise AssertionError("Phase 418 documentary premise changed; review correction before rerun")

    rows = []
    for referent in phase436.REFERENTS:
        failed = tuple(
            name for name in phase436.GATE_NAMES
            if not referent["gates"][name]
        )
        rows.append({**referent, "failed_gates": failed, "eligible": not failed})

    eligible = tuple(row["id"] for row in rows if row["eligible"])
    authenticated_uncovered_ineligible = tuple(
        row["id"] for row in rows
        if row["gates"]["authenticated"]
        and row["gates"]["genuinely_uncovered"]
        and not row["eligible"]
    )
    if eligible:
        decision = "eligible_referent_requires_separate_execution_preregistration"
    else:
        decision = "no_source_referent_passes_all_gates"

    return {
        "phase": 437,
        "correction": {
            "phase436_decision": "protocol_invalid",
            "phase418_protocol_exists": True,
            "phase418_completed_finding_exists": False,
            "eligibility_rules_changed": False,
        },
        "authenticated_sources": live,
        "phase270_inventory": {"base_count": len(base_values), "material_count": len(material_values)},
        "gate_names": phase436.GATE_NAMES,
        "referent_count": len(rows),
        "referents": tuple(rows),
        "eligible_referents": eligible,
        "authenticated_uncovered_but_ineligible": authenticated_uncovered_ineligible,
        "decision": decision,
        "next_trigger": "new evidence must select raw versus CP1141 versus decoded source and fix prime unit/base/direction/rail/boundary",
        "and_or_authorized": False,
        "password_materials_generated": 0,
        "oracle_calls": 0,
        "gpu_touched": False,
    }


def self_test():
    report = audit()
    assert report["correction"] == {
        "phase436_decision": "protocol_invalid",
        "phase418_protocol_exists": True,
        "phase418_completed_finding_exists": False,
        "eligibility_rules_changed": False,
    }
    assert report["referent_count"] == 11
    assert report["eligible_referents"] == ()
    assert report["authenticated_uncovered_but_ineligible"] == (
        "raw_encoded_321", "cp1141_beaufort_ciphertext"
    )
    rows = {row["id"]: row for row in report["referents"]}
    assert rows["raw_encoded_321"]["failed_gates"] == (
        "locally_selected", "unique_representation", "operator_fixed", "unit_boundary_fixed"
    )
    assert rows["parent_prefix"]["failed_gates"] == ("genuinely_uncovered",)
    assert report["and_or_authorized"] is False
    assert report["password_materials_generated"] == report["oracle_calls"] == 0
    assert report["gpu_touched"] is False
    print("[*] Phase 437 self-test OK: 11 referents, 0 eligible, 2 authenticated uncovered raw-source families remain gated")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit()
    if args.self_test:
        self_test()
    payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    elif not args.self_test:
        print(payload, end="")


if __name__ == "__main__":
    main()
