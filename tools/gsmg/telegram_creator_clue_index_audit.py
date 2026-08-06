#!/usr/bin/env python3
"""Validate the consolidated Telegram creator clue/confirmation index.

Inclusion is intentionally semantic and bounded:

* explicit hints or accidentally disclosed puzzle facts;
* creator confirmations/refutations of concrete puzzle claims;
* creator praise/progress statements that identify a useful artifact or state;
* explicit caveats showing that a tempting statement is a joke, hedge, or
  non-hint;
* prize/solvability statements relevant to interpreting the final phase.

Ordinary conversation, greetings, moderation, finance chat, and generic
encouragement are excluded.  Every indexed record is tied to Telegram's stable
creator user ID; direct reply relationships are asserted where JSON preserves
them.
"""

import argparse
import json
from collections import Counter
from pathlib import Path

from telegram_export_manifest import DEFAULT_EXPORT_DIR

CREATOR_FROM_ID = "user9815232"
CLOSE_FRIENDS_QUESTION_ID = 66874
CLOSE_FRIENDS_HINT_ID = 66574
DEFAULT_INDEX_DOC = (
    Path(__file__).resolve().parents[2]
    / "doc"
    / "GSMG_CREATOR_CLUE_AND_CONFIRMATION_INDEX.md"
)

# id: (category, required text fragment)
INDEX = {
    866: ("historical_correction", "mistake in phase III"),
    867: ("historical_correction", "giveit = givetit"),
    879: ("praise_progress", "unbelievable amount of progress"),
    881: ("prize_meta", "final hint"),
    1710: ("operational_hint", "Yellow has a number and so does Blue"),
    1806: ("negative_caveat", "No clues to be found in those typos"),
    3338: ("praise_progress", "one team managed to find something"),
    3391: ("negative_caveat", "not a hint btw"),
    4094: ("confirmation", "It is"),
    4096: ("confirmation", "This one"),
    4102: ("operational_hint", "answer is there"),
    4105: ("operational_hint", "First or zero"),
    4590: ("operational_hint", "extra door"),
    4688: ("praise_progress", "hints stating the path pretty obvious"),
    4694: ("praise_progress", "stuck in the next phase"),
    4696: ("confirmation", "Correct"),
    5966: ("operational_hint", "prime part"),
    5969: ("operational_hint", "might have been a hint"),
    6497: ("recognition_hint", "feeling of the phase's name"),
    6509: ("operational_hint", "unforseen hint already"),
    6884: ("operational_hint", "{1 },{4} ,{21}"),
    6913: ("operational_hint", "R=18"),
    7418: ("confirmation", "Good point"),
    7529: ("negative_caveat", "first of april"),
    7914: ("operational_hint", "Another"),
    8000: ("operational_hint", "zeroed out"),
    8048: ("operational_hint", "expiry date of neo's passport"),
    8311: ("praise_progress", "very specific"),
    8315: ("praise_progress", "scary specific"),
    8328: ("confirmation", "provided a very specific hint already"),
    8330: ("operational_hint", "prime number is very important"),
    8352: ("praise_progress", "really getting close"),
    8354: ("operational_hint", "theory of everything"),
    8360: ("prize_meta", "remaining 2.5 btc"),
    8385: ("low_priority_meta", "42"),
    8483: ("confirmation", "👆"),
    8516: ("operational_hint", "expiration date of his passport"),
    8795: ("praise_progress", "really really far"),
    8796: ("praise_progress", "hardest part is done"),
    9599: ("recognition_hint", 'hit a "ying yang"'),
    9603: ("recognition_hint", "Both?"),
    9607: ("confirmation", "You have all the info"),
    9615: ("praise_progress", "My hat off to you"),
    9621: ("prize_meta", "high likely no hints anymore"),
    9627: ("praise_progress", "Something was solved"),
    9639: ("confirmation", "need the internet to claim the prize"),
    12653: ("negative_caveat", "Correct"),
    20223: ("confirmation", "Regular Bitcoin Private key"),
    20224: ("negative_caveat", "🤐"),
    23151: ("negative_caveat", "Technically yes but Nope"),
    32579: ("recognition_hint", "1 microstep further"),
    39224: ("recognition_hint", "yingyang is reached, 2 hours max"),
    39237: ("confirmation", "It’s the next phase"),
    60306: ("negative_caveat", "Maybe"),
    60309: ("operational_hint", "Looks at gnomad"),
    60312: ("confirmation", "Bingo"),
    60314: ("prize_meta", "price is taken in no-time"),
    60326: ("negative_caveat", "Nope"),
    63957: ("prize_meta", "puzzle is still valid"),
    66568: ("prize_meta", "hidden laptop"),
    66571: ("operational_hint", "Some of you, can find me"),
    66573: ("operational_hint", "close friends have the best chance"),
    66574: ("operational_hint", "that is a hint"),
    66584: ("prize_meta", 'original puzzle) is "gone"'),
    66586: ("negative_caveat", "Nope"),
    66588: ("confirmation", "Yes"),
    66589: ("prize_meta", "all still solvable"),
    66592: ("prize_meta", "secret in my head"),
    66593: ("prize_meta", "never the actual prize"),
    66595: ("prize_meta", "btc is still available"),
    66600: ("prize_meta", "Some already found it"),
    1487: ("operational_hint", "piece be found outside the main puzzle"),
    2910: ("negative_caveat", "too much of a hint"),
    2918: ("operational_hint", "something hidden in there"),
    4624: ("confirmation", "a private key"),
    7998: ("operational_hint", "mini mini hint"),
    8446: ("operational_hint", "00100110 10100110"),
    32535: ("prize_meta", "puzzle not solved"),
    32671: ("negative_caveat", "last number of pi"),
    53342: ("operational_hint", "01001000 01100001"),
}

