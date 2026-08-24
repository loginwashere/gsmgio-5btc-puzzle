#!/usr/bin/env python3
"""Phase 384: re-tests Phase 269's X2SH4Y0QB15 candidate family under the
Naddiseo fork's own resolved B/H values, instead of this project's.

**What differs, and why it's a genuinely new candidate family, not a
rephrasing:** Phase 269 (`x2sh4y0qb15_p32_candidate_audit.py`) fixed
`RESOLVED = {"S": 32, "H": -42, "B": -16, "Q": 82}` as "previously
established" and never recorded why `-16` was chosen over the riddle's own
other algebraically valid reading, `B = 25` (`(5i - i)^2` vs `(i5)^2` for
`BV80605001911AP`'s "i5" -- both are defensible parses of "i5- i", per the
riddle's own text), nor why `H`'s `* -1` was applied as a second, literal
arithmetic negation on top of the semantic negation already used to reach
"42" via the Hitchhiker's Guide reading (an "answer to only this puzzle"
negated is "answer to everything" = 42; negating the *number* 42 again is
a different, unrecorded second step).

A semantic concordance against `Naddiseo/gsmgio-5btc-puzzle`'s own
`phase2.ipynb` (commit `15b43fc`, cell 4) found that repository resolves
both differently, and for a stated, checkable reason this project's own
script never recorded: `B = 25` is chosen over `B = -16` specifically
because only `25` yields a *valid* DMS coordinate (minutes < 60) once the
"worst gear" instruction is read as one whole-string character reversal;
`-16` produces "61 minutes", which is not a valid sexagesimal value. Under
`B = 25`, `H = 42` (no second negation), the same whole-string-reversal
operation Phase 269 already tests reproduces `51 52 28.0 N 4 24 23.2 E` --
a real coordinate near a real SafeNet/Thales facility, cited in this
project's own `doc/GSMG_PHASE2_DECENTRALAND_COORDINATE_AUDIT.md` as "the
established SafeNet reading" without ever recording the B/H values that
actually produce it. Phase 269's own script, meanwhile, silently used the
*other* B/H values throughout, so it never actually tested the material
that produces the coordinate this project's own docs already treat as
authoritative.

This is exactly Phase 269's own declared transform family (numeric
substitution, coordinate serialization, and the four reversal scopes,
including the automatic whole-form character-reversal every base form
already receives) -- only the two input values change. No new transform is
added. (Confirmed directly: reversing the new compact numeric form
"X232424Y0822515" -- already one of the forms this produces -- yields
"5152280Y424232X" byte-for-byte, i.e. the fork's own literal digit string,
with zero hand-added candidates.)

Items from Phase 269's family that do NOT depend on B or H (the literal
un-substituted source text and block-level joins) are deliberately not
repeated here -- rerunning them would be exactly the "repeat an
already-tested candidate" this project's own discipline forbids.
"""

import hashlib
import json

from cb_common import BLOBS
from x2sh4y0qb15_p32_candidate_audit import material_family

RESOLVED = {"S": 32, "H": 42, "B": 25, "Q": 82}
SOLVED_HEADER = "# X 2 32 42 4 Y 0 82 25 15 #"
INSTRUCTION = "Ok kid, on the highway, let put it in the worst gear."

BASE_FORMS = (
    # 2. Numerically substituted text (Phase 269 family, new B/H values).
    "X 2 32 42 4 Y 0 82 25 15",
    "X232424Y0822515",
    "232424082 2515",
    # 3. Coordinate-serialized text (row-label reading: X row / Y row).
    "(2,0)(32,82)(42,25)(4,15)",
    "2,0|32,82|42,25|4,15",
    # 4. "Worst gear" = reverse, at the same three non-arbitrary scopes
    #    Phase 269 already declared:
    #    (a) reverse the whole token sequence, keeping each token intact;
    "15 25 82 0 Y 4 42 32 2 X",
    #    (b) reverse each X/Y row independently, keeping its own label first;
    "X 4 42 32 2 Y 15 25 82 0",
    #    (c) reverse each coordinate pair by swapping X and Y within it;
    "(0,2)(82,32)(25,42)(15,4)",
    "0,2|82,32|25,42|15,4",
    #    (d) reverse the route/point order while preserving each (X,Y) pair.
    "(4,15)(42,25)(32,82)(2,0)",
    "4,15|42,25|32,82|2,0",
    # 5. The solved header (embeds B/H) joined to the instruction -- the two
    #    Phase 269 forms that actually depend on B/H; the literal-header and
    #    whole-block forms don't and are not repeated.
    f"{SOLVED_HEADER}\n{INSTRUCTION}",
    f"{SOLVED_HEADER} {INSTRUCTION}",
)

# Same automatic doubling Phase 269 uses: every base form also tested
# character-reversed, without hand-picking which one "matters". This is
# what reproduces the fork's own literal coordinate digit string.
CANDIDATES = BASE_FORMS + tuple(form[::-1] for form in BASE_FORMS)
CANDIDATE_DIGEST = hashlib.sha256("\n".join(CANDIDATES).encode()).hexdigest()


def audit():
    report = material_family(CANDIDATES, BLOBS)
    return {
        "candidates": CANDIDATES,
        "resolved_values": RESOLVED,
        "candidate_digest": CANDIDATE_DIGEST,
        "blob_names": tuple(sorted(BLOBS)),
        **report,
    }


def self_test():
    report = audit()
    assert report["resolved_values"] == {"S": 32, "H": 42, "B": 25, "Q": 82}
    assert report["blob_names"] == ("COSMIC", "P32TRAILING", "SALPH", "URLBLOB")
    assert report["candidate_count"] == len(BASE_FORMS) * 2
    # Confirms the fork's own literal reversed-digit coordinate string is
    # among the tested candidates, reproduced from the declared transform
    # family alone -- not hand-added.
    assert "5152280Y424232X" in report["candidates"]
    assert "X232424Y0822515" in report["candidates"]
    assert report["hits"] == []
    print(
        f"[*] self-test OK: {report['candidate_count']} fork-resolution "
        f"candidates (B=25, H=42) / {report['unique_material_count']} unique "
        f"key materials against all 4 tracked blobs; fork's literal digit "
        f"string confirmed present"
    )
    return report


def main():
    import argparse
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
