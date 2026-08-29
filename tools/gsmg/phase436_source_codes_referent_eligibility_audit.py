#!/usr/bin/env python3
"""Phase 436: oracle-free eligibility audit for `SOURCE CODES` referents."""

import argparse
import hashlib
import json
from pathlib import Path

from findings_store import read_findings
import p32_sibling_password_audit as phase270
from data import VALIDATION_NUM


REPO_ROOT = Path(__file__).resolve().parents[2]

EXPECTED = {
    "phase32_plaintext": (2422, "b82afeb86f9e50848220f9b64b744b821400308aea273a1c949b9d2d0e408a34"),
    "encoded_321": (1539, "bd7a29432546c67c4170e0c523ddbf43ae82d20ee187d1b4dbf7907a0faf4c7b"),
    "cipher_321": (1539, "6d66e0e0e2dfdb812d5ecee2be6f54c1f3b8c84b0d74580686cf2053d76a200e"),
    "answer_321": (1539, "56c43a300e28b86bb43b8dcbae74c43c76bde90b3e1190620fb656f2c94b2241"),
    "validation_num": (149, "71e3af174d533ad2c1c79fce64308f5fdf200f3cc50f059b2f1485a2c5f1765d"),
    "answer_322": (91, "878b7afacc9e35412e76b8506cc8297fa5aeba5381e108dc421b71a0ab8993d8"),
}

REQUIRED_PHASES = (118, 265, 268, 269, 270, 370, 418, 421, 423)
GATE_NAMES = (
    "authenticated",
    "locally_selected",
    "unique_representation",
    "operator_fixed",
    "unit_boundary_fixed",
    "consumer_fixed",
    "genuinely_uncovered",
)


def gate(**values):
    if set(values) != set(GATE_NAMES):
        raise AssertionError(f"gate fields differ: {set(values)}")
    return values


