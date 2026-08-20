---
type: index
status: live
date: 2026-08-19
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
per-gap table. The remaining P0 gaps are locally exhausted — each depends
entirely on new primary evidence, not further re-derivation from what is
already on hand:

- The physical *Cosmic Duality* book's pages 57–58 were photographed and
  transcribed 2026-08-13 (Phase 259), closing the last genuinely
  uninspected primary source for `matrixsumlist`'s operation — with a
  negative result: no matrix/dimension/traversal content, only a
  continuation of the Eve/goddess-worship narrative and a Black Madonna
  sidebar. [G-MSL-001](GSMG_OPEN_GAP_REGISTRY.md) stays `Structural
  checkpoint; parked`, now with its source reviewed rather than pending.
- A source reconciling FAED's independently-best `{g,i}` escape pair with
  the Architect-mirror-predicted `{h,e}` pair
  ([G-ESC-001](GSMG_OPEN_GAP_REGISTRY.md); `parked` — the page-markup branch
  and 16 successful Wayback/urlscan capture events are exhausted as of
  Phase 243/244/249).
- Creator evidence defining the DBBI/FAED operator itself
  ([G-YIN-001](GSMG_OPEN_GAP_REGISTRY.md); `parked` — the Telegram corpora
  and every decoded-slot page-syntax rule are already exhausted).

Between Phase 271 and Phase 321, ~50 further phases ran a broad
cryptanalytic/structural sweep directly against this pair of gaps —
transition matrices, mirror9 substitution, positional co-occurrence, GF(9),
base-27/81, an FSM model, sequence alignment, audio-spectrogram and
matrix-barcode renders, continued fractions, Bacon and Nihilist ciphers, a
Cosmic-Duality-text running key, Bellaso's 1553 reciprocal cipher, ADFGVX
transposition, and Gronsfeld/progressive shifts — all negative or null-like
(see [GSMG_DBBI_FAED_BOUNDARY_SELECTOR_AUDIT](GSMG_DBBI_FAED_BOUNDARY_SELECTOR_AUDIT.md)
and FINDINGS.md Phases 271-321). This does not change either gap's `parked`
disposition; it further supports that the blocker is missing primary
evidence, not an untried technique.

The frontier is honestly exhausted pending new primary evidence, not stalled
for lack of trying — see each gap's row for exactly what was checked.

## Recently completed phases

See [GSMG_PHASE_INDEX](GSMG_PHASE_INDEX.md) for the full generated table of
all 349 phase entries (re-run `generate_phase_index.py` any time this count
looks stale). Most recent:

