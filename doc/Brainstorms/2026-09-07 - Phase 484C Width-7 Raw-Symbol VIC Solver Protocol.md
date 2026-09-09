# Phase 484C width-7 raw-symbol VIC solver development protocol

Date: 2026-09-07

Status: development only; no execution lock, holdout consumption, or FAED scoring

## Question

Can the Phase-484A blind raw-symbol checkerboard/transposition solver be
extended from widths 2/3/5/6 to ragged width 7 by exhaustively ranking all
`36 * 7! = 181,440` escape-pair/order hypotheses and board-solving only a
global shortlist?

Width 7 is treated separately because its complete order family remains
enumerable and because seven is independently prominent in the puzzle. This
prominence motivates testing the width; it does not select an escape pair,
column order, board, or interpretation of an output.

## Development sequence

1. Reuse the byte-locked Phase-484A geometry, fixture generator, spectral
   statistic, board annealer, corpus split, and normalized quadgram score
   without modifying that implementation.
2. Enumerate all 5,040 orders independently for each of all 36 escape pairs.
   Invalid dangling-escape segmentations are recorded, never repaired.
3. On fresh development fixtures in both `vic_profile` and `broad_random`,
   record the planted hypothesis's one-based rank among all valid hypotheses.
4. Choose a shortlist budget only from development ranks and benchmark cost.
5. Board-solve a fresh development batch blindly. Report pair, exact order,
   Kendall tau, board accuracy, plaintext accuracy, and decoded-length error.
6. Only after a fixed recovery design exists may a separate amendment freeze
   a disjoint holdout gate. FAED remains prohibited until that gate passes and
   a separately locked real protocol exists.

The initial rank survey is descriptive development work; no cutoff or power
claim is frozen by this draft.

## Limits

Success at width 7 would not power widths 8--40. Those require a different
non-factorial column-path search. Failure during development is not evidence
against FAED because no powered real experiment would have occurred.

## Development result and frozen holdout amendment

The full width-7 family was benchmarked on one initial fixture per pool, then
on ten fresh fixtures per pool (development indices 51--60). The initial
planted ranks were 1 and 2. In the 20-fixture survey, `vic_profile` had median
rank 4.5 and maximum 248; `broad_random` had median rank 60 and maximum 842.
All 20 planted hypotheses lay inside a 1,536-item global shortlist.

Using only that board-free survey, the highest-ranked fixture from each pool
was selected for end-to-end blind solving: `vic_profile` index 57 at rank 248
and `broad_random` index 56 at rank 842. Under two 6,000-proposal board
anneals per retained hypothesis (`T 20 -> 1`), both recovered the exact pair,
exact order, board, and plaintext. This is development evidence, not holdout
power.

The frozen holdout contains width 7 only, both board pools, ten fixtures per
pool (20 total), and planted pair indices `0,1,5,9,14,18,23,27,32,35` at
fixture indices 0--9. It uses the untouched holdout corpus split and seed
`0x484C401D`. The search retains 1,536 hypotheses and uses two 6,000-proposal
board anneals with `T 20 -> 1`.

A fixture passes only with exact pair and order recovery, exact decoded
length, plaintext character accuracy at least 0.95, and board accuracy at
least 0.80. Each pool must pass at least 8 of 10. Eight worker processes may
schedule fixtures independently; all random streams are derived from the
fixed seed, fixture coordinates, candidate pair/order, and restart. Any
worker failure prevents atomic result publication. FAED remains prohibited
until this gate passes and a separate real-run lock is issued.