REFERENTS = (
    {
        "id": "matrix_film_screenplay_difference",
        "object": "Matrix film/screenplay dialogue compared with the custom monologue",
        "coverage": "Phase 118 fixed a screenplay/custom word-LCS and tested shared/custom-only prime retention under bases 0 and 1; negative. Phase 235 proves the custom text blends film and screenplay.",
        "status": "covered and representation-nonunique",
        "gates": gate(authenticated=True, locally_selected=True, unique_representation=False, operator_fixed=False, unit_boundary_fixed=False, consumer_fixed=False, genuinely_uncovered=False),
        "failed_gate_reason": "Film versus screenplay and alignment/unit alternatives remain; the strongest fixed family is already negative.",
    },
    {
        "id": "raw_encoded_321",
        "object": "Raw 1,539-byte Phase 3.2.1 encoded block",
        "coverage": "Pinned and exposed as evidence in Phase 418; not an individual Phase 270 candidate and no prime-derived family is registered.",
        "status": "uncovered but ineligible",
        "gates": gate(authenticated=True, locally_selected=False, unique_representation=False, operator_fixed=False, unit_boundary_fixed=False, consumer_fixed=True, genuinely_uncovered=True),
        "failed_gate_reason": "SOURCE CODES does not distinguish raw high bytes from CP1141 ciphertext or decoded letters; prime base/direction/rail are unset.",
    },
    {
        "id": "cp1141_beaufort_ciphertext",
        "object": "CP1141-transcoded 1,539-letter Beaufort ciphertext",
        "coverage": "Pinned and exposed as evidence in Phase 418; used to derive the answer but absent as an individual Phase 270 candidate and prime source.",
        "status": "uncovered but ineligible",
        "gates": gate(authenticated=True, locally_selected=False, unique_representation=False, operator_fixed=False, unit_boundary_fixed=False, consumer_fixed=True, genuinely_uncovered=True),
        "failed_gate_reason": "Equally local raw/transcoded/decoded representations exist; no clause fixes prime base, direction, complement, or extent.",
    },
    {
        "id": "decoded_answer_321",
        "object": "Decoded 1,539-letter Phase 3.2.1 Architect answer",
        "coverage": "Direct whole-answer material is Phase 270-negative; line/word/reverse/whole-block forms are closed by Phases 265, 267, 295, 307, and 314. Pure prime indexing over the whole answer is not registered.",
        "status": "direct use covered; transformed self-source ineligible",
        "gates": gate(authenticated=True, locally_selected=False, unique_representation=False, operator_fixed=False, unit_boundary_fixed=False, consumer_fixed=True, genuinely_uncovered=False),
        "failed_gate_reason": "Reading an instruction as its own SOURCE CODES operand is self-referential and not uniquely selected.",
    },
    {
        "id": "raw_validation_num",
        "object": "Raw 149-digit Phase 3.2.2 validation number",
        "coverage": "Direct passphrase family closed by Phase 265; also unanimous but negative in the Phase 416 panel.",
        "status": "covered direct material",
        "gates": gate(authenticated=True, locally_selected=False, unique_representation=False, operator_fixed=False, unit_boundary_fixed=False, consumer_fixed=True, genuinely_uncovered=False),
        "failed_gate_reason": "The adjacent numeric code is plausible but not selected over its decoded answer, and prime semantics are not fixed.",
    },
    {
        "id": "decoded_answer_322",
        "object": "Decoded 91-letter Phase 3.2.2 answer",
        "coverage": "Phase 270 tested direct use, pure base-0/base-1 primes, established prime-walk selection, sibling compositions, and guide projections; negative.",
        "status": "strongest adjacent-data constructions covered",
        "gates": gate(authenticated=True, locally_selected=False, unique_representation=False, operator_fixed=False, unit_boundary_fixed=False, consumer_fixed=True, genuinely_uncovered=False),
        "failed_gate_reason": "Adjacency does not uniquely select decoded rather than raw data; declared grounded prime consumers are already negative.",
    },
    {
        "id": "parent_prefix",
        "object": "Exact authenticated Phase 3.2 bytes before P32, with/without separator",
        "coverage": "Both exact parent-prefix boundaries were tested raw and SHA-256-hex across six specs in Phase 270; negative.",
        "status": "covered exact boundary",
        "gates": gate(authenticated=True, locally_selected=True, unique_representation=True, operator_fixed=True, unit_boundary_fixed=True, consumer_fixed=True, genuinely_uncovered=False),
        "failed_gate_reason": "The only failed eligibility gate is novelty: this exact source-order reading is closed.",
    },
    {
        "id": "first_piece_stage0",
        "object": "First-piece/Stage-0 prime cells and their projection",
        "coverage": "Phase 270 tested prime source characters, blue/yellow subsets, projection to 3.2.2, and composition; negative.",
        "status": "covered grounded projections",
        "gates": gate(authenticated=True, locally_selected=False, unique_representation=False, operator_fixed=False, unit_boundary_fixed=False, consumer_fixed=True, genuinely_uncovered=False),
        "failed_gate_reason": "A separate creator clue returns to the first piece, but this Architect clause does not choose its grid convention or consumer.",
    },
    {
        "id": "split_final_be_guide",
        "object": "Recovered split-final-BE guide with 23 endpoints / 16 blue / 7 yellow",
        "coverage": "Phase 270 tested prime-rule, token-endpoint, raw-endpoint, and sibling-composition readings; negative.",
        "status": "checkpoint covered under direct consumers",
        "gates": gate(authenticated=True, locally_selected=False, unique_representation=False, operator_fixed=False, unit_boundary_fixed=False, consumer_fixed=True, genuinely_uncovered=False),
        "failed_gate_reason": "The count checkpoint is real but the monologue does not bind endpoint mapping, source string, direction, or AND/OR serialization.",
    },
    {
        "id": "x2sh4y0qb15",
        "object": "Earlier X2SH4Y0QB15 code/riddle block",
        "coverage": "Phases 268-269 tested literal, solved, coordinate, reversal, full-block, and source-order forms; negative.",
        "status": "distant carried-code reading covered",
        "gates": gate(authenticated=True, locally_selected=False, unique_representation=False, operator_fixed=False, unit_boundary_fixed=False, consumer_fixed=False, genuinely_uncovered=False),
        "failed_gate_reason": "It is several stages distant and no creator edge identifies it as THE CODE YOU CARRY.",
    },
    {
        "id": "repository_source_files",
        "object": "Repository implementation/source files",
        "coverage": "Not eligible puzzle bytes; the repository is a later reconstruction and audit environment.",
        "status": "excluded provenance",
        "gates": gate(authenticated=False, locally_selected=False, unique_representation=False, operator_fixed=False, unit_boundary_fixed=False, consumer_fixed=False, genuinely_uncovered=True),
        "failed_gate_reason": "SOURCE CODES cannot authenticate later solver/repository implementation files as creator-authored operands.",
    },
)


