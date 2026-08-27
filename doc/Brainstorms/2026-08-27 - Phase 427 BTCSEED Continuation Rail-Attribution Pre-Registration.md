# Phase 427 — BTCSEED Continuation Rail-Attribution Pre-Registration

## Trigger and question

Phase 426's frozen exact-tail-multiset test was positive through raw-DEFLATE
saving and lag-1 mutual information, while its English quadgram and repeated-
substring statistics were null-like. Phase 408 had already established that
the period-570 Bifid output mechanically alternates a restricted `{B,C,D,E}`
rail with a wider-alphabet rail.

Does any Phase-426 signal remain after the null preserves those two rails, or
is the apparent continuation structure attributable to that known Bifid
mechanic?

This follow-up was registered after observing Phase 426 and is an attribution
control, not part of Phase 426's original p-value.

## Frozen object and statistics

- use the identical Phase-386 decoded stream and `decoded[7:]` tail;
- retain Phase 426's four statistics, directions, implementation, seed
  (`0x426`), 10,000 trials, inclusive rank-max correction, and gates unchanged;
- add no new statistic, cut point, orientation, token, or decoder variant.

## Rail-preserving null

For every trial, independently permute the characters occupying local even
tail positions and local odd tail positions, then interleave them back into
their original parity slots. Thus every trial preserves:

- length 563;
- the exact character multiset of each parity rail;
- the deterministic rail alternation and its unequal alphabet supports;

while destroying sequential order within both rails. Assert those invariants
on every trial.

## Interpretation gates

- corrected `p <= 0.01`: **residual structure positive** — the Phase-426 hit
  is not fully explained by rail composition;
- `0.01 < p <= 0.05`: **residual structure suggestive only**;
- corrected `p > 0.05`: **rail-mechanical attribution** — Phase 426's broad
  ordering hit is absorbed by the already-known alternating-rail mechanic.

Even a residual positive would not establish plaintext. A rail-mechanical
result closes these four statistics as a forward edge but does not retract the
separate Phase-425 significance of the exact `BTCSEED` prefix.
