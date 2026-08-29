#!/usr/bin/env python3
"""Phase 448 -- oracle-free brute-force eligibility audit."""

import argparse
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
OPEN_GAPS = REPO_ROOT / "doc/GSMG_OPEN_GAP_REGISTRY.md"
PHASE446_RESULT = REPO_ROOT / "tools/gsmg/phase446_result.json"
PHASE441_RESULT = REPO_ROOT / "tools/gsmg/phase441_result.json"
FEASIBILITY_AUDIT = REPO_ROOT / "doc/GSMG_CREATOR_FEASIBILITY_ENVELOPE_AUDIT.md"
ARCHITECT_MATRIX = REPO_ROOT / "doc/GSMG_PHASE434_ARCHITECT_INSTRUCTION_COVERAGE_MATRIX.md"

GATES = (
    "clue_selected_operands",
    "fixed_operation_domain",
    "fixed_serialization",
    "fixed_consumer",
    "fixed_validator",
    "unresolved_not_exhausted",
    "count_calculable_without_new_bounds",
)

EXPECTED_GAPS = (
    "G-MSL-001",
    "G-ARCH-001",
    "G-ESC-001",
    "G-YIN-001",
    "G-PRIME-001",
    "G-MATPROD-001",
    "G-KIT-001",
    "G-GGN-001",
    "G-X2SH-001",
)


def gates(*passed):
    passed = set(passed)
    unknown = passed - set(GATES)
    if unknown:
        raise AssertionError(f"unknown gates: {sorted(unknown)}")
    return {gate: gate in passed for gate in GATES}


