#!/usr/bin/env python3
"""Verify the Matrix-dialogue count interpretation of `matrixsumlist`/`enter`.

Telegram message 10721 claims that, in the Architect scene, ``Matrix`` is
spoken nine times, ``sum`` once, and ``enter`` once in the line where Trinity
entered the Matrix.  The screenplay contains a tenth ``Matrix`` in stage
direction and two additional direction-only ``enter`` forms, so dialogue
scope is load-bearing.

This audit fixes the complete control-room scene boundaries, verifies all nine
spoken Matrix contexts against the screenplay, and identifies the unique
numeric Matrix context: ``twenty three individuals, sixteen female, seven
male``.  It corroborates the established ``[23,16,7]`` list but does not invent
a downstream operation.
"""

import argparse
import re
import subprocess
from pathlib import Path

from prime_matrixsum_reconstruction import EXPECTED_SUM_LIST
from telegram_export_manifest import DEFAULT_EXPORT_DIR, load_export, plain_text
from telegram_matrix_sum_passage_audit import (
    DEFAULT_WALKTHROUGH,
    extract_phase_plaintext,
)

PDF_PATH = (
    Path(__file__).resolve().parents[2]
    / "wordlists"
    / "matrix"
    / "the-matrix-reloaded-2003.pdf"
)
COMMUNITY_CLAIM_ID = 10721
SCENE_START = "I am the Architect."
SCENE_END = "We won't."
SPOKEN_MATRIX_PHRASES = (
    "I created the Matrix",
    "programming of the Matrix",
    "The Matrix is older",
    "The first Matrix I designed",
    "father of the Matrix",
    "select from the Matrix twenty three individuals sixteen female seven male",
    "everyone connected to the Matrix",
    "she entered the Matrix",
    "leads back to the Matrix",
)
NUMERIC_LIST = (23, 16, 7)
PUZZLE_LIST_PHRASE = (
    "OVER TWENTY THREE CIPHERS SIXTEEN ENCRYPTIONS AND OR SEVEN "
    "INTERTWINED PASSWORDS"
)


def extract_scene(pdf_path=PDF_PATH):
    completed = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    text = completed.stdout
    start = text.find(SCENE_START)
    if start < 0:
        raise AssertionError("Architect scene start was not found")
    end = text.find(SCENE_END, start)
    if end < 0:
        raise AssertionError("Architect scene end was not found")
    return text[start:end + len(SCENE_END)]


def normalize_words(text):
    return " ".join(re.findall(r"[A-Za-z]+", text))


def count_word(text, word):
    return len(re.findall(rf"\b{re.escape(word)}\b", text, flags=re.IGNORECASE))


def community_claim(export_dir=DEFAULT_EXPORT_DIR):
    data = load_export(export_dir)
    message = next(
        message for message in data["messages"]
        if message["id"] == COMMUNITY_CLAIM_ID
    )
    return plain_text(message)


