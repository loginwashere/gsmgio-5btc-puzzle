#!/usr/bin/env python3
"""Refresh the primary-evidence record for the ``matrixsumlist`` transition.

This audit deliberately does not try another transform.  It checks whether the
complete Telegram export, the incremental 2026-08-09 export, the recovered
yellow/blue guide, the public walkthrough, a historical community attachment,
or the transcribed Cosmic Duality book supplies a unique operation for the
exact 31-character DBBI selection.
"""

import argparse
import hashlib
import json
import re
from pathlib import Path

from denis_prime_extraction_audit import TARGET as SELECTED_31
from salphaseion_title_rebus_audit import (
    CREATOR_ID,
    EXPECTED_MACRO,
    MACRO_MESSAGE_ID,
    decode_reversed_bitstream,
)
from telegram_export_manifest import DEFAULT_EXPORT_DIR
from telegram_guide_neighborhood_audit import audit as audit_guide_neighborhood
from telegram_matrix_sum_passage_audit import audit as audit_matrix_passage

LATEST_EXPORT_DIR = Path(
    "/home/loginwashere/Downloads/Telegram Desktop/ChatExport_2026-08-09 (1)"
)
HISTORICAL_ATTACHMENT_ID = 33950
HISTORICAL_ATTACHMENT = "files/696783482-puzzle-1.txt"
HISTORICAL_ATTACHMENT_SHA256 = (
    "b6cbab2b55a83e1bbd993c33596b4d732155a8fe9e26c1a922cb8db3de63f0c5"
)
BOOK_GAP_SCREENSHOT = Path(
    "/home/loginwashere/Pictures/Screenshots/"
    "Screenshot from 2026-07-12 14-44-39.png"
)
BOOK_GAP_SCREENSHOT_SHA256 = (
    "19c3ccfd31257d9832884d1d7a1011cf44423e2903c6c51bb5f831a761cbeaa8"
)
EXPECTED_LATEST_RELEVANT_IDS = (67787, 68021, 68057, 68249)
EXPECTED_LATEST_CONTEXT_IDS = (67787, 67789, 68021, 68057, 68249)
MATRIX_RE = re.compile(r"matrix[ _-]*sum[ _-]*list|matrixsumlist", re.I)


def flatten_text(value):
    if isinstance(value, str):
        return value
    if not isinstance(value, list):
        return ""
    return "".join(
        item if isinstance(item, str) else item.get("text", "")
        for item in value
    )


