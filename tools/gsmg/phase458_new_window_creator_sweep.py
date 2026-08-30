#!/usr/bin/env python3
"""Phase 458 -- creator-message sweep of five Telegram-sensitive gaps' vocabulary.

Scope note: this covers five gaps only -- G-ARCH-001, G-YIN-001, G-ESC-001,
G-MSL-001, G-PRIME-001 -- not the registry's other four parked gaps
(G-MATPROD-001, G-KIT-001, G-GGN-001, G-X2SH-001), which are not
Telegram-corpus-blocked in the same way and are out of scope here.

Phase 247 (`architect_mirror_selector_audit.py`, `INDEXED_SOLVER_MAX_ID =
67263`) checked message ids beyond the indexed cutoff for `G-ARCH-001`'s three
narrower lanes only, against the single newer export available at the time
(`ChatExport_2026-08-09 (1)`, up to id 68343). That means the window swept
here (`id > 67263`, through `ChatExport_2026-08-30`'s id 70186) is *not*
uniformly new: ids 67269-68343 (952 messages) duplicate Phase 247's
already-checked span -- re-swept here only to widen it to the other four
gaps' vocabulary, not because it was previously unchecked -- while ids
68344-70186 (1,564 messages) are the genuinely unswept tail.

Vocabulary provenance also differs by gap: `G-ARCH-001`'s terms are Phase
247's frozen `MIRROR_KEYWORDS`/`ARCHITECT_WORD`/`HYE_WORD`/`SELECTOR_LANGUAGE`,
and `G-PRIME-001`'s terms are Phase 450's frozen numeral/Roman/phrase
patterns -- both reused verbatim. `G-YIN-001`/`G-ESC-001`/`G-MSL-001`'s
patterns below are newly assembled for this phase directly from each gap's
own registry description; no prior phase froze a vocabulary for them. This
does not weaken the negative result (zero creator activity makes vocabulary
choice immaterial to the verdict), but it is not a case of reusing an
existing frozen protocol for those three gaps the way it is for the other two.

Display-name caution: 143 messages in this window show `from: "Denis
Golovkin"`, matching the creator's real name, but belong to Telegram account
`user398109413` -- not the creator's fixed id `user9815232` (whose only
observed display name is `Jrk Bgrt`). All creator-authorship checks below use
`from_id`, never the display name, specifically to avoid this collision.

This script does not decode or interpret anything. It runs one frozen,
bounded pass over every message with `id > 67263` in the current overlay:

1. does any creator-authored (`user9815232`) message exist in this window at
   all;
2. do any messages -- creator-authored, or non-creator with a creator reply
   -- match the union of these five gaps' vocabulary;
3. does any creator-authored media (photo/file) appear in this window (all
   frozen creator media ids from Phase 248 are below the cutoff, so any hit
   here is unconditionally new).

This is a corpus-existence check, not a new decoder or oracle call.
"""

import argparse
import json
import re
from pathlib import Path

from telegram_export_manifest import plain_text
from telegram_export_overlay_manifest import DEFAULT_EXPORTS, merge_exports

CREATOR_ID = "user9815232"
INDEXED_MAX_ID = 67263  # Phase 247's already-checked cutoff; frozen, not re-derived here
GENUINELY_NEW_TAIL_MIN_ID = 68343  # Phase 247 also checked up to here (G-ARCH-001 lanes only)

EXPECTED_WINDOW_MESSAGE_COUNT = 2516
EXPECTED_WINDOW_MIN_ID = 67269
EXPECTED_WINDOW_MAX_ID = 70186
EXPECTED_CREATOR_MESSAGE_COUNT = 0
EXPECTED_CREATOR_MEDIA_COUNT = 0
EXPECTED_GAP_HIT_COUNTS = {
    "G-ARCH-001": 0,
    "G-YIN-001": 0,
    "G-ESC-001": 0,
    "G-MSL-001": 0,
    "G-PRIME-001": 0,
}

