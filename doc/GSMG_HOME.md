---
type: index
status: live
date: 2026-08-11
---

# GSMG 5 BTC Puzzle — Home

Entry point for this vault. [README.md](../README.md) is the historical
community-solution walkthrough (Phases 1–3, all publicly solved); this note
is the current, actively-maintained research state. See
[Current vs. historical](#current-vs-historical) below before trusting a
statement found by search alone.

## Current verified frontier

The open boundary, per
[GSMG_STRICT_TRANSITION_WORKSHEET](GSMG_STRICT_TRANSITION_WORKSHEET.md):

```text
yellowblueprimes -> matrixsumlist -> lastwordsbeforearchichoice -> yinyang
```

Default working model (Phase 236,
[GSMG_MACRO_MODEL_DISPOSITION_AUDIT](GSMG_MACRO_MODEL_DISPOSITION_AUDIT.md)):

```text
574061 -> `[[5,7,4],[0,6,1]]` -> `[23,16,7]`
  -> BOTH / ULTIMATELY / THE  (Architect film/screenplay)
  -> BUT / HYE                (cross-source-stable boundary)
  -> BYE                      (partial_mirror9, recognition only)
  -> CIAO BELLA O              (authenticated page text, not creator-selected)
  -> UNKNOWN CONSUMER          <- live frontier
```

See also [[GSMG Frontier.canvas|the Frontier canvas]] for a visual map of
this chain.

## Open transition rows

From the worksheet's master table — rows still live or parked, not closed:

| Row | Disposition |
|---|---|
| 31-char DBBI selection -> `matrixsumlist` | **Structural checkpoint; parked** (Phase 236) |
| Decimal matrix -> `[23,16,7]` -> Architect words -> BYE -> CIAO BELLA O | **Recognition checkpoint; parked** |
| DBBI/FAED -> creator's `yinyang` state | **Live semantic boundary, not executable** |
| Prime lists -> `401/400/73` | Structural checkpoint only |
| Matrix product -> `(255,103)` / `FF67` | Strong arithmetic checkpoint; parked |
| Second matrix list difference -> reversed `KIT` | Parked; never a password |
| FEFE tuple `{1,4,21}` -> `ggn` -> secp256k1 | Narrative hypothesis; parked |

Full table with G1–G5 gate detail:
[GSMG_STRICT_TRANSITION_WORKSHEET](GSMG_STRICT_TRANSITION_WORKSHEET.md).

## Highest-value missing evidence

See [GSMG_OPEN_GAP_REGISTRY](GSMG_OPEN_GAP_REGISTRY.md) for the full,
per-gap table. All three P0 gaps are now locally exhausted — each depends
entirely on new primary evidence, not further re-derivation from what is
already on hand:

- The physical *Cosmic Duality* book's pages 57–58 gatefold — the only
  genuinely uninspected primary source for `matrixsumlist`'s operation
  ([G-MSL-001](GSMG_OPEN_GAP_REGISTRY.md); `external`).
- A source reconciling FAED's independently-best `{g,i}` escape pair with
  the Architect-mirror-predicted `{h,e}` pair
  ([G-ESC-001](GSMG_OPEN_GAP_REGISTRY.md); `parked` — the page-markup branch
  and all 5 known Wayback captures are exhausted as of Phase 243/244).
- Creator evidence defining the DBBI/FAED operator itself
  ([G-YIN-001](GSMG_OPEN_GAP_REGISTRY.md); `parked` — the Telegram corpora
  and every decoded-slot page-syntax rule are already exhausted).

The frontier is honestly exhausted pending new primary evidence, not stalled
for lack of trying — see each gap's row for exactly what was checked.

## Recently completed phases

See [GSMG_PHASE_INDEX](GSMG_PHASE_INDEX.md) for the full generated table of
all 246 phases. Most recent:

| Phase | Subject | Result |
|---|---|---|
| 245 | Creator personal-disclosures audit | Netherlands residency and substance-use references verified, both provenance-only |
| 244 | DBBI/FAED cross-capture stability | SalPhaseIon textarea byte-identical across all 5 known Wayback captures; G-ESC-001 page-boundary branch fully closed |
| 243 | DBBI/FAED boundary page-selector audit | Textarea markup/CSS/JS branch of G-ESC-001 closed negative |
| 242 | SVG/PNG edge geometry | C9 channel closed: contour-bound, zero residue |
| 241 | Favicon Wayback chronology | Bytes authenticated to 2019-04-28; chronology unresolved |
| 240 | Shadow/macro length + FAED factor calibration | Nesting real but dependency-dense; width 38 not selected |
| 238 | Page-syntax house-style audit | Mixed grammar, no directional selector |

## Canonical documents

- [GSMG_STRICT_TRANSITION_WORKSHEET](GSMG_STRICT_TRANSITION_WORKSHEET.md) — the 5-gate evidence-discipline worksheet; start here for any new candidate.
- [GSMG_FACT_LEDGER](GSMG_FACT_LEDGER.md) — what claims are currently accepted, with exact scope.
- [GSMG_OPEN_GAP_REGISTRY](GSMG_OPEN_GAP_REGISTRY.md) — what specific evidence would unblock progress, per gap.
- [GSMG_PHASE_INDEX](GSMG_PHASE_INDEX.md) — generated index of all FINDINGS.md phases.
- [GSMG_PHASE_TEMPLATE](GSMG_PHASE_TEMPLATE.md) — standard fields for new phase entries.
- [GSMG_OBJECT_DBBI](GSMG_OBJECT_DBBI.md), [GSMG_OBJECT_FAED](GSMG_OBJECT_FAED.md) — pilot per-artifact reference pages.
- [tools/gsmg/FINDINGS.md](../tools/gsmg/FINDINGS.md) — full chronological research log (243 phases).
- [GSMG_STAGE_INPUT_OUTPUT_SUMMARY](GSMG_STAGE_INPUT_OUTPUT_SUMMARY.md) — solved-chain input/output map.
- [GSMG_CREATOR_CLUE_AND_CONFIRMATION_INDEX](GSMG_CREATOR_CLUE_AND_CONFIRMATION_INDEX.md) — indexed creator Telegram messages.
- [GSMG_CREATOR_AUTHORED_CLUE_LEDGER](GSMG_CREATOR_AUTHORED_CLUE_LEDGER.md) — ledger of creator-authored clues only.
- [../README.md](../README.md) — historical community walkthrough (Phases 1–3, solved).
- [../doc/GSMG_PUZZLE.md](GSMG_PUZZLE.md) — narrative solved-chain writeup.

## Topic indexes

- [MOC - Architect and Macro](MOC%20-%20Architect%20and%20Macro.md)
- [MOC - Image and Raster Forensics](MOC%20-%20Image%20and%20Raster%20Forensics.md)
- [MOC - Creator Evidence](MOC%20-%20Creator%20Evidence.md)
- [MOC - Negative Results](MOC%20-%20Negative%20Results.md)

## Commands for running verification

```bash
# Full regression suite (both files)
python3 -m unittest tools.gsmg.test_recent_audits tools.gsmg.test_cb_common

# Any individual audit's self-test
python3 tools/gsmg/<script_name>.py --self-test

# Regenerate this vault's phase index after adding a new phase
python3 tools/gsmg/generate_phase_index.py
```

## Current vs. historical

- **Historical community solution**: [README.md](../README.md) — Phases 1–3, publicly solved, stable.
- **Current verified reconstruction / live frontier**: this note and the worksheet.
- **Raw chronological findings**: [tools/gsmg/FINDINGS.md](../tools/gsmg/FINDINGS.md) — includes retired/superseded hypotheses in place; a phase being *in* FINDINGS does not mean it is still believed (e.g. Phase 217's routing was itself corrected by Phase 223 — read verdicts, not just headings).
- **Retired hypotheses**: closed rows in the worksheet's master table, and any FINDINGS phase whose own text says "closed," "debunked," "superseded," or "withdrawn."
