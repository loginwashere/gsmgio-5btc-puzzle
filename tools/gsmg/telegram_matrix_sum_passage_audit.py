#!/usr/bin/env python3
"""Audit the provenance of Denis's "matrix sum list" book-passage claim.

The exact ``YOUR LIFE IS THE SUM...`` text is not missing Cosmic Duality book
content.  It is the already-solved Phase 3.2.1 Beaufort plaintext documented
in the public GSMG walkthrough and discussed in Telegram as "the matrix text"
in January 2021.  This audit verifies that provenance, checks the complete
Cosmic book OCR files for the phrase, and distinguishes the authenticated text
from later community interpretations of what ``matrixsumlist`` instructs.
"""

import argparse
import json
import re
from pathlib import Path

from telegram_export_manifest import DEFAULT_EXPORT_DIR

PROJECTS_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_WALKTHROUGH = PROJECTS_ROOT / "gsmgio-5btc-puzzle" / "README.md"
DEFAULT_BOOK_OCR = (
    Path(__file__).resolve().parents[2]
    / "wordlists"
    / "gsmg"
    / "cosmic_duality_book_screenshot_ocr.txt"
)
DEFAULT_BOOK_FULL = (
    Path(__file__).resolve().parents[2]
    / "wordlists"
    / "gsmg"
    / "cosmic_duality_book_full_text.txt"
)

MATRIX_CONTEXT_ID = 5595
MATRIX_INTRO_ID = 5596
EARLIEST_SUM_REFERENCE_ID = 5597
EXPLICIT_INTERPRETATION_ID = 10721
DENIS_CHAIN_ID = 60352

PHASE_TEXT_START = (
    "YOUR LIFE IS THE SUM OF A REMAINDER OF AN UNBALANCED EQUATION "
    "INHERENT TO THE PROGRAMMING OF THIS PUZZLE"
)
PHASE_TEXT_END = "HOPE YOURE THE ONE CIAO BELLA O"


def flatten_text(value):
    if isinstance(value, str):
        return value
    return "".join(
        item if isinstance(item, str) else item.get("text", "")
        for item in value
    )


def load_messages(export_dir):
    payload = json.loads((export_dir / "result.json").read_text(encoding="utf-8"))
    return payload, {message["id"]: message for message in payload["messages"]}


def message_text(messages, message_id):
    return flatten_text(messages[message_id].get("text", ""))


def extract_phase_plaintext(walkthrough_path):
    text = walkthrough_path.read_text(encoding="utf-8", errors="replace")
    start = text.find(PHASE_TEXT_START)
    if start < 0:
        raise AssertionError("Phase 3.2.1 plaintext start was not found")
    end = text.find(PHASE_TEXT_END, start)
    if end < 0:
        raise AssertionError("Phase 3.2.1 plaintext end was not found")
    return text[start:end + len(PHASE_TEXT_END)]


def count_phrase(path, phrase):
    return path.read_text(encoding="utf-8", errors="replace").lower().count(
        phrase.lower()
    )


