#!/usr/bin/env python3
"""Test four bounded phrases from the Smith/Neo "equation" exchange
(Revolutions climactic rain-fight monologue), discovered while comparing the
locally committed English subtitle files against the shooting-script PDFs
(FINDINGS.md Phase 183).

That comparison found "what do you want" occurs three times in Revolutions,
not the single Deus Ex Machina occurrence Phase 182 scoped its scene anchor
to -- two of the three are call-and-response repetitions inside this earlier
Smith/Neo scene. This script declares the four short, directly-quoted lines
from that scene as a fixed candidate family (mirroring Phase 182's
predeclare-then-test discipline) and runs them through the same oracle.
Deliberately not a sweep over the surrounding dialogue window.
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

from cb_common import BLOBS  # noqa: E402
from remaining_structural_avenues_audit import material_family  # noqa: E402

REVOLUTIONS_SRT = ROOT / "wordlists/matrix/the-matrix-revolutions-2003.en.srt"
EXPECTED_SRT_SHA256 = (
    "333e2a6ed3b3346e5db5d508ee749ea2c8ffbf47bf0510ca65b8e9863ecb7f0d"
)

CANDIDATES = (
    "i want the same thing you want",
    "i want what you want",
    "the end of the war",
    "nothing this weak is meant to survive",
)

SCENE_ANCHORS = (
    "whatdoyouwantiwantthesamethingyouwantneo",
    "theendofthewar",
    # SRT text renders "I" as a lowercase "l" at this exact spot (a
    # subtitle-source OCR/typesetting artifact, not a puzzle signal) --
    # anchor matches the literal subtitle text, not the corrected reading.
    "nothingthisweakismeanttosurvivewhatdoyouwantlwantwhatyouwant",
)

TIMESTAMP_RE = re.compile(r"^\d+:\d+:\d+[,.]\d+ --> \d+:\d+:\d+[,.]\d+")
INDEX_RE = re.compile(r"^\d+$")
BRACKET_RE = re.compile(r"\[[^\]]*\]")
TAG_RE = re.compile(r"</?[a-zA-Z][^>]*>")


def letters_only(value):
    return re.sub(r"[^a-z]", "", value.lower())


def srt_to_text(raw):
    lines = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or INDEX_RE.match(line) or TIMESTAMP_RE.match(line):
            continue
        line = BRACKET_RE.sub("", TAG_RE.sub("", line))
        if line:
            lines.append(line)
    return " ".join(lines)


def source_provenance():
    raw = REVOLUTIONS_SRT.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_SRT_SHA256:
        raise AssertionError(f"unexpected Revolutions SRT SHA-256: {digest}")
    text = srt_to_text(raw.decode("utf-8"))
    normalized = letters_only(text)
    missing = tuple(anchor for anchor in SCENE_ANCHORS if anchor not in normalized)
    if missing:
        raise AssertionError(f"missing scene anchors: {missing}")
    occurrences = normalized.count("whatdoyouwant")
    if occurrences != 3:
        raise AssertionError(f"unexpected 'what do you want' occurrence count: {occurrences}")
    return {
        "path": str(REVOLUTIONS_SRT),
        "sha256": digest,
        "scene_anchor_count": len(SCENE_ANCHORS),
        "what_do_you_want_occurrences": occurrences,
    }


def audit():
    return {
        "scope": (
            "four predeclared Smith/Neo equation-scene phrases; no window growth"
        ),
        "source": source_provenance(),
        "candidates": CANDIDATES,
        "note": (
            "'what do you want' recurs across this scene and the Deus Ex "
            "Machina scene Phase 182 already covers -- see FINDINGS.md "
            "Phase 183 item 3"
        ),
        "oracle": material_family(CANDIDATES, BLOBS),
    }


def self_test():
    assert len(CANDIDATES) == 4
    assert len(set(CANDIDATES)) == 4
    assert letters_only("Nothing this weak is meant to survive.") == (
        "nothingthisweakismeanttosurvive"
    )
    print(
        "[*] self-test OK: four fixed candidates, one bound SRT source, "
        "3 confirmed 'what do you want' occurrences"
    )


def print_report(report):
    oracle = report["oracle"]
    print(
        f"[*] source: {report['source']['path']}; "
        f"scene anchors: {report['source']['scene_anchor_count']}; "
        f"'what do you want' occurrences: {report['source']['what_do_you_want_occurrences']}"
    )
    print(
        f"[*] Smith/Neo equation phrases: {oracle['candidate_count']} candidates / "
        f"{oracle['unique_material_count']} materials / {len(oracle['hits'])} hits"
    )
    for candidate in report["candidates"]:
        print(f"    {candidate}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    self_test()
    if args.self_test:
        return
    report = audit()
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)


if __name__ == "__main__":
    main()
