#!/usr/bin/env python3
"""Regenerate the creator-hint / Telegram-dialog lane in the GSMG Draw.io board.

The canonical scope is the bounded creator-evidence index, not every message
ever posted by the creator account.  One card is emitted per evidence-table
row (a multi-message exchange remains one dialog card), plus the primary
binary-chain post and the unresolved deleted-parent caveat described outside
the tables.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BOARD = ROOT / "doc/drawio/gsmg_puzzle_board.drawio"
DEFAULT_INDEX = ROOT / "doc/GSMG_CREATOR_CLUE_AND_CONFIRMATION_INDEX.md"
DEFAULT_SOLVERS = Path(
    "/home/loginwashere/Downloads/Telegram Desktop/ChatExport_2026-07-26/result.json"
)
DEFAULT_SUPPORT = Path(
    "/home/loginwashere/Downloads/Telegram Desktop/ChatExport_2026-07-29 (2)/result.json"
)

CREATOR_ID = "user9815232"
START_MARKER = "<!-- BEGIN GENERATED CREATOR EVIDENCE PANELS -->"
END_MARKER = "<!-- END GENERATED CREATOR EVIDENCE PANELS -->"

TABLE_SECTIONS = [
    "Original Public Support-Group Evidence",
    "Historical Corrections",
    "First Piece and Extra Door",
    "Book, Prime, Matrix, and Ordered Chain",
    "Near-Final Recognition and Progress",
    "“In Front of Your Eyes” Exchange",
    "July 2026 Creator Return",
    "Additional Records From a Full-Export Review (2026-07-26)",
]

SECTION_COLORS = {
    "Original Public Support-Group Evidence": ("#e8f0fe", "#4a86e8"),
    "Historical Corrections": ("#fff2cc", "#d6b656"),
    "First Piece and Extra Door": ("#fff9e6", "#d6b656"),
    "Book, Prime, Matrix, and Ordered Chain": ("#e1d5e7", "#9673a6"),
    "Near-Final Recognition and Progress": ("#d5e8d4", "#82b366"),
    "“In Front of Your Eyes” Exchange": ("#dae8fc", "#6c8ebf"),
    "July 2026 Creator Return": ("#f8cecc", "#b85450"),
    "Additional Records From a Full-Export Review (2026-07-26)": (
        "#f5f5f5",
        "#666666",
    ),
    "Creator-Authored Non-Chat Artifact": ("#ffe6cc", "#d79b00"),
    "Unresolved Deleted-Parent Caveat": ("#f8cecc", "#b85450"),
}

# Telegram did not always preserve replies as reply edges.  These are the
# narrowly cited adjacent community records required to reconstruct exchanges
# that the canonical index explicitly describes.  They are labelled as
# adjacency, never as direct replies.
ADJACENT_CONTEXT_IDS = {
    ("support", (28812,)): (28810, 28811),
    ("support", (29132,)): (29131,),
    ("solvers", (9603,)): (9602,),
    ("solvers", (60306,)): (60304,),
    ("solvers", (60312,)): (60310,),
    ("solvers", (60314,)): (60313,),
    ("solvers", (66586,)): (66585,),
    ("solvers", (66588, 66589)): (66587,),
}


@dataclass(frozen=True)
class EvidenceRow:
    section: str
    ids: tuple[int, ...]
    id_label: str
    evidence: str
    meaning: str
    source: str


def message_text(message: dict) -> str:
    value = message.get("text", "")
    if isinstance(value, str):
        return value
    return "".join(
        part if isinstance(part, str) else part.get("text", "")
        for part in value
    )


def plain_markdown(value: str) -> str:
    value = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", value)
    value = value.replace("`", "").replace("**", "").replace("*", "")
    return value.strip()


def parse_ids(cell: str) -> tuple[int, ...]:
    range_match = re.search(r"`(\d+)`[–-]`(\d+)`", cell)
    if range_match:
        start, end = map(int, range_match.groups())
        return tuple(range(start, end + 1))
    return tuple(int(value) for value in re.findall(r"`(\d+)`", cell))


def parse_index(path: Path) -> list[EvidenceRow]:
    current_section = ""
    active = False
    rows: list[EvidenceRow] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            current_section = line[3:].strip()
            active = current_section in TABLE_SECTIONS
            continue
        if not active or not line.startswith("| `"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        assert len(cells) == 3, (current_section, line)
        ids = parse_ids(cells[0])
        assert ids, line
        rows.append(
            EvidenceRow(
                section=current_section,
                ids=ids,
                id_label=plain_markdown(cells[0]),
                evidence=plain_markdown(cells[1]),
                meaning=plain_markdown(cells[2]),
                source=(
                    "support"
                    if current_section == "Original Public Support-Group Evidence"
                    else "solvers"
                ),
            )
        )
    assert len(rows) == 79, len(rows)
    assert len({message_id for row in rows for message_id in row.ids}) == 105
    return rows


def load_export(path: Path) -> tuple[str, dict[int, dict]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload["name"], {message["id"]: message for message in payload["messages"]}


def readable_binary(value: str) -> tuple[str, str] | None:
    compact = "".join(value.split())
    if len(compact) < 256 or set(compact) - {"0", "1"}:
        return None
    digest = hashlib.sha256(compact.encode("ascii")).hexdigest()
    if len(compact) % 8:
        return (
            f"[binary payload: {len(compact)} bits; SHA-256 {digest}]",
            "",
        )
    decoded = bytes(
        int(compact[offset : offset + 8], 2)
        for offset in range(0, len(compact), 8)
    )
    printable = sum(byte in b"\n\r\t" or 32 <= byte < 127 for byte in decoded)
    decoded_text = decoded.decode("utf-8", errors="replace") if printable / len(decoded) > 0.85 else ""
    return (
        f"[binary payload: {len(compact)} bits; SHA-256 {digest}]",
        decoded_text,
    )


def display_text(value: str, message_id: int) -> str:
    binary = readable_binary(value)
    if binary is None:
        return value or "[no text; media/action record]"
    summary, decoded = binary
    if message_id == 8446:
        return (
            summary
            + "\nDecoded after reversing the full bitstream:\n"
            + "yellowblueprimes\nmatrixsumlist\nlastwordsbeforearchichoice\n"
            + "yinyang\nwewontgiveawaythepassword\n"
            + "itsinfrontofyoureyesbutyourenotseeingit\n"
            + "verylaststepisatruegiveaway\npromised"
        )
    if decoded:
        return summary + "\n8-bit byte view:\n" + decoded
    return summary + "\nRaw bits remain in the authenticated Telegram export."


def render_transcript(
    row: EvidenceRow,
    exports: dict[str, tuple[str, dict[int, dict]]],
) -> tuple[str, str]:
    group_name, by_id = exports[row.source]
    blocks: list[str] = []
    dates: list[str] = []
    included_parents: set[int] = set()
    for context_id in ADJACENT_CONTEXT_IDS.get((row.source, row.ids), ()):
        context = by_id.get(context_id)
        assert context is not None, (row.source, context_id)
        context_value = display_text(message_text(context), context_id)
        blocks.append(
            f"<b>Adjacent community context #{context_id} (not a direct reply edge):</b> "
            f"{escape_with_breaks(context_value)}"
        )
    for message_id in row.ids:
        message = by_id.get(message_id)
        assert message is not None, (row.source, message_id)
        assert (
            message.get("from_id") == CREATOR_ID
            or message.get("actor_id") == CREATOR_ID
        ), (row.source, message_id, message.get("from_id"), message.get("actor_id"))
        date = message.get("date", "")
        dates.append(date)
        parent_id = message.get("reply_to_message_id")
        if parent_id is not None and parent_id not in included_parents:
            parent = by_id.get(parent_id)
            if parent is None:
                blocks.append(
                    f"<b>Reply parent #{parent_id}:</b> [deleted or absent from export]"
                )
            elif parent_id not in row.ids:
                parent_value = display_text(message_text(parent), parent_id)
                blocks.append(
                    f"<b>Community parent #{parent_id}:</b> {escape_with_breaks(parent_value)}"
                )
            included_parents.add(parent_id)
        creator_value = display_text(message_text(message), message_id)
        media = message.get("photo") or message.get("file")
        media_suffix = f"<br><i>Media:</i> {html.escape(media)}" if media else ""
        blocks.append(
            f"<b>Creator #{message_id} · {html.escape(date)}:</b> "
            f"{escape_with_breaks(creator_value)}{media_suffix}"
        )
    first = min(dates)[:10] if dates else "unknown"
    last = max(dates)[:10] if dates else first
    date_label = first if first == last else f"{first}–{last}"
    transcript = "<br><br>".join(blocks)
    return date_label, f"<i>Source:</i> {html.escape(group_name)}<br><br>{transcript}"


def escape_with_breaks(value: str) -> str:
    return html.escape(value).replace("\n", "<br>")


def card_height(value_html: str) -> int:
    plain = re.sub(r"<br\s*/?>", "\n", value_html, flags=re.I)
    plain = re.sub(r"<[^>]+>", "", plain)
    explicit = plain.count("\n") + 1
    wrapped = sum(max(1, math.ceil(len(line) / 185)) for line in plain.splitlines())
    return max(132, 42 + max(explicit, wrapped) * 15)


def cell_xml(
    cell_id: str,
    parent: str,
    style: str,
    value: str,
    x: int,
    y: int,
    width: int,
    height: int,
) -> str:
    return (
        f'        <mxCell id="{cell_id}" parent="{parent}" style="{style}" '
        f'value="{html.escape(value, quote=True)}" vertex="1">\n'
        f'          <mxGeometry height="{height}" width="{width}" x="{x}" y="{y}" as="geometry" />\n'
        f"        </mxCell>"
    )


def generated_lane(
    rows: list[EvidenceRow],
    exports: dict[str, tuple[str, dict[int, dict]]],
) -> str:
    cards: list[tuple[str, EvidenceRow, str, str, int]] = []
    for index, row in enumerate(rows, start=1):
        date_label, transcript = render_transcript(row, exports)
        value = (
            f"<b>{html.escape(date_label)} · Telegram {html.escape(row.id_label)}</b><br>"
            f"{transcript}<br><br>"
            f"<b>Indexed evidence:</b> {html.escape(row.evidence)}<br>"
            f"<b>Meaning / limit:</b> {html.escape(row.meaning)}"
        )
        cards.append((f"creator-evidence-card-{index:03d}", row, date_label, value, card_height(value)))

    artifact_row = EvidenceRow(
        section="Creator-Authored Non-Chat Artifact",
        ids=(8446,),
        id_label="8446",
        evidence="Creator posts the raw reversed binary dependency chain.",
        meaning="Primary creator artifact fixing the macro order; not a password or a selected downstream transform.",
        source="solvers",
    )
    artifact_date, artifact_transcript = render_transcript(artifact_row, exports)
    artifact_value = (
        f"<b>{artifact_date} · Telegram 8446</b><br>{artifact_transcript}<br><br>"
        f"<b>Indexed evidence:</b> {html.escape(artifact_row.evidence)}<br>"
        f"<b>Meaning / limit:</b> {html.escape(artifact_row.meaning)}"
    )
    cards.append(
        (
            "creator-evidence-card-080",
            artifact_row,
            artifact_date,
            artifact_value,
            card_height(artifact_value),
        )
    )

    caveat_row = EvidenceRow(
        section="Unresolved Deleted-Parent Caveat",
        ids=(28548,),
        id_label="28548",
        evidence='Creator says “Depends how you look at it” in the first rabbit discussion.',
        meaning="The reply parent #28547 is absent. This cannot confirm any proposed interpretation and is retained only as unresolved puzzle dialogue.",
        source="support",
    )
    caveat_date, caveat_transcript = render_transcript(caveat_row, exports)
    caveat_value = (
        f"<b>{caveat_date} · Telegram 28548</b><br>{caveat_transcript}<br><br>"
        f"<b>Indexed evidence:</b> {html.escape(caveat_row.evidence)}<br>"
        f"<b>Meaning / limit:</b> {html.escape(caveat_row.meaning)}"
    )
    cards.append(
        (
            "creator-evidence-card-081",
            caveat_row,
            caveat_date,
            caveat_value,
            card_height(caveat_value),
        )
    )

    by_section: dict[str, list[tuple[str, EvidenceRow, str, str, int]]] = {}
    for card in cards:
        by_section.setdefault(card[1].section, []).append(card)

    section_order = TABLE_SECTIONS + [
        "Creator-Authored Non-Chat Artifact",
        "Unresolved Deleted-Parent Caveat",
    ]
    lane_width = 1900
    inner_width = lane_width - 40
    y = 52
    emitted: list[str] = []
    intro = (
        "<b>Scope:</b> all 79 canonical creator-evidence/dialog clusters, the primary Telegram #8446 binary-chain post, and the unresolved #28548 deleted-parent caveat. "
        "That is 81 separate cards covering 107 authenticated creator records. Ordinary chat is intentionally excluded.<br><br>"
        "Each card preserves Telegram namespace, message IDs, dates, direct reply context where Telegram retained it, the indexed evidence summary, and the limit on what the exchange validates. "
        "Canonical source: doc/GSMG_CREATOR_CLUE_AND_CONFIRMATION_INDEX.md."
    )
    emitted.append(
        cell_xml(
            "creator-evidence-intro",
            "creator-evidence-lane",
            "rounded=0;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#999999;align=left;verticalAlign=top;spacing=8;fontSize=12;",
            intro,
            20,
            y,
            inner_width,
            132,
        )
    )
    y += 150

    card_counter = 0
    for section_index, section in enumerate(section_order, start=1):
        section_cards = by_section.get(section, [])
        if not section_cards:
            continue
        fill, stroke = SECTION_COLORS[section]
        emitted.append(
            cell_xml(
                f"creator-evidence-section-{section_index:02d}",
                "creator-evidence-lane",
                f"rounded=0;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};align=left;verticalAlign=middle;spacingLeft=8;fontSize=15;fontStyle=1;",
                f"{html.escape(section)} — {len(section_cards)} panel{'s' if len(section_cards) != 1 else ''}",
                20,
                y,
                inner_width,
                40,
            )
        )
        y += 52
        for cell_id, row, _date, value, height in section_cards:
            card_counter += 1
            emitted.append(
                cell_xml(
                    cell_id,
                    "creator-evidence-lane",
                    f"rounded=0;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};align=left;verticalAlign=top;spacing=8;fontSize=11;",
                    value,
                    20,
                    y,
                    inner_width,
                    height,
                )
            )
            y += height + 12
        y += 16

    assert card_counter == 81, card_counter
    lane_height = y + 20
    lane = cell_xml(
        "creator-evidence-lane",
        "1",
        "swimlane;whiteSpace=wrap;html=1;startSize=40;fontSize=18;fontStyle=1;fillColor=#eef7f7;strokeColor=#3f7f7f;verticalAlign=top;align=left;spacingLeft=10;rounded=0;",
        "CREATOR HINTS & TELEGRAM PUZZLE DIALOGS — COMPLETE AUTHENTICATED INDEX",
        4920,
        40,
        lane_width,
        lane_height,
    )
    return "\n".join([START_MARKER, lane, *emitted, END_MARKER])


def update_board(board: Path, generated: str) -> None:
    original = board.read_text(encoding="utf-8")
    if START_MARKER in original or END_MARKER in original:
        assert original.count(START_MARKER) == 1
        assert original.count(END_MARKER) == 1
        start = original.index(START_MARKER)
        end = original.index(END_MARKER) + len(END_MARKER)
        updated = original[:start] + generated + original[end:]
    else:
        assert "      </root>" in original
        updated = original.replace("      </root>", generated + "\n      </root>", 1)
    ET.fromstring(updated)
    board.write_text(updated, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--solvers", type=Path, default=DEFAULT_SOLVERS)
    parser.add_argument("--support", type=Path, default=DEFAULT_SUPPORT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    rows = parse_index(args.index)
    exports = {
        "solvers": load_export(args.solvers),
        "support": load_export(args.support),
    }
    generated = generated_lane(rows, exports)
    if args.check:
        current = args.board.read_text(encoding="utf-8")
        assert START_MARKER in current and END_MARKER in current
        existing = current[
            current.index(START_MARKER) : current.index(END_MARKER) + len(END_MARKER)
        ]
        assert existing == generated, "generated creator lane is stale"
        ET.fromstring(current)
        print("[*] creator-evidence lane is current; XML valid; 81 panels / 107 records")
        return
    update_board(args.board, generated)
    print("[*] regenerated creator-evidence lane: 81 panels / 107 records")


if __name__ == "__main__":
    main()
