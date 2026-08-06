#!/usr/bin/env python3
"""Enumerate every barrystyle/semaj attachment in the Telegram JSON export."""

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

from telegram_export_manifest import DEFAULT_EXPORT_DIR

SENDER_ID = "user925838121"
CREATOR_ID = "user9815232"
EXPECTED_MESSAGE_COUNT = 580
EXPECTED_SERVICE_COUNT = 1
EXPECTED_MEDIA_IDS = (
    8220, 8310, 13003, 13031, 13636, 13637, 13947, 14025, 14042, 14055,
    14091, 14096, 14143, 14943, 15144, 21033, 26132, 30868, 45691, 45749,
    45751, 45753, 46885,
)
EXPECTED_CREATOR_REPLY_PAIRS = ((8311, 8310), (8438, 8436))
PAGE_PATTERNS = ("page 57", "page57", "page 58", "page58", "pp. 57", "pp.57",
                 "pp. 58", "pp.58")


def message_text(message):
    entities = message.get("text_entities") or []
    return "".join(entity.get("text", "") for entity in entities)


def media_path(message):
    return message.get("photo") or message.get("file")


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit(export_dir):
    export_dir = Path(export_dir)
    with (export_dir / "result.json").open(encoding="utf-8") as handle:
        data = json.load(handle)

    authored = [
        message for message in data["messages"]
        if message.get("from_id") == SENDER_ID or message.get("actor_id") == SENDER_ID
    ]
    normal_messages = [message for message in authored if message.get("type") == "message"]
    service_messages = [message for message in authored if message.get("type") == "service"]
    media_messages = [message for message in normal_messages if media_path(message)]

    manifest = []
    for message in media_messages:
        relative_path = media_path(message)
        full_path = export_dir / relative_path
        manifest.append(
            {
                "id": message["id"],
                "date": message["date"],
                "path": relative_path,
                "media_type": message.get("media_type"),
                "mime_type": message.get("mime_type"),
                "declared_size": message.get("file_size", message.get("photo_file_size")),
                "exists": full_path.is_file(),
                "actual_size": full_path.stat().st_size if full_path.is_file() else None,
                "sha256": sha256_file(full_path) if full_path.is_file() else None,
                "caption": message_text(message),
            }
        )

    page_matches = []
    for message in normal_messages:
        text = message_text(message)
        lowered = text.lower()
        matched = [pattern for pattern in PAGE_PATTERNS if pattern in lowered]
        if matched:
            page_matches.append({"id": message["id"], "patterns": matched, "text": text})

    messages_by_id = {message["id"]: message for message in data["messages"]}
    creator_replies = []
    for message in data["messages"]:
        parent = messages_by_id.get(message.get("reply_to_message_id"))
        if message.get("from_id") != CREATOR_ID or not parent:
            continue
        if parent.get("from_id") != SENDER_ID:
            continue
        creator_replies.append(
            {
                "id": message["id"],
                "reply_to": parent["id"],
                "parent_text": message_text(parent),
                "creator_text": message_text(message),
            }
        )

    return {
        "message_count": len(normal_messages),
        "service_count": len(service_messages),
        "media_count": len(manifest),
        "media_ids": [entry["id"] for entry in manifest],
        "first_media_date": manifest[0]["date"] if manifest else None,
        "last_media_date": manifest[-1]["date"] if manifest else None,
        "missing_files": [entry["path"] for entry in manifest if not entry["exists"]],
        "page_matches": page_matches,
        "creator_replies": creator_replies,
        "manifest": manifest,
    }


def verify_expected(report):
    assert report["message_count"] == EXPECTED_MESSAGE_COUNT
    assert report["service_count"] == EXPECTED_SERVICE_COUNT
    assert tuple(report["media_ids"]) == EXPECTED_MEDIA_IDS
    assert report["media_count"] == len(EXPECTED_MEDIA_IDS)
    assert report["first_media_date"] == "2022-07-01T01:01:11"
    assert report["last_media_date"] == "2025-08-09T19:13:22"
    assert report["missing_files"] == []
    assert report["page_matches"] == []
    assert tuple(
        (entry["id"], entry["reply_to"]) for entry in report["creator_replies"]
    ) == EXPECTED_CREATOR_REPLY_PAIRS


def self_test():
    with tempfile.TemporaryDirectory() as tmp:
        export_dir = Path(tmp)
        attachment = export_dir / "photos" / "x.jpg"
        attachment.parent.mkdir()
        attachment.write_bytes(b"test")
        data = {
            "messages": [
                {
                    "id": 1,
                    "type": "service",
                    "actor_id": SENDER_ID,
                    "date": "2020-01-01T00:00:00",
                    "text_entities": [],
                },
                {
                    "id": 2,
                    "type": "message",
                    "from_id": SENDER_ID,
                    "date": "2020-01-02T00:00:00",
                    "photo": "photos/x.jpg",
                    "photo_file_size": 4,
                    "text_entities": [{"type": "plain", "text": "caption"}],
                },
                {
                    "id": 3,
                    "type": "message",
                    "from_id": SENDER_ID,
                    "date": "2020-01-03T00:00:00",
                    "text_entities": [{"type": "plain", "text": "PAGE 57"}],
                },
                {
                    "id": 4,
                    "type": "message",
                    "from_id": CREATOR_ID,
                    "reply_to_message_id": 2,
                    "date": "2020-01-04T00:00:00",
                    "text_entities": [{"type": "plain", "text": "specific"}],
                },
            ]
        }
        (export_dir / "result.json").write_text(json.dumps(data), encoding="utf-8")
        report = audit(export_dir)
        assert report["message_count"] == 2
        assert report["service_count"] == 1
        assert report["media_ids"] == [2]
        assert report["manifest"][0]["actual_size"] == 4
        assert report["manifest"][0]["caption"] == "caption"
        assert report["page_matches"][0]["id"] == 3
        assert report["creator_replies"][0]["id"] == 4
    print("[*] self-test OK")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    self_test()
    if args.self_test:
        return

    report = audit(args.export_dir)
    verify_expected(report)
    print(
        f"[*] messages={report['message_count']} service={report['service_count']} "
        f"media={report['media_count']} missing={len(report['missing_files'])} "
        f"page_matches={len(report['page_matches'])} "
        f"creator_replies={len(report['creator_replies'])}"
    )
    for entry in report["manifest"]:
        print(
            f"{entry['id']}\t{entry['date']}\t{entry['actual_size']}\t"
            f"{entry['sha256']}\t{entry['path']}"
        )
    if args.json_out:
        args.json_out.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"[*] wrote {args.json_out}")


if __name__ == "__main__":
    main()
