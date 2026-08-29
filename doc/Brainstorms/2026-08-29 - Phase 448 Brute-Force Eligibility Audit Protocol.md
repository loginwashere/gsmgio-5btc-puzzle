---
type: protocol
phase: 448
date: 2026-08-29
status: frozen-before-classification
topics:
  - brute-force
  - eligibility
  - finite-search
  - open-gaps
---

# Phase 448 — Brute-Force Eligibility Audit Protocol

## Question

Does any still-unresolved, clue-supported construction define a complete,
finite search space that can be enumerated without inventing a parameter bound?

The expected answer is `none`, but the gates and universe are fixed before the
rows are classified.

## Frozen universe

1. Every row currently present in `GSMG_OPEN_GAP_REGISTRY.md`.
2. Phase 446's P32 residual classes, including its one finite bookkeeping
   backfill.
3. The Architect clause `BRUTE FORCING MIGHT BE REQUIRED` as method evidence.
4. Blinded-panel/model resampling as a possible search mechanism.

Completed families such as the exact Phase-441 `16!` Bifid run are controls,
not remaining constructions. They may demonstrate what a valid finite domain
looks like but cannot become eligible again without independent reopening
evidence.

## Eligibility gates

A row is brute-force eligible only if all seven gates pass:

1. `clue_selected_operands`: authenticated evidence fixes the exact source
   object and operand boundary;
2. `fixed_operation_domain`: the operation and every varied parameter have a
   clue-supported, explicit domain;
3. `fixed_serialization`: direction, order, indexing, normalization, and output
   serialization require no analyst choice;
4. `fixed_consumer`: one unresolved downstream target/consumer is selected;
5. `fixed_validator`: success is independently defined with a controlled
   false-positive rate;
6. `unresolved_not_exhausted`: the exact family remains unresolved and was not
   already run to completion;
7. `count_calculable_without_new_bounds`: the candidate count follows from the
   preceding evidence rather than a convenient cutoff chosen for the run.

Finite arithmetic alone is insufficient. A one-item hypothesis fails if the
clue never selected that item; a two-choice escape pair fails if the decoder,
serialization, or consumer remains unknown.

## Classification controls

- `computationally_finite_skeleton` records whether a proposal can be made
  finite after analyst choices. It does not affect eligibility.
- Phase 446 F09 must be reported separately: its ~700,000-keystring nopad
  whitespace delta is finite and implementation-ready, but it is a coverage
  backfill over a curated corpus, not a newly clue-defined construction.
- “More samples” from a model/panel is not a finite domain unless the generator
  and stopping rule are independently fixed.
- Creator statements about anti-bruteforce web state do not license a
  cryptanalytic sweep.
- The creator-added Architect sentence may authorize brute force as a method
  only after another construction passes every operand/domain/consumer gate.

## Stop rules

- No candidates or password materials are generated.
- No cipher/address/blob oracle is called.
- No GPU, Docker, network, or external agent is used.
- If zero rows pass, disposition is `no_clue_supported_finite_search_space`.
