#!/usr/bin/env python3
"""Phase 366: chronology audit for the confirmed "in front of your eyes" clue.

This is an evidence-selection audit, not a decoder or password oracle.  It
pins the complete Telegram export, reconstructs the exact 2026 exchange, and
tests only referents that were already public when the creator wrote "Bingo".
The purpose is to prevent a later community reveal from being treated as if
the creator had confirmed it earlier.
"""

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

from salphaseion_title_rebus_audit import EXPECTED_MACRO, load_macro
from telegram_export_manifest import DEFAULT_EXPORT_DIR, plain_text


CREATOR_ID = "user9815232"
EXPORT = DEFAULT_EXPORT_DIR / "result.json"
EXPECTED_EXPORT_SHA256 = (
    "09fa513506ded392d56894424f6e019297781d8d669c27c3c0e9f62f3a31a084"
)

REQUIRED = {
    1710: "Yellow has a number and so does Blue",
    5966: "prime part already",
    6884: "another door might be found on {1 },{4} ,{21}",
    8000: "zeroed out",
    8330: "prime number is very important",
    8446: "00100110 10100110",
    9599: 'Once you hit a "ying yang"',
    32579: "1 microstep further",
    39237: "next phase",
    39937: "What are your thoughts on this approach?",
    60304: "in front of your eyes",
    60306: "Maybe, Cartman's quote",
    60309: "Looks at gnomad",
    60310: "in front of your eyes",
    60312: "Bingo",
    60313: "specific prime inexes",
    60314: "reaches the next phase",
    60325: "guide to yellow-blue-primes",
    60333: "ncsyangcahiriasogaleafayanestve",
    60352: "yellow blue primes matrix sum list",
}

CREATOR_MESSAGES = {
    1710, 5966, 6884, 8000, 8330, 8446, 9599, 32579, 39237,
    60306, 60309, 60312, 60314,
}


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def parse_time(value):
    return datetime.fromisoformat(value)


def load_messages(export_path=EXPORT):
    export_path = Path(export_path)
    if sha256_file(export_path) != EXPECTED_EXPORT_SHA256:
        raise AssertionError("Telegram export SHA-256 drifted")
    data = json.loads(export_path.read_text(encoding="utf-8"))
    messages = {message["id"]: message for message in data["messages"]}
    texts = {message_id: plain_text(message) for message_id, message in messages.items()}
    for message_id, fragment in REQUIRED.items():
        if fragment.lower() not in texts[message_id].lower():
            raise AssertionError(f"required message {message_id} drifted")
    for message_id in CREATOR_MESSAGES:
        if messages[message_id].get("from_id") != CREATOR_ID:
            raise AssertionError(f"message {message_id} lost creator provenance")
    return messages, texts


