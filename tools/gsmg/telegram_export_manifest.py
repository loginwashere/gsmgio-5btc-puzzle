#!/usr/bin/env python3
"""Stage 0: structural manifest of the complete GSMG Telegram export.

The 2026-07-26 export (`result.json`) is the full 2019-2026 history of the
"GSMG Puzzle Solvers" private supergroup (id 1166734859) -- 57,729 messages
plus ~4,900 media files. It is far more complete than the existing
`chat_transcript.txt`, which dozens of scripts in this directory cite by
exact line number in their self-tests. This module never touches that file.

This is Stage 0 of a narrowing funnel (see the analysis plan): emit one
cheap manifest row per message (id, timestamp, sender, media presence,
reply link, text length) plus summary counts. No message text is inspected
for content here -- that is Stage 1's job, bounded to a pre-registered
keyword list.
"""

import argparse
import json
from collections import Counter
from pathlib import Path

DEFAULT_EXPORT_DIR = Path("/home/loginwashere/Downloads/Telegram Desktop/ChatExport_2026-07-26")
DEFAULT_MANIFEST_OUTPUT = (
    Path(__file__).resolve().parents[3]
    / "gsmgio-5btc-puzzle"
    / "_work"
    / "telegram_export_manifest.jsonl"
)

EXPECTED_TOTAL_MESSAGES = 57729
EXPECTED_MESSAGE_TYPE_COUNTS = {"message": 55963, "service": 1766}
EXPECTED_FIRST_DATE_UNIXTIME = 1555743302
EXPECTED_LAST_DATE_UNIXTIME = 1785051540
EXPECTED_GROUP_NAME = "GSMG Puzzle Solvers"
EXPECTED_GROUP_ID = 1166734859
EXPECTED_MEDIA_KEY_COUNTS = {"photo": 2303, "file": 1928}


def load_export(export_dir):
    with open(Path(export_dir) / "result.json", encoding="utf-8") as handle:
        return json.load(handle)


def plain_text(message):
    entities = message.get("text_entities") or []
    return "".join(entity.get("text", "") for entity in entities)


def media_descriptor(message):
    if "photo" in message:
        return "photo", message.get("photo")
    if "file" in message:
        return message.get("media_type") or "file", message.get("file_name") or message.get("file")
    return None, None


def build_manifest(data):
    rows = []
    type_counts = Counter()
    media_key_counts = Counter()
    for message in data["messages"]:
        type_counts[message.get("type")] += 1
        if "photo" in message:
            media_key_counts["photo"] += 1
        if "file" in message:
            media_key_counts["file"] += 1
        media_type, media_name = media_descriptor(message)
        rows.append(
            {
                "id": message["id"],
                "type": message.get("type"),
                "date_unixtime": int(message["date_unixtime"]),
                "from": message.get("from"),
                "from_id": message.get("from_id"),
                "reply_to_message_id": message.get("reply_to_message_id"),
                "media_type": media_type,
                "media_name": media_name,
                "text_length": len(plain_text(message)),
            }
        )
    return rows, type_counts, media_key_counts


def summarize(rows, type_counts, media_key_counts):
    sender_counts = Counter(row["from"] for row in rows if row["from"])
    import datetime as _datetime

    year_counts = Counter(
        _datetime.datetime.fromtimestamp(row["date_unixtime"], _datetime.timezone.utc).year
        for row in rows
    )
    text_only = sum(1 for row in rows if row["media_type"] is None and row["text_length"] > 0)
    media_only = sum(1 for row in rows if row["media_type"] is not None and row["text_length"] == 0)
    media_and_text = sum(1 for row in rows if row["media_type"] is not None and row["text_length"] > 0)
    empty = sum(1 for row in rows if row["media_type"] is None and row["text_length"] == 0)
    return {
        "total_messages": len(rows),
        "type_counts": dict(type_counts),
        "media_key_counts": dict(media_key_counts),
        "top_senders": sender_counts.most_common(15),
        "messages_per_year": dict(sorted(year_counts.items())),
        "text_only": text_only,
        "media_only": media_only,
        "media_and_text": media_and_text,
        "empty_service_or_blank": empty,
    }


def write_manifest(rows, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def audit(export_dir=DEFAULT_EXPORT_DIR, output_path=DEFAULT_MANIFEST_OUTPUT, write=True):
    data = load_export(export_dir)
    rows, type_counts, media_key_counts = build_manifest(data)
    summary = summarize(rows, type_counts, media_key_counts)
    summary["group_name"] = data.get("name")
    summary["group_id"] = data.get("id")
    summary["first_date_unixtime"] = min(row["date_unixtime"] for row in rows)
    summary["last_date_unixtime"] = max(row["date_unixtime"] for row in rows)
    if write:
        write_manifest(rows, output_path)
    return rows, summary


def self_test(export_dir=DEFAULT_EXPORT_DIR):
    rows, summary = audit(export_dir, write=False)
    assert summary["group_name"] == EXPECTED_GROUP_NAME
    assert summary["group_id"] == EXPECTED_GROUP_ID
    assert summary["total_messages"] == EXPECTED_TOTAL_MESSAGES
    assert summary["type_counts"] == EXPECTED_MESSAGE_TYPE_COUNTS
    assert summary["first_date_unixtime"] == EXPECTED_FIRST_DATE_UNIXTIME
    assert summary["last_date_unixtime"] == EXPECTED_LAST_DATE_UNIXTIME
    assert summary["media_key_counts"] == EXPECTED_MEDIA_KEY_COUNTS
    assert summary["text_only"] + summary["media_only"] + summary["media_and_text"] + summary["empty_service_or_blank"] == EXPECTED_TOTAL_MESSAGES
    print(
        "[*] self-test OK: 57,729 messages (55,963 message / 1,766 service), "
        "group id/name, first/last timestamp, and media-key counts all match "
        "the values confirmed during planning"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_MANIFEST_OUTPUT)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    self_test(args.export_dir)
    if args.self_test:
        return

    rows, summary = audit(args.export_dir, args.output)
    print(f"[*] group: {summary['group_name']!r} (id {summary['group_id']})")
    print(f"[*] total messages: {summary['total_messages']} {summary['type_counts']}")
    print(f"[*] first/last date_unixtime: {summary['first_date_unixtime']} / {summary['last_date_unixtime']}")
    print(f"[*] media key counts: {summary['media_key_counts']}")
    print(f"[*] text-only: {summary['text_only']}, media-only: {summary['media_only']}, "
          f"media+text: {summary['media_and_text']}, empty/service: {summary['empty_service_or_blank']}")
    print("[*] top 15 senders by message count:")
    for name, count in summary["top_senders"]:
        print(f"    {count:6d}  {name}")
    print("[*] messages per year:")
    for year, count in summary["messages_per_year"].items():
        print(f"    {year}: {count}")
    print(f"[*] manifest written to: {args.output}")


if __name__ == "__main__":
    main()
