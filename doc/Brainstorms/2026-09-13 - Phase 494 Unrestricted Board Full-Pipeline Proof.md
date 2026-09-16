# Phase 494 unrestricted-board full-pipeline proof

Date: 2026-09-13
Status: development proof; no FAED

Phase 493 found positive genuine-fragment separation in all 30 controlled
partition-violation cells. This proof changes exactly one Phase-490 component:
every partial board fit uses the unrestricted Phase-484Q CUDA annealer instead
of the fixed single/double letter partition. Search capacities, restarts,
iterations, seed, dual-lane schedule, and final unrestricted board resolution
remain unchanged.

The first and only authorized fixture is Phase-493 development fixture 3 with
three cross-partition swaps. It is the lowest-language-score three-swap fixture
in the five-fixture diagnostic (`-4.6236`). Pass requires exact top-1 order
recovery. Every stage remains checkpointed, and a marker pins the fixture,
objective binary, schedules, and wrapper before reuse. Failure stops this lane;
success permits two additional synthetic proof fixtures, but never directly
authorizes FAED.
