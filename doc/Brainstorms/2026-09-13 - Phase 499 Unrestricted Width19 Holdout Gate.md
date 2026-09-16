# Phase 499 unrestricted width-19 holdout gate

Date: 2026-09-13
Status: frozen design; execution lock issued separately

## Purpose

Phases 497 and 498 recovered two independent three-swap development fixtures
exactly at rank 1.  Phase 499 tests that fixed architecture on a small,
predeclared holdout set before any further FAED run.

This is a calibration gate, not evidence that FAED uses width 19, escape pair
`{g,i}`, English plaintext, or a partition-violating checkerboard.

## Frozen fixtures

- corpus split: `holdout`;
- fixture indices: `0`, `1`, and `2`;
- raw stream: the Phase-491 invariant 570-symbol histogram;
- escape pair: `{g,i}`;
- board construction: Phase-493's deterministic three disjoint swaps between
  the frequency-profile single and double partitions;
- no fixture is selected by language score, difficulty, or solver behavior.

The holdout corpus has appeared in earlier experiments, so "holdout" here
means uninspected under this Phase-499 fixture construction and unrestricted
schedule, not a never-before-used text source.

## Frozen solver

For each fixture:

1. use the original invariant front through depth 5;
2. use unrestricted-board scoring with Phase-490 budgets through refined
   depth 7 and depths 8--9;
3. use unrestricted `3 x 10,000` board annealing at depths 10--19;
4. retain the Phase-497/498 parent-reserved depth-11 bridge and all existing
   beam capacities;
5. run the existing unrestricted final full-board resolve.

Training models are created before fixture injection, exactly as in Phase 498.
No schedule, seed, capacity, fixture, or stopping rule may change after the
execution lock is issued.

Each fixture has its own objective marker and depth checkpoints.  Restarts
must validate and resume those checkpoints.  Results may be run sequentially.

## Gate and stop rule

Pass requires all three fixtures to recover the exact planted order at final
rank 1.  A first failure closes this gate as failed; remaining fixtures need
not be spent.  Plaintext accuracy and all intermediate truth ranks are
diagnostics only and cannot rescue a non-exact result.

- `3/3`: gate passes and licenses a separately locked single FAED `{g,i}`
  width-19 run with this schedule.
- anything else: no FAED run; diagnose the first failed stage or revisit the
  training model.

No FAED bytes or P32 oracle are available to this phase.
