#!/usr/bin/env python3
"""Test the seven bounded trilogy-wide Neo-choice boundary phrases.

This is deliberately not a sweep over arbitrary dialogue windows.  It tests
only the seven phrases declared before execution, after confirming their
scene anchors in the three locally committed screenplay PDFs.  Candidate
normalization and passphrase derivation use the repository's established
answer/key-string forms and broad OpenSSL-container oracle.
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

from cb_common import BLOBS  # noqa: E402
from remaining_structural_avenues_audit import material_family  # noqa: E402


PDFS = {
    "MATRIX_1999": (
        ROOT / "wordlists/matrix/the-matrix-1999.pdf",
        "9f88050ce73c254df61163e0f6dbd6e6c2661833ff66418e9a3116d32f2e1546",
    ),
    "RELOADED_2003": (
        ROOT / "wordlists/matrix/the-matrix-reloaded-2003.pdf",
        "2b9d43c9bb32fe85b1ed7651b095855e6ea7a25a236853d7823ea92b211d0db4",
    ),
    "REVOLUTIONS_2003": (
        ROOT / "wordlists/matrix/the-matrix-revolutions-2003.pdf",
        "149f825a87499d07a2e700d875dff41af843dfffb5ad47218d185bb624e64f24",
    ),
}

CANDIDATES = (
    "the truth nothing more",
    "what choice",
    "run neo run",
    "what",
    "what do you want",
    "why do you persist",
    "it was inevitable",
)

CHOICE_PATTERN = re.compile(
    r"\b(?:choice|choices|choose|chooses|chose|chosen|decision|decide|decides|decided)\b",
    re.IGNORECASE,
)
EXPECTED_CHOICE_LEXEMES = {
    "MATRIX_1999": 13,
    "RELOADED_2003": 19,
    "REVOLUTIONS_2003": 19,
}

BOUNDARY_NOTES = {
    "what": "real Machine-City announcement boundary, but non-discriminating",
    "what do you want": (
        "Deus Ex Machina prompt immediately before Neo answers 'Peace'; "
        "'SPEAK!' occurs earlier, before Neo presents the Smith threat"
    ),
}
UNPROMOTED_ALTERNATES = {
    "speak": "start-of-pitch boundary, not the prompt immediately before 'Peace'",
    "because i choose to": "Neo's choice statement itself, not words before it",
}

# These longer normalized fragments bind each short candidate to its intended
# scene rather than merely proving that common words occur somewhere in a PDF.
SCENE_ANCHORS = {
    "MATRIX_1999": (
        "rememberthatalliamofferingisthetruthnothingmore",
        "whatchoicehemakeshischoice",
        "runneorun",
        "looksatthedeadescalator",
    ),
    "RELOADED_2003": (
        "sheisgoingtodieandthereisnothingyoucandotostopit",
    ),
    "REVOLUTIONS_2003": (
        "togowhereneotothemachinecity",
        "whatdoyouwantneolooksupintotheblindingbrightnessneopeace",
        "whydoyoupersistneobecauseichooseto",
        "itwasinevitablesmithseyesfire",
    ),
}


def letters_only(value):
    return re.sub(r"[^a-z]", "", value.lower())


def pdf_text(path):
    completed = subprocess.run(
        ["pdftotext", "-layout", str(path), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def source_provenance():
    reports = {}
    for label, (path, expected_sha256) in PDFS.items():
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != expected_sha256:
            raise AssertionError(f"unexpected {label} PDF SHA-256: {digest}")
        text = pdf_text(path)
        normalized = letters_only(text)
        missing = tuple(
            anchor for anchor in SCENE_ANCHORS[label] if anchor not in normalized
        )
        if missing:
            raise AssertionError(f"missing {label} scene anchors: {missing}")
        choice_lexemes = len(CHOICE_PATTERN.findall(text))
        if choice_lexemes != EXPECTED_CHOICE_LEXEMES[label]:
            raise AssertionError(
                f"unexpected {label} choice-lexeme count: {choice_lexemes}"
            )
        reports[label] = {
            "path": str(path),
            "sha256": digest,
            "scene_anchor_count": len(SCENE_ANCHORS[label]),
            "choice_lexeme_count": choice_lexemes,
        }
    return reports


def audit():
    return {
        "scope": "seven predeclared Neo-choice boundary phrases; no window growth",
        "sources": source_provenance(),
        "candidates": CANDIDATES,
        "boundary_notes": BOUNDARY_NOTES,
        "unpromoted_alternates": UNPROMOTED_ALTERNATES,
        "oracle": material_family(CANDIDATES, BLOBS),
    }


def self_test():
    assert len(CANDIDATES) == 7
    assert len(set(CANDIDATES)) == 7
    assert letters_only("Run, Neo. Run.") == "runneorun"
    assert set(SCENE_ANCHORS) == set(PDFS)
    assert sum(EXPECTED_CHOICE_LEXEMES.values()) == 51
    print(
        "[*] self-test OK: seven fixed candidates, three bound PDFs, "
        "and expected 13/19/19 choice-lexeme counts"
    )


def print_report(report):
    oracle = report["oracle"]
    print(
        f"[*] source PDFs: {len(report['sources'])}; "
        f"scene anchors: {sum(row['scene_anchor_count'] for row in report['sources'].values())}; "
        f"choice lexemes: {sum(row['choice_lexeme_count'] for row in report['sources'].values())}"
    )
    print(
        f"[*] Neo-choice phrases: {oracle['candidate_count']} candidates / "
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
