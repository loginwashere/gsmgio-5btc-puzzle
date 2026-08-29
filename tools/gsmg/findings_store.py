#!/usr/bin/env python3
"""Split, validate, and rebuild the canonical per-phase findings store.

The files under ``tools/gsmg/findings/`` are canonical. ``FINDINGS.md`` is a
generated compatibility artifact retained for existing links, anchors, and
external readers.
"""

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MONOLITH = REPO_ROOT / "tools" / "gsmg" / "FINDINGS.md"
STORE_DIR = REPO_ROOT / "tools" / "gsmg" / "findings"
MANIFEST = STORE_DIR / "manifest.json"
PREAMBLE_NAME = "_PREAMBLE.md"
HEADING_RE = re.compile(r"^## Phase (\S+)\s+[—-]{1,2}\s*(.+)$")
MARKER_RE = re.compile(r"^<!--\s*([a-z_]+):\s*(.+?)\s*-->\s*$")
PHASE_ID_RE = re.compile(r"^<!--\s*phase_id:\s*(\S+)\s*-->\s*$")
FILENAME_RE = re.compile(r"^P\d{5}(?:-\d+)?(?:-[A-Z][A-Z0-9]*)?\.md$")
RELATIVE_LINK_RE = re.compile(r"(\]\()((?:\.\./)+)")


class FindingsStoreError(Exception):
    pass


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def deepen_relative_links(text):
    """Move Markdown link targets one directory deeper for fragment files."""
    return RELATIVE_LINK_RE.sub(lambda match: match.group(1) + "../" + match.group(2), text)


def shallow_relative_links(text):
    """Move fragment Markdown link targets one directory up for FINDINGS.md."""
    return RELATIVE_LINK_RE.sub(
        lambda match: match.group(1) + match.group(2)[3:], text
    )


def phase_sort_stem(number):
    match = re.fullmatch(r"(\d+)(?:\.(\d+))?", number)
    if not match:
        raise FindingsStoreError(f"unsupported phase number: {number!r}")
    major, minor = match.groups()
    stem = f"P{int(major):05d}"
    return f"{stem}-{minor}" if minor is not None else stem


def automatic_stable_id(number):
    return f"P{number.replace('.', '_').zfill(3)}"


def explicit_phase_id(fragment):
    for line in fragment.splitlines():
        match = PHASE_ID_RE.match(line)
        if match:
            return match.group(1)
        if HEADING_RE.match(line):
            break
    return None


def phase_heading(fragment):
    matches = [HEADING_RE.match(line) for line in fragment.splitlines()]
    matches = [match for match in matches if match]
    if len(matches) != 1:
        raise FindingsStoreError(
            f"fragment must contain exactly one Phase heading, found {len(matches)}"
        )
    return matches[0].group(1), matches[0].group(0)


def split_sections(text):
    lines = text.splitlines(keepends=True)
    offsets = []
    cursor = 0
    for line in lines:
        offsets.append(cursor)
        cursor += len(line)

    heading_lines = []
    for index, line in enumerate(lines):
        if HEADING_RE.match(line.rstrip("\r\n")):
            start = index
            while start > 0 and MARKER_RE.match(lines[start - 1].rstrip("\r\n")):
                start -= 1
            heading_lines.append((index, start))
    if not heading_lines:
        raise FindingsStoreError("no Phase headings found")

    boundaries = [offsets[start] for _, start in heading_lines]
    preamble = text[: boundaries[0]]
    fragments = []
    for position, (heading_index, _) in enumerate(heading_lines):
        end = boundaries[position + 1] if position + 1 < len(boundaries) else len(text)
        fragments.append(text[boundaries[position] : end])
        if not HEADING_RE.match(lines[heading_index].rstrip("\r\n")):
            raise AssertionError("internal heading index drift")
    if preamble + "".join(fragments) != text:
        raise AssertionError("split does not round-trip")
    return preamble, fragments


