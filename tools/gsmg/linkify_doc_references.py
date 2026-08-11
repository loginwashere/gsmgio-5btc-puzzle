#!/usr/bin/env python3
"""Convert backtick-quoted `doc/GSMG_*.md` references into real relative
Markdown links, so Obsidian (and GitHub) can build backlinks/graph edges
from them.

Only touches inline spans of the exact form `` `doc/GSMG_NAME.md` `` or
`` `doc/GSMG_NAME.md:123-456` `` (optionally line-numbered), where the
referenced file actually exists. Skips anything inside fenced ``` code
blocks, so literal shell examples are left untouched. Does not touch
wikilink-style, already-linked, or non-`doc/GSMG_*` references.
"""

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC_DIR = REPO_ROOT / "doc"

REF_RE = re.compile(r"`(doc/GSMG_[A-Za-z0-9_]+\.md)(:[0-9]+(?:-[0-9]+)?)?`")

DEFAULT_TARGETS = (
    REPO_ROOT / "tools" / "gsmg" / "FINDINGS.md",
    REPO_ROOT / "README.md",
    *sorted(DOC_DIR.glob("*.md")),
)


def relative_link(from_file, target_path):
    return Path(
        __import_relpath(target_path, from_file.parent)
    ).as_posix()


def __import_relpath(target_path, base_dir):
    import os
    return os.path.relpath(target_path, base_dir)


def convert_file(path, dry_run):
    original = path.read_text(encoding="utf-8")
    lines = original.split("\n")
    in_fence = False
    changed = 0
    skipped_missing = []

    for index, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        def replace(match):
            nonlocal changed
            # Skip a backtick span that is already a link's label, e.g.
            # [`doc/GSMG_X.md`](GSMG_X.md) -- re-wrapping it would nest links.
            if line[match.end():match.end() + 1] == "]":
                return match.group(0)
            doc_relpath, suffix = match.group(1), match.group(2) or ""
            target = REPO_ROOT / doc_relpath
            if not target.exists():
                skipped_missing.append(doc_relpath)
                return match.group(0)
            link = relative_link(path, target)
            changed += 1
            display = doc_relpath + suffix
            return f"[{display}]({link})"

        lines[index] = REF_RE.sub(replace, line)

    updated = "\n".join(lines)
    if changed and not dry_run:
        path.write_text(updated, encoding="utf-8")
    return changed, skipped_missing


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--files", nargs="*", type=Path, default=None)
    args = parser.parse_args()

    targets = args.files or DEFAULT_TARGETS
    total = 0
    for path in targets:
        if not path.exists():
            print(f"[!] missing: {path}", file=sys.stderr)
            continue
        changed, skipped_missing = convert_file(path, args.dry_run)
        if changed:
            print(f"[*] {path.relative_to(REPO_ROOT)}: {changed} references linkified")
        for missing in skipped_missing:
            print(f"    [!] referenced file does not exist, left as-is: {missing}",
                  file=sys.stderr)
        total += changed
    print(f"[*] total: {total} references {'would be ' if args.dry_run else ''}linkified")


if __name__ == "__main__":
    main()
