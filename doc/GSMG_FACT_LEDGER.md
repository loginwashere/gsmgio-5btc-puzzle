---
type: index
status: live
topics:
  - fact-ledger
---

# GSMG Fact Ledger

What claims are currently accepted, and with exactly what scope. Distinct
from [GSMG_PHASE_INDEX](GSMG_PHASE_INDEX.md) (what work happened and when)
and [GSMG_STRICT_TRANSITION_WORKSHEET](GSMG_STRICT_TRANSITION_WORKSHEET.md)
(what operations may advance). See
[GSMG_HOME#Current vs. historical](GSMG_HOME.md#current-vs-historical) for
how this fits the rest of the vault.

## Axes

| Property | Meaning | Example values |
|---|---|---|
| `evidence_level` | Provenance strength | creator-primary, authenticated-artifact, community-sourced, solver-derived |
| `status` | Lifecycle of the claim itself | stable, parked, closed, superseded |
| `result` | Outcome polarity, where applicable | positive, negative, partial |
| `disposition` | Puzzle significance | operative, recognition-only, structural-only, provenance-only, rejected |

A fact can be `status: stable` and `disposition: rejected` at once — e.g. "BYE
is not a valid direct password" is a stable, well-established fact whose
puzzle significance is that it rejects a candidate. Do not conflate the two.

## Scope note

This starts with ~20 load-bearing claims per the criteria below, not every
established measurement. Zero-hit sweeps, intermediate counts, and
single-audit-only facts belong in their audit and, when relevant, the
[MOC - Negative Results](MOC%20-%20Negative%20Results.md). A claim earns a
row here only if it is part of the current default chain, has 3+ dependent
documents, has been disputed/corrected, or needs a precise scope statement
to avoid being overstated later.

## Ledger

| Fact ID | Exact claim | Evidence level | Status | Result | Disposition | Established by | Canonical audit |
|---|---|---|---|---|---|---|---|
| F-CHAIN-001 | The 24-cell first-piece grid (blue=1/yellow=0, spiral order) reconstructs to the prime `574061` | authenticated-artifact | stable | positive | structural-only | 32 | [GSMG_MATRIXSUMLIST_CHECKPOINT](GSMG_MATRIXSUMLIST_CHECKPOINT.md) |
| F-CHAIN-002 | Reading `574061` as a forward 2×3 digit matrix and taking row sums gives `[23,16,7]`; this exact list is independently reproduced by the `SALPHATION -> SALVATION` letter-count route | authenticated-artifact | stable | positive | structural-only | 32, 97 | [GSMG_MATRIXSUMLIST_CHECKPOINT](GSMG_MATRIXSUMLIST_CHECKPOINT.md) |
| F-CHAIN-003 | `[23,16,7]`, applied as forward one-based word indices to the Architect film/screenplay dialogue, selects `BOTH / ULTIMATELY / THE`; this selection is stable under a film-vs-screenplay stress test | authenticated-artifact | stable | positive | structural-only | 33, 216 | [GSMG_ARCHITECT_CHOICE_BOUNDARY_AUDIT](GSMG_ARCHITECT_CHOICE_BOUNDARY_AUDIT.md) |
| F-CHAIN-004 | The initials/endings of `BOTH/ULTIMATELY/THE` give `BUT`/`HYE`; this boundary does **not** by itself mechanically establish the creator's `yinyang` state (an earlier stronger claim was corrected) | authenticated-artifact | stable | partial | structural-only | 33, 216 | corrected by 223 — [GSMG_ARCHITECT_CHOICE_BOUNDARY_AUDIT](GSMG_ARCHITECT_CHOICE_BOUNDARY_AUDIT.md) |
| F-CHAIN-005 | Only `BOTH`, among the three eligible B-initial words in the 48 stable `BUT` rows, has its own mirror9-related endpoints (`B...H`); all 5 partial-mirror rows producing `BYE` begin with `BOTH` | authenticated-artifact | stable | positive | recognition-only | 236 | [GSMG_MACRO_MODEL_DISPOSITION_AUDIT](GSMG_MACRO_MODEL_DISPOSITION_AUDIT.md) |
| F-CHAIN-006 | Under the declared `partial_mirror9` operation (B↔H/D↔F/C↔G, `Y` preserved), `HYE` maps to `BYE`; `BYE` is the unique dictionary word among 48 stable `BUT`-family rows | solver-derived | stable | positive | recognition-only | 232 | [GSMG_ARCHITECT_HYE_BYE_AUDIT](GSMG_ARCHITECT_HYE_BYE_AUDIT.md) |
| F-CHAIN-007 | `BYE` has zero hits as a literal direct password (18 keystring forms) against all 4 tracked blobs | authenticated-artifact | stable | negative | rejected | 232 | [GSMG_ARCHITECT_HYE_BYE_AUDIT](GSMG_ARCHITECT_HYE_BYE_AUDIT.md) |
| F-CHAIN-008 | `BYE` has a real but non-creator-selected semantic bridge to authenticated page text `CIAO BELLA O`, via the historically-attested *Bella Ciao* precedent | community-sourced | stable | partial | recognition-only | 233 | [GSMG_BYE_CIAO_PROVENANCE_AUDIT](GSMG_BYE_CIAO_PROVENANCE_AUDIT.md) |
| F-CHAIN-009 | Neither creator Telegram corpus (solver-group or support-group) ever selects `CIAO`, `BELLA`, or `BYE` as the yin-yang state | creator-primary | stable | negative | rejected | 234 | [GSMG_CIAO_SELECTION_COVERAGE_AUDIT](GSMG_CIAO_SELECTION_COVERAGE_AUDIT.md) |
| F-CHAIN-010 | The `ciao`/`bella`/`bye`/`key`/`note`/`self`/`keynote` word family has zero hits as a direct blob password or checkerboard keyword against all 4 tracked blobs (SALPH/COSMIC/P32TRAILING/URLBLOB) | authenticated-artifact | closed | negative | rejected | 234, 235, 237 | [GSMG_CHECKERBOARD_KEYWORD_BLOB_GAP_AUDIT](GSMG_CHECKERBOARD_KEYWORD_BLOB_GAP_AUDIT.md) |
| F-CHAIN-011 | The exact 31-character DBBI selection `ncsyangcahiriasogaleafayanestve` has no source binding it to matrix dimensions, traversal, value mapping, aggregation, or serialization as `matrixsumlist`'s operand — 7 of 7 required G3 fields are unbound | authenticated-artifact | parked | partial | structural-only | 236 | [GSMG_MACRO_MODEL_DISPOSITION_AUDIT](GSMG_MACRO_MODEL_DISPOSITION_AUDIT.md) |
| F-CHAIN-012 | The six-digit-prime route (Model B) consumes 3 consecutive authenticated macro tokens and reaches `BUT/HYE`; the 31-char selection (Model A) consumes only 1 token and stops. Model B is the default working grammar | authenticated-artifact | stable | positive | structural-only | 236 | [GSMG_MACRO_MODEL_DISPOSITION_AUDIT](GSMG_MACRO_MODEL_DISPOSITION_AUDIT.md) |
| F-OBJ-001 | `DBBI` is a fixed 91-symbol 9-ary (`a`–`i`) raw string; its best-fit checkerboard escape pair by code-level Index of Coincidence is `{b,e}` (rank 1 of 36), a signature unique among all 36 pairs | authenticated-artifact | stable | positive | structural-only | — | `tools/gsmg/checkerboard_code_ic_oracle.py` |
| F-OBJ-002 | `FAED` is a fixed 570-symbol 9-ary raw string (`570 = 2×3×5×19`, 8 factor pairs); its best-fit escape pair is `{g,i}` (rank 1 of 36), a signature shared by 5 of 36 pairs | authenticated-artifact | stable | positive | structural-only | 113 | `tools/gsmg/checkerboard_code_ic_oracle.py` |
| F-OBJ-003 | FAED's independently-best `{g,i}` pair and the Architect-mirror-predicted `{h,e}` pair remain unreconciled. Neither pair's mirror9 image (`{a,c}` / `{c,g}`) validly segments its own origin stream — `{c,g}` cannot even segment FAED (dangling final escape) | authenticated-artifact | stable | negative | structural-only | 225, 236 | [GSMG_MACRO_MODEL_DISPOSITION_AUDIT](GSMG_MACRO_MODEL_DISPOSITION_AUDIT.md) |
| F-FAV-001 | The Stage-0 footer's exact `#383838` color layer uniquely touches all 5 literal `G` glyphs (banner+address) among all grayscale sparse layers; its non-G residue parses as `O/C/Be` → atomic numbers `8,6,4` | authenticated-artifact | stable | partial | recognition-only | 186, 188, 189, 190 | `tools/gsmg/stage0_g_shadow_consumer_audit.py` |
| F-FAV-002 | The native `favicon_small.png`'s sole visible grayscale byte is `C9` (201,201,201). Alpha-compositing it over the page's `F5F5F5` background at exactly one source pixel `(27,26)`, alpha `E0`, produces the rendered `CE` (206,206,206) seen in the Stage-0 logo | authenticated-artifact | stable | positive | provenance-only | 239 | [GSMG_NATIVE_FAVICON_SHADOW_AUDIT](GSMG_NATIVE_FAVICON_SHADOW_AUDIT.md) |
| F-FAV-003 | All 96 visible native `C9` pixels lie within the ordinary SVG-registered antialias-edge envelope (max distance `1.0047px`, vs. `1.322px` for ordinary edges); off-contour residue is zero. `C9` is not a hidden spatial channel | authenticated-artifact | closed | negative | rejected | 242 | [GSMG_SVG_PNG_EDGE_GEOMETRY_AUDIT](GSMG_SVG_PNG_EDGE_GEOMETRY_AUDIT.md) |
| F-FAV-004 | The nested macro-token-length identity (`18/38/43/56` matching contiguous spans of `matrixsumlist+enter+lastwordsbeforearchichoice+thispassword`) is real, but FAED width `38` is not a geometrically exceptional dimension under any of 3 null models after correction across all 16 divisor widths | authenticated-artifact | closed | negative | rejected | 240 | [GSMG_SHADOW_MACRO_FAED_GEOMETRY_AUDIT](GSMG_SHADOW_MACRO_FAED_GEOMETRY_AUDIT.md) |
| F-FAV-005 | `favicon_small.png`'s bytes are authenticated to a single Wayback capture on 2019-04-28, 8 days after the 2019-04-20 puzzle launch; no pre-launch capture exists, so branding-vs-puzzle-era origin cannot be distinguished by chronology alone | authenticated-artifact | stable | partial | provenance-only | 241 | [GSMG_FAVICON_WAYBACK_CHRONOLOGY_AUDIT](GSMG_FAVICON_WAYBACK_CHRONOLOGY_AUDIT.md) |
| F-NEG-001 | The COSMIC raw32/MD5/103×103/base-38 construction is a complete, reproducible community-code pipeline built from spam-linked, mutually-citing on-chain addresses — a fabrication/negative control, not a creator transition | community-sourced | closed | negative | rejected | 210 | `tools/gsmg/FINDINGS.md#phase-210` |
| F-STAGE-001 | Phase 3's seven-part concatenated password (`causality`/`Safenet`/`Luna`/`HSM`/`11110`/hex artifact/chess FEN) SHA-256-hashes to the verified value `1a57c572...ec30d5` | authenticated-artifact | stable | positive | operative | pre-phase-numbering | [GSMG_STAGE_INPUT_OUTPUT_SUMMARY](GSMG_STAGE_INPUT_OUTPUT_SUMMARY.md) |

## Adding a row

A fact earns a row only if it meets at least one criterion from
[the investigation this ledger came from]: load-bearing in the current
chain, 3+ dependent documents, disputed/corrected, easy-to-misstate scope,
multiple provenance sources, or needs an explicit reopening condition.
Otherwise it belongs in its audit document only.

Promote a ledger row to its own fact note (`type: fact`, with Claim / Exact
scope / Evidence / Controls / Downstream consequences / Invalidation
conditions sections) only once it accumulates enough dependents or disputes
that a one-line ledger row stops being enough — none currently qualify.
