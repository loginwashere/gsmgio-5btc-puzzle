#!/usr/bin/env python3
"""Candidate family 10 -- fork-surfaced residual leads (2026-08-14).

Executes the four leads from
doc/Brainstorms/2026-08-14 - P32 New Attack Surfaces Beyond Text Recombination.md's
"Candidate family 10" section, surfaced by the independently-maintained
`HosterjackAGV/gsmg-5btc-puzzle` fork's `docs/LOOSE-ENDS.md`. Each lead is a
source-grounded artifact this project already has authenticated, paired with
a specific, narrow, previously-untested operation -- not a new artifact and
not an open-ended reinterpretation. Every candidate is tested in exactly two
forms (literal, hex SHA-256 of literal) against the standard CBC oracle
across all four tracked blobs -- the same bounded discipline this project
uses everywhere else (see FINDINGS.md Phase 290's P1A backfill).

Lead 1 (VIC alphabet alternate reconstruction) is mechanically derived, not
copied verbatim, from the fork's shorthand note (`...JQZXW` vs `...ZJQWX.`):
this project's own cb_common.pad25() docstring already independently
confirms the tail order of the five unused letters {J,Q,W,X,Z} is provably
UNCONSTRAINED by the one available ground-truth decode (VALIDATION_NUM never
uses any of those five letters). The fork's literal alternate text
`...ZJQWX.` is taken at face value and slotted into the fixed 28-symbol
board format cb_common.decode() requires: the trailing period moves from
before the tail letters to after them, changing which two-digit escape
codes decode to a blank. This is one specific, disclosed alternate -- not a
sweep over the 120 possible tail orderings.

Lead 2 (Safenet/Luna/HSM digit-glued fragments) is only partially
executable as declared. The digits 2/3/4 in the Phase 3.2 plaintext's
"2name...3Moon?...4How so mate?" are the SAME digits that already fix
Safenet/Luna/HSM as parts 2/3/4 of the solved 7-part concatenation order
(README.md) -- reading them as "an ordering key over parts 2/3/4" therefore
reproduces the identity permutation already used to solve Phase 3, not a
new candidate. No independently-sourced non-identity reordering rule exists
in this project. Only the literal digit-glued fragment substrings
themselves (zero interpretation, direct quotes) are tested here; the
"ordering key" reading is recorded as inconclusive, not invented.

Lead 3 (genesis coinbase headline) is fully executable: the raw genesis
coinbase scriptSig hex (main.cpp line 1616, public immutable blockchain
data) is decoded here directly from its bytes -- not typed from memory --
to get the exact 69-byte headline with no transcription risk.

Lead 4 (orphan trailing "O") is bounded exactly as declared: the
authenticated tail "CIAO BELLA O" (bye_ciao_provenance_audit.py) is tested
with the digit "0" in place of the letter "O" in the same trailing
position -- a discrete token substitution, not a new phrase permutation.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from cb_common import BLOBS, MAPS, aes_try_open_bytes, decode  # noqa: E402
from data import DBBI, FAED  # noqa: E402

# ---------------------------------------------------------------------------
# Lead 1: VIC alphabet alternate reconstruction
# ---------------------------------------------------------------------------

CANONICAL_ALPHA28 = "FUBCDORA.LETHINGKYMVPS.JQZXW"
# Same 21 dedupe-derived letters (FUBCDORA + LETHINGKYMVPS) as the canonical,
# confirmed ground-truth alphabet. Only the final 10-symbol board segment
# changes: the fork's literal "...ZJQWX." puts the blank-marker period AFTER
# the reordered tail letters instead of before them.
ALTERNATE_ALPHA28 = "FUBCDORA.LETHINGKYMVPSZJQWX."
ESCAPES = (1, 4)  # VALIDATION_ESCAPES -- the only validated escape pair.
STREAMS = {"DBBI": DBBI, "FAED": FAED}


def vic_alternate_candidates():
    assert len(CANONICAL_ALPHA28) == 28
    assert len(ALTERNATE_ALPHA28) == 28
    assert sorted(c for c in ALTERNATE_ALPHA28 if c != ".") == sorted(
        c for c in CANONICAL_ALPHA28 if c != "."
    ), "alternate alphabet must be a rearrangement of the same 26 letters"
    assert CANONICAL_ALPHA28 != ALTERNATE_ALPHA28

    candidates = []
    for stream_name, stream in STREAMS.items():
        for map_name, mapping in MAPS.items():
            digits = "".join(mapping[symbol] for symbol in stream)
            decoded = decode(digits, ALTERNATE_ALPHA28, *ESCAPES)
            candidates.append({
                "lead": "lead1_vic_alternate",
                "label": f"{stream_name}/{map_name}",
                "text": decoded,
                "clean_decode": "?" not in decoded,
            })
    return candidates


# ---------------------------------------------------------------------------
# Lead 2: Safenet/Luna/HSM digit-glued fragments (literal substrings only)
# ---------------------------------------------------------------------------

DIGIT_GLUED_FRAGMENTS = ("2name", "3Moon", "4How so mate")


def digit_glued_candidates():
    candidates = [
        {"lead": "lead2_digit_glued_fragments", "label": frag, "text": frag}
        for frag in DIGIT_GLUED_FRAGMENTS
    ]
    candidates.append({
        "lead": "lead2_digit_glued_fragments",
        "label": "concatenated",
        "text": "".join(f.replace(" ", "") for f in DIGIT_GLUED_FRAGMENTS),
    })
    return candidates


# ---------------------------------------------------------------------------
# Lead 3: genesis coinbase headline, decoded from raw hex (not typed)
# ---------------------------------------------------------------------------

GENESIS_COINBASE_SCRIPTSIG_HEX = (
    "04ffff001d0104455468652054696d65732030332f4a616e2f32303039204368"
    "616e63656c6c6f72206f6e206272696e6b206f66207365636f6e64206261696c"
    "6f757420666f722062616e6b73"
)


def genesis_headline_text():
    raw = bytes.fromhex(GENESIS_COINBASE_SCRIPTSIG_HEX)
    # 04 <ffff001d> 01 <04> 45 <69-byte text>: push-4 (bits), push-1 (extranonce
    # byte 0x04), then push-69 (the headline) at offset 7.
    length_prefix = raw[7]
    text = raw[8:8 + length_prefix].decode("ascii")
    assert len(text) == length_prefix
    return text


def genesis_headline_candidates():
    text = genesis_headline_text()
    letters_only = "".join(c for c in text if c.isalpha())
    forms = {
        "raw": text,
        "upper": text.upper(),
        "letters_only": letters_only,
        "letters_only_upper": letters_only.upper(),
    }
    return [
        {"lead": "lead3_genesis_headline", "label": name, "text": value}
        for name, value in forms.items()
    ]


# ---------------------------------------------------------------------------
# Lead 4: orphan trailing "O" as digit "0"
# ---------------------------------------------------------------------------

CIAO_BELLA_TAIL = "CIAO BELLA O"


def orphan_zero_candidates():
    with_zero = CIAO_BELLA_TAIL[:-1] + "0"
    forms = {
        "spaced": with_zero,
        "nospace": with_zero.replace(" ", ""),
        "nospace_lower": with_zero.replace(" ", "").lower(),
    }
    return [
        {"lead": "lead4_orphan_zero", "label": name, "text": value}
        for name, value in forms.items()
    ]


# ---------------------------------------------------------------------------
# Oracle execution -- raw + sha256-hex only, matching this family's own
# declared discipline (no open-ended format sweep, no ECB/stream/keywrap).
# ---------------------------------------------------------------------------

def all_candidates():
    return (
        vic_alternate_candidates()
        + digit_glued_candidates()
        + genesis_headline_candidates()
        + orphan_zero_candidates()
    )


def run(blobs=None):
    active_blobs = BLOBS if blobs is None else blobs
    candidates = all_candidates()
    attempts = []
    hits = []
    for candidate in candidates:
        text = candidate["text"]
        forms = (text, hashlib.sha256(text.encode()).hexdigest())
        for form_kind, form_text in zip(("literal", "sha256"), forms):
            result = aes_try_open_bytes(form_text.encode(), blobs=active_blobs)
            attempts.append({
                "lead": candidate["lead"],
                "label": candidate["label"],
                "form": form_kind,
            })
            if result:
                tag, body, kdf_label, key_len = result
                hits.append({
                    "lead": candidate["lead"],
                    "label": candidate["label"],
                    "form": form_kind,
                    "blob": tag,
                    "kdf": f"{kdf_label}/aes{key_len * 8}",
                    "plaintext_hex": body.hex(),
                })
    return {
        "candidate_count": len(candidates),
        "passphrase_attempts": len(attempts),
        "blobs": tuple(active_blobs),
        "hits": hits,
        "total_hits": len(hits),
        "_candidates": candidates,
    }


def self_test():
    candidates = all_candidates()
    assert len(candidates) == 4 + 4 + 4 + 3
    vic = [c for c in candidates if c["lead"] == "lead1_vic_alternate"]
    assert len(vic) == 4
    assert all(c["clean_decode"] for c in vic), "alternate alphabet produced an undecodable '?' cell"
    genesis = genesis_headline_text()
    assert genesis == "The Times 03/Jan/2009 Chancellor on brink of second bailout for banks"
    assert len(genesis) == 69
    zero_candidates = orphan_zero_candidates()
    assert zero_candidates[0]["text"] == "CIAO BELLA 0"
    print(f"[*] self-test OK: {len(candidates)} family-10 candidates across 4 leads")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.run:
        for candidate in all_candidates():
            print(candidate)
        return
    report = run()
    report.pop("_candidates")
    if args.json:
        print(json.dumps(report, indent=2, default=repr))
    else:
        for key, value in report.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
