# Phase 484B powered small-width raw-symbol VIC real protocol

Date: 2026-09-07

Status: freeze before execution; FAED not yet scored by this phase

## Question and powered scope

Does real FAED decode as English-like plaintext under the historical Model-B
construction powered by Phase 484A?

```text
plaintext -> unknown 25-slot checkerboard -> 570 raw a-i symbols
          -> standard columnar transposition -> observed FAED
```

The family is strictly widths 2, 3, 5, and 6. At every width, all 36 unordered
escape pairs are considered. Widths 7--40 are excluded because Phase 484A did
not power their order search. The exact FAED ASCII bytes are pinned by SHA-256
`066191b4aafc114fbca7f0d168382f40129c4ff18490375b689741081d5ef3c2`.

## Frozen search

For each width, enumerate every escape-pair/order tuple and rank valid
segmentations by Phase 484A's substitution-invariant spectral statistic.
Retain the first 1,536 valid hypotheses. Each receives two independently
seeded 6,000-proposal 25-slot board anneals with geometric cooling from 20 to
1. Candidates below the mathematical 285-character decoded-length floor are
ineligible. Rank candidates by summed quadgram log probability divided by
the number of quadgram windows. Retain the best ten per width and the family
maximum across all four widths.

Four worker processes evaluate widths independently. Every anneal seed is a
deterministic function of `SEED_REAL = 0x484B0001`, width, escape-pair index,
column permutation, and restart, so scheduling does not affect results.

## Decision and stop rule

The locked Phase 484A holdout's minimum winning normalized score was
`-4.571151156706407`. A real family maximum at or above that floor is a
permissive trigger for human readability review and a separately locked
confirmation. It is not automatic promotion: maximizing over the real family
can create pseudo-English, and no shuffled family-wide null is included here.

If the maximum is below the floor or the retained outputs are gibberish, the
disposition is `no_powered_family_solve_no_calibrated_null_claim`. Do not tune
the score floor, shortlist, widths, pair family, annealing budget, or seed and
rerun. A calibrated bounded-negative claim would require a separately frozen
same-budget raw-symbol-shuffle family; it is not inferred from this run.

## Verification

Before execution, lock hashes cover this protocol, the Phase 484A solver,
the real runner, verifier, `data.py`, the Cosmic Duality corpus, quadgram
table, Phase 484A execution lock, and Phase 484A holdout result. The verifier
checks those hashes; the exact four width cells; hypothesis totals; ten sorted
candidates per cell; pair/index, plaintext-length and normalized-score
consistency; the family maximum; and the frozen trigger/disposition mapping.

## Limits

This tests only a single standard raw-symbol columnar transposition at the
four powered small widths, a 25-slot checkerboard, and English-like plaintext.
It does not cover larger widths, disrupted/double transposition, another
language model, another checkerboard topology, or any P32 password consumer.