def audit(
    export_dir=DEFAULT_EXPORT_DIR,
    walkthrough_path=DEFAULT_WALKTHROUGH,
    book_ocr_path=DEFAULT_BOOK_OCR,
    book_full_path=DEFAULT_BOOK_FULL,
):
    payload, messages = load_messages(export_dir)
    context = message_text(messages, MATRIX_CONTEXT_ID)
    intro = message_text(messages, MATRIX_INTRO_ID)
    earliest = message_text(messages, EARLIEST_SUM_REFERENCE_ID)
    interpretation = message_text(messages, EXPLICIT_INTERPRETATION_ID)
    denis_chain = message_text(messages, DENIS_CHAIN_ID)
    phase_plaintext = extract_phase_plaintext(walkthrough_path)
    phase_upper = phase_plaintext.upper()
    words = re.findall(r"[A-Z]+", phase_upper)

    exact_hits = [
        message["id"]
        for message in payload["messages"]
        if "life is the sum of a remainder" in flatten_text(
            message.get("text", "")
        ).lower()
    ]
    report = {
        "context": context,
        "intro": intro,
        "earliest_reference": earliest,
        "earliest_reference_date": messages[EARLIEST_SUM_REFERENCE_ID]["date"],
        "earliest_exact_hit_id": min(exact_hits),
        "explicit_interpretation": interpretation,
        "denis_chain": denis_chain,
        "phase_plaintext": phase_plaintext,
        "phase_word_count": len(words),
        "phase_sum_count": words.count("SUM"),
        "phase_matrix_count": words.count("MATRIX"),
        "phase_choice_count": words.count("CHOICE"),
        "book_ocr_phrase_count": count_phrase(
            book_ocr_path,
            "your life is the sum",
        ),
        "book_full_phrase_count": count_phrase(
            book_full_path,
            "your life is the sum",
        ),
        "context_media": tuple(
            messages[message_id].get("photo") or messages[message_id].get("file")
            for message_id in (
                MATRIX_CONTEXT_ID,
                MATRIX_INTRO_ID,
                EARLIEST_SUM_REFERENCE_ID,
                EXPLICIT_INTERPRETATION_ID,
                DENIS_CHAIN_ID,
            )
        ),
    }

    if "what is the matrix text" not in context.lower():
        raise AssertionError(f"unexpected 2021 matrix context: {context!r}")
    if "I've been waiting for you" not in intro:
        raise AssertionError("the 2021 message no longer contains the Phase 3.2 intro")
    if earliest != "this and YOUR LIFE IS THE SUM OF A REMAINDER ....":
        raise AssertionError(f"unexpected earliest sum reference: {earliest!r}")
    if report["earliest_exact_hit_id"] != EARLIEST_SUM_REFERENCE_ID:
        raise AssertionError(
            f"earliest exact Telegram hit changed: {report['earliest_exact_hit_id']}"
        )
    if "Matrixsumlist = focus on the scene between Architect and Neo" not in interpretation:
        raise AssertionError("explicit 2023 community interpretation changed")
    if "leafing through a puzzle book" not in denis_chain:
        raise AssertionError("Denis's 2026 narrated-chain wording changed")
    if not phase_plaintext.startswith(PHASE_TEXT_START):
        raise AssertionError("walkthrough plaintext differs at its start")
    if not phase_plaintext.endswith(PHASE_TEXT_END):
        raise AssertionError("walkthrough plaintext differs at its end")
    if report["phase_sum_count"] != 1:
        raise AssertionError(f"unexpected SUM count: {report['phase_sum_count']}")
    if report["phase_matrix_count"] != 0:
        raise AssertionError(
            f"custom Phase 3.2 plaintext unexpectedly names MATRIX: "
            f"{report['phase_matrix_count']}"
        )
    if report["phase_choice_count"] != 0:
        raise AssertionError(
            f"custom Phase 3.2 plaintext unexpectedly names CHOICE: "
            f"{report['phase_choice_count']}"
        )
    if report["book_ocr_phrase_count"] or report["book_full_phrase_count"]:
        raise AssertionError("the Matrix phrase unexpectedly appears in Cosmic book OCR")
    if any(report["context_media"]):
        raise AssertionError("one of the bounded text-evidence messages gained media")
    return report


def self_test():
    report = audit()
    assert report["earliest_exact_hit_id"] == EARLIEST_SUM_REFERENCE_ID
    assert report["phase_sum_count"] == 1
    assert report["phase_choice_count"] == 0
    assert report["book_ocr_phrase_count"] == 0
    assert report["book_full_phrase_count"] == 0
    print(
        "[*] self-test OK: the Matrix-sum phrase is verified as Phase 3.2.1 "
        "plaintext, with 2021 Telegram provenance and no Cosmic-book OCR hit"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--walkthrough", type=Path, default=DEFAULT_WALKTHROUGH)
    parser.add_argument("--book-ocr", type=Path, default=DEFAULT_BOOK_OCR)
    parser.add_argument("--book-full", type=Path, default=DEFAULT_BOOK_FULL)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    report = audit(
        args.export_dir,
        args.walkthrough,
        args.book_ocr,
        args.book_full,
    )
    print(
        f"[*] earliest Telegram reference: message {report['earliest_exact_hit_id']} "
        f"at {report['earliest_reference_date']}"
    )
    print(f"[*] 2021 context: {report['context']!r}")
    print(f"[*] 2021 phrase reference: {report['earliest_reference']!r}")
    print(
        f"[*] Phase 3.2.1 plaintext: words={report['phase_word_count']} "
        f"SUM={report['phase_sum_count']} MATRIX={report['phase_matrix_count']} "
        f"CHOICE={report['phase_choice_count']}"
    )
    print(
        f"[*] Cosmic book phrase hits: screenshot OCR="
        f"{report['book_ocr_phrase_count']}, full text="
        f"{report['book_full_phrase_count']}"
    )
    print(
        "[*] verdict: Denis's 'puzzle book' wording points back to known "
        "Phase 3.2.1/Matrix material, not missing Cosmic Duality pages. The "
        "source text is fixed, but it contains no literal CHOICE boundary, so "
        "the subsequent 'last words before archi choice' source/operation "
        "remains community interpretation rather than an authenticated rule."
    )
    if args.self_test:
        self_test()


if __name__ == "__main__":
    main()
