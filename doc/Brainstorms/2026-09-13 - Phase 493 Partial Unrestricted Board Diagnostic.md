# Phase 493 partial unrestricted-board diagnostic

Date: 2026-09-13
Status: development diagnostic frozen before GPU execution

## Question

At the Phase-490 switch depths 6 and 7, can an unrestricted checkerboard fit
rank genuine column fragments when the true board violates the fixed
`E,A,T,I,O,N,S` single-slot partition?

## Frozen fixture family

- Start from Phase-491 raw-histogram-only development fixtures 0--4.
- Produce three variants per fixture by swapping 1, 2, or 3 disjoint
  single-slot/double-slot letter pairs. Pairs are selected greedily by the
  smallest absolute difference between their sampled latent code counts;
  letter names break ties. This creates controlled partition violations while
  minimizing unrelated unigram damage.
- Reapply Phase 491's exact minimum-count edits to the same source passage.
  Require exact nine-symbol raw counts, exact round-trip, edit fraction <=18%,
  and normalized quadgram >=-4.70. Preserve the original column order.

## Frozen comparison

For each of 15 variants and depths 6 and 7:

- include every genuine contiguous fragment of the planted order;
- add 512 deterministic random distinct-column paths, excluding genuine paths;
- score the identical panel with three 2,000-iteration restarts under the
  partition-constrained Phase-490 board fit and the unrestricted Phase-484Q
  board fit;
- compute the planted-board score as a ceiling and report best genuine rank,
  score gap above the best control, and maximum genuine-fragment board
  accuracy for both fitted objectives.

This is a sensitivity diagnostic, not a solver or holdout gate. It passes its
bounded development question if the planted-board objective ranks a genuine
fragment first in at least 24/30 cells and the unrestricted fitted objective
places a genuine fragment in the top five in at least 20/30 cells. The
constrained objective is a comparator, not a required failure condition.

No FAED ciphertext, alternative pair, width, seed tuning, or full order search
is authorized here.
