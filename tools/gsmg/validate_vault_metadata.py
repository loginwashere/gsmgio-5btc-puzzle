#!/usr/bin/env python3
"""Validate YAML frontmatter across doc/*.md against the controlled vocabulary
in doc/GSMG_FACT_LEDGER.md.

This is deliberately partial: only files that already carry frontmatter are
checked. The ~48 not-yet-migrated documents are silently skipped rather than
forced onto the schema early -- see doc/GSMG_FACT_LEDGER.md's migration note.
Re-run after editing any file's frontmatter, or after migrating a new batch.
"""

import argparse
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC_DIR = REPO_ROOT / "doc"
PHASE_INDEX = DOC_DIR / "GSMG_PHASE_INDEX.md"

FRONTMATTER_RE = re.compile(r"\A---\n(.*?\n)---\n", re.DOTALL)

ALLOWED = {
    "type": {
        "audit", "fact", "source", "object", "synthesis", "hypothesis",
        "index", "worksheet", "moc",
    },
    "status": {"live", "stable", "parked", "closed", "superseded", "withdrawn"},
    "result": {
        "positive", "negative", "partial", "inconclusive", "correction", "mixed",
    },
    "disposition": {
        "operative", "recognition-only", "structural-only", "provenance-only",
        "rejected",
    },
    "evidence_level": {
        "creator-primary", "authenticated-artifact", "community-sourced",
        "solver-derived",
    },
}

# Fields that MUST be present for a given `type`. `result` is intentionally
# absent from index/worksheet -- those types get a warning, not an error, if
# it shows up (the guideline is "generally", not "never").
REQUIRED_BY_TYPE = {
    "audit": ("status", "result", "disposition"),
    "fact": ("fact_id", "status", "disposition", "evidence_level"),
    "index": ("status",),
    "worksheet": ("status",),
    "moc": ("topics",),
    "source": ("status",),
    "object": ("status",),
    "synthesis": ("status",),
    "hypothesis": ("status",),
}

DISCOURAGED_BY_TYPE = {
    "index": ("result",),
    "worksheet": ("result",),
}


def load_frontmatter(path):
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        return None
    return yaml.safe_load(match.group(1)) or {}


def known_phase_numbers():
    if not PHASE_INDEX.exists():
        return None
    numbers = set()
    for line in PHASE_INDEX.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| "):
            continue
        cell = line.split("|")[1].strip()
        if cell and cell != "Phase":
            numbers.add(cell)
    return numbers


def validate_file(path, frontmatter, phase_numbers):
    errors = []
    warnings = []
    note_type = frontmatter.get("type")

    if note_type is None:
        errors.append("missing required field: type")
    elif note_type not in ALLOWED["type"]:
        errors.append(f"type={note_type!r} not in {sorted(ALLOWED['type'])}")

    for field in ("status", "result", "disposition", "evidence_level"):
        if field in frontmatter and frontmatter[field] not in ALLOWED[field]:
            errors.append(
                f"{field}={frontmatter[field]!r} not in {sorted(ALLOWED[field])}"
            )

    required = REQUIRED_BY_TYPE.get(note_type, ())
    for field in required:
        if field not in frontmatter or frontmatter[field] in (None, "", []):
            errors.append(f"type={note_type!r} requires field {field!r}")

    for field in DISCOURAGED_BY_TYPE.get(note_type, ()):
        if field in frontmatter:
            warnings.append(
                f"type={note_type!r} conventionally omits {field!r} "
                f"(found {frontmatter[field]!r})"
            )

    if phase_numbers is not None:
        phase = frontmatter.get("phase")
        if phase is not None and str(phase) not in phase_numbers:
            errors.append(
                f"phase={phase!r} is not a phase number in {PHASE_INDEX.name}"
            )
        for related in frontmatter.get("related_phases") or ():
            if str(related) not in phase_numbers:
                warnings.append(
                    f"related_phases contains {related!r}, not found in "
                    f"{PHASE_INDEX.name}"
                )

    script = frontmatter.get("script")
    if script and not (REPO_ROOT / script).exists():
        errors.append(f"script={script!r} does not exist")

    return errors, warnings


def run(doc_dir=DOC_DIR):
    phase_numbers = known_phase_numbers()
    checked = 0
    skipped = 0
    all_errors = {}
    all_warnings = {}
    for path in sorted(doc_dir.glob("*.md")):
        frontmatter = load_frontmatter(path)
        if frontmatter is None:
            skipped += 1
            continue
        checked += 1
        errors, warnings = validate_file(path, frontmatter, phase_numbers)
        if errors:
            all_errors[path.name] = errors
        if warnings:
            all_warnings[path.name] = warnings
    return {
        "checked": checked,
        "skipped": skipped,
        "errors": all_errors,
        "warnings": all_warnings,
    }


def self_test():
    report = run()
    assert report["checked"] >= 15, report["checked"]
    assert not report["errors"], report["errors"]
    print(
        f"[*] self-test OK: {report['checked']} files with frontmatter "
        f"validated, {report['skipped']} skipped (no frontmatter), 0 errors"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0

    report = run()
    print(
        f"[*] checked {report['checked']} files with frontmatter "
        f"({report['skipped']} skipped, no frontmatter)"
    )
    for name, warnings in report["warnings"].items():
        for warning in warnings:
            print(f"    [~] {name}: {warning}")
    for name, errors in report["errors"].items():
        for error in errors:
            print(f"    [!] {name}: {error}", file=sys.stderr)
    if report["errors"]:
        print(f"[!] {sum(len(v) for v in report['errors'].values())} error(s)",
              file=sys.stderr)
        return 1
    print("[*] all frontmatter valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
