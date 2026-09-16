# Phase 502 repaired unrestricted width-19 holdout gate

Date: 2026-09-13
Status: frozen design; execution lock issued separately

## Basis

Phase 499 failed on holdout fixture 0 because its correct depth-11 children
ranked below the eight-child local reservation under `3 x 10,000` board
annealing.  Phase 500 isolated the cause: the same children ranked 1st and 2nd
under `8 x 20,000`.  Phase 501 changed only that bridge budget and recovered
the consumed fixture's exact order and plaintext at rank 1.

Phase 502 tests that one-field repair on two new fixture constructions that
have not been inspected or scored under this solver.

## Frozen universe and schedule

- split: `holdout`;
- fixture indices: `3` and `4`, selected by enumeration before generation;
- escape pair: `{g,i}`;
- raw histogram: Phase 491's frozen 570-symbol count vector;
- board: Phase 493's deterministic three cross-partition swaps;
- original invariant front through depth 5;
- unrestricted original budgets through refined depth 7 and depths 8--10;
- depth-11 bridge only: unrestricted `8 x 20,000`;
- depths 12--19: unrestricted `3 x 10,000`;
- all beam capacities, selection rules, seeds, and final resolution unchanged.

Each fixture is checkpointed independently.  No parameter may change after
the execution lock.  Runs are sequential and stop on the first failure.

## Decision

Pass requires exact planted order at final rank 1 on both fixtures (`2/2`).
Plaintext accuracy and intermediate truth ranks are diagnostics only.

- `2/2`: licenses a separately locked single FAED `{g,i}`, width-19 run with
  the repaired unrestricted schedule.
- otherwise: no FAED run; the repair has failed to generalize.

This small gate establishes operational power, not a population recovery
probability.  It does not establish the real escape pair, width, board family,
transposition direction, or English plaintext assumption.  FAED and P32 are
unavailable during the gate.
