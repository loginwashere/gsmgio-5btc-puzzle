---
type: protocol
phase: 483A
date: 2026-09-06
status: development-frozen-before-holdout
topics:
  - faed
  - transposition
  - substitution-invariant-statistic
  - synthetic-power
---

# Phase 483A — substitution-invariant order-statistic probe

## Question

Can local equality structure distinguish the true ragged-columnar order of a
436-letter English passage after every letter has been replaced by an unknown
symbol?

This is a synthetic power experiment only. It does not score FAED, optimize a
checkerboard, test a password, or call any decryption/address oracle.

## Why this differs from Phase 477A

Phase 477A's order-only statistic counted repeated digrams and trigrams over
the entire reconstructed stream. It discarded where those repetitions
occurred. This phase scores the local equality partition of each sliding
window. For example, `THERE` has shape `ABCDE` except for its repeated `E`,
more precisely canonical labels `ABCDC`; `LEVEL` is `ABCBA`. These shapes are
unchanged by any one-to-one substitution.

The implementation encodes a window's complete equality partition as its
pairwise-equality bit mask. Models for lengths 5, 6, 7 and 8 are learned from
the training split. Additive smoothing is fixed at 0.2. The score is the sum
of log probabilities over every sliding window and every model length.

## Frozen data split

Use the existing local Cosmic Duality prose extraction and exclusions from
Phase 477A, uppercase letters only with `J -> I`. Divide the normalized text
into three contiguous regions by index:

- training: first 50%, with the final 500 letters discarded;
- development: next 25%, with 500 letters removed at both boundaries;
- holdout: final 25%, with the first 500 letters discarded.

No 436-letter fixture may cross a split boundary. Development output may be
used to diagnose or replace the statistic, but not to change the frozen
holdout rules below. Any changed statistic requires a new protocol revision
before holdout execution.

## Frozen geometry and fixtures

Reuse Phase 477A's exact ragged convention: `rows = ceil(436 / width)`, the
last `width*rows - 436` original-index columns are short, and no padding ever
existed. Test widths 7, 10, 12, 15, 19, 25, 30, 38 and 40 in both `untranspose`
and `transpose` directions.

Each fixture selects a 436-letter passage, applies a random one-to-one
renaming of the 25-letter alphabet, chooses a random direct column
permutation, and applies the selected geometry. The scorer receives only the
renamed observed integer stream, width and direction.

Development and holdout each contain ten fixtures per cell, derived from
disjoint fixed PCG32 seed domains. The reference implementation may run a
smaller explicit prefix for timing, but the holdout gate requires all ten.

## Comparators

For every fixture:

1. Score the planted order.
2. Score exactly 10,000 independently random orders. Ties count against the
   planted order.
3. Starting from the planted order, generate 100 corruptions at each severity
   1, 2 and 4. One corruption step is chosen uniformly from swap, remove-and-
   insert, contiguous-block reversal and three-cycle.

Record the planted rank among random orders, its percentile, the random
maximum and quantiles, and corruption-score distributions. Exact planted
order recovery is not attempted in 483A.

## Gate

A width/direction cell is statistic-powered only if at least 8 of its 10
holdout fixtures satisfy both:

- no more than 10 of 10,000 random orders tie or exceed the planted score
  (top 0.1%, tie-inclusive); and
- the planted score exceeds the median score at each corruption severity,
  while the three corruption medians are non-increasing from severity 1 to 4.

This gate establishes only sensitivity of the frozen statistic near and far
from a planted order. It does not establish that a global permutation search
can recover that order.

## Decision

- No powered cells: stop this solver design; do not score FAED.
- Some powered cells: only those cells may proceed to a separately specified
  Phase 483B population-search power test.
- A direction-wide asymmetry is reported as such. Success in one direction
  cannot promote the other.

## Limits

Natural book passages do not reproduce FAED's exact 25-class histogram or its
0.693 top-seven share. Therefore even a passed 483A cell cannot authorize a
real FAED run. A later recovery test must add credible exact-profile fixtures,
require plaintext/order recovery rather than score reach, and freeze its own
null decision before FAED is inspected.

