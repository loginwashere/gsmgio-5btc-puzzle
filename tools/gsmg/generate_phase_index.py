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


def github_slug(heading_text):
    slug = heading_text.strip().lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    return slug


def parse_phases(text):
    rows = []
    for line in text.splitlines():
        match = HEADING_RE.match(line)
        if not match:
            continue
        number, rest = match.groups()
        date_match = DATE_RE.search(rest)
        date = date_match.group(1) if date_match else None
        body = rest[: date_match.start()].strip() if date_match else rest.strip()
        subject, _, result = body.partition(":")
        subject = subject.strip().rstrip(":")
        result = result.strip()
        rows.append(
            {
                "number": number,
                "heading_text": f"Phase {number} {'--' if '--' in line else chr(0x2014)} {rest}".strip(),
                "raw_line": line,
                "subject": subject,
                "result": result,
                "date": date,
                "slug": github_slug(line[3:]),
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


def build_index(rows, doc_dir):
    duplicate_numbers = sorted(
        number for number, count in Counter(row["number"] for row in rows).items()
        if count > 1
    )
    lines = [
        "---",
        "type: index",
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
    ]
    if duplicate_numbers:
        lines += [
            "> [!warning] Duplicate phase numbers",
            "> These phase numbers are reused with different subjects in "
            "FINDINGS.md and have not been renumbered: "
            + ", ".join(duplicate_numbers) + ".",
            "",
        ]
    lines += [
        "| Phase | Date | Subject | Result | FINDINGS | Audit doc |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        findings_link = f"[link](../tools/gsmg/FINDINGS.md#{row['slug']})"
        audit_doc = find_audit_doc(f"{row['subject']} {row['result']}", doc_dir)
        audit_link = f"[{audit_doc.stem}]({audit_doc.name})" if audit_doc else "—"
        subject = row["subject"] or row["heading_text"]
        result = row["result"] or "—"
        date = row["date"] or "—"
        lines.append(
            f"| {row['number']} | {date} | {subject} | {result} | "
            f"{findings_link} | {audit_link} |"
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
