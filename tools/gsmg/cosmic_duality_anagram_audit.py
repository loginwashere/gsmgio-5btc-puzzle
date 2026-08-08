#!/usr/bin/env python3
"""Has `COSMIC DUALITY` itself -- the page's own theme heading, not
`SalPhaseIon` -- ever been run through an open-ended dictionary anagram
search? Checked (2026-08-08): no. `salphaseion_aphelion_anagram_audit.py`
(Phase 148) checked whether `APHELION` fits `SalPhaseIon`'s letters, and
`salvation_anagram_audit.py` (Phase 159) searched `SALVATION`'s own 9-letter
multiset -- but every prior mention of `Cosmic Duality`'s own 13-letter
multiset (Phase 153) only ever checked whether one specific *other* word
(`perihelion`) fits it, never searched it the way Phase 159 searched
SALVATION. This module runs that same technique -- full dictionary
anagrams, sub-anagram base rate, and exact two-word full-anagram phrase
pairs -- against `COSMICDUALITY`'s own letters, reusing
`salvation_anagram_audit.py`'s exact functions rather than duplicating them.
"""

import argparse
from pathlib import Path

from salvation_anagram_audit import (
    SYSTEM_DICT_PATH,
    full_anagrams,
    load_dictionary,
    sub_anagrams,
    two_word_full_anagrams,
)

TARGET_WORD = "cosmicduality"


def audit(dict_path=SYSTEM_DICT_PATH):
    words = load_dictionary(dict_path)
    full = full_anagrams(words, target=TARGET_WORD)
    subs = sub_anagrams(words, target=TARGET_WORD)
    pairs = two_word_full_anagrams(words, target=TARGET_WORD)
    return {
        "target": TARGET_WORD,
        "target_letters": "".join(sorted(TARGET_WORD)),
        "dictionary_size": len(words),
        "full_anagrams": full,
        "sub_anagram_count": len(subs),
        "sub_anagrams_top": subs[:20],
        "two_word_pair_count": len(pairs),
        "two_word_pairs_sample": pairs[:20],
    }


def print_report(report):
    print(f"[*] target: {report['target']!r} (letters: {report['target_letters']})")
    print(f"[*] dictionary size: {report['dictionary_size']}")
    print(f"[*] full 13-letter dictionary anagrams (exact multiset match): {report['full_anagrams']}")
    print(f"[*] sub-anagram dictionary words (len>=3): {report['sub_anagram_count']} total")
    for w in report["sub_anagrams_top"]:
        print(f"    {w}")
    print(f"[*] exact two-word full-anagram phrase pairs: {report['two_word_pair_count']} total")
    for pair in report["two_word_pairs_sample"]:
        print(f"    {pair}")


def self_test():
    report = audit()
    assert report["target_letters"] == "".join(sorted(TARGET_WORD))
    assert report["sub_anagram_count"] > 0, "expected at least some sub-anagram words"
    print(
        f"[*] self-test OK: {report['sub_anagram_count']} sub-anagram words, "
        f"{report['two_word_pair_count']} two-word full-anagram pairs found "
        "for COSMICDUALITY's 13-letter multiset"
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dict", type=Path, default=SYSTEM_DICT_PATH)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return

    report = audit(args.dict)
    print_report(report)


if __name__ == "__main__":
    main()
