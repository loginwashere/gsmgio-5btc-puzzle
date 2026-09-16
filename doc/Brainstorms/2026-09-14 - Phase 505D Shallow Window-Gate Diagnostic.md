# Phase 505D shallow minimum-window diagnostic

Date: 2026-09-14
Status: development diagnostic and CPU tests complete; not run

Phase 505C's exhaustive depth-4 pilot completed in about 103 seconds but the
true pairs ranked 28, 24, and 11. All three winning wrong hypotheses achieved
the identical score `-2.505883470978432` from paths contributing exactly one
quadgram window. Best paths under the true pair contributed 8, 7, and 4
windows respectively. The registered maximum-score statistic therefore
failed through a clear small-sample extreme-value mechanism.

This diagnostic reruns the same 108 cheap cells while preserving the GPU
kernel's path-level window counts. For each cell it records the best score
after requiring at least each integer number of windows from 1 through 30,
the complete possible range at depth 4. Pair ranks are then recomputed for
every threshold.

The threshold curve is explicitly post-hoc development diagnosis. No point
on it can be promoted or applied to FAED. If no threshold puts all three true
pairs in the top three, the shallow lane closes. If a region succeeds, its
rule must be frozen and tested on disjoint synthetic fixtures before any real
use. No vocabulary, puzzle ciphertext, or P32 oracle is involved.

Five focused CPU-only tests pass before lock issuance: full threshold-grid
coverage, absent-lock refusal before work, planted-window identification,
independent per-threshold ranking, and invariant window counts across GPU
annealing restarts.
