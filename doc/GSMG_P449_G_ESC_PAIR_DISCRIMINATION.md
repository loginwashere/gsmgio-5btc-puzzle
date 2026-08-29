---
type: audit
phase: 449
date: 2026-08-29
status: parked
result: inconclusive
disposition: structural-only
topics:
  - G-ESC-001
  - FAED
  - escape-pair
  - selector
---

# Phase 449 — G-ESC-001 Pair Discrimination

## Result

`{g,i}` is the strongest working prior for a FAED checkerboard decoder, but
neither `{g,i}` nor `{h,e}` is selected by authenticated evidence. G-ESC-001
therefore remains parked and unreconciled.

The distinction matters: FAED's internal statistics strongly rank `{g,i}`
over `{h,e}`, but those statistics presuppose the ordinary-English
checkerboard model. `{h,e}` is produced exactly by the Architect mirror route,
but that route depends on the still-unselected G-ARCH-001 mirror operation.
Neither conditional argument excludes the other candidate at pair level.

## Candidate comparison

| Constraint | `{g,i}` | `{h,e}` | What it establishes |
|---|---|---|---|
| Complete FAED segmentation | 436 codes; all 25 types | 469 codes; all 25 types | Both admissible; no contradiction |
| Code IC near English `0.067` | `0.07429`, rank 1/29 valid pairs | `0.09817`, rank 16/29 | Favors `{g,i}` conditional on English checkerboard plaintext |
| Escape-character/profile fit | 31.93%; rare but reachable in audited English | 22.28%; 78.46% top-code profile outside audited English corpora | Strongly disfavors `{h,e}` under the same model, not unconditionally |
| Share of FAED's non-uniform chi-square | 73.75% | 2.19% | Strong descriptive `{g,i}` ranking; not a sourced escape rule |
| Architect `BUT/HYE` mirror | Not produced | Exactly `mirror9({b,e})` | Conditional `{h,e}` support; depends on G-ARCH-001 |
| Creator `YING/YANG` parse | `YING -> IG` exactly | Not produced | Rejected as selector: typo disclaimer and authenticated `yinyang` spelling |
| Page/archive presentation | No selector | No selector | Tie; page branch exhausted across 16 successful capture events |
| Pair-specific decoder tests | Monoalphabetic `p=0.0396`; chain-addition 0 hits | Monoalphabetic `p=0.63366`; curated chain/autokey/direct seeds 0 hits | `{g,i}` is less null-like, but neither pair is falsified |
| FAED Bifid `BTCSEED` | Pair not used | Pair not used | Escape-independent and non-discriminating |

## Independence audit

The apparent amount of `{g,i}` evidence must not be counted as three or four
independent votes. Code IC, escape density, and English-profile reachability
are correlated views of one `FAED + English checkerboard` assumption. Raw
symbol non-uniformity is a simpler, partially independent descriptive signal,
but it still does not say which symbols the creator designated as escapes.

The exact creator `YING -> IG` alignment is a separate lexical observation,
but Phase 225's authorship gate failed: the creator explicitly rejected typo
clues, and the authenticated binary macro uses standard `yinyang`. It remains
an explanation candidate, not a selector.

`{h,e}` has one genuinely different positive evidence group: the Architect
macro/mirror derivation. It is exact once the mirror rule is assumed, but the
rule itself is exactly what G-ARCH-001 says no creator clue selects. Treating
that dependent derivation as decisive would close one parked gap by assuming
another.

## Contradiction audit

Neither pair is contradicted at pair level:

- both segment all 570 authenticated FAED symbols and use all 25 code types;
- `{h,e}`'s profile mismatch contradicts only the hypothesis “ordinary English
  encoded directly under this checkerboard segmentation,” not every possible
  role for `{h,e}`;
- the monoalphabetic, chain-addition, autokey, direct-seed, mirror-substitution,
  and blob-oracle negatives are tied to decoders/consumers the clue never fixed;
- `{g,i}`'s better `p=0.0396` monoalphabetic result still failed the frozen
  project threshold and cannot be promoted by relative comparison with
  `{h,e}`'s worse result;
- the family-corrected `BTCSEED` Bifid checkpoint does not use either escape
  pair, and its continuation was attributed to Bifid digraph mechanics.

## Selection gates

| Gate | `{g,i}` | `{h,e}` |
|---|---:|---:|
| Valid on complete FAED | pass | pass |
| Independent authenticated selector | fail | fail |
| Rival excluded or roles reconciled | fail | fail |
| No load-bearing parked-gap dependency | pass | fail (`G-ARCH-001`) |

Decision: `remain_unreconciled_with_gi_as_working_prior`.

## What would actually reopen the gap

Useful new evidence must do one of two things:

1. a creator clue or primary artifact outside the unchanged SalPhaseIon page
   explicitly selects one pair or explains that `{g,i}` and `{h,e}` serve
   different roles; or
2. an authenticated clue fixes a decoder and a pair-independent validator,
   making the current pair ranking a decisive test rather than a model choice.

More page captures with known hashes, another free decoder menu, larger
wordlists, or rerunning pair-specific blob oracles do not meet that bar.

## Reproducibility

- Frozen protocol: `doc/Brainstorms/2026-08-29 - Phase 449 G-ESC-001 Pair Discrimination Protocol.md`
- Audit: `tools/gsmg/phase449_g_esc_pair_discrimination_audit.py`
- Tests: `tools/gsmg/test_phase449_g_esc_pair_discrimination_audit.py`
- Result: `tools/gsmg/phase449_result.json`
- Result SHA-256: `0c25de2f6d5681f8e039a6af0afd6f84cebda5f84232b883223166bf95f2e88c`

No password material, oracle call, GPU, Docker, network, or external agent was
used.
