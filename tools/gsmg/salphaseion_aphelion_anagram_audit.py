#!/usr/bin/env python3
"""Test the `SalPhaseIon -> APHELION` sub-anagram reading (brainstorm item 1,
`doc/GSMG_FRESH_BRAINSTORM_2026-08-06.md` section 1).

Prior heading work (Phases 96-99, `salphaseion_title_rebus_audit.py`) tested an
exact case-sensitive *replacement*: `SalPhaseIon` differs from `SALVATION` by
exactly one substring (`PHASE` -> `VAT`), which is why that reading earned a
"unique replacement" claim. This script tests a structurally weaker claim --
that the archived heading's 11-letter multiset contains `APHELION` (the
astronomical "far point" counterpart to `perihelion`, and a thematically
tighter match to the page's own "Cosmic Duality" title than the chemistry
parse) as a *sub-anagram*, leaving `S`,`S`,`A` over.

Unlike the VAT rebus this is not a unique string difference -- many 8-letter
words could in principle be sub-anagrams of an 11-letter multiset. This script
therefore also runs a base-rate control (how many real dictionary words of the
same length are also sub-anagrams) before treating the match as notable, and
checks the creator's own corpus (full Telegram export + Cosmic Duality book
text) for either `aphelion` or `perihelion` before promoting this to a
candidate worth an oracle check at all.
"""

import argparse
import json
import re
import sys
from collections import Counter
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
from page_structure_audit import DEFAULT_HTML  # noqa: E402
from salphaseion_title_rebus_audit import load_title  # noqa: E402
from telegram_export_manifest import DEFAULT_EXPORT_DIR  # noqa: E402

BOOK_TEXT_PATH = (
    SCRIPT_DIR.parent.parent / "wordlists" / "gsmg" / "cosmic_duality_book_full_text.txt"
)
BOOK_OCR_PATH = (
    SCRIPT_DIR.parent.parent
    / "wordlists"
    / "gsmg"
    / "cosmic_duality_book_screenshot_ocr.txt"
)
SYSTEM_DICT_PATH = Path("/usr/share/dict/words")

EXPECTED_TITLE = "SalPhaseIon"
TARGET_WORD = "APHELION"
COMPANION_WORD = "PERIHELION"


def letters_only(value):
    return re.sub(r"[^A-Za-z]", "", value).lower()


def sub_anagram(source_letters, word):
    source_counts = Counter(source_letters)
    word_counts = Counter(word.lower())
    return all(source_counts[ch] >= count for ch, count in word_counts.items())


def leftover(source_letters, word):
    source_counts = Counter(source_letters)
    source_counts.subtract(Counter(word.lower()))
    if any(count < 0 for count in source_counts.values()):
        raise ValueError(f"{word!r} is not a sub-anagram of {source_letters!r}")
    return "".join(sorted(ch * count for ch, count in source_counts.items() if count > 0))


def flatten_text(value):
    if isinstance(value, str):
        return value
    return "".join(
        item if isinstance(item, str) else item.get("text", "")
        for item in value
    )


def corpus_mentions(export_path, book_paths, words):
    pattern = re.compile("|".join(re.escape(word) for word in words), re.IGNORECASE)
    hits = {word: [] for word in words}

    payload = json.loads(export_path.read_text(encoding="utf-8"))
    for message in payload["messages"]:
        text = flatten_text(message.get("text", ""))
        if pattern.search(text):
            for word in words:
                if word.lower() in text.lower():
                    hits[word].append(("telegram", message.get("id")))

    for book_path in book_paths:
        if not book_path.exists():
            continue
        text = book_path.read_text(encoding="utf-8", errors="replace")
        for word in words:
            if word.lower() in text.lower():
                hits[word].append((book_path.name, None))

    return hits


def dictionary_base_rate(source_letters, dict_path=SYSTEM_DICT_PATH, min_len=4):
    if not dict_path.exists():
        return None
    target_len = len(TARGET_WORD)
    same_length_hits = []
    all_hits = []
    with dict_path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            word = line.strip()
            if not word.isalpha() or len(word) < min_len:
                continue
            if not sub_anagram(source_letters, word):
                continue
            all_hits.append(word)
            if len(word) == target_len:
                same_length_hits.append(word)
    return {
        "min_len": min_len,
        "dictionary_size": sum(1 for _ in dict_path.open(encoding="utf-8", errors="replace")),
        "all_sub_anagrams": sorted(all_hits, key=len, reverse=True),
        "same_length_as_target": sorted(same_length_hits),
    }


