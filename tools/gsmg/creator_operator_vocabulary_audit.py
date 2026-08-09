#!/usr/bin/env python3
"""Inventory authenticated GSMG operators without composing new transforms.

The audit separates three evidence classes:

* operators demonstrated by a successful, reproduced stage transition;
* creator-authored endgame vocabulary whose operation is still unresolved;
* attractive terms that are not authenticated operator precedents.

It then asks whether the first two classes jointly fix every field required to
consume the exact 31-character DBBI selection under ``matrixsumlist``.
"""

import argparse
import json
from pathlib import Path

import first_hint_hash_audit
import first_puzzle_announcement_audit
import grid_spiral
import page_structure_audit
from data import VALIDATION_ANSWER, VALIDATION_NUM
from salphaseion_title_rebus_audit import (
    EXPECTED_MACRO,
    decode_reversed_bitstream,
)
from support_group_export_delta_audit import (
    CREATOR_ID,
    DEFAULT_EXPORT_DIR as SUPPORT_EXPORT_DIR,
    plain_text,
)
from telegram_export_manifest import DEFAULT_EXPORT_DIR as SOLVER_EXPORT_DIR


SELECTED_31 = "ncsyangcahiriasogaleafayanestve"
CREATOR_MACRO_ID = 8446

# Each record is a precedent whose output is independently recognizable or
# authenticated by the next solved stage.  These are intentionally not a bag
# of words mined from all puzzle prose.
SOLVED_OPERATORS = (
    {
        "operator": "concatenate",
        "stage": "pre-rabbit first puzzle",
        "fixed_parameters": "two adjacent creator binary posts, source order",
        "verified_output": "one 5,368-bit stream",
    },
    {
        "operator": "decode 8-bit binary as ASCII",
        "stage": "pre-rabbit first puzzle and Stage 0",
        "fixed_parameters": "MSB-first bytes",
        "verified_output": "creator command stream / gsmg.io/theseedisplanted",
    },
    {
        "operator": "Caesar shift",
        "stage": "pre-rabbit first puzzle",
        "fixed_parameters": "shift -3, selected by creator Caesar clue",
        "verified_output": "removethecorrecthinttoproceedtothenextstage",
    },
    {
        "operator": "reverse complete stream",
        "stage": "pre-rabbit first puzzle",
        "fixed_parameters": "whole text or whole inner bitstream",
        "verified_output": "reverse / BASE64 payload",
    },
    {
        "operator": "Base64 decode",
        "stage": "pre-rabbit first puzzle",
        "fixed_parameters": "literal BASE64 prefix",
        "verified_output": "terminal Rick Astley URL",
    },
    {
        "operator": "map colors to bits",
        "stage": "rabbit Stage 0",
        "fixed_parameters": "black/blue=1; white/yellow/FEFE=0",
        "verified_output": "Stage-1 URL after traversal",
    },
    {
        "operator": "counterclockwise spiral",
        "stage": "rabbit Stage 0",
        "fixed_parameters": "14x14, start top-left, first move down",
        "verified_output": "gsmg.io/theseedisplanted",
    },
    {
        "operator": "enter/submit literal password",
        "stage": "Stage 1 form",
        "fixed_parameters": "one exact lyric-derived string",
        "verified_output": "next authenticated page",
    },
    {
        "operator": "concatenate ordered fields",
        "stage": "Phase 3",
        "fixed_parameters": "seven parts in clue order",
        "verified_output": "known Phase-3 SHA-256 password",
    },
    {
        "operator": "preserve case; remove or retain whitespace",
        "stage": "Phase 3",
        "fixed_parameters": "explicit aBa / connected enf syntax",
        "verified_output": "known Phase-3 SHA-256 password",
    },
    {
        "operator": "prefix literal text",
        "stage": "Phase 3.2 clues",
        "fixed_parameters": "put giveit in front of justonesecond",
        "verified_output": "known Phase-3.2 SHA-256 password",
    },
    {
        "operator": "SHA-256 exact bytes",
        "stage": "Phases 2, 3, 3.2 and SalPhaseIon entry",
        "fixed_parameters": "one fixed preimage at each boundary",
        "verified_output": "four reproduced hashes used by solved transitions",
    },
    {
        "operator": "AES-256-CBC decrypt",
        "stage": "Phases 2, 3 and 3.2",
        "fixed_parameters": "OpenSSL Salted__ Base64 with the solved hash password",
        "verified_output": "authenticated next plaintext",
    },
    {
        "operator": "EBCDIC 1141 then Beaufort",
        "stage": "Phase 3.2.1",
        "fixed_parameters": "encoding 1141; key THEMATRIXHASYOU",
        "verified_output": "known Architect-derived plaintext",
    },
    {
        "operator": "keyed straddling-checkerboard decode",
        "stage": "Phase 3.2.2",
        "fixed_parameters": "deduped 28-symbol alphabet; escape digits 1 and 4",
        "verified_output": VALIDATION_ANSWER,
    },
    {
        "operator": "hash concatenated visible text",
        "stage": "extra-door entry",
        "fixed_parameters": "GSMGIO5BTCPUZZLECHALLENGE + prize address",
        "verified_output": first_hint_hash_audit.KNOWN_ENTRY_HASH,
    },
)


