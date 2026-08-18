#!/usr/bin/env python3
"""Lexical half of the "both" follow-up to `doc/Brainstorms/2026-08-17 - The
Warning (Logic) Phase 2-3 Meaning Close Read.md`.

That close read established: Logic's "The Warning" is a *confirmed* creator
source (not a guess) -- its opening lines are already the verified Stage 0/1
URL, icon-rebus answer, and Phase 1 form password (`doc/GSMG_PUZZLE.md` lines
78/91). Everything in the song from that point on (the rest of the "mold the
flower" list, the rose/no-in-between line, and the entire final section) has
never been tried as password/key material anywhere in this project. This
tests exactly that closed, bounded gap -- not a dictionary sweep.

Candidates (closed set, all derived directly from the song's own remaining
lines, normalized the identical way the *already-verified* Phase 1 password
was: lowercase, strip everything but letters -- see `doc/GSMG_PUZZLE.md:91`):
  - each remaining full line, normalized whole
  - the handful of short multi-word phrases within those lines, in the same
    short/compound style as this project's own existing `CORE_ALPHABET_SEEDS`
    (e.g. "causality", "architect", "lastwordsbeforearchichoice")

Two independent test paths, reusing this project's existing validated
machinery rather than new logic:
  1. Checkerboard alphabet seed (`pad25` + `decode_9ary`) against DBBI/FAED,
     scored with `matrixsum_permutation_sweep.text_score` -- directly
     comparable to that script's own established CORE_ALPHABET_SEEDS scores.
  2. AES password candidate (`answer_forms` + `keystr_forms` + `aes_try_open`)
     against SALPH/COSMIC/P32TRAILING/URLBLOB.

Reproduce with:
    python3 tools/gsmg/warning_song_remainder_keyword_audit.py --self-test
    python3 tools/gsmg/warning_song_remainder_keyword_audit.py
"""
import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from cb_common import BLOBS, answer_forms, keystr_forms, aes_try_open, decode_9ary, pad25  # noqa: E402
from matrixsum_permutation_sweep import CORE_ALPHABET_SEEDS, TARGET_ESCAPES, text_score  # noqa: E402

# Full remaining lines, normalized (lowercase, letters only) exactly like the
# already-verified Phase 1 password.
LINE_CANDIDATES = (
    "iegreedracisminsanityphysicalandsocialhandicaps",
    "thesearethethingsthatmoldtheflower",
    "redroseorblackrosenoinbetween",
    "thejudgement",
    "ifitweretofalluponyoutodaywhichflowerwouldyoube",
    "theredroseortheblack",
    "thisisthewarning",
)

# Short/compound-word candidates pulled from those lines, matching this
# project's existing CORE_ALPHABET_SEEDS style.
WORD_CANDIDATES = (
    "judgement", "warning", "redrose", "blackrose", "noinbetween",
    "moldtheflower", "whichflower", "greed", "racism", "insanity",
    "handicaps",
)

ALL_CANDIDATES = LINE_CANDIDATES + WORD_CANDIDATES


def checkerboard_pass():
    results = []
    from data import DBBI, FAED  # noqa: E402
    ciphertexts = {"dbbi": DBBI, "faed": FAED}
    for target_name, ciphertext in ciphertexts.items():
        for e1, e2 in TARGET_ESCAPES[target_name]:
            for seed in ALL_CANDIDATES:
                alphabet = pad25(seed)
                if len(alphabet) != 25:
                    continue
                answer = decode_9ary(ciphertext, alphabet, e1, e2)
                if "?" in answer:
                    continue
                results.append((text_score(answer), target_name, e1, e2, seed, answer))
    results.sort(key=lambda r: -r[0])
    return results


def aes_pass():
    hits = []
    tested = set()
    for seed in ALL_CANDIDATES:
        for form in answer_forms(seed):
            if not form:
                continue
            for keystring in keystr_forms(form):
                if keystring in tested:
                    continue
                tested.add(keystring)
                result = aes_try_open(keystring)
                if result:
                    tag, plaintext, digest_name, key_len = result
                    hits.append({
                        "seed": seed, "form": form, "keystring": keystring,
                        "blob": tag, "kdf": f"{digest_name}/aes{key_len * 8}",
                        "plaintext": plaintext[:200].decode("utf-8", errors="replace"),
                    })
    return hits


def self_test():
    from data import DBBI  # noqa: E402
    assert len(ALL_CANDIDATES) == len(set(ALL_CANDIDATES)), "duplicate candidate strings"
    for c in ALL_CANDIDATES:
        assert c.isalpha() and c == c.lower(), f"candidate not normalized: {c!r}"
    alphabet = pad25(ALL_CANDIDATES[0])
    assert len(alphabet) == 25
    answer = decode_9ary(DBBI, alphabet, "b", "e")
    assert isinstance(answer, str) and len(answer) > 0
    assert "P32TRAILING" in BLOBS
    print("self-test OK: candidate normalization, pad25/decode_9ary wiring, "
          "and BLOBS target set all verified")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return

    print(f"Testing {len(ALL_CANDIDATES)} candidates derived from the song's "
          f"unused remainder ({len(LINE_CANDIDATES)} full lines + "
          f"{len(WORD_CANDIDATES)} short/compound forms).\n")

    print("=== Checkerboard alphabet-seed pass (compare against "
          "CORE_ALPHABET_SEEDS baseline scores in matrixsum_permutation_sweep.py) ===")
    cb_results = checkerboard_pass()
    for score, target, e1, e2, seed, answer in cb_results[:15]:
        print(f"  {score:8.1f}  {target} {e1}/{e2}  seed={seed[:30]:30s}  "
              f"answer_preview={answer[:60]}")
    if not cb_results:
        print("  (no valid decodes -- unexpected, check pad25 output)")

    print("\n=== AES password-candidate pass (SALPH/COSMIC/P32TRAILING/URLBLOB) ===")
    aes_hits = aes_pass()
    if aes_hits:
        for h in aes_hits:
            print(f"  HIT: {h}")
    else:
        print("  no hits")


if __name__ == "__main__":
    main()
