---
type: preregistration
phase: 466
date: 2026-09-01
status: frozen-before-execution
---

# Phase 466 — Phase-1 Credential Exact-Crib Protocol

## Hypothesis

If `THEFLOWER` routes the solver back to the authenticated Stage-1
credential, that credential—or the exact continuation after `THEFLOWER`—may
occur as plaintext inside DBBI or FAED under the already-established
straddling-checkerboard segmentation model.

This differs from prior coverage: Phase 313 used unused song text as alphabet
keywords, and the original crib attack used the creator's 2023 macro text.
Neither tested the 53-letter authenticated credential as known plaintext.

## Frozen family

- cribs: the complete credential and the 44-letter continuation strictly
  after `theflower`;
- targets/pairs: DBBI with `{b,e}`; FAED with `{g,i}` and `{h,e}`;
- detector: exact bijective repetition-pattern matching from `crib_drag.py`;
- controls: every nonzero cyclic rotation of each crib.

No reversal, substring, spelling change, alternate escape pair, fuzzy match,
language score, or password oracle is allowed.

## Promotion

Promotion requires at least one offset-zero match and requires offset zero to
be unique among every cyclic control for that crib/target/pair. The forced
code-to-letter map must then expose coherent surrounding plaintext not supplied
to the detector. Otherwise close this exact embedded-credential hypothesis.
