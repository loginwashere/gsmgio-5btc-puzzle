# Phase 496 depth-10 iteration rescore

Date: 2026-09-13
Status: development gate; no FAED

Phase 495 isolated under-optimization as the primary cause of Phase 494's
depth-10 collapse.  At the production `3 x 2,000` budget the two true paths
were 0.46--0.60 normalized-score units below their planted-board scores.  At
`3 x 10,000`, one true path was within 0.009 of its planted-board score and had
84% board accuracy.  At `8 x 20,000`, both true paths slightly exceeded their
planted-board scores with 84--88% board accuracy, while the frozen top-512
false panel remained below them.

This gate changes only the annealing iteration count at Phase 494's exact
depth-10 lane-A transition:

- same saved and marker-verified depth-9 population;
- same 5,242,880 bidirectional children;
- same unrestricted CUDA objective, seeds, three restarts, diversity rule,
  and keep size of 262,144;
- iterations increased from 2,000 to 10,000.

Pass requires at least one true depth-10 fragment after the real diversity
selection.  The complete scored population is not retained; the selected
checkpoint and before/after truth diagnostics are persisted.  Failure stops
this repair.  Success permits a separately specified continuation using the
stronger budget at later partial depths.  It does not authorize FAED.
