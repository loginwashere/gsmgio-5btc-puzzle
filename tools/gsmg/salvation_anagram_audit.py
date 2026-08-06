#!/usr/bin/env python3
"""Item 1 follow-up (`doc/GSMG_FRESH_BRAINSTORM_2026-08-06.md` section 1):
has `SALVATION` itself -- the word Phases 96-99 derived from `SalPhaseIon`
via the `PHASE -> VAT` letter-replacement rebus, and Phase 105 read as a
fixed 3x3 letter grid under 8 deterministic orderings -- ever been run
through an open-ended dictionary anagram search the way Phase 148 did for
the *heading itself* (`SalPhaseIon -> APHELION`)? Checked: no. Every prior
SALVATION phase either derives the word (Phases 96/97) or applies a fixed,
motivated reading to its letters (Phase 105's 8 grid orderings); none asks
what else the 9-letter multiset `{s,a,a,l,v,t,i,o,n}` can spell.

This module answers that directly: (1) whether any *other* dictionary word
shares SALVATION's exact 9-letter multiset, (2) the dictionary base rate of
sub-anagram words at every length, and (3) how many exact two-word phrase
anagrams exist (splitting all 9 letters across two dictionary words) --
the same class of search Denis Golovkin ran (unsuccessfully, "trillions of
anagrams") over the much longer 31-character DBBI selection, but here
exhaustively tractable at only 9 letters.
"""

import argparse
from collections import Counter
from pathlib import Path

TARGET_WORD = "salvation"
SYSTEM_DICT_PATH = Path("/usr/share/dict/words")
MIN_SUB_LEN = 3
MIN_PAIR_WORD_LEN = 2


def load_dictionary(dict_path=SYSTEM_DICT_PATH):
    words = []
    with dict_path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            word = line.strip()
            if word.isalpha():
                words.append(word)
    return words


def sub_anagram(counts, word):
    word_counts = Counter(word)
    return all(counts[ch] >= n for ch, n in word_counts.items())


def leftover_counts(counts, word):
    remainder = Counter(counts)
    remainder.subtract(Counter(word))
    if any(v < 0 for v in remainder.values()):
        raise ValueError(f"{word!r} is not a sub-anagram")
    return remainder


def full_anagrams(words, target=TARGET_WORD):
    target_counts = Counter(target)
    return sorted(
        {w for w in words if len(w) == len(target) and Counter(w.lower()) == target_counts},
        key=str.lower,
    )


def sub_anagrams(words, target=TARGET_WORD, min_len=MIN_SUB_LEN):
    target_counts = Counter(target)
    hits = [w for w in words if len(w) >= min_len and sub_anagram(target_counts, w.lower())]
    return sorted(hits, key=lambda w: (-len(w), w.lower()))


def two_word_full_anagrams(words, target=TARGET_WORD, min_word_len=MIN_PAIR_WORD_LEN):
    target_counts = Counter(target)
    candidates = [w for w in words if len(w) >= min_word_len and sub_anagram(target_counts, w.lower())]
    by_letters = {}
    for w in candidates:
        key = "".join(sorted(w.lower()))
        by_letters.setdefault(key, []).append(w)

    pairs = set()
    for w1 in candidates:
        remainder = leftover_counts(target_counts, w1.lower())
        rem_key = "".join(sorted(ch * n for ch, n in remainder.items() if n > 0))
        if not rem_key or rem_key not in by_letters:
            continue
        for w2 in by_letters[rem_key]:
            pairs.add(tuple(sorted((w1.lower(), w2.lower()))))
    return sorted(pairs)


def audit(dict_path=SYSTEM_DICT_PATH):
    words = load_dictionary(dict_path)
    full = full_anagrams(words)
    subs = sub_anagrams(words)
    pairs = two_word_full_anagrams(words)
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
    print(f"[*] full 9-letter dictionary anagrams (exact multiset match): {report['full_anagrams']}")
    print(
        f"[*] sub-anagram dictionary words (len>={MIN_SUB_LEN}): "
        f"{report['sub_anagram_count']} total"
    )
    for w in report["sub_anagrams_top"]:
        print(f"    {w}")
    print(
        f"[*] exact two-word full-anagram phrase pairs: {report['two_word_pair_count']} total"
    )
    for pair in report["two_word_pairs_sample"]:
        print(f"    {pair}")


def self_test():
    report = audit()
    assert report["full_anagrams"] == ["salvation"], report["full_anagrams"]
    assert report["sub_anagram_count"] > 200
    assert report["two_word_pair_count"] > 50
    print(
        "[*] self-test OK: SALVATION is the unique 9-letter dictionary anagram "
        f"of its own letters ({report['sub_anagram_count']} sub-anagram words, "
        f"{report['two_word_pair_count']} two-word full-anagram pairs -- too "
        "large a base rate to treat any single sub-anagram as signal)"
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dict", type=Path, default=SYSTEM_DICT_PATH)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()

    report = audit(args.dict)
    print_report(report)


if __name__ == "__main__":
    main()
