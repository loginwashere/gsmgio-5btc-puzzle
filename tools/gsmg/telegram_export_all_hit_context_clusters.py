#!/usr/bin/env python3
"""Generalize same-sender context clustering to every Stage-1 keyword hit.

The complete two-hour expansion is retained in counts and witness mappings.
For human review, a bounded context lane keeps non-hit neighbors only when
they name a technique/surprise term, contain media, or carry at least 500
characters.  This preserves technical payloads without pretending the raw
10k-message expansion is itself a reviewable shortlist.
"""

import argparse
import bisect
import json
from collections import defaultdict
from pathlib import Path

from telegram_export_keyword_sweep import sweep as keyword_sweep
from telegram_export_manifest import DEFAULT_EXPORT_DIR, load_export, plain_text
from telegram_export_technique_surprise_sweep import SURPRISE, TECHNIQUES, matched


DEFAULT_WINDOW_SECONDS = 2 * 60 * 60
MIN_LONG_TEXT = 500


def is_media(message):
    return "photo" in message or "file" in message


def context_worthy(message):
    text = plain_text(message)
    return (
        bool(matched(text, TECHNIQUES))
        or bool(matched(text, SURPRISE))
        or len(text) >= MIN_LONG_TEXT
        or is_media(message)
    )


def audit(export_dir=DEFAULT_EXPORT_DIR, window_seconds=DEFAULT_WINDOW_SECONDS):
    data = load_export(export_dir)
    messages = [m for m in data["messages"] if m.get("type") == "message"]
    messages_by_id = {m["id"]: m for m in messages}
    hits = keyword_sweep(data)
    hit_ids = {h["id"] for h in hits}

    sender_timeline = defaultdict(list)
    for message in messages:
        if message.get("from"):
            sender_timeline[message["from"]].append(
                (int(message["date_unixtime"]), message["id"])
            )

    witnesses = defaultdict(set)
    for hit in hits:
        timeline = sender_timeline[hit["from"]]
        timestamp = int(hit["date_unixtime"])
        lo = bisect.bisect_left(timeline, (timestamp - window_seconds, -1))
        hi = bisect.bisect_right(timeline, (timestamp + window_seconds, 10**18))
        for _time, message_id in timeline[lo:hi]:
            witnesses[message_id].add(hit["id"])

    full_ids = set(witnesses)
    review_ids = {
        message_id
        for message_id in full_ids
        if message_id in hit_ids or context_worthy(messages_by_id[message_id])
    }
    context = []
    for message_id in sorted(review_ids - hit_ids):
        message = messages_by_id[message_id]
        context.append({
            "id": message_id,
            "date": message.get("date"),
            "from": message.get("from"),
            "seed_hit_ids": tuple(sorted(witnesses[message_id])),
            "text": plain_text(message),
            "is_media": is_media(message),
        })
    return {
        "stage1_hit_count": len(hits),
        "full_cluster_count": len(full_ids),
        "full_new_context_count": len(full_ids - hit_ids),
        "review_lane_count": len(review_ids),
        "review_lane_new_context_count": len(context),
        "context": tuple(context),
    }


def self_test(export_dir=DEFAULT_EXPORT_DIR):
    report = audit(export_dir)
    context_ids = {row["id"] for row in report["context"]}
    assert {43258, 43441, 43442} <= context_ids
    assert report["full_new_context_count"] > report["review_lane_new_context_count"]
    assert report["review_lane_new_context_count"] < 2000
    print(
        "[*] self-test OK: generalized clustering retains BTCSEED follow-ups "
        "43258/43441/43442 and keeps the review lane bounded"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--window-seconds", type=int, default=DEFAULT_WINDOW_SECONDS)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    if args.self_test:
        self_test(args.export_dir)
        return
    report = audit(args.export_dir, args.window_seconds)
    print(f"[*] Stage-1 hits: {report['stage1_hit_count']}")
    print(
        f"[*] full same-sender expansion: {report['full_cluster_count']} total, "
        f"{report['full_new_context_count']} new"
    )
    print(
        f"[*] review lane: {report['review_lane_count']} total, "
        f"{report['review_lane_new_context_count']} new context messages"
    )
    if args.json_out:
        args.json_out.write_text(
            json.dumps(report["context"], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
