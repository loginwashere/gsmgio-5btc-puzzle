# GSMG Phase 426–428 — BTCSEED Held-Out Continuation Structure Audit

Date: 2026-08-27

## Outcome

The fixed 563-character continuation has detectable ordering under a naive
whole-tail shuffle, but the signal is fully attributable to the full-block
Bifid transform's mechanically coupled output digraphs. No tested evidence of
English plaintext, longer-range repetition, or beyond-digraph structure
remains. Final branch: **`digraph_mechanical_attribution`**.

This does not retract Phase 425's family-corrected `BTCSEED` prefix result. It
closes the requested held-out continuation gate as a forward decoder edge.

## Frozen decoder and held-out boundary

All three stages reproduce Phase 386's exact 570-character output
(`sha256 0c5d984f...7745e`) using the DBBI-first-13 square, one 570-character
Bifid block, row-column convention, and forward input/output. They then remove
exactly `decoded[0:7] == BTCSEED`. Only `decoded[7:]` (563 characters;
`sha256 18ca76bf...22fb5`) enters the statistics.

No alternate key, period, direction, boundary, rail extraction, keyword,
password, or oracle was tried. Dictionary words, fixed keywords, `Z@97`, and
`KMODEST` were excluded because earlier phases had already inspected them.

The four frozen one-sided statistics were:

1. English quadgram mean under the repository's pinned table;
2. level-9 raw-DEFLATE byte saving;
3. lag-1 mutual information between adjacent letters;
4. longest exact repeated substring.

Each stage used 10,000 deterministic permutations and the same inclusive
rank-max correction across all four statistics.

## Results

| Stage | Null preserves | Corrected p | Decisive behavior | Registered outcome |
|---|---|---:|---|---|
| 426 | exact 563-letter tail multiset | 0.000300 | compression and lag-1 dependence | `continuation_structure_positive` |
| 427 | exact multiset within each parity rail | 0.004100 | lag-1 dependence only | `residual_structure_positive` |
| 428 | leading singleton plus all 281 globally aligned output digraphs | 0.536346 | every statistic null-like | `digraph_mechanical_attribution` |

Phase 428's final individual upper-tail p-values were:

| Statistic | Observed | p |
|---|---:|---:|
| English quadgram mean | -6.986328 | 0.377462 |
| Raw-DEFLATE saving | 247 bytes | 0.189981 |
| Lag-1 mutual information | 0.788627 bits | 0.425857 |
| Longest repeated substring | 5 | 0.885611 |

## Why the controls change the conclusion

The period-570 Bifid transform splits the 1,140-coordinate ciphertext stream
in half. For each `k`, global decoded positions `(2k, 2k+1)` are respectively
the row-pair and column-pair projections of the same two FAED letters, separated
by 285 ciphertext positions. This produces two unequal parity rails and couples
each aligned output digraph even when there is no higher-level plaintext.

Phase 426 destroyed both artifacts and therefore detected them. Phase 427 kept
the rail alphabets but broke the paired-letter coupling, so mutual information
remained exceptional. Phase 428 kept every coupled digraph intact and randomized
only their order; the complete family became ordinary. The data therefore
support transform mechanics, not sequential meaning after `BTCSEED`.

## Scope

The conclusion is deliberately narrow: these four predeclared whole-tail
statistics provide no held-out forward edge beyond the Bifid digraph mechanic.
It does not prove that every possible encoding of the tail is impossible.
Further work on this branch should require an independent clue selecting a
specific consumer or structural operation; mining more tail windows or tokens
would undo the held-out discipline.

## Artifacts

- `tools/gsmg/phase426_btcseed_heldout_continuation_structure_audit.py`
- `tools/gsmg/phase426_result.json`
- `tools/gsmg/phase427_btcseed_continuation_rail_attribution_audit.py`
- `tools/gsmg/phase427_result.json`
- `tools/gsmg/phase428_btcseed_continuation_digraph_attribution_audit.py`
- `tools/gsmg/phase428_result.json`
- three frozen pre-registrations in `doc/Brainstorms/`
