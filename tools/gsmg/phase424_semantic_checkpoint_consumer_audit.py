#!/usr/bin/env python3
"""Phase 424: test whether Phase 423 convergence selects a forward consumer.

This is a provenance/dataflow audit only. It partitions the exact promoted
Phase 423 candidates into five pre-registered semantic families, carries
forward existing assertion-backed artifact and role audits, and applies five
promotion gates. It never invokes a password or cipher oracle.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import bye_ciao_provenance_audit as bye_ciao  # noqa: E402
import phase423_execution_replay as phase423_replay  # noqa: E402
import post_yinyang_dataflow_audit as post_yinyang  # noqa: E402
import salphaseion_salvation_role_audit as salvation_roles  # noqa: E402
import yinyang_artifact_inventory_audit as artifact_inventory  # noqa: E402
from telegram_export_manifest import DEFAULT_EXPORT_DIR  # noqa: E402


PHASE423_RESULT_PATH = SCRIPT_DIR / "phase423_result.json"
RESULT_PATH = SCRIPT_DIR / "phase424_result.json"
PHASE423_RESULT_SHA256 = (
    "b1da26548f2acd24d4234ac19283d9114d9f6f7e89b81c332be97b18e30404da"
)
YINYANG_INVENTORY_SOURCE_SHA256 = (
    "698f876f0d5ebfb73e9fcb2d6c78a85da5a83fcc5736d0baddda940fbe7d5ca9"
)

FAMILY_MEMBERS = {
    "farewell": ("BYE", "CIAOBELLAO"),
    "title_salvation": ("SALVATION", "SALVATIONpromised"),
    "architect_rails": ("BUTHYE", "BOTHULTIMATELYTHE"),
    "creator_macro_literals": (
        "promised",
        "verylaststepisatruegiveaway",
        "itsinfrontofyoureyesbutyourenotseeingit",
        "yinyang",
    ),
    "solved_tail_extraction": ("HALFANDBETTERHALF", "LIVE"),
}

EXPECTED_PHASE423 = {
    "outcome": "comparison_new_convergence_negative",
    "eligible_count": 5,
    "distinct_candidate_count": 18,
    "promoted_count": 12,
    "duplicate_promoted_count": 5,
    "comparison_new_promoted_count": 7,
    "evaluated_new_count": 7,
    "terminal_hits": 0,
    "structural_hits": 0,
}


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def phase423_state():
    if sha256_file(PHASE423_RESULT_PATH) != PHASE423_RESULT_SHA256:
        raise AssertionError("Phase 423 result artifact drifted")
    result = json.loads(PHASE423_RESULT_PATH.read_text(encoding="utf-8"))
    for key, value in EXPECTED_PHASE423.items():
        if result.get(key) != value:
            raise AssertionError(f"Phase 423 {key} drifted")
    if any(row["outcome"] != "negative" for row in result["evaluations"]):
        raise AssertionError("Phase 423 evaluation outcome drifted")

    displays = {
        hashlib.sha256(display.encode("utf-8")).hexdigest(): display
        for rows in phase423_replay.candidate_rows().values()
        for display in rows
    }
    promoted = {}
    for row in result["promoted"]:
        digest = row["candidate_sha256"]
        if digest not in displays:
            raise AssertionError(f"unresolved Phase 423 promotion {digest}")
        display = displays[digest]
        if display in promoted:
            raise AssertionError(f"duplicate Phase 423 promotion {display!r}")
        promoted[display] = {
            "votes": row["votes"],
            "best_rank": row["best_rank"],
            "comparator_disposition": row["comparator_disposition"],
            "candidate_sha256": digest,
        }

    declared = {item for members in FAMILY_MEMBERS.values() for item in members}
    if set(promoted) != declared or sum(map(len, FAMILY_MEMBERS.values())) != len(declared):
        raise AssertionError("Phase 424 semantic-family partition drifted")
    return result, promoted


def frozen_inventory_state():
    """Recover committed inventory gates without its retired _work input."""
    source = SCRIPT_DIR / "yinyang_artifact_inventory_audit.py"
    if sha256_file(source) != YINYANG_INVENTORY_SOURCE_SHA256:
        raise AssertionError("yin-yang artifact inventory source drifted")
    if tuple(artifact_inventory.QUALIFICATION) != artifact_inventory.EXPECTED_ARTIFACT_ORDER:
        raise AssertionError("yin-yang artifact order drifted")
    artifacts = []
    for artifact_id, frozen in artifact_inventory.QUALIFICATION.items():
        qualification = dict(frozen)
        qualification["all_core"] = all(
            qualification[field]
            for field in ("primary", "visible", "dual", "correct_boundary")
        )
        qualification["qualifies_for_local_mechanics"] = (
            qualification["all_core"] and qualification["independent_discriminator"]
        )
        artifacts.append({"artifact_id": artifact_id, "qualification": qualification})
    qualifying = [
        row["artifact_id"] for row in artifacts
        if row["qualification"]["qualifies_for_local_mechanics"]
    ]
    return {"artifacts": artifacts, "qualifying_artifacts": qualifying}


def family_records(promoted, farewell, inventory, salvation):
    artifacts = {row["artifact_id"]: row for row in inventory["artifacts"]}
    if artifacts["but_hye_rails"]["qualification"]["independent_discriminator"]:
        raise AssertionError("BUT/HYE unexpectedly became an independent discriminator")
    if farewell["gates"]["deterministic_bye_to_ciao_operation"]:
        raise AssertionError("BYE->CIAO operation unexpectedly became deterministic")
    if farewell["gates"]["fixed_downstream_consumer"]:
        raise AssertionError("BYE/CIAO unexpectedly acquired a downstream consumer")
    if salvation["roles"]["checksum"]["status"] != "open_untestable":
        raise AssertionError("SALVATION checksum role drifted")

    gates = {
        "farewell": {
            "source_grounded": True,
            "correct_boundary": True,
            "independent_discriminator": farewell["independent_prior"][
                "all_predate_phase232"
            ],
            "unique_referent": False,
            "executable_consumer": False,
            "classification": "recognition_echo_no_forward_edge",
            "basis": (
                "HYE->BYE is a controlled boundary result and historical community "
                "discussion independently links BYE with the authenticated CIAO BELLA O "
                "tail, but no creator source selects that translation, no deterministic "
                "BYE->CIAO operation exists, and no downstream consumer is fixed."
            ),
        },
        "title_salvation": {
            "source_grounded": True,
            "correct_boundary": False,
            "independent_discriminator": False,
            "unique_referent": True,
            "executable_consumer": False,
            "classification": "container_theme_echo",
            "basis": (
                "SalPhaseIon is the authenticated page title and SALVATION is a bounded "
                "researcher-established rebus, but the title is the containing artifact, "
                "not an output reached from lastwords; its only open role is an "
                "untestable post-decryption checksum."
            ),
        },
        "architect_rails": {
            "source_grounded": True,
            "correct_boundary": True,
            "independent_discriminator": False,
            "unique_referent": True,
            "executable_consumer": False,
            "classification": "same_boundary_restatement",
            "basis": (
                "BUTHYE and BOTHULTIMATELYTHE restate the mechanically reconstructed "
                "boundary. The artifact inventory finds no independent yin-yang "
                "discriminator and no surviving deterministic downstream operation."
            ),
        },
        "creator_macro_literals": {
            "source_grounded": True,
            "correct_boundary": True,
            "independent_discriminator": False,
            "unique_referent": False,
            "executable_consumer": False,
            "classification": "prompt_literal_no_referent",
            "basis": (
                "These are exact creator-authored macro literals, but the prompt exposed "
                "them verbatim and the referents of yinyang and in-front-of-your-eyes "
                "remain unresolved; convergence adds no independent selector."
            ),
        },
        "solved_tail_extraction": {
            "source_grounded": True,
            "correct_boundary": False,
            "independent_discriminator": False,
            "unique_referent": True,
            "executable_consumer": False,
            "classification": "backward_solved_output_echo",
            "basis": (
                "HALFANDBETTERHALF and LIVE are exact substrings of the already-solved "
                "Phase 3.2.2 answer. No creator instruction reselects them after the "
                "Architect boundary or specifies a new consumer."
            ),
        },
    }

    records = []
    for family, members in FAMILY_MEMBERS.items():
        record = {
            "family": family,
            "members": [
                {"display": member, **promoted[member]} for member in members
            ],
            "total_votes": sum(promoted[member]["votes"] for member in members),
            "gates": gates[family],
        }
        record["all_gates"] = all(
            gates[family][name]
            for name in (
                "source_grounded",
                "correct_boundary",
                "independent_discriminator",
                "unique_referent",
                "executable_consumer",
            )
        )
        records.append(record)
    return records


def consumer_records(dataflow, inventory, salvation):
    artifacts = {row["artifact_id"]: row for row in inventory["artifacts"]}
    routes = dataflow["routes"]
    return [
        {
            "consumer": "recognition_output_is_thispassword",
            "status": routes["recognition_output_is_password"]["status"],
            "selected_by_phase423": False,
        },
        {
            "consumer": "faed_plaintext_is_thispassword",
            "status": routes["faed_plaintext_is_password"]["status"],
            "selected_by_phase423": False,
        },
        {
            "consumer": "dbbi_faed_joint_result_is_thispassword",
            "status": routes["dbbi_faed_joint_result_is_password"]["status"],
            "selected_by_phase423": False,
        },
        {
            "consumer": "paired_page_objects_are_yinyang",
            "status": "not_qualified",
            "selected_by_phase423": False,
            "qualification": artifacts["paired_page_objects"]["qualification"],
        },
        {
            "consumer": "cosmic_duality_book_is_reached_artifact",
            "status": "wrong_boundary_no_operation",
            "selected_by_phase423": False,
            "qualification": artifacts["cosmic_duality_book"]["qualification"],
        },
        {
            "consumer": "salphaseion_title_is_reached_artifact",
            "status": "container_not_forward_edge",
            "selected_by_phase423": False,
            "salvation_checksum_role": salvation["roles"]["checksum"]["status"],
        },
    ]


def audit(export_dir=DEFAULT_EXPORT_DIR):
    phase423, promoted = phase423_state()
    farewell = bye_ciao.audit(export_dir)
    inventory = frozen_inventory_state()
    dataflow = post_yinyang.audit(Path(export_dir) / "result.json")
    salvation = salvation_roles.audit()

    if inventory["qualifying_artifacts"]:
        raise AssertionError("an inherited yin-yang artifact unexpectedly qualified")
    if dataflow["most_local_live_role"] != "faed_plaintext_is_password":
        raise AssertionError("post-yinyang live-role ranking drifted")

    families = family_records(promoted, farewell, inventory, salvation)
    consumers = consumer_records(dataflow, inventory, salvation)
    promoted_families = [row["family"] for row in families if row["all_gates"]]
    selected_consumers = [
        row["consumer"] for row in consumers if row["selected_by_phase423"]
    ]
    if promoted_families or selected_consumers:
        outcome = "consumer_promoted" if len(promoted_families) == 1 and len(selected_consumers) == 1 else "ambiguous_forward_roles"
    else:
        outcome = "recognition_only_no_forward_edge"

    return {
        "phase": 424,
        "outcome": outcome,
        "oracle_calls": 0,
        "phase423_input": {
            "result_sha256": PHASE423_RESULT_SHA256,
            **{key: phase423[key] for key in EXPECTED_PHASE423},
        },
        "semantic_family_count": len(families),
        "families": families,
        "promoted_families": promoted_families,
        "consumer_count": len(consumers),
        "consumers": consumers,
        "selected_consumers": selected_consumers,
        "strongest_recognition_family": "farewell",
        "most_local_live_role": dataflow["most_local_live_role"],
        "missing_edge": "a source-grounded FAED decoder or DBBI/FAED relationship",
        "verdict": (
            "Phase 423 convergence strengthens the BYE/CIAO farewell family as the "
            "best recognition echo because it also has independent historical community "
            "support. It does not select a unique referent or executable forward edge. "
            "The other families are prompt literals, same-boundary restatements, page "
            "themes, or backward echoes. No known consumer is selected; the live frontier "
            "remains FAED plaintext as thispassword with its decoder unknown."
        ),
    }


def self_test(export_dir=DEFAULT_EXPORT_DIR):
    report = audit(export_dir)
    assert report["outcome"] == "recognition_only_no_forward_edge"
    assert report["oracle_calls"] == 0
    assert report["semantic_family_count"] == 5
    assert report["consumer_count"] == 6
    assert report["promoted_families"] == []
    assert report["selected_consumers"] == []
    farewell = next(row for row in report["families"] if row["family"] == "farewell")
    assert farewell["gates"]["independent_discriminator"] is True
    assert farewell["gates"]["unique_referent"] is False
    assert farewell["gates"]["executable_consumer"] is False
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write-artifact", action="store_true")
    args = parser.parse_args()
    report = self_test(args.export_dir) if args.self_test else audit(args.export_dir)
    if args.write_artifact:
        RESULT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
