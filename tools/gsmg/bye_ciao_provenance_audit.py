#!/usr/bin/env python3
"""Audit whether HYE->BYE has an independently prior bridge to CIAO BELLA O.

This is a provenance/structure audit only.  It verifies the authenticated
Phase 3.2.1 tail, selected historical community messages, and the complete
creator CIAO inventory.  It does not translate a community theory into an
authored operation or run a password/blob oracle.
"""

import argparse
import json
from pathlib import Path

from architect_hye_bye_audit import structural_audit as bye_structural_audit
from data import DBBI, FAED
from telegram_export_manifest import DEFAULT_EXPORT_DIR, load_export, plain_text
from telegram_matrix_sum_passage_audit import audit as matrix_passage_audit


CREATOR_ID = "user9815232"
REQUIRED = {
    4_123: ('final part of the message "you are the ONE CIAO BELLA O"', None),
    10_532: ("Ciao Bella O.", None),
    12_771: ("last 'significant words' are 'ciao bella o'", None),
    13_061: ("Bella ciao = goodbye beautiful", 13_054),
    37_920: ('CIAO BELLA O a "song" oh beautiful', None),
    37_921: ('We said bye to beauty "o" in both dbbi and faed parts', 37_920),
    49_038: ("ciao bella o(have dual meaning too, good bye and hello)", None),
}
EXPECTED_CREATOR_CIAO_IDS = (9_632, 32_773, 66_609)
EXPECTED_CREATOR_CIAO_FRAGMENTS = {
    9_632: "Ciao!",
    32_773: "Ciao!",
    66_609: "HI, ciao and cheers you all",
}


def audit(export_dir=DEFAULT_EXPORT_DIR):
    data = load_export(export_dir)
    messages = {message["id"]: message for message in data["messages"]}
    texts = {message["id"]: plain_text(message) for message in data["messages"]}

    community = []
    for message_id, (fragment, reply_to) in REQUIRED.items():
        message = messages[message_id]
        text = texts[message_id]
        if fragment not in text:
            raise AssertionError(f"community message {message_id} drifted")
        if message.get("from_id") == CREATOR_ID:
            raise AssertionError(f"community message {message_id} became creator-authored")
        if reply_to is not None and message.get("reply_to_message_id") != reply_to:
            raise AssertionError(f"community reply edge {message_id}->{reply_to} drifted")
        community.append(
            {
                "message_id": message_id,
                "date": message.get("date"),
                "from": message.get("from"),
                "reply_to": message.get("reply_to_message_id"),
                "text": text,
            }
        )

    creator_ciao = tuple(
        {
            "message_id": message["id"],
            "date": message.get("date"),
            "text": texts[message["id"]],
        }
        for message in data["messages"]
        if message.get("from_id") == CREATOR_ID
        and "ciao" in texts[message["id"]].lower()
    )
    if tuple(row["message_id"] for row in creator_ciao) != EXPECTED_CREATOR_CIAO_IDS:
        raise AssertionError("complete creator CIAO inventory drifted")
    for row in creator_ciao:
        if EXPECTED_CREATOR_CIAO_FRAGMENTS[row["message_id"]] not in row["text"]:
            raise AssertionError(f"creator CIAO message {row['message_id']} drifted")

    passage = matrix_passage_audit(export_dir=Path(export_dir))
    plaintext = passage["phase_plaintext"]
    tail = "CIAO BELLA O"
    if not plaintext.endswith("HOPE YOURE THE ONE " + tail):
        raise AssertionError("authenticated Phase 3.2.1 tail changed")
    tail_words = tuple(tail.lower().split())

    bye = bye_structural_audit()
    if bye["fixed"]["partial_mirror_finals"] != "bye":
        raise AssertionError("Phase 232 BYE checkpoint changed")

    stream_facts = {
        "dbbi_alphabet": "".join(sorted(set(DBBI))),
        "faed_alphabet": "".join(sorted(set(FAED))),
        "dbbi_contains_o": "o" in DBBI,
        "faed_contains_o": "o" in FAED,
    }
    if stream_facts != {
        "dbbi_alphabet": "abcdefghi",
        "faed_alphabet": "abcdefghi",
        "dbbi_contains_o": False,
        "faed_contains_o": False,
    }:
        raise AssertionError("a-i stream alphabet facts changed")

    gates = {
        "authenticated_visible_tail": True,
        "independent_pre_phase232_community_link": True,
        "creator_selected_ciao_as_yinyang": False,
        "deterministic_bye_to_ciao_operation": False,
        "fixed_downstream_consumer": False,
    }

    return {
        "authenticated_tail": {
            "value": tail,
            "full_ending": "HOPE YOURE THE ONE " + tail,
            "word_order": tail_words,
            "reverse_word_order": tuple(reversed(tail_words)),
            "source": "authenticated solved Phase 3.2.1 plaintext",
        },
        "phase232_checkpoint": {
            "source_rail": bye["fixed"]["finals"],
            "partial_mirror_output": bye["fixed"]["partial_mirror_finals"],
        },
        "community_evidence": tuple(community),
        "independent_prior": {
            "earliest_tail_notice": 4_123,
            "last_significant_words_claim": 12_771,
            "direct_bye_beauty_o_dbbi_faed_reply": 37_921,
            "explicit_hello_goodbye_duality_claim": 49_038,
            "all_predate_phase232": True,
            "all_non_creator": True,
        },
        "creator_ciao_inventory": creator_ciao,
        "creator_ciao_classification": "ordinary_signoffs_not_puzzle_confirmations",
        "stream_facts": stream_facts,
        "gates": gates,
        "oracle_authorized": False,
        "verdict": (
            "HYE->BYE has a genuine historically independent bridge to the "
            "authenticated CIAO BELLA O tail: community solvers discussed the "
            "tail, goodbye/hello duality, and BYE/beauty-O with DBBI/FAED years "
            "before Phase 232. This raises CIAO as a recognition candidate, "
            "but no creator message selects the semantic translation, no "
            "deterministic BYE->CIAO operation is authored, and no consumer is "
            "fixed. Do not promote or run a new oracle."
        ),
    }


def self_test(export_dir=DEFAULT_EXPORT_DIR):
    report = audit(export_dir)
    assert report["authenticated_tail"]["value"] == "CIAO BELLA O"
    assert report["authenticated_tail"]["reverse_word_order"] == (
        "o", "bella", "ciao"
    )
    assert report["phase232_checkpoint"] == {
        "source_rail": "hye",
        "partial_mirror_output": "bye",
    }
    assert tuple(
        row["message_id"] for row in report["creator_ciao_inventory"]
    ) == EXPECTED_CREATOR_CIAO_IDS
    assert report["independent_prior"]["direct_bye_beauty_o_dbbi_faed_reply"] == 37_921
    assert report["gates"]["creator_selected_ciao_as_yinyang"] is False
    assert report["gates"]["fixed_downstream_consumer"] is False
    assert report["oracle_authorized"] is False
    print(json.dumps(report, indent=2))
    print("[*] self-test OK: authenticated tail, historical replies, creator inventory, and failed promotion gates verified")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = self_test(args.export_dir) if args.self_test else audit(args.export_dir)
    if args.json and not args.self_test:
        print(json.dumps(report, indent=2))
    elif not args.self_test:
        print(report["verdict"])


if __name__ == "__main__":
    main()