# Authenticated words/instructions near the unresolved transition.  Presence
# is primary evidence; "demonstrated" remains false unless the instruction has
# already produced a solved downstream transition.
ENDGAME_VOCABULARY = (
    {
        "token": "yellow blue primes",
        "source": "creator macro 8446 + prime/zeroing hints",
        "role": "upstream selection vocabulary",
        "demonstrated_consumer": False,
    },
    {
        "token": "matrix sum list",
        "source": "creator macro 8446 and authenticated SalPhaseIon bytes",
        "role": "names the unresolved consumer",
        "demonstrated_consumer": False,
    },
    {
        "token": "last words before archi choice",
        "source": "creator macro 8446 and authenticated SalPhaseIon bytes",
        "role": "semantic selection instruction; operand relationship unresolved",
        "demonstrated_consumer": False,
    },
    {
        "token": "yin yang",
        "source": "creator macro 8446 + creator recognition messages",
        "role": "reached state/next phase, not an algorithm",
        "demonstrated_consumer": False,
    },
    {
        "token": "zeroed out",
        "source": "creator message 8000",
        "role": "destructive/filtering verb without fixed characters or stage scope",
        "demonstrated_consumer": False,
    },
    {
        "token": "first or zero",
        "source": "creator message 4105",
        "role": "bit/index vocabulary without a selected convention here",
        "demonstrated_consumer": False,
    },
    {
        "token": "sha256 our first hint is your last command",
        "source": "authenticated SalPhaseIon bytes",
        "role": "hash/command instruction with unresolved exact preimage",
        "demonstrated_consumer": False,
    },
    {
        "token": "enter",
        "source": "authenticated SalPhaseIon bytes",
        "role": "validated separator between equal AES halves; no matrix role",
        "demonstrated_consumer": True,
    },
)


EXCLUDED_TERMS = (
    {
        "term": "XOR",
        "reason": "no verified solved puzzle transition uses it; current prominence is spam/community-derived",
    },
    {
        "term": "beginnings/endings",
        "reason": "post-hoc Architect-word indexing label, not a creator-authored or solved operator",
    },
    {
        "term": "subtract/difference",
        "reason": "used in brainstorm arithmetic, not in an authenticated solved transition",
    },
    {
        "term": "BATCH/execute",
        "reason": "community rebus hypothesis, explicitly parked by the strict gate",
    },
)


def load_messages(path):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return {message["id"]: message for message in payload["messages"]}


