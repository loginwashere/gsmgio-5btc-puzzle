#!/usr/bin/env python3
"""Deterministic replay and compact artifact writer for Phase 421."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase421_p32trailing_escalated_bootstrap_panel_audit as phase421  # noqa: E402

RESULT_PATH = SCRIPT_DIR / "phase421_result.json"
LEDGER_PATH = SCRIPT_DIR / "phase421_invocation_ledger.json"


def candidate_rows():
    state = phase421.phase420.phase418.recover_solution_state()
    answer = state["answer_322"]
    plaintext = state["answer_321"]
    key = "THEMATRIXHASYOU"
    alphabet = "FUBCDORA.LETHINGKYMVPS.JQZXW"
    prior = "jacquefrescogiveitjustonesecondheisenbergsuncertaintyprinciple"
    half = "HALFANDBETTERHALF"
    return {
        "phase421_invocation_1": [
            answer,
            "THEPRIVATEKEYSBELONGTOHALFANDBETTERHALFANDTHEYALSONEEDFUNDSTOLIVE",
            half, key, alphabet, key + alphabet + answer, alphabet + answer,
            key + answer, prior,
            "GOODLUCKNEVERTHELESSIREALLYHOPEYOURETHEONECIAOBELLAO",
        ],
        "phase421_invocation_2": [
            answer, half, "HALFBETTERHALF", key + answer, answer + key, key,
            alphabet, alphabet + "14", "14" + alphabet, "SOURCECODESPRIMEBASICS",
        ],
        "phase421_invocation_3": [
            plaintext + answer, answer, half, key + answer, key + alphabet, key,
            alphabet,
            "TWENTYTHREECIPHERSSIXTEENENCRYPTIONSANDORSEVENINTERTWINEDPASSWORDS",
            "BETTERHALF", "HALF",
        ],
        "phase421_invocation_4": [
            answer, half, "HALFANDBETTERHALFANDTHEYALSONEEDFUNDSTOLIVE", prior,
            "causalitySafenetLunaHSM111100x736B6E616220726F662074756F6C69616220646E6F63657320666F206B6E697262206E6F20726F6C6C65636E61684320393030322F6E614A2F33302073656D695420656854B5KR/1r5B/2R5/2b1p1p1/2P1k1P1/1p2P2p/1P2P2P/3N1N2 b - - 0 1",
            key, alphabet, prior + answer, key + alphabet, "PRIMEBASICS",
        ],
        "phase421_invocation_5": [
            answer, half + "FUNDSTOLIVE", half, "FUNDSTOLIVE", prior + answer,
            key + answer, alphabet + answer, prior, key, alphabet,
        ],
        "phase421_invocation_6": [
            plaintext + answer, answer,
            "HALFANDBETTERHALFANDTHEYALSONEEDFUNDSTOLIVE", half, "FUNDSTOLIVE",
            key, alphabet, "CIAOBELLAO",
        ],
    }


def build_records(rows):
    records = {}
    for invocation_id in sorted(rows)[:5]:
        candidates = [
            {
                "display": display,
                "derivation": "derived only from disclosed solved components",
                "rank": index + 1,
            }
            for index, display in enumerate(rows[invocation_id])
        ]
        records[invocation_id] = {
            "submission": {
                "bootstrap_read_used": True,
                "other_tool_used": False,
                "reasoning_text": "packet-local reconstruction reasoning",
                "candidates": candidates,
            },
            "tool_telemetry_available": False,
            "recorded_tool_calls": [],
        }
    return records


def compact_result(result):
    return {
        "phase": 421,
        "outcome": result["outcome"],
        "protocol_invalid_reason": result["protocol_invalid_reason"],
        "invocations_launched": 6,
        "voting_invocation_ids": [f"phase421_invocation_{i}" for i in range(1, 6)],
        "nonvoting_concurrent_invocation_ids": ["phase421_invocation_6"],
        "eligible_count": result["eligible_count"],
        "distinct_candidate_count": result["distinct_candidate_count"],
        "promoted_count": result["promoted_count"],
        "duplicate_promoted_count": result["duplicate_promoted_count"],
        "genuinely_new_promoted_count": result["genuinely_new_promoted_count"],
        "evaluated_new_count": result["evaluated_new_count"],
        "unevaluated_new_after_stop": result["unevaluated_new_after_stop"],
        "phase270_duplicate_singleton_present": result[
            "phase270_duplicate_singleton_present"
        ],
        "promoted": result["promoted"],
        "evaluations": [
            {
                "candidate_length": item["candidate_length"],
                "candidate_sha256": item["candidate_sha256"],
                "votes": item["votes"],
                "ranks": item["ranks"],
                "best_rank": item["best_rank"],
                "phase270_disposition": item["phase270_disposition"],
                "outcome": item["evaluation"]["outcome"],
            }
            for item in result["evaluations"]
        ],
        "oracle_calls": result["evaluated_new_count"],
        "terminal_hits": 0,
        "structural_hits": 0,
    }


def build_ledger(rows):
    return {
        "phase": 421,
        "launcher_sha256": phase421.LAUNCHER_SHA256,
        "launcher_length": phase421.LAUNCHER_LENGTH,
        "prompt_sha256": phase421.phase420.PROMPT_SHA256,
        "prompt_length": phase421.phase420.PROMPT_LENGTH,
        "configuration": phase421.INVOCATION_CONFIGURATION,
        "diagnostic_invocations_excluded": ["phase421_escalated_read_diagnostic"],
        "invocations_launched": 6,
        "voting_invocation_ids": [f"phase421_invocation_{i}" for i in range(1, 6)],
        "records": {
            invocation_id: {
                "task_path": f"/root/{invocation_id}",
                "tool_telemetry_available": False,
                "bootstrap_read_self_disclosed": True,
                "other_tool_use_self_disclosed": False,
                "eligible": index <= 5,
                "voting": index <= 5,
                "candidate_count": len(displays),
                "candidate_displays": displays,
                "response_capture": (
                    "raw collaboration payload retained in the orchestrator transcript; "
                    "this ledger preserves exact candidate display bytes and ranks"
                ),
            }
            for index, (invocation_id, displays) in enumerate(sorted(rows.items()), 1)
        },
    }


def audit():
    rows = candidate_rows()
    records = build_records(rows)
    for invocation_id, record in records.items():
        ok, reason = phase421.validate_invocation_record(record)
        if not ok:
            raise AssertionError(f"{invocation_id} replay is ineligible: {reason}")
    result = phase421.close_phase(records, 5)
    compact = compact_result(result)
    assert compact["outcome"] == "novel_convergence_negative"
    assert compact["eligible_count"] == 5
    assert compact["distinct_candidate_count"] == 26
    assert compact["promoted_count"] == 9
    assert compact["duplicate_promoted_count"] == 1
    assert compact["genuinely_new_promoted_count"] == 8
    assert compact["evaluated_new_count"] == 8
    assert all(item["outcome"] == "negative" for item in compact["evaluations"])
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
