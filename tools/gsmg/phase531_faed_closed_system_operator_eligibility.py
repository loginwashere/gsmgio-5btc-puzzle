#!/usr/bin/env python3
"""Phase 531: refresh the closed-system eligibility matrix for FAED."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

from data import FAED  # noqa: E402

RESULT_PATH = SCRIPT_DIR / "phase531_faed_operator_eligibility_result.json"
EXPECTED_FAED_SHA256 = "066191b4aafc114fbca7f0d168382f40129c4ff18490375b689741081d5ef3c2"
FIELDS = (
    "authenticated_source",
    "faed_operand_binding",
    "operation_selected",
    "parameters_fixed",
    "consumer_fixed",
    "validator_fixed",
)

EVIDENCE_CHECKS = {
    "P00101.md": "no unique typed program is recovered",
    "P00218.md": "no authenticated decoder or combining operation",
    "P00219.md": "No clue-supported decoder model remains untested",
    "P00220.md": "presentation supplies no DBBI/FAED",
    "P00371.md": "recognition_checkpoint_no_demonstrated_consumer",
    "P00386.md": "not promoted",
    "P00424.md": "FAED decoder unknown",
    "P00477.md": "bounded negative",
    "P00525.md": "structural-only",
    "P00530.md": "bounded negative",
}


def row(identifier: str, label: str, values: tuple[bool, ...], **extra) -> dict:
    if len(values) != len(FIELDS):
        raise ValueError("eligibility row has wrong field count")
    record = {"id": identifier, "label": label, **dict(zip(FIELDS, values)), **extra}
    record["eligible"] = all(record[field] for field in FIELDS) and not record["covered"]
    record["first_missing_field"] = next(
        (field for field in FIELDS if not record[field]),
        "already_covered" if record["covered"] else None,
    )
    return record


def operator_rows() -> list[dict]:
    return [
        row(
            "adjacent_lastwords_thispassword",
            "literal lastwordsbeforearchichoice / thispassword adjacency",
            (True, False, False, False, False, False),
            covered=False,
            evidence="Phases 101/218/371: adjacency is exact, but three typed roles remain and adjacency does not select FAED as operand",
        ),
        row(
            "checkerboard_25_code",
            "25-code straddling-checkerboard substitution",
            (True, True, False, False, False, False),
            covered=True,
            evidence="{g,i} is a ciphertext-only statistical checkpoint; board mapping and output consumer remain unfixed; plain cells are calibrated negative",
        ),
        row(
            "checkerboard_columnar_transposition",
            "checkerboard plus columnar transposition",
            (True, True, False, False, False, False),
            covered=False,
            evidence="historical precedent exists, but FAED locally selects no pair/width/direction/board; bounded cells in Phases 477 and 484-508 missed",
        ),
        row(
            "dbbi_keyed_bifid",
            "DBBI-keyed Bifid over FAED",
            (True, False, False, False, False, False),
            covered=True,
            evidence="Phase 386 reproduces BTCSEED but period/key construction is community-selected and output is noise-like with no consumer",
        ),
        row(
            "matrixsumlist",
            "matrixsumlist",
            (True, False, True, False, False, False),
            covered=False,
            evidence="authenticated token is adjacent to DBBI, not bound to FAED; seven operation fields remain unbound (G-MSL-001)",
        ),
        row(
            "prime_color_selectors",
            "established prime/color selectors",
            (True, False, True, True, False, False),
            covered=True,
            evidence="operators are real elsewhere but no source binds them to FAED; direct color-mask and 23/16/7 FAED applications are negative",
        ),
        row(
            "hash_kdf_encrypted_consumer",
            "SHA/KDF into tracked encrypted containers",
            (True, False, True, True, False, True),
            covered=True,
            evidence="crypto profile and validators are fixed, but no decoded FAED boundary/preimage or unique target role is selected",
        ),
        row(
            "dbbi_84_host_rails",
            "DBBI 84-token residue and 16/7 host rails",
            (True, False, True, True, False, True),
            covered=True,
            evidence="Phases 525-530 validate DBBI structure and close direct password use; no edge maps these rails into FAED",
        ),
        row(
            "known_text_crib",
            "exact known-text crib constraint",
            (True, False, True, True, False, True),
            covered=False,
            evidence="the CSP is mechanically calibrated, but no independent clue says FAED contains any known solved phrase",
        ),
        row(
            "terminal_structural_validator",
            "terminal AES/address/key-format validator",
            (True, False, True, True, True, True),
            covered=False,
            evidence="strong validators exist only at full terminal outputs; they do not select a decoder or provide a search gradient",
        ),
    ]


def verify_evidence() -> dict[str, str]:
    digests = {}
    findings = SCRIPT_DIR / "findings"
    for filename, snippet in EVIDENCE_CHECKS.items():
        path = findings / filename
        text = path.read_text(encoding="utf-8")
        normalized_text = " ".join(text.lower().split())
        normalized_snippet = " ".join(snippet.lower().split())
        if normalized_snippet not in normalized_text:
            raise AssertionError(f"evidence snippet missing from {filename}: {snippet}")
        digests[filename] = hashlib.sha256(path.read_bytes()).hexdigest()
    return digests


def audit() -> dict:
    faed_hash = hashlib.sha256(FAED.encode("ascii")).hexdigest()
    if faed_hash != EXPECTED_FAED_SHA256:
        raise AssertionError("FAED source bytes changed")
    rows = operator_rows()
    eligible = [record for record in rows if record["eligible"]]
    return {
        "phase": 531,
        "scope": "closed-system evidence-to-operation eligibility refresh; no candidate generation",
        "faed": {"length": len(FAED), "sha256": faed_hash},
        "eligibility_fields": list(FIELDS),
        "evidence_file_sha256": verify_evidence(),
        "rows": rows,
        "row_count": len(rows),
        "eligible_uncovered_rows": eligible,
        "eligible_uncovered_count": len(eligible),
        "new_delta_since_phase219": [
            "the transposition/search campaign adds bounded misses but no local width/direction/board selector",
            "the DBBI 84-token parse strengthens DBBI structure but creates no authenticated DBBI-to-FAED edge",
            "the 61-symbol residue and 35/25 rails are negative as direct passwords under the fixed oracle",
            "generic prose and shallow pair-ranking objectives fail real-versus-null discrimination",
        ],
        "execution_decision": "no_decoder_run_authorized",
        "next_required_evidence": (
            "a closed-system artifact that binds FAED to one operation and fixes its load-bearing parameters, "
            "or an exact consumer that predicts a terminal output without using generic fluency"
        ),
        "scope_checks": {
            "candidate_materials_generated": 0,
            "oracle_calls": 0,
            "faed_decodes_run": 0,
            "gpu_used": False,
        },
    }


def self_test() -> None:
    result = audit()
    assert result["row_count"] == 10
    assert result["eligible_uncovered_count"] == 0
    assert all(record["first_missing_field"] for record in result["rows"])
    assert result["scope_checks"]["oracle_calls"] == 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("[*] Phase 531 self-test passed")
        return 0
    if args.run:
        result = audit()
        RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({
            "row_count": result["row_count"],
            "eligible_uncovered_count": result["eligible_uncovered_count"],
            "execution_decision": result["execution_decision"],
        }, indent=2))
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
