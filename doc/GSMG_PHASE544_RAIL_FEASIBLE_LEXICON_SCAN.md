---
type: audit
phase: 544
date: 2026-09-21
status: complete
result: closed-negative
disposition: rejected
script: tools/gsmg/phase544_rail_feasible_lexicon_scan.py
topics:
  - btcseed
  - bifid
  - faed
---

# Phase 544 — rail-feasible lexicon scan of the BTCSEED decode

2026-09-21. Result: **null-like; family-corrected p = 0.050 against a 0.01 bar**. Option A1 of the
[BTCSEED tail options brainstorm](Brainstorms/2026-09-21%20-%20BTCSEED%20Tail%20Decoding%20Options%20Brainstorm.md).
Protocol: [Phase 544 protocol](Brainstorms/2026-09-21%20-%20Phase%20544%20Rail-Feasible%20Lexicon%20Scan%20Protocol.md),
locked before the real tail was scored (lock verified, null recomputed and matched, at run time).

## Question

The community decode (DBBI-keyed square, one 570-symbol block) starts `BTCSEED`. Output letters
2k and 2k+1 depend only on FAED[k] and FAED[285+k], and all FAED symbols sit in the square's first
two rows, so the even output rail can only be B/C/D/E. Does the tail contain dictionary words
rarer than that exact mechanical null produces?

## Method

Every occurrence (offset 7 or later) of an ASCII dictionary word of 5-20 letters
(67,696 words) is scored by its surprisal under the rail model (row marginals for the even
rail, column marginals for the odd rail, from the exact FAED multiset). S1 is the largest
surprisal; S2 is the best non-overlapping cover. Null: 10,000 exact-multiset FAED shuffles,
family correction over (S1, S2) by the Phase 426-428 rank-max rule.

Controls passed before the lock: decode reproduces the Phase 425 hash with even rail exactly
`{B,C,D,E}` (also in 200 shuffles); model sums to 1 and matches 4,000 shuffled decodes within 0.01;
toy scan and cover correct; planted dictionary words recovered as the top occurrence in both
alignments (length 8: family p 0.0003 and 0.0001, the gate; length 6 about 0.0046 in each alignment; no
10-letter word could be planted at the even alignment).

## Result

| Statistic | Real tail | Null 99th pct | p |
|---|---:|---:|---:|
| S1 (rarest occurrence) | 17.6 bits (`MEDEA` at 129) | 20.7 | 0.174 |
| S2 (best cover) | 48.7 bits | 53.7 | 0.028 |
| Family-corrected | | | **0.050** |

The tail has only three dictionary occurrences of 5 or more letters: `MEDEA` (129), `ENDUE`
(218) and `MELDS` (351), 17.6, 15.0 and 16.1 bits. The puzzle-word arm (`YOUWON`, `KMODEST`,
`MODEST`, `SATOSHI`, `SEED`, `KEY`, `WALLET`) finds none past the prefix (p = 1.0). No oracle
or key-shape check was part of this phase.

## What this supports

- Under an exact rail-aware null, the tail's dictionary content is null-like at the declared
  bar. The corrected p of 0.05 is above 0.01 and is not a lead; it also does not change
  Phases 426-428.
- The instrument has power: planted 8-letter words were recovered at family p of 0.0003 or
  better.
- It bounds one decode, one lexicon and two statistics. It says nothing about non-dictionary
  content, typed streams, other squares, or any blob, key or address.

## Scope and stop

One configuration, one run. Do not add dictionaries, lengths, squares, periods, statistics
or single-rail reads after seeing this. The Phase 386 addendum had previously scanned this
tail's dictionary words, so the outcome was not blind in that sense; development used only
shuffles and planted words.

## Reproduction

```bash
python3 tools/gsmg/phase544_rail_feasible_lexicon_scan.py --self-test
python3 tools/gsmg/phase544_rail_feasible_lexicon_scan.py --run   # verifies the lock first
```
