#!/usr/bin/env python3
"""Test the macro clue's final word, `promised`, standalone.

The ordered macro clue is:

    yellowblueprimes
    matrixsumlist
    lastwordsbeforearchichoice
    yinyang
    wewontgiveawaythepassword
    itsinfrontofyoureyesbutyourenotseeingit
    verylaststepisatruegiveaway
    promised

Every other fragment in this list has been consumed by some established
reading (`yellowblueprimes` -> the first-piece color reconstruction,
`matrixsumlist` -> the `[23,16,7]` matrix, `lastwordsbeforearchichoice` ->
the Architect dialogue selection, `verylaststepisatruegiveaway` -> the `VAT`
rebus). `promised` is the one fragment that has only ever been tested as
part of the *concatenated* macro-clue string, never checked on its own as a
direct candidate. That is a real, narrow gap, not a new hypothesis -- this
module closes it the same way every other single-word candidate in this
project has been closed: a small declared form family straight into the
existing oracle.

Not a new cipher family or a new idea about what `promised` means -- just
the missing standalone data point.
"""

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

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

WORD = "promised"
MACRO_CLUE = (
    "yellowblueprimes",
    "matrixsumlist",
    "lastwordsbeforearchichoice",
    "yinyang",
    "wewontgiveawaythepassword",
    "itsinfrontofyoureyesbutyourenotseeingit",
    "verylaststepisatruegiveaway",
    "promised",
)


def candidate_family(word):
    return tuple(
        dict.fromkeys(
            (
                word,
                word.upper(),
                word.lower(),
                word.capitalize(),
            )
        )
    )


def audit():
    if MACRO_CLUE[-1] != WORD:
        raise AssertionError("promised is no longer the final macro-clue fragment")
    return {
        "word": WORD,
        "position": len(MACRO_CLUE),
        "total_fragments": len(MACRO_CLUE),
        "candidates": candidate_family(WORD),
    }


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
    print(f"[*] word: {report['word']!r} (fragment {report['position']}/{report['total_fragments']} of the macro clue)")
    print("[*] candidates:")
    for candidate in report["candidates"]:
        print(f"    {candidate!r}")


def self_test():
    report = audit()
    assert report["word"] == "promised"
    assert report["position"] == 8
    assert "promised" in report["candidates"]
    assert "PROMISED" in report["candidates"]
    assert "Promised" in report["candidates"]
    assert len(report["candidates"]) == 3
    print("[*] self-test OK: promised is fragment 8/8, candidate family verified")
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
        result = oracle_check(report["candidates"], blobs)
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
