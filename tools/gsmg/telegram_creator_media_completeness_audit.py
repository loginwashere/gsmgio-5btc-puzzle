#!/usr/bin/env python3
"""Audit Telegram media completeness and creator-connected reply gaps.

This is a structural inventory: it does not keyword-search captions or infer
that a deleted reply parent contained media.  Telegram only preserves a media
path when the corresponding message record survives in the export.
"""

import argparse
import json
import tempfile
from pathlib import Path


CREATOR_ID = "user9815232"
DEFAULT_SOLVERS = Path(
    "/home/loginwashere/Downloads/Telegram Desktop/ChatExport_2026-07-26"
)
DEFAULT_SUPPORT = Path(
    "/home/loginwashere/Downloads/Telegram Desktop/ChatExport_2026-07-29 (2)"
)
EXPECTED = {
    "solvers": {
        "messages": 57729,
        "media": 4231,
        "thumbnails": 1089,
        "creator_records": 500,
        "creator_normal_messages": 482,
        "creator_media": 18,
        "media_replies_to_creator": 18,
        "creator_replies_to_media": 5,
        "broken_creator_reply_edges": 8,
    },
    "support": {
        "messages": 52851,
        "media": 2273,
        "thumbnails": 307,
        "creator_records": 5426,
        "creator_normal_messages": 5419,
        "creator_media": 70,
        "media_replies_to_creator": 29,
        "creator_replies_to_media": 81,
        "broken_creator_reply_edges": 31,
    },
}


def message_text(message):
    text = message.get("text", "")
    if isinstance(text, str):
        return text
    return "".join(
        part if isinstance(part, str) else part.get("text", "")
        for part in text
    )


def media_path(message):
    return message.get("photo") or message.get("file")


def path_record(export_dir, message, field):
    relative = message.get(field)
    if not relative:
        return None
    full = export_dir / relative
    return {
        "message_id": message.get("id"),
        "field": field,
        "path": relative,
        "exists": full.is_file(),
        "size": full.stat().st_size if full.is_file() else None,
    }


def audit_export(export_dir):
    export_dir = Path(export_dir)
    with (export_dir / "result.json").open(encoding="utf-8") as handle:
        messages = json.load(handle)["messages"]

    by_id = {message["id"]: message for message in messages}
    media = [path_record(export_dir, message, "photo") or
             path_record(export_dir, message, "file")
             for message in messages if media_path(message)]
    thumbnails = [
        path_record(export_dir, message, "thumbnail")
        for message in messages if message.get("thumbnail")
    ]
    creator_records = [
        message for message in messages
        if message.get("from_id") == CREATOR_ID
        or message.get("actor_id") == CREATOR_ID
    ]
    creator_normal = [
        message for message in creator_records if message.get("type") == "message"
    ]
    creator_media = [message for message in creator_normal if media_path(message)]

    media_replies_to_creator = []
    creator_replies_to_media = []
    broken_creator_replies = []
    for message in messages:
        parent_id = message.get("reply_to_message_id")
        if parent_id is None:
            continue
        parent = by_id.get(parent_id)
        if media_path(message) and parent and parent.get("from_id") == CREATOR_ID:
            media_replies_to_creator.append(message)
        if message.get("from_id") != CREATOR_ID:
            continue
        if parent is None:
            sibling_replies = [
                sibling for sibling in messages
                if sibling.get("reply_to_message_id") == parent_id
                and sibling.get("id") != message.get("id")
            ]
            broken_creator_replies.append(
                {
                    "message_id": message.get("id"),
                    "date": message.get("date"),
                    "missing_parent_id": parent_id,
                    "creator_text": message_text(message),
                    "surviving_sibling_replies": [
                        {
                            "message_id": sibling.get("id"),
                            "from": sibling.get("from"),
                            "text": message_text(sibling),
                            "media": media_path(sibling),
                        }
                        for sibling in sibling_replies
                    ],
                }
            )
        elif media_path(parent):
            creator_replies_to_media.append(message)

    return {
        "messages": len(messages),
        "media": len(media),
        "thumbnails": len(thumbnails),
        "missing_media": [item for item in media if not item["exists"]],
        "missing_thumbnails": [item for item in thumbnails if not item["exists"]],
        "creator_records": len(creator_records),
        "creator_normal_messages": len(creator_normal),
        "creator_media": len(creator_media),
        "missing_creator_media": [
            path_record(export_dir, message, "photo")
            or path_record(export_dir, message, "file")
            for message in creator_media
            if not (export_dir / media_path(message)).is_file()
        ],
        "media_replies_to_creator": len(media_replies_to_creator),
        "missing_media_replies_to_creator": [
            media_path(message) for message in media_replies_to_creator
            if not (export_dir / media_path(message)).is_file()
        ],
        "creator_replies_to_media": len(creator_replies_to_media),
        "missing_parent_media": [
            media_path(by_id[message["reply_to_message_id"]])
            for message in creator_replies_to_media
            if not (export_dir / media_path(
                by_id[message["reply_to_message_id"]]
            )).is_file()
        ],
        "broken_creator_reply_edges": len(broken_creator_replies),
        "broken_creator_replies": broken_creator_replies,
    }


