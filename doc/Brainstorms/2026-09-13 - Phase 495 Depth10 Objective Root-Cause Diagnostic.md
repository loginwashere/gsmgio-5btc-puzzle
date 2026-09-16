# Phase 495 depth-10 objective root-cause diagnostic

Date: 2026-09-13
Status: development diagnostic; no FAED

## Motivation

Phase 494's unrestricted-board proof retained the planted width-19 path at
rank 1 through depth 9, but at depth 10 its best true child ranked 1,392,757
of 5,242,880 before selection.  This diagnostic distinguishes two mechanisms:

1. **under-optimization**: the larger 25-slot annealing space fails to find a
   good board for the true candidate at the production budget;
2. **over-flexibility**: wrong candidates obtain equal or better fitted boards,
   even when the true candidate itself is adequately optimized.

The Phase-494 protocol called fixture 3 the lowest-language-score three-swap
fixture.  That is a factual error: fixture 1 is lower (`-4.626843`) than
fixture 3 (`-4.623619`).  The completed Phase-494 marker pins its protocol, so
that historical file is not edited.  Fixture 3 remains a valid development
fixture, but not the hardest by that metric.

## Frozen input and population

The input is Phase 494's saved, marker-verified lane-A depth-9 population.
It is expanded bidirectionally once to the same 5,242,880 depth-10 children.
The fixture, objective binaries, schedules, and input checkpoint hashes are
recorded in the result.  This phase neither imports nor scores real FAED.

## Full-population comparison

Score every depth-10 child at the production budget (3 restarts x 2,000
iterations) with both:

- the constrained 7-single/18-double board objective;
- the unrestricted 25-slot board objective.

Record the true candidates' global ranks.  Also record descriptive hybrid
ranks for fixed mixtures of the two normalized scores at alpha
`0, .25, .5, .75, 1`, where alpha weights the unrestricted score.  These
mixtures are diagnostics only and cannot promote a solver on this one fixture.

## Frozen diagnostic panel

After the full scores exist, form the union of:

- every true depth-10 child;
- the top 512 false candidates under the unrestricted objective;
- the top 512 false candidates under the constrained objective;
- 512 deterministic PCG32-sampled false candidates.

Deduplicate by exact path.  The selection rule is fixed before inspecting any
larger-budget scores.

## Budget arms

Run the unrestricted annealer on that panel under four arms:

- baseline: 3 restarts x 2,000 iterations;
- iterations: 3 x 10,000;
- restarts: 12 x 2,000;
- combined: 8 x 20,000.

For every arm retain per-restart scores, the best board, score stability,
planted-board score, planted-board accuracy, and distance from the expected
three-swap partition.  Run the constrained objective at its baseline budget
on the same panel as a comparator.

## Interpretation

- A true score materially below its planted-board score that closes the gap
  as iterations increase supports under-optimization.
- A well-optimized true score accompanied by equally strong or stronger false
  improvements supports over-flexibility.
- Improvement from restarts but not iterations indicates basin multiplicity;
  improvement from iterations but not restarts indicates trajectories that
  are simply too short.
- A useful constrained/unrestricted mixture or soft-partition signal is only a
  candidate repair.  It requires a multi-fixture power test before reuse.

This is a root-cause diagnostic, not a locked power test.  It cannot authorize
a FAED run by itself.