def build_inventory(fragments):
    phase_numbers = [phase_heading(fragment)[0] for fragment in fragments]
    counts = Counter(phase_numbers)
    entries = []
    used_files = set()
    used_ids = set()
    for order, (number, fragment) in enumerate(zip(phase_numbers, fragments), 1):
        explicit_id = explicit_phase_id(fragment)
        if counts[number] > 1 and not explicit_id:
            raise FindingsStoreError(
                f"duplicate Phase {number} lacks an explicit phase_id marker"
            )
        stable_id = explicit_id or automatic_stable_id(number)
        suffix = ""
        if counts[number] > 1:
            match = re.fullmatch(rf"P{re.escape(number.zfill(3))}-([A-Z][A-Z0-9]*)", stable_id)
            if not match:
                raise FindingsStoreError(
                    f"duplicate Phase {number} has incompatible stable ID {stable_id!r}"
                )
            suffix = f"-{match.group(1)}"
        filename = f"{phase_sort_stem(number)}{suffix}.md"
        if filename in used_files or stable_id in used_ids:
            raise FindingsStoreError(f"duplicate filename or stable ID: {filename}, {stable_id}")
        used_files.add(filename)
        used_ids.add(stable_id)
        entries.append(
            {
                "order": order,
                "phase": number,
                "stable_id": stable_id,
                "file": filename,
            }
        )
    return entries


def manifest_payload(entries):
    return {
        "schema_version": 1,
        "canonical_directory": "tools/gsmg/findings",
        "generated_compatibility_file": "tools/gsmg/FINDINGS.md",
        "preamble": PREAMBLE_NAME,
        "phase_count": len(entries),
        "entries": entries,
    }


def load_manifest():
    if not MANIFEST.is_file():
        raise FindingsStoreError(f"manifest missing: {MANIFEST}")
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise FindingsStoreError("unsupported findings manifest schema")
    if data.get("preamble") != PREAMBLE_NAME:
        raise FindingsStoreError("unexpected preamble path")
    entries = data.get("entries")
    if not isinstance(entries, list) or data.get("phase_count") != len(entries):
        raise FindingsStoreError("manifest phase_count/entries mismatch")
    return data


def validate_store():
    data = load_manifest()
    entries = data["entries"]
    if [entry.get("order") for entry in entries] != list(range(1, len(entries) + 1)):
        raise FindingsStoreError("manifest order must be contiguous and one-based")
    listed_files = [entry.get("file") for entry in entries]
    if len(listed_files) != len(set(listed_files)):
        raise FindingsStoreError("manifest contains duplicate fragment filenames")
    stable_ids = [entry.get("stable_id") for entry in entries]
    if len(stable_ids) != len(set(stable_ids)):
        raise FindingsStoreError("manifest contains duplicate stable IDs")

    fragments = []
    for entry in entries:
        filename = entry["file"]
        if not FILENAME_RE.fullmatch(filename):
            raise FindingsStoreError(f"invalid five-digit fragment filename: {filename}")
        path = STORE_DIR / filename
        if not path.is_file():
            raise FindingsStoreError(f"listed fragment is missing: {filename}")
        fragment = path.read_text(encoding="utf-8")
        number, _ = phase_heading(fragment)
        if number != entry["phase"]:
            raise FindingsStoreError(
                f"{filename}: heading Phase {number} != manifest {entry['phase']}"
            )
        explicit_id = explicit_phase_id(fragment)
        stable_id = explicit_id or automatic_stable_id(number)
        if stable_id != entry["stable_id"]:
            raise FindingsStoreError(
                f"{filename}: stable ID {stable_id} != manifest {entry['stable_id']}"
            )
        fragments.append(fragment)

    actual_phase_files = {
        path.name for path in STORE_DIR.glob("P*.md") if path.is_file()
    }
    unlisted = sorted(actual_phase_files - set(listed_files))
    if unlisted:
        raise FindingsStoreError(f"unlisted phase fragments: {', '.join(unlisted)}")
    return data, fragments


def read_findings():
    if not MANIFEST.is_file():
        return MONOLITH.read_text(encoding="utf-8")
    data, fragments = validate_store()
    preamble = (STORE_DIR / data["preamble"]).read_text(encoding="utf-8")
    return shallow_relative_links(preamble) + "".join(
        shallow_relative_links(fragment) for fragment in fragments
    )


