# Phase 505B blind escape-pair selector implementation note

Date: 2026-09-14
Status: implementation and CPU-only tests complete; benchmark not run

Phase 505A passed its known-order ceiling on all 72 fixtures. The correct
escape pair ranked first in every fixture, with a minimum advantage of
`+0.32932088195358045` and a median advantage of
`+0.48166483787785763` normalized quadgram units over the best wrong pair.
This licenses implementation of the blind development selector, but not a
FAED pair ranking.

## Implemented split

- Logical fixture 0 from each of the 36 true pairs trains a single shared,
  pair-balanced invariant model at depths 4--6.
- Logical fixture 1 from each true pair is the development evaluation row.
- Every evaluation row is searched under all 36 assumed pairs.
- Positive and negative training counts are equal across pair labels.
- The primary observable selector is the maximum refined depth-7
  unrestricted-board normalized score.
- Score distributions at the invariant, depth-6, depth-7 coarse, and depth-7
  refined stages are retained for diagnosis.
- Planted order survival is written under `audit_only`; it is never consumed
  by scoring, pruning, checkpoint validation, or pair ranking.

## Checkpointing

Every matrix cell is written atomically to its own JSON file. A resumed run
validates the true-pair row, assumed-pair column, fixture hash, schedule hash,
and finiteness of the primary selector before accepting the checkpoint.
Thus the three-row benchmark or later 36-row development matrix can be
interrupted between cells without discarding completed work.

Two fail-closed execution barriers enforce the sequencing:

1. `phase505b_benchmark_lock.json` must pin the implementation, dependencies,
   unrestricted-board binary, Phase-505 fixture manifest, Phase-505A result,
   model construction, schedule, primary statistic, and the exact three-row
   benchmark universe before `--benchmark` can execute.
2. `phase505b_matrix_lock.json` must additionally pin the verified benchmark
   lock and completed `benchmark_summary.json` before
   `--run-development-matrix` can execute.

Neither lock currently exists. The two output summaries have distinct names,
so the full matrix cannot silently overwrite the benchmark evidence it pins.

## Execution boundary

The code exists in `tools/gsmg/phase505b_blind_escape_pair_selector.py`.
Eight focused CPU-only tests pass, covering both absent-lock barriers,
checkpoint model-hash rejection, non-finite selector rejection, canonical
tie handling, truth-field isolation from ranking, score summaries, and
matrix bookkeeping. In particular:

- no shared model has yet been trained;
- no GPU cell has been scored;
- the 108-cell benchmark has not started;
- no Phase 505B execution lock exists;
- no holdout has been consumed;
- FAED has not been imported or scored.

The next action is to issue and verify the dedicated benchmark lock. Only then
may the three predeclared benchmark rows `(0, 17, 35)` run. Their measured time
and development recovery determine whether the matrix design is affordable
and promising enough to formalize as a locked holdout protocol.
