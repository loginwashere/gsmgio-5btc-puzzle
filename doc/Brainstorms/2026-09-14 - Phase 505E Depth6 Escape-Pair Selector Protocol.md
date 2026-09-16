# Phase 505E depth-6 escape-pair selector protocol

Date: 2026-09-14
Status: development implementation and CPU tests complete; no timing run

## Motivation

Phase 505C-D closes exhaustive depth-4 maximum scoring and every minimum-
window correction from 1 through 30. Phase 505B's completed true-pair cell,
however, showed a different regime at depth 6: after shared pair-balanced
invariant pruning, eight planted fragments survived and the best planted
fragment ranked first under the unrestricted-board score. Its later depth-7
expansion created 13.6 million candidates and drove the 303-second cell cost.

Phase 505E reproduces the Phase-505B path only through depth 6 and ranks pairs
immediately. It changes no model, pruning schedule, board objective, or seed
before that boundary.

## Two execution gates

1. A timing lock permits exactly one cell: true pair index 0 evaluated under
   hypothesis pair index 0. Its wall time is multiplied by 108.
2. The three-row pilot may be locked only if the projection is at most 7,200
   seconds. Its lock must pin the timing lock and timing result.

The pilot rows are true-pair indices `(0, 17, 35)`, each evaluated under all
36 pairs. Every cell trains from the same logical fixture-0 pair-balanced
model and evaluates logical fixture 1. The primary statistic is the maximum
depth-6 unrestricted-board normalized score. Planted-fragment rank remains
audit-only. Each cell is atomic and resumable.

This is development calibration, not a FAED screen. If all three true pairs
do not reach the top three, the depth-6 maximum closes. A success would still
require a disjoint powered synthetic gate and a separately locked real run.

Six CPU-only tests pass before the timing lock: absent-lock refusal before
training, the two-hour pilot cost gate, canonical model hashing, truth-field
isolation from pair ranking, exact quadgram-window counting, and stale-model
checkpoint rejection.
