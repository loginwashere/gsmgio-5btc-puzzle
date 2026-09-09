# Phase 483A — substitution-invariant order-statistic power audit

## Question

Can local equality patterns rank the true ragged-columnar order of a
436-letter English passage after an unknown monoalphabetic substitution?

This was a synthetic power test. FAED was not imported, scored or searched.
The frozen protocol is `doc/Brainstorms/2026-09-06 - Phase 483A
Substitution-Invariant Order Statistic Probe.md`.

## Statistic

Every sliding window of length 5, 6, 7 and 8 was represented by its complete
pairwise equality partition. This retains local repeated-letter positions but
is invariant under any one-to-one renaming. Pattern probabilities were learned
only from the frozen training portion of the existing Cosmic Duality prose
corpus, with additive smoothing 0.2.

This differs from Phase 477A's global repeated-digram/trigram coincidence
count, which discarded the positions of repetitions.

## Frozen design

The normalized local prose corpus was divided into disjoint contiguous
training, development and holdout regions with 500-letter boundary gaps.
Fixtures used Phase 477A's 436-position ragged geometry, random 25-letter
substitutions, and random direct column orders.

Widths 7, 10, 12, 15, 19, 25, 30, 38 and 40 were tested independently in
both directions. Each cell contained ten fixtures. Every planted order was
compared with exactly 10,000 random orders and 100 one-, two- and four-move
corruptions. Ties counted against the planted order.

A cell passed only when at least 8/10 fixtures had at most 10 random
exceedances and showed the frozen monotone local-degradation behavior.

The execution lock was issued before holdout. Its SHA-256 is
`7f8c9fd16b1d7a7e979a1080cbfa86a842acad02109f1a135f4c8a62a6fded85`.

## Development

Five cells met the numeric gate on development data: untranspose widths 19,
25, 30, 38 and 40. No transpose cell passed. A post-run bookkeeping correction
renamed these development outcomes from `statistic_powered` to
`development_gate_equivalent`; it changed no score, fixture, statistic or gate
and was completed before the execution lock.

## Locked holdout result

| width | untranspose passes | transpose passes |
|---:|---:|---:|
| 7  | 4/10 | 0/10 |
| 10 | 6/10 | 0/10 |
| 12 | 6/10 | 0/10 |
| 15 | 8/10 | 0/10 |
| 19 | 5/10 | 0/10 |
| 25 | 10/10 | 0/10 |
| 30 | 7/10 | 0/10 |
| 38 | 8/10 | 0/10 |
| 40 | 7/10 | 1/10 |

Powered holdout cells are therefore:

- width 15, untranspose;
- width 25, untranspose;
- width 38, untranspose.

All untranspose fixtures satisfied the local-degradation condition; their
failures came from random-order rank. Transpose remained decisively weak.

The fail-closed verifier confirmed the lock hashes, complete 18-cell set,
ten fixtures per cell, frozen budgets, tie-inclusive classifications and
powered-cell list. Result SHA-256:
`d59b1b2f5d676763761fffd789769502e10ae6e392fef1e843c659de153c3b45`.
Eight unit tests passed.

## Disposition

Positive synthetic sensitivity result for untranspose widths 15, 25 and 38
under this statistic and natural-prose calibration. Only these cells may enter
a separately specified Phase 483B population-search power test.

This does not show global order recovery, board recovery or plaintext
recovery. It does not authorize a FAED run. Natural fixtures do not reproduce
FAED's exact symbol histogram or 0.693 top-seven concentration; credible
exact-profile recovery fixtures remain mandatory before any real search.

