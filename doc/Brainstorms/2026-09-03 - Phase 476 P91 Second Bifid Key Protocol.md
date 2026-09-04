# Phase 476 P91-as-second-Bifid-key protocol

Date frozen: 2026-09-03

## Question

Does idea-bank item 83 produce an unusually English-like continuation when
P91 is interpreted literally as the keyword source for a second Bifid square?

## Sole eligible cascade

1. Build Phase 386's square from `DBBI[:13]`.
2. Bifid-decrypt exact `FAED` as one 570-character block in row-column order.
3. Parse `P91 = decoded[7:98]` and `Q472 = decoded[98:]`.
4. Deduplicate all of P91 in first-occurrence order and append the unused
   no-J alphabet, using Phase 386's `build_grid(P91)` convention.
5. Bifid-decrypt Q472 as one 472-character block in row-column order through
   that P91-derived square.

This is the mechanically executable ordered schedule `DBBI square -> P91
square`. P91 does not exist before the DBBI pass, so a reversed schedule is
circular and ineligible. M91, alternate periods, encryption direction,
coordinate-order swaps, reversals, block partitions, and further passes are
excluded.

## Statistic and controls

The sole decision statistic is the complete 472-character English quadgram
score using the project's frozen table.

Primary dependency-aware null, 100,000 trials, seed `0x476`: permute the exact
FAED multiset, rerun the full first DBBI-keyed pass, regenerate synthetic P91
and Q472, build each trial's dynamic P91 square, run the complete second pass,
and compare its score with the observed score.

Secondary fixed-key attribution null, 100,000 trials, seed `0x47601`: hold the
observed P91-derived square fixed, permute the exact observed Q472 multiset,
and rerun the second pass. This asks whether Q472's order is special given the
observed key, but it is descriptive and cannot override the primary gate.

Use add-one empirical p-values. Promote only if the primary p-value is at most
`0.005`. Frozen Phase-396 keyword hits are descriptive only. No password,
ciphertext-oracle, or Bitcoin endpoint calls are allowed.

## Required checks and limitation

- Reproduce Phase 386's P91 and Q472 byte for byte.
- Match vectorized and scalar Bifid implementations on the observed cascade.
- Round-trip the observed second pass through Bifid encryption.
- Include a planted second-pass English positive.

The primary null is conditional on the selected decoder and fixed `[7:98]` /
`[98:]` parse, but does not condition controls on also producing `BTCSEED` or a
terminal `Z` at P91's final position. This test therefore measures the frozen
cascade, not the full historical discovery process or creator intent.
