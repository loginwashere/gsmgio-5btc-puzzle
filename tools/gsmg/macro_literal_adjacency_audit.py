#!/usr/bin/env python3
"""Audit literal local syntax around the creator macro's visibility clause.

This is deliberately not a password or cipher oracle.  It asks whether the
shortest possible reading of "the password ... in front of your eyes" selects
a value through source order alone.  Only contiguous bytes, immediate word
neighbors, and the two already-registered macro word segmentations are used.
"""

import argparse
import json
from pathlib import Path

from macro_clue_acrostic_audit import (
    WORD_SPLIT_COMPOUND,
    WORD_SPLIT_SPLIT_GIVEAWAY,
    all_words,
    verify_word_split,
)
from promised_standalone_audit import MACRO_CLUE
from salphaseion_title_rebus_audit import EXPECTED_MACRO, load_macro
from telegram_export_manifest import DEFAULT_EXPORT_DIR


ANCHORS = (
    "yinyang",
    "password",
    "youreyes",
    "eyesbut",
    "verylaststep",
    "truegiveaway",
    "promised",
)


def unique_span(text, needle):
    start = text.find(needle)
    if start < 0 or text.find(needle, start + 1) >= 0:
        raise AssertionError(f"anchor is absent or non-unique: {needle!r}")
    return (start, start + len(needle))


def neighbor(words, target):
    indexes = [index for index, word in enumerate(words) if word == target]
    if len(indexes) != 1:
        raise AssertionError(f"word is absent or non-unique: {target!r}")
    index = indexes[0]
    return {
        "index_zero_based": index,
        "previous": words[index - 1] if index else None,
        "next": words[index + 1] if index + 1 < len(words) else None,
    }


def word_report(split):
    verify_word_split(split)
    words = all_words(split)
    password_index = words.index("password")
    eyes_index = words.index("eyes")
    return {
        "word_count": len(words),
        "password": neighbor(words, "password"),
        "eyes": neighbor(words, "eyes"),
        "but": neighbor(words, "but"),
        "promised": neighbor(words, "promised"),
        "between_password_and_eyes": tuple(words[password_index + 1 : eyes_index]),
        "literal_your_eyes_but": tuple(words[eyes_index - 1 : eyes_index + 2]),
        "initials_your_eyes_but": "".join(
            word[0] for word in words[eyes_index - 1 : eyes_index + 2]
        ),
    }


def audit(export_path=DEFAULT_EXPORT_DIR / "result.json"):
    macro = load_macro(Path(export_path))
    if macro != EXPECTED_MACRO or macro != "".join(MACRO_CLUE):
        raise AssertionError("creator macro changed")

    spans = {anchor: unique_span(macro, anchor) for anchor in ANCHORS}
    password_end = spans["password"][1]
    your_eyes_start = spans["youreyes"][0]
    eyes_start = spans["eyesbut"][0]
    promised_start = spans["promised"][0]

    raw = {
        "length": len(macro),
        "spans": spans,
        "after_password_before_youreyes": macro[password_end:your_eyes_start],
        "after_password_before_eyes": macro[password_end:eyes_start],
        "immediately_before_youreyes": macro[your_eyes_start - 2 : your_eyes_start],
        "immediately_after_youreyes": macro[spans["youreyes"][1] : spans["youreyes"][1] + 3],
        "suffix_after_truegiveaway": macro[spans["truegiveaway"][1] :],
        "final_fragment": macro[promised_start:],
        "but_count": macro.count("but"),
        "hye_count": macro.count("hye"),
        "hyebut_count": macro.count("hyebut"),
    }

    compound = word_report(WORD_SPLIT_COMPOUND)
    split_giveaway = word_report(WORD_SPLIT_SPLIT_GIVEAWAY)
    stable_local_syntax = {
        key: compound[key]
        for key in (
            "password",
            "eyes",
            "but",
            "between_password_and_eyes",
            "literal_your_eyes_but",
            "initials_your_eyes_but",
        )
        if compound[key] == split_giveaway[key]
    }

    gates = {
        "authenticated_source": True,
        "contiguous_or_immediate_selection": True,
        "non_placeholder_password_value": False,
        "independent_consumer_binding": False,
    }
    if all(gates.values()):
        raise AssertionError("literal adjacency unexpectedly qualified")

    return {
        "raw": raw,
        "word_segmentations": {
            "giveaway_compound": compound,
            "give_away_split": split_giveaway,
        },
        "stable_local_syntax": stable_local_syntax,
        "gates": gates,
        "oracle_authorized": False,
        "verdict": (
            "Literal order confirms BUT immediately after 'your eyes' and "
            "PROMISED as the final fragment. Around PASSWORD it supplies only "
            "ordinary grammatical neighbors and the clause 'its in front of your'; "
            "it does not expose a password value. HYE and HYEBUT are absent, so "
            "the retracted H|YE|BUT construction cannot be recovered by adjacency."
        ),
    }


def self_test(export_path=DEFAULT_EXPORT_DIR / "result.json"):
    report = audit(export_path)
    assert report["raw"]["length"] == 161
    assert report["raw"]["after_password_before_youreyes"] == "itsinfrontof"
    assert report["raw"]["after_password_before_eyes"] == "itsinfrontofyour"
    assert report["raw"]["immediately_before_youreyes"] == "of"
    assert report["raw"]["immediately_after_youreyes"] == "but"
    assert report["raw"]["suffix_after_truegiveaway"] == "promised"
    assert report["raw"]["but_count"] == 1
    assert report["raw"]["hye_count"] == 0
    assert report["stable_local_syntax"]["literal_your_eyes_but"] == (
        "your", "eyes", "but"
    )
    assert report["stable_local_syntax"]["initials_your_eyes_but"] == "yeb"
    assert report["gates"]["non_placeholder_password_value"] is False
    assert report["oracle_authorized"] is False
    print(json.dumps(report, indent=2))
    print("[*] self-test OK: exact macro adjacency and two word splits verified")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--export",
        type=Path,
        default=DEFAULT_EXPORT_DIR / "result.json",
    )
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = self_test(args.export) if args.self_test else audit(args.export)
    if args.json and not args.self_test:
        print(json.dumps(report, indent=2))
    elif not args.self_test:
        print(report["verdict"])


if __name__ == "__main__":
    main()
