#!/usr/bin/env python3
"""Verify creator claims that constrain the remaining GSMG search.

This audit separates exact first-party constraints from stronger community
paraphrases about brute force and construction time.  It does not execute a
cipher oracle or infer an algorithm from feasibility language.
"""

import argparse
import json
import re
from pathlib import Path

from salphaseion_title_rebus_audit import EXPECTED_MACRO, load_macro
from telegram_export_manifest import DEFAULT_EXPORT_DIR, load_export, plain_text


CREATOR_ID = "user9815232"
REQUIRED = {
    5717: "a few might not require the internet anymore",
    9605: "another URL to find?",
    9607: "No need. You have all the info.",
    9639: "you'll need the internet to claim the prize",
    16624: '"Given the available knowledge, is internet still required to solve it?"',
    32579: "1 microstep further",
    60309: "Looks at gnomad",
    60310: "its in front of your eyes but you're not seeing it",
    60312: "Bingo",
    66557: "spur of the moment decision",
    66559: "inspired me to make an actual puzzle",
    66561: "A day later I can hardly understand what I have done",
}


def audit(export_dir=DEFAULT_EXPORT_DIR):
    data = load_export(export_dir)
    ordered = data["messages"]
    messages = {message["id"]: message for message in ordered}
    texts = {message["id"]: plain_text(message) for message in ordered}
    for message_id, fragment in REQUIRED.items():
        if fragment not in texts[message_id]:
            raise AssertionError(f"required message {message_id} drifted")
    for message_id in (5717, 9607, 9639, 16624, 32579, 60309, 60312, 66559, 66561):
        if messages[message_id].get("from_id") != CREATOR_ID:
            raise AssertionError(f"message {message_id} is no longer creator-authored")
    if messages[9607].get("reply_to_message_id") != 9605:
        raise AssertionError("no-new-URL reply edge drifted")
    if messages[66559].get("reply_to_message_id") != 66557:
        raise AssertionError("spur-of-moment reply edge drifted")
    if not (60309 < 60310 < 60312):
        raise AssertionError("in-front-of-eyes Bingo sequence drifted")

    creator_rows = [
        (message["id"], texts[message["id"]])
        for message in ordered
        if message.get("from_id") == CREATOR_ID
    ]
    brute_rows = tuple(
        {"message_id": message_id, "text": text}
        for message_id, text in creator_rows
        if re.search(r"\bbrut(?:e|eforce|e-force|ing|ed)", text, re.I)
    )
    duration_pattern = re.compile(
        r"(?:creat(?:e|ed|ing)|built|wrote|made (?:an? |the |this )?(?:actual )?puzzle)"
        r".{0,100}\b(?:hour|day|week)s?\b"
        r"|\b(?:hour|day|week)s?\b.{0,100}"
        r"(?:creat(?:e|ed|ing)|built|wrote|made (?:an? |the |this )?(?:actual )?puzzle)",
        re.I | re.S,
    )
    explicit_duration_rows = tuple(
        {"message_id": message_id, "text": text}
        for message_id, text in creator_rows
        if duration_pattern.search(text)
    )

    macro = load_macro(Path(export_dir) / "result.json")
    if macro != EXPECTED_MACRO or "itsinfrontofyoureyesbutyourenotseeingit" not in macro:
        raise AssertionError("authenticated macro visibility clause drifted")

    return {
        "offline_solvability": {
            "status": "verified",
            "strongest_message": {"message_id": 16624, "text": texts[16624]},
            "claim_only_exception": {"message_id": 9639, "text": texts[9639]},
            "earlier_qualified_message": {"message_id": 5717, "text": texts[5717]},
            "implication": (
                "No new internet lookup is required to derive the solution from "
                "the knowledge already available by 2023; internet may still be "
                "needed to claim or spend the prize."
            ),
        },
        "no_new_url": {
            "status": "verified",
            "question": {"message_id": 9605, "text": texts[9605]},
            "answer": {"message_id": 9607, "text": texts[9607]},
            "reply_edge": True,
        },
        "visible_referent": {
            "status": "phrase_verified_referent_unknown",
            "macro_message_id": 8446,
            "macro_clause": "itsinfrontofyoureyesbutyourenotseeingit",
            "bingo_sequence": (
                {"message_id": 60309, "text": texts[60309]},
                {"message_id": 60310, "text": texts[60310]},
                {"message_id": 60312, "text": texts[60312]},
            ),
            "implication": (
                "A qualifying interpretation should identify already-present "
                "evidence; the exchange does not identify which visible artifact."
            ),
        },
        "moderate_bruteforce": {
            "status": "not_creator_supported",
            "creator_brute_mentions": brute_rows,
            "implication": (
                "Do not use a claimed creator endorsement of moderate brute force "
                "to admit a search family; no such wording occurs in the complete export."
            ),
        },
        "rapid_construction": {
            "status": "qualitative_rushed_frenzy_only",
            "spur_question": {"message_id": 66557, "text": texts[66557]},
            "creator_reply": {"message_id": 66559, "text": texts[66559]},
            "creator_frenzy": {"message_id": 66561, "text": texts[66561]},
            "explicit_creation_duration_rows": explicit_duration_rows,
            "implication": (
                "The creator confirms spur-of-the-moment, rushed/frenzied work, "
                "but never says the puzzle was completed in one or two days. This "
                "supports tolerance for simple mistakes, not a bound on layer count."
            ),
        },
        "near_completion": {
            "status": "verified_conditionally",
            "message": {"message_id": 32579, "text": texts[32579]},
            "implication": (
                "One missing microstep was expected to unlock same-day completion; "
                "that constrains the post-transition tail, not necessarily the "
                "difficulty of recovering the microstep itself."
            ),
        },
        "search_policy": {
            "require": (
                "authenticated/already-present operands",
                "an explicit binding or a rare controlled structural match",
                "offline reproducibility",
            ),
            "reject": (
                "new URL or broad web archaeology",
                "brute force justified only by an attributed creator hint",
                "assuming few layers from an unstated two-day construction time",
            ),
        },
        "verdict": (
            "Two strong constraints are real: the remaining solve is offline from "
            "already-available information, and the in-front-of-your-eyes phrase "
            "matters. The claimed moderate-bruteforce endorsement and precise "
            "one/two-day construction bound are not creator statements."
        ),
    }


def self_test(export_dir=DEFAULT_EXPORT_DIR):
    report = audit(export_dir)
    assert report["offline_solvability"]["status"] == "verified"
    assert report["no_new_url"]["reply_edge"]
    assert report["visible_referent"]["status"] == "phrase_verified_referent_unknown"
    assert report["moderate_bruteforce"]["creator_brute_mentions"] == ()
    assert report["rapid_construction"]["explicit_creation_duration_rows"] == ()
    assert report["near_completion"]["status"] == "verified_conditionally"
    print(json.dumps(report, indent=2))
    print("[*] self-test OK: exact feasibility constraints separated from paraphrases")
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
