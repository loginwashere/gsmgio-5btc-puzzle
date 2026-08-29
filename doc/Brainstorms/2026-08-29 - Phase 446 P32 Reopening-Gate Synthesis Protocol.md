---
type: protocol
phase: 446
date: 2026-08-29
status: frozen-before-classification
topics:
  - p32-trailing
  - coverage
  - reopening
  - synthesis
---

# Phase 446 — P32 Reopening-Gate Synthesis Protocol

## Question

Across the project's completed work, which materially distinct P32TRAILING
families have actually been tested, what remains genuinely untested, and what
new evidence would license each residual?

This is a documentation and coverage synthesis. It generates no password
material and invokes no cryptographic oracle.

## Inclusion rule

Include a family if at least one of these holds:

1. it explicitly targeted P32TRAILING;
2. it established or calibrated P32TRAILING's container, KDF, cipher, or
   output-role mechanics;
3. it appears in either canonical P32 brainstorm and was later executed;
4. it is recorded in the backlog or frontier ledger as a residual capable of
   changing P32 coverage.

Evidence-prospecting families that produced no password candidate remain in
scope because they close possible sources of future P32 material.

## Aggregation rule

Aggregate phases when they vary only a cipher mode, KDF, newline form,
detector, implementation repair, or corpus backfill over the same material
source. Split families when they change the source object, construction rule,
or evidence channel. A protocol-invalid run is not counted as tested; its
corrected successful successor is.

The table is a family-level map, not an attempt-count ledger. Phase references
must make every aggregation auditable.

## Residual classes

Each family receives exactly one residual class:

- `none_within_scope`: its declared finite family is exhausted;
- `finite_unrun`: a bounded implementation-ready delta is genuinely unrun;
- `conditional_unrun`: a concrete delta exists but requires separate
  authorization, provenance, or a prerequisite object;
- `unselected_variants`: conceivable variants exist, but no primary evidence
  selects their parameters; they are not an executable backlog;
- `new_evidence_only`: only a changed or newly authenticated source can reopen
  the family.

## Reopening rule

An untested construction is licensed only if at least one load-bearing field
changes through evidence independent of the proposed output:

1. source object or authenticated bytes;
2. operand boundary and normalization;
3. operation/KDF/cipher/direction/order;
4. downstream consumer or output role;
5. target object or independently fixed validator.

Merely increasing permutations, dictionaries, model samples, cipher menus, or
language-score thresholds does not count as new evidence.

## Required controls

- State the one already-runnable finite residual separately from speculative
  variants.
- Preserve explicit but unauthorized widenings rather than calling them
  covered.
- Do not imply that a zero-hit family disproves all possible passwords.
- Do not repeat an oracle run during this synthesis.
- No Docker, GPU, network, or external-agent activity.
