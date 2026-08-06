#!/usr/bin/env python3
"""Acrostic/telestich test on the 2023-02-23 reversed-binary macro clue.

Chat question: "what if we split every word and check every first or last
letter, other technic?" Never tried in this project (grepped FINDINGS.md for
acrostic/first letter/last letter -- zero hits) despite the macro clue having
been worked over extensively at the fragment level since Phase 7.

The creator's decoded string has no authored spaces -- it is one 165-char
run. This module declares an explicit word-level split of each of the 8
known fragments (reusing the exact fragment strings from
promised_standalone_audit.MACRO_CLUE, not re-typing them) and asserts each
split's concatenation reproduces the fragment exactly before doing anything
else with it -- the same "declare and verify structure first" pattern this
project uses throughout.

Two things are then computed, at two granularities:

  - Word-level: first letter of every one of the ~38-39 words in order
    (acrostic), and last letter of every word in order (telestich).
  - Fragment-level: first/last letter of each of the 8 fragments treated as
    one "word" apiece -- the coarser, cheaper version of the same idea.

The final fragment ("verylaststepisatruegiveaway") is ambiguous between
"giveaway" (one word, a noun) and "give away" (two words, a verb phrase) --
the chat's own manual transcriptions used both (see FINDINGS.md's Phase 110
neighbourhood). Both segmentations are tested rather than picking one
arbitrarily.

All of this is bounded, declared-before-testing candidate generation -- not
a new cipher hypothesis -- straight into the same oracle every prior
candidate in this project has used.
"""

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from promised_standalone_audit import MACRO_CLUE  # noqa: E402
from cb_common import (  # noqa: E402
    BLOBS,
    EXTENDED_CIPHER_VARIANTS,
    QUARANTINED_BLOBS,
    aes_keywrap_try_open_bytes,
    aes_try_open,
    aes_try_open_ecb,
    aes_try_open_stream,
    answer_forms,
    keystr_forms,
)

# Word-level split per fragment, "giveaway" as one compound word.
WORD_SPLIT_COMPOUND = {
    "yellowblueprimes": ["yellow", "blue", "primes"],
    "matrixsumlist": ["matrix", "sum", "list"],
    "lastwordsbeforearchichoice": ["last", "words", "before", "archi", "choice"],
    "yinyang": ["yin", "yang"],
    "wewontgiveawaythepassword": ["we", "wont", "give", "away", "the", "password"],
    "itsinfrontofyoureyesbutyourenotseeingit": [
        "its", "in", "front", "of", "your", "eyes", "but", "youre", "not",
        "seeing", "it",
    ],
    "verylaststepisatruegiveaway": ["very", "last", "step", "is", "a", "true", "giveaway"],
    "promised": ["promised"],
}

# Same, but the final fragment splits "giveaway" -> "give", "away" (matches
# how the chat itself manually transcribed this fragment in several posts).
WORD_SPLIT_SPLIT_GIVEAWAY = dict(WORD_SPLIT_COMPOUND)
WORD_SPLIT_SPLIT_GIVEAWAY["verylaststepisatruegiveaway"] = [
    "very", "last", "step", "is", "a", "true", "give", "away",
]

EXPECTED_FRAGMENT_ORDER = (
    "yellowblueprimes",
    "matrixsumlist",
    "lastwordsbeforearchichoice",
    "yinyang",
    "wewontgiveawaythepassword",
    "itsinfrontofyoureyesbutyourenotseeingit",
    "verylaststepisatruegiveaway",
    "promised",
)


def verify_word_split(word_split):
    for fragment in EXPECTED_FRAGMENT_ORDER:
        words = word_split[fragment]
        joined = "".join(words)
        if joined != fragment:
            raise AssertionError(
                f"word split for {fragment!r} does not reconstruct it: {joined!r}"
            )
    return word_split


def all_words(word_split):
    words = []
    for fragment in EXPECTED_FRAGMENT_ORDER:
        words.extend(word_split[fragment])
    return words


def acrostic(words):
    return "".join(word[0] for word in words)


def telestich(words):
    return "".join(word[-1] for word in words)


