# Phase 498 fixture-1 unrestricted generalization

Date: 2026-09-13
Status: development generalization test; no FAED

Phase 497 recovered the exact order and plaintext at rank 1 on fixture 3 after
raising unrestricted-board annealing from 2,000 to 10,000 iterations at depth
10 and later.  Phase 498 repeats that architecture independently on Phase
493's fixture 1 with three cross-partition swaps.  Fixture 1 has the lowest
language score among the five three-swap development fixtures (`-4.626843`).

The schedule is fixed as follows:

- regenerate fixture 1 from the Phase-493 construction;
- original invariant front through depth 5;
- unrestricted board scoring with the original Phase-490 budgets through
  refined depth 7 and through depths 8--9;
- unrestricted `3 x 10,000` scoring from depth 10 through depth 19;
- retain the parent-reserved depth-11 bridge and all Phase-490 capacities;
- use the existing unrestricted final full-board solve.

The run is checkpointed from depth 7 onward.  Pass requires exact top-1 final
order recovery.  Failure stops this schedule for diagnosis.  Success supports,
but does not alone complete, a multi-fixture generalization claim and cannot
authorize FAED.
