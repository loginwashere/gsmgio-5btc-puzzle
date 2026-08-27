# Phase 428 — BTCSEED Continuation Digraph-Attribution Pre-Registration

## Trigger and question

Phase 427 preserved decoded parity-rail composition and retained a corrected
signal only in lag-1 mutual information. Under the frozen one-block Bifid
algebra, consecutive global decoded positions `(2k, 2k+1)` are the row-pair
and column-pair projections of the same two `FAED` letters separated by half
the 570-character block. Their statistical coupling is therefore built into
the transform.

Does any Phase-426/427 signal remain after preserving every such output
digraph intact and randomizing only digraph order?

This is a post-result attribution control, not part of either earlier p-value.

## Frozen object, null, and statistics

- use the identical Phase-386 stream and tail `decoded[7:]`;
- because global position 7 is the second half of the `(6,7)` digraph, hold
  `decoded[7]` fixed as a leading singleton;
- split the remainder into the 281 globally aligned digraphs
  `decoded[8:10] ... decoded[568:570]`;
- for 10,000 trials with seed `0x426`, permute those exact digraph blocks and
  concatenate them after the fixed singleton;
- retain Phase 426's four statistics, directions, inclusive rank-max family
  correction, and gates unchanged;
- assert exact full-tail multiset, exact digraph multiset, fixed singleton,
  and length on every trial.

This null preserves parity rails and the within-digraph dependency that the
Bifid transform mechanically creates, while destroying dependence between
successive digraphs.

## Interpretation gates

- corrected `p <= 0.01`: **beyond-digraph residual positive**;
- `0.01 < p <= 0.05`: **beyond-digraph residual suggestive only**;
- corrected `p > 0.05`: **digraph-mechanical attribution**.

A digraph-mechanical result means the earlier broad and rail-preserving hits
do not establish continuation semantics. It does not retract Phase 425's
separate exact-prefix result or claim that every possible tail encoding is
excluded.
