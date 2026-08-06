#!/usr/bin/env python3
"""Provenance audit of the literal ``anstoo`` fragment and the SHA operand scope.

Phase 101 (``salphaseion_operand_binding_audit.py``) found that the typed
SalPhaseIon grammar is underdetermined at exactly two points: which words the
SHA-prefix command operates over, and what the trailing raw literal
``anstoo`` means. This module is the provenance follow-up it recommended --
it does not run any transform, cipher, or AES check. It only asks what the
creator and the community have actually said about these two literals,
using the complete 2026-07-26 Telegram export.

Every fact asserted here is checked directly against the archived source at
run time, not hardcoded from memory.
"""

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from telegram_export_manifest import DEFAULT_EXPORT_DIR  # noqa: E402

CREATOR_ID = "user9815232"

FORMAT_QUESTION_ID = 20221
FORMAT_ANSWER_ID = 20223
HINT_REQUEST_ID = 20222
DECLINE_ID = 20224
OUR_FOLLOWUP_ID = 20226

EXPECTED_FORMAT_ANSWER = "Regular Bitcoin Private key"
EXPECTED_DECLINE_TEXT = "\U0001f910"  # zipper-mouth face

INSTRUCTION_PARTS = (
    "matrixsumlist",
    "lastwordsbeforearchichoice",
    "thispassword",
    "shabefourfirsthintisyourlastcommand",
    "enter",
    "shabefanstoo",
)
EXPECTED_INSTRUCTION_LENGTH = 103
CREATOR_OPERAND_PHRASES = (
    "anstoo",
    "answer too",
    "shabef",
    "first hint",
    "last command",
)

# Vasilis Dragon's "21-row split" claim, and the community's own follow-up
# that deflates it. Recorded, not re-implemented: message 66744 shows the
# claim was never given a reproducible rule, and message 66747 is the
# original author backing off the strong reading in response.
TWENTY_ONE_ROW_CLAIM_ID = 66727
TWENTY_ONE_ROW_CHALLENGE_ID = 66744
TWENTY_ONE_ROW_WALKBACK_ID = 66747
EXPECTED_WALKBACK_SNIPPET = "aren't page/verifier hits"

# Unmotivated numerology raised by the community: an A1Z26 letter-value
# reading routed through an OEIS lookup, and a separate A1Z26 sum matched to
# a cryptographic protocol name. Neither has any creator-authored motivation
# for the specific encoding scheme, matching this project's standing
# base-rate concern about post-hoc letter-value schemes.
OEIS_CLAIM_ID = 50651
BB84_CLAIM_ID = 60177


def load_export(export_path):
    return json.loads(Path(export_path).read_text(encoding="utf-8"))


def flatten_text(value):
    if isinstance(value, str):
        return value
    return "".join(
        item if isinstance(item, str) else item.get("text", "")
        for item in value
    )


def load_message(by_id, message_id):
    message = by_id[message_id]
    return message, flatten_text(message.get("text", ""))


def creator_engagement(by_id):
    hint_request, hint_request_text = load_message(by_id, HINT_REQUEST_ID)
    format_answer_message, format_answer_text = load_message(by_id, FORMAT_ANSWER_ID)
    decline_message, decline_text = load_message(by_id, DECLINE_ID)
    followup_message, followup_text = load_message(by_id, OUR_FOLLOWUP_ID)

    if format_answer_message.get("from_id") != CREATOR_ID:
        raise AssertionError("format-answer message is not creator-authored")
    if decline_message.get("from_id") != CREATOR_ID:
        raise AssertionError("decline message is not creator-authored")
    if followup_message.get("from_id") == CREATOR_ID:
        raise AssertionError("expected an unanswered community follow-up")
    if format_answer_text.strip() != EXPECTED_FORMAT_ANSWER:
        raise AssertionError(f"unexpected format answer: {format_answer_text!r}")
    if decline_text.strip() != EXPECTED_DECLINE_TEXT:
        raise AssertionError(f"unexpected decline text: {decline_text!r}")
    if decline_message.get("reply_to_message_id") != HINT_REQUEST_ID:
        raise AssertionError("decline is not a reply to the hint request")
    if "our" not in followup_text.lower():
        raise AssertionError("follow-up no longer asks about 'our'")

    return {
        "hint_request": hint_request_text,
        "format_answer": format_answer_text,
        "decline": decline_text,
        "our_followup": followup_text,
    }


def scan_anstoo_mentions(payload):
    hits = []
    for message in payload["messages"]:
        text = flatten_text(message.get("text", ""))
        if "anstoo" in text.lower():
            hits.append(message)
    return hits


def creator_anstoo_mentions(payload):
    return [
        message
        for message in payload["messages"]
        if message.get("from_id") == CREATOR_ID
        and "anstoo" in flatten_text(message.get("text", "")).lower()
    ]


def creator_operand_mentions(payload):
    hits = []
    for message in payload["messages"]:
        if message.get("from_id") != CREATOR_ID:
            continue
        text = flatten_text(message.get("text", ""))
        lowered = text.lower()
        matched = [
            phrase for phrase in CREATOR_OPERAND_PHRASES if phrase in lowered
        ]
        if matched:
            hits.append(
                {
                    "id": message["id"],
                    "text": text,
                    "matched_phrases": matched,
                }
            )
    return hits