def split_monolith():
    if MANIFEST.exists():
        raise FindingsStoreError("manifest already exists; refusing to re-split canonical files")
    STORE_DIR.mkdir(parents=True, exist_ok=True)
    text = MONOLITH.read_text(encoding="utf-8")
    preamble, fragments = split_sections(text)
    entries = build_inventory(fragments)
    (STORE_DIR / PREAMBLE_NAME).write_text(
        deepen_relative_links(preamble), encoding="utf-8"
    )
    for entry, fragment in zip(entries, fragments):
        (STORE_DIR / entry["file"]).write_text(
            deepen_relative_links(fragment), encoding="utf-8"
        )
    MANIFEST.write_text(
        json.dumps(manifest_payload(entries), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    rebuilt = read_findings()
    if rebuilt != text:
        raise AssertionError("post-write findings store does not round-trip")
    return len(entries), sha256_text(text)


def build_monolith(check=False):
    text = read_findings()
    current = MONOLITH.read_text(encoding="utf-8") if MONOLITH.exists() else ""
    if check:
        if current != text:
            raise FindingsStoreError(
                "tools/gsmg/FINDINGS.md is stale; run findings_store.py build"
            )
        return len(load_manifest()["entries"]), sha256_text(text), False
    MONOLITH.write_text(text, encoding="utf-8")
    return len(load_manifest()["entries"]), sha256_text(text), current != text


def register_fragment(filename):
    data = load_manifest()
    if not FILENAME_RE.fullmatch(filename):
        raise FindingsStoreError(f"invalid five-digit fragment filename: {filename}")
    path = STORE_DIR / filename
    if not path.is_file():
        raise FindingsStoreError(f"fragment does not exist: {filename}")
    if any(entry["file"] == filename for entry in data["entries"]):
        raise FindingsStoreError(f"fragment is already registered: {filename}")
    fragment = path.read_text(encoding="utf-8")
    number, _ = phase_heading(fragment)
    if any(entry["phase"] == number for entry in data["entries"]):
        raise FindingsStoreError(
            f"Phase {number} already exists; duplicate phases require explicit IDs "
            "and a reviewed manifest/filename migration"
        )
    expected = f"{phase_sort_stem(number)}.md"
    if filename != expected:
        raise FindingsStoreError(
            f"Phase {number} must use five-digit filename {expected}, got {filename}"
        )
    stable_id = explicit_phase_id(fragment) or automatic_stable_id(number)
    if any(entry["stable_id"] == stable_id for entry in data["entries"]):
        raise FindingsStoreError(f"stable ID already exists: {stable_id}")
    data["entries"].append(
        {
            "order": len(data["entries"]) + 1,
            "phase": number,
            "stable_id": stable_id,
            "file": filename,
        }
    )
    data["phase_count"] = len(data["entries"])
    MANIFEST.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    validate_store()
    return data["phase_count"], stable_id


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("split", help="one-time split of the monolithic file")
    build_parser = subparsers.add_parser("build", help="rebuild FINDINGS.md")
    build_parser.add_argument("--check", action="store_true")
    subparsers.add_parser("validate", help="validate the canonical fragment store")
    register_parser = subparsers.add_parser(
        "register", help="append one new, uniquely numbered phase fragment"
    )
    register_parser.add_argument("filename")
    args = parser.parse_args()
    try:
        if args.command == "split":
            count, digest = split_monolith()
            print(f"[*] split {count} findings; compatibility SHA-256 {digest}")
        elif args.command == "build":
            count, digest, changed = build_monolith(check=args.check)
            state = "up to date" if args.check or not changed else "rebuilt"
            print(f"[*] FINDINGS.md {state}: {count} findings, SHA-256 {digest}")
        elif args.command == "validate":
            data, _ = validate_store()
            print(f"[*] findings store valid: {data['phase_count']} findings")
        elif args.command == "register":
            count, stable_id = register_fragment(args.filename)
            print(f"[*] registered {args.filename} as {stable_id}; {count} findings")
    except FindingsStoreError as error:
        print(f"[!] {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
