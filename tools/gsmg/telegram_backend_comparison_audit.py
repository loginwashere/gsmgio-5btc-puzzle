#!/usr/bin/env python3
"""Compare the old HTML-derived chat transcript with the new JSON export.

The old archive is a flat transcript produced by ``parse_chat.py`` from a
Telegram HTML export.  The current backend is Telegram Desktop's structured
``result.json``.  Messages are aligned by their absolute Unix timestamp and
normalized text, not by approximate chronology or keyword similarity.

The comparison deliberately keeps two text-normalization levels:

* strict normalization removes ordinary whitespace and rendered URL targets;
* relaxed normalization additionally removes the old parser's empty ``[]``
  link artifacts and ``tel:``/``mailto:`` annotations.

This distinguishes real content changes from known HTML-rendering artifacts.
"""

import argparse
import html
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from telegram_export_manifest import DEFAULT_EXPORT_DIR

DEFAULT_OLD_TRANSCRIPT = (
    Path(__file__).resolve().parents[3]
    / "gsmgio-5btc-puzzle"
    / "_work"
    / "chat_transcript.txt"
)
CREATOR_FROM_ID = "user9815232"

EXPECTED = {
    "old_records": 51_177,
    "new_records": 57_729,
    "new_through_old_end": 55_987,
    "new_nonempty_through_old_end": 51_166,
    "strict_matches": 50_755,
    "parser_artifact_differences": 411,
    "relaxed_matches": 51_166,
    "old_only_deleted": 11,
    "new_nonempty_without_old_counterpart": 0,
    "new_after_old_end": 1_742,
    "new_nonempty_after_old_end": 1_589,
    "replies_through_old_end": 13_137,
    "media_through_old_end": 4_083,
    "captionless_media_through_old_end": 3_108,
    "creator_old_headers": 411,
    "creator_old_headers_verified": 411,
    "creator_new_nonempty_through_old_end": 411,
    "creator_new_after_old_end": 55,
    "sender_same": 40_476,
    "sender_new_null": 10_172,
    "sender_named_difference": 518,
    "forward_like_sender_differences": 57,
    "false_jrk_like_sender_labels": 33,
}

OLD_RECORD_PATTERN = re.compile(
    r"^=== \[(.*?)\] (.*?)\n(.*?)(?=\n\n=== \[|\Z)",
    re.MULTILINE | re.DOTALL,
)
OLD_DATE_PATTERN = re.compile(
    r"(\d\d\.\d\d\.\d{4} \d\d:\d\d:\d\d) UTC([+-])(\d\d):(\d\d)"
)
NUMBERED_DATE_PATTERN = re.compile(r"\d{2}\.\d{2}\.\d{4}")


def flatten_text(value):
    if isinstance(value, str):
        return value
    if not isinstance(value, list):
        return ""
    return "".join(
        item if isinstance(item, str) else item.get("text", "")
        for item in value
    )


def timestamp_from_old_date(value):
    match = OLD_DATE_PATTERN.fullmatch(value)
    if not match:
        raise ValueError(f"unsupported old transcript date: {value!r}")
    local = datetime.strptime(match.group(1), "%d.%m.%Y %H:%M:%S")
    minutes = int(match.group(3)) * 60 + int(match.group(4))
    if match.group(2) == "-":
        minutes = -minutes
    return int(local.replace(tzinfo=timezone(timedelta(minutes=minutes))).timestamp())


def strict_normalize(value):
    value = html.unescape(value).replace("\u00a0", " ")
    value = re.sub(r"\s*\[(?:https?://|tg://)[^\]]+\]", "", value)
    return "\n".join(
        " ".join(line.split())
        for line in value.strip().splitlines()
    )


def relaxed_normalize(value):
    value = strict_normalize(value)
    value = value.replace(" []", "").replace("[] ", "").replace("[]", "")
    value = re.sub(r"\s*\[(?:tel:|mailto:)[^\]]+\]", "", value)
    return "\n".join(" ".join(line.split()) for line in value.splitlines())


def parse_old_transcript(path):
    raw = Path(path).read_text(encoding="utf-8")
    return tuple(
        {
            "date": match.group(1),
            "timestamp": timestamp_from_old_date(match.group(1)),
            "sender": match.group(2),
            "text": match.group(3).strip(),
        }
        for match in OLD_RECORD_PATTERN.finditer(raw)
    )


def parse_new_export(export_dir):
    payload = json.loads(
        (Path(export_dir) / "result.json").read_text(encoding="utf-8")
    )
    records = tuple(
        {
            **message,
            "timestamp": int(message["date_unixtime"]),
            "flat_text": flatten_text(message.get("text", "")),
        }
        for message in payload["messages"]
    )
    return payload, records


def match_records(old_records, new_records, normalizer):
    new_by_timestamp = defaultdict(list)
    for record in new_records:
        new_by_timestamp[record["timestamp"]].append(record)

    matched = []
    unmatched_old = []
    for old in old_records:
        normalized_old = normalizer(old["text"])
        candidates = tuple(
            candidate
            for candidate in new_by_timestamp[old["timestamp"]]
            if normalizer(candidate["flat_text"]) == normalized_old
        )
        if candidates:
            matched.append((old, candidates[0]))
        else:
            unmatched_old.append(old)
    return tuple(matched), tuple(unmatched_old)


def has_media(record):
    return "photo" in record or "file" in record


