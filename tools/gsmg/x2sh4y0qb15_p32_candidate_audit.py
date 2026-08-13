#!/usr/bin/env python3
"""Test whether the X2SH4Y0QB15 riddle's own text -- literal, numerically
substituted, or coordinate-serialized -- is P32's password, as a distinct
hypothesis from the Phase 3.2 monologue vocabulary (Phase 265) and the
Phase 3 seven-part reuse (Phase 266).

X2SH4Y0QB15 sits in the Phase 2 decrypted text -- explicitly flagged in the
README as "unclear how to use" and bypassed by the canonical Phase 2->3
solve (which uses the same paragraph's "2name/3Moon/4How so mate" instead).
P32TRAILING is likewise an orphaned artifact appended after the already-
solved Phase 3.2 plaintext, with no stated instruction, and the monologue
immediately above it says "RETURN TO THE SOURCE CODES ... THE CODE YOU
HOPEFULLY CARRY" -- read here as a possible pointer back to this earlier
unconsumed "code." This is a weaker-precedent hypothesis than Phase
265/266's (X2SH4Y0QB15 precedes Phase 3.2 by several stages, not adjacent
to it), tested because it is cheap, bounded, and disclosed, not because the
proximity argument is strong.

Resolved values, all previously established and independently re-verified
in this project (not re-derived here):
  S = 32   (Klingon numerals: cha' + (vagh*jav) = 2 + 5*6)
  H = -42  (community reading: "Answer to only this puzzle" = 42, times -1)
  B = -16  ((5i - i)^2 = (4i)^2, from "i5" in the Intel Core i5-750 model
            number BV80605001911AP)
  Q = 82   (Mr. Robot's fish "Qwerty" extended to QWERTYUIOP; the digits
            above I and W, in that order, are 8 and 2 -- Phase 264)
X and Y are left undefined in the riddle itself; the Decentraland coordinate
reading built from them was already closed as unverified (G-X2SH-001) and
is not re-litigated here -- only the row-label serialization
"X: 2,32,-42,4 / Y: 0,82,-16,15" is tested, as the source text's own layout.

The candidate family (disclosed in full, nothing added after seeing a
result):
  1. Literal source text, three forms.
  2. Numerically substituted text, three forms.
  3. Coordinate-serialized text, two forms.
  4. Three additional "worst gear" = reverse scopes beyond plain character
     reversal: whole-token-sequence reversal, per-row reversal (X and Y
     rows reversed independently, label first), and coordinate-pair X/Y
     swap (the last of which turns (4,15) into (15,4)).
  5. Every one of the 12 forms above, character-reversed on top -- so the
     structural reversals in (4) also get character-reversed, without
     hand-picking which combination "matters".
A 2025 solver repost (Telegram message 38301) appends eight literal `\b`
text characters after "worst gear.", but the earliest preserved 2020 repost
(message 2834) does not -- confirmed directly against both raw exports, not
assumed -- so those are not treated as authenticated puzzle bytes here.
`answer_forms`/`keystr_forms` then supply case variants, alpha-only forms,
SHA-256 hex, and double-SHA-256 hex for every one of these; raw SHA-256
digest bytes are added explicitly as separate key material.
"""

import argparse
import hashlib
import json

from cb_common import BLOBS, answer_forms, keystr_forms
from color_mask_full_stream_audit import passphrase_hits

RESOLVED = {"S": 32, "H": -42, "B": -16, "Q": 82}

BASE_FORMS = (
    # 1. Literal source text.
    "# X 2 S H 4 Y 0 Q B 15 #",
    "X 2 S H 4 Y 0 Q B 15",
    "X2SH4Y0QB15",
    # 2. Numerically substituted text.
    "X 2 32 -42 4 Y 0 82 -16 15",
    "X232-424Y082-1615",
    "232-424082-1615",
    # 3. Coordinate-serialized text (row-label reading: X row / Y row).
    "(2,0)(32,82)(-42,-16)(4,15)",
    "2,0|32,82|-42,-16|4,15",
    # 4. "Worst gear" = reverse (authenticated at the puzzle's first solved
    #    stage), applied at three distinct, non-arbitrary scopes rather than
    #    only character-reversing the whole string:
    #    (a) reverse the whole token sequence, keeping each token intact;
    "15 -16 82 0 Y 4 -42 32 2 X",
    #    (b) reverse each X/Y row independently, keeping its own label first;
    "X 4 -42 32 2 Y 15 -16 82 0",
    #    (c) reverse each coordinate pair by swapping X and Y within it
    #        (notably turns (4,15) into the historically meaningful (15,4)).
    "(0,2)(82,32)(-16,-42)(15,4)",
    "0,2|82,32|-16,-42|15,4",
)

# Character-level reversal of every base form (the fourth, most literal
# reading of "worst gear") is applied uniformly on top of all of the above,
# including the three structural reversals -- so e.g. the token-reversed
# form also gets tested character-reversed, without hand-selecting which
# combinations "matter."
CANDIDATES = BASE_FORMS + tuple(form[::-1] for form in BASE_FORMS)


def material_family(candidates, blobs):
    materials = {}
    for candidate in candidates:
        for form in answer_forms(candidate):
            for keystr in keystr_forms(form, newline_variants=True, whitespace_variants=True):
                materials.setdefault(keystr.encode("utf-8"), set()).add(candidate)
        materials.setdefault(hashlib.sha256(candidate.encode()).digest(), set()).add(candidate)
    hits = []
    for material, sources in sorted(materials.items()):
        for hit in passphrase_hits(material, blobs):
            hits.append({
                "sources": tuple(sorted(sources)),
                "material_hex": material.hex(),
                **hit,
            })
    return {
        "candidate_count": len(candidates),
        "unique_material_count": len(materials),
        "hits": hits,
    }


def audit():
    report = material_family(CANDIDATES, BLOBS)
    return {
        "candidates": CANDIDATES,
        "resolved_values": RESOLVED,
        "blob_names": tuple(sorted(BLOBS)),
        **report,
    }


def self_test():
    report = audit()
    assert report["candidate_count"] == len(BASE_FORMS) * 2 == 24
    assert report["resolved_values"] == {"S": 32, "H": -42, "B": -16, "Q": 82}
    assert report["blob_names"] == ("COSMIC", "P32TRAILING", "SALPH", "URLBLOB")
    assert report["unique_material_count"] > 0
    assert report["hits"] == []
    print(
        f"[*] self-test OK: {report['candidate_count']} X2SH4Y0QB15-derived "
        f"candidates (literal/substituted/coordinate x forward+reversed) / "
        f"{report['unique_material_count']} unique key materials against "
        f"all 4 tracked blobs, 0 hits"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    report = audit()
    print(json.dumps({k: v for k, v in report.items() if k != "candidates"}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