def audit():
    if MACRO_CLUE != EXPECTED_FRAGMENT_ORDER:
        raise AssertionError("MACRO_CLUE fragment order changed upstream")

    verify_word_split(WORD_SPLIT_COMPOUND)
    verify_word_split(WORD_SPLIT_SPLIT_GIVEAWAY)

    words_compound = all_words(WORD_SPLIT_COMPOUND)
    words_split = all_words(WORD_SPLIT_SPLIT_GIVEAWAY)

    word_acrostic_compound = acrostic(words_compound)
    word_telestich_compound = telestich(words_compound)
    word_acrostic_split = acrostic(words_split)
    word_telestich_split = telestich(words_split)

    fragment_acrostic = acrostic(EXPECTED_FRAGMENT_ORDER)
    fragment_telestich = telestich(EXPECTED_FRAGMENT_ORDER)

    return {
        "word_count_compound": len(words_compound),
        "word_count_split": len(words_split),
        "word_acrostic_compound": word_acrostic_compound,
        "word_telestich_compound": word_telestich_compound,
        "word_acrostic_split": word_acrostic_split,
        "word_telestich_split": word_telestich_split,
        "fragment_acrostic": fragment_acrostic,
        "fragment_telestich": fragment_telestich,
    }


def candidate_family(report):
    return (
        report["word_acrostic_compound"],
        report["word_telestich_compound"],
        report["word_acrostic_split"],
        report["word_telestich_split"],
        report["fragment_acrostic"],
        report["fragment_telestich"],
    )


def oracle_check(candidates, blobs):
    tested = set()
    hits = {"cbc": [], "ecb": [], "stream": [], "keywrap": []}
    for candidate in candidates:
        for form in sorted(answer_forms(candidate)):
            for keystring in keystr_forms(form, newline_variants=True):
                if keystring in tested:
                    continue
                tested.add(keystring)
                for variants in (None, EXTENDED_CIPHER_VARIANTS):
                    result = aes_try_open(keystring, kdf_variants=variants, blobs=blobs)
                    if result:
                        hits["cbc"].append((candidate, keystring, result))
                result = aes_try_open_ecb(keystring, blobs=blobs)
                if result:
                    hits["ecb"].append((candidate, keystring, result))
                result = aes_try_open_stream(keystring, blobs=blobs)
                if result:
                    hits["stream"].append((candidate, keystring, result))
                for result in aes_keywrap_try_open_bytes(keystring.encode(), blobs=blobs):
                    hits["keywrap"].append((candidate, keystring, result))
    return {
        "candidate_count": len(candidates),
        "unique_keystrings": len(tested),
        "blob_count": len(blobs),
        "hits": hits,
    }


def print_report(report):
    print(f"[*] words (giveaway compound): {report['word_count_compound']}")
    print(f"[*] words (give away split):   {report['word_count_split']}")
    print(f"[*] word acrostic  (compound): {report['word_acrostic_compound']}")
    print(f"[*] word telestich (compound): {report['word_telestich_compound']}")
    print(f"[*] word acrostic  (split):    {report['word_acrostic_split']}")
    print(f"[*] word telestich (split):    {report['word_telestich_split']}")
    print(f"[*] fragment acrostic (8):     {report['fragment_acrostic']}")
    print(f"[*] fragment telestich (8):    {report['fragment_telestich']}")


def self_test():
    report = audit()
    assert report["word_count_compound"] == 38
    assert report["word_count_split"] == 39
    assert len(report["word_acrostic_compound"]) == 38
    assert len(report["word_telestich_compound"]) == 38
    assert len(report["word_acrostic_split"]) == 39
    assert len(report["word_telestich_split"]) == 39
    assert report["fragment_acrostic"] == "ymlywivp"
    assert report["fragment_telestich"] == "stegdtyd"
    print("[*] self-test OK: word split verified, acrostic/telestich strings computed")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--oracle", action="store_true")
    parser.add_argument("--include-quarantined", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()

    report = audit()
    print_report(report)

    if args.oracle:
        blobs = dict(BLOBS)
        if args.include_quarantined:
            blobs.update(QUARANTINED_BLOBS)
        result = oracle_check(candidate_family(report), blobs)
        total_hits = sum(len(v) for v in result["hits"].values())
        print(
            f"[*] oracle: candidates={result['candidate_count']} "
            f"unique_keystrings={result['unique_keystrings']} "
            f"blobs={result['blob_count']} hits={total_hits}"
        )
        for family, family_hits in result["hits"].items():
            print(f"    {family}: {len(family_hits)}")
            for hit in family_hits:
                print(f"      {hit!r}")


if __name__ == "__main__":
    main()
