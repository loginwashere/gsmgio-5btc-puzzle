---
type: audit
phase: 547
date: 2026-09-28
status: complete
result: null-like
disposition: closed-negative
script: tools/gsmg/phase547_nine_symbol_origin_census.py
topics:
  - faed
  - dbbi
  - nine-symbol-alphabet
  - trifid
---

# Phase 547 — nine-symbol origin census

2026-09-28. Result: **null-like in all three gated cells; 0 valid Morbit and Pollux maps in all four streams.**
Protocol: [Phase 547 protocol](Brainstorms/2026-09-24%20-%20Phase%20547%20Nine-Symbol%20Origin%20Census%20Protocol.md),
locked before any M1 or M2 real statistic was computed (lock verified at run time).

## Question

DBBI and FAED use nine symbols `a..i` and never `o`, so the nine-symbol alphabet is native to whatever
produced them. The nine-column straddling checkerboard has had most of the attention. This phase tests
the other native nine-symbol producers that had never been tested (or only partly), each with an exact
or key-invariant statistic:

- **M1:** keyed Trifid coordinates, two trits per symbol, regrouped in threes. The 27-cell IoC does not
  depend on the unknown cube, so it covers all 9! symbol maps, all three offsets and every cube alphabet.
  This covers more than Phase 277 did.
- **M2:** phone multi-tap, with one symbol as `X` (C1 pause, C2 word space) and the other eight as keys
  2..9. That gives 9 x 8! maps, scored by quadgrams.
- **M3 / M4:** Morbit (9! pair maps) and Pollux (3^9 maps), with exact International Morse validity,
  forward and reversed.

## Controls (before the lock, all passed)

| Control | Result |
|---|---|
| Machinery | vectorized M1 IoC and M2 decode equal direct computation (M2: 306 maps) |
| M1 planted (Architect text, 5 offsets) | true map and offset reach the family maximum every time; IoC 0.064-0.066 vs null p99 0.043-0.049 |
| M2 planted C1 / C2 | true map valid and is the family maximum (-4.20 / -4.18) vs null maximum -6.97 / -6.99 |
| Morse planted | Morbit 2 valid maps including the true key; Pollux 5 valid |

## Result

| Cell | Real | Null median | Raw p | Holm | Outcome |
|---|---:|---:|---:|---:|---|
| M1-FAED (gated) | IoC 0.0444 | 0.0433 (p99 0.0454) | 0.098 | 0.196 | null-like |
| M2-FAED (gated) | -7.75 | -7.59 | 0.856 | 0.856 | null-like |
| M2-DBBI (gated) | -6.10 | -6.62 | 0.012 | 0.036 | null-like |
| M1-DBBI (reported only) | IoC 0.0785 | 0.0774 (p99 0.0955) | 0.447 | — | — |

- M1-FAED's best value over all maps and offsets is 0.0444. The planted Trifid texts gave 0.064-0.066,
  with an English expectation near 0.066. FAED behaves like a shuffle.
- M2: no map satisfies C1 (pause) for either stream. Only C2 produces decodes. The M2-DBBI best decode
  (`PBJAMATHADAJTWAAJTAEDABD...`, `e` as space) is not text. Its raw p of 0.012 does not survive Holm
  correction and has no follow-up under the stop rule.
- M3 / M4: 0 valid Morbit maps and 0 valid Pollux maps for FAED and DBBI, forward and reversed.

Census verdict, as the protocol defines it: **no untested native nine-symbol producer remains in this
declared census.**

## What this supports, and what it does not

- It closes keyed Trifid coordinate regrouping (any cube, any symbol map, any offset), phone multi-tap
  under the two conventions, Morbit and Pollux as the origin of the `a..i` alphabet.
- It formalizes the unlocked Morbit/Pollux pre-screens of 2026-09-24 under a lock with planted controls.
  The pre-screen results were known before this run; see the protocol's disclosures.
- It does not cover periodic Trifid fractionation (Phase 146), predictive T9, other keypad layouts,
  ten-digit ACA ciphers (excluded by definition), or the straddling checkerboard family. It does not
  show that no process could produce the alphabet.

## Scope and stop

One run. Do not add maps, offsets, conventions, keypad layouts, statistics or members after seeing this.

## Reproduction

```bash
python3 tools/gsmg/phase547_nine_symbol_origin_census.py --self-test
python3 tools/gsmg/phase547_nine_symbol_origin_census.py --run   # verifies the lock first (~34 min, 16 cores)
```
