# Phase 431 — Phase-430 Bifid `16!` Output-Equivalence Audit

## Question

How many of Phase 430's `16! = 20,922,789,888,000` alphabet ranks produce
genuinely distinct 570-character decoded strings, and why does its retained
GPU shortlist contain large clusters of identical decodes?

This is a combinatorial accounting audit. It does not change the sealed Phase
430 score, inspect new cipher families, or invoke a language, password,
Bitcoin, or blob oracle.

## Frozen family reused

- base square: `DBIFHCEGAKLMNOPQRSTUVWXYZ`;
- free symbols: `GHKLMNOPQRUVWXYZ`;
- the same sixteen free positions and lexicographic `16!` domain as Phase 430;
- the authenticated normalized 570-letter `FAED`, SHA-256
  `585ee5d801486348f3396b3301bc87f14420204ed3242e67bc53d60cfed14664`;
- Phase 386/430's one-block, row-then-column Bifid decryption convention.

## Exact equivalence construction

There are `16 × 15 = 240` ordered placements of `G` and `H`. Once one such
placement is fixed, every input-letter coordinate is fixed because the other
seven FAED source symbols remain in fixed cells. The complete 570-cell output
path is therefore fixed.

For each placement, the audit replaces every visited non-`G/H` free cell by a
placeholder numbered by first occurrence. Fixed-cell outputs and outputs from
the `G/H` cells remain literal letters. This is its canonical output template.

If a template visits `m` of the other fourteen free cells, its number of
distinct decoded strings is `P(14,m) = 14! / (14-m)!`. Each such decoded
string has `(14-m)!` rank representations, because symbols in invisible free
cells can be permuted without changing any output position.

Canonical templates also give an exact cross-placement test. Placeholder
letters are drawn injectively from `KLMNOPQRUVWXYZ`, while literals are drawn
from the disjoint fixed/`G/H` set. Therefore two templates can share an output
only if their literal positions and letters agree and their placeholder
equality partitions agree. First-occurrence canonicalization makes that
condition exact template equality. All 240 templates are distinct, so there
are no cross-placement output collisions.

## Results

| Visible other free cells `m` | Ordered `G/H` placements | Ranks per decoded output | Distinct decoded outputs |
|---:|---:|---:|---:|
| 5 | 42 | `9! = 362,880` | 10,090,080 |
| 10 | 6 | `4! = 24` | 21,794,572,800 |
| 11 | 12 | `3! = 6` | 174,356,582,400 |
| 12 | 38 | `2! = 2` | 1,656,387,532,800 |
| 13 | 12 | 1 | 1,046,139,494,400 |
| 14 | 130 | 1 | 11,333,177,856,000 |
| **Total** | **240** | — | **14,231,866,128,480** |

The exact unique-output fraction is `0.6802088155864198`. An ideal
equivalence-aware enumerator can omit `6,690,923,759,520` duplicate ranks, or
`31.979118441358023%` of the raw domain. The raw-to-unique ratio is
`1.4701367831257564`.

As a conservation check, multiplying every output count by its corresponding
rank multiplicity reconstructs exactly `20,922,789,888,000 = 16!` ranks.

## Verification

The implementation includes three regressions:

1. the complete census must reproduce all table values and reconstruct `16!`;
2. for a five-visible-cell placement, swapping two of its nine invisible-cell
   symbols must leave the full decoded string byte-identical;
3. swapping two visible-cell symbols must change the decoded string.

Run:

```bash
cd tools/gsmg
python3 -m unittest test_phase431_bifid16_equivalence_class_audit.py
python3 phase431_bifid16_equivalence_class_audit.py --output phase431_result.json
```

## Interpretation

The duplicate effect is highly nonuniform. Most placements expose thirteen or
all fourteen remaining free cells and have no rank duplication. The 42
five-visible-cell placements instead have `362,880` equivalent ranks per
decoded string. A high-scoring output in that region consequently floods a
block-winner shortlist with equivalent ranks, explaining Phase 430's observed
1,000 retained rows collapsing to only a few distinct decoded strings.

Future searches can enumerate ordered `G/H` placements and injective
assignments only to visible cells, reducing this exact family by 31.98% while
preserving its global maximum. Candidate-review tooling should always collapse
full decoded-string duplicates before reporting semantic diversity.

The running Phase 430 sweep should **not** be restarted: it is already well
advanced, remains exact, and its remaining raw work is comparable to a new
reduced run after implementation and validation overhead. Phase 431 improves
future enumeration and current result interpretation; it does not invalidate
Phase 430.

## Artifacts

- `tools/gsmg/phase431_bifid16_equivalence_class_audit.py`
- `tools/gsmg/test_phase431_bifid16_equivalence_class_audit.py`
- `tools/gsmg/phase431_result.json`
