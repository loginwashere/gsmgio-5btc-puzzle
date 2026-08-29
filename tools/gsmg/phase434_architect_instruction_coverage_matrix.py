#!/usr/bin/env python3
"""Phase 434: assertion-backed Architect instruction/coverage matrix.

This is synthesis, not a password search.  It freshly derives the connected
Phase-3.2.1 plaintext, verifies every displayed instruction clause against it,
and records which concrete consumers prior phases tested.  No encrypted blob
is queried and no password material is generated.
"""

import argparse
import json
import re
from pathlib import Path

from findings_store import read_findings
from p32_sibling_password_audit import derive_sibling_outputs


REPO_ROOT = Path(__file__).resolve().parents[2]

CLAUSES = (
    {
        "id": "function_you",
        "display": "THE FUNCTION OF THE YOU IS",
        "provenance": "Film skeleton; ONE is replaced by YOU.",
        "best_role": "Addressing/routing frame, not password material.",
        "source_object": "Matrix Architect dialogue is fixed for the parody; no new downstream source.",
        "operator": "Substitution ONE -> YOU is visible but supplies no general transform.",
        "boundary": "README words only; connected letters are authenticated.",
        "coverage": "Passage-wide and line/word password families closed by Phases 267, 307, and 314.",
        "status": "thematic frame",
        "reopen_condition": "A creator-grounded target for the ONE -> YOU substitution.",
    },
    {
        "id": "source_codes",
        "display": "NOW TO RETURN TO THE SOURCE CODES",
        "provenance": "Film has RETURN TO THE SOURCE; puzzle pluralizes SOURCE CODES.",
        "best_role": "Possible source-selection instruction.",
        "source_object": "Unfixed: film, screenplay, source code, sibling output, and first-piece material compete.",
        "operator": "RETURN/REINSERT suggests reuse but does not specify extraction.",
        "boundary": "No authenticated code-unit or source boundary.",
        "coverage": "Literal forms closed by Phase 265; whole passage by Phase 307; source-reinsertion variants proved unstable in earlier Architect audits.",
        "status": "operationally underdefined",
        "reopen_condition": "An authenticated source object plus its unit, order, and boundary.",
    },
    {
        "id": "temporary_dissemination",
        "display": "ALLOWING A TEMPORARY DISSEMINATION OF THE CODE YOU HOPEFULLY CARRY",
        "provenance": "TEMPORARY traces to the screenplay; HOPEFULLY is creator-added; surrounding sentence is Matrix-derived.",
        "best_role": "Provenance texture and narrative description.",
        "source_object": "The code carried by YOU is not independently identified.",
        "operator": "DISSEMINATION does not fix split, copy, or interleave semantics.",
        "boundary": "Mixed film/screenplay wording defeats a single-source positional rail.",
        "coverage": "Mixed provenance established by Phase 235; direct/whole-text families negative.",
        "status": "recognition-only",
        "reopen_condition": "Independent evidence assigning CODE YOU CARRY to a concrete artifact.",
    },
    {
        "id": "prime_basics",
        "display": "REINSERTING THE PRIME BASICS",
        "provenance": "Film PRIME PROGRAM is replaced by PRIME BASICS.",
        "best_role": "Prime-selection operator candidate.",
        "source_object": "No clause-local source; Phase 270 tried the grounded 3.2.2 and Stage-0 referents.",
        "operator": "Prime indexing/prime walk is plausible but base, rail, and event serialization are not fixed here.",
        "boundary": "No clause-local index base or length.",
        "coverage": "Literal forms negative in Phase 265; prime walk, pure prime indices, Stage-0 projections, and split-guide retarget negative in Phase 270.",
        "status": "tested constructions negative; general phrase underdefined",
        "reopen_condition": "New authenticated source and exact prime consumer, not another index variant.",
    },
    {
        "id": "required_select",
        "display": "AFTER WHICH YOU WILL BE REQUIRED TO SELECT FROM",
        "provenance": "Direct film sentence skeleton.",
        "best_role": "Operator framing; doubled BE REQUIRED is separately frozen for Phase 435.",
        "source_object": "SELECT FROM has no local object beyond the following thematic count nouns.",
        "operator": "Selection is named; selection rule is absent.",
        "boundary": "The BE REQUIRED repetition depends on README word segmentation.",
        "coverage": "Selection constructions tied to prime/guide consumers were negative in Phase 270.",
        "status": "Phase 435 negative; otherwise underdefined",
        "reopen_condition": "New evidence must identify a unique operation and independently registered consumer.",
    },
    {
        "id": "numeric_triple",
        "display": "OVER TWENTY-THREE CIPHERS SIXTEEN ENCRYPTIONS AND OR SEVEN INTERTWINED PASSWORDS",
        "provenance": "Film's 23 individuals / 16 female / 7 male with crypto nouns substituted.",
        "best_role": "Structural checkpoint, not an independently sourced fresh key.",
        "source_object": "Split-final-BE guide gives 23 endpoints partitioned 16 blue / 7 yellow.",
        "operator": "AND/OR is logically suggestive, but endpoint union/intersection is trivial; source-bound strings remain unspecified.",
        "boundary": "The split-final-BE boundary is recovered externally, not specified by this sentence.",
        "coverage": "Phase 61 classifies the profile; Phase 270 tests direct prime-rule/token/raw endpoint consumers and sibling compositions, all negative.",
        "status": "checkpoint real; downstream consumer unbound",
        "reopen_condition": "A fixed source string, endpoint-to-character map, direction, and AND/OR serialization.",
    },
    {
        "id": "private_key_note",
        "display": "TO FIND THE ACTUAL PRIVATE KEYNOTE THAT ALSO",
        "provenance": "Creator rewrite; authenticated Beaufort output has no spaces or punctuation.",
        "best_role": "PRIVATE KEY is the expected output type; NOTE THAT is a plausible meta-instruction boundary.",
        "source_object": "P32's two-key payload hypothesis is structurally motivated, but KEY/NOTE is not password material.",
        "operator": "No operator follows from KEY, NOTE, or KEYNOTE alone.",
        "boundary": "KEYNOTE vs KEY / NOTE is not cryptographically authenticated; README prints KEYNOTE.",
        "coverage": "KEY, NOTE, SELF, KEYNOTE, and SELFSELF direct-password forms are negative in Phase 235; whole-block families are also negative.",
        "status": "semantic reading retained; literal-material route closed",
        "reopen_condition": "Independent punctuation/boundary evidence or a consumer explicitly requesting a note field.",
    },
    {
        "id": "brute_force",
        "display": "BRUTE FORCING MIGHT BE REQUIRED",
        "provenance": "Creator-added; no counterpart in the Matrix film sentence.",
        "best_role": "Method warning applying to the selection/encryption/password step.",
        "source_object": "No candidate alphabet or unknown positions are specified locally.",
        "operator": "Authorizes search only after a finite construction space is independently defined.",
        "boundary": "README sentence boundary is editorial; connected letters are authenticated.",
        "coverage": "Literal phrase negative in Phase 265; it does not broaden already bounded brute-force scopes.",
        "status": "method, not material",
        "reopen_condition": "A sealed alphabet, variable positions, consumer, and success oracle.",
    },
)

