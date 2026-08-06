#!/usr/bin/env python3
"""Audit the Telegram evidence immediately surrounding the recovered guide.

This is deliberately message-ID scoped.  It does not keyword-mine the full
export or inspect unrelated media.  It verifies the guide's direct challenge,
the admitted prime-fitting choice, the contemporary FEFE/hidden-box
speculation, Denis Golovkin's later "One"/"Two" artifact pairing, and the exact
creator chronology around the 2026 guide/extraction reveal.
"""

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

from telegram_export_manifest import DEFAULT_EXPORT_DIR

GUIDE_ID = 39937
SEGMENTATION_CHALLENGE_ID = 39987
SEGMENTATION_ANSWER_ID = 39989
FAED_QUESTION_ID = 39940
FAED_ANSWER_ID = 39941
NO_PROGRESS_ID = 39944
HIDDEN_BOX_ID = 40048
GUIDE_LABEL_ONE_ID = 60886
MASK_IMAGE_ID = 54430
MASK_LABEL_TWO_ID = 60887
CREATOR_UNRELATED_REPLY_ID = 60326
CREATOR_GOODBYE_ID = 60327
GUIDE_CAPTION_ID = 60325
EXTRACTION_ID = 60333
NARRATED_CHAIN_ID = 60352

MASK_PHOTO = "photos/photo_1872@04-01-2026_10-00-07.jpg"
MASK_PHOTO_SHA256 = (
    "efdf08b8268f883eafb136a5a37a9e04d236374ebcf95900f71b99d0c1172671"
)
SELECTED = "ncsyangcahiriasogaleafayanestve"


def flatten_text(value):
    if isinstance(value, str):
        return value
    return "".join(
        item if isinstance(item, str) else item.get("text", "")
        for item in value
    )


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_messages(export_dir):
    payload = json.loads((export_dir / "result.json").read_text(encoding="utf-8"))
    return payload, {message["id"]: message for message in payload["messages"]}


def text(messages, message_id):
    return flatten_text(messages[message_id].get("text", ""))


def reply_pair(messages, child_id, parent_id):
    if messages[child_id].get("reply_to_message_id") != parent_id:
        raise AssertionError(f"message {child_id} does not reply to {parent_id}")
    return text(messages, parent_id), text(messages, child_id)


def parse_date(message):
    return datetime.fromisoformat(message["date"])