GAP_VOCABULARY = {
    "G-ARCH-001": re.compile(
        r"\bmirror|\breflect|\bflip\b|\bopposite\b|\bbackwards?\b|"
        r"\bbeginning|\bending|\breversed?\b|\binvert|\barchitect|\bhye\b|"
        r"\bbye\b|both.*ultimately|ultimately.*the\b",
        re.IGNORECASE,
    ),
    "G-YIN-001": re.compile(
        r"\byin\b|\byang\b|yin.?yang|\bdbbi\b|\bfaed\b", re.IGNORECASE
    ),
    "G-ESC-001": re.compile(
        r"escape|mirror9|checkerboard|\{\s*g\s*,\s*i\s*\}|\{\s*h\s*,\s*e\s*\}",
        re.IGNORECASE,
    ),
    "G-MSL-001": re.compile(
        r"matrixsumlist|matrix.{0,20}dimension|traversal", re.IGNORECASE
    ),
    "G-PRIME-001": re.compile(
        r"(?<!\d)(?:401|400|73)(?!\d)|(?<![A-Za-z])(?:CDI|CD)(?![A-Za-z])|"
        r"roman numerals?|title initial",
        re.IGNORECASE,
    ),
}


def load_window(export_dirs=DEFAULT_EXPORTS, min_id=INDEXED_MAX_ID):
    messages, _source_rows, _overlap_rows, _conflict_ids = merge_exports(export_dirs)
    return tuple(
        m for m in messages if m.get("type") == "message" and m["id"] > min_id
    )


def _base(message, text):
    return {
        "id": message["id"],
        "date": message.get("date"),
        "from": message.get("from"),
        "from_id": message.get("from_id"),
        "is_creator": message.get("from_id") == CREATOR_ID,
        "text": text,
    }


def sweep(export_dirs=DEFAULT_EXPORTS, min_id=INDEXED_MAX_ID):
    window = load_window(export_dirs, min_id)
    by_id = {m["id"]: m for m in window}

    creator_messages = tuple(
        _base(m, plain_text(m)) for m in window if m.get("from_id") == CREATOR_ID
    )

    creator_media = tuple(
        {
            "id": m["id"],
            "date": m.get("date"),
            "media_type": "photo" if "photo" in m else (m.get("media_type") or "file"),
        }
        for m in window
        if m.get("from_id") == CREATOR_ID and ("photo" in m or "file" in m)
    )

    gap_hits = {gap: [] for gap in GAP_VOCABULARY}
    for message in window:
        text = plain_text(message)
        if not text:
            continue
        for gap, pattern in GAP_VOCABULARY.items():
            if not pattern.search(text):
                continue
            is_creator = message.get("from_id") == CREATOR_ID
            children = tuple(
                child
                for child in window
                if child.get("reply_to_message_id") == message["id"]
            )
            has_creator_reply = any(
                child.get("from_id") == CREATOR_ID for child in children
            )
            if is_creator or has_creator_reply:
                gap_hits[gap].append(
                    {**_base(message, text), "has_creator_reply": has_creator_reply}
                )

    any_creator_message = len(creator_messages) > 0
    any_gap_hit = any(hits for hits in gap_hits.values())
    any_creator_media = len(creator_media) > 0

    if any_gap_hit:
        verdict = "gap_vocabulary_hit_licensed"
    elif any_creator_message or any_creator_media:
        verdict = "creator_present_no_gap_vocabulary"
    else:
        verdict = "no_creator_activity_in_window"

    return {
        "window_message_count": len(window),
        "window_min_id": min(m["id"] for m in window) if window else None,
        "window_max_id": max(m["id"] for m in window) if window else None,
        "creator_messages": creator_messages,
        "creator_message_count": len(creator_messages),
        "creator_media": creator_media,
        "gap_hits": gap_hits,
        "any_creator_message": any_creator_message,
        "any_creator_media": any_creator_media,
        "any_gap_hit": any_gap_hit,
        "verdict": verdict,
    }


def _write_synthetic(messages):
    import tempfile

    directory = Path(tempfile.mkdtemp())
    path = directory / "result.json"
    path.write_text(
        json.dumps({"name": "GSMG Puzzle Solvers", "id": 1166734859, "messages": messages}),
        encoding="utf-8",
    )
    return path


