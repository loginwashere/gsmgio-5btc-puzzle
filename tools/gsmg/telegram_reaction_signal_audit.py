#!/usr/bin/env python3
"""Use Telegram reaction counts as a community-significance signal.

Every prior sweep of this export selected messages by keyword or by anchor
timing/reply. This is a third, independent axis: which messages did the
*community itself* react to most, regardless of whether they contain any of
our pre-registered keywords. High-reaction messages already known to this
project (Phase 65's New Year "tiny hint," already-indexed creator messages,
already-shortlisted media) are a sanity check that the signal is real, not
noise; anything else in the top set is a genuinely new candidate.

Threshold (>=5 total reactions) was chosen from the observed distribution
before reviewing content: 6,007 of 57,729 messages have any reaction, and
counts drop off sharply (105 messages at >=5, versus 523 at >=3) -- >=5 is
the natural knee, not a value picked to include or exclude a specific
message.
"""

import argparse
import json
from pathlib import Path

from telegram_creator_clue_index_audit import INDEX as CREATOR_INDEX
from telegram_export_anchor_media_triage import audit as triage_audit
from telegram_export_manifest import DEFAULT_EXPORT_DIR, load_export, plain_text

REACTION_THRESHOLD = 5
EXPECTED_TOP_ID = 53342
EXPECTED_TOP_TOTAL = 18
EXPECTED_AT_LEAST_5 = 105
EXPECTED_AT_LEAST_3 = 523


def reaction_total(message):
    reactions = message.get("reactions")
    if not reactions:
        return 0
    return sum(reaction.get("count", 0) for reaction in reactions)


def audit(export_dir=DEFAULT_EXPORT_DIR, threshold=REACTION_THRESHOLD):
    data = load_export(export_dir)
    shortlist_ids = {item["id"] for item in triage_audit(export_dir)["shortlist"]}
    creator_indexed_ids = set(CREATOR_INDEX)

    scored = []
    for message in data["messages"]:
        total = reaction_total(message)
        if total <= 0:
            continue
        scored.append((total, message))
    scored.sort(key=lambda pair: pair[0], reverse=True)

    at_least_5 = sum(1 for total, _ in scored if total >= 5)
    at_least_3 = sum(1 for total, _ in scored if total >= 3)

    top = []
    for total, message in scored:
        if total < threshold:
            break
        top.append(
            {
                "id": message["id"],
                "date": message["date"],
                "from": message.get("from"),
                "total_reactions": total,
                "text": plain_text(message),
                "already_creator_indexed": message["id"] in creator_indexed_ids,
                "already_shortlisted": message["id"] in shortlist_ids,
            }
        )

    novel = tuple(
        record
        for record in top
        if not record["already_creator_indexed"] and not record["already_shortlisted"]
    )

    return {
        "messages_with_any_reaction": len(scored),
        "at_least_5": at_least_5,
        "at_least_3": at_least_3,
        "top": tuple(top),
        "novel": novel,
    }


def self_test(export_dir=DEFAULT_EXPORT_DIR):
    report = audit(export_dir)
    assert report["at_least_5"] == EXPECTED_AT_LEAST_5, report["at_least_5"]
    assert report["at_least_3"] == EXPECTED_AT_LEAST_3, report["at_least_3"]
    assert report["top"][0]["id"] == EXPECTED_TOP_ID
    assert report["top"][0]["total_reactions"] == EXPECTED_TOP_TOTAL
    assert report["top"][0]["already_creator_indexed"] is True, (
        "expected the top-reacted message to already be Phase 65's indexed "
        "New Year 'tiny hint' -- if this changes, the signal may no longer "
        "be validated against known content"
    )
    print(
        f"[*] self-test OK: {report['at_least_5']} messages at >=5 total reactions "
        f"(top: message {report['top'][0]['id']}, {report['top'][0]['total_reactions']} "
        "reactions, already known-indexed -- signal validated)"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--threshold", type=int, default=REACTION_THRESHOLD)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args()

    self_test(args.export_dir)
    if args.self_test:
        return

    report = audit(args.export_dir, args.threshold)
    print(f"[*] {report['messages_with_any_reaction']} messages have any reaction; "
          f"{report['at_least_5']} at >=5, {report['at_least_3']} at >=3")
    print(f"[*] top {len(report['top'])} at threshold >={args.threshold}:")
    for record in report["top"]:
        flags = []
        if record["already_creator_indexed"]:
            flags.append("creator-indexed")
        if record["already_shortlisted"]:
            flags.append("shortlisted")
        flag_str = f" [{', '.join(flags)}]" if flags else " [NOVEL]"
        print(f"    {record['total_reactions']:3d}  {record['id']:6d} {record['date']} "
              f"{record['from']!r}{flag_str}: {record['text'][:120]!r}")
    print(f"\n[*] novel (not already covered by any prior pass): {len(report['novel'])}")
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as handle:
            json.dump(report["top"], handle, ensure_ascii=False, indent=2)
        print(f"[*] full top list written to {args.json_out}")


if __name__ == "__main__":
    main()
