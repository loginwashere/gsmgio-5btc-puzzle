#!/usr/bin/env python3
"""Verify creator claims that constrain the remaining GSMG search.

Phase 230 corrects Phase 226's one-chat scope: both the complete puzzle-solvers
export and the largest complete support-group export are required.  The audit
separates exact first-party constraints from stronger community paraphrases.
It does not execute a cipher oracle or infer an algorithm from feasibility
language.
"""

import argparse
import hashlib
import json
import re
from pathlib import Path

from salphaseion_title_rebus_audit import EXPECTED_MACRO, load_macro
from telegram_export_manifest import DEFAULT_EXPORT_DIR, load_export, plain_text


CREATOR_ID = "user9815232"
SOLVER_RESULT = DEFAULT_EXPORT_DIR / "result.json"
SUPPORT_RESULT = Path(
    "/home/loginwashere/Downloads/Telegram Desktop/"
    "ChatExport_2026-07-29 (2)/result.json"
)
EXPECTED_SOLVER_SHA256 = "09fa513506ded392d56894424f6e019297781d8d669c27c3c0e9f62f3a31a084"
EXPECTED_SUPPORT_SHA256 = "6e616bfe72d81c9d9134c0631781b594d9abf9bc7d2f6de3518f9e75b5dad9fd"
EXPECTED_SUPPORT_NAME = "GSMG - Community & support group"
EXPECTED_SUPPORT_TYPE = "public_supergroup"
EXPECTED_SUPPORT_ID = 1246576180
EXPECTED_SUPPORT_MESSAGES = 52_851
EXPECTED_SUPPORT_CREATOR_MESSAGES = 5_419

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

SUPPORT_REQUIRED = {
    12_697: "icloud didn't notice bruteforce attempts",
    28_699: "alterting between tokens",
    28_701: "making testing stuff on this hard",
    28_702: "how many stages to this?",
    28_703: "against bruteforcing",
    28_704: "You'll have to find out.",
    54_419: "Bruteforced numbers on historic price data",
    67_741: "spent two sloppy days throwing one together",
}

BRUTE_PATTERN = re.compile(r"brut(?:e|eforce|e-force|ing|ed)", re.I)

# Deliberately excludes bare `line`, `form`, and `page`: those words have many
# non-presentation meanings and do not specify responsive geometry.  This is a
# source-vocabulary inventory, not a search for arbitrary layout synonyms.
PRESENTATION_PATTERN = re.compile(
    r"\b(?:screens?|displays?|monitors?|viewports?|resolutions?|widths?|"
    r"resiz\w*|zoom\w*|wrapp?\w*|line[ -]?breaks?|newlines?|rows?|columns?|"
    r"scroll\w*|textareas?|fonts?|monospace|browsers?|windows?|mobile|desktop|"
    r"layouts?|align\w*)\b",
    re.I,
)
EXPECTED_PRESENTATION_IDS = {
    "solver": (1_806, 6_497),
    "support": (
        1_786, 5_790, 7_600, 8_944, 11_201, 13_081, 13_489, 17_849,
        18_023, 21_453, 27_128, 30_345, 32_682, 33_104, 33_141, 36_966,
        37_698, 38_306, 38_992, 41_866, 43_840, 44_990, 49_493, 52_883,
        63_687,
    ),
}


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def creator_rows(data):
    return tuple(
        (message["id"], plain_text(message), message)
        for message in data["messages"]
        if message.get("from_id") == CREATOR_ID
    )


def matching_rows(rows, pattern):
    return tuple(
        {
            "message_id": message_id,
            "text": text,
            "matched_terms": tuple(match.group(0) for match in pattern.finditer(text)),
        }
        for message_id, text, _message in rows
        if pattern.search(text)
    )