def self_test():
    synthetic_old = [
        {
            "id": 100,
            "type": "message",
            "date": "2020-01-01T00:00:00",
            "date_unixtime": "1577836800",
            "from": "Someone",
            "from_id": "userX",
            "text_entities": [{"type": "plain", "text": "old window, ignored"}],
        }
    ]
    synthetic_new = [
        {
            "id": 67264,
            "type": "message",
            "date": "2026-08-15T00:00:00",
            "date_unixtime": "1786838400",
            "from": "Solver",
            "from_id": "userY",
            "text_entities": [{"type": "plain", "text": "just chatting, nothing relevant"}],
        },
        {
            "id": 67265,
            "type": "message",
            "date": "2026-08-15T00:00:01",
            "date_unixtime": "1786838401",
            "from": "Jrk Bgrt",
            "from_id": CREATOR_ID,
            "text_entities": [{"type": "plain", "text": "gm everyone, hope you are well"}],
        },
        {
            "id": 67266,
            "type": "message",
            "date": "2026-08-15T00:00:02",
            "date_unixtime": "1786838402",
            "from": "Solver",
            "from_id": "userZ",
            "text_entities": [{"type": "plain", "text": "does anyone see a mirror in the architect text"}],
        },
        {
            "id": 67267,
            "type": "message",
            "date": "2026-08-15T00:00:03",
            "date_unixtime": "1786838403",
            "from": "Jrk Bgrt",
            "from_id": CREATOR_ID,
            "reply_to_message_id": 67266,
            "text_entities": [{"type": "plain", "text": "interesting theory"}],
            "photo": "photos/photo1.jpg",
        },
    ]
    path_a = _write_synthetic(synthetic_old)
    path_b = _write_synthetic(synthetic_new)
    try:
        result = sweep(export_dirs=[path_a.parent, path_b.parent], min_id=67263)
    finally:
        path_a.unlink()
        path_a.parent.rmdir()
        path_b.unlink()
        path_b.parent.rmdir()

    assert result["window_message_count"] == 4
    assert result["creator_message_count"] == 2
    assert result["any_creator_media"] is True
    assert len(result["creator_media"]) == 1
    assert result["creator_media"][0]["id"] == 67267
    assert len(result["gap_hits"]["G-ARCH-001"]) == 1
    assert result["gap_hits"]["G-ARCH-001"][0]["id"] == 67266
    assert result["gap_hits"]["G-ARCH-001"][0]["is_creator"] is False
    assert result["gap_hits"]["G-ARCH-001"][0]["has_creator_reply"] is True
    assert result["any_gap_hit"] is True
    assert result["verdict"] == "gap_vocabulary_hit_licensed"
    print(
        "[*] self-test OK: old window excluded by id cutoff, creator messages "
        "and media counted correctly, non-creator gap-vocabulary hit correctly "
        "gated on its creator reply"
    )
    return result


def real_corpus_self_test():
    """Assert the frozen real-corpus result, not just synthetic mechanics."""
    report = sweep()
    assert report["window_message_count"] == EXPECTED_WINDOW_MESSAGE_COUNT
    assert report["window_min_id"] == EXPECTED_WINDOW_MIN_ID
    assert report["window_max_id"] == EXPECTED_WINDOW_MAX_ID
    assert report["creator_message_count"] == EXPECTED_CREATOR_MESSAGE_COUNT
    assert len(report["creator_media"]) == EXPECTED_CREATOR_MEDIA_COUNT
    for gap, expected_count in EXPECTED_GAP_HIT_COUNTS.items():
        assert len(report["gap_hits"][gap]) == expected_count, gap
    assert report["verdict"] == "no_creator_activity_in_window"
    print(
        f"[*] real-corpus self-test OK: {report['window_message_count']} messages "
        f"(ids {report['window_min_id']}-{report['window_max_id']}), 0 creator "
        "messages, 0 creator media, 0 gap-vocabulary hits"
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args()

    self_test()
    report = real_corpus_self_test()
    if args.self_test:
        return

    print(
        f"[*] window: ids {report['window_min_id']}-{report['window_max_id']}, "
        f"{report['window_message_count']} messages, "
        f"{report['creator_message_count']} creator-authored"
    )
    for message in report["creator_messages"]:
        print(f"    [creator] id={message['id']} {message['date']}")
        print(f"        {message['text'][:300]!r}")
    for media in report["creator_media"]:
        print(f"    [creator-media] id={media['id']} {media['date']} type={media['media_type']}")
    for gap, hits in report["gap_hits"].items():
        for hit in hits:
            print(
                f"    [{gap}] id={hit['id']} {hit['date']} {hit['from']!r} "
                f"creator={hit['is_creator']} creator_reply={hit['has_creator_reply']}"
            )
            print(f"        {hit['text'][:300]!r}")
    print(f"[*] verdict: {report['verdict']}")

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2, default=list)
        print(f"\n[*] full report written to {args.json_out}")


if __name__ == "__main__":
    main()
