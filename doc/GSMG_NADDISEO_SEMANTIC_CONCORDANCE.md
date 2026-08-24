---
type: index
status: live
date: 2026-08-24
topics:
  - naddiseo
  - concordance
  - semantic-comparison
aliases:
  - Semantic Concordance
---

# Naddiseo-versus-local semantic concordance

The full-repository audit (`doc/GSMG_NADDISEO_REPOSITORY_FULL_AUDIT.md`) was
file-complete: it confirmed nothing is hidden or missing. It was not
claim-by-claim complete: it did not check whether every *interpretive step*
the fork's notebooks take matches the step this project independently took
for the same clue. This document is that comparison, one clue at a time.
Each row records the exact source clue, the fork's interpretation, this
project's interpretation, the resulting value each side used, what
downstream work consumed that value, and a confidence/alternatives note.

Differences that change a password, key-material candidate, or other
consumed input outrank differences that only confirm an already-shared
result -- those get investigated (and, where cheap, re-tested) first.

## Entry 1 — `X2SH4Y0QB15`: the `B` and `H` variable resolution

**Exact source clue** (Phase 2 decrypted plaintext, `README.md`; identical
in both projects, byte-verified):

```text
# X 2 S H 4 Y 0 Q B 15 #
Q -> extend the name of a hackers' swordless fish, the I and W are below.
B -> ((BV80605001911AP)- (sqrt(-1)))^2
H -> (Answer to only this puzzle but nothing else) * -1
S -> cha' + (vagh * jav)
Ok kid, on the highway, let put it in the worst gear.
```

Both projects agree: `S = 32` (Klingon numerals) and `Q = 82` (Mr. Robot's
fish "Qwerty" extended to the keyboard row `QWERTYUIOP`; digits above `I`
and `W`, in that order). No discrepancy on these two.

### `B`

- **Fork interpretation** (`phase2.ipynb`, cell 4, commit `15b43fc`): the
  clue's `BV80605001911AP` is an Intel Core i5-750 processor model number.
  Read as "`i5` minus `i`", two parses are both grammatically available:
  `(5i - i)^2 = (4i)^2 = -16` ("choice 1"), or `(i5` *with* `i` removed`)^2
  = 5^2 = 25` ("choice 2"). The notebook explicitly holds both open
  ("we'll figure out which of the two choices we need later") and resolves
  it two sections down using the *output domain*: applying the `-16`
  reading inside the "worst gear" (reverse) instruction produces a
  string that parses as `61` minutes in a geographic DMS coordinate --
  not a valid sexagesimal value (minutes must be `< 60`) -- while `25`
  produces `52` minutes, valid. The fork picks `B = 25` on that basis.
- **Our interpretation** (`tools/gsmg/x2sh4y0qb15_p32_candidate_audit.py`,
  Phase 269): `RESOLVED = {..., "B": -16, ...}`, stated as "previously
  established" with no citation of the `25` alternative, the DMS-validity
  argument, or any other stated reason for preferring `-16`.
- **Resulting value:** fork `B = 25`; this project `B = -16`.
- **Downstream dependency:** this project's `B = -16` was carried into (a)
  `G-X2SH-001`'s Decentraland four-point candidate coordinates
  (`doc/GSMG_PHASE2_DECENTRALAND_COORDINATE_AUDIT.md`, `(-42,-16)` as one of
  the four pairs) and (b) Phase 269's full X2SH4Y0QB15 password-candidate
  sweep against all 4 tracked blobs (`COSMIC`, `P32TRAILING`, `SALPH`,
  `URLBLOB`) -- meaning that sweep never actually tested any material built
  from `B = 25`.

### `H`

- **Fork interpretation:** "`* -1`" is read as *already accomplished* by
  the semantic negation used to reach the answer: negating "answer to only
  this puzzle but nothing else" gives "answer to everything," which *is*
  the Hitchhiker's Guide's `42` -- i.e., the phrase-level negation already
  performs the instructed `* -1`, so the notebook uses `H = 42` with no
  further arithmetic step.
- **Our interpretation:** `RESOLVED = {..., "H": -42, ...}` -- the
  Hitchhiker's-Guide `42` is derived the same way, then a second, literal
  arithmetic `* -1` is applied on top of that number, giving `-42`.
- **Resulting value:** fork `H = 42`; this project `H = -42`.
- **Downstream dependency:** same two consumers as `B` above -- both used
  `H = -42` throughout.

### Confidence and unresolved alternatives

The fork's resolution is better-supported on its own terms: it has an
explicit, checkable tie-breaker for `B` (DMS-minute validity) that this
project's own docs implicitly rely on without recording -- `doc/
GSMG_PHASE2_DECENTRALAND_COORDINATE_AUDIT.md` already calls "the
established SafeNet reading" (one global reversal producing "one standard
geographic coordinate") authoritative enough to be preferred over the
Decentraland reading, but that exact coordinate (`51°52'28.0"N
4°24'23.2"E`, near a real SafeNet/Thales facility) only reproduces under
`B = 25, H = 42` -- values this project's own scripts never used. This is
an internal inconsistency, not merely a difference of opinion: the doc
defers to a reading its own candidate-generation script doesn't test.

The `H` question is softer -- both semantic negation *of the phrase* and a
subsequent literal negation *of the resulting number* are defensible
readings of "(...) * -1" in isolation. The fork's reading is preferred here
only because it's the one that, combined with `B = 25`, reproduces a
verified real-world coordinate; this project's `-42` was never
independently checked against that same target.

Neither project treats `X2SH4Y0QB15` as consumed into the real,
already-solved 7-part password (`README.md` calls its use "unclear," and
the fork's own notebook only uses the coordinate as thematic confirmation
of the SafeNet/Luna/HSM reading already reached by other clues, not as
password material). So this discrepancy does not touch anything
already-solved. It only matters for still-open candidate-generation work
downstream of `X2SH4Y0QB15` -- which is exactly what Phase 269 is.

**Action taken:** Phase 384 (`tools/gsmg/x2sh4y0qb15_fork_resolution_delta_audit.py`)
reruns Phase 269's exact declared transform family under `B = 25, H = 42`
instead of `B = -16, H = -42`, against all 4 tracked blobs: 26 candidates,
650 unique key materials, **0 hits**. See `FINDINGS.md` Phase 384 for the
full result.

## Entries 2+ — not yet built

The remaining six notebooks (`phase0`, `phase1`, `phase2.1`'s embedded
content, `phase3`, `phase3.2`, `salphaseion`, `decentraland`) and the 34
`hints/` images have not yet been walked clue-by-clue against this
project's own interpretation of the same material. This document should be
extended one clue at a time, following the same schema as Entry 1, ranking
password/input-altering discrepancies above confirmation-only ones.
