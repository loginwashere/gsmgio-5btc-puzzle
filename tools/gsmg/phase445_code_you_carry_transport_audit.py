#!/usr/bin/env python3
"""Phase 445 -- authenticated Phase-3.2 transport-role graph audit."""

import argparse
import base64
import hashlib
import json
from pathlib import Path

from data import (
    ALPHA_322,
    PHASE32_BLOB_B64,
    PHASE32_PASSWORD,
    P32_TRAILING_BLOB_B64,
)
from p32_sibling_password_audit import BEAUFORT_KEY, derive_sibling_outputs


REPO_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_NODES = {
    "phase32_password": (64, "e06146aee02e11ba83a2d0e2f4a6ada7e0bd9a501e7f5fde0208211be4ae740b"),
    "phase32_blob": (2448, "9d172dc017034564b40eb381fa61e31421f509a08430864c77ccf86cfc8fe784"),
    "phase32_plaintext": (2422, "b82afeb86f9e50848220f9b64b744b821400308aea273a1c949b9d2d0e408a34"),
    "raw_encoded_321": (1539, "bd7a29432546c67c4170e0c523ddbf43ae82d20ee187d1b4dbf7907a0faf4c7b"),
    "cp1141_ciphertext": (1539, "6d66e0e0e2dfdb812d5ecee2be6f54c1f3b8c84b0d74580686cf2053d76a200e"),
    "beaufort_key": (15, "b8de97f4752f353ae8f18bc20afff94c16fec87a230d14aead8572287c2f196c"),
    "answer_321": (1539, "56c43a300e28b86bb43b8dcbae74c43c76bde90b3e1190620fb656f2c94b2241"),
    "validation_num": (149, "71e3af174d533ad2c1c79fce64308f5fdf200f3cc50f059b2f1485a2c5f1765d"),
    "clue_322": (145, "fe2ee9e1d2218db842b5973f7761760d799ad6992cff4b6037fb0e940c7d358a"),
    "alpha_322": (28, "f48871f6826fcd56670d412ad9056c7b48caf112fefe50a767063b8d431d745f"),
    "answer_322": (91, "878b7afacc9e35412e76b8506cc8297fa5aeba5381e108dc421b71a0ab8993d8"),
    "p32_text": (130, "3c18b97e8481a3d1e4dc8823d66a625fb2aba83b786461b4e2c52751ad1191f3"),
    "p32_envelope": (96, "291dfd6f3e759ec2e272b35a00c24907da70c3e7a9291b4c13605c7b0b4f3de9"),
}

TRANSPORT_CLAUSE = (
    "ALLOWINGATEMPORARYDISSEMINATIONOFTHECODEYOUHOPEFULLYCARRY"
)


def payload_bytes(value):
    return value.encode("ascii") if isinstance(value, str) else bytes(value)


def make_node(
    node_id,
    value,
    role,
    *,
    established_output,
    available_before_p32,
    native_consumed,
    exact_serialization=True,
    target=False,
):
    payload = payload_bytes(value)
    gates = {
        "exact_reproducible": True,
        "established_transform_output": established_output,
        "available_before_p32": available_before_p32,
        "not_fully_consumed_by_native_solve": not native_consumed,
        "serializable_without_new_choice": exact_serialization,
        "not_the_target_itself": not target,
    }
    return {
        "id": node_id,
        "length": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "role": role,
        "native_consumed": native_consumed,
        "carrier_gates": gates,
        "carrier_eligible": all(gates.values()),
    }


