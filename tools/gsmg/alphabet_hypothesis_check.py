#!/usr/bin/env python3
"""Phase 0.2 — validate (or falsify) the "keyword -> pad28 -> alphabet" hypothesis
that cosmic_sweep.py's big wordlist sweep depends on.

The known-good Phase 3.2.2 alphabet (ALPHA_322 = "FUBCDORA.LETHINGKYMVPS.JQZXW") is
hardcoded in the community's cb2.py — it is NOT demonstrated anywhere to come from
pad28(some_keyword). joint_attack.py *assumes* new candidate alphabets are built via
pad28(keyword), but that assumption is unverified against the one ground-truth case
we actually have.

This script tries every keyword anyone (community + this session) has tried so far
through pad28() and reports whether any of them reproduce ALPHA_322 exactly. The
result gates how much confidence to place in cosmic_sweep.py's big keyword sweep.
"""
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from cb_common import ALPHA_322, pad28  # noqa: E402

# Every keyword tried by the community fork's cb2.py + joint_attack.py, plus every
# keyword I tried in this session's my_sweep.py.
ALL_TRIED_KEYWORDS = [
    # cb2.py
    "MATRIXSUMLIST", "ENTER", "", "YELLOWBLUE", "SALPHASEION", "THEMATRIXHASYOU",
    # joint_attack.py
    "LASTWORDSBEFOREARCHICHOICE", "THISPASSWORD", "THESEEDISPLANTED",
    "FOLLOWTHEWHITERABBIT", "YELLOWBLUEPRIME", "CAUSALITY", "THEWARNING",
    "HASHTHETEXT", "COSMICDUALITY", "THEFLOWERBLOSSOMS",
    # my_sweep.py (this session)
    "ARCHITECT", "MEROVINGIAN", "ANOMALY", "HALFANDBETTERHALF", "BETTERHALF",
    "CIAOBELLA", "CIAOBELLAO", "THEONE", "NEO", "PRIMEBASICS", "SOURCECODE",
    "GSMGIO5BTCPUZZLECHALLENGE", "JRKBGRT", "GOODPUZZLESDONTNEEDHINTS",
    "EVENTUALITYOFANANOMALY", "THEARCHITECTCHOICE", "UNBALANCEDEQUATION",
    "RESTLESSSOUL", "WISEMAN", "TAKETHEPRIVATEKEY", "HUNDREDFOURTY",
    "TWENTYTHREECIPHERS", "GIVEITJUSTONESECOND", "IHOPEYOURETHEONE",
    "THEFUNCTIONOFTHEYOUISNOW",
    # a few more plausible candidates specific to this alphabet's own puzzle name
    "COSMIC", "DUALITY", "COSMICDUALITY", "SALPHASEIONCOSMICDUALITY", "GSMG",
    "GSMGIO", "PUZZLE", "THEPUZZLE",
]


def main():
    print(f"[*] known-good alphabet: {ALPHA_322!r}")
    print(f"[*] testing {len(ALL_TRIED_KEYWORDS)} keywords through pad28()...\n")
    matches = []
    for kw in ALL_TRIED_KEYWORDS:
        derived = pad28(kw)
        if derived == ALPHA_322:
            matches.append(kw)
            print(f"  [MATCH] pad28({kw!r}) == ALPHA_322")
    print()
    if matches:
        print(f"[*] HYPOTHESIS VALIDATED — {len(matches)} keyword(s) reproduce the "
              f"known alphabet: {matches}")
    else:
        print("[*] HYPOTHESIS NOT CONFIRMED — none of the "
              f"{len(ALL_TRIED_KEYWORDS)} tried keywords reproduce ALPHA_322 via "
              "pad28(). This does not disprove the keyword->alphabet model (the "
              "3.2.2 keyword itself may simply not be in this list, or may use a "
              "construction rule other than pad28's dedupe-then-fill-alphabet "
              "order), but it means cosmic_sweep.py's big sweep rests on an "
              "unverified assumption, not a confirmed one. Treat any 'hit' from "
              "the sweep with that in mind, and treat a clean sweep as inconclusive "
              "about the *model*, not just the keyword.")


if __name__ == "__main__":
    main()
