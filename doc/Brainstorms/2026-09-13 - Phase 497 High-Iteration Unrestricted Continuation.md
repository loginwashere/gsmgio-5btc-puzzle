# Phase 497 high-iteration unrestricted continuation

Date: 2026-09-13
Status: development proof; no FAED

Phase 496 rescored all 5,242,880 Phase-494 depth-10 children with the
unrestricted objective at 3 restarts x 10,000 iterations.  The best planted
child moved from rank 1,392,757 at 3 x 2,000 to rank 1, and both planted
children survived the unchanged 262,144-candidate diversity cut.

This proof continues from that exact checkpoint.  It retains Phase 490's
lane-A parent-reserved depth-11 bridge, downstream keep sizes, bidirectional
expansion, diversity selection, and final full-board solve.  Every partial
board fit at depths 11--19 uses the unrestricted objective at 3 x 10,000.
The redundant lane-B restart is omitted because Phase 496 already retains two
ranked true depth-10 candidates; this is a bounded capability proof, not a
production schedule freeze.

Every depth is written as an independently verified checkpoint.  Pass requires
exact top-1 final order recovery.  Failure stops this schedule.  Success only
permits multi-fixture synthetic validation before any real-data use.
