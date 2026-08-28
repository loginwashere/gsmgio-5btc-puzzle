---
type: preregistration
status: frozen
date: 2026-08-28
phase: 437
topics:
  - phase-3.2.1
  - source-codes
  - source-identification
  - protocol-correction
---

# Phase 437 — Corrected `SOURCE CODES` Referent Eligibility Protocol

Frozen after Phase 436 failed closed and before Phase 437 execution.

Phase 436 incorrectly required a completed Phase 418 findings entry. Phase 418
has a frozen protocol and implementation/evidence artifacts but no completed
result or findings heading. Phase 437 changes only that documentary assertion:

- require completed findings for Phases 118, 265, 268, 269, 270, 370, 416,
  417, 421, and 423;
- require the exact Phase 418 preregistration artifact to exist;
- explicitly assert that Phase 418 has no findings heading, so its protocol is
  not accidentally cited as a completed outcome.

All eleven referents, seven eligibility gates, decision rules, exclusions, and
zero-oracle/GPU scope are inherited unchanged from the frozen Phase 436
protocol. No source, transform, or eligibility decision is added or removed.

The audit may classify the raw Phase 3.2.1 block and CP1141 ciphertext as
`uncovered but ineligible`; it must not execute prime/base/direction/complement
variants unless exactly one referent passes every inherited gate. Repository
source files remain provenance-ineligible and do not count as an authenticated
uncovered puzzle family.
