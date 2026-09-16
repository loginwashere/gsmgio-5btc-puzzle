# Phase 501 holdout-0 depth-11 repair proof

Date: 2026-09-13
Status: post-hoc repair proof on an already-consumed failed holdout fixture

Phase 500 showed that Phase 499's two correct depth-11 children rank 11th and
16th among 18 siblings under the locked `3 x 10,000` budget, but 1st and 2nd
under `8 x 20,000`.  Phase 501 asks whether changing only the depth-11 bridge
to that diagnostic budget restores exact end-to-end recovery.

The input is Phase 499 fixture 0's hash-verified selected depth-10 population.
The depth-11 bridge uses unrestricted `8 x 20,000`; depths 12--19 and final
resolve resolve use the Phase-497/498 `3 x 10,000` schedule unchanged.  Beam
capacities, selection rules, seeds, and final ranking are unchanged.

Pass requires exact order at final rank 1.  This fixture has already been
inspected and tuned against, so a pass is engineering evidence only.  It does
not repair the failed Phase-499 gate and cannot authorize FAED.  A successful
repair would license freezing the amended schedule against new, uninspected
holdout fixture indices.
