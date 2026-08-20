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

k=8 (Phase 331, 2026-08-20): the k=1..7 sweep above (Phase 322) came back
negative, so per this file's own reopen condition, k=8 is now run -- as a
separate, explicitly opt-in generator (`--k8`/`--write-k8`), not by silently
raising MAX_K, matching this project's "opt-in, don't silently expand an
existing sweep" discipline (see e.g. SEED-CBC's `--seed-cbc` flag). k=8 has
exactly one combination per permutation (all 8 fragments, no subset choice),
so it's P(8,8) = 8! = 40,320 base combinations -- written to its own output
file, `macro_clue_permutation_combinations_k8.txt`, so the k=1..7 corpus
Phase 322 already swept is never silently re-defined.
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
OUTPUT_PATH_K8 = WORDLIST_DIR / "macro_clue_permutation_combinations_k8.txt"

MIN_K = 1
MAX_K = 7  # deliberately < len(MACRO_CLUE) == 8; see module docstring
K8 = 8  # Phase 331's separate, opt-in k=8 generator -- see module docstring


def generate():
    for k in range(MIN_K, MAX_K + 1):
        for perm in itertools.permutations(MACRO_CLUE, k):
            yield "".join(perm)


def generate_k8():
    for perm in itertools.permutations(MACRO_CLUE, K8):
        yield "".join(perm)


def expected_count():
    import math

    n = len(MACRO_CLUE)
    return sum(math.perm(n, k) for k in range(MIN_K, MAX_K + 1))


def expected_count_k8():
    import math

    return math.perm(len(MACRO_CLUE), K8)


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


def self_test_k8():
    lines = list(generate_k8())
    assert len(lines) == expected_count_k8() == 40320, f"got {len(lines)}, expected 40320"
    assert len(set(lines)) == len(lines), "duplicate k=8 combination produced"
    # Every k=8 line must use ALL 8 fragments exactly once (no subset choice at k=8).
    frag_set = set(MACRO_CLUE)
    for line in lines[:200]:  # spot-check, not all 40,320, for self-test speed
        remaining = line
        used = []
        while remaining:
            for f in frag_set:
                if remaining.startswith(f) and f not in used:
                    used.append(f)
                    remaining = remaining[len(f):]
                    break
            else:
                raise AssertionError(f"k=8 combination {line!r} does not decompose into MACRO_CLUE fragments")
        assert len(used) == 8, f"k=8 combination {line!r} used {len(used)} fragments, not all 8"
    print(f"[*] k=8 self-test OK: {len(lines)} unique combinations, digest={digest(lines)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true", help=f"write {OUTPUT_PATH}")
    parser.add_argument("--k8", action="store_true", help="also run the k=8 self-test")
    parser.add_argument("--write-k8", action="store_true", help=f"write {OUTPUT_PATH_K8} (implies --k8)")
    args = parser.parse_args()

    if args.self_test or not (args.write or args.write_k8):
        self_test()
    if args.k8 or args.write_k8 or (args.self_test and not (args.write or args.write_k8)):
        self_test_k8()
    if args.write:
        WORDLIST_DIR.mkdir(parents=True, exist_ok=True)
        lines = list(generate())
        OUTPUT_PATH.write_text("\n".join(lines) + "\n")
        print(f"[*] wrote {len(lines)} lines to {OUTPUT_PATH}, digest={digest(lines)}")
    if args.write_k8:
        WORDLIST_DIR.mkdir(parents=True, exist_ok=True)
        lines = list(generate_k8())
        OUTPUT_PATH_K8.write_text("\n".join(lines) + "\n")
        print(f"[*] wrote {len(lines)} lines to {OUTPUT_PATH_K8}, digest={digest(lines)}")


if __name__ == "__main__":
    main()