def native_graph():
    derived = derive_sibling_outputs()
    components = derived["components"]
    values = {
        "phase32_password": PHASE32_PASSWORD,
        "phase32_blob": base64.b64decode(PHASE32_BLOB_B64, validate=True),
        "phase32_plaintext": derived["phase32_plaintext"],
        "raw_encoded_321": components["encoded_321"],
        "cp1141_ciphertext": derived["cipher_321"],
        "beaufort_key": BEAUFORT_KEY,
        "answer_321": derived["answer_321"],
        "validation_num": components["validation_num"],
        "clue_322": components["clue_322"],
        "alpha_322": ALPHA_322,
        "answer_322": derived["answer_322"],
        "p32_text": components["p32_text"],
        "p32_envelope": base64.b64decode(P32_TRAILING_BLOB_B64, validate=True),
    }
    specifications = {
        "phase32_password": ("inbound SHA-256-derived decryption password", True, True, True, False),
        "phase32_blob": ("authenticated encrypted Phase-3.2 container", False, True, True, False),
        "phase32_plaintext": ("authenticated decrypted parent container", True, True, True, False),
        "raw_encoded_321": ("creator-delivered 3.2.1 encoded child block", False, True, True, False),
        "cp1141_ciphertext": ("clue-selected EBCDIC intermediate", True, True, True, False),
        "beaufort_key": ("clue-derived Beaufort parameter", True, True, True, False),
        "answer_321": ("decoded Architect instruction output", True, True, False, False),
        "validation_num": ("creator-delivered 3.2.2 digit child stream", False, True, True, False),
        "clue_322": ("creator-delivered 3.2.2 decoder clue", False, True, True, False),
        "alpha_322": ("clue-derived keyed checkerboard alphabet", True, True, True, False),
        "answer_322": ("decoded two-private-key semantic output", True, True, False, False),
        "p32_text": ("textual Base64 form of unresolved trailing target", False, False, True, True),
        "p32_envelope": ("binary unresolved P32TRAILING target", True, False, False, True),
    }
    nodes = []
    for node_id, value in values.items():
        role, established_output, before, consumed, target = specifications[node_id]
        nodes.append(
            make_node(
                node_id,
                value,
                role,
                established_output=established_output,
                available_before_p32=before,
                native_consumed=consumed,
                target=target,
            )
        )

    edges = (
        {
            "from": ("phase32_password", "phase32_blob"),
            "to": "phase32_plaintext",
            "operation": "SHA256-EVP AES-256-CBC decryption",
            "status": "established",
        },
        {
            "from": ("phase32_plaintext",),
            "to": "raw_encoded_321",
            "operation": "authenticated delimiter extraction",
            "status": "container",
        },
        {
            "from": ("phase32_plaintext",),
            "to": "validation_num",
            "operation": "authenticated delimiter extraction",
            "status": "container",
        },
        {
            "from": ("phase32_plaintext",),
            "to": "clue_322",
            "operation": "authenticated delimiter extraction",
            "status": "container",
        },
        {
            "from": ("phase32_plaintext",),
            "to": "p32_text",
            "operation": "authenticated trailing extraction",
            "status": "container",
        },
        {
            "from": ("raw_encoded_321",),
            "to": "cp1141_ciphertext",
            "operation": "ISO-8859-1 to CP1141 transcode",
            "status": "established",
        },
        {
            "from": ("cp1141_ciphertext", "beaufort_key"),
            "to": "answer_321",
            "operation": "classical Beaufort decrypt",
            "status": "established",
        },
        {
            "from": ("clue_322",),
            "to": "alpha_322",
            "operation": "solve keyed-alphabet and escape-digit clue",
            "status": "established",
        },
        {
            "from": ("validation_num", "alpha_322"),
            "to": "answer_322",
            "operation": "keyed 9-ary checkerboard decode",
            "status": "established",
        },
        {
            "from": ("p32_text",),
            "to": "p32_envelope",
            "operation": "Base64 decode",
            "status": "established",
        },
        {
            "from": ("answer_321",),
            "to": "p32_envelope",
            "operation": "direct or SHA-256 password transport",
            "status": "tested-negative",
        },
        {
            "from": ("answer_322",),
            "to": "p32_envelope",
            "operation": "direct or SHA-256 password transport",
            "status": "tested-negative",
        },
        {
            "from": ("answer_321", "answer_322"),
            "to": "p32_envelope",
            "operation": "ordered sibling composition",
            "status": "tested-negative",
        },
    )
    return derived, nodes, edges