def audit(
    pdf_path=PDF_PATH,
    export_dir=DEFAULT_EXPORT_DIR,
    walkthrough_path=DEFAULT_WALKTHROUGH,
):
    scene = extract_scene(pdf_path)
    normalized = normalize_words(scene)
    claim = community_claim(export_dir)
    phase_plaintext = normalize_words(
        extract_phase_plaintext(walkthrough_path)
    ).upper()
    phrase_counts = {
        phrase: normalized.count(phrase)
        for phrase in SPOKEN_MATRIX_PHRASES
    }
    matrix_count = count_word(scene, "Matrix")
    sum_count = count_word(scene, "sum")
    enter_count = count_word(scene, "enter")
    entered_count = count_word(scene, "entered")
    spoken_matrix_count = sum(phrase_counts.values())
    direction_matrix_count = matrix_count - spoken_matrix_count

    matrix_ordinals = {
        phrase: index + 1
        for index, phrase in enumerate(SPOKEN_MATRIX_PHRASES)
    }
    report = {
        "community_claim": claim,
        "scene_word_count": len(normalized.split()),
        "matrix_count_all": matrix_count,
        "matrix_count_spoken": spoken_matrix_count,
        "matrix_count_direction": direction_matrix_count,
        "sum_count_all": sum_count,
        "enter_count_exact_all": enter_count,
        "entered_count_all": entered_count,
        "spoken_phrase_counts": phrase_counts,
        "sum_matrix_ordinal": matrix_ordinals["programming of the Matrix"],
        "list_matrix_ordinal": matrix_ordinals[
            "select from the Matrix twenty three individuals sixteen female seven male"
        ],
        "enter_matrix_ordinal": matrix_ordinals["she entered the Matrix"],
        "numeric_list": NUMERIC_LIST,
        "numeric_list_sum": sum(NUMERIC_LIST),
        "matches_prime_matrix_sum_list": NUMERIC_LIST == EXPECTED_SUM_LIST,
        "puzzle_parody_carries_list": PUZZLE_LIST_PHRASE in phase_plaintext,
    }

    if "word Matrix was mentioned 9 times" not in claim:
        raise AssertionError("community Matrix-count claim changed")
    if 'word sum was only mentioned once' not in claim:
        raise AssertionError("community SUM-count claim changed")
    if "word enter was only mentioned" not in claim:
        raise AssertionError("community ENTER-count claim changed")
    if any(count != 1 for count in phrase_counts.values()):
        raise AssertionError(f"spoken Matrix contexts changed: {phrase_counts}")
    if matrix_count != 10:
        raise AssertionError(f"unexpected complete-scene Matrix count: {matrix_count}")
    if spoken_matrix_count != 9 or direction_matrix_count != 1:
        raise AssertionError(
            f"unexpected spoken/direction Matrix split: "
            f"{spoken_matrix_count}/{direction_matrix_count}"
        )
    if sum_count != 1:
        raise AssertionError(f"unexpected SUM count: {sum_count}")
    if enter_count != 1 or entered_count != 1:
        raise AssertionError(
            f"unexpected ENTER/ENTERED counts: {enter_count}/{entered_count}"
        )
    if report["numeric_list"] != EXPECTED_SUM_LIST:
        raise AssertionError(
            f"dialogue list differs from prime matrix list: "
            f"{report['numeric_list']} != {EXPECTED_SUM_LIST}"
        )
    if not report["puzzle_parody_carries_list"]:
        raise AssertionError("Phase 3.2.1 parody no longer carries the 23/16/7 list")
    return report


def self_test():
    assert normalize_words("A,  b!\nC") == "A b C"
    assert count_word("enter entered reenter", "enter") == 1
    report = audit()
    assert report["matrix_count_spoken"] == 9
    assert report["numeric_list"] == EXPECTED_SUM_LIST
    print(
        "[*] self-test OK: complete scene has 10 Matrix tokens, exactly 9 "
        "spoken; SUM and the [23,16,7] list are unique spoken contexts"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, default=PDF_PATH)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--walkthrough", type=Path, default=DEFAULT_WALKTHROUGH)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    report = audit(args.pdf, args.export_dir, args.walkthrough)
    print(
        f"[*] complete scene: words={report['scene_word_count']} "
        f"Matrix={report['matrix_count_all']} "
        f"(spoken={report['matrix_count_spoken']}, "
        f"direction={report['matrix_count_direction']})"
    )
    print(
        f"[*] SUM={report['sum_count_all']}; exact ENTER="
        f"{report['enter_count_exact_all']}; ENTERED={report['entered_count_all']}"
    )
    print(
        f"[*] spoken Matrix ordinals: sum={report['sum_matrix_ordinal']}, "
        f"numeric-list={report['list_matrix_ordinal']}, "
        f"entered={report['enter_matrix_ordinal']}"
    )
    print(
        f"[*] unique numeric Matrix list: {report['numeric_list']} "
        f"sum={report['numeric_list_sum']} "
        f"matches established matrix sum list="
        f"{report['matches_prime_matrix_sum_list']}"
    )
    print(
        f"[*] Phase 3.2.1 parody carries 23 ciphers / 16 encryptions / "
        f"7 passwords: {report['puzzle_parody_carries_list']}"
    )
    print(
        "[*] verdict: the community's nine-Matrix dialogue scope is exact and "
        "independently recovers [23,16,7]. It validates the screenplay as a "
        "clue source, but no wording selects indexing, summing to 46, or another "
        "consumer; do not escalate those alternatives without another clue."
    )
    if args.self_test:
        self_test()


if __name__ == "__main__":
    main()