def fixed_candidates(leftover_letters):
    leftover_upper = leftover_letters.upper()
    return (
        TARGET_WORD,
        leftover_upper,
        "".join(reversed(leftover_upper)),
        TARGET_WORD + leftover_upper,
        leftover_upper + TARGET_WORD,
        f"{TARGET_WORD} {leftover_upper}",
        f"{leftover_upper} {TARGET_WORD}",
    )


def oracle_check(candidates, blobs):
    tested_keystrings = set()
    hits = {"cbc": [], "ecb": [], "stream": [], "keywrap": []}
    for candidate in candidates:
        for form in sorted(answer_forms(candidate)):
            for keystring in keystr_forms(form, newline_variants=True):
                if keystring in tested_keystrings:
                    continue
                tested_keystrings.add(keystring)

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
        "unique_keystrings": len(tested_keystrings),
        "blob_count": len(blobs),
        "hits": hits,
    }


def audit(html_path, export_path):
    title = load_title(html_path)
    if title != EXPECTED_TITLE:
        raise AssertionError(f"unexpected archived title: {title!r}")

    source_letters = letters_only(title)
    if not sub_anagram(source_letters, TARGET_WORD):
        raise AssertionError(f"{TARGET_WORD} is not a sub-anagram of {title!r}")
    if sub_anagram(source_letters, COMPANION_WORD):
        raise AssertionError(
            f"{COMPANION_WORD} unexpectedly fits -- update the companion-word note"
        )

    remainder = leftover(source_letters, TARGET_WORD)
    mentions = corpus_mentions(
        export_path,
        (BOOK_TEXT_PATH, BOOK_OCR_PATH),
        (TARGET_WORD, COMPANION_WORD),
    )
    base_rate = dictionary_base_rate(source_letters)
    candidates = fixed_candidates(remainder)

    return {
        "title": title,
        "source_letters": "".join(sorted(source_letters)),
        "target_word": TARGET_WORD,
        "companion_word": COMPANION_WORD,
        "leftover": remainder,
        "corpus_mentions": mentions,
        "base_rate": base_rate,
        "candidates": candidates,
    }


def print_report(report):
    print(f"[*] archived title: {report['title']}")
    print(f"[*] title letters (sorted): {report['source_letters']}")
    print(
        f"[*] {report['target_word']} fits as a sub-anagram; "
        f"leftover = {report['leftover'].upper()!r}"
    )
    print(
        f"[*] companion word {report['companion_word']} does NOT fit "
        "(needs an R the heading lacks) -- not testable from this heading alone"
    )
    print("[*] corpus mentions (creator Telegram export + Cosmic Duality book text):")
    for word, hits in report["corpus_mentions"].items():
        print(f"    {word}: {len(hits)} mention(s){' ' + repr(hits) if hits else ''}")
    base_rate = report["base_rate"]
    if base_rate is None:
        print("[*] dictionary base-rate check: skipped (no system dictionary found)")
    else:
        print(
            f"[*] dictionary base-rate ({base_rate['dictionary_size']} words, "
            f"min_len={base_rate['min_len']}):"
        )
        print(
            f"    total sub-anagram words found: {len(base_rate['all_sub_anagrams'])}"
        )
        print(
            f"    same length as {report['target_word']} "
            f"({len(report['target_word'])} letters): "
            f"{len(base_rate['same_length_as_target'])} "
            f"{base_rate['same_length_as_target']}"
        )
    print(f"[*] fixed candidate family ({len(report['candidates'])}):")
    for candidate in report["candidates"]:
        print(f"    {candidate!r}")


def self_test():
    assert letters_only("SalPhaseIon") == "salphaseion"
    assert sub_anagram("salphaseion", "aphelion")
    assert leftover("salphaseion", "aphelion") == "ass"
    assert not sub_anagram("salphaseion", "perihelion")
    assert fixed_candidates("ass") == (
        "APHELION",
        "ASS",
        "SSA",
        "APHELIONASS",
        "ASSAPHELION",
        "APHELION ASS",
        "ASS APHELION",
    )
    print("[*] self-test OK: sub-anagram math and fixed candidates")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", type=Path, default=DEFAULT_HTML)
    parser.add_argument(
        "--export", type=Path, default=DEFAULT_EXPORT_DIR / "result.json"
    )
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--oracle", action="store_true")
    parser.add_argument("--include-quarantined", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()

    report = audit(args.html, args.export)
    print_report(report)

    if args.oracle:
        blobs = dict(BLOBS)
        if args.include_quarantined:
            blobs.update(QUARANTINED_BLOBS)
        result = oracle_check(report["candidates"], blobs)
        total_hits = sum(len(values) for values in result["hits"].values())
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
