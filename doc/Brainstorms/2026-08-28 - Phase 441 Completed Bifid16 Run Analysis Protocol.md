---
type: preregistration
phase: 441
date: 2026-08-28
status: frozen-before-execution
oracle: forbidden
gpu: read-completed-artifacts-only
---

# Phase 441 — Completed Bifid-16 Run Analysis Protocol

## Question

Did the exact completed `16!` Phase-430 search recover evidence of coherent
plaintext beyond the sealed `BTCSEED` crib, or did exhaustive quadgram
optimization strengthen the Phase-433 selection pathology?

## Evidence already observed before freezing

- The checkpoint reports `next_rank = 20,922,789,888,000 = 16!`.
- The final result reports `interrupted=false` and exact winner rank
  `8,041,961,541,600`, score total `-3465.5264`, mean `-6.18843994`.
- The winner begins `BTCSEEDDGAGEOAEAIFINOFI...`, not readable prose.
- The existing frozen Phase-432 reviewer collapses the 1,000 retained block
  winners to nine decoded strings: class sizes 524, 469, and seven singletons.
- No reviewed decode contains a fixed Bitcoin/puzzle keyword; longest repeated
  substring is five. Dictionary calibrations appear strong for several rows,
  but many apparent words recur at identical positions across related decodes.

These observations may be confirmed, not redefined, by the audit.

## Pinned artifacts

- checkpoint SHA-256 `2735d25f...17770`;
- final result SHA-256 `0b389df0...5de3`;
- final Phase-432 review SHA-256 `2b8a9cea...fcae`;
- prior Phase-433 result SHA-256 `5f33f313...fa93d`;
- prior Phase-432 snapshot SHA-256 `16b87412...0663e`;
- dictionary SHA-256 `9f513f1c...6a32`.

Full digests are fixed in the implementation. All source/input/kernel/driver,
CUDA-architecture, score-contract, and range fingerprints must match the sealed
Phase-430 values.

## Completion and equivalence checks

The implementation must independently:

1. prove the range is exactly `[0,16!)` and complete;
2. CPU-decode every retained rank and verify its GPU score and `BTCSEED` prefix;
3. reproduce exact decoded-string equivalence classes and class sizes;
4. verify the result winner equals the checkpoint/reviewer winner;
5. report resumed-range count, elapsed time, throughput, and projected full-run time;
6. state explicitly that retained block winners are not an exact global top-K.

## Final-winner controls

Reuse Phase 433's definitions without alteration, excluding `BTCSEED`:

- quadgram total/mean and unseen-floor fraction;
- alphabet size, entropy, vowel fraction, IoC, lag-1 mutual information,
  raw-DEFLATE saving, longest repeated substring, and distinct 1–4-grams;
- top-ten repeated quadgram contribution concentration;
- 1,000 exact-multiset shuffles;
- 1,000 intact aligned-digraph shuffles;
- 10,000 uniform global Phase-430 ranks;
- 10,000 random non-`G/H` assignments conditional on the winner's `G/H` cells;
- the exact Phase-433 pinned English control.

Seeds are fixed to `0x441` and derived constants. Inclusive add-one p-values
are descriptive only because the winner was selected from `16!` candidates.

Compare the final winner directly with rank zero, the completed Phase-429
winner, the 38%-snapshot leader, and English using Phase 433's pinned profiles.

## Nine-decode invariance analysis

Across all nine distinct retained decodes, report:

- invariant tail positions and fraction;
- per-position consensus string (`?` for disagreement);
- pairwise Hamming-distance minimum/median/maximum;
- intersection of exact dictionary hits as `(start, word)` pairs;
- union of fixed keyword hits;
- class-size distribution and score range.

The saved 200-trial dictionary p-values must not be treated as multiplicity-
corrected plaintext evidence. Explain whether high segmentations arise on a
shared optimized template.

## Decision rule

`coherent_plaintext_evidence` requires all of:

- at least one fixed puzzle/Bitcoin keyword outside the crib;
- word-scale structure longer than five characters that is not common to the
  optimized template;
- final absolute quadgram gap to English below 0.5 log10 units per window;
- broad sequential metrics moving materially toward English, not merely the
  optimized quadgram objective.

Otherwise disposition is
`exact_16factorial_negative_quadgram_selection_pathology_confirmed`.

## Stop conditions

No password candidate, downstream oracle, new GPU kernel/run, Docker mutation,
or alternate score search is allowed. The completed run files remain unchanged.