def audit(
    solver_export=SOLVER_EXPORT_DIR / "result.json",
    support_export=SUPPORT_EXPORT_DIR / "result.json",
    page_html=page_structure_audit.DEFAULT_HTML,
):
    solver_messages = load_messages(solver_export)
    support_messages = load_messages(support_export)

    macro_message = solver_messages[CREATOR_MACRO_ID]
    macro = decode_reversed_bitstream(macro_message["text"])
    creator_hints = {}
    for message_id, fragment in (
        (4105, "First or zero"),
        (8000, "zeroed out"),
    ):
        message = solver_messages[message_id]
        text = message["text"] if isinstance(message["text"], str) else "".join(
            item if isinstance(item, str) else item.get("text", "")
            for item in message["text"]
        )
        if message.get("from_id") != CREATOR_ID or fragment not in text:
            raise AssertionError(f"creator hint {message_id} changed")
        creator_hints[message_id] = text

    # The support-group record explicitly confirms that reverse was a real
    # creator-selected operation in the older puzzle, rather than a generic
    # transform added retrospectively.
    reverse_confirmation = support_messages[26083]
    if reverse_confirmation.get("from_id") != CREATOR_ID:
        raise AssertionError("support reverse confirmation is not creator-authored")
    if "Use that hint on the 2nd binary code." not in plain_text(reverse_confirmation):
        raise AssertionError("support reverse confirmation text changed")

    _, old_binary = first_puzzle_announcement_audit.extract_forwarded_payload(
        solver_export
    )
    old_chain = first_puzzle_announcement_audit.reconstruct(old_binary)
    _, _, _, stage0_url = grid_spiral.decode()
    first_hint_hash_audit.self_test()
    page = page_structure_audit.audit(Path(page_html))
    decoded_page_tokens = tuple(
        segment["decoded"]
        for segment in page["salphaseion"]["segments"]
        if segment["decoded"]
    )

    # Fields that a complete `matrixsumlist` consumer must specify.  A
    # precedent is not a binding: the current instruction must select it.
    g3_fields = {
        "matrix_dimensions": {
            "status": "MISSING",
            "precedent": "14x14 exists at Stage 0",
            "why_not_fixed": "31 symbols do not fill 14x14 and no padding/placement rule is authored",
        },
        "input_placement": {
            "status": "MISSING",
            "precedent": "ordered concatenation exists in solved phases",
            "why_not_fixed": "no row/column/spiral placement of the 31 symbols is selected",
        },
        "traversal_orientation": {
            "status": "MISSING",
            "precedent": "top-left CCW spiral and whole-stream reverse both exist",
            "why_not_fixed": "neither is bound to matrixsumlist; they are competing precedents",
        },
        "symbol_to_number_mapping": {
            "status": "MISSING",
            "precedent": "bit mapping and clue-specific numeric alphabets exist",
            "why_not_fixed": "no mapping is selected for letters in the 31-character input",
        },
        "aggregation": {
            "status": "MISSING",
            "precedent": "the word sum is authenticated",
            "why_not_fixed": "no solved stage demonstrates matrix row sums, column sums, totals, or indices",
        },
        "list_serialization": {
            "status": "MISSING",
            "precedent": "ordered concatenation exists",
            "why_not_fixed": "row-only vs column-only vs row+column and delimiters remain unspecified",
        },
        "next_artifact_or_target": {
            "status": "MISSING",
            "precedent": "hash and AES consumers exist at earlier boundaries",
            "why_not_fixed": "no authenticated expected hash, plaintext, URL, or blob binding is supplied",
        },
    }

    return {
        "source_checks": {
            "creator_macro": macro,
            "creator_macro_matches": macro == EXPECTED_MACRO,
            "creator_hints": creator_hints,
            "old_reverse_command": old_chain["reverse_command"].decode(),
            "old_final_url": old_chain["final_url"].decode(),
            "stage0_url": stage0_url,
            "page_decoded_tokens": decoded_page_tokens,
            "checkerboard_validation_input_length": len(VALIDATION_NUM),
            "checkerboard_validation_answer": VALIDATION_ANSWER,
        },
        "solved_operator_count": len(SOLVED_OPERATORS),
        "solved_operators": SOLVED_OPERATORS,
        "endgame_vocabulary": ENDGAME_VOCABULARY,
        "excluded_terms": EXCLUDED_TERMS,
        "g3_fields": g3_fields,
        "g3_fixed_field_count": sum(
            field["status"] == "FIXED" for field in g3_fields.values()
        ),
        "g3_total_field_count": len(g3_fields),
        "g3_pass": all(field["status"] == "FIXED" for field in g3_fields.values()),
        "verdict": "operator precedents constrain style but do not bind a matrixsumlist consumer",
    }


def self_test(**kwargs):
    report = audit(**kwargs)
    checks = report["source_checks"]
    assert checks["creator_macro_matches"]
    assert checks["old_reverse_command"] == "reverse"
    assert checks["stage0_url"] == "gsmg.io/theseedisplanted"
    assert "matrixsumlist" in checks["page_decoded_tokens"]
    assert "enter" in checks["page_decoded_tokens"]
    assert report["solved_operator_count"] == 16
    assert {item["term"] for item in report["excluded_terms"]} >= {
        "XOR", "beginnings/endings"
    }
    assert report["g3_fixed_field_count"] == 0
    assert report["g3_total_field_count"] == 7
    assert not report["g3_pass"]
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--solver-export", type=Path, default=SOLVER_EXPORT_DIR / "result.json")
    parser.add_argument("--support-export", type=Path, default=SUPPORT_EXPORT_DIR / "result.json")
    parser.add_argument("--page-html", type=Path, default=page_structure_audit.DEFAULT_HTML)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    kwargs = {
        "solver_export": args.solver_export,
        "support_export": args.support_export,
        "page_html": args.page_html,
    }
    report = self_test(**kwargs) if args.self_test else audit(**kwargs)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