def candidate_rows(bingo_time):
    """Frozen referent inventory; no output-dependent additions are allowed."""
    rows = (
        {
            "candidate": "first_piece_rabbit_grid",
            "public_by": "2019-04-20",
            "provenance": "creator artifact",
            "published_by_bingo": True,
            "direct_eyes_binding": False,
            "boundary_adjacent": False,
            "fixed_operation": True,
            "independent_output": True,
            "note": "Prime/door/zero clues bind this artifact, but the eyes phrase does not; its reconstructed role ends at the selector/checkpoint.",
        },
        {
            "candidate": "salphaseion_dbbi_faed_page",
            "public_by": "2021-05-07",
            "provenance": "creator page, community-documented route",
            "published_by_bingo": True,
            "direct_eyes_binding": False,
            "boundary_adjacent": True,
            "fixed_operation": False,
            "independent_output": False,
            "note": "The page is the nearest visible unresolved object, but neither the eyes exchange nor page syntax binds DBBI to FAED or names a consumer.",
        },
        {
            "candidate": "cosmic_duality_book",
            "public_by": "2022-12-11",
            "provenance": "community discovery, exact cover creator-validated",
            "published_by_bingo": True,
            "direct_eyes_binding": False,
            "boundary_adjacent": False,
            "fixed_operation": False,
            "independent_output": False,
            "note": "A validated thematic clue, but not the object named in Denis's Looking Forward question and no page supplies the missing operation.",
        },
        {
            "candidate": "creator_binary_macro_itself",
            "public_by": "2023-02-24",
            "provenance": "creator message 8446",
            "published_by_bingo": True,
            "direct_eyes_binding": True,
            "boundary_adjacent": False,
            "fixed_operation": False,
            "independent_output": False,
            "note": "It contains the exact phrase, but this is self-reference rather than a pointed-to operand; literal macro order places the clause after yinyang.",
        },
        {
            "candidate": "looking_forward_book",
            "public_by": "2026-03-04T03:22:29",
            "provenance": "community proposal in message 60304",
            "published_by_bingo": True,
            "direct_eyes_binding": False,
            "boundary_adjacent": False,
            "fixed_operation": False,
            "independent_output": False,
            "note": "The creator answered Maybe and offered another fitting joke; Bingo later confirms only the repeated phrase.",
        },
        {
            "candidate": "historical_guide_image_39937",
            "public_by": "2025-05-01",
            "provenance": "community artifact",
            "published_by_bingo": True,
            "direct_eyes_binding": False,
            "boundary_adjacent": True,
            "fixed_operation": True,
            "independent_output": False,
            "note": "Public before Bingo, but the creator never replies to it; its b/be segmentation was admitted to be fitted to prime positions.",
        },
        {
            "candidate": "selected_mask_image_54430",
            "public_by": "2026-01-04",
            "provenance": "community artifact",
            "published_by_bingo": True,
            "direct_eyes_binding": False,
            "boundary_adjacent": True,
            "fixed_operation": True,
            "independent_output": False,
            "note": "The mask image predates Bingo, but no reply edge or creator text identifies it as the phrase's referent.",
        },
        {
            "candidate": "exact_31_character_text",
            "public_by": "2026-03-04T03:39:06",
            "provenance": "community message 60333",
            "published_by_bingo": False,
            "direct_eyes_binding": False,
            "boundary_adjacent": True,
            "fixed_operation": False,
            "independent_output": False,
            "note": "The exact text was posted 10 minutes 1 second after Bingo and therefore cannot be what that earlier response authenticated.",
        },
    )
    gate_names = (
        "published_by_bingo",
        "direct_eyes_binding",
        "boundary_adjacent",
        "fixed_operation",
        "independent_output",
    )
    result = []
    for row in rows:
        checked = dict(row)
        checked["qualifies"] = all(checked[gate] for gate in gate_names)
        result.append(checked)
    if any(row["qualifies"] for row in result):
        raise AssertionError("a frozen referent unexpectedly passed every gate")
    return tuple(result)


