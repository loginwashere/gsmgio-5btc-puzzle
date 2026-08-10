#!/usr/bin/env python3
"""Stress-test ``SalPhaseIon + T -> SaltPhaseIon`` without editorial case.

The creator's decoded macro is lowercase and contains ``true``.  This audit
therefore gives every distinct letter of that source word the same chance at
every insertion position in the title, then reports every exact three-word
dictionary segmentation.  It does not choose SALT because the blob header is
already known; the header is retained only as an independent recognition
property after the complete family is enumerated.
"""

import argparse
import hashlib
import json
from pathlib import Path

from cb_common import BLOBS, QUARANTINED_BLOBS
from salphaseion_presentation_binding_audit import audit as presentation_audit
from salphaseion_title_rebus_audit import EXPECTED_MACRO


TITLE = "salphaseion"
SOURCE_WORD = "true"
DEFAULT_DICTIONARY = Path("/usr/share/dict/words")
EXPECTED_DICTIONARY_SHA256 = (
    "9f513f1ceadb6a01c5485b7dbdfd5118dc66cd70b59cae2851292112d4066a32"
)
EXPECTED_READINGS = (
    ("t", 3, "saltphaseion", ("salt", "phase", "ion")),
    ("r", 5, "salphraseion", ("sal", "phrase", "ion")),
    ("r", 9, "salphaseiron", ("sal", "phase", "iron")),
    ("u", 2, "saulphaseion", ("saul", "phase", "ion")),
    ("e", 1, "sealphaseion", ("seal", "phase", "ion")),
    ("e", 3, "salephaseion", ("sale", "phase", "ion")),
)


def load_words(path):
    raw = Path(path).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_DICTIONARY_SHA256:
        raise AssertionError("dictionary corpus changed")
    words = {
        line.strip().lower()
        for line in raw.decode("utf-8", errors="ignore").splitlines()
        if line.strip().isalpha() and len(line.strip()) >= 2
    }
    return words, digest


def three_word_splits(value, words):
    readings = []
    for first_end in range(2, len(value) - 3):
        for second_end in range(first_end + 2, len(value) - 1):
            parts = (
                value[:first_end],
                value[first_end:second_end],
                value[second_end:],
            )
            if all(part in words for part in parts):
                readings.append(parts)
    return tuple(readings)


def enumerate_readings(words):
    rows = []
    for letter in dict.fromkeys(SOURCE_WORD):
        for position in range(len(TITLE) + 1):
            candidate = TITLE[:position] + letter + TITLE[position:]
            for parts in three_word_splits(candidate, words):
                rows.append((letter, position, candidate, parts))
    return tuple(rows)


def audit(dictionary_path=DEFAULT_DICTIONARY):
    presentation = presentation_audit()
    if presentation["headings"][0] != "SalPhaseIon":
        raise AssertionError("authenticated title changed")
    if "atruegiveaway" not in EXPECTED_MACRO:
        raise AssertionError("lowercase creator macro tail changed")
    if "True" in EXPECTED_MACRO or "TRUE" in EXPECTED_MACRO:
        raise AssertionError("macro unexpectedly supplies authored T case")

    words, dictionary_hash = load_words(dictionary_path)
    readings = enumerate_readings(words)
    if readings != EXPECTED_READINGS:
        raise AssertionError(f"title insertion family changed: {readings!r}")

    salted_headers = tuple(
        tag for tag, (salt, _body) in BLOBS.items() if len(salt) == 8
    )
    authenticated_headers = tuple(
        tag for tag in salted_headers if tag not in QUARANTINED_BLOBS
    )
    salt_rows = tuple(row for row in readings if row[3][0] == "salt")
    boundary_rows = tuple(row for row in readings if row[1] in (3, 8))
    return {
        "source_title": "SalPhaseIon",
        "source_macro_word": SOURCE_WORD,
        "macro_authored_case": "lowercase",
        "family_size": len(dict.fromkeys(SOURCE_WORD)) * (len(TITLE) + 1),
        "dictionary_sha256": dictionary_hash,
        "valid_three_word_readings": readings,
        "valid_reading_count": len(readings),
        "original_camel_boundary_readings": boundary_rows,
        "salt_readings": salt_rows,
        "openssl_salted_envelope_count": len(salted_headers),
        "openssl_salted_envelope_tags": salted_headers,
        "authenticated_envelope_tags": authenticated_headers,
        "quarantined_envelope_tags": tuple(
            tag for tag in salted_headers if tag in QUARANTINED_BLOBS
        ),
        "selection_status": "recognizable_after_enumeration_but_not_source_unique",
        "missing_operation": (
            "a source-authored rule selecting t from lowercase true and insertion "
            "position 3, followed by a specified use of the recovered salt"
        ),
        "verdict": (
            "Salt|Phase|Ion is a strong bounded recognition because it is one "
            "of six dictionary-valid TRUE-letter insertions and uniquely "
            "resonates with the authenticated OpenSSL Salted__ envelopes "
            "(and the separately quarantined URLBLOB). It "
            "is not a uniquely instructed extraction: the macro supplies "
            "lowercase true, not an authored capital T, and even the original "
            "Sal|Phase boundary admits both Salt|Phase|Ion and "
            "Sale|Phase|Ion. Existing salt consumers remain negative, so this "
            "recognition does not bind a decoder."
        ),
    }


def self_test(dictionary_path=DEFAULT_DICTIONARY):
    report = audit(dictionary_path)
    assert report["family_size"] == 48
    assert report["valid_reading_count"] == 6
    assert len(report["original_camel_boundary_readings"]) == 2
    assert len(report["salt_readings"]) == 1
    assert len(report["authenticated_envelope_tags"]) == 3
    assert report["quarantined_envelope_tags"] == ("URLBLOB",)
    assert report["selection_status"].endswith("not_source_unique")
    print(json.dumps(report, indent=2))
    print("[*] self-test OK: SaltPhaseIon recognition is bounded but non-unique")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dictionary", type=Path, default=DEFAULT_DICTIONARY)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = self_test(args.dictionary) if args.self_test else audit(args.dictionary)
    if args.json and not args.self_test:
        print(json.dumps(report, indent=2))
    elif not args.self_test:
        print(report["verdict"])


if __name__ == "__main__":
    main()
