#!/usr/bin/env python3
"""Generate doc/GSMG_PHASE_INDEX.md from tools/gsmg/FINDINGS.md's phase headings.

FINDINGS.md is not split into per-phase files (tests and other docs already
depend on its current layout), so this script builds a navigable table from
its existing "## Phase N -- Subject: Result (date)" headings instead, without
changing FINDINGS.md itself. Re-run after adding new phases; the index is
derived, not hand-maintained.

Link targets use GitHub's heading-slug algorithm so the index works on
GitHub as a plain relative link; Obsidian's own heading search/Outline panel
can be used for in-app navigation regardless of slug format.
"""

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FINDINGS = REPO_ROOT / "tools" / "gsmg" / "FINDINGS.md"
OUTPUT = REPO_ROOT / "doc" / "GSMG_PHASE_INDEX.md"

HEADING_RE = re.compile(r"^## Phase (\S+)\s+[—-]{1,2}\s*(.+)$")
DATE_RE = re.compile(r"\((\d{4}-\d{2}-\d{2})[^)]*\)\s*$")
PHASE_ID_MARKER_RE = re.compile(r"^<!--\s*phase_id:\s*(\S+)\s*-->\s*$")
# Generic marker line, stackable immediately above a heading (any order, no
# blank lines between them or the heading). Currently recognized keys:
#   index_note          -- short corrective text appended to the Result cell,
#                           for a same-day/later correction that changed a
#                           heading's original claim without editing the
#                           heading itself (see GSMG_PHASE_TEMPLATE.md).
#   audit_doc_override   -- exact doc/GSMG_*.md filename to use instead of
#                           find_audit_doc()'s keyword match, for a phase
#                           whose own text names a different canonical doc.
GENERIC_MARKER_RE = re.compile(r"^<!--\s*([a-z_]+):\s*(.+?)\s*-->\s*$")


def github_slug(heading_text):
    slug = heading_text.strip().lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    return slug


def collect_markers(lines, heading_index):
    """Walk upward from immediately above a heading, collecting every
    consecutive `<!-- key: value -->` marker line. Stops at the first line
    that isn't a recognized marker, so markers must be stacked directly
    above the heading with no gap."""
    markers = {}
    i = heading_index - 1
    while i >= 0:
        match = GENERIC_MARKER_RE.match(lines[i])
        if not match:
            break
        key, value = match.groups()
        markers.setdefault(key, value)
        i -= 1
    return markers


def parse_phases(text):
    rows = []
    lines = text.splitlines()
    for index, line in enumerate(lines):
        match = HEADING_RE.match(line)
        if not match:
            continue
        number, rest = match.groups()
        date_match = DATE_RE.search(rest)
        date = date_match.group(1) if date_match else None
        body = rest[: date_match.start()].strip() if date_match else rest.strip()
        # Split on the heading delimiter "colon-space", not a bare colon:
        # a bare-colon split matches the first ":" anywhere in the heading,
        # including one inside inline code with no following space (e.g.
        # `decoded[7:98]`), which produces a subject/result split in the
        # middle of a slice expression instead of at the real separator.
        subject, _, result = body.partition(": ")
        subject = subject.strip().rstrip(":")
        result = result.strip()
        markers = collect_markers(lines, index)
        rows.append(
            {
                "number": number,
                "heading_text": f"Phase {number} {'--' if '--' in line else chr(0x2014)} {rest}".strip(),
                "raw_line": line,
                "subject": subject,
                "result": result,
                "date": date,
                "slug": github_slug(line[3:]),
                "explicit_id": markers.get("phase_id"),
                "index_note": markers.get("index_note"),
                "audit_doc_override": markers.get("audit_doc_override"),
            }
        )
    return rows


def find_audit_doc(subject_and_result, doc_dir):
    words = set(re.findall(r"[a-z0-9]+", subject_and_result.lower()))
    best = None
    best_score = 0
    for path in sorted(doc_dir.glob("GSMG_*.md")):
        doc_words = set(re.findall(r"[a-z0-9]+", path.stem.lower()))
        score = len(words & doc_words)
        if score > best_score:
            best_score = score
            best = path
    return best if best_score >= 2 else None


class PhaseIdError(Exception):
    pass


