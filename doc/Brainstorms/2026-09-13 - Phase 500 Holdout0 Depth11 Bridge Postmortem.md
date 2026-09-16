# Phase 500 holdout-0 depth-11 bridge postmortem

Date: 2026-09-13
Status: post-hoc diagnostic on an already-consumed failed holdout fixture

Phase 499 failed its first holdout fixture.  The true fragment survived depth
10 but both true depth-11 children were discarded by the parent-reserved
bridge.  This diagnostic scores only the children of the surviving true
depth-10 parent and records each true child's local sibling rank under:

- the locked production budget (`3 x 10,000` unrestricted annealing);
- a diagnostic high budget (`8 x 20,000`);
- the planted checkerboard ceiling.

The comparison distinguishes a too-small eight-child local reservation from
under-optimization of the correct child.  It cannot amend, rescue, or rerun
the failed Phase-499 holdout gate, and it cannot authorize FAED.