def verify_expected(reports):
    for name, expected in EXPECTED.items():
        report = reports[name]
        for key, value in expected.items():
            assert report[key] == value, (name, key, report[key], value)
        assert report["missing_media"] == []
        assert report["missing_thumbnails"] == []
        assert report["missing_creator_media"] == []
        assert report["missing_media_replies_to_creator"] == []
        assert report["missing_parent_media"] == []


def self_test():
    with tempfile.TemporaryDirectory() as temporary:
        export_dir = Path(temporary)
        photo = export_dir / "photos" / "one.jpg"
        photo.parent.mkdir()
        photo.write_bytes(b"one")
        data = {
            "messages": [
                {"id": 1, "type": "message", "from_id": CREATOR_ID,
                 "photo": "photos/one.jpg", "text": "creator photo"},
                {"id": 2, "type": "message", "from_id": "user2",
                 "reply_to_message_id": 1, "file": "missing/two.bin"},
                {"id": 3, "type": "message", "from_id": CREATOR_ID,
                 "reply_to_message_id": 99, "text": "reply"},
                {"id": 4, "type": "message", "from_id": "user3",
                 "reply_to_message_id": 99, "text": "same parent"},
            ]
        }
        (export_dir / "result.json").write_text(
            json.dumps(data), encoding="utf-8"
        )
        report = audit_export(export_dir)
        assert report["media"] == 2
        assert len(report["missing_media"]) == 1
        assert report["creator_media"] == 1
        assert report["media_replies_to_creator"] == 1
        assert report["broken_creator_reply_edges"] == 1
        assert len(report["broken_creator_replies"][0][
            "surviving_sibling_replies"
        ]) == 1
    print("[*] self-test OK")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--solvers", type=Path, default=DEFAULT_SOLVERS)
    parser.add_argument("--support", type=Path, default=DEFAULT_SUPPORT)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    self_test()
    if args.self_test:
        return
    reports = {
        "solvers": audit_export(args.solvers),
        "support": audit_export(args.support),
    }
    verify_expected(reports)
    for name, report in reports.items():
        print(
            f"[*] {name}: messages={report['messages']} "
            f"media={report['media']} thumbnails={report['thumbnails']} "
            f"missing_media={len(report['missing_media'])} "
            f"creator_media={report['creator_media']} "
            f"media_replies_to_creator={report['media_replies_to_creator']} "
            f"creator_replies_to_media={report['creator_replies_to_media']} "
            f"broken_creator_replies={report['broken_creator_reply_edges']}"
        )
    if args.json_out:
        args.json_out.write_text(
            json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"[*] wrote {args.json_out}")


if __name__ == "__main__":
    main()