def load_export(export_dir):
    payload = json.loads(
        (Path(export_dir) / "result.json").read_text(encoding="utf-8")
    )
    return payload, {message["id"]: message for message in payload["messages"]}


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def audit(
    full_export_dir=DEFAULT_EXPORT_DIR,
    latest_export_dir=LATEST_EXPORT_DIR,
):
    full_payload, full_messages = load_export(full_export_dir)
    latest_payload, latest_messages = load_export(latest_export_dir)

    creator_macro = full_messages[MACRO_MESSAGE_ID]
    macro_text = flatten_text(creator_macro.get("text", ""))
    decoded_macro = decode_reversed_bitstream(macro_text)
    if creator_macro.get("from_id") != CREATOR_ID:
        raise AssertionError("the macro clue is no longer creator-authored")
    if decoded_macro != EXPECTED_MACRO:
        raise AssertionError("the creator macro decode changed")

    full_matrix_hits = tuple(
        message
        for message in full_payload["messages"]
        if MATRIX_RE.search(flatten_text(message.get("text", "")))
    )
    creator_literal_hits = tuple(
        message["id"]
        for message in full_matrix_hits
        if message.get("from_id") == CREATOR_ID
    )
    creator_selected_hits = tuple(
        message["id"]
        for message in full_payload["messages"]
        if (
            message.get("from_id") == CREATOR_ID
            and SELECTED_31 in flatten_text(message.get("text", ""))
        )
    )

    latest_hits = tuple(
        message
        for message in latest_payload["messages"]
        if MATRIX_RE.search(flatten_text(message.get("text", "")))
    )
    latest_hit_ids = tuple(message["id"] for message in latest_hits)
    latest_creator_hits = tuple(
        message["id"]
        for message in latest_hits
        if message.get("from_id") == CREATOR_ID
    )
    latest_context = tuple(
        latest_messages[message_id]
        for message_id in EXPECTED_LATEST_CONTEXT_IDS
    )

    attachment_message = full_messages[HISTORICAL_ATTACHMENT_ID]
    attachment_path = Path(full_export_dir) / HISTORICAL_ATTACHMENT
    attachment_text = attachment_path.read_text(
        encoding="utf-8", errors="replace"
    )
    attachment_defines_row_plus_column = all(
        fragment in attachment_text
        for fragment in (
            "row_sums = [sum(row) for row in matrix]",
            "col_sums = [sum(col) for col in zip(*matrix)]",
            "matrix_sum_list = row_sums + col_sums",
        )
    )
    attachment_uses_selected_31 = SELECTED_31 in attachment_text

    guide = audit_guide_neighborhood(Path(full_export_dir))
    passage = audit_matrix_passage(export_dir=Path(full_export_dir))
    book_path = (
        Path(__file__).resolve().parents[2]
        / "wordlists/gsmg/cosmic_duality_book_full_text.txt"
    )
    book_text = book_path.read_text(encoding="utf-8", errors="replace")
    book_has_57_58_gap = "## p.56" in book_text and "## p.59" in book_text and not any(
        heading in book_text for heading in ("## p.57", "## p.58", "## p.57-58")
    )

    report = {
        "full_export": {
            "group": full_payload["name"],
            "messages": len(full_payload["messages"]),
            "last_date": full_payload["messages"][-1]["date"],
            "literal_matrixsumlist_hits": len(full_matrix_hits),
        },
        "creator": {
            "macro_message_id": MACRO_MESSAGE_ID,
            "macro_date": creator_macro["date"],
            "decoded_macro": decoded_macro,
            "literal_matrixsumlist_message_ids": creator_literal_hits,
            "selected_31_message_ids": creator_selected_hits,
        },
        "guide": {
            "segmentation_challenge": guide["segmentation_challenge"],
            "segmentation_answer": guide["segmentation_answer"],
            "faed_answer": guide["faed_answer"],
            "no_progress": guide["no_progress"],
            "creator_chronology": guide["creator_chronology"],
        },
        "historical_attachment": {
            "message_id": HISTORICAL_ATTACHMENT_ID,
            "date": attachment_message["date"],
            "author": attachment_message.get("from"),
            "author_id": attachment_message.get("from_id"),
            "file": attachment_message.get("file"),
            "sha256": sha256(attachment_path),
            "defines_row_plus_column": attachment_defines_row_plus_column,
            "uses_selected_31": attachment_uses_selected_31,
        },
        "passage_and_book": {
            "phase_sum_count": passage["phase_sum_count"],
            "phase_matrix_count": passage["phase_matrix_count"],
            "phase_choice_count": passage["phase_choice_count"],
            "book_matrix_phrase_hits": passage["book_full_phrase_count"],
            "book_has_57_58_gap": book_has_57_58_gap,
            "gap_screenshot": str(BOOK_GAP_SCREENSHOT),
            "gap_screenshot_sha256": sha256(BOOK_GAP_SCREENSHOT),
        },
        "latest_export": {
            "group": latest_payload["name"],
            "messages": len(latest_payload["messages"]),
            "first_date": latest_payload["messages"][0]["date"],
            "last_date": latest_payload["messages"][-1]["date"],
            "relevant_ids": latest_hit_ids,
            "context_ids": EXPECTED_LATEST_CONTEXT_IDS,
            "creator_relevant_ids": latest_creator_hits,
            "records": tuple(
                {
                    "id": message["id"],
                    "date": message["date"],
                    "author": message.get("from"),
                    "reply_to": message.get("reply_to_message_id"),
                    "text": flatten_text(message.get("text", "")),
                }
                for message in latest_context
            ),
        },
        "gates": {
            "G1_source": "PASS for the literal instruction; community-only for proposed mechanics",
            "G2_input": "PASS for the exact 31-character selection",
            "G3_operation": "FAIL: no source fixes dimensions, traversal, and sum/index semantics",
            "G4_output": "FAIL: no independently authenticated next-stage output",
            "G5_controls": "PARTIAL: several bounded consumer families are already negative",
        },
        "verdict": (
            "The refreshed evidence does not supply a unique matrixsumlist consumer. "
            "The creator authored the literal macro clue but never posted the literal "
            "word or the selected 31-character output as ordinary text. The recovered "
            "guide and the 2024 attachment are community artifacts with different "
            "operations and inputs. The August export adds theories, not a fixing "
            "instruction. Keep the worksheet row live but blocked at G3."
        ),
    }
    return report


