---
type: audit
status: closed
topics:
  - dbbi
  - transposition
  - closed-system
---

# GSMG Phase 516 — DBBI Width-7 Unrestricted-Order Transposition Audit

Date: 2026-09-17

## Question

The unrestricted-order columnar-transposition/CSP solver line (Phase 477
onward — token transposition feasibility, the width-19/30 CSP/annealing
board search, the Phase 512 exact-crib CSP architecture) was built and run
exclusively against `FAED`. `DBBI` is the same checkerboard-escape-pair
cipher construction on the same page and has never received this
treatment — its own transposition-shaped work (Phase 319) tested only a
small family of fixed, named routes (spiral, boustrophedon, row-major,
column-major) over `DBBI`'s known `7x13` grid, not a search over unknown
column order. This asymmetry was flagged by
[GSMG_TECHNIQUE_TARGET_COVERAGE_MATRIX](GSMG_TECHNIQUE_TARGET_COVERAGE_MATRIX.md).

Does an unknown column order exist under which `DBBI`'s raw 91-symbol
stream, untransposed and checkerboard-decoded, produces readable plaintext
at `DBBI`'s only nontrivial rectangular width (7 columns / 13 rows;
`91 = 7 x 13`)? Scoped in
[doc/Brainstorms/2026-09-16 - Phase 516 DBBI Unrestricted-Order Transposition Scoping.md](Brainstorms/2026-09-16%20-%20Phase%20516%20DBBI%20Unrestricted-Order%20Transposition%20Scoping.md).

## Why width 7 only

`DBBI` is 91 raw symbols, factoring only as `91 = 7 x 13` (divisors
`{1, 7, 13, 91}`, confirmed by direct computation). Width 7 admits genuine
order exhaustion (`7! = 5,040`). Width 13 (`13! ~= 6.2e9` orders) does not —
benchmarked at this search's measured per-order rate, even the cheap
stage-1 pass alone would cost roughly 100 CPU-days, before any board
refinement. Width 13 needs a genuinely different (CSP-pruned or
spectral-shortlist) order search, not brute enumeration, and is left for a
follow-up phase.

## Method

Reused this project's own validated `phase484a_raw_symbol_vic_solver`
primitives (`Geometry`, `segment_raw`, `decode_raw`, `anneal_board`, the
frozen English quadgram model) rather than reimplementing decode logic —
`Geometry` and the decode functions are already width/length-agnostic.

**A naive single-stage design (anneal every one of the 5,040 orders
directly at the FAED-tuned budget of 6,000 iters x 2 restarts) was tried
first and failed its own synthetic self-test**: the search's winning order
did not match the planted order, and a direct score comparison confirmed
this was because the planted order's board scored *below* a wrong
competitor's board at that budget (-4.492 vs -4.283 normalized). A follow-up
diagnostic ruled out both a code bug (round-trip and true-board decode were
verified correct) and a fundamental short-text identifiability limit: a much
heavier anneal budget (40,000 iters x 20 restarts) made the true order's
board win (-4.198 vs -4.214), and the win saturated (unchanged at 50,000
iters x 30 restarts) — this was under-annealing, not noise. This mirrors
this project's own FAED-line finding of under-annealing at depths 9/11
(Phase 500), independently rediscovered here at a smaller scale.

Full exhaustive search at that heavier budget would cost roughly 189
CPU-hours across all 36 pairs — too slow to iterate on. A **two-stage
architecture** was adopted instead, after directly checking its premise
rather than assuming it: rank all 5,040 orders per pair with a cheap anneal
(6,000 iters x 2 restarts), then re-anneal only the top 100 of that ranking
with the heavier budget (60,000 iters x 30 restarts in the final
configuration). A direct rank-check diagnostic on a synthetic fixture found
the true order ranked 5th of 3,840 valid candidates under the cheap pass —
comfortably inside a 100-candidate shortlist. Three synthetic self-test
trials at the final settings all recovered the exact planted column order
(3/3); character accuracy was 96.4% and lower on two trials, with residual
errors being single-letter board-substitution confusions typical of
short-text (~56-90 letter) monoalphabetic recovery, not order-search
failures.

The real run swept all 36 escape pairs (validity checked per candidate
order via `segment_raw`, not pre-filtered), checkpointing each pair's
result to disk as soon as it completed so the run was resumable across a
machine shutdown mid-sweep. Three shuffled-DBBI-multiset null trials
(identical two-stage search, same lock) were run for calibration.

## Result

The real `DBBI` width-7 sweep's best candidate: pair `{b,g}`, order
`[0, 1, 4, 3, 2, 5, 6]`, normalized quadgram score **-4.2269**, decoding to

```
ILVESORTEENGITANOBLEASSMONENBERCUSSTERNMERORIDERTHERESSTOBEENETSALENE
```

— not English. `DBBI`'s own established code-IC-best pair `{b,e}` ranked
only 9th of 36 under this search (score -4.3034).

Three shuffled-`DBBI`-multiset null trials, identical search:

| Trial | Winner pair | Normalized score |
|---|---|---|
| Real `DBBI` | `{b,g}` | **-4.2269** |
| Null 0 | `{a,g}` | -4.1307 |
| Null 1 | `{b,h}` | -4.0956 |
| Null 2 | `{f,i}` | -4.1661 |

**All three null trials outscored the real result.** The real candidate is
not merely unremarkable against chance — it falls below the observed null
range. With only 3 null trials this is not a precise p-value, but
qualitatively it is an unambiguous negative: 3 of 3 nulls beat the real
winner, and the winning real decode itself contains no recognizable English
words.

## Disposition

Closed negative for width 7, exhaustively (all 5,040 orders, all 36 escape
pairs checked per-candidate) and calibrated (3/3 null trials outscore the
real winner). This is the first application of the unrestricted-order
transposition technique class to `DBBI`, closing the asymmetry the
coverage matrix flagged. Does not resolve `G-YIN-001` (the DBBI/FAED
relationship) or `G-MSL-001` (the `matrixsumlist` consumer) — it only
removes one specific technique-class gap. Width 13 remains open, gated on a
genuinely different search architecture, not more compute at the current
one.

## Artifacts

- `tools/gsmg/phase516_dbbi_width7_exhaustive.py` — self-test, calibrate,
  run, verify-lock modes; per-pair checkpointing/resume.
- `tools/gsmg/test_phase516_dbbi_width7_exhaustive.py` — fast structural
  tests (the module's own `self_test()` is the real correctness check but
  costs ~19 minutes per trial, so it is run manually, not wired into the
  fast suite).
- `tools/gsmg/phase516_execution_lock.json`,
  `tools/gsmg/phase516_width7_result.json`,
  `tools/gsmg/phase516_width7_null.json`,
  `tools/gsmg/phase516_width7_{real,null0,null1,null2}_checkpoint.json`.
- [doc/Brainstorms/2026-09-16 - Phase 516 DBBI Unrestricted-Order Transposition Scoping.md](Brainstorms/2026-09-16%20-%20Phase%20516%20DBBI%20Unrestricted-Order%20Transposition%20Scoping.md)

## Reopen condition

A genuinely new order-search architecture (CSP-pruned or spectral-shortlist,
not brute enumeration) reaches width 13 with a comparable calibrated null
comparison, or a creator source/primary artifact independently selects a
`DBBI` escape pair or column order.