def audit(
    old_transcript=DEFAULT_OLD_TRANSCRIPT,
    export_dir=DEFAULT_EXPORT_DIR,
):
    old_records = parse_old_transcript(old_transcript)
    payload, new_records = parse_new_export(export_dir)
    strict_matches, strict_unmatched = match_records(
        old_records,
        new_records,
        strict_normalize,
    )
    relaxed_matches, old_only = match_records(
        old_records,
        new_records,
        relaxed_normalize,
    )

    old_end = max(record["timestamp"] for record in old_records)
    new_before = tuple(
        record for record in new_records if record["timestamp"] <= old_end
    )
    new_after = tuple(
        record for record in new_records if record["timestamp"] > old_end
    )
    relaxed_old_timestamps = {
        old["timestamp"] for old, _ in relaxed_matches
    }
    new_nonempty_without_old = tuple(
        record
        for record in new_before
        if relaxed_normalize(record["flat_text"])
        and record["timestamp"] not in relaxed_old_timestamps
    )

    sender_classes = Counter()
    for old, new in relaxed_matches:
        if old["sender"] == new.get("from"):
            sender_classes["same"] += 1
        elif new.get("from") is None:
            sender_classes["new_null"] += 1
        else:
            sender_classes["named_difference"] += 1

    named_differences = tuple(
        (old, new)
        for old, new in relaxed_matches
        if new.get("from") is not None and old["sender"] != new.get("from")
    )
    old_creator = tuple(
        record for record in old_records if record["sender"] == "Jrk Bgrt"
    )
    verified_old_creator = tuple(
        (old, new)
        for old, new in relaxed_matches
        if old["sender"] == "Jrk Bgrt"
        and new.get("from_id") == CREATOR_FROM_ID
    )

    counts = {
        "old_records": len(old_records),
        "new_records": len(new_records),
        "new_through_old_end": len(new_before),
        "new_nonempty_through_old_end": sum(
            bool(relaxed_normalize(record["flat_text"]))
            for record in new_before
        ),
        "strict_matches": len(strict_matches),
        "parser_artifact_differences": len(strict_unmatched) - len(old_only),
        "relaxed_matches": len(relaxed_matches),
        "old_only_deleted": len(old_only),
        "new_nonempty_without_old_counterpart": len(new_nonempty_without_old),
        "new_after_old_end": len(new_after),
        "new_nonempty_after_old_end": sum(
            bool(relaxed_normalize(record["flat_text"]))
            for record in new_after
        ),
        "replies_through_old_end": sum(
            "reply_to_message_id" in record for record in new_before
        ),
        "media_through_old_end": sum(has_media(record) for record in new_before),
        "captionless_media_through_old_end": sum(
            has_media(record) and not relaxed_normalize(record["flat_text"])
            for record in new_before
        ),
        "creator_old_headers": len(old_creator),
        "creator_old_headers_verified": len(verified_old_creator),
        "creator_new_nonempty_through_old_end": sum(
            record.get("from_id") == CREATOR_FROM_ID
            and bool(relaxed_normalize(record["flat_text"]))
            for record in new_before
        ),
        "creator_new_after_old_end": sum(
            record.get("from_id") == CREATOR_FROM_ID for record in new_after
        ),
        "sender_same": sender_classes["same"],
        "sender_new_null": sender_classes["new_null"],
        "sender_named_difference": sender_classes["named_difference"],
        "forward_like_sender_differences": sum(
            bool(NUMBERED_DATE_PATTERN.search(old["sender"]))
            for old, _ in named_differences
        ),
        "false_jrk_like_sender_labels": sum(
            "Jrk Bgrt" in old["sender"]
            and new.get("from_id") != CREATOR_FROM_ID
            for old, new in relaxed_matches
        ),
    }

    return {
        "group_name": payload["name"],
        "old_first": old_records[0]["date"],
        "old_last": old_records[-1]["date"],
        "new_first": new_records[0]["date"],
        "new_last": new_records[-1]["date"],
        "counts": counts,
        "old_only_messages": old_only,
        "new_nonempty_without_old": new_nonempty_without_old,
        "creator_mapping_complete": len(old_creator) == len(verified_old_creator),
    }


def self_test(
    old_transcript=DEFAULT_OLD_TRANSCRIPT,
    export_dir=DEFAULT_EXPORT_DIR,
):
    report = audit(old_transcript, export_dir)
    assert report["group_name"] == "GSMG Puzzle Solvers"
    assert report["counts"] == EXPECTED
    assert report["creator_mapping_complete"]
    assert not report["new_nonempty_without_old"]
    assert all(
        message["sender"] in {"R", "Sparky"}
        for message in report["old_only_messages"]
    )
    print(
        "[*] self-test OK: full timestamp/text alignment, 11 deleted old-only "
        "messages, parser artifacts, sender drift, creator identity, replies, "
        "media, and six-week extension verified"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-transcript", type=Path, default=DEFAULT_OLD_TRANSCRIPT)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    report = audit(args.old_transcript, args.export_dir)
    print(
        f"[*] coverage: old {report['old_first']} -> {report['old_last']}; "
        f"new {report['new_first']} -> {report['new_last']}"
    )
    for key, value in report["counts"].items():
        print(f"    {key}: {value}")
    print("[*] old-only messages removed before the current export:")
    for message in report["old_only_messages"]:
        print(
            f"    {message['date']} {message['sender']!r}: "
            f"{message['text']!r}"
        )
    print(
        "[*] verdict: use the JSON export for reply graphs, stable user IDs, "
        "media paths, and post-2026-06-12 messages. Retain the old transcript "
        "as a deletion/historical-name supplement. Its creator-only exact "
        "headers are fully verified, but generic sender labels can be wrong "
        "for forwarded/quoted messages."
    )
    if args.self_test:
        self_test(args.old_transcript, args.export_dir)


if __name__ == "__main__":
    main()