REQUIRED_PHASE_HEADINGS = {
    61: "## Phase 61 --",
    235: "## Phase 235 --",
    265: "## Phase 265 --",
    267: "## Phase 267 --",
    270: "## Phase 270 --",
    307: "## Phase 307 --",
    314: "## Phase 314 --",
    370: "## Phase 370 --",
}


def letters(value):
    return re.sub(r"[^A-Za-z]", "", value).upper()


def audit():
    derived = derive_sibling_outputs()
    answer = derived["answer_321"]
    offsets = []
    cursor = 0
    for row in CLAUSES:
        needle = letters(row["display"])
        position = answer.find(needle, cursor)
        if position < 0:
            raise AssertionError(f"clause not found in derived plaintext: {row['id']}")
        offsets.append({"id": row["id"], "start_0": position, "end_exclusive_0": position + len(needle)})
        cursor = position + len(needle)

    findings = read_findings()
    for phase, heading in REQUIRED_PHASE_HEADINGS.items():
        if heading not in findings:
            raise AssertionError(f"required Phase {phase} finding is absent")

    return {
        "phase": 434,
        "kind": "oracle-free synthesis",
        "fresh_321_length": len(answer),
        "fresh_321_sha256_not_recorded": True,
        "clause_count": len(CLAUSES),
        "clauses": CLAUSES,
        "derived_offsets": offsets,
        "model_comparison": (
            {
                "model": "literal passphrase",
                "fit": "weak",
                "coverage": "word, phrase, line, reverse, creator-only rows, and whole-block families are negative",
                "disposition": "closed absent new material boundary",
            },
            {
                "model": "macro routing/checkpoint",
                "fit": "partial",
                "coverage": "23/16/7 is a real recovered checkpoint and feeds the established Architect dialogue indexing chain",
                "disposition": "retained where already solved; no new P32 consumer",
            },
            {
                "model": "3.2.1 operator / 3.2.2 data / P32 output",
                "fit": "plausible architecture, unsupported execution",
                "coverage": "Phase 270 tested 25 declared candidates / 50 materials / 6 specs with zero structural hits",
                "disposition": "parked; reopen only with a new authenticated selector",
            },
            {
                "model": "semantic instruction",
                "fit": "strongest line-by-line reading",
                "coverage": "PRIVATE KEY as output type, NOTE as possible meta-boundary, BRUTE FORCING as method",
                "disposition": "retained as interpretation, insufficient to generate candidates",
            },
        ),
        "and_or_gate": {
            "endpoint_sets": "source-free union/intersection is structurally trivial because blue and yellow partition the 23 endpoints",
            "decoded_strings": "blocked until source, sequence, direction, boundary, and serialization are independently fixed",
            "authorized_now": False,
        },
        "oracle_calls": 0,
        "password_materials_generated": 0,
    }


def self_test():
    report = audit()
    assert report["clause_count"] == 8
    assert [row["id"] for row in report["clauses"]] == [row["id"] for row in CLAUSES]
    assert all(a["end_exclusive_0"] <= b["start_0"] for a, b in zip(report["derived_offsets"], report["derived_offsets"][1:]))
    assert report["model_comparison"][2]["disposition"].startswith("parked")
    assert report["and_or_gate"]["authorized_now"] is False
    assert report["oracle_calls"] == report["password_materials_generated"] == 0
    print("[*] Phase 434 self-test OK: 8 ordered clauses, 4 models, 0 oracle calls")


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
