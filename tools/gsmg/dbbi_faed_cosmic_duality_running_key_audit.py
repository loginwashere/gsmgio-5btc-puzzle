#!/usr/bin/env python3
"""Running-key extension of Phase 310's Nihilist additive-key test: instead
of a short repeating keyword, uses the actual OCR'd text of the *confirmed*
physical *Cosmic Duality* book (Time-Life "Mysteries of the Unknown", 1991)
as the additive key stream over DBBI/FAED's checkerboard code-slot
sequence. Unlike every other cipher-family candidate tried this session,
this one doesn't need a book-ownership hypothesis to be true -- the book is
already an established physical artifact in this project
(`wordlists/gsmg/cosmic_duality_book_full_text.txt`, transcribed from the
user's own photographs), previously only ever searched for a hidden riddle
SENTENCE. This tests a structurally different question: whether the book's
own prose, read as a running numeric key, decodes the checkerboard-
segmented ciphertext -- not whether a sentence in it names a password.

Candidate starting points (closed, bounded to the book's own explicit
structure -- not an arbitrary offset sweep): the very start of real prose
(the front-matter essay "The Unity of Opposites"), and the start of each of
the 4 named chapters per the book's own table of contents. Five points
total, each independently motivated by the book's own section boundaries,
not invented.

Reproduce with:
    python3 tools/gsmg/dbbi_faed_cosmic_duality_running_key_audit.py --self-test
    python3 tools/gsmg/dbbi_faed_cosmic_duality_running_key_audit.py
"""
import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from data import DBBI, FAED  # noqa: E402
from matrixsum_permutation_sweep import natural_code_index, segment_codes  # noqa: E402
from dbbi_faed_nihilist_additive_audit import (  # noqa: E402
    slot_sequence, apply_shift, hillclimb_slots, score, TOPOLOGIES,
)

BOOK_PATH = SCRIPT_DIR.parent.parent / "wordlists" / "gsmg" / "cosmic_duality_book_full_text.txt"

TARGETS = {
    "DBBI": (DBBI, [("b", "e"), ("e", "b")]),
    "FAED": (FAED, [("g", "i"), ("i", "g"), ("h", "e"), ("e", "h")]),
}

# (label, 1-based source line to start reading from) -- each is the book's own
# section boundary (essay opening or a named chapter start), per its table of
# contents, not an arbitrary offset.
START_POINTS = (
    ("essay_opening_p6", 24),
    ("chapter1_p16", 184),
    ("chapter2_p48", 436),
    ("chapter3_p78", 668),
    ("chapter4_p106", 882),
)


def load_book_letters():
    with open(BOOK_PATH, encoding="utf-8") as f:
        lines = f.readlines()
    return lines


def letters_from_line(start_idx, lines, need):
    """A=0..Z=24 (J collapsed into I), reading order, starting at 1-based
    line `start_idx`, skipping this project's own '#'-prefixed annotation
    lines, until `need` letters are collected."""
    out = []
    for line in lines[start_idx - 1:]:
        if line.lstrip().startswith("#"):
            continue
        for ch in line.upper():
            if not ch.isalpha():
                continue
            c = "I" if ch == "J" else ch
            pos = ord(c) - ord("A")
            if c > "J":
                pos -= 1
            out.append(pos)
            if len(out) >= need:
                return out
    return out  # book ran out before `need` -- caller must handle short keys


def self_test():
    lines = load_book_letters()
    key = letters_from_line(24, lines, 20)
    assert len(key) == 20
    assert all(0 <= k <= 24 for k in key)
    # First real prose word after the '#' header lines at line 24 is
    # "Sidebar" (the photo caption) -- S=18(no collapse needed, S<J false
    # since S>J -> collapse: S was 18, minus 1 = 17). Just check round-trip
    # shift/unshift instead of hand-deriving the exact letters, matching the
    # style of the Phase 310 self-test.
    slots = slot_sequence(DBBI, "b", "e", "top_first")
    shifted = apply_shift(slots, key[:len(slots)], +1)
    back = apply_shift(shifted, key[:len(slots)], -1)
    assert back == slots, "shift/unshift round-trip failed"
    print("self-test OK: book text loads, letter extraction and shift round-trip verified")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--iters", type=int, default=800)
    ap.add_argument("--restarts", type=int, default=30)
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return

    lines = load_book_letters()
    results = []
    for name, (raw, pairs) in TARGETS.items():
        for e1, e2 in pairs:
            for topo in TOPOLOGIES:
                base_slots = slot_sequence(raw, e1, e2, topo)
                if base_slots is None:
                    continue
                n = len(base_slots)
                for label, start_line in START_POINTS:
                    key = letters_from_line(start_line, lines, n)
                    if len(key) < n:
                        print(f"[SKIP {name} {e1}/{e2} {topo} {label}] book ran out: "
                              f"needed {n}, got {len(key)}")
                        continue
                    for sign, sign_label in ((+1, "+"), (-1, "-")):
                        shifted = apply_shift(base_slots, key, sign)
                        seed = hash((name, e1, e2, topo, label, sign)) & 0xffff
                        best = hillclimb_slots(shifted, args.iters, args.restarts, seed=seed)
                        results.append((best[0], name, e1, e2, topo, f"{label}{sign_label}"))

    results.sort(key=lambda r: -r[0])
    print("\nTop 15 by score (compare against Phase 310's unshifted baselines: "
          "DBBI best -302.1, FAED best -2447.2):")
    for score_, name, e1, e2, topo, label in results[:15]:
        print(f"  {score_:8.1f}  {name} {e1}/{e2} {topo}  start={label}")


if __name__ == "__main__":
    main()
