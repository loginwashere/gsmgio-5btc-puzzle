#!/usr/bin/env python3
"""Phase 532: rank tracked consumers by evidence-complete executability."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
RESULT_PATH = SCRIPT_DIR / "phase532_consumer_first_frontier_result.json"

FIELDS = (
    "authenticated_target",
    "expected_output_schema_fixed",
    "exact_terminal_validator",
    "independent_input_selector",
    "serialization_transform_fixed",
    "finite_uncovered_scope",
)

EVIDENCE_CHECKS = {
    "tools/gsmg/findings/P00270.md": "false-positive probability 2^-128",
    "tools/gsmg/findings/P00370.md": "0 genuinely new candidates",
    "tools/gsmg/findings/P00372.md": "COSMIC fails eligibility entirely: 0/5 fields bound",
    "tools/gsmg/findings/P00446.md": "sole already-runnable finite residual",
    "tools/gsmg/findings/P00448.md": "curated coverage debt rather than a clue-selected construction",
    "tools/gsmg/findings/P00479.md": "Tier-1 `--whitespace-variants` residual",
    "doc/GSMG_PHASE509A_CONSUMER_VALIDATOR_FEASIBILITY_AUDIT.md": "zero matches against the two frozen targets",
    "tools/gsmg/findings/P00517.md": "0 address hits on the other 3 readings",
    "tools/gsmg/findings/P00522.md": "34,074 total across all 4 tracked blobs",
    "tools/gsmg/findings/P00524.md": "closed negative",
    "tools/gsmg/findings/P00530.md": "bounded negative",
}


def make_row(
    identifier: str,
    label: str,
    values: tuple[bool, ...],
    *,
    operationally_runnable: bool,
    evidence: str,
) -> dict:
    if len(values) != len(FIELDS):
        raise ValueError("frontier row has wrong field count")
    record = {
        "id": identifier,
        "label": label,
        **dict(zip(FIELDS, values)),
        "operationally_runnable": operationally_runnable,
        "evidence": evidence,
    }
    record["gates_passed"] = sum(bool(record[field]) for field in FIELDS)
    record["eligible"] = all(record[field] for field in FIELDS)
    record["first_missing_field"] = next(
        (field for field in FIELDS if not record[field]), None
    )
    return record


def frontier_rows() -> list[dict]:
    return [
        make_row(
            "p32_two_private_key_role",
            "P32TRAILING as a 64-byte two-private-key payload",
            (True, True, True, False, True, False),
            operationally_runnable=False,
            evidence=(
                "The 80-byte ciphertext gives a conditional 2^-128 full-padding-block "
                "validator, and the solved crypto profile fixes the consumer transform; "
                "P32 has no local annotation selecting a new preimage source or finite boundary."
            ),
        ),
        make_row(
            "p32_tier1_nopad_whitespace",
            "Phase-163 Tier-1 no-padding whitespace backfill",
            (True, True, True, False, True, True),
            operationally_runnable=True,
            evidence=(
                "Approximately 700,000 keystrings remain finite and unrun, but Phases "
                "446/448 classify this as curated coverage debt rather than a clue-selected construction."
            ),
        ),
        make_row(
            "known_p2pkh_targets",
            "direct scalar derivation to the prize or halving P2PKH address",
            (True, True, True, False, False, False),
            operationally_runnable=False,
            evidence=(
                "The two targets and exact address validator are fixed, but no open artifact "
                "selects scalar bytes, hashing, compression state, or a finite fresh input family."
            ),
        ),
        make_row(
            "salph_local_password",
            "SALPH local/self-password branch",
            (True, False, False, True, True, False),
            operationally_runnable=False,
            evidence=(
                "The literal hash-prefix self-reading is grammar-eligible and covered; its "
                "plaintext type is not independently fixed and PKCS7/printability is not a decisive validator."
            ),
        ),
        make_row(
            "cosmic_local_container",
            "COSMIC as a self-contained OpenSSL container",
            (True, False, False, False, False, False),
            operationally_runnable=False,
            evidence=(
                "COSMIC contains no local instruction, has no fixed output schema, and fails "
                "the solved-boundary eligibility grammar before candidate generation."
            ),
        ),
        make_row(
            "urlblob_orphan",
            "orphaned URLBLOB encrypted object",
            (False, False, False, False, False, False),
            operationally_runnable=False,
            evidence=(
                "The object is retained as an oracle target, but lacks an authenticated local "
                "role, selected input, predicted plaintext schema, or standalone exact validator."
            ),
        ),
        make_row(
            "matrixsumlist_output",
            "matrixsumlist as a typed output/consumer",
            (True, False, False, False, False, False),
            operationally_runnable=False,
            evidence=(
                "The instruction token is authenticated, but dimensions, traversal, mapping, "
                "aggregation, serialization, consumer, and validator remain unbound."
            ),
        ),
        make_row(
            "dbbi84_direct_terminal_consumers",
            "DBBI 84-token residue/rails through the fixed terminal oracle",
            (True, True, True, True, True, False),
            operationally_runnable=False,
            evidence=(
                "This is the positive-control shape: source, boundaries, standard forms, "
                "consumers, and validators were all fixed, but Phase 530 already covered it negative."
            ),
        ),
    ]


def verify_evidence() -> dict[str, str]:
    digests: dict[str, str] = {}
    for filename, snippet in EVIDENCE_CHECKS.items():
        path = REPO_ROOT / filename
        text = " ".join(path.read_text(encoding="utf-8").lower().split())
        expected = " ".join(snippet.lower().split())
        if expected not in text:
            raise AssertionError(f"evidence snippet missing from {filename}: {snippet}")
        digests[filename] = hashlib.sha256(path.read_bytes()).hexdigest()
    return digests


def audit() -> dict:
    rows = frontier_rows()
    eligible = [row for row in rows if row["eligible"]]
    coverage_debts = [
        row for row in rows if row["operationally_runnable"] and not row["eligible"]
    ]
    ranking = sorted(
        rows,
        key=lambda row: (
            -row["gates_passed"],
            not row["exact_terminal_validator"],
            row["id"],
        ),
    )
    return {
        "phase": 532,
        "scope": "consumer-first evidence-completeness matrix; no candidate generation",
        "eligibility_fields": list(FIELDS),
        "rows": rows,
        "row_count": len(rows),
        "eligible_rows": eligible,
        "eligible_count": len(eligible),
        "operational_coverage_debts": coverage_debts,
        "operational_coverage_debt_count": len(coverage_debts),
        "ranking": [row["id"] for row in ranking],
        "strongest_evidence_selected_target": "p32_two_private_key_role",
        "execution_decision": "no_evidence_selected_consumer_run_authorized",
        "coverage_debt_decision": (
            "p32_tier1_nopad_whitespace_is_runnable_but_not_puzzle_selected"
        ),
        "evidence_file_sha256": verify_evidence(),
        "next_required_evidence": (
            "an existing closed-system object selecting the input preimage source and boundary "
            "for P32 or the known-address validator; absent that, more oracle menus only add coverage"
        ),
        "scope_checks": {
            "candidate_materials_generated": 0,
            "oracle_calls": 0,
            "decryptions": 0,
            "gpu_used": False,
        },
    }


def self_test() -> None:
    result = audit()
    assert result["row_count"] == 8
    assert result["eligible_count"] == 0
    assert result["operational_coverage_debt_count"] == 1
    assert result["operational_coverage_debts"][0]["id"] == "p32_tier1_nopad_whitespace"
    assert result["scope_checks"]["oracle_calls"] == 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("[*] Phase 532 self-test passed")
        return 0
    if args.run:
        result = audit()
        RESULT_PATH.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(
            json.dumps(
                {
                    "eligible_count": result["eligible_count"],
                    "operational_coverage_debt_count": result[
                        "operational_coverage_debt_count"
                    ],
                    "execution_decision": result["execution_decision"],
                },
                indent=2,
            )
        )
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
