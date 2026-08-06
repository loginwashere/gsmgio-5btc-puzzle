#!/usr/bin/env python3
"""Generate 'content-word-only' candidate keyword seeds from prose sources.

Motivation (2026-07-13): 3.2.2's real riddle sentence ("A fubcd-king & oracle-queen,
thingky mvps, on a sad board but as wide as the first one seen") does NOT reproduce its
known-good alphabet when run whole through pad28()'s generic first-occurrence-letter
dedup (already established in doc/GSMG_PUZZLE.md's 2026-07-03 entry). It only works if
you first drop every non-content word (articles, conjunctions, prepositions, the
"-king"/"-queen" chess-metaphor suffixes) and concatenate just the four content-bearing
tokens ("fubcd", "oracle", "thingky", "mvps") before deduping.

That means every previous sweep that fed a *whole prose sentence* (book passages, Matrix
script windows, chat lines) through pad25()/pad28() as-is was testing a mechanism that
structurally cannot reproduce the real alphabet-construction rule, regardless of whether
the sentence's content was right. This script closes that specific tooling gap: it
strips a curated English stopword list from each source line and emits the
concatenated content words as a new candidate, alongside the untouched original (so both
mechanisms get tested).

Does NOT attempt to guess coined/invented words the way "fubcd"/"thingky"/"mvps" were
coined for 3.2.2 -- those are fundamentally unguessable from any wordlist. This only
tests the hypothesis that the Cosmic Duality riddle (if it exists) uses REAL words as
its content anchors.
"""
import re
import sys
from pathlib import Path

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "of", "to", "in", "on", "at", "for", "with",
    "from", "by", "as", "is", "are", "was", "were", "be", "been", "being", "that",
    "this", "these", "those", "it", "its", "his", "her", "their", "our", "your", "my",
    "i", "you", "he", "she", "they", "we", "not", "no", "so", "if", "than", "then",
    "when", "while", "such", "some", "both", "each", "all", "most", "more", "very",
    "also", "only", "just", "like", "near", "far", "above", "below", "between",
    "through", "into", "onto", "upon", "about", "against", "before", "after", "over",
    "under", "again", "further", "once", "here", "there", "where", "why", "how", "who",
    "whom", "which", "what", "do", "does", "did", "done", "doing", "have", "has", "had",
    "having", "will", "would", "shall", "should", "may", "might", "must", "can",
    "could", "up", "down", "out", "off", "own", "even", "still", "yet", "too",
}


def content_words(line: str):
    words = re.findall(r"[A-Za-z']+", line.lower())
    return [w for w in words if w not in STOPWORDS and len(w) > 1]


def filtered_candidate(line: str) -> str:
    return "".join(content_words(line))


def generate(sources):
    seen = set()
    out = []
    for path in sources:
        p = Path(path)
        if not p.exists():
            print(f"[!] missing: {path}", file=sys.stderr)
            continue
        for raw in p.read_text(encoding="utf-8", errors="replace").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            for cand in (raw, filtered_candidate(raw)):
                cand = re.sub(r"[^A-Za-z]", "", cand)
                if len(cand) >= 4 and cand.lower() not in seen:
                    seen.add(cand.lower())
                    out.append(cand)
    return out


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("sources", nargs="+", help="text files, one candidate line per line")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    cands = generate(args.sources)
    Path(args.out).write_text("\n".join(cands) + "\n")
    print(f"[*] wrote {len(cands)} candidates to {args.out}")
