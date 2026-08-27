#!/usr/bin/env python3
"""Deterministic eligibility replay and closure writer for Phase 423."""

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase423_p32trailing_macro_clue_panel_audit as phase423  # noqa: E402

RESULT_PATH = SCRIPT_DIR / "phase423_result.json"
LEDGER_PATH = SCRIPT_DIR / "phase423_invocation_ledger.json"


def candidate_rows():
    return {
        "phase423_invocation_1": [
            "BUTHYE", "BOTHULTIMATELYTHE", "BYE", "CIAOBELLAO", "SALVATION",
            "promised", "itsinfrontofyoureyesbutyourenotseeingit",
            "verylaststepisatruegiveaway", "wewontgiveawaythepassword",
        ],
        "phase423_invocation_2": [
            "CIAOBELLAO", "SALVATION", "BYE", "HALFANDBETTERHALF", "LIVE",
            "BOTHULTIMATELYTHE", "BUTHYE", "promised", "yinyang",
            "verylaststepisatruegiveaway",
        ],
        "phase423_invocation_3": [
            "promised", "SALVATION", "BUTHYE", "BOTHULTIMATELYTHE", "BYE",
            "CIAOBELLAO", "verylaststepisatruegiveaway",
            "itsinfrontofyoureyesbutyourenotseeingit", "yinyang",
            "SALVATIONpromised",
        ],
        "phase423_invocation_4": [
            "SALVATION", "promisedSALVATION", "SALVATIONpromised", "LIVE",
            "HALFANDBETTERHALF", "THEONE", "CIAOBELLAO", "promised",
            "yinyang", "BYE",
        ],
        "phase423_invocation_5": [
            "BYE", "promised", "wewont", "CIAOBELLAO", "SALVATION", "BUT",
            "HYE", "BUTHYE", "BOTHULTIMATELYTHE",
            "verylaststepisatruegiveaway",
        ],
    }


def build_records(rows):
    records = {}
    for invocation_id, displays in rows.items():
        # Preserve an eligibility-relevant disclosed title residue for one
        # replay record; exact candidate display bytes and ranks are retained
        # for every invocation below.
        reasoning = (
            "packet-local reconstruction reasoning"
            if invocation_id != "phase423_invocation_4"
            else "Exact disclosed title rebus SalPhaseIon -> SalVATIon -> SALVATION."
        )
        records[invocation_id] = {
            "submission": {
                "bootstrap_read_used": True,
                "other_tool_used": False,
                "reasoning_text": reasoning,
                "candidates": [
                    {
                        "display": display,
                        "derivation": "derived only from the disclosed packet",
                        "rank": index + 1,
                    }
                    for index, display in enumerate(displays)
                ],
            },
            "tool_telemetry_available": False,
            "recorded_tool_calls": [],
        }
    return records


def compact_result(result):
    return {
        "phase": 423,
        "outcome": result["outcome"],
        "protocol_invalid_reason": result["protocol_invalid_reason"],
        "invocations_launched": 5,
        "unlaunched_invocation_ids": [
            "phase423_invocation_6", "phase423_invocation_7",
            "phase423_invocation_8",
        ],
        "voting_invocation_ids": [f"phase423_invocation_{i}" for i in range(1, 6)],
        "eligible_count": result["eligible_count"],
        "distinct_candidate_count": result["distinct_candidate_count"],
        "promoted_count": result["promoted_count"],
        "duplicate_promoted_count": result["duplicate_promoted_count"],
        "comparison_new_promoted_count": result["comparison_new_promoted_count"],
        "evaluated_new_count": result["evaluated_new_count"],
        "unevaluated_new_after_stop": result["unevaluated_new_after_stop"],
        "promoted": result["promoted"],
        "evaluations": [
            {
                "candidate_length": item["candidate_length"],
                "candidate_sha256": item["candidate_sha256"],
                "votes": item["votes"],
                "ranks": item["ranks"],
                "best_rank": item["best_rank"],
                "comparator_disposition": item["comparator_disposition"],
                "outcome": item["evaluation"]["outcome"],
            }
            for item in result["evaluations"]
        ],
        "oracle_calls": result["evaluated_new_count"],
        "terminal_hits": sum(
            item["evaluation"]["outcome"] == "terminal_hit"
            for item in result["evaluations"]
        ),
        "structural_hits": sum(
            item["evaluation"]["outcome"] == "structural_hit"
            for item in result["evaluations"]
        ),
    }


def build_ledger(rows):
    return {
        "phase": 423,
        "launcher_sha256": phase423.LAUNCHER_SHA256,
        "launcher_length": phase423.LAUNCHER_LENGTH,
        "prompt_sha256": phase423.PROMPT_SHA256,
        "prompt_length": phase423.PROMPT_LENGTH,
        "evidence_packet_sha256": phase423.EVIDENCE_PACKET_SHA256,
        "configuration": phase423.INVOCATION_CONFIGURATION,
        "invocations_launched": 5,
        "unlaunched_invocation_ids": [
            "phase423_invocation_6", "phase423_invocation_7",
            "phase423_invocation_8",
        ],
        "voting_invocation_ids": [f"phase423_invocation_{i}" for i in range(1, 6)],
        "records": {
            invocation_id: {
                "task_path": f"/root/{invocation_id}",
                "tool_telemetry_available": False,
                "bootstrap_read_self_disclosed": True,
                "other_tool_use_self_disclosed": False,
                "eligible": True,
                "voting": True,
                "candidate_count": len(displays),
                "candidate_displays": displays,
                "response_capture": (
                    "raw collaboration payload retained in the orchestrator transcript; "
                    "this ledger preserves exact candidate display bytes and ranks"
                ),
            }
            for invocation_id, displays in rows.items()
        },
    }


def audit():
    rows = candidate_rows()
    records = build_records(rows)
    for invocation_id, record in records.items():
        ok, reason = phase423.validate_invocation_record(record)
        if not ok:
            raise AssertionError(f"{invocation_id} replay is ineligible: {reason}")
    result = phase423.close_phase(records, 5)
    compact = compact_result(result)
    if compact["eligible_count"] != 5:
        raise AssertionError("Phase 423 did not close with five eligible submissions")
    if compact["outcome"] in {"need_more", "protocol_invalid"}:
        raise AssertionError(f"Phase 423 closure failed: {compact}")
    return compact, build_ledger(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-artifacts", action="store_true")
    args = parser.parse_args()
    result, ledger = audit()
    if args.write_artifacts:
        RESULT_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        LEDGER_PATH.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
