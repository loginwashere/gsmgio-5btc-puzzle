#!/usr/bin/env python3
"""Phase 435: frozen, oracle-free `BE REQUIRED` operator-selector audit."""

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from data import VALIDATION_ESCAPES
from p32_sibling_password_audit import derive_sibling_outputs
from telegram_23167_operation_audit import guide_endpoint_profile


REPO_ROOT = Path(__file__).resolve().parents[2]
README_PATH = REPO_ROOT / "README.md"
SRT_PATH = REPO_ROOT / "wordlists" / "matrix" / "the-matrix-reloaded-2003.en.srt"
START_MARKER = "YOUR LIFE IS THE SUM OF A REMAINDER"
END_MARKER = "HOPE YOURE THE ONE CIAO BELLA O"
TARGET_WORDS = ("BE", "REQUIRED")

# Both are repeated content-bearing bigrams with one occurrence in a borrowed
# Matrix sentence and another in creator-added prose.  This frozen
# classification prevents uniqueness from being granted to BE REQUIRED merely
# because it motivated the audit.
MIXED_PROVENANCE_REPEATED_BIGRAMS = (
    ("BE", "REQUIRED"),
    ("RESULT", "IN"),
)


def overlapping_positions(text, needle):
    return tuple(match.start() for match in re.finditer(f"(?={re.escape(needle)})", text))


def readme_passage(path=README_PATH):
    text = Path(path).read_text(encoding="utf-8")
    start = text.index(START_MARKER)
    end = text.index(END_MARKER, start) + len(END_MARKER)
    display = text[start:end]
    words = tuple(re.findall(r"[A-Za-z]+", display.upper()))
    connected = "".join(words)
    return display, words, connected


def repeated_ngrams(words, width):
    counts = Counter(tuple(words[index:index + width]) for index in range(len(words) - width + 1))
    return tuple(
        {"words": gram, "count": count}
        for gram, count in counts.items()
        if count > 1
    )


def word_occurrences(words, gram):
    width = len(gram)
    return tuple(index for index in range(len(words) - width + 1) if tuple(words[index:index + width]) == tuple(gram))


def contexts(words, positions, radius=6):
    return tuple(
        " ".join(words[max(0, index - radius):min(len(words), index + len(TARGET_WORDS) + radius)])
        for index in positions
    )