EXPECTED_REPLY_TO = {
    4094: 4076,
    4096: 1710,
    6497: 6496,
    6509: 6508,
    7418: 7416,
    7529: 7528,
    7914: 7913,
    8048: 8045,
    8311: 8310,
    8483: 8448,
    8516: 8515,
    8795: 8791,
    9607: 9605,
    9615: 9609,
    9621: 9616,
    12653: 12580,
    20223: 20221,
    20224: 20222,
    23151: 23148,
    39237: 39233,
    60309: 60308,
    60326: 60323,
    63957: 63942,
    66600: 66599,
    2910: 2906,
    2918: 2911,
    32671: 32666,
}

EXPECTED_CATEGORY_COUNTS = {
    "confirmation": 13,
    "historical_correction": 2,
    "low_priority_meta": 1,
    "negative_caveat": 11,
    "operational_hint": 24,
    "praise_progress": 11,
    "prize_meta": 13,
    "recognition_hint": 5,
}


def flatten_text(value):
    if isinstance(value, str):
        return value
    if not isinstance(value, list):
        return ""
    return "".join(
        item if isinstance(item, str) else item.get("text", "")
        for item in value
    )


def load_messages(export_dir):
    payload = json.loads(
        (Path(export_dir) / "result.json").read_text(encoding="utf-8")
    )
    return payload, {message["id"]: message for message in payload["messages"]}