ROWS = (
    {
        "id": "G-MSL-001",
        "construction": "31-character DBBI selection -> matrixsumlist",
        "finite_skeleton": False,
        "gates": gates("clue_selected_operands", "unresolved_not_exhausted"),
        "missing": "matrix dimensions, traversal, value map, aggregation, serialization, consumer, and validator",
        "license": "primary source fixing all seven recorded G3 fields and a downstream target",
    },
    {
        "id": "G-ARCH-001",
        "construction": "Architect words -> BYE -> CIAO BELLA O",
        "finite_skeleton": False,
        "gates": gates("unresolved_not_exhausted"),
        "missing": "creator-selected word boundary, beginnings/endings rule, B/H mirror, role, and consumer",
        "license": "creator message or media explicitly selecting the operation and role",
    },
    {
        "id": "G-ESC-001",
        "construction": "FAED escape-pair choice ({g,i} versus {h,e})",
        "finite_skeleton": True,
        "gates": gates("unresolved_not_exhausted"),
        "missing": "a clue-selected pair, valid segmentation/decoder, serialization, consumer, and validator",
        "license": "external primary source selecting one pair or explaining why reconciliation is unnecessary",
    },
    {
        "id": "G-YIN-001",
        "construction": "DBBI/FAED -> yinyang relationship",
        "finite_skeleton": False,
        "gates": gates("clue_selected_operands", "unresolved_not_exhausted"),
        "missing": "whether the streams combine at all, operation, parameter domain, output role, and consumer",
        "license": "creator evidence defining the relationship or a structurally forced unique reading",
    },
    {
        "id": "G-PRIME-001",
        "construction": "prime-list sums -> 401/400/73",
        "finite_skeleton": True,
        "gates": gates("clue_selected_operands", "unresolved_not_exhausted"),
        "missing": "selection of Roman/title-C projection, FEFE/73 role, serialization, and consumer",
        "license": "clue consuming all three sums or independently selecting the complete construction",
    },
    {
        "id": "G-MATPROD-001",
        "construction": "matrix product -> (255,103) / FF67",
        "finite_skeleton": True,
        "gates": gates("clue_selected_operands", "unresolved_not_exhausted"),
        "missing": "clue-selected multiplication, byte serialization, consumer, and validator",
        "license": "clue selecting multiplication and naming a byte consumer",
    },
    {
        "id": "G-KIT-001",
        "construction": "second matrix-list difference -> reversed KIT",
        "finite_skeleton": True,
        "gates": gates("clue_selected_operands", "unresolved_not_exhausted"),
        "missing": "selection of subtraction, A1Z26, reversal, consumer, and validator",
        "license": "clue explicitly requesting difference/reversal or naming the rabbit reading",
    },
    {
        "id": "G-GGN-001",
        "construction": "FEFE tuple {1,4,21} -> ggn -> secp256k1",
        "finite_skeleton": False,
        "gates": gates("clue_selected_operands", "unresolved_not_exhausted"),
        "missing": "index convention, case promotion, scalar k domain, negation, curve role, and consumer",
        "license": "independent clue supplying k and selecting group order/negation",
    },
    {
        "id": "G-X2SH-001",
        "construction": "X2SH4Y0QB15 -> four-point Decentraland route",
        "finite_skeleton": True,
        "gates": gates("clue_selected_operands", "unresolved_not_exhausted"),
        "missing": "creator selection of the slicing/route and resolution of the chronology conflict",
        "license": "creator statement selecting the route or chronology evidence making it possible",
    },
    {
        "id": "P32-UNSELECTED",
        "construction": "P32 sibling/Architect reversal, interleave, source, and transport variants",
        "finite_skeleton": False,
        "gates": gates("fixed_validator", "unresolved_not_exhausted"),
        "missing": "unique source/carrier, exact operation domain, serialization, and demonstrated P32 binding",
        "license": "primary evidence fixing source, operation/direction/order, serialization, consumer, and transform",
    },
    {
        "id": "P32-CONDITIONAL",
        "construction": "custom KDF/mode, raw-response, and larger classifier widenings",
        "finite_skeleton": False,
        "gates": gates("fixed_validator", "unresolved_not_exhausted"),
        "missing": "clue-selected family and a preregistered complete parameter/corpus domain",
        "license": "authenticated KDF/container/source clue or separately authorized finite scope with distinct information gain",
    },
    {
        "id": "P32-F09-BACKFILL",
        "construction": "Tier-1 nopad whitespace-variant coverage delta",
        "finite_skeleton": True,
        "gates": gates(
            "fixed_operation_domain",
            "fixed_serialization",
            "fixed_consumer",
            "fixed_validator",
            "unresolved_not_exhausted",
            "count_calculable_without_new_bounds",
        ),
        "missing": "clue selection: this is a curated-corpus coverage backfill, not a clue-defined construction",
        "license": "already runnable as bookkeeping, but cannot be cited as the Architect-requested brute-force construction",
    },
    {
        "id": "P32-NEW-SOURCES",
        "construction": "future corpus, fragment, date, repository, archive, or external candidate",
        "finite_skeleton": False,
        "gates": gates("unresolved_not_exhausted"),
        "missing": "the new authenticated bytes and every construction field that depends on them",
        "license": "actual new primary evidence, not periodic re-search or a hypothetical source class",
    },
    {
        "id": "PANEL-RESAMPLING",
        "construction": "more blinded-panel/model samples",
        "finite_skeleton": False,
        "gates": gates(
            "clue_selected_operands",
            "fixed_consumer",
            "fixed_validator",
            "unresolved_not_exhausted",
        ),
        "missing": "deterministic generator domain, exhaustive stopping point, and evidence that resampling is a puzzle operation",
        "license": "primary-evidence packet delta or independently justified instrument with distinct expected information gain",
    },
    {
        "id": "ARCHITECT-METHOD",
        "construction": "BRUTE FORCING MIGHT BE REQUIRED",
        "finite_skeleton": False,
        "gates": gates("unresolved_not_exhausted"),
        "missing": "the operand, operation, parameter domain, serialization, consumer, validator, and candidate count",
        "license": "another clue-supported construction passing the six non-method gates first",
    },
)