def assign_stable_ids(rows):
    """Stable IDs must not depend on document order, because inserting or
    reordering another same-numbered phase would silently change existing
    IDs. Rules:

    1. An explicit `<!-- phase_id: P008-A -->` marker on the line before the
       heading is always used as-is.
    2. A phase number that occurs exactly once gets the ordinary `P<NNN>`
       form automatically -- there is nothing for reordering to disturb.
    3. A phase number that occurs more than once and lacks an explicit
       marker on every occurrence is a hard error: auto-suffixing by
       occurrence order is exactly the non-stable behavior this replaces.
    4. Any two rows resolving to the same stable ID (a typo'd explicit
       marker, or an explicit marker colliding with an auto-generated one)
       is a hard error.
    """
    counts = Counter(row["number"] for row in rows)
    unmarked_duplicates = sorted({
        row["number"] for row in rows
        if counts[row["number"]] > 1 and not row["explicit_id"]
    })
    if unmarked_duplicates:
        raise PhaseIdError(
            "duplicate phase number(s) without an explicit phase_id marker "
            f"on every occurrence: {', '.join(unmarked_duplicates)}. Add "
            "`<!-- phase_id: P0NN-A -->` (and -B, -C, ...) immediately above "
            "each occurrence's heading in FINDINGS.md."
        )

    seen_ids = {}
    for row in rows:
        stable_id = row["explicit_id"] or f"P{row['number'].replace('.', '_').zfill(3)}"
        if stable_id in seen_ids:
            raise PhaseIdError(
                f"stable ID collision: {stable_id!r} assigned to both "
                f"Phase {seen_ids[stable_id]} and Phase {row['number']}"
            )
        seen_ids[stable_id] = row["number"]
        row["stable_id"] = stable_id
    return rows


def build_index(rows, doc_dir):
    duplicate_numbers = sorted(
        number for number, count in Counter(row["number"] for row in rows).items()
        if count > 1
    )
    lines = [
        "---",
        "type: index",
        "status: live",
        "generated_from: tools/gsmg/FINDINGS.md",
        "generator: tools/gsmg/generate_phase_index.py",
        "---",
        "",
        "# GSMG Phase Index",
        "",
        f"Generated from **{len(rows)}** `## Phase` headings in "
        "[tools/gsmg/FINDINGS.md](../tools/gsmg/FINDINGS.md). This table is "
        "derived, not hand-maintained — re-run "
        "`python3 tools/gsmg/generate_phase_index.py` after adding a phase "
        "rather than editing this file directly.",
        "",
        "Audit-doc links are a best-effort keyword match on the phase heading "
        "and are not guaranteed correct for every row; the FINDINGS.md link is "
        "authoritative.",
        "",
        "A phase whose original heading was later corrected without editing "
        "the heading itself can carry `<!-- index_note: ... -->` and/or "
        "`<!-- audit_doc_override: FILENAME.md -->` marker comments stacked "
        "directly above its `## Phase N` line in FINDINGS.md; this generator "
        "reads them into the Result/Audit-doc cells below.",
        "",
    ]
    if duplicate_numbers:
        lines += [
            "> [!warning] Duplicate phase numbers",
            "> These phase numbers are reused with different subjects in "
            "FINDINGS.md and have not been renumbered: "
            + ", ".join(duplicate_numbers) + ". Each row still has a unique "
            "**Stable ID** (e.g. `P008-A`, `P008-B`) for citation from other "
            "documents instead of the bare phase number.",
            "",
        ]
    lines += [
        "| Phase | Stable ID | Date | Subject | Result | FINDINGS | Audit doc |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        findings_link = f"[link](../tools/gsmg/FINDINGS.md#{row['slug']})"
        override = row.get("audit_doc_override")
        if override:
            override_path = doc_dir / override
            audit_link = f"[{override_path.stem}]({override_path.name})"
        else:
            audit_doc = find_audit_doc(f"{row['subject']} {row['result']}", doc_dir)
            audit_link = f"[{audit_doc.stem}]({audit_doc.name})" if audit_doc else "—"
        subject = row["subject"] or row["heading_text"]
        result = row["result"] or "—"
        if row.get("index_note"):
            note = f"**{row['index_note']}**"
            result = f"{result} — {note}" if result != "—" else note
        date = row["date"] or "—"
        lines.append(
            f"| {row['number']} | {row['stable_id']} | {date} | {subject} | "
            f"{result} | {findings_link} | {audit_link} |"
        )
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                         help="exit 1 if the generated file would differ from disk")
    args = parser.parse_args()

    text = FINDINGS.read_text(encoding="utf-8")
    rows = parse_phases(text)
    if not rows:
        print("[!] no phase headings found", file=sys.stderr)
        return 1
    try:
        rows = assign_stable_ids(rows)
    except PhaseIdError as error:
        print(f"[!] {error}", file=sys.stderr)
        return 1
    content = build_index(rows, REPO_ROOT / "doc")

    if args.check:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
        if current != content:
            print("[!] doc/GSMG_PHASE_INDEX.md is stale; re-run without --check",
                  file=sys.stderr)
            return 1
        print(f"[*] doc/GSMG_PHASE_INDEX.md is up to date ({len(rows)} phases)")
        return 0

    OUTPUT.write_text(content, encoding="utf-8")
    print(f"[*] wrote {OUTPUT} ({len(rows)} phases)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
