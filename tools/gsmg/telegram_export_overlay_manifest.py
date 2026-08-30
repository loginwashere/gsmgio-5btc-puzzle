#!/usr/bin/env python3
"""Build a current GSMG manifest from the pinned full export plus partial overlays.

The complete 2026-07-26 export remains the historical base. Two overlapping
partial exports bridge it through 2026-08-30; later exports win when an edited
or reaction-updated message appears in more than one source.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from telegram_export_manifest import build_manifest, summarize, write_manifest


EXPORT_ROOT = Path("/home/loginwashere/Downloads/Telegram Desktop")
DEFAULT_EXPORTS = [
    EXPORT_ROOT / "ChatExport_2026-07-26",
    EXPORT_ROOT / "ChatExport_2026-08-09 (1)",
    EXPORT_ROOT / "ChatExport_2026-08-30",
]
DEFAULT_OUTPUT = Path(__file__).resolve().parents[2] / "_work" / "telegram_export_overlay_manifest.jsonl"
EXPECTED_GROUP_NAME = "GSMG Puzzle Solvers"
EXPECTED_GROUP_ID = 1166734859
EXPECTED_TOTAL_MESSAGES = 60_375
EXPECTED_TYPE_COUNTS = {"message": 58_479, "service": 1_896}
EXPECTED_MEDIA_KEY_COUNTS = {"photo": 2_386, "file": 2_006}
EXPECTED_FIRST_DATE_UNIXTIME = 1_555_743_302
EXPECTED_LAST_DATE_UNIXTIME = 1_788_071_394
EXPECTED_SOURCE_ROWS = [57_729, 1_026, 1_722]
EXPECTED_OVERLAP_ROWS = 102
EXPECTED_CONFLICT_IDS = [67203, 67230, 67232, 67251, 67257, 67259, 68320, 68332, 68333, 68342]


def load_and_validate(export_dir: Path) -> dict:
    data = json.loads((export_dir / "result.json").read_text(encoding="utf-8"))
    if data.get("name") != EXPECTED_GROUP_NAME or data.get("id") != EXPECTED_GROUP_ID:
        raise AssertionError(f"wrong Telegram group in {export_dir}")
    return data


def merge_exports(export_dirs=DEFAULT_EXPORTS):
    by_id = {}
    overlap_rows = 0
    conflict_ids = []
    source_rows = []
    for export_dir in export_dirs:
        data = load_and_validate(Path(export_dir))
        source_rows.append(len(data["messages"]))
        for message in data["messages"]:
            message_id = message["id"]
            if message_id in by_id:
                overlap_rows += 1
                if by_id[message_id] != message:
                    conflict_ids.append(message_id)
            by_id[message_id] = message
    messages = sorted(by_id.values(), key=lambda row: (int(row["date_unixtime"]), row["id"]))
    return messages, source_rows, overlap_rows, sorted(set(conflict_ids))


def audit(export_dirs=DEFAULT_EXPORTS, output_path=DEFAULT_OUTPUT, write=True):
    messages, source_rows, overlap_rows, conflict_ids = merge_exports(export_dirs)
    rows, type_counts, media_key_counts = build_manifest({"messages": messages})
    summary = summarize(rows, type_counts, media_key_counts)
    summary.update(
        {
            "group_name": EXPECTED_GROUP_NAME,
            "group_id": EXPECTED_GROUP_ID,
            "first_date_unixtime": min(row["date_unixtime"] for row in rows),
            "last_date_unixtime": max(row["date_unixtime"] for row in rows),
            "source_directories": [str(Path(path)) for path in export_dirs],
            "source_rows": source_rows,
            "overlap_rows": overlap_rows,
            "conflict_ids_latest_export_wins": conflict_ids,
            "message_id_min": min(row["id"] for row in rows),
            "message_id_max": max(row["id"] for row in rows),
        }
    )
    if write:
        write_manifest(rows, output_path)
    return rows, summary


def self_test(export_dirs=DEFAULT_EXPORTS):
    rows, summary = audit(export_dirs, write=False)
    assert summary["total_messages"] == EXPECTED_TOTAL_MESSAGES
    assert summary["type_counts"] == EXPECTED_TYPE_COUNTS
    assert summary["media_key_counts"] == EXPECTED_MEDIA_KEY_COUNTS
    assert summary["first_date_unixtime"] == EXPECTED_FIRST_DATE_UNIXTIME
    assert summary["last_date_unixtime"] == EXPECTED_LAST_DATE_UNIXTIME
    assert summary["source_rows"] == EXPECTED_SOURCE_ROWS
    assert summary["overlap_rows"] == EXPECTED_OVERLAP_ROWS
    assert summary["conflict_ids_latest_export_wins"] == EXPECTED_CONFLICT_IDS
    assert summary["message_id_min"] == 1 and summary["message_id_max"] == 70_186
    ids = {row["id"] for row in rows}
    assert {69_850, 69_852, 69_853, 69_856} <= ids
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", action="append", type=Path, dest="export_dirs")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    export_dirs = args.export_dirs or DEFAULT_EXPORTS
    summary = self_test(export_dirs) if export_dirs == DEFAULT_EXPORTS else audit(export_dirs, write=False)[1]
    if args.self_test:
        print("[*] overlay self-test OK")
        return
    rows, summary = audit(export_dirs, args.output, write=True)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"[*] wrote {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
