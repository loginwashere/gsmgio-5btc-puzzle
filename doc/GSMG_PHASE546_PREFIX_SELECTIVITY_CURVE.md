---
type: audit
phase: 546
date: 2026-09-21
status: complete
result: calibration-cherry-pickable
disposition: calibration-gate
script: tools/gsmg/phase546_prefix_selectivity_curve.py
topics:
  - btcseed
  - bifid
  - faed
---

# Phase 546 — selectivity curve for the BTCSEED prefix

2026-09-21. Result: **`cherry_pickable` under the pre-registered broad class (k3 = 4,948 of 362,880 squares; rate 1.36%)**.
The exact string is still rare (8 orderings, rate 2.2e-5). Option 2 of the
[BTCSEED tail options brainstorm](Brainstorms/2026-09-21%20-%20BTCSEED%20Tail%20Decoding%20Options%20Brainstorm.md).
Protocol: [Phase 546 protocol](Brainstorms/2026-09-21%20-%20Phase%20546%20Prefix%20Selectivity%20Curve%20Protocol.md),
locked before any class rate was computed for the real FAED (lock verified at run time).

## Question

Phase 425 fixed `BTCSEED` in advance and found the prefix unusual inside a 12-square family. The
target was chosen after looking. So: over a wide population of Bifid squares, how often does the
community decode of FAED give some prefix a reader could call meaningful? This is a calibration
gate on the prefix as evidence. It says nothing about the tail.

## Method

FAED and the decoder fixed (whole block, row-column, forward); only the square varies.
**Arm A (exact, gating):** all 9! = 362,880 squares with `A..I` in any order in the first nine cells, then
`K..Z`. **Arm B (sample):** 20,000,000 uniform random squares. Classes: E1 = exactly `BTCSEED`; E2 = a
7-letter dictionary word; E3 = E2, or a 3-letter token (dictionary word or `BTC`) plus a 4-letter
dictionary word in either order. Gate on `k3`: at least 37 is `cherry_pickable`, at most 3 is
`selective`, else `indeterminate`, with the declared assumption `T_max` = 10,000 squares tried.
Controls passed before the lock: vectorised prefix equals the full decode, the real ordering gives
`BTCSEED` and Phase 425's hash, class machinery, exact-vs-Monte-Carlo counting.

## Result

| Class | Arm A count (of 362,880) | Arm A rate | Arm B count (of 20M) | Arm B rate |
|---|---:|---:|---:|---:|
| E1 exact `BTCSEED` | 8 | 2.2e-5 | 2 | 1.0e-7 |
| E2 7-letter word | 2 | 5.5e-6 | 33 | 1.65e-6 |
| E3 broad class | 4,948 | 1.36% | 112,028 | 0.56% |

Outcome by the frozen gate: **`cherry_pickable`** (4,948 is far above 37).

Chance of at least one hit among `T` independent squares:

| T | E3, Arm A | E3, Arm B | E1, Arm A | E1, Arm B |
|---:|---:|---:|---:|---:|
| 12 | 0.152 | 0.065 | 0.0003 | 1e-6 |
| 1,248 | 1.0 | 0.999 | 0.027 | 0.0001 |
| 10,000 | 1.0 | 1.0 | 0.198 | 0.001 |

The most frequent E3 prefixes in Arm A are junk such as `FAAIEEE` (1,440 orderings), `ALAIEEE`,
`AVAIEEE`: the class is dominated by dictionary abbreviations and proper names, not phrases.

## What this supports, and what it does not

- The result stands as pre-registered: **a prefix that can be split into two words is not selective**.
  A reader looking at prefixes of natural-keyword squares would find something like it in a few
  squares, and seeing one does not separate design from post hoc reading.
- **Class dependence matters.** At the strict level the picture is different: E2 (a genuine 7-letter
  word) occurs in only 2 of 362,880 Arm A squares (rate 5.5e-6), which by itself would be `selective`
  under the same assumption. The exact string `BTCSEED` arises in 8 of the 362,880 orderings in Arm A
  (equivalent squares, one mechanism) and in 2 of 20 million random squares. So the gate's outcome
  comes from the breadth of E3, which the protocol disclosed, and not from an abundance of
  `BTCSEED`-like strings. No class or threshold was changed after seeing this.
- It does **not** say `BTCSEED` is accidental, does not change Phase 425's fixed-target p = 1/10001,
  and does not bear on the tail (Phases 426-428, 544, 545).
- Disposition for the branch: prefix-level evidence should not be used as the reason to spend more
  effort on the tail. A reason would have to come from an independent consumer or clue.

## Scope and stop

One run, one decoder, first seven letters, squares only. Do not add classes, thresholds,
prefix lengths, decoders or dictionaries after seeing this. `T_max` is an assumption.

## Reproduction

```bash
python3 tools/gsmg/phase546_prefix_selectivity_curve.py --self-test
python3 tools/gsmg/phase546_prefix_selectivity_curve.py --run   # verifies the lock first
```