def audit():
    answer = derive_sibling_outputs()["answer_321"]
    _, words, connected = readme_passage()
    if connected != answer:
        raise AssertionError("README word segmentation letters differ from fresh Phase-3.2.1 derivation")

    connected_positions_0 = overlapping_positions(answer, "BEREQUIRED")
    word_positions_0 = word_occurrences(words, TARGET_WORDS)
    be_word_positions_0 = tuple(index for index, word in enumerate(words) if word == "BE")
    raw_be_positions_0 = overlapping_positions(answer, "BE")
    bigrams = repeated_ngrams(words, 2)
    trigrams = repeated_ngrams(words, 3)

    if connected_positions_0 != (1131, 1277):
        raise AssertionError("BEREQUIRED connected offsets drifted")
    if word_positions_0 != (256, 283):
        raise AssertionError("BE REQUIRED README word offsets drifted")

    film = " ".join(SRT_PATH.read_text(encoding="utf-8", errors="replace").upper().split())
    inherited_phrase = "AFTER WHICH YOU WILL BE REQUIRED TO SELECT"
    creator_phrase = "BRUTE FORCING MIGHT BE REQUIRED"
    provenance = (
        {
            "occurrence": 1,
            "classification": "Matrix-inherited sentence skeleton",
            "film_contains_phrase": inherited_phrase in film,
            "phrase": inherited_phrase,
        },
        {
            "occurrence": 2,
            "classification": "creator-added method warning",
            "film_contains_phrase": creator_phrase in film,
            "phrase": creator_phrase,
        },
    )
    if not provenance[0]["film_contains_phrase"] or provenance[1]["film_contains_phrase"]:
        raise AssertionError("film provenance classification drifted")

    repeated_bigram_values = tuple(tuple(row["words"]) for row in bigrams)
    for gram in MIXED_PROVENANCE_REPEATED_BIGRAMS:
        if gram not in repeated_bigram_values:
            raise AssertionError(f"mixed-provenance comparator no longer repeats: {gram}")

    profile = guide_endpoint_profile()
    registered_mechanisms = (
        {
            "mechanism": "Phase 3.2.2 checkerboard escapes",
            "markers": tuple(VALIDATION_ESCAPES),
            "relation_to_two_be": "Numeric escapes (1,4), not two BE phrase markers.",
            "supplies_matching_consumer": False,
        },
        {
            "mechanism": "DBBI B/BE tokenization",
            "markers": ("B", "BE"),
            "relation_to_two_be": "A token alphabet/segmentation, not an instruction to use exactly two BE occurrences.",
            "supplies_matching_consumer": False,
        },
        {
            "mechanism": "split-final-BE guide",
            "markers": (profile["token_83"], profile["token_84"]),
            "relation_to_two_be": "One terminal BE token is split into B and E; it is not two BE tokens.",
            "supplies_matching_consumer": False,
        },
        {
            "mechanism": "Architect BUT/HYE choice extraction",
            "markers": ("BUT", "HYE"),
            "relation_to_two_be": "A solved dialogue-choice boundary with different markers and consumer.",
            "supplies_matching_consumer": False,
        },
    )

    criteria = {
        "exact_repetition_with_authenticated_letters": True,
        "unambiguous_operation_without_new_choices": False,
        "registered_consumer_independently_requires_two_markers": False,
        "not_duplicate_of_registered_mechanism": True,
    }
    promoted = all(criteria.values())

    return {
        "phase": 435,
        "word_boundary_authority": "README transcription; letters/order authenticated by fresh Beaufort derivation",
        "word_count": len(words),
        "connected_letter_count": len(answer),
        "be_required": {
            "count": len(connected_positions_0),
            "connected_positions_0": connected_positions_0,
            "connected_positions_1": tuple(position + 1 for position in connected_positions_0),
            "word_positions_0": word_positions_0,
            "word_positions_1": tuple(position + 1 for position in word_positions_0),
            "contexts": contexts(words, word_positions_0),
        },
        "be_counts": {
            "whole_word_be": len(be_word_positions_0),
            "whole_word_be_positions_0": be_word_positions_0,
            "raw_connected_be": len(raw_be_positions_0),
            "raw_connected_be_positions_0": raw_be_positions_0,
            "whole_word_be_required": len(word_positions_0),
        },
        "repeated_bigrams": bigrams,
        "repeated_trigrams": trigrams,
        "mixed_provenance_repeated_bigrams": MIXED_PROVENANCE_REPEATED_BIGRAMS,
        "be_required_unique_under_mixed_provenance_test": len(MIXED_PROVENANCE_REPEATED_BIGRAMS) == 1,
        "provenance": provenance,
        "registered_mechanisms": registered_mechanisms,
        "decision_criteria": criteria,
        "promoted": promoted,
        "classification": "real textual repetition, not an actionable selector",
        "reason": (
            "BE REQUIRED repeats exactly, but it does not define an operation or independently fixed consumer. "
            "RESULT IN is also a repeated mixed-provenance bigram, weakening uniqueness, and none of the four "
            "registered nearby mechanisms requires exactly two BE markers."
        ),
        "password_materials_generated": 0,
        "oracle_calls": 0,
        "gpu_touched": False,
    }


def self_test():
    report = audit()
    assert report["word_count"] == 336
    assert report["connected_letter_count"] == 1539
    assert report["be_required"]["connected_positions_0"] == (1131, 1277)
    assert report["be_required"]["connected_positions_1"] == (1132, 1278)
    assert report["be_required"]["word_positions_0"] == (256, 283)
    assert report["be_counts"]["whole_word_be"] == 3
    assert report["be_counts"]["raw_connected_be"] == 7
    assert len(report["repeated_bigrams"]) == 9
    assert report["repeated_trigrams"] == ()
    assert report["be_required_unique_under_mixed_provenance_test"] is False
    assert len(report["registered_mechanisms"]) == 4
    assert not report["promoted"]
    assert report["password_materials_generated"] == report["oracle_calls"] == 0
    assert report["gpu_touched"] is False
    print("[*] Phase 435 self-test OK: 2 BE REQUIRED, 9 repeated bigrams, 0 repeated trigrams, not promoted")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit()
    if args.self_test:
        self_test()
    payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    elif not args.self_test:
        print(payload, end="")


if __name__ == "__main__":
    main()
