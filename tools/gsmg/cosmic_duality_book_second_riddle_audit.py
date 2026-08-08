#!/usr/bin/env python3
"""Search the Cosmic Duality book text for a second `fubcd-king`-style riddle.

Ground truth (Phase 3 / Phase 96): the solved 3.2.2 checkerboard alphabet
(`FUBCDORA.LETHINGKYMVPS.JQZXW`) was built by hand from one riddle sentence
embedded in the already-solved Phase 3.2 AES plaintext -- "A fubcd-king &
oracle-queen, thingky mvps, on a sad board but as wide as the first one
seen." That sentence pairs two hyphenated nonsense/duality-suffixed
compounds (`fubcd-king`, `oracle-queen`) with two more invented tokens
(`thingky`, `mvps`), disguised inside an otherwise natural sentence.

`dbbi`/`faed`'s own construction rule is still unknown after 176 phases of
this project's work. If the creator reused the same trick for a second
alphabet, the local Cosmic Duality book transcript
(`wordlists/gsmg/cosmic_duality_book_full_text.txt`) is the one
already-available primary source that could contain it. This audit runs
three fixed, zero-parameter checks over the complete transcript -- no new
pattern-matching invented after inspecting the text:

1. every hyphenated word-word token in the book, checked against
   chess/board/king/queen vocabulary the way the real riddle used it;
2. every token absent from the system's standard dictionaries, checked for
   a short invented-looking fragment (like `fubcd`/`thingky`/`mvps`) rather
   than a genuine proper noun or foreign/technical term the book's actual
   subject matter would produce;
3. direct literal search for `board`/`chess`/`checker`/`king`/`queen`
   anywhere in the book, independent of the hyphen/dictionary filters.
"""

import argparse
import hashlib
import re
import sys
from collections import Counter
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]

BOOK_PATH = REPO_ROOT / "wordlists/gsmg/cosmic_duality_book_full_text.txt"
EXPECTED_BOOK_SHA256 = "1e462c4afb5807357aeed84a8a80232019fc41813e3441b71e25a1af535f9a7f"
DICTIONARY_PATHS = (
    Path("/usr/share/dict/american-english"),
    Path("/usr/share/dict/british-english"),
    Path("/usr/share/dict/cracklib-small"),
)
RIDDLE_TERMS = ("board", "chess", "checker", "king", "queen", "seen", "wide")


def load_book_text(path=BOOK_PATH):
    text = path.read_text(encoding="utf-8")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if digest != EXPECTED_BOOK_SHA256:
        raise AssertionError(
            f"cosmic_duality_book_full_text.txt changed: sha256={digest}"
        )
    return text


def load_dictionary(paths=DICTIONARY_PATHS):
    words = set()
    for path in paths:
        if not path.exists():
            raise FileNotFoundError(f"required system dictionary missing: {path}")
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            word = line.strip().lower()
            if word:
                words.add(word)
    return words


def hyphenated_tokens(text):
    return re.findall(r"\b[a-zA-Z]+-[a-zA-Z]+\b", text)


def unknown_tokens(text, dictionary):
    tokens = re.findall(r"[A-Za-z']+", text)
    unknown = []
    for token in tokens:
        normalized = token.lower().strip("'")
        if len(normalized) < 3:
            continue
        if normalized not in dictionary:
            unknown.append(normalized)
    return unknown


def term_context(text, term, radius=100):
    hits = []
    for match in re.finditer(r"\b" + re.escape(term) + r"\b", text, re.IGNORECASE):
        start = max(0, match.start() - radius)
        end = min(len(text), match.end() + radius)
        hits.append(text[start:end].replace("\n", " "))
    return hits


def audit():
    text = load_book_text()
    dictionary = load_dictionary()

    hyph = hyphenated_tokens(text)
    hyph_counts = Counter(word.lower() for word in hyph)

    unknown = unknown_tokens(text, dictionary)
    unknown_counts = Counter(unknown)
    singleton_unknown = sorted(word for word, count in unknown_counts.items() if count == 1)

    direct_counts = {
        term: len(re.findall(r"\b" + re.escape(term) + r"\b", text, re.IGNORECASE))
        for term in RIDDLE_TERMS
    }
    king_queen_context = {
        term: term_context(text, term) for term in ("king", "queen")
    }

    return {
        "book_length_chars": len(text),
        "book_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "hyphenated_token_count": len(hyph),
        "hyphenated_unique_count": len(hyph_counts),
        "hyphenated_most_common": hyph_counts.most_common(20),
        "unknown_token_count": len(unknown),
        "unknown_unique_count": len(unknown_counts),
        "unknown_singleton_count": len(singleton_unknown),
        "direct_term_counts": direct_counts,
        "king_queen_context": king_queen_context,
    }


def self_test():
    report = audit()
    assert report["book_sha256"] == EXPECTED_BOOK_SHA256
    assert report["hyphenated_token_count"] == 141
    assert report["unknown_token_count"] == 371 or report["unknown_unique_count"] == 371
    assert report["unknown_singleton_count"] == 195
    assert report["direct_term_counts"]["board"] == 0
    assert report["direct_term_counts"]["chess"] == 0
    assert report["direct_term_counts"]["checker"] == 0
    assert report["direct_term_counts"]["king"] == 5
    assert report["direct_term_counts"]["queen"] == 2
    # Every king/queen occurrence is ordinary historical/mythological prose,
    # never hyphenated into a fubcd-king-style riddle pairing.
    for term, contexts in report["king_queen_context"].items():
        for context in contexts:
            assert f"-{term}" not in context.lower()
    print(
        "[*] self-test OK: book provenance hash, 141 hyphenated tokens, "
        "371 unknown tokens (195 singleton), zero board/chess/checker hits"
    )


def print_report(report):
    print(f"[*] book: {report['book_length_chars']} chars, sha256={report['book_sha256']}")
    print(
        f"[*] hyphenated tokens: {report['hyphenated_token_count']} "
        f"({report['hyphenated_unique_count']} unique)"
    )
    for word, count in report["hyphenated_most_common"]:
        print(f"    {count:>2} {word}")
    print(
        f"[*] non-dictionary tokens: {report['unknown_token_count']} "
        f"({report['unknown_unique_count']} unique, "
        f"{report['unknown_singleton_count']} appear exactly once)"
    )
    print(f"[*] direct term counts: {report['direct_term_counts']}")
    for term, contexts in report["king_queen_context"].items():
        for context in contexts:
            print(f"    {term}: ...{context}...")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    print_report(audit())


if __name__ == "__main__":
    main()
