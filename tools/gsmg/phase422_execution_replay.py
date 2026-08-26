#!/usr/bin/env python3
"""Deterministic eligibility replay and closure writer for Phase 422."""

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase422_p32trailing_macro_clue_panel_audit as phase422  # noqa: E402

RESULT_PATH = SCRIPT_DIR / "phase422_result.json"
LEDGER_PATH = SCRIPT_DIR / "phase422_invocation_ledger.json"


def candidate_rows():
    all_fragments = (
        "yellowblueprimesmatrixsumlistlastwordsbeforearchichoiceyinyang"
        "wewontgiveawaythepassworditsinfrontofyoureyesbutyourenotseeingit"
        "verylaststepisatruegiveawaypromised"
    )
    return {
        "phase422_invocation_1": [
            "THEONE", "CIAOBELLAO", "HALFANDBETTERHALF", "PROMISED",
            "SALVATION", "BUTULTIMATELYTHE", "BUTHYE",
            "verylaststepisatruegiveawaypromised",
            "GOODLUCKNEVERTHELESSIREALLYHOPEYOURETHEONECIAOBELLAO",
            all_fragments,
        ],
        "phase422_invocation_2": [
            "promised", "verylaststepisatruegiveawaypromised",
            "wewontgiveawaythepassword",
            "itsinfrontofyoureyesbutyourenotseeingit", "yinyangpromised",
            "BUTHYEpromised", "BOTHULTIMATELYTHEpromised", "BYEpromised",
            "SALVATION", all_fragments,
        ],
        "phase422_invocation_3": [
            "BUTHYE", "BUTBYE", "promised", "HYE", "BYE", "CIAOBELLAO",
            "itsinfrontofyoureyesbutyourenotseeingit", "yinyang",
            "SALVATION", "wewontgiveawaythepassword",
        ],
        "phase422_invocation_4": [
            "promised", "verylaststepisatruegiveawaypromised", "salvation",
            "BUTHYE", "BYE", "CIAOBELLAO", "FUNDSTOLIVE",
            "CIAOBELLAOFUNDSTOLIVE", "oneforonefourforone",
            "itsinfrontofyoureyesbutyourenotseeingit",
        ],
        "phase422_invocation_5": [
            "BOTHULTIMATELYTHESALVATION", "BUTHYESALVATION", "SALVATION",
            "verylaststepisatruegiveawaypromised",
            "itsinfrontofyoureyesbutyourenotseeingitverylaststepisatruegiveawaypromised",
            "wewontgiveawaythepassworditsinfrontofyoureyesbutyourenotseeingitverylaststepisatruegiveawaypromised",
            "yellowblueprimesmatrixsumlistlastwordsbeforearchichoiceyinyang",
            "BUTHYE", "CIAOBELLAO", "promised",
        ],
    }


def build_records(rows):
    records = {}
    for invocation_id, displays in rows.items():
        # Invocations 1-3 and 5 contain `yinyang` in an exact candidate.
        # Invocation 4's actual rank-3 derivation contains the exact disclosed
        # title `SalPhaseIon`; retain that eligibility-relevant excerpt here.
        reasoning = (
            "packet-local reconstruction reasoning"
            if invocation_id != "phase422_invocation_4"
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


def audit():
    rows = candidate_rows()
    records = build_records(rows)
    eligibility = {}
    for invocation_id, record in records.items():
        ok, reason = phase422.validate_invocation_record(record)
        violations = phase422.phase420.phase416.blinding_violations(
            phase422.phase420.phase416.submission_full_text(record["submission"])
        )
        if ok or not violations:
            raise AssertionError(f"{invocation_id} unexpectedly passed the frozen filter")
        eligibility[invocation_id] = {
            "eligible": False,
            "reason": reason,
            "blinding_violations": violations,
        }

    panel = phase422.evaluate_panel(records, 5)
    if panel["status"] != "need_more" or panel["eligible"]:
        raise AssertionError("five-response replay did not produce zero eligible records")
    remaining_ids = phase422.INVOCATION_CAP - len(records)
    if remaining_ids >= phase422.PANEL_TARGET:
        raise AssertionError("panel is not yet mathematically impossible")

    result = {
        "phase": 422,
        "outcome": "protocol_invalid",
        "protocol_invalid_reason": (
            "all five launched submissions were rejected by the inherited "
            "residue filter for repeating newly solver-visible macro terms; "
            "only three invocation IDs remained, fewer than the five eligible "
            "submissions still required"
        ),
        "invocations_launched": 5,
        "unlaunched_invocation_ids": [
            "phase422_invocation_6", "phase422_invocation_7",
            "phase422_invocation_8",
        ],
        "eligible_count": 0,
        "candidate_occurrence_count": sum(map(len, rows.values())),
        "distinct_candidate_count": len({value for values in rows.values() for value in values}),
        "promoted_count": 0,
        "oracle_calls": 0,
        "terminal_hits": 0,
        "structural_hits": 0,
        "eligibility": eligibility,
    }
    ledger = {
        "phase": 422,
        "launcher_sha256": phase422.LAUNCHER_SHA256,
        "launcher_length": phase422.LAUNCHER_LENGTH,
        "prompt_sha256": phase422.PROMPT_SHA256,
        "prompt_length": phase422.PROMPT_LENGTH,
        "configuration": phase422.INVOCATION_CONFIGURATION,
        "invocations_launched": 5,
        "records": {
            invocation_id: {
                "task_path": f"/root/{invocation_id}",
                "tool_telemetry_available": False,
                "bootstrap_read_self_disclosed": True,
                "other_tool_use_self_disclosed": False,
                "eligible": False,
                "candidate_count": len(displays),
                "candidate_displays": displays,
                "blinding_violations": eligibility[invocation_id]["blinding_violations"],
                "response_capture": (
                    "raw collaboration payload retained in the orchestrator "
                    "transcript; this ledger preserves exact candidate display "
                    "bytes, ranks, and eligibility-relevant residue"
                ),
            }
            for invocation_id, displays in rows.items()
        },
    }
    return result, ledger


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
