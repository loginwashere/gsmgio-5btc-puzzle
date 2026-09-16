# GSMG Phase 512G — exact credential crib audit

Date: 2026-09-16

## Scope

Phase 512G tested one closed, independently authenticated crib against FAED
under one exact Model-B geometry:

- crib: the complete 53-letter Phase-1 credential;
- width/direction: width 15, untranspose;
- all 36 escape pairs;
- all 518 possible raw starts;
- all 26,333 legal single/double classifications of the crib's letters;
- exact checkerboard-code equality and injectivity constraints;
- valid token boundary at the crib start and valid full-stream segmentation.

No text scoring, substring, mutation, or near-match criterion was available.

## Calibration

The blind synthetic positive recovered the exact pair, raw start, length
pattern, and column order without an earlier false hit. A deterministic
crib-absent fixture exhausted the full 18,648-cell family with zero hits. The
real runner was locked only after truth-agnostic and boundary-aware tests
passed.

## Result

The locked real search completed all 518 × 36 = 18,648 cells:

- exact hits: 0;
- incomplete/node-limited cells: 0;
- runtime: 2,622.1 seconds;
- verdict: bounded negative.

The independent verifier revalidated all cell identities and counts and the
lock/checkpoint/result hash chain. No sensitive-hit artifact exists.

## Limits

This result rejects only the complete Phase-1 credential at width 15 in the
untranspose geometry. It does not reject the Phase-3.2.2 answer, creator macro,
other independently established cribs, other widths/directions, Model B as a
whole, or non-checkerboard constructions.

The two longer cribs are currently too slow in the Python implementation
(roughly 6.4 and 13.1 projected hours). Their next prerequisite is a native CSP
with exact parity against the frozen reference—not a larger Python run.