| Phase | Subject | Result |
|---|---|---|
| 349 | Provenance monitor repeat-safety repair and low-frequency activation | Fixed wrong-level prior-hash lookup and missing root-Wayback comparison; failed checks now preserve last-known-good state; manual writes are atomic and scheduled checks read-only. Recovered and persisted the documented 140-entry root Wayback reference. Live run: gsmg.io root and SalPhaseIon unchanged, Hosterjack HEAD unchanged, dynamic GitHub HTML informational only, 0 evidence alerts/errors. Monthly heartbeat active |
| 348 | Seed 6: multi-blob structural concordance before aggregate language scoring | Exact parser/checksum/delimiter-record/scalar-to-HASH160 relations across 18,144 same-candidate/same-variant blob pairs in the frozen 12,128-body sentinel corpus. Real maximum **0 events**; 1,000/1,000 label-permutation null maxima also 0; family-wise p=1.0; candidate-inspection gate stayed closed. Negative on this registry only; D1 weak-language scoring remains unlicensed |
| 347 | Provenance-monitoring baseline for restored gsmg.io, SalPhaseIon, and Hosterjack (chosen over seed 6) | One-shot baseline: 3 frozen URLs, live-fetch hash/status/redirects + passive Wayback/urlscan/GitHub-commit checks. SalPhaseIon raw hash exactly matches Phase 329's own recorded value; gsmg.io root's first-ever Wayback check found 140 captures back to 2019; Hosterjack HEAD unchanged since Phase 330. **Zero alerts** -- clean "no movement" baseline, informs the seed-6 sequencing decision |
| 346 | BIP32-paths-c1 (Phase 340) scaled to the two larger core corpora, deduplicated | Proved `648_core_candidates` is a literal subset of `14551_core_expanded` (every base candidate is one of `answer_forms()`'s outputs, `keystr_forms()`'s first output is always unmodified), so ran only against the 14,551-item corpus: 494,734 address checks, 1,455,100 derivation steps, 0 hits. Closes both of Phase 343's genuinely-untested BIP32 coverage-cube cells |
| 345 | Correction to Phase 344: hint/capture chronology gap closed by this repo's own git history | User-flagged, independently re-verified (not taken on trust): commits `9d99692`/`99bd811`/`8382341` in this repo's own git history document the live SalPhaseIon/Cosmic Duality page, screenshot, and exact route ~7 months *before* the 2021-12-26 hint, not 17 months after it. Phase 344's `new_adjacency_found` claim withdrawn; graph updated with 2 new cited nodes, self-test now 10 checks |
| 344 | Seed 5: blob chronology / dependency graph over already-documented facts (same brainstorm, scoped immediately after Phase 343) | 24 nodes / 29 edges (post-Phase-345), every date cited, no guesses. Zero anachronism among well-dated pairs; restored-`gsmg.io` node mechanically pinned to `attribution="unknown"`. Original "new adjacency" claim withdrawn by Phase 345 -- see that row |
| 343 | Seed 4 (ledger half only): minimal machine-readable coverage ledger for Phases 336-342 | Infrastructure, not a hypothesis test. 15-cell (corpus x detector) coverage cube: 5 covered, 8 sentinel-only-awaiting-scale, 4 excluded/evidence-blocked, **2 genuinely untested with no declared reason** (BIP32 paths x larger core corpora -- cheap, never scoped, not compute-blocked) |
| 342 | Seed 2: typed decode-and-parse ladder, bounded pilot (same brainstorm, ranked #2) | Hex/Base64/gzip/zlib/ZIP decode + DER/PSBT/tx/key-format/Salted__ structural validation over the same 12,128-body Phase 336-338 corpus; 150,141 segments, 0 parser-valid findings, 0 exact-target hits |
| 341 | Seed 1: solved-boundary rule audit + leave-one-out controls (Post-Phase-340 Future Search Portfolio brainstorm, ranked #1) | All 3 known AES boundaries (Phase 2/3/3.2) recovered at rank 1 from a 6-candidate enumeration each; shuffled-order and naive-global-rule controls clean; positive but scoped as calibration only, no unresolved blob queried |
| 340 | C1 BIP32 paths from authenticated numbers (same brainstorm, ranked #4) | Tightly bounded pilot (1,428 checks), negative; speculative wallet semantics, disposition explicitly scoped to not close the underlying numbers |
| 339 | Code review corrections to Phases 336-338 | Bloom fail-closed, mandatory live confirmation, frozen-digest enforcement, hit provenance added to all three; no recorded result changed |
| 338 | A3 unconditional embedded key-format scanner (same brainstorm, ranked #3) | Bounded pilot, 6 finder types x 42 sentinel candidates, negative; caught and fixed its own SEC1-pubkey false-positive-rate bug before recording a result |
| 337 | A1+A2 sliding raw-key windows + byte-order transforms (same brainstorm, ranked #1) | Bounded pilot, 33 offsets x 7 byte-order forms x 42 sentinel candidates, negative; full-corpus/GPU scale left for a future phase |
| 336 | B1 "half and better half" combine algebra (Creative Brute-Force Coverage Expansion brainstorm) | Bounded pilot, 15 combine ops x 42 sentinel candidates, negative; full-corpus/GPU scale left for a future phase |
| 335 | Model 11 (81+10 FSM) report-plumbing fix; P0A/P1A sentinel backfill extended to 42 | Report gap closed, regression test added, all 42 P0A-eligible candidates now negative |
| 334 | k=8 macro-clue permutation sweep (the case Phase 322 explicitly excluded) | 725,760 forms x 240 (variant, blob) pairs, negative; closes Phase 322's reopen condition at every subset size |
| 333 | Phase-328 weak-hit key-shape review | All 43 reconstructed weak-hit bodies contain zero hex64/WIF/checksum-valid BIP39 matches |
| 332 | GPU-oracle Bloom/API and merged-kernel work, retroactively documented | Historical phase-number collision corrected; implementation and validation recorded |
| 331 | GPU oracle prize-pubkey EC neighbor/half/double detector | Tooling gap closed; independently re-derived targets added; no hits |
| 330 | Hosterjack interactive-compendium delta audit | Two narrow DBBI/FAED capacity bounds retained; stronger list/private-data/mod-9 claims rejected; no new attack path |
| 329 | Live `gsmg.io` restoration and ownership-provenance audit | Known puzzle chain restored; no new puzzle payload; operator attribution unresolved |
| 322-328 | Oracle and candidate-coverage hardening | Additional hashes/ciphers/key shapes and CBC/ECB raw-key checks covered; all bounded sweeps negative |
| 321 | ADFGVX-style keyed columnar transposition on DBBI/FAED | Borderline result traced to a multiple-comparisons artifact via shuffle-gate, closed negative |
| 320 | Gronsfeld pre-segmentation/progressive shift + extra Nihilist keywords on DBBI/FAED | Bounded exploratory pass, no signal |
| 319 | Spiral/boustrophedon route transposition on DBBI/FAED's grid factorizations | Negative, shuffle-gate clean |
| 318 | DBBI/FAED as raw base-9 bignums (no checkerboard) | Negative |
| 317 | All 5040 orderings of Phase 3's seven-part password | Negative |
| 316 | Anti-banking-theme candidates as password material | Negative |
| 315 | Mr. Robot identity-theme show terms as password material | Negative |
| 314 | Architect monologue's "no film equivalent" rows (6/7/14) as password material | Negative |
| 309-313 | Bacon cipher, Nihilist additive-key, Cosmic Duality running-key, Bellaso 1553, "The Warning" remainder | All negative or parked, not testable from available sources |
| 271-308 | Extended DBBI/FAED structural/cryptanalytic sweep (GF(9), base-27/81, FSM, sequence alignment, spectrogram, matrix-barcode, continued-fraction, mirror9, co-occurrence matrix, QR finder-ring texture x11, Architect-monologue exhaustive passes) | All negative or null-like; see [GSMG_DBBI_FAED_BOUNDARY_SELECTOR_AUDIT](GSMG_DBBI_FAED_BOUNDARY_SELECTOR_AUDIT.md) |
| 259 | Physical Cosmic Duality book pages 57-58 recovered | G-MSL-001's last uninspected source reviewed, negative |
| 250 | Designing the Future source audit | Page-10 `salvation`/`damnation` echoes `F-CHAIN-002`'s `SALVATION`; word-boundary keyword sweep zero across both Fresco books; recognition-only |

## Canonical documents

- [GSMG_STRICT_TRANSITION_WORKSHEET](GSMG_STRICT_TRANSITION_WORKSHEET.md) — the 5-gate evidence-discipline worksheet; start here for any new candidate.
- [GSMG_FACT_LEDGER](GSMG_FACT_LEDGER.md) — what claims are currently accepted, with exact scope.
- [GSMG_OPEN_GAP_REGISTRY](GSMG_OPEN_GAP_REGISTRY.md) — what specific evidence would unblock progress, per gap.
- [GSMG_PHASE_INDEX](GSMG_PHASE_INDEX.md) — generated index of all FINDINGS.md phases.
- [GSMG_PHASE_TEMPLATE](GSMG_PHASE_TEMPLATE.md) — standard fields for new phase entries.
- [GSMG_OBJECT_DBBI](GSMG_OBJECT_DBBI.md), [GSMG_OBJECT_FAED](GSMG_OBJECT_FAED.md) — pilot per-artifact reference pages.
- [tools/gsmg/FINDINGS.md](../tools/gsmg/FINDINGS.md) — full chronological research log.
- [GSMG_STAGE_INPUT_OUTPUT_SUMMARY](GSMG_STAGE_INPUT_OUTPUT_SUMMARY.md) — solved-chain input/output map.
- [GSMG_CREATOR_CLUE_AND_CONFIRMATION_INDEX](GSMG_CREATOR_CLUE_AND_CONFIRMATION_INDEX.md) — indexed creator Telegram messages.
- [GSMG_CREATOR_AUTHORED_CLUE_LEDGER](GSMG_CREATOR_AUTHORED_CLUE_LEDGER.md) — ledger of creator-authored clues only.
- [../README.md](../README.md) — historical community walkthrough (Phases 1–3, solved).
- [../doc/GSMG_PUZZLE.md](GSMG_PUZZLE.md) — narrative solved-chain writeup.
- [GSMG_FRESH_BRAINSTORM_2026-08-06](GSMG_FRESH_BRAINSTORM_2026-08-06.md) / [GSMG_FRESH_BRAINSTORM_RESIDUAL_AUDIT](GSMG_FRESH_BRAINSTORM_RESIDUAL_AUDIT.md) — a breadth-first brainstorm pass and its later residual-closure audit (Phase 252).
- [doc/Brainstorms/](Brainstorms/README.md) — dated ideation sessions, incubation-only until promoted to a `tools/gsmg/FINDINGS.md` phase.

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
