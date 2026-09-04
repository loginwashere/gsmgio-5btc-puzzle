#!/usr/bin/env python3
"""Phase 467 closed-system instruction/operand constraint closure."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent.parent
MANIFEST_PATH = SCRIPT_DIR / "phase467_constraint_closure_manifest.json"
RESULT_PATH = SCRIPT_DIR / "phase467_result.json"
EXPECTED_MANIFEST_SHA256 = "ca62ee312849bc172602be0e35e11cebd5b2556068e049b4ce79bf921a959f5c"


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest() -> dict:
    if sha256_path(MANIFEST_PATH) != EXPECTED_MANIFEST_SHA256:
        raise AssertionError("Phase 467 manifest drifted")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest["phase"] != 467 or not all(manifest["prohibitions"].values()):
        raise AssertionError("invalid Phase 467 manifest")
    protocol = manifest["protocol"]
    if sha256_path(ROOT / protocol["path"]) != protocol["sha256"]:
        raise AssertionError("Phase 467 protocol drifted")
    for row in manifest["inputs"]:
        if sha256_path(ROOT / row["path"]) != row["sha256"]:
            raise AssertionError(f"pinned input drifted: {row['path']}")
    return manifest


def load_inputs(manifest: dict) -> dict[int, dict]:
    data = {}
    for row in manifest["inputs"]:
        obj = json.loads((ROOT / row["path"]).read_text(encoding="utf-8"))
        data[obj.get("phase", 451)] = obj
    # Phase 451's synthesis predates phase metadata; its pinned filename owns 451.
    if 451 not in data:
        row = next(r for r in manifest["inputs"] if "phase451" in r["path"])
        data[451] = json.loads((ROOT / row["path"]).read_text(encoding="utf-8"))
    return data


def assert_frozen_facts(data: dict[int, dict]) -> dict:
    p434, p439, p449 = data[434], data[439], data[449]
    p451, p455, p464 = data[451], data[455], data[464]
    p465, p466 = data[465], data[466]
    assert [r["id"] for r in p434["clauses"]] == [
        "function_you", "source_codes", "temporary_dissemination",
        "prime_basics", "required_select", "numeric_triple",
        "private_key_note", "brute_force",
    ]
    assert not any(row["eligible"] for row in p439["candidates"])
    assert p449["selected_candidates"] == []
    assert p449["decision_gates"]["GI"]["valid_on_faed"]
    assert p449["decision_gates"]["HE"]["valid_on_faed"]
    assert not p449["decision_gates"]["GI"]["independent_selector"]
    assert not p449["decision_gates"]["HE"]["independent_selector"]
    assert p451["all_citations_verified"]
    assert "unchanged: parked" in p451["gyin_001_disposition"]["status"]
    assert p455["verdict"] == "all_roles_survive"
    assert set(p455["surviving_roles"]) == {
        "password_for_faed", "faed_answer_is_password", "password_for_salph_blob"
    }
    assert all(value == 0 for value in p455["contradiction_counts"].values())
    assert not any(p464["manual_verdict"]["promotion_gates"].values())
    assert p465["verdict"] == "no_offset_zero_structural_gate"
    assert p465["faed_offset_zero_rank1_count"] == 0
    assert p466["verdict"] == "exact_crib_negative"
    assert p466["offset_zero_match_count"] == 0
    assert p466["nonzero_control_match_count"] == 0
    return {
        "architect_clause_count": len(p434["clauses"]),
        "eligible_source_referents": 0,
        "faed_pairs_admissible_but_selected": 0,
        "thispassword_roles_surviving": len(p455["surviving_roles"]),
        "theflower_promotion_gates_passed": 0,
        "phase1_consumer_families_promoted": 0,
    }


def cell(state: str, value: str, basis: str) -> dict:
    return {"state": state, "value": value, "basis": basis}


def edge_contracts(assignment: dict) -> dict:
    escape = assignment["faed_escape"]
    role = assignment["thispassword_role"]
    relation = assignment["architect_relation"]
    return {
        "dbbi_matrixsumlist": {
            "status": "live",
            "source": cell("bound", "DBBI", "literal page adjacency"),
            "operand_boundary": cell("bound", "complete DBBI stream", "authenticated textarea segment"),
            "operation": cell("unbound", "matrixsumlist schema", "dimensions/value map/aggregation absent"),
            "direction_representation": cell("unbound", "traversal and serialization", "G-MSL-001"),
            "output_type": cell("conditional", "numeric list", "instruction semantics only"),
            "consumer": cell("unbound", "none selected", "no downstream target"),
        },
        "faed_decode": {
            "status": "live",
            "source": cell("bound", "FAED", "authenticated textarea segment"),
            "operand_boundary": cell("conditional", escape, "both pairs tokenize; neither selected"),
            "operation": cell("unbound", "decoder", "no authenticated decoder"),
            "direction_representation": cell("unbound", "alphabet/order", "no selected representation"),
            "output_type": cell("conditional", "plaintext", "checkerboard model only"),
            "consumer": cell("unbound", "none selected", "role attachment unresolved"),
        },
        "architect_relation": {
            "status": "live",
            "source": cell("bound", "Architect word list", "authenticated solved list"),
            "operand_boundary": cell("bound", "last words before Architect choice", "literal instruction"),
            "operation": cell("conditional" if relation != "unbound" else "unbound", relation, "G-ARCH-001"),
            "direction_representation": cell("conditional" if relation != "unbound" else "unbound", "edge mirror", "unselected relation"),
            "output_type": cell("bound", "recognition token", "BUT/HYE checkpoint class"),
            "consumer": cell("unbound", "none selected", "yinyang transition has no operator/consumer"),
        },
        "thispassword_attachment": {
            "status": "live",
            "source": cell("bound", "thispassword token", "literal decoded token"),
            "operand_boundary": cell("unbound", role, "all three roles survive"),
            "operation": cell("unbound", "label or key use", "attachment marker absent"),
            "direction_representation": cell("conditional", role, "role hypothesis only"),
            "output_type": cell("bound", "password", "literal semantic type"),
            "consumer": cell("unbound", "FAED/result/SALPH", "consumer tie unresolved"),
        },
        "sha_instruction": {
            "status": "live",
            "source": cell("bound", "sha256 instruction", "literal decoded instruction"),
            "operand_boundary": cell("unbound", "our first hint / your last command", "referents unresolved"),
            "operation": cell("bound", "SHA-256", "literal operator"),
            "direction_representation": cell("unbound", "exact bytes/case", "serialization unstated"),
            "output_type": cell("bound", "SHA-256 digest", "operator type"),
            "consumer": cell("unbound", "none selected", "adjacency does not bind consumption"),
        },
        "salph_enter_reconstruction": {
            "status": "solved_control",
            "source": cell("bound", "two 64-character Base64 halves", "literal page offsets"),
            "operand_boundary": cell("bound", "prefix + suffix", "ENTER is embedded between halves"),
            "operation": cell("bound", "concatenate", "fixed local grammar"),
            "direction_representation": cell("bound", "page order / Base64", "literal order"),
            "output_type": cell("bound", "OpenSSL Salted__ envelope", "decoded header"),
            "consumer": cell("bound", "SALPH encrypted object", "reconstructed object identity"),
        },
        "theflower_router": {
            "status": "live",
            "source": cell("bound", "24 colored apertures", "authenticated first piece"),
            "operand_boundary": cell("bound", "24 apertures + inverse-prime pair", "bounded Phase 461 family"),
            "operation": cell("conditional", "rotation/frame/parity/affix chain", "post-hoc recognition chain"),
            "direction_representation": cell("conditional", "90-degree rotated decimal matrices", "not independently selected"),
            "output_type": cell("bound", "recognition checksum", "Phase-1 prefix"),
            "consumer": cell("unbound", "none authenticated", "Phases 464-466"),
        },
    }


def valid_assignment(row: dict) -> bool:
    # Conditional mirror produces HE, never GI; leaving the relation unbound
    # does not select either escape pair.
    return not (
        row["architect_relation"] == "conditional_edge_mirror"
        and row["faed_escape"] != "HE"
    )


def enumerate_assignments(manifest: dict) -> list[dict]:
    names = list(manifest["domains"])
    rows = []
    for values in itertools.product(*(manifest["domains"][name] for name in names)):
        assignment = dict(zip(names, values))
        if not valid_assignment(assignment):
            continue
        edges = edge_contracts(assignment)
        live = {name: edge for name, edge in edges.items() if edge["status"] == "live"}
        closure = sum(
            edge[field]["state"] == "bound"
            for edge in live.values()
            for field in manifest["contract_fields"]
        )
        executable = [
            name for name, edge in live.items()
            if all(edge[field]["state"] == "bound" for field in manifest["contract_fields"])
        ]
        rows.append({"assignment": assignment, "closure_count": closure, "executable_live_edges": executable, "edges": edges})
    return rows


def build_report(manifest: dict) -> dict:
    facts = assert_frozen_facts(load_inputs(manifest))
    rows = enumerate_assignments(manifest)
    max_closure = max(row["closure_count"] for row in rows)
    maximum = [row for row in rows if row["closure_count"] == max_closure]
    fields = manifest["contract_fields"]
    shared_missing = []
    for edge_name in edge_contracts(maximum[0]["assignment"]):
        if maximum[0]["edges"][edge_name]["status"] != "live":
            continue
        for field in fields:
            if all(row["edges"][edge_name][field]["state"] != "bound" for row in maximum):
                shared_missing.append(f"{edge_name}.{field}")
    variable_selectors = [
        name for name in manifest["domains"]
        if len({row["assignment"][name] for row in maximum}) > 1
    ]
    deficits = {}
    first = maximum[0]
    for edge_name, edge in first["edges"].items():
        if edge["status"] != "live":
            continue
        deficits[edge_name] = [field for field in fields if edge[field]["state"] != "bound"]
    min_deficit = min(map(len, deficits.values()))
    closest = {name: missing for name, missing in deficits.items() if len(missing) == min_deficit}
    full = [row for row in rows if row["executable_live_edges"]]
    verdict = "unique_executable_assignment" if len(full) == 1 else "no_executable_assignment_constraint_tie"
    return {
        "phase": 467,
        "date": manifest["date"],
        "manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "frozen_fact_checks": facts,
        "domain_product_count": __import__("math").prod(len(v) for v in manifest["domains"].values()),
        "hard_constraint_survivor_count": len(rows),
        "maximum_closure_count": max_closure,
        "live_contract_field_count": sum(
            edge["status"] == "live" for edge in first["edges"].values()
        ) * len(fields),
        "maximum_assignment_count": len(maximum),
        "full_assignment_count": len(full),
        "variable_selectors_required_for_unique_assignment": variable_selectors,
        "shared_missing_bindings": shared_missing,
        "closest_live_edges": closest,
        "maximum_assignments": [row["assignment"] for row in maximum],
        "solved_control_complete": all(
            first["edges"]["salph_enter_reconstruction"][field]["state"] == "bound"
            for field in fields
        ),
        "transform_licensed": len(full) == 1,
        "password_materials_generated": 0,
        "hashes_computed_on_candidates": 0,
        "decryptions_attempted": 0,
        "oracle_calls": 0,
        "weighted_scores_computed": 0,
        "verdict": verdict,
        "next_experiment": {
            "kind": "internal_binding_recovery",
            "targets": variable_selectors,
            "rule": "recover a selector from authenticated artifact structure before executing any transform",
        },
    }


def self_test(report: dict) -> None:
    assert report["solved_control_complete"]
    assert report["domain_product_count"] == 36
    assert report["hard_constraint_survivor_count"] == 27
    assert report["full_assignment_count"] == 0
    assert report["maximum_assignment_count"] == 27
    assert report["variable_selectors_required_for_unique_assignment"] == [
        "topology", "faed_escape", "thispassword_role", "architect_relation"
    ]
    assert report["closest_live_edges"]
    assert not report["transform_licensed"]
    assert report["oracle_calls"] == report["password_materials_generated"] == 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=RESULT_PATH)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    report = build_report(load_manifest())
    self_test(report)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.self_test:
        print("[*] Phase 467 self-test OK")
    print(json.dumps({key: report[key] for key in (
        "verdict", "hard_constraint_survivor_count", "maximum_assignment_count",
        "full_assignment_count", "variable_selectors_required_for_unique_assignment",
        "closest_live_edges", "transform_licensed"
    )}, indent=2))


if __name__ == "__main__":
    main()