def audit(export_path=EXPORT):
    messages, texts = load_messages(export_path)
    times = {message_id: parse_time(messages[message_id]["date"]) for message_id in REQUIRED}

    # The exact reply metadata matters more than conversational proximity.
    if messages[60309].get("reply_to_message_id") != 60308:
        raise AssertionError("creator direction reply edge drifted")
    if messages[60325].get("reply_to_message_id") != 39937:
        raise AssertionError("recovered-guide reply edge drifted")
    if messages[60333].get("reply_to_message_id") != 60325:
        raise AssertionError("exact-extraction reply edge drifted")
    if messages[60352].get("reply_to_message_id") != 60333:
        raise AssertionError("chain-narration reply edge drifted")
    if messages[60306].get("reply_to_message_id") is not None:
        raise AssertionError("hedged response unexpectedly gained a direct reply edge")
    if messages[60312].get("reply_to_message_id") is not None:
        raise AssertionError("Bingo unexpectedly gained a direct reply edge")

    ordered_ids = (60304, 60306, 60309, 60310, 60312, 60313, 60314, 60325, 60333, 60352)
    if tuple(sorted(ordered_ids, key=lambda item: times[item])) != ordered_ids:
        raise AssertionError("eyes/extraction chronology drifted")

    macro = load_macro(Path(export_path))
    if macro != EXPECTED_MACRO:
        raise AssertionError("creator macro drifted")
    anchors = {
        token: macro.index(token)
        for token in (
            "yellowblueprimes",
            "matrixsumlist",
            "lastwordsbeforearchichoice",
            "yinyang",
            "wewontgiveawaythepassword",
            "itsinfrontofyoureyesbutyourenotseeingit",
            "verylaststepisatruegiveaway",
            "promised",
        )
    }
    if tuple(anchors.values()) != tuple(sorted(anchors.values())):
        raise AssertionError("macro clause order drifted")

    bingo_time = times[60312]
    abstract_delay = int((times[60313] - bingo_time).total_seconds())
    exact_delay = int((times[60333] - bingo_time).total_seconds())
    narrative_delay = int((times[60352] - bingo_time).total_seconds())
    rows = candidate_rows(bingo_time)

    return {
        "source": {
            "path": str(export_path),
            "sha256": EXPECTED_EXPORT_SHA256,
        },
        "timeline": tuple(
            {
                "message_id": message_id,
                "date": messages[message_id]["date"],
                "sender": messages[message_id].get("from"),
                "reply_to": messages[message_id].get("reply_to_message_id"),
                "text": texts[message_id],
            }
            for message_id in ordered_ids
        ),
        "timing": {
            "bingo_to_abstract_claim_seconds": abstract_delay,
            "bingo_to_exact_text_seconds": exact_delay,
            "bingo_to_chain_narration_seconds": narrative_delay,
        },
        "macro": {
            "length": len(macro),
            "anchors": anchors,
            "eyes_clause_is_after_yinyang": (
                anchors["itsinfrontofyoureyesbutyourenotseeingit"]
                > anchors["yinyang"]
            ),
            "interpretive_limit": (
                "Literal source order makes the visibility clause downstream of "
                "yinyang. This ranks it as a clue about the post-yinyang password, "
                "not as an authenticated operator for reaching yinyang; macro order "
                "alone is not proof that every clause is procedural."
            ),
        },
        "candidate_referents": rows,
        "qualifier_count": sum(row["qualifies"] for row in rows),
        "oracle_authorized": False,
        "verdict": (
            "Bingo authenticates the phrase-level pointer only. It precedes Denis's "
            "abstract extraction claim by 13 seconds, the exact 31-character text by "
            "601 seconds, and the narrated chain by 1705 seconds. No already-public "
            "referent passes the frozen visibility, binding, boundary, operation, and "
            "output gates. The eyes clue therefore does not select a consumer for the "
            "31-character string or a DBBI/FAED operation."
        ),
    }


def self_test(export_path=EXPORT):
    report = audit(export_path)
    assert report["timing"] == {
        "bingo_to_abstract_claim_seconds": 13,
        "bingo_to_exact_text_seconds": 601,
        "bingo_to_chain_narration_seconds": 1705,
    }
    assert report["macro"]["length"] == 161
    assert report["macro"]["eyes_clause_is_after_yinyang"]
    assert len(report["candidate_referents"]) == 8
    assert report["qualifier_count"] == 0
    assert not report["oracle_authorized"]
    exact = next(
        row for row in report["candidate_referents"]
        if row["candidate"] == "exact_31_character_text"
    )
    assert not exact["published_by_bingo"]
    print(json.dumps(report, indent=2))
    print("[*] self-test OK: chronology, reply edges, macro order, and referent gates verified")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", type=Path, default=EXPORT)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = self_test(args.export) if args.self_test else audit(args.export)
    if args.json and not args.self_test:
        print(json.dumps(report, indent=2))
    elif not args.self_test:
        print(report["verdict"])


if __name__ == "__main__":
    main()