def registry_gap_ids():
    text = OPEN_GAPS.read_text(encoding="utf-8")
    return tuple(
        line.split("|", 2)[1].strip()
        for line in text.splitlines()
        if line.startswith("| G-")
    )


def audit():
    if registry_gap_ids() != EXPECTED_GAPS:
        raise AssertionError("open-gap registry drifted; reclassify Phase 448")

    phase446 = json.loads(PHASE446_RESULT.read_text(encoding="utf-8"))
    if phase446["directly_runnable_finite_residuals"] != ["P32-F09"]:
        raise AssertionError("Phase 446 finite residual changed")
    phase441 = json.loads(PHASE441_RESULT.read_text(encoding="utf-8"))
    if phase441["decision"] != "exact_16factorial_negative_quadgram_selection_pathology_confirmed":
        raise AssertionError("Phase 441 control disposition drifted")

    feasibility = FEASIBILITY_AUDIT.read_text(encoding="utf-8")
    if "there is no\ncreator endorsement of moderate endgame brute force" not in feasibility:
        raise AssertionError("creator feasibility control drifted")
    architect = ARCHITECT_MATRIX.read_text(encoding="utf-8")
    if "no finite local search space specified" not in architect:
        raise AssertionError("Architect method control drifted")

    rows = []
    for row in ROWS:
        if tuple(row["gates"]) != GATES:
            raise AssertionError(f"gate order drifted for {row['id']}")
        passed = sum(row["gates"].values())
        rows.append(
            {
                **row,
                "passed_gate_count": passed,
                "failed_gates": [gate for gate, value in row["gates"].items() if not value],
                "bruteforce_eligible": passed == len(GATES),
            }
        )

    eligible = [row["id"] for row in rows if row["bruteforce_eligible"]]
    finite_skeletons = [row["id"] for row in rows if row["finite_skeleton"]]
    return {
        "gate_names": list(GATES),
        "open_gap_ids": list(EXPECTED_GAPS),
        "row_count": len(rows),
        "rows": rows,
        "computationally_finite_skeletons": finite_skeletons,
        "eligible_constructions": eligible,
        "eligible_construction_count": len(eligible),
        "bookkeeping_exception": {
            "id": "P32-F09-BACKFILL",
            "estimated_keystrings": 700000,
            "finite": True,
            "clue_supported_construction": False,
        },
        "closed_finite_control": {
            "phase": 441,
            "domain": "16!",
            "candidate_count": 20922789888000,
            "completed": True,
            "negative": True,
            "remaining": False,
        },
        "method_evidence": {
            "architect_phrase_creator_added": True,
            "finite_space_supplied_by_phrase": False,
            "creator_endorses_moderate_endgame_bruteforce": False,
            "puzzle_specific_creator_bruteforce_context": "anti-bruteforce web state; find the right hint",
        },
        "decision": "no_clue_supported_finite_search_space",
        "password_materials_generated": 0,
        "oracle_calls": 0,
        "gpu_touched": False,
        "docker_touched": False,
        "network_touched": False,
        "external_agents_used": False,
    }


def self_test():
    report = audit()
    assert report["row_count"] == len(ROWS) == 15
    assert report["eligible_constructions"] == []
    assert report["eligible_construction_count"] == 0
    assert report["bookkeeping_exception"]["finite"] is True
    assert report["bookkeeping_exception"]["clue_supported_construction"] is False
    assert report["closed_finite_control"]["candidate_count"] == 20922789888000
    assert report["decision"] == "no_clue_supported_finite_search_space"
    assert report["password_materials_generated"] == report["oracle_calls"] == 0
    assert not any(
        report[key]
        for key in ("gpu_touched", "docker_touched", "network_touched", "external_agents_used")
    )
    print("[*] self-test OK: 15 rows, 0 brute-force-eligible constructions, no oracle")


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
