#!/usr/bin/env python3
"""Phase 0.1 — cheap high-confidence probe.

An early community notebook (Naddiseo/gsmgio-5btc-puzzle) found that the raw
SalPhaseIon page text contains a *literal* embedded base64 "Salted__" AES blob
(no checkerboard decode needed — see data.SALPHASEION_BLOB_B64) plus a decoded
plaintext fragment: "our first hint is your last command".

This tests that literal blob against a short, curated candidate list built from
that hint, before committing to the much larger keyword sweep in cosmic_sweep.py.
"""
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from cb_common import BLOBS, aes_try_open  # noqa: E402

CANDIDATES = [
    # the hint text itself, in case it's self-referential
    "our first hint is your last command",
    "ourfirsthintisyourlastcommand",
    "OURFIRSTHINTISYOURLASTCOMMAND",
    "your last command",
    "yourlastcommand",
    "YOURLASTCOMMAND",
    "last command",
    "lastcommand",
    # prior-stage URLs / paths (the "command" used to reach this page)
    "gsmg.io/theseedisplanted",
    "theseedisplanted",
    "THESEEDISPLANTED",
    "/theseedisplanted",
    "gsmg.io/puzzle",
    "salphaseion",
    "SALPHASEION",
    "gsmg.io/salphaseion",
    "follow the white rabbit",
    "followthewhiterabbit",
    "FOLLOWTHEWHITERABBIT",
    # generic "last command" a solver might literally type
    "curl gsmg.io/theseedisplanted",
    "wget gsmg.io/theseedisplanted",
    "cd theseedisplanted",
    "view-source:gsmg.io/theseedisplanted",
    "ctrl+u",
    "view source",
    "viewsource",
    # the known 3.2.2 answer (in case it chains forward as a passphrase)
    "INCASEYOUMANAGETOCRACKTHISTHEPRIVATEKEYSBELONGTOHALFANDBETTERHALFANDTHEYALSONEEDFUNDSTOLIVE",
    "incaseyoumanagetocrackthistheprivatekeysbelongtohalfandbetterhalfandtheyalsoneedfundstolive",
]


def probe():
    """Every candidate x newline/CRLF x raw/SHA-256 form against the literal
    SalPhaseIon AES blob. Also try each candidate with a trailing newline/CRLF
    appended, before and after SHA-256 -- the "enter" reading of the abba-
    encoded word embedded in the AES blob itself (an `echo "x" | sha256sum`-
    style terminal session includes the newline from pressing Enter; `echo -n`
    does not). Returns (forms, hits)."""
    forms = []
    for c in CANDIDATES:
        for base in (c, c + "\n", c + "\r\n"):
            forms.append((c, base))
            forms.append((c, __import__("hashlib").sha256(base.encode()).hexdigest()))
    hits = []
    for c, keystr in forms:
        r = aes_try_open(keystr, blobs={"SALPH": BLOBS["SALPH"]})
        if r:
            hits.append((c, keystr, r))
    return forms, hits


def main():
    forms, hits = probe()
    print(f"[*] testing {len(CANDIDATES)} candidates ({len(forms)} forms incl. "
          f"newline variants) against the literal SalPhaseIon AES blob...")
    for c, keystr, r in hits:
        tag, body, digest_name, key_len = r
        print(f"\n[+++ HIT] candidate={c!r} keystr={keystr!r} blob={tag} kdf={digest_name}/aes{key_len*8}")
        print(f"    plaintext={body[:300]!r}")
    print(f"\n[*] done. {len(hits)} hits out of {len(forms)} forms.")
    if not hits:
        print("[*] negative result — none of the direct 'last command' readings "
              "(incl. trailing-newline/'enter' variants) open the blob.")


if __name__ == "__main__":
    main()
