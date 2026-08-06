#!/usr/bin/env python3
"""Known-plaintext ("crib") attack against dbbi/faed's straddling checkerboard,
instead of guessing candidate keywords.

Key insight: for a fixed escape pair {e1,e2}, the raw ciphertext string segments
into a sequence of "codes" (1-symbol, or 2-symbol if the symbol is e1/e2) *without
needing to know the alphabet* -- decode_9ary's scan (escape-or-not) depends only on
e1/e2 and the raw string, not on the keyword. So if a crib (hypothesized plaintext
fragment) really appears somewhere in the decoded output, its *letter-repetition
pattern* (e.g. "matrixsumlist" -> which letters repeat, and where) must exactly match
the *code-repetition pattern* of some contiguous run of codes in the ciphertext's
segmentation -- a bijective substitution cipher can't break that invariant. This can
be checked directly, with no alphabet/keyword guess at all, and if it matches, the
crib pins down real code<->letter equalities that can decode surrounding ciphertext
too (wherever a pinned-down code recurs elsewhere in the string).
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data import DBBI, FAED


def segment(raw, e1, e2):
    """Split raw ciphertext into codes, or return None for a dangling escape."""
    codes = []
    i = 0
    while i < len(raw):
        ch = raw[i]
        if ch in (e1, e2):
            if i + 1 >= len(raw):
                return None
            else:
                codes.append(raw[i:i + 2])
                i += 2
        else:
            codes.append(ch)
            i += 1
    return codes


def pattern(seq):
    """Canonical repetition pattern: first-occurrence index of each element."""
    first = {}
    out = []
    for x in seq:
        if x not in first:
            first[x] = len(first)
        out.append(first[x])
    return tuple(out)


def find_crib_matches(raw, e1, e2, crib):
    """Return list of (start_code_idx, forced_code_to_letter_dict) for every
    contiguous code-window whose repetition pattern matches the crib's."""
    codes = segment(raw, e1, e2)
    if codes is None:
        return []
    crib = crib.lower()
    n = len(crib)
    crib_pat = pattern(crib)
    matches = []
    for start in range(0, len(codes) - n + 1):
        window = codes[start:start + n]
        if pattern(window) != crib_pat:
            continue
        # build forced code->letter map (guaranteed consistent since patterns match)
        mapping = {}
        ok = True
        for code, letter in zip(window, crib):
            if code in mapping and mapping[code] != letter:
                ok = False
                break
            mapping[code] = letter
        if not ok:
            continue
        # also check reverse-injectivity (bijection: no two codes map to the same letter)
        rev = {}
        for code, letter in mapping.items():
            if letter in rev and rev[letter] != code:
                ok = False
                break
            rev[letter] = code
        if not ok:
            continue
        matches.append((start, mapping, codes))
    return matches


def apply_mapping(codes, mapping):
    return "".join(mapping.get(c, "?") for c in codes)


# Only cribs with enough length/internal repetition to be statistically decisive.
# Short or low-repetition words (e.g. "yellow", "password") match dozens of
# positions by chance in a 63-469 code sequence -- that's noise, not signal;
# excluded here after confirming they're worthless via a full run.
CRIB_CANDIDATES_DBBI = [
    "yellowblueprimesmatrixsumlist",
    "yellowblueprimematrixsumlist",
    "yellowblueprimes",
    "yellowblueprime",
    "matrixsumlist",
    "matrixsumlistyellowblueprimes",
    "tsilmusxirtamsemirpeulbwolley",
    "semirpeulbwolley",
    "blueyellowprime",
]

CRIB_CANDIDATES_FAED = [
    "lastwordsbeforearchichoiceyinyangwewontgiveawaythepassworditsinfrontofyoureyesbutyourenotseeingitverylaststepisatruegiveawaypromised",
    "lastwordsbeforearchichoice",
    "yinyangwewontgiveawaythepassword",
    "wewontgiveawaythepassword",
    "itsinfrontofyoureyes",
    "butyourenotseeingit",
    "verylaststepisatruegiveawaypromised",
    "thepasswordisinfrontofyoureyes",
    "eciohcihcraerofebsdrowtsal",
    "desimorpyawaevigeurtasi",
    "tignieestoneruoytub",
]


def run(target_name, raw, escape_pairs, cribs):
    print(f"\n=== {target_name} (len={len(raw)}) ===")
    for e1, e2 in escape_pairs:
        codes = segment(raw, e1, e2)
        if codes is None:
            print(f"  escapes={{{e1},{e2}}}: invalid (dangling escape)")
            continue
        print(f"  escapes={{{e1},{e2}}}: {len(codes)} codes")
        for crib in cribs:
            matches = find_crib_matches(raw, e1, e2, crib)
            if matches:
                print(f"    CRIB {crib!r}: {len(matches)} match(es)")
                for start, mapping, all_codes in matches:
                    decoded_full = apply_mapping(all_codes, mapping)
                    print(f"      start_code_idx={start} mapping={mapping}")
                    print(f"      full-string-partial-decode: {decoded_full}")


if __name__ == "__main__":
    run("dbbi", DBBI, [("b", "e")], CRIB_CANDIDATES_DBBI)
    run("faed", FAED, [("b", "e"), ("g", "i"), ("h", "e")], CRIB_CANDIDATES_FAED)
    print("\ndone.")
