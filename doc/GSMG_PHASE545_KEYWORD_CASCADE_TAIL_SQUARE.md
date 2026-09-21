---
type: audit
phase: 545
date: 2026-09-21
status: complete
result: closed-negative
disposition: rejected
script: tools/gsmg/phase545_keyword_cascade_tail_square.py
topics:
  - btcseed
  - bifid
  - faed
---

# Phase 545 — keyword cascade and tail-derived squares

2026-09-21. Result: **null-like; family-corrected p = 0.025 against a 0.01 bar**. Options 4 and 5 of the
[BTCSEED tail options brainstorm](Brainstorms/2026-09-21%20-%20BTCSEED%20Tail%20Decoding%20Options%20Brainstorm.md).
Protocol: [Phase 545 protocol](Brainstorms/2026-09-21%20-%20Phase%20545%20Keyword%20Cascade%20and%20Tail-Derived%20Square%20Protocol.md),
locked before any cascade decode was scored (lock verified at run time).

## Question

The community decode keys its Bifid square from `DBBI[:13]` and yields `BTCSEED...`. If output-derived
keywords are fed back as the next square's key (options 4), or used to decode the project's other 91-symbol
strings (option 5), does anything unusual come out? Phase 425 had excluded output-derived words; Phases 419
and 476 tested an outside keyword and one P91 square over Q472, not this universe.

## Universe

Keyword rules: prefix of 7, prefix of 13, or the whole decode (deduplicated), iterated three times from
`DBBI[:13]`, giving nine FAED decodes and nine distinct new squares. Under each new square, `DBBI` and
`VALIDATION_ANSWER` were also decoded. That is 27 cells. Each decode was scored with Phase 544's rail-aware
lexicon statistics (generalised to any square and odd block lengths) against 10,000 exact-multiset shuffles,
with FAED cascade cells regenerating the whole cascade on each shuffle. One rank-max family correction over
27 cells x 2 statistics.

Controls passed before the lock: construction (Phase 425 hash, Phase 476's P91 square, `BTCSEED` keyword),
Bifid round trips at block lengths 570, 91 and 90, the generalised model equals Phase 544's on FAED, and planted
words recovered at both lengths under the right square (corrected p about 0.0001) and not under a wrong one.

## Result

The chains never cycle or return to the baseline square within depth 3. The three chains' squares:

| Rule | Step 1 | Step 2 | Step 3 |
|---|---|---|---|
| 7 | `BTCSEDAFGHIKLMNOPQRUVWXYZ` | `AKFDBZCEGHILMNOPQRSTUVWXY` | `AIFCMBDEGHKLNOPQRSTUVWXYZ` |
| 13 | `BTCSEDOMAFGHIKLNPQRUVWXYZ` | `OYMQBZHSGECADFIKLNPRTUVWX` | `DLEHXSRABCFGIKMNOPQTUVWYZ` |
| full | `BTCSEDOMKAHVXPRIQNGLUZFWY` | `ZRKUBYOQLICTMWPHDVSNXGEFA` | `ANGMSOIQFCPYDWZUXVRLTBEHK` |

Most cells had no dictionary occurrence of 5 or more letters. The exceptions:

- FAED, rule `full`, step 1 (square keyed by the deduplicated `D0`): six occurrences, `TRACK` (102),
  `SWING` (202), `BRICK`/`BRICKS`/`RICKS` (242-243), `SPECS` (382); `S2` 85.3 bits, nominal p = 0.001. It is
  the strongest cell, and the words are scattered, unrelated, and read as noise.
- Other single-word cells: `ALICIA`, `BIDET`, `PHIAL`, `CRAGS` (FAED); `FAZED`, `AURAS` (`VALIDATION_ANSWER`).
  Every `DBBI` cell had zero occurrences.

Family-min p (best of 54 columns) is 0.0006; family-corrected p is **0.025**, above the 0.01 bar. Outcome
`null_like`. A best-of-54 nominal 0.001 is what noise gives.

## What this supports

- Under these deterministic keyword rules the FAED cascade and the derived squares over `DBBI` and
  `VALIDATION_ANSWER` produce nothing beyond the null at the declared bar.
- It does not say anything about other rules, depths, objects, periods, other decoders or any blob, key
  or address, and it does not change Phases 425-428 or 544.
- Power at 91 symbols is low; those cells mainly bound gross effects.

## Scope and stop

One universe, one run. Do not add rules, depths, objects, periods, directions, squares, lexicons or
statistics after seeing this, and do not treat the `full`-rule step-1 cell as a lead: it is the maximum of 54
correlated columns and was not pre-selected. The dynamic null does not condition on `BTCSEED` being the
observed prefix.

## Reproduction

```bash
python3 tools/gsmg/phase545_keyword_cascade_tail_square.py --self-test
python3 tools/gsmg/phase545_keyword_cascade_tail_square.py --run   # verifies the lock first
```
