# Phase 505C shallow escape-pair screen protocol

Date: 2026-09-14
Status: development implementation and CPU tests complete; pilot not run

## Motivation

Phase 505A proved that the unrestricted English objective identifies the true
escape pair when the complete transposition order is supplied: 72/72 rank 1.
The first locked Phase-505B blind cell then took 303.06 seconds, projecting to
about 9.1 hours for its 108-cell benchmark and 109 hours for the full matrix.
That architecture is paused with its first checkpoint preserved.

The cost is dominated by independently expanding every assumed pair through
depth 7. Phase 505C instead asks whether pair identity is already observable
at the first exact fragment depth. It exhaustively enumerates all
`19P4 = 93,024` ordered depth-4 fragments for every pair, fits an unrestricted
25-slot board to each fragment, and ranks pairs by their best score. No order
heuristic can discard the correct fragment because the depth-4 universe is
complete.

## Frozen pilot

- Synthetic Phase-505 logical fixture 1 is evaluated for true-pair indices
  `(0, 17, 35)`.
- Every row evaluates all 36 unordered escape-pair hypotheses.
- Every cell scores exactly the same 93,024 paths.
- Board budget: 3 restarts x 2,000 iterations, seed `0x505C001`.
- Objective: unrestricted 25-slot English quadgram score.
- Primary pair statistic: maximum normalized score over all paths.
- Canonical pair index breaks score ties.
- The top 32 paths and distribution summaries are descriptive only.
- Planted-fragment ranks are audit-only and never affect pair ranking.
- Each of the 108 cells is atomically checkpointed and validated on resume.

This is a development identifiability pilot, not a promotion test. No
post-hoc threshold is interpreted as evidence about FAED. A promising result
must be followed by a separately frozen, disjoint synthetic power gate before
any real pair screen is considered.

## Stop rule

If the three true pairs do not rank consistently near the top, stop this
shallow statistic rather than increasing the path depth or selecting a subset
of favorable pairs. If it is promising, measure its actual runtime and design
a disjoint calibration universe with a frozen promotion rule.

## Scope

The implementation imports no puzzle ciphertext and does not call the P32
oracle. The pilot lock must pin this protocol, implementation, dependencies,
Phase-505 fixture manifest, Phase-505A result, the first Phase-505B timing
cell, GPU binary, full pair/path universe, budget, and statistic before
`--run-pilot` can execute.

Seven focused CPU-only tests pass before lock issuance: exact path-universe
coverage, non-finite-score rejection, primary-statistic calculation,
absent-lock refusal before work starts, truth-field isolation from ranking,
checkpoint identity rejection, and a mocked full cell path.