def digest_record(value):
    value = value.encode("ascii") if isinstance(value, str) else bytes(value)
    return {"length": len(value), "sha256": hashlib.sha256(value).hexdigest()}


def audit():
    derived = phase270.derive_sibling_outputs()
    components = derived["components"]
    live = {
        "phase32_plaintext": digest_record(derived["phase32_plaintext"]),
        "encoded_321": digest_record(components["encoded_321"]),
        "cipher_321": digest_record(derived["cipher_321"]),
        "answer_321": digest_record(derived["answer_321"]),
        "validation_num": digest_record(components["validation_num"]),
        "answer_322": digest_record(derived["answer_322"]),
    }
    for name, (length, digest) in EXPECTED.items():
        if live[name] != {"length": length, "sha256": digest}:
            raise AssertionError(f"authenticated source drifted: {name} -> {live[name]}")
    if components["validation_num"] != VALIDATION_NUM.encode("ascii"):
        raise AssertionError("live validation number differs from data.py")

    candidates, _ = phase270.build_candidates(
        derived["answer_321"],
        derived["answer_322"],
        derived["phase32_plaintext"],
        components["offsets"]["p32_start"],
    )
    materials = phase270.password_materials(candidates)
    base_values = {row["value"] for row in candidates}
    material_values = {row["material"] for row in materials}
    if len(base_values) != 25 or len(material_values) != 50:
        raise AssertionError("Phase 270 inventory drifted from 25 bases / 50 materials")
    for raw_name, raw_value in (
        ("raw_encoded_321", components["encoded_321"]),
        ("cp1141_beaufort_ciphertext", derived["cipher_321"].encode("ascii")),
    ):
        if raw_value in base_values or raw_value in material_values:
            raise AssertionError(f"{raw_name} unexpectedly entered Phase 270 inventory")

    findings = read_findings()
    missing_phases = tuple(
        phase for phase in REQUIRED_PHASES
        if f"## Phase {phase} --" not in findings
    )
    if missing_phases:
        return {
            "phase": 436,
            "decision": "protocol_invalid",
            "reason": "frozen required findings are absent",
            "missing_phase_findings": missing_phases,
            "authenticated_sources": live,
            "phase270_inventory": {"base_count": len(base_values), "material_count": len(material_values)},
            "password_materials_generated": 0,
            "oracle_calls": 0,
            "gpu_touched": False,
        }

    rows = []
    for referent in REFERENTS:
        failed = tuple(name for name in GATE_NAMES if not referent["gates"][name])
        rows.append({**referent, "failed_gates": failed, "eligible": not failed})
    eligible = tuple(row["id"] for row in rows if row["eligible"])
    uncovered_ineligible = tuple(
        row["id"] for row in rows
        if row["gates"]["genuinely_uncovered"] and not row["eligible"]
    )
    return {
        "phase": 436,
        "authenticated_sources": live,
        "phase270_inventory": {"base_count": len(base_values), "material_count": len(material_values)},
        "gate_names": GATE_NAMES,
        "referent_count": len(rows),
        "referents": tuple(rows),
        "eligible_referents": eligible,
        "uncovered_but_ineligible": uncovered_ineligible,
        "decision": "no_source_referent_passes_all_gates",
        "next_trigger": "new evidence must fix source representation plus operator/unit/boundary",
        "password_materials_generated": 0,
        "oracle_calls": 0,
        "gpu_touched": False,
    }


def self_test():
    report = audit()
    assert report["decision"] == "protocol_invalid"
    assert report["missing_phase_findings"] == (418,)
    assert report["phase270_inventory"] == {"base_count": 25, "material_count": 50}
    assert report["password_materials_generated"] == report["oracle_calls"] == 0
    assert report["gpu_touched"] is False
    print("[*] Phase 436 self-test OK: protocol_invalid, missing Phase 418 findings entry, 0 oracle calls")


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
