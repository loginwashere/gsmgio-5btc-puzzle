#!/usr/bin/env python3
"""Generates every order-sensitive combination of the 8 creator-authored macro-clue
fragments (promised_standalone_audit.MACRO_CLUE), choosing 1..7 of the 8 fragments
per combination (P(8,k) for k=1..7, no repeats within one combination), concatenated
directly with no separator.

Scope rationale (2026-08-19 chat): these 8 fragments are the only strings this
project's own Phase 79/111 work established as literally the creator's own
authored text (decoded from their binary Telegram message), as opposed to
solver-derived numeric artifacts or third-party movie-quote reconstructions
(BUT/HYE/EOL etc., already covered by a different bounded family -- see
GSMG_MATRIXSUMLIST_CHECKPOINT.md). k=8 (all 8 fragments, one more order of
magnitude of permutations) is deliberately excluded -- if this bounded sweep is
negative, re-open k=8 explicitly rather than silently including it here.

`wordlists/gsmg/macro_clue_permutation_combinations.txt` is a generated output,
gitignored like this project's other derived candidate corpora; regenerate with
`--write` rather than hand-editing it.
"""

import argparse
import hashlib
import itertools
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from promised_standalone_audit import MACRO_CLUE  # noqa: E402

WORDLIST_DIR = SCRIPT_DIR.parent.parent / "wordlists" / "gsmg"
OUTPUT_PATH = WORDLIST_DIR / "macro_clue_permutation_combinations.txt"

MIN_K = 1
MAX_K = 7  # deliberately < len(MACRO_CLUE) == 8; see module docstring


def generate():
    for k in range(MIN_K, MAX_K + 1):
        for perm in itertools.permutations(MACRO_CLUE, k):
            yield "".join(perm)


def expected_count():
    import math

    n = len(MACRO_CLUE)
    return sum(math.perm(n, k) for k in range(MIN_K, MAX_K + 1))


def digest(lines):
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()[:16]


def self_test():
    assert MACRO_CLUE == (
        "yellowblueprimes",
        "matrixsumlist",
        "lastwordsbeforearchichoice",
        "yinyang",
        "wewontgiveawaythepassword",
        "itsinfrontofyoureyesbutyourenotseeingit",
        "verylaststepisatruegiveaway",
        "promised",
    ), "MACRO_CLUE changed upstream -- re-derive expected_count() / scope note above"

    lines = list(generate())
    assert len(lines) == expected_count() == 69280, f"got {len(lines)}, expected 69280"
    assert len(set(lines)) == len(lines), "duplicate combination produced"
    # Every line must be an exact concatenation of a subset (no repeats) of MACRO_CLUE.
    frag_set = set(MACRO_CLUE)
    for line in lines[:200]:  # spot-check, not all 69,280, for self-test speed
        remaining = line
        used = []
        while remaining:
            for f in frag_set:
                if remaining.startswith(f) and f not in used:
                    used.append(f)
                    remaining = remaining[len(f):]
                    break
            else:
                raise AssertionError(f"combination {line!r} does not decompose into MACRO_CLUE fragments")
    print(f"[*] self-test OK: {len(lines)} unique combinations, digest={digest(lines)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true", help=f"write {OUTPUT_PATH}")
    args = parser.parse_args()

    if args.self_test or not args.write:
        self_test()
    if args.write:
        WORDLIST_DIR.mkdir(parents=True, exist_ok=True)
        lines = list(generate())
        OUTPUT_PATH.write_text("\n".join(lines) + "\n")
        print(f"[*] wrote {len(lines)} lines to {OUTPUT_PATH}, digest={digest(lines)}")


if __name__ == "__main__":
    main()
