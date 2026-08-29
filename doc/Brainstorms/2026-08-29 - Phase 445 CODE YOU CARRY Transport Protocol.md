---
type: protocol
phase: 445
date: 2026-08-29
status: frozen-before-execution
topics:
  - phase-3.2
  - architect
  - provenance
  - transport
  - p32-trailing
---

# Phase 445 — CODE YOU CARRY Transport-Role Protocol

## Question

Does the Architect clause

    ALLOWING A TEMPORARY DISSEMINATION OF THE CODE YOU HOPEFULLY CARRY

identify one exact Phase-3.2 value that is produced by an authenticated solve,
carried forward without an established consumer, and uniquely bound to the
P32TRAILING target?

This is a provenance and dataflow audit. It is not a password sweep.

## Frozen scope

Reproduce the authenticated Phase-3.2 container and the following native
objects:

1. Phase-3.2 password and encrypted blob;
2. decrypted Phase-3.2 plaintext container;
3. raw encoded 3.2.1 block;
4. CP1141 Beaufort ciphertext;
5. Beaufort key;
6. decoded answer_321;
7. raw 3.2.2 digit stream;
8. 3.2.2 decoder clue/parameters;
9. decoded answer_322;
10. textual and binary P32TRAILING envelope.

The split-final-BE guide and Phase 442–444 selections are recorded only as
downstream experimental derivatives. They are not promoted into native
Phase-3.2 outputs.

## Frozen edge classes

Each directed edge is one of:

- established: reproduced from authenticated artifacts and solved mechanics;
- container: exact child bytes occur inside the authenticated parent;
- semantic: a decoded answer describes a role but performs no demonstrated
  transformation;
- tested-negative: a proposed downstream edge was evaluated and did not open
  its target;
- hypothetical: structurally possible but not selected by primary evidence.

Only established and container edges count as demonstrated transport.

## Carrier eligibility

A node is a carried-output candidate only if all of these hold:

1. its exact value and digest are reproducible;
2. it is the output of an established transformation, not merely an analyst
   projection;
3. it is available before P32TRAILING;
4. it is not already fully consumed by the native Phase-3.2 solve;
5. it can be serialized without a new normalization choice.

The audit must report every node passing these gates. It must not remove a
candidate merely because a semantic-role interpretation seems more plausible.

## Promotion rule

A transport edge may be promoted only if:

1. exactly one carried-output candidate survives;
2. exactly one downstream consumer is independently established;
3. exactly one solved-chain transformation connects them;
4. the edge is not already covered negative.

If any count exceeds one or the consumer/transformation is absent, disposition
is non-unique transport and no password materials or oracle calls are allowed.

## Phrase-provenance control

Phase 235 established that TEMPORARY DISSEMINATION OF THE CODE YOU CARRY is
inherited from the Matrix screenplay; HOPEFULLY is the creator-added word.
This provenance is retained as a control: inherited transport language does
not independently select a puzzle object.

## Stop rules

- No candidate strings are generated.
- No blob oracle is queried.
- No GPU or Docker work occurs.
- Existing negative transport experiments may be summarized only from frozen
  result artifacts.
- A negative or ambiguous result closes only the unique-transport reading of
  this clause, not all possible downstream uses of answer_321 or answer_322.
