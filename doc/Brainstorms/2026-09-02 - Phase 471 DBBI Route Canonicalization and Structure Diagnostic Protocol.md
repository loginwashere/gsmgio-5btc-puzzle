---
type: preregistration
status: frozen
date: 2026-09-02
phase: 471
topics:
  - DBBI
  - 7x13
  - route-canonicalization
  - seven-segment
  - finite-field-rank
  - calibrated-2d-statistics
---

# Phase 471 — DBBI Route Canonicalization and Structure Diagnostic Protocol

## Provenance

This protocol executes the bounded, purely diagnostic subset of a broad
DBBI matrix-hypothesis catalog drafted in-session on 2026-09-02 (234
numbered hypotheses across 13 families, ending in a 10-item "best first
experimental batch"). The catalog is ideation only; nothing in it is
promoted. This phase implements batch items 1 (affine toroidal route
enumeration with equivalence control), 3 (seven-segment interpretation),
4 (finite-field rank/parity tests), 5 (calibrated 2D statistics against
count-preserving shuffles), 6 (row/column-local base-9 packing), and
7 ({b,e} as row/column-local bit syntax). Batch items 2 (visual mask
inspection) is included descriptively only (ASCII renderings, no automated
bar); items 8 (route-aware plaintext alignment), 9 (first-occurrence
permutation schedules), and 10 (oracle feeding) are explicitly deferred to
separately preregistered phases.

## Why this is genuinely different from closed work

- Phase 469 and earlier sum/count audits used row-major placement only;
  no phase has enumerated and *canonicalized* the closed toroidal/affine
  route universe to measure how many genuinely distinct 91-symbol readings
  exist (the catalog's equivalence-control caution).
- The seven-segment reading (7 rows/columns as segment states across 13
  positions) has no prior phase.
- Matrix rank / parity-check structure over GF(2)/GF(3)/GF(9) has no prior
  phase (Phase 271-321 coupling models did not test linear-algebraic rank
  deficiency of DBBI alone).
- Calibrated 2D neighbor/offset statistics against count-preserving
  shuffled grids have no prior phase (Phase 412/413 tested DBBI/FAED
  generative comparison, not within-grid 2D anisotropy).
- Row/column-local base-9 packing and {b,e} column-bitmask ASCII differ
  from the whole-stream base conversions already covered.

## Frozen inputs

- The canonical 91-symbol `DBBI` stream from `tools/gsmg/data.py`.
- Shapes `7x13` and `13x7`, row-major fill. No other shapes.
- Value map `a=0..i=8` (`a0i8`) for all numeric interpretations. No other
  numeric map is used anywhere in this phase.
- RNG: `random.Random(471)`; `N_SHUFFLES = 10000` count-preserving
  shuffles of the 91-symbol multiset, drawn once and reused for every
  calibrated statistic.

## Frozen family

### A. Route canonicalization census (diagnostic, no scan bar)

1. Rectangle routes, per shape: read rows; rows with each row reversed;
   rows in reverse row order; columns; columns with each column reversed;
   columns in reverse column order; 180° rotation; boustrophedon rows
   (both starting directions); boustrophedon columns (both); NW–SE
   diagonals; anti-diagonals; inward spiral (CW and CCW); outward spiral
   (CW and CCW). Sixteen reads × two shapes.
2. Toroidal walks, per shape `(R,C)`: every start cell (all `R*C`) and
   every step `(dr,dc)` with `dr in 1..R-1`, `dc in 1..C-1` (exactly the
   full-period walks). 6×12×91 walks for `7x13` and 12×6×91 for `13x7`.
3. Linear index maps `n -> (a*n + b) mod 91` for all `a` coprime to 91
   and all `b in 0..90` (72×91 maps), applied to the row-major stream.
4. Canonicalize every route as a permutation of positions 0..90; count
   unique permutations and unique output strings; verify empirically
   whether family 3 equals family 2's `7x13` output set (the CRT claim).

Deliverable: census counts only. No token scan is run over route outputs
(the nine-letter alphabet cannot spell the frozen clue vocabulary, and no
downstream consumer is licensed). This section is equivalence-control
infrastructure for any later preregistered route phase.

### B. Binary masks (11, frozen)

Nine single-symbol planes, the `{b,e}` plane, and the odd-value plane
(`a0i8` parity). Each is rendered as ASCII art in both shapes in the
result file for human inspection — descriptive only, no automated bar.

### C. Seven-segment decode (exact bar)

For each of the 11 masks × two orientations (`7x13`: 13 columns as
glyphs, 7 rows as segments; `13x7`: 13 rows as glyphs, 7 cells as
segments) × two segment orders (a..g forward and reversed) × two
polarities: decode the 13 seven-bit states against the canonical 16-glyph
hex seven-segment table (0-9, A, b, C, d, E, F). Bar: exactly 13/13 valid
glyphs. Anything less is a count, not a lead.

### D. Finite-field rank (calibrated)

On the `7x13` grid: rank over GF(2) of the parity plane and the `{b,e}`
plane; rank over GF(3) of value mod 3 and of the high trit (`value // 3`);
rank over GF(9) (GF(3)[x]/(x²+1), value `v -> (v//3)·x + (v%3)`) of the
full value matrix. Five statistics. Calibration: empirical
`P(shuffle rank <= observed)` over the frozen shuffles.

### E. 2D offset statistics (calibrated)

On the `7x13` torus: equality-match rates at offsets (0,1), (1,0), (1,1),
(1,-1), (2,0), (0,2), for the full symbol plane and the `{b,e}` indicator
plane. Twelve statistics, two-sided empirical p against the frozen
shuffles.

### F. Line-local packings (exact bars)

1. Base-9: per shape × axis (rows/columns) × digit order (forward/
   reverse), convert each line from base 9 (`a0i8`) to an integer and
   render minimal big-endian bytes. Bar: every line in a reading renders
   to all-printable ASCII (0x20–0x7E).
2. `{b,e}` bitmasks as 7-bit codes: masks {b}, {e}, {b,e}; per shape,
   read each 7-cell line (columns of `7x13`, rows of `13x7`) as a 7-bit
   integer, both bit orders, both polarities. Bar: all 13 values in a
   reading printable ASCII.

## Decision rule and stop rule

- Calibrated family: 17 statistics (5 ranks + 12 offsets). A lead
  requires two-sided empirical p < 0.001 after Bonferroni over the
  17-statistic family (raw p < 0.0000588).
- Exact-bar family: a lead requires the full exact bar (13/13 valid
  glyphs; an entire reading printable), not partial counts.
- Any lead is recorded as requiring a separately preregistered follow-up.
  Nothing is promoted in this phase.
- One execution. No output-driven additions of masks, maps, routes,
  moduli, orders, or bars. No password materials, no decryptions, no
  oracle calls, no plaintext alignment, no FAED usage.
- This phase does not reopen `G-MSL-001` and licenses no operand or
  transform (diagnostic structure only).