def audit(export_dir=DEFAULT_EXPORT_DIR):
    payload, messages = load_messages(export_dir)

    challenge, answer = reply_pair(
        messages,
        SEGMENTATION_ANSWER_ID,
        SEGMENTATION_CHALLENGE_ID,
    )
    faed_question, faed_answer = reply_pair(messages, FAED_ANSWER_ID, FAED_QUESTION_ID)
    guide_parent, guide_label = reply_pair(messages, GUIDE_LABEL_ONE_ID, GUIDE_ID)
    mask_parent, mask_label = reply_pair(messages, MASK_LABEL_TWO_ID, MASK_IMAGE_ID)

    guide_caption = messages[GUIDE_CAPTION_ID]
    creator_unrelated = messages[CREATOR_UNRELATED_REPLY_ID]
    creator_goodbye = messages[CREATOR_GOODBYE_ID]
    extraction = messages[EXTRACTION_ID]
    chronology = (
        parse_date(guide_caption),
        parse_date(creator_unrelated),
        parse_date(creator_goodbye),
        parse_date(extraction),
    )
    if chronology != tuple(sorted(chronology)):
        raise AssertionError("creator/guide chronology is not ordered as expected")
    if creator_unrelated.get("reply_to_message_id") in (
        GUIDE_ID,
        GUIDE_CAPTION_ID,
        EXTRACTION_ID,
    ):
        raise AssertionError("creator's intervening reply unexpectedly targets the guide")

    narrated_delay = int(
        (parse_date(messages[NARRATED_CHAIN_ID]) - parse_date(extraction)).total_seconds()
    )
    selected_literal_hits = {
        word: word in SELECTED
        for word in ("yin", "ying", "yang", "salvation", "everything")
    }
    mask_path = export_dir / MASK_PHOTO

    report = {
        "group_name": payload["name"],
        "message_count": len(payload["messages"]),
        "segmentation_challenge": challenge,
        "segmentation_answer": answer,
        "faed_question": faed_question,
        "faed_answer": faed_answer,
        "no_progress": text(messages, NO_PROGRESS_ID),
        "hidden_box": text(messages, HIDDEN_BOX_ID),
        "guide_label": guide_label,
        "mask_label": mask_label,
        "mask_photo": messages[MASK_IMAGE_ID]["photo"],
        "mask_photo_sha256": sha256(mask_path),
        "creator_chronology": tuple(
            {
                "id": message_id,
                "date": messages[message_id]["date"],
                "from": messages[message_id].get("from"),
                "reply_to": messages[message_id].get("reply_to_message_id"),
                "text": text(messages, message_id),
            }
            for message_id in (
                GUIDE_CAPTION_ID,
                CREATOR_UNRELATED_REPLY_ID,
                CREATOR_GOODBYE_ID,
                EXTRACTION_ID,
            )
        ),
        "narrated_chain_delay_seconds": narrated_delay,
        "selected_literal_hits": selected_literal_hits,
    }

    if "just to match the pattern" not in challenge:
        raise AssertionError("segmentation challenge text changed")
    if answer != "To match all prime positions":
        raise AssertionError(f"unexpected segmentation answer: {answer!r}")
    if "don't have such pattern" not in faed_answer:
        raise AssertionError(f"unexpected FAED answer: {faed_answer!r}")
    if "nothing more" not in report["no_progress"]:
        raise AssertionError("guide author no-progress statement changed")
    if "hidden box" not in report["hidden_box"]:
        raise AssertionError("hidden-box message changed")
    if guide_label != "One" or mask_label != "Two":
        raise AssertionError(f"unexpected artifact labels: {guide_label!r}/{mask_label!r}")
    if report["mask_photo"] != MASK_PHOTO:
        raise AssertionError(f"unexpected mask image: {report['mask_photo']!r}")
    if report["mask_photo_sha256"] != MASK_PHOTO_SHA256:
        raise AssertionError(f"mask image hash mismatch: {report['mask_photo_sha256']}")
    if narrated_delay != 1104:
        raise AssertionError(f"unexpected narrated-chain delay: {narrated_delay}")
    if selected_literal_hits != {
        "yin": False,
        "ying": False,
        "yang": True,
        "salvation": False,
        "everything": False,
    }:
        raise AssertionError(f"literal-hit classification changed: {selected_literal_hits}")
    return report


def self_test():
    assert flatten_text(["a", {"type": "bold", "text": "b"}]) == "ab"
    report = audit()
    assert report["guide_label"] == "One"
    assert report["mask_label"] == "Two"
    print(
        "[*] self-test OK: direct reply evidence, fitted segmentation, "
        "One/Two media pairing, creator chronology, and literal-hit "
        "classification all verified"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    report = audit(args.export_dir)
    print(
        "[*] segmentation challenge/answer:",
        repr(report["segmentation_challenge"]),
        "->",
        repr(report["segmentation_answer"]),
    )
    print("[*] FAED response:", repr(report["faed_answer"]))
    print("[*] guide-author outcome:", repr(report["no_progress"]))
    print("[*] contemporaneous FEFE speculation:", repr(report["hidden_box"]))
    print(
        f"[*] later artifact pairing: guide={report['guide_label']!r}, "
        f"mask={report['mask_label']!r}"
    )
    print(
        f"[*] mask media: {report['mask_photo']} "
        f"sha256={report['mask_photo_sha256']}"
    )
    print("[*] creator chronology:")
    for record in report["creator_chronology"]:
        print(
            f"    {record['id']} {record['date']} {record['from']!r} "
            f"reply={record['reply_to']} {record['text']!r}"
        )
    print(
        f"[*] narrated chain follows extraction by "
        f"{report['narrated_chain_delay_seconds']} seconds"
    )
    print(f"[*] selected literal hits: {report['selected_literal_hits']}")
    print(
        "[*] verdict: the guide and exact mask were later paired by Denis, "
        "but the guide segmentation was explicitly fitted to prime positions; "
        "FEFE was noticed without an operation, and the creator supplied no "
        "confirmation of the guide, extraction, or downstream transform."
    )
    if args.self_test:
        self_test()


if __name__ == "__main__":
    main()
