---
type: audit
phase: 238
date: 2026-08-11
status: closed-negative
disposition: active
topics:
  - macro-chain
  - matrixsumlist
  - page-structure
related_phases:
  - 101
  - 236
script: tools/gsmg/page_syntax_house_style_audit.py
aliases:
  - Phase 238
---

# GSMG Page-Syntax House-Style Audit

Phase 238 tests whether the other authenticated SalPhaseIon instruction slots
establish a reusable directional “house style” capable of fixing
`matrixsumlist` or `thispassword`. It combines the byte-exact page segmentation,
the Phase-101 grammar family, the independently structured `enter` control,
the presentation-layer negative, and Phase 236's default macro model. It runs
no transform, decoder, or blob oracle.

Reproduce it with:

```bash
python3 tools/gsmg/page_syntax_house_style_audit.py --self-test
```

## Exact slot inventory

| Slot | Transport | Physical position | Independently constrained role |
|---|---|---|---|
| `matrixsumlist` | binary ASCII | DBBI `[slot]` FAED | Default external macro step `574061 -> [23,16,7]`, but three judgment calls remain; local direction unfixed |
| `lastwordsbeforearchichoice` | decimal | after FAED, before `thispassword` | Default external Architect selector reaching `BUT/HYE`; local page neighbors are not its source operand |
| `thispassword` | decimal | after `lastwords...`, before SHA phrase | Deictic label; three Phase-101 roles remain |
| `sha256 our first hint is your last command` | raw mixed text | immediately before SALPH | Algorithm named; operand referents unresolved |
| `enter` | binary ASCII | between SALPH Base64 pieces | **Fixed infix formatting join**: removing it reconstructs one authenticated 128-character blob from equal 64-character halves |
| `sha256 + anstoo` | raw mixed text | immediately after SALPH | SHA marker fixed; literal `anstoo` unresolved |

The HTML contributes no hidden separator, line, class, or markup binding: all
SalPhaseIon characters occupy one uniformly spaced textarea node. Transport
encoding and presentation therefore cannot silently supply the missing
direction.

## Falsification controls

Six candidate house rules were declared and checked:

| Proposed rule | Result | Counterexample |
|---|---|---|
| Every instruction is prefix | fail | `enter` is fixed infix |
| Every instruction is postfix | fail | SHA phrase precedes SALPH; `enter` is infix |
| A token between payloads means join | fail | Only `enter` has equal operands and an authenticated joined object; DBBI/FAED do not |
| Transport encoding fixes role | fail | Binary carries both fixed formatting `enter` and unresolved `matrixsumlist`; raw SHA markers occur on opposite sides |
| Nearest page neighbor is the operand | fail | The best current `lastwords...` role selects an external Architect passage |
| SHA prefix/suffix form a complete bracket | fail | The prefix referents and suffix `anstoo` remain unresolved |

**Zero of six rules survives.** The positive `enter` control demonstrates the
standard required to bind a slot: adjacency plus an independently valid
consumer structure. Position alone is insufficient.

## Effect on the Phase-101 model family

Phase 101 enumerated `3 x 3 x 3 x 2 = 54` local models and found zero strictly
supported model. Under the current *working* Model B, the three-way local
`matrixsumlist` direction can be projected away because the macro consumes it
externally. That leaves `3 x 3 x 2 = 18` distinct password/SHA/tail models;
only nine are structurally total, and all nine require the unsupported
`anstoo -> answer too` expansion.

This reduction is conditional, not creator-authenticated. It is bookkeeping
for the current frontier, not evidence that one of the 18 is correct.

## Verdict

The page uses mixed syntax and does not expose an empirical uniform house
style. The independently fixed slots do not select prefix, postfix, infix,
transport-based, or nearest-neighbor semantics for the unresolved slots.
Consequently:

- `matrixsumlist` remains locally directionless even though Model B is the
  default external macro reading;
- `thispassword`, the SHA operand, and `anstoo` remain unresolved;
- the selected-31 row stays parked;
- no transform, password family, or blob oracle is authorized.