def audit(export_dir=DEFAULT_EXPORT_DIR, support_result=SUPPORT_RESULT):
    solver_result = Path(export_dir) / "result.json"
    if sha256_file(solver_result) != EXPECTED_SOLVER_SHA256:
        raise AssertionError("puzzle-solvers export SHA-256 drifted")
    if sha256_file(support_result) != EXPECTED_SUPPORT_SHA256:
        raise AssertionError("support-group export SHA-256 drifted")

    data = load_export(export_dir)
    support_data = load_json(support_result)
    if (
        support_data.get("name") != EXPECTED_SUPPORT_NAME
        or support_data.get("type") != EXPECTED_SUPPORT_TYPE
        or support_data.get("id") != EXPECTED_SUPPORT_ID
        or len(support_data["messages"]) != EXPECTED_SUPPORT_MESSAGES
    ):
        raise AssertionError("support-group export identity/count drifted")
    support_creator_count = sum(
        message.get("from_id") == CREATOR_ID
        for message in support_data["messages"]
    )
    if support_creator_count != EXPECTED_SUPPORT_CREATOR_MESSAGES:
        raise AssertionError("support-group creator-message count drifted")

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

    solver_creator_rows = tuple(
        (message["id"], texts[message["id"]])
        for message in ordered
        if message.get("from_id") == CREATOR_ID
    )
    support_messages = {message["id"]: message for message in support_data["messages"]}
    support_texts = {
        message["id"]: plain_text(message)
        for message in support_data["messages"]
    }
    for message_id, fragment in SUPPORT_REQUIRED.items():
        if fragment not in support_texts[message_id]:
            raise AssertionError(f"support message {message_id} drifted")
    for message_id in (12_697, 28_703, 28_704, 54_419, 67_741):
        if support_messages[message_id].get("from_id") != CREATOR_ID:
            raise AssertionError(f"support message {message_id} is not creator-authored")

    solver_creator_full = creator_rows(data)
    support_creator_full = creator_rows(support_data)
    solver_brute_rows = matching_rows(solver_creator_full, BRUTE_PATTERN)
    support_brute_rows = matching_rows(support_creator_full, BRUTE_PATTERN)
    if tuple(row["message_id"] for row in solver_brute_rows) != ():
        raise AssertionError("unexpected solver-group creator brute-force match")
    if tuple(row["message_id"] for row in support_brute_rows) != (12_697, 28_703, 54_419):
        raise AssertionError("support-group creator brute-force inventory drifted")

    solver_presentation = matching_rows(solver_creator_full, PRESENTATION_PATTERN)
    support_presentation = matching_rows(support_creator_full, PRESENTATION_PATTERN)
    presentation_ids = {
        "solver": tuple(row["message_id"] for row in solver_presentation),
        "support": tuple(row["message_id"] for row in support_presentation),
    }
    if presentation_ids != EXPECTED_PRESENTATION_IDS:
        raise AssertionError("creator presentation-vocabulary inventory drifted")

    duration_pattern = re.compile(
        r"(?:creat(?:e|ed|ing)|built|wrote|made (?:an? |the |this )?(?:actual )?puzzle)"
        r".{0,100}\b(?:hour|day|week)s?\b"
        r"|\b(?:hour|day|week)s?\b.{0,100}"
        r"(?:creat(?:e|ed|ing)|built|wrote|made (?:an? |the |this )?(?:actual )?puzzle)",
        re.I | re.S,
    )
    explicit_duration_rows = tuple(
        {"message_id": message_id, "text": text}
        for message_id, text in solver_creator_rows
        if duration_pattern.search(text)
    )

    retrospective = support_messages[67_741]
    retrospective_text = support_texts[67_741]
    if "Full of grammatical mistakes and zero polish" not in retrospective_text:
        raise AssertionError("construction-quality retrospective drifted")

    # 28703 has no reply metadata.  It immediately follows the token/testing
    # complaint; 28704, not 28703, carries the direct reply edge to 28702.
    if support_messages[28_703].get("reply_to_message_id") is not None:
        raise AssertionError("anti-bruteforce message unexpectedly gained a reply edge")
    if support_messages[28_704].get("reply_to_message_id") != 28_702:
        raise AssertionError("stage-count direct reply edge drifted")

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
            "status": "not_endgame_endorsed",
            "solver_group_mentions": solver_brute_rows,
            "support_group_mentions": support_brute_rows,
            "classification": {
                12_697: "unrelated_icloud_security_anecdote",
                28_703: "puzzle_specific_anti_bruteforce_and_find_hint",
                54_419: "unrelated_trading_backtest",
            },
            "puzzle_thread_context": tuple(
                {"message_id": message_id, "text": support_texts[message_id]}
                for message_id in (28_699, 28_701, 28_702, 28_703, 28_704)
            ),
            "anti_bruteforce_reply_edge": False,
            "stage_count_reply_edge": (28_704, 28_702),
            "implication": (
                "The only puzzle-specific creator use describes protection against "
                "brute force and tells solvers to find the right next hint. It does "
                "not endorse moderate brute force for the unresolved endgame."
            ),
        },
        "rapid_construction": {
            "status": "two_sloppy_days_verified_retrospectively",
            "spur_question": {"message_id": 66557, "text": texts[66557]},
            "creator_reply": {"message_id": 66559, "text": texts[66559]},
            "creator_frenzy": {"message_id": 66561, "text": texts[66561]},
            "solver_group_explicit_creation_duration_rows": explicit_duration_rows,
            "support_group_retrospective": {
                "message_id": 67_741,
                "date": retrospective.get("date"),
                "text": retrospective_text,
                "contemporaneous": False,
            },
            "implication": (
                "A 2026 first-party retrospective says the puzzle was thrown together "
                "in two sloppy days with zero polish. This favors short clue-selected "
                "mechanics and tolerance for mistakes, but does not mechanically bound "
                "the number of layers."
            ),
        },
        "presentation_vocabulary": {
            "pattern": PRESENTATION_PATTERN.pattern,
            "solver_group_matches": solver_presentation,
            "support_group_matches": support_presentation,
            "classification": {
                "solver": {
                    1_806: "typo_disclaimer_display_of_words_not_layout_instruction",
                    6_497: "monitor_progress_as_verb_not_display_instruction",
                },
                "support": "all_twenty_five_are_trading_product_or_device_support_context",
            },
            "puzzle_geometry_instruction_count": 0,
            "implication": (
                "No creator message in either pinned corpus instructs solvers to "
                "resize, wrap, align, or use rows/columns, viewport, font, textarea, "
                "zoom, or screen geometry for the puzzle."
            ),
        },
        "corpus_scope": {
            "solver": {
                "sha256": EXPECTED_SOLVER_SHA256,
                "message_count": len(data["messages"]),
                "group_name": data.get("name"),
                "group_id": data.get("id"),
            },
            "support": {
                "path": str(Path(support_result)),
                "sha256": EXPECTED_SUPPORT_SHA256,
                "message_count": len(support_data["messages"]),
                "creator_message_count": support_creator_count,
                "group_name": support_data.get("name"),
                "group_type": support_data.get("type"),
                "group_id": support_data.get("id"),
            },
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
                "complex formatting theories without a creator-selected parameter",
            ),
        },
        "verdict": (
            "Two strong constraints are real: the remaining solve is offline from "
            "already-available information, and the in-front-of-your-eyes phrase "
            "matters. A 2026 creator retrospective verifies two sloppy construction "
            "days, but no creator statement endorses endgame brute force or selects "
            "responsive screen geometry."
        ),
    }


def self_test(export_dir=DEFAULT_EXPORT_DIR, support_result=SUPPORT_RESULT):
    report = audit(export_dir, support_result)
    assert report["offline_solvability"]["status"] == "verified"
    assert report["no_new_url"]["reply_edge"]
    assert report["visible_referent"]["status"] == "phrase_verified_referent_unknown"
    assert report["moderate_bruteforce"]["status"] == "not_endgame_endorsed"
    assert len(report["moderate_bruteforce"]["support_group_mentions"]) == 3
    assert report["rapid_construction"]["status"] == "two_sloppy_days_verified_retrospectively"
    assert report["presentation_vocabulary"]["puzzle_geometry_instruction_count"] == 0
    assert report["near_completion"]["status"] == "verified_conditionally"
    print(json.dumps(report, indent=2))
    print("[*] self-test OK: exact feasibility constraints separated from paraphrases")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--support-result", type=Path, default=SUPPORT_RESULT)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = (
        self_test(args.export_dir, args.support_result)
        if args.self_test
        else audit(args.export_dir, args.support_result)
    )
    if args.json and not args.self_test:
        print(json.dumps(report, indent=2))
    elif not args.self_test:
        print(report["verdict"])


if __name__ == "__main__":
    main()
