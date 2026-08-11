---
type: audit
phase: 236
date: 2026-08-11
status: verified
disposition: active
topics:
  - macro-chain
  - matrixsumlist
  - architect
related_phases:
  - 217
  - 223
  - 232
  - 233
  - 234
  - 235
script: tools/gsmg/macro_model_disposition_audit.py
aliases:
  - Phase 236
  - Macro Model Disposition Audit
---

# GSMG Macro-Model and Checkpoint-Disposition Audit

Phase 236 compares the two surviving readings of the authenticated macro
prefix without running a cipher or blob oracle:

```text
yellowblueprimes -> matrixsumlist -> lastwordsbeforearchichoice -> yinyang
```

Reproduce it with:

```bash
python3 tools/gsmg/macro_model_disposition_audit.py --self-test
```

## Model comparison

### Model A — selected 31 characters feed `matrixsumlist`

```text
yellowblueprimes
-> ncsyangcahiriasogaleafayanestve
-> matrixsumlist
-> UNKNOWN
```

The extraction is exact, but this model consumes only the first macro token.
It then requires seven fields that no primary source fixes: dimensions,
placement, traversal, letter values, aggregation, serialization, and target.

The selected text's `gale`/`leaf`/`nest`/`yang` cluster cannot upgrade it to a
recognition checkpoint. Phase 132's conservative broad-word control gave
`5469/1,000,000`, empirical `p=0.005469995`, just outside the project's fixed
`p<0.005` promotion threshold. Its correct disposition is therefore:

```text
structural checkpoint; parked
```

### Model B — the six-digit prime feeds `matrixsumlist`

```text
yellowblueprimes
-> 574061
-> `[[5,7,4],[0,6,1]]`
-> matrixsumlist = [23,16,7]
-> lastwordsbeforearchichoice
-> BOTH / ULTIMATELY / THE
-> BUT / HYE
-> yinyang still unverified
```

This model consumes three consecutive macro tokens and reaches the
cross-source-stable Architect boundary. It retains three visible judgment
calls: reading the digits as a forward 2x3 matrix, taking total then row sums,
and inspecting both word edges. Those prevent creator-confirmed promotion,
but Model B is substantially more complete than Model A and remains the
default working grammar.

## `BOTH` endpoint and polarity control

The exact clause is affirmative:

```text
... the anomaly revealed as both beginning and end.
```

It is not a negated or conditional “cannot save both” construction; the
two-door ultimatum follows afterward. This deflates the impossible-choice
polarity proposal while strengthening the narrower instruction to inspect
both edges.

Across the 48 cross-source-stable `BUT` rows, the eligible first words are:

| First word | Rows | Endpoints |
|---|---:|---|
| `BRINGS` | 16 | B/S |
| `BOTH` | 16 | B/H |
| `BEGINNING` | 16 | B/G |

Only `BOTH` has mirror9-related endpoints (`B↔H`), and all five
partial-mirror rows producing `BYE` begin with `BOTH`. This is real internal
support for the B/H edge observation.

It still does not authenticate the operation. The simpler mixed-edge rule
“beginning of the first word plus endings of the other two” produces `BYE` in
15/48 rows, so `BYE` alone is not the discriminator. The useful fact is the
conjunction of the fixed `[23,16,7]` selection, affirmative edge wording, and
`BOTH`'s own B/H endpoints.

## Puzzle-derived output roles

The verified solved chain emits several kinds of object:

- credentials;
- instructions;
- routes/URLs;
- prose carrying the next clue.

Therefore a recovered English word does not automatically have to be a
password. But the solved chain supplies no clean precedent for a
puzzle-derived, terminal recognition word that is simply left unconsumed.
`Bingo` cannot fill that role: it is an external creator reaction to a later
message, not an output produced by the puzzle. It also appears in the Tier-1
candidate corpus, so it is not a clean “never treated as candidate material”
control.

The evidence permits `BYE` to be non-credential control flow or recognition,
but does not prove that role. Existing direct-password negatives remain
consistent with it.

## Complete mirror-orbit table

| Origin | Best pair on DBBI | Best pair on FAED | Mirrored pair | Mirror on DBBI | Mirror on FAED |
|---|---:|---:|---|---:|---:|
| DBBI | `{b,e}` rank 1 | rank 17 | `{h,e}` | invalid | rank 16 |
| FAED | `{g,i}` rank 13 | rank 1 | `{a,c}` | rank 24 | invalid |

Each best pair segments both streams; each mirror fails on its origin stream
but segments the opposite stream. The `{b,e}` admissibility signature is
unique among all 36 pairs, while the `{g,i}` signature is shared by five.
Seventeen of 36 pairs and their mirrors segment both streams, so mirror closure
in general is common. Combined with the low opposite-stream ranks and the
completed `{h,e}` decoder negatives, this table is descriptive rather than a
new decoder selector.

## Disposition changes

- Model B is the default macro grammar.
- The exact 31-character selection is reclassified from the sole priority
  transition input to **Structural checkpoint; parked**.
- `BUT/HYE -> BYE` remains **Recognition checkpoint; parked**.
- `BYE` is not promoted to a credential or creator-confirmed recognition.
- No DBBI/FAED decoder, autokey/chain-addition run, or blob oracle is
  authorized.

Reopen the selected-31 branch only if primary evidence binds its exact input
to all seven missing consumer fields. Reopen BYE only if a source selects its
edge/mirror operation or identifies what consumes the result.
