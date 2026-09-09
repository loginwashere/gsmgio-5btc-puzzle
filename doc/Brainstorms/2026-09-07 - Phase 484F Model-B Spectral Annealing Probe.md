# Phase 484F Model-B spectral annealing development probe

Date: 2026-09-07

Status: development only; no lock, holdout, or FAED

Test whether multi-start simulated annealing on Phase 484A's actual 570-symbol
Model-B spectral statistic reaches the planted order or at least its local
neighborhood at exact widths 10, 15, and 19. Both board pools are mandatory.

Start classes are kept separate: controlled non-cancelling swap corruptions
measure the planted basin; independent random orders and top-scoring orders
from a random spectral population measure usable blind recovery. Controlled
starts can never satisfy a future search-power gate because they require the
unknown truth.

Every anneal uses swap/move/reversal/three-cycle proposals, geometric cooling,
best-state retention, and deterministic exhaustive-swap refinement. Report
exact recovery and Kendall tau by start class. A high-tau false maximum is not
a solve; it motivates an explicitly tested consensus/adjacency reconstruction.

The initial six-fixture run is a budget/tendency smoke test only. No threshold
is frozen. FAED is prohibited.
