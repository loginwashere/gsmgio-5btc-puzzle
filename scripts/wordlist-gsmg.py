#!/usr/bin/env python3
"""
Generate a curated GSMG.io 5 BTC puzzle phrase wordlist for the "Cosmic Duality"
checkerboard-keyword sweep (tools/gsmg/cosmic_sweep.py).

Covers: every keyword already tried by the community fork
(halbgott29a/gsmgio-5btc-puzzle: cb2.py, joint_attack.py) and by this project's own
prior session (my_sweep.py), plus new candidates pulled from the puzzle's own lore —
prior-stage answers/URLs, and direct quotes from the creator's Telegram export
("Jrk Bgrt", 2019-2026, ~1283 messages). See doc/GSMG_PUZZLE.md for the full writeup.

No downloads required — all content is hardcoded.

Usage:
    python3 scripts/wordlist-gsmg.py

Output:
    wordlists/gsmg/phrases.txt        — raw phrases (spaces preserved)
    wordlists/gsmg/phrases-joined.txt — spaces + punctuation stripped
"""

from pathlib import Path

OUT_DIR = Path("wordlists/gsmg")

# ─────────────────────────────────────────────────────────────────────────────
# Curated phrases — ordered by estimated hit probability
# ─────────────────────────────────────────────────────────────────────────────

PHRASES = [
    # ── Prior-stage answers / URLs already known to be part of the solve chain ──
    "theseedisplanted",
    "the seed is planted",
    "gsmg.io/theseedisplanted",
    "salphaseion",
    "SalPhaseIon",
    "cosmic duality",
    "cosmicduality",
    "Cosmic Duality",
    "follow the white rabbit",
    "followthewhiterabbit",
    "in case you manage to crack this",
    "incaseyoumanagetocrackthis",
    "the private keys belong to half and better half",
    "half and better half",
    "halfandbetterhalf",
    "and they also need funds to live",
    "theyalsoneedfundstolive",

    # ── Community fork candidates already tried (cb2.py / joint_attack.py) ──────
    "matrixsumlist",
    "enter",
    "yellowblue",
    "yellowblueprime",
    "thematrixhasyou",
    "lastwordsbeforearchichoice",
    "thispassword",
    "causality",
    "thewarning",
    "hashthetext",
    "theflowerblossoms",
    "the flower blossoms through what seems to be a concrete surface",

    # ── This project's own prior-session candidates (my_sweep.py) ──────────────
    "architect",
    "merovingian",
    "anomaly",
    "betterhalf",
    "ciaobella",
    "ciaobellao",
    "theone",
    "neo",
    "primebasics",
    "sourcecode",
    "gsmgio5btcpuzzlechallenge",
    "jrkbgrt",
    "goodpuzzlesdontneedhints",
    "eventualityofananomaly",
    "thearchitectchoice",
    "unbalancedequation",
    "restlesssoul",
    "wiseman",
    "taketheprivatekey",
    "hundredfourty",
    "twentythreeciphers",
    "giveitjustonesecond",
    "ihopeyourtheone",
    "thefunctionoftheyouisnow",

    # ── "Your last command" hint (Phase 0.1 already covers the AES-blob probe;
    #    these are folded in here too so the big sweep also covers them as
    #    checkerboard keywords, not just direct AES passphrases) ────────────────
    "our first hint is your last command",
    "ourfirsthintisyourlastcommand",
    "your last command",
    "yourlastcommand",
    "last command",
    "lastcommand",

    # ── Direct creator quotes (Telegram export, "Jrk Bgrt", 2019-2026) ──────────
    # The recurring "no hint" refrain — deliberately puzzle-flavored phrasing
    "no clue friday every saturday",
    "no clue friday",
    "crazy no hint thursday every friday",
    "good puzzles dont need hints",
    "goodpuzzlesdontneedhints",
    "there is no hint",
    "i have no clue",
    # "another door" hint (2021-04-01) — a separate, still-unresolved sub-hint
    "another door might be found on",
    "anotherdoormightbefoundon",
    "another door",
    "anotherdoor",
    # follow-up hint (2021-12-26): prime numbers + "zeroed out" characters
    "prime numbers",
    "primenumbers",
    "zeroed out",
    "zeroedout",
    # The Matrix reference — Neo's prop passport expiry date is a famous Easter
    # egg (Sept 11, 2001) in the film; creator explicitly invokes "neo's passport"
    "the expiry date of neos passport",
    "neos passport",
    "neospassport",

    # ── Puzzle/community-coined terminology ─────────────────────────────────────
    "gsmg",
    "gsmgio",
    "puzzle",
    "thepuzzle",
    "cosmic",
    "duality",
    "salphaseioncosmicduality",
]

# ─────────────────────────────────────────────────────────────────────────────


def joined(phrase: str) -> str:
    """Strip spaces and common punctuation to produce a joined variant."""
    return (
        phrase
        .replace(" ", "")
        .replace("-", "")
        .replace("/", "")
        .replace(":", "")
        .replace(".", "")
        .replace("'", "")
        .replace(",", "")
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    seen: set[str] = set()
    unique: list[str] = []
    for p in PHRASES:
        if p not in seen:
            seen.add(p)
            unique.append(p)

    out_phrases = OUT_DIR / "phrases.txt"
    out_phrases.write_text("\n".join(unique) + "\n", encoding="utf-8")
    print(f"→ {out_phrases} ({len(unique):,} phrases)")

    seen_joined: set[str] = set()
    joined_list: list[str] = []
    for p in unique:
        j = joined(p)
        if j != p and j not in seen_joined:
            seen_joined.add(j)
            joined_list.append(j)

    out_joined = OUT_DIR / "phrases-joined.txt"
    out_joined.write_text("\n".join(joined_list) + "\n", encoding="utf-8")
    print(f"→ {out_joined} ({len(joined_list):,} joined variants)")

    total = len(unique) + len(joined_list)
    print(f"   {total:,} total entries")
    print()
    print("Feed into the Cosmic Duality checkerboard-keyword sweep:")
    print()
    print("  python3 tools/gsmg/cosmic_sweep.py \\")
    print("    --wordlist wordlists/gsmg/phrases.txt \\")
    print("    --wordlist wordlists/gsmg/phrases-joined.txt")


if __name__ == "__main__":
    main()