def self_test(
    full_export_dir=DEFAULT_EXPORT_DIR,
    latest_export_dir=LATEST_EXPORT_DIR,
):
    report = audit(full_export_dir, latest_export_dir)
    assert report["full_export"]["messages"] == 57729
    assert report["full_export"]["literal_matrixsumlist_hits"] == 294
    assert report["creator"]["literal_matrixsumlist_message_ids"] == ()
    assert report["creator"]["selected_31_message_ids"] == ()
    assert "just to match the pattern" in report["guide"]["segmentation_challenge"]
    assert report["guide"]["segmentation_answer"] == "To match all prime positions"
    assert "don't have such pattern" in report["guide"]["faed_answer"]
    assert "nothing more" in report["guide"]["no_progress"]
    attachment = report["historical_attachment"]
    assert attachment["file"] == HISTORICAL_ATTACHMENT
    assert attachment["sha256"] == HISTORICAL_ATTACHMENT_SHA256
    assert attachment["defines_row_plus_column"]
    assert not attachment["uses_selected_31"]
    book = report["passage_and_book"]
    assert book == {
        "phase_sum_count": 1,
        "phase_matrix_count": 0,
        "phase_choice_count": 0,
        "book_matrix_phrase_hits": 0,
        "book_has_57_58_gap": True,
        "gap_screenshot": str(BOOK_GAP_SCREENSHOT),
        "gap_screenshot_sha256": BOOK_GAP_SCREENSHOT_SHA256,
    }
    assert report["latest_export"]["relevant_ids"] == EXPECTED_LATEST_RELEVANT_IDS
    assert report["latest_export"]["context_ids"] == EXPECTED_LATEST_CONTEXT_IDS
    assert report["latest_export"]["creator_relevant_ids"] == ()
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full-export", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--latest-export", type=Path, default=LATEST_EXPORT_DIR)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    report = (
        self_test(args.full_export, args.latest_export)
        if args.self_test
        else audit(args.full_export, args.latest_export)
    )
    print(
        "[*] full export: "
        f"messages={report['full_export']['messages']} "
        f"literal matrixsumlist hits={report['full_export']['literal_matrixsumlist_hits']}"
    )
    print(
        "[*] creator: "
        f"macro={report['creator']['macro_message_id']} "
        f"literal hits={report['creator']['literal_matrixsumlist_message_ids']} "
        f"selected-31 hits={report['creator']['selected_31_message_ids']}"
    )
    attachment = report["historical_attachment"]
    print(
        "[*] community attachment: "
        f"message={attachment['message_id']} date={attachment['date']} "
        f"row+column={attachment['defines_row_plus_column']} "
        f"uses-selected-31={attachment['uses_selected_31']}"
    )
    print(
        "[*] latest export: "
        f"through={report['latest_export']['last_date']} "
        f"relevant={report['latest_export']['relevant_ids']} "
        f"creator={report['latest_export']['creator_relevant_ids']}"
    )
    print(f"[*] verdict: {report['verdict']}")
    if args.self_test:
        print("[*] self-test OK")


if __name__ == "__main__":
    main()