def audit(export_dir=DEFAULT_EXPORT_DIR):
    payload, messages = load_messages(export_dir)
    records = []
    for message_id, (category, fragment) in INDEX.items():
        message = messages[message_id]
        text = flatten_text(message.get("text", ""))
        if message.get("from_id") != CREATOR_FROM_ID:
            raise AssertionError(f"message {message_id} is not creator-authored")
        if fragment not in text:
            raise AssertionError(
                f"message {message_id} no longer contains {fragment!r}"
            )
        expected_reply = EXPECTED_REPLY_TO.get(message_id)
        if expected_reply is not None:
            actual_reply = message.get("reply_to_message_id")
            if actual_reply != expected_reply:
                raise AssertionError(
                    f"message {message_id} replies to {actual_reply}, "
                    f"expected {expected_reply}"
                )
        parent = messages.get(
            message.get("reply_to_message_id") or expected_reply
        )
        records.append(
            {
                "id": message_id,
                "date": message["date"],
                "category": category,
                "text": text,
                "reply_to": message.get("reply_to_message_id"),
                "parent_from": parent.get("from") if parent else None,
                "parent_text": flatten_text(parent.get("text", "")) if parent else "",
            }
        )

    all_creator = tuple(
        message
        for message in payload["messages"]
        if message.get("from_id") == CREATOR_FROM_ID
    )
    classification_question = messages[CLOSE_FRIENDS_QUESTION_ID]
    question_text = flatten_text(classification_question.get("text", ""))
    if classification_question.get("reply_to_message_id") != CLOSE_FRIENDS_HINT_ID:
        raise AssertionError("close-friends classification question changed parent")
    if "specific public puzzle artifact" not in question_text:
        raise AssertionError("close-friends classification question text changed")
    direct_question_replies = tuple(
        message
        for message in payload["messages"]
        if message.get("reply_to_message_id") == CLOSE_FRIENDS_QUESTION_ID
    )
    later_creator = tuple(
        message
        for message in all_creator
        if message["id"] > CLOSE_FRIENDS_QUESTION_ID
    )
    category_counts = Counter(record["category"] for record in records)
    return {
        "group_name": payload["name"],
        "creator_total_messages": len(all_creator),
        "creator_text_messages": sum(
            bool(flatten_text(message.get("text", "")).strip())
            for message in all_creator
        ),
        "creator_reply_messages": sum(
            "reply_to_message_id" in message for message in all_creator
        ),
        "creator_text_reply_messages": sum(
            "reply_to_message_id" in message
            and bool(flatten_text(message.get("text", "")).strip())
            for message in all_creator
        ),
        "indexed_records": tuple(records),
        "category_counts": dict(sorted(category_counts.items())),
        "close_friends_followup": {
            "question_id": CLOSE_FRIENDS_QUESTION_ID,
            "direct_reply_ids": tuple(
                message["id"] for message in direct_question_replies
            ),
            "creator_direct_reply_ids": tuple(
                message["id"]
                for message in direct_question_replies
                if message.get("from_id") == CREATOR_FROM_ID
            ),
            "later_creator_message_ids": tuple(
                message["id"] for message in later_creator
            ),
            "export_last_message_id": payload["messages"][-1]["id"],
        },
    }


def self_test(export_dir=DEFAULT_EXPORT_DIR, index_doc=DEFAULT_INDEX_DOC):
    report = audit(export_dir)
    assert report["group_name"] == "GSMG Puzzle Solvers"
    assert report["creator_total_messages"] == 482
    assert report["creator_text_messages"] == 466
    assert report["creator_reply_messages"] == 148
    assert report["creator_text_reply_messages"] == 145
    assert len(report["indexed_records"]) == len(INDEX) == 80
    assert report["category_counts"] == EXPECTED_CATEGORY_COUNTS
    followup = report["close_friends_followup"]
    assert followup["direct_reply_ids"] == (66875,)
    assert followup["creator_direct_reply_ids"] == ()
    assert len(followup["later_creator_message_ids"]) == 24
    assert followup["later_creator_message_ids"][0] == 66884
    assert followup["later_creator_message_ids"][-1] == 66976
    assert followup["export_last_message_id"] == 67267
    document = Path(index_doc).read_text(encoding="utf-8")
    missing_ids = tuple(
        message_id
        for message_id in INDEX
        if f"`{message_id}`" not in document
    )
    assert not missing_ids, f"index document omits message IDs: {missing_ids}"
    print(
        "[*] self-test OK: 80 clue/confirmation/progress/caveat/meta records, "
        "stable creator identity, text fragments, 27 direct reply edges, and "
        "document coverage verified; message 66874's classification question "
        "has no creator reply through export end"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--index-doc", type=Path, default=DEFAULT_INDEX_DOC)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    report = audit(args.export_dir)
    print(
        f"[*] creator messages: total={report['creator_total_messages']} "
        f"text={report['creator_text_messages']} "
        f"replies={report['creator_reply_messages']} "
        f"text_replies={report['creator_text_reply_messages']}"
    )
    print(f"[*] indexed categories: {report['category_counts']}")
    for record in report["indexed_records"]:
        print(
            f"    {record['id']} {record['date']} {record['category']} "
            f"reply={record['reply_to']} {record['text']!r}"
        )
    if args.self_test:
        self_test(args.export_dir, args.index_doc)


if __name__ == "__main__":
    main()