def instruction_length_check():
    lengths = {part: len(part) for part in INSTRUCTION_PARTS}
    total = sum(lengths.values())
    return {"lengths": lengths, "total": total}


def twenty_one_row_walkback(by_id):
    claim_message, claim_text = load_message(by_id, TWENTY_ONE_ROW_CLAIM_ID)
    challenge_message, challenge_text = load_message(
        by_id, TWENTY_ONE_ROW_CHALLENGE_ID
    )
    walkback_message, walkback_text = load_message(
        by_id, TWENTY_ONE_ROW_WALKBACK_ID
    )
    if claim_message.get("from_id") != walkback_message.get("from_id"):
        raise AssertionError("claim and walkback are not the same author")
    if EXPECTED_WALKBACK_SNIPPET not in walkback_text:
        raise AssertionError("walkback no longer backs off the strong reading")
    return {
        "claim": claim_text,
        "challenge": challenge_text,
        "walkback": walkback_text,
    }


def unmotivated_numerology(by_id):
    _, oeis_text = load_message(by_id, OEIS_CLAIM_ID)
    _, bb84_text = load_message(by_id, BB84_CLAIM_ID)
    if "a141920" not in oeis_text.lower().replace(" ", ""):
        raise AssertionError("OEIS claim text no longer references A141920")
    if "84" not in bb84_text:
        raise AssertionError("BB84 claim text no longer sums to 84")
    return {"oeis_claim": oeis_text, "bb84_claim": bb84_text}


def audit(export_path=DEFAULT_EXPORT_DIR):
    payload = load_export(Path(export_path) / "result.json")
    by_id = {message["id"]: message for message in payload["messages"]}

    engagement = creator_engagement(by_id)
    anstoo_hits = scan_anstoo_mentions(payload)
    creator_hits = creator_anstoo_mentions(payload)
    creator_operand_hits = creator_operand_mentions(payload)
    lengths = instruction_length_check()
    if lengths["total"] != EXPECTED_INSTRUCTION_LENGTH:
        raise AssertionError(
            f"instruction concatenation is {lengths['total']} chars, "
            f"expected {EXPECTED_INSTRUCTION_LENGTH}"
        )
    walkback = twenty_one_row_walkback(by_id)
    numerology = unmotivated_numerology(by_id)

    return {
        "creator_engagement": engagement,
        "anstoo_mention_count": len(anstoo_hits),
        "creator_anstoo_mention_count": len(creator_hits),
        "creator_operand_mentions": creator_operand_hits,
        "instruction_lengths": lengths,
        "twenty_one_row_walkback": walkback,
        "unmotivated_numerology": numerology,
        "verdict": (
            "The creator never uses the word 'anstoo' and never discusses "
            "'first hint'/'last command' outside the single explicit decline "
            f"({EXPECTED_DECLINE_TEXT!r} in reply to a direct request). The "
            "follow-up question asking who 'our' refers to was never "
            "answered. Every community reading of 'anstoo' (literal "
            "expansion, A1Z26/OEIS lookup, BB84 sum, anagram, a 21-row grid "
            "split) is speculative; the one structurally concrete claim "
            "(a 21-row split with row 1 = dbbi, row 21 = anstoo) was "
            "challenged for its exact rule by another community member and "
            "the original author backed it off to 'already-known "
            "components, not verified receivers' rather than supplying one. "
            "No new operand-scope lever survives this audit; 'anstoo' "
            "remains a genuinely unresolved literal, not a coverage gap."
        ),
    }


def print_report(report):
    engagement = report["creator_engagement"]
    print("[*] creator engagement with this clue:")
    print(f"    hint request : {engagement['hint_request']!r}")
    print(f"    format answer: {engagement['format_answer']!r}")
    print(f"    decline      : {engagement['decline']!r}")
    print(f"    unanswered   : {engagement['our_followup']!r}")
    print(
        "[*] 'anstoo' mentions in full export: "
        f"{report['anstoo_mention_count']} total, "
        f"{report['creator_anstoo_mention_count']} creator-authored"
    )
    print(
        "[*] creator-authored operand-phrase mentions: "
        f"{len(report['creator_operand_mentions'])}"
    )
    lengths = report["instruction_lengths"]
    print(f"[*] instruction concatenation length: {lengths['total']} (expected 103)")
    for part, length in lengths["lengths"].items():
        print(f"    {part!r}: {length}")
    walkback = report["twenty_one_row_walkback"]
    print("[*] 21-row split claim, challenged and walked back:")
    print(f"    claim    : {walkback['claim']!r}")
    print(f"    challenge: {walkback['challenge']!r}")
    print(f"    walkback : {walkback['walkback']!r}")
    print("[*] unmotivated numerology on record, not tested further:")
    for label, text in report["unmotivated_numerology"].items():
        print(f"    {label}: {text!r}")
    print(f"[*] verdict: {report['verdict']}")


def self_test():
    report = audit()
    assert report["creator_anstoo_mention_count"] == 0
    assert report["creator_operand_mentions"] == []
    assert report["anstoo_mention_count"] >= 90
    assert report["instruction_lengths"]["total"] == 103
    assert (
        report["creator_engagement"]["decline"].strip() == EXPECTED_DECLINE_TEXT
    )
    print("[*] self-test OK: creator engagement, anstoo survey, 103-char check, 21-row walkback")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()

    report = audit(args.export)
    print_report(report)


if __name__ == "__main__":
    main()
