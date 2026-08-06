#!/usr/bin/env python3
"""Stage 1: pre-registered keyword sweep over the complete Telegram export.

Every keyword below was written down before this script was run, tied
directly to the open question this project has flagged as its current
priority (`doc/GSMG_PHASE_BOUNDARY_REAUDIT.md`: what operation, if any,
consumes the recovered 31-character prime-walk output). This is not a
fishing expedition over the full 57,729-message corpus -- it is a fixed,
narrow, case-insensitive substring match intended to surface a short,
reviewable hit list, not a language-model summarization of the whole chat.

Two independent axes are reported:

* KEYWORDS matched against every message's plain text.
* Messages authored by Denis Golovkin or Flo Sku (the two names already
  central to the recovered prime-walk provenance) that ALSO match a keyword
  -- a bounded cross-reference, not a dump of their ~1,436 combined messages.
"""

import argparse
import json
from pathlib import Path

from telegram_export_manifest import DEFAULT_EXPORT_DIR, load_export, plain_text

KEYWORDS = (
    "31 characters",
    "matrixsumlist",
    "consume",
    "zeroed",
    "next step",
    "instruction",
    "guide",
    "yellow-blue",
    "yellow blue",
    "prime walk",
    "ncsyang",
    "dbbi",
    "faed",
)
ANCHOR_SENDERS = ("Denis Golovkin", "Flo Sku")


def matched_keywords(text):
    lowered = text.lower()
    return tuple(keyword for keyword in KEYWORDS if keyword in lowered)


def sweep(data):
    hits = []
    for message in data["messages"]:
        if message.get("type") != "message":
            continue
        text = plain_text(message)
        if not text:
            continue
        matches = matched_keywords(text)
        if not matches:
            continue
        hits.append(
            {
                "id": message["id"],
                "date": message.get("date"),
                "date_unixtime": int(message["date_unixtime"]),
                "from": message.get("from"),
                "matched_keywords": matches,
                "text": text,
                "is_anchor_sender": message.get("from") in ANCHOR_SENDERS,
            }
        )
    return hits


def audit(export_dir=DEFAULT_EXPORT_DIR):
    data = load_export(export_dir)
    hits = sweep(data)
    anchor_sender_hits = tuple(hit for hit in hits if hit["is_anchor_sender"])
    return {
        "hits": tuple(hits),
        "hit_count": len(hits),
        "anchor_sender_hits": anchor_sender_hits,
        "keyword_counts": {
            keyword: sum(1 for hit in hits if keyword in hit["matched_keywords"])
            for keyword in KEYWORDS
        },
    }


def self_test():
    synthetic = {
        "messages": [
            {"id": 1, "type": "message", "date": "2020-01-01T00:00:00", "date_unixtime": "1",
             "from": "Nobody", "text_entities": [{"type": "plain", "text": "just chatting about pizza"}]},
            {"id": 2, "type": "message", "date": "2020-01-01T00:00:01", "date_unixtime": "2",
             "from": "Denis Golovkin", "text_entities": [{"type": "plain", "text": "check the DBBI string"}]},
            {"id": 3, "type": "message", "date": "2020-01-01T00:00:02", "date_unixtime": "3",
             "from": "Someone Else", "text_entities": [{"type": "plain", "text": "what does MATRIXSUMLIST even do"}]},
            {"id": 4, "type": "service", "date": "2020-01-01T00:00:03", "date_unixtime": "4",
             "from": None, "text_entities": []},
            {"id": 5, "type": "message", "date": "2020-01-01T00:00:04", "date_unixtime": "5",
             "from": "Flo Sku", "text_entities": [{"type": "plain", "text": "no relevant content here"}]},
        ]
    }
    hits = sweep(synthetic)
    assert len(hits) == 2, hits
    assert hits[0]["id"] == 2 and hits[0]["matched_keywords"] == ("dbbi",)
    assert hits[1]["id"] == 3 and hits[1]["matched_keywords"] == ("matrixsumlist",)
    assert hits[0]["is_anchor_sender"] is True
    assert hits[1]["is_anchor_sender"] is False
    print("[*] self-test OK: keyword matching, case-insensitivity, service-message "
          "skip, and anchor-sender cross-reference all verified on synthetic data")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args()

    self_test()
    if args.self_test:
        return

    report = audit(args.export_dir)
    print(f"[*] {report['hit_count']} of 57,729 messages matched a pre-registered keyword")
    print(f"[*] keyword counts: {report['keyword_counts']}")
    print(f"[*] of those, {len(report['anchor_sender_hits'])} are from Denis Golovkin/Flo Sku")
    print()
    for hit in report["hits"]:
        print(f"--- id={hit['id']} {hit['date']} {hit['from']!r} matched={hit['matched_keywords']}")
        print(f"    {hit['text'][:300]!r}")
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as handle:
            json.dump(report["hits"], handle, ensure_ascii=False, indent=2)
        print(f"\n[*] full hit list written to {args.json_out}")


if __name__ == "__main__":
    main()
