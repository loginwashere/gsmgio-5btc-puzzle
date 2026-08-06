#!/usr/bin/env python3
"""Stage 2: anchor-window + filename media triage over the complete export.

~4,900 media files cannot be viewed one by one. This narrows them to a short,
reviewable shortlist via two independent, bounded axes:

* ANCHORS -- messages already established as central to the recovered
  prime-walk provenance (Phase 48/53/54's exact citations: the creator's only
  reply in this thread, Denis Golovkin's guide/extraction/chain messages,
  Flo Sku's method/highlight posts). For each anchor, every media message from
  the same sender, within a bounded time window, or replying to the anchor is
  pulled in.
* a filename/caption pre-filter over ALL media messages, independent of
  timing, using the same pre-registered keyword list as Stage 1
  (`telegram_export_keyword_sweep.KEYWORDS`) -- catches a self-labeled file
  anywhere in the 7-year history.

Phase 53 already recovered and fully audited one guide image this way
(message 39937, Nik, replied to by message 60325) -- it is included below as
a verification fixture, not re-discovered from scratch.
"""

import argparse
import json
from pathlib import Path

from telegram_export_keyword_sweep import KEYWORDS
from telegram_export_manifest import DEFAULT_EXPORT_DIR, load_export, plain_text

ANCHORS = (
    {"id": 39937, "label": "Nik's guide image (Phase 53)"},
    {"id": 60313, "label": "Denis abstract pre-reveal claim"},
    {"id": 60314, "label": "Jrk Bgrt (creator) only reply in this thread"},
    {"id": 60325, "label": "Denis 'guide' caption, replies to 39937"},
    {"id": 60333, "label": "Denis extraction reveal"},
    {"id": 60352, "label": "Denis full chain interpretation"},
    {"id": 60359, "label": "bitkek endgame theory"},
    {"id": 61381, "label": "Flo Sku method post"},
    {"id": 61456, "label": "Flo Sku highlighted-string post"},
    {"id": 61489, "label": "Denis boundary explanation"},
)
DEFAULT_WINDOW_SECONDS = 2 * 60 * 60

EXPECTED_ANCHOR_MEDIA_HIT_IDS = (39937,)
EXPECTED_KEYWORD_MEDIA_HIT_COUNT_MIN = 0


def is_media_message(message):
    return "photo" in message or "file" in message


def media_path(message):
    if "photo" in message:
        return message["photo"]
    return message.get("file")


def build_reply_children(messages_by_id):
    children = {}
    for message in messages_by_id.values():
        parent = message.get("reply_to_message_id")
        if parent is not None:
            children.setdefault(parent, []).append(message["id"])
    return children


def anchor_media(messages_by_id, reply_children, anchor_id, window_seconds):
    anchor = messages_by_id.get(anchor_id)
    if anchor is None:
        return []
    anchor_time = int(anchor["date_unixtime"])
    anchor_sender = anchor.get("from")
    hits = []

    if is_media_message(anchor):
        hits.append((anchor["id"], "is_the_anchor_itself"))

    for child_id in reply_children.get(anchor_id, ()):
        child = messages_by_id[child_id]
        if is_media_message(child):
            hits.append((child_id, f"replies_to_anchor_{anchor_id}"))

    for message in messages_by_id.values():
        if not is_media_message(message):
            continue
        if message["id"] == anchor_id:
            continue
        same_sender = anchor_sender and message.get("from") == anchor_sender
        within_window = abs(int(message["date_unixtime"]) - anchor_time) <= window_seconds
        if same_sender and within_window:
            hits.append((message["id"], f"same_sender_within_window_of_{anchor_id}"))

    return hits


def keyword_media_hits(messages_by_id):
    hits = []
    for message in messages_by_id.values():
        if not is_media_message(message):
            continue
        filename = media_path(message) or ""
        caption = plain_text(message)
        haystack = f"{filename} {caption}".lower()
        matched = tuple(keyword for keyword in KEYWORDS if keyword in haystack)
        if matched:
            hits.append((message["id"], matched))
    return hits


def audit(export_dir=DEFAULT_EXPORT_DIR, window_seconds=DEFAULT_WINDOW_SECONDS):
    data = load_export(export_dir)
    messages_by_id = {message["id"]: message for message in data["messages"]}
    reply_children = build_reply_children(messages_by_id)

    anchor_hits = {}
    for anchor in ANCHORS:
        anchor_hits[anchor["id"]] = {
            "label": anchor["label"],
            "media": anchor_media(messages_by_id, reply_children, anchor["id"], window_seconds),
        }

    keyword_hits = keyword_media_hits(messages_by_id)

    shortlist_ids = set()
    for entry in anchor_hits.values():
        shortlist_ids.update(media_id for media_id, _ in entry["media"])
    shortlist_ids.update(media_id for media_id, _ in keyword_hits)

    shortlist = []
    for media_id in sorted(shortlist_ids):
        message = messages_by_id[media_id]
        shortlist.append(
            {
                "id": media_id,
                "date": message.get("date"),
                "from": message.get("from"),
                "media_path": media_path(message),
                "caption": plain_text(message),
            }
        )

    return {
        "anchor_hits": anchor_hits,
        "keyword_hits": tuple(keyword_hits),
        "shortlist": tuple(shortlist),
    }


def self_test(export_dir=DEFAULT_EXPORT_DIR):
    report = audit(export_dir)
    guide_entry = report["anchor_hits"][39937]
    assert guide_entry["media"] == [(39937, "is_the_anchor_itself")], guide_entry
    assert len(report["shortlist"]) < 200, (
        f"expected a bounded shortlist, got {len(report['shortlist'])} -- "
        "widen narrowing before treating this as reviewable"
    )
    ids = {item["id"] for item in report["shortlist"]}
    assert 39937 in ids
    print(
        f"[*] self-test OK: {len(report['shortlist'])} media messages shortlisted "
        f"(bounded, reviewable); Nik's guide image (39937) correctly present"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--window-seconds", type=int, default=DEFAULT_WINDOW_SECONDS)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args()

    self_test(args.export_dir)
    if args.self_test:
        return

    report = audit(args.export_dir, args.window_seconds)
    print("[*] anchor media hits:")
    for anchor_id, entry in report["anchor_hits"].items():
        print(f"    {anchor_id} ({entry['label']}): {entry['media']}")
    print(f"\n[*] keyword-matched media (filename/caption): {len(report['keyword_hits'])}")
    for media_id, matched in report["keyword_hits"]:
        print(f"    {media_id}: {matched}")
    print(f"\n[*] total shortlist: {len(report['shortlist'])} media messages")
    for item in report["shortlist"]:
        print(f"    id={item['id']} {item['date']} {item['from']!r} -> {item['media_path']!r} "
              f"caption={item['caption'][:80]!r}")
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as handle:
            json.dump(report["shortlist"], handle, ensure_ascii=False, indent=2)
        print(f"\n[*] shortlist written to {args.json_out}")


if __name__ == "__main__":
    main()
