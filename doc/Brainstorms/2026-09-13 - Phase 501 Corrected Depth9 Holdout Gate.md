# Phase 501 corrected-depth-9 holdout gate

Date: 2026-09-13
Status: frozen design; execution lock issued separately

## Why this exists

Phase 499 froze a schedule that only raises unrestricted board-anneal
iterations from 2,000 to 10,000 starting at depth 10, because that is where
Phase 494/495/496 found the collapse on development fixture 3. Holdout
fixture 0 failed Phase 499's gate: its true completion held rank 1 through
depth 8, then collapsed to rank 45,203 (before selection) / 31,532 (after)
at depth 9 under the 2,000-iteration budget. Phase 499's own stop rule
("first failure closes the gate; remaining fixtures need not be spent")
was honored -- fixtures 1 and 2 were never run.

Phase 500 (`phase500_holdout_depth9_rescue_diagnostic.py`) re-scored that
same depth-9 step from the already-committed depth-8 checkpoint at
3 x 10,000 iterations, changing nothing else. The true completion's rank
recovered from 45,203/31,532 to exactly rank 1 (before and after selection),
with 7 true-consistent fragments retained after selection instead of 1. This
is a diagnostic re-analysis of already-failed, already-consumed fixture 0;
it spent no new holdout fixture and did not touch FAED.

This confirms the failure mode is the same one already characterized in
Phase 495/496 (an under-annealed single-pass "coarse" score at a `global_depth`
merge step, structurally different from depth 8's two-stage coarse+refine
funnel, which already runs its refine pass at 10,000 iterations in both
schedules). It is not evidence of a defect in the unrestricted objective
itself, and it is not evidence that raising the budget only at depth 10 is
sufficient in general.

## What changes

The only change from Phase 499's schedule: unrestricted board-anneal coarse
iterations are 10,000 (not 2,000) starting at depth 9, not depth 10. Depth 8
and earlier are unchanged, because depth 8's existing refine pass already
runs at 10,000 iterations under both schedules and was never implicated in
either collapse. No other parameter, capacity, seed, or stopping rule
changes from Phase 497/498/499.

## Fixture selection: why not fixture 0 again

Fixture 0 directly motivated this schedule change. Re-running it under the
corrected schedule and calling that a pass would validate the fix against
the same instance used to derive it, which is not a fair generalization
test. The corrected schedule is evaluated only on holdout fixtures that were
never used to diagnose or tune it.

Fixture 1 was the first candidate but fails Phase 491/493's own frozen
construction-time language gate under this three-swap variant: its
minimum-edit plaintext scores -4.7167 normalized quadgram against the
frozen -4.70 floor, a construction failure, not a solver result. Fixture 4
independently fails the same construction gate (-4.6745 falls under a
separate edit-fraction/quadgram interaction -- checked, and also rejected).
Both are skipped for the same reason any Phase-491 fixture that fails its
own frozen generator gate is skipped: this is a fixed, pre-solver validity
check, identical in kind to the check every existing dev/holdout fixture in
this project must already pass, not a selection based on difficulty or
solver behavior.

The three fixtures used are the next three holdout indices, in index order,
that construct validly under the frozen three-swap variant:

- fixture 2: reserved but unspent under Phase 499 (its gate closed after
  fixture 0's failure, before fixture 2 was run).
- fixture 3 and fixture 5: fresh, previously untouched holdout indices,
  added to keep the gate at three fixtures now that fixture 0 is excluded as
  tuning-tainted and fixtures 1 and 4 fail construction. Index 3 in the
  `holdout` split has not been used by any prior phase (index 3 in `dev` was
  Phase 494/495/496/497's fixture; this is a different split).

No fixture is selected by language score, difficulty, or solver behavior --
2, 3, and 5 are simply the next three holdout indices that pass the frozen
construction gate.

## Frozen fixtures

- corpus split: `holdout`;
- fixture indices: `2`, `3`, `5`;
- raw stream: the Phase-491 invariant 570-symbol histogram;
- escape pair: `{g,i}`;
- board construction: Phase-493's deterministic three disjoint swaps between
  the frequency-profile single and double partitions (identical construction
  to Phase 499).

## Frozen solver

For each fixture:

1. use the original invariant front through depth 5, then the unchanged
   depth-6/7 refined stage and lane-A depth-8 funnel (identical to Phase 499,
   still 3 x 2,000 coarse / 4 x 10,000 refine);
2. use unrestricted `3 x 10,000` board annealing at every `global_depth` merge
   step from depth 9 through depth 19 (Phase 499 started this at depth 10);
3. retain the depth-11 parent-reserved bridge and all existing beam
   capacities from Phase 497/498/499 unchanged;
4. run the existing unrestricted final full-board resolve.

Training models are created before fixture injection, exactly as in Phase
498/499. No schedule, seed, capacity, fixture, or stopping rule may change
after the execution lock is issued.

## Gate and stop rule

Pass requires all three fixtures to recover the exact planted order at final
rank 1. A first failure closes this gate as failed; remaining fixtures need
not be spent. Plaintext accuracy and all intermediate truth ranks are
diagnostics only and cannot rescue a non-exact result.

- `3/3`: gate passes and licenses a separately locked single FAED `{g,i}`
  width-19 run with this schedule.
- anything else: no FAED run; the corrected-depth-9 schedule is not sufficient
  in general, and the failing stage is diagnosed the same way Phase 500
  diagnosed depth 9 -- before any further schedule change is proposed.

No FAED bytes or P32 oracle are available to this phase.
