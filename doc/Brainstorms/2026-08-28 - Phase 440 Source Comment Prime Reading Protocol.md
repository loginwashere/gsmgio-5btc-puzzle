---
type: preregistration
phase: 440
date: 2026-08-28
status: frozen-before-execution
classification: exploratory-not-instruction-licensed
oracle: forbidden
gpu: forbidden
---

# Phase 440 — Source-Comment Prime Reading Protocol

## Purpose and status

Phase 439 registered one especially clean but ineligible web-source object: the
ordered pair of source-only comments on the two prior HTML stages. Phase 440
will show what the smallest natural `PRIME BASICS` readings actually produce.

This is explicitly exploratory. A readable fragment cannot promote the family
without independent evidence because Phase 439 found no instruction selecting
comments, units, base, direction, rail, boundary, or consumer.

## Frozen source

Stage order is fixed:

1. `Nice to see you around! Good luck little bunny hunter ;)`
2. `You made it to the next step! Good luck little bunny hunter ;)`

The implementation must re-extract these comments from the SHA-256-pinned raw
historical HTML used by Phase 439. Retyping them as the live input is forbidden.

## Frozen normalization and boundaries

Two units:

- `letters`: retain ASCII `A-Z` only and uppercase;
- `words`: maximal ASCII alphabetic tokens, uppercase.

Two boundary modes:

- `global`: concatenate the two normalized comments in stage order, then index;
- `reset_each_comment`: index each normalized comment separately, then
  concatenate the two selected results in stage order.

No separator is inserted into selected output. For word-unit display only,
selected words are joined by a single space; the machine comparison form is
their direct concatenation.

## Frozen prime family

For every unit and boundary mode, test exactly:

- index base: zero-based and one-based;
- direction: forward and reversed before indexing;
- rail: retain prime positions and retain non-prime positions.

Primality is ordinary nonnegative integer primality: 0 and 1 are non-prime.
This gives exactly `2 × 2 × 2 × 2 = 16` variants for each unit and 32 total.
No offsets, rotations, interleavings, comment-order swaps, punctuation units,
or ad hoc substring boundaries are allowed.

## Frozen controls and comparisons

For every output report:

- variant identifier and full displayed output;
- selected/source unit counts;
- machine-form length, SHA-256, vowel fraction, and index of coincidence;
- exact occurrences of the fixed vocabulary
  `SOURCE`, `CODE`, `PRIME`, `KEY`, `PASSWORD`, `BLUE`, `YELLOW`, `RABBIT`,
  `HUNTER`, `NEXT`, `STEP`, `GOOD`, `LUCK`;
- exact equality and reverse-equality classes across all 32 outputs.

For word variants, also report the selected word list. No dictionary or language
model score is allowed: the input is already English, so such scoring would
mostly reward retention of more source text.

## Decision rule

Allowed dispositions:

- `exact_new_instruction_token_present`: an output contains one of
  `SOURCE`, `CODE`, `PRIME`, `KEY`, `PASSWORD`, `BLUE`, or `YELLOW` that was
  not already contiguous in the normalized source contributing that output;
- `only_inherited_or_flavor_tokens`: matches are limited to source-inherited
  `RABBIT`, `HUNTER`, `NEXT`, `STEP`, `GOOD`, or `LUCK`, or no fixed token occurs;
- `structural_collision_requires_review`: two distinct parameter rows become
  exactly equal or reverse-equal for a nontrivial reason that changes coverage.

Substring coincidences must be reported mechanically and not interpreted as
words unless they match the fixed vocabulary exactly.

## Stop conditions

No candidate is passed to an oracle, hashed as password material, decoded under
another cipher, sent to Docker, or evaluated on the GPU. Any further transform
requires a separate frozen protocol.