def saved_negative_coverage():
    records = []
    for phase in (442, 443, 444):
        path = REPO_ROOT / f"tools/gsmg/phase{phase}_result.json"
        report = json.loads(path.read_text(encoding="utf-8"))
        oracle = report["structural_oracle"]
        records.append(
            {
                "phase": phase,
                "artifact": str(path.relative_to(REPO_ROOT)),
                "trial_count": oracle["trial_count"],
                "hits": oracle["hits"],
                "machine_verified": True,
            }
        )
    records.insert(
        0,
        {
            "phase": 270,
            "artifact": "tools/gsmg/FINDINGS.md and p32_sibling_password_audit.py",
            "candidate_count": 25,
            "material_count": 50,
            "trial_count": 300,
            "hits": 0,
            "machine_verified": False,
            "note": "documented historical result; deliberately not re-executed",
        },
    )
    return records


def audit():
    derived, nodes, edges = native_graph()
    node_by_id = {node["id"]: node for node in nodes}
    for node_id, (length, digest) in EXPECTED_NODES.items():
        node = node_by_id[node_id]
        if (node["length"], node["sha256"]) != (length, digest):
            raise AssertionError(f"native node drifted: {node_id}")

    eligible = tuple(node["id"] for node in nodes if node["carrier_eligible"])
    established_consumer_bindings = tuple(
        edge
        for edge in edges
        if edge["to"] == "p32_envelope"
        and edge["status"] in ("established", "container")
        and any(source in eligible for source in edge["from"])
    )
    established_transforms_to_target = tuple(
        edge["operation"] for edge in established_consumer_bindings
    )

    answer_321 = derived["answer_321"]
    if TRANSPORT_CLAUSE not in answer_321:
        raise AssertionError("connected Architect transport clause drifted")

    unique_edge = (
        len(eligible) == 1
        and len(established_consumer_bindings) == 1
        and len(established_transforms_to_target) == 1
    )
    disposition = (
        "unique_native_transport_edge_selected"
        if unique_edge
        else "two_native_carriers_no_established_consumer_binding"
    )

    return {
        "phrase_control": {
            "connected_clause": TRANSPORT_CLAUSE,
            "temporary_dissemination_code_you_carry": "screenplay-inherited",
            "hopefully": "creator-added",
            "independent_object_selector": False,
        },
        "nodes": nodes,
        "edges": edges,
        "edge_class_counts": {
            status: sum(edge["status"] == status for edge in edges)
            for status in (
                "established",
                "container",
                "semantic",
                "tested-negative",
                "hypothetical",
            )
        },
        "eligible_carried_outputs": eligible,
        "eligible_carried_output_count": len(eligible),
        "eligible_roles": {
            node_id: node_by_id[node_id]["role"] for node_id in eligible
        },
        "unresolved_target": "p32_envelope",
        "established_consumer_bindings": established_consumer_bindings,
        "established_consumer_binding_count": len(established_consumer_bindings),
        "established_transforms_to_target": established_transforms_to_target,
        "unique_transport_edge_selected": unique_edge,
        "saved_negative_coverage": saved_negative_coverage(),
        "experimental_derivatives_are_native_outputs": False,
        "decision": disposition,
        "password_materials_generated": 0,
        "oracle_calls": 0,
        "gpu_touched": False,
        "docker_touched": False,
    }


def self_test():
    report = audit()
    assert len(report["nodes"]) == len(EXPECTED_NODES) == 13
    assert report["edge_class_counts"] == {
        "established": 6,
        "container": 4,
        "semantic": 0,
        "tested-negative": 3,
        "hypothetical": 0,
    }
    assert report["eligible_carried_outputs"] == ("answer_321", "answer_322")
    assert report["eligible_carried_output_count"] == 2
    assert report["established_consumer_binding_count"] == 0
    assert report["established_transforms_to_target"] == ()
    assert report["unique_transport_edge_selected"] is False
    assert all(record["hits"] == 0 for record in report["saved_negative_coverage"])
    assert report["decision"] == "two_native_carriers_no_established_consumer_binding"
    assert report["password_materials_generated"] == report["oracle_calls"] == 0
    assert report["gpu_touched"] is report["docker_touched"] is False
    print(
        "[*] self-test OK: 13 native nodes, 10 demonstrated edges, "
        "2 eligible carriers, 0 established target bindings, no oracle"
    )


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
