# Phase 484L bidirectional solver holdout protocol

Date: 2026-09-07

Status: pre-execution lock

Freeze Phase 484K's bidirectional internal-segment solver for exact raw-symbol
Model-B widths 10 and 15. Both vic_profile and broad_random board pools must
pass independently. Width 19 is excluded because development recovery was only
one of four observed fixtures.

Use ten untouched holdout fixtures per cell, generated from the frozen holdout
corpus split and holdout seed. Training remains entirely on development
fixtures 6-15.

Budgets are frozen at start depth four, beam width 4,096, endpoint-reserved
fraction 0.5, and six workers. A cell passes only with at least 8/10 exact
column-order recoveries. All four cells must pass.

No FAED access, no real-stream scoring, no threshold changes, and no rerun
after inspecting holdout results. A pass licenses a separately locked real
search; it is not itself evidence about FAED.
