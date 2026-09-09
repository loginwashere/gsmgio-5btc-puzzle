# Phase 484M powered bidirectional FAED real protocol

Date: 2026-09-07

Status: pre-execution lock

Phase 484L powered the bidirectional Model-B order solver at exact widths 10
and 15 in both synthetic board pools. Run that fixed solver against FAED for
all 36 unordered escape pairs. Width 19 and every ragged width remain excluded.

For each pair/width cell, retain the solver's top full order and run the frozen
Phase 484A board annealer with two restarts of 6,000 iterations. Rank all 72
cells by normalized quadgram score. The inherited successful-holdout floor is
-4.571151156706407 per quadgram window.

Crossing the numerical floor is only a confirmation trigger because the real
family contains 72 opportunities. A solve additionally requires readable
plaintext, exact decrypt/re-encrypt consistency, and an independently
checkable relationship to established puzzle material. A miss closes only
these 72 powered pair/width cells under the fixed solver and board budget.

One execution only. Pin FAED, all solver inputs, Phase 484L's lock/result/
verification, the quadgram table, the exact cell set, randomness, and budgets
before any candidate-order or plaintext scoring of FAED. Pre-lock access is
limited to verifying its length and pinned SHA-256.
