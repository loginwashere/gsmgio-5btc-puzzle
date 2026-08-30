---
type: hypothesis
phase: 456
date: 2026-08-30
status: frozen
topics:
  - seed-1
  - calibration
  - roman-rail
  - architect
  - matrix-product
---

# Phase 456 — Seed-1 Transfer to Three Unresolved Rules Protocol

> [!caution] Frozen before execution
> The three rules, solved boundaries, applicability gates, success criterion,
> and non-applicability treatment below are fixed before the transfer audit is
> run. Missing source types or instructions may not be repaired with invented
> encodings.

## Question

Do any of three unresolved exact-looking rules belong to the demonstrated
creator grammar measured by Phase 341, when transferred unchanged to the
three solved AES boundaries using only each boundary's native authenticated
inputs and local instructions?

This implements item 7 in
[Post-Phase-452 Scientific Experiment Portfolio](2026-08-29%20-%20Post-Phase-452%20Scientific%20Experiment%20Portfolio.md).

## Calibration precedent

Phase 341 recovered the exact Phase 2, Phase 3, and Phase 3.2 password
preimages at rank 1 because each applied rule was licensed by that boundary's
own local instructions: component order, case/whitespace annotations,
connected assembly, literal `giveit`, and explicit SHA behavior. Its gate was
exact recovery in the top 10 from at most 100 candidates.

This phase preserves the decisive part of that method: a rule cannot be
credited on a solved boundary unless its required input type and operation are
both locally available and its output can be compared to the known preimage
without inventing a consumer or serialization.

## Frozen rules

### R-ROMAN

1. Keep only `IVXLCDM` from each authenticated rail, preserving order.
2. Prefix the literal title initial `C`.
3. Require strict canonical Roman syntax.
4. Interpret the resulting pair as ordered integers.

Source replay must recover `DBBI/FAED -> CDI/CD -> 401/400`, the unique hit
in the original 14-case rail family. `FEFE/73` remains outside the rule.

Required transfer types: textual rails, a locally selected `C)-like title
fragment, an instruction selecting Roman projection, and a locally specified
serialization from one or more numerals to password bytes.

### R-ARCH

1. Select three ordered words using a locally supplied three-index selector.
2. Extract their beginnings and endings.
3. Apply the established partial mirror9 involution to the endings, preserving
   symbols outside `a..i`.
4. Treat the transformed endings as the rule output.

Source replay must recover
`(23,16,7) -> BOTH/ULTIMATELY/THE -> BUT/HYE -> BYE`.

Required transfer types: an indexed word source, a locally supplied
three-index selector, an instruction selecting beginnings/endings and mirror9,
and a locally specified role/serialization for the three-letter output.

### R-MATPROD

1. Read a native six-decimal-digit value as a row-major 2×3 matrix.
2. Use its already-derived `(total,row1,row2)` sum list as a three-vector.
3. Multiply matrix by vector.
4. Serialize both results as unsigned bytes in listed order.

Source replay must recover
`574061 -> [[5,7,4],[0,6,1]] @ [23,16,7] -> (255,103) -> FF67`.

Required transfer types: a native six-digit value, a locally licensed 2×3
matrix reading and sum-list vector, a multiplication instruction, and a byte
consumer/serialization.

## Frozen solved boundaries

Only the Phase-341 benchmark is eligible:

| Boundary | Native solved components | Locally licensed construction |
|---|---:|---|
| Phase 2 | 1 | single unambiguous component |
| Phase 3 | 7 | ordered concatenation, per-component case/whitespace, explicit SHA |
| Phase 3.2 | 3 | ordered concatenation, lowercase/connected annotations, literal `giveit` prefix |

No Stage-1 web-form answer is added because Phase 341's executable AES
preimage/hash benchmark excluded it.

## Frozen applicability gates

For each rule × boundary cell, evaluate in order:

1. **native input type** — every required source object already exists without
   digit extraction, A1Z26, token splitting, padding, truncation, or regrouping;
2. **local operation license** — the boundary itself instructs the candidate
   operation or an exact solved precedent binds that operation at this
   boundary;
3. **comparable output type** — the rule directly emits password-preimage
   bytes, or the boundary locally specifies the exact serialization that does.

Only a cell passing all three gates may enumerate candidates or hash-compare
against the known preimage. A failed gate yields:

- `status = not_applicable`;
- `candidate_count = 0`;
- `exact_recovery = false`;
- `rank = null`;
- `branching_factor = 0`;
- `tie_count = 0`; and
- shuffled/order-preserving controls `not_run_no_eligible_main`.

Non-applicability is not a failed prediction. It measures calibration coverage
and prevents a type mismatch from being narrated as evidence against a rule.

## Pre-registered boundary expectations

- R-ROMAN: text exists at all three boundaries, but none locally selects
  Roman filtering, a title-`C) prefix, or numeral-to-password serialization.
- R-ARCH: Phase 2 lacks three components; Phase 3 and Phase 3.2 have at least
  three components, but none supplies the three-index selector or
  beginnings/endings/mirror operation, and none defines the output's role.
- R-MATPROD: none contains a native six-digit component with a locally
  licensed 2×3/sum-list reading; none instructs multiplication or byte
  serialization.

Therefore the expected strict transfer coverage is zero of nine cells. If
execution finds an authenticated local instruction contradicting this freeze,
the result is `protocol_invalidated_by_new_precedent`; the matrix must not be
silently edited after seeing it.

## Outcomes

Each rule receives exactly one:

- `seed1_transfer_supported` — at least two applicable solved boundaries,
  every applicable boundary recovers exactly within Phase 341's rank/branch
  gate, and controls are clean;
- `seed1_transfer_rejected` — at least two applicable boundaries but an
  applicable boundary fails exact recovery or controls;
- `insufficient_comparable_boundaries` — fewer than two applicable solved
  boundaries;
- `protocol_invalidated_by_new_precedent`.

The overall result reports the three independent outcomes; one rule cannot
borrow applicability or success from another.

## Exclusions and stop rule

- No new password candidates, blob oracle, decryption, language score, or
  transform menu.
- No extraction of arbitrary six digits, conversion of words to numbers,
  importing Cosmic title `C` into another page, or inventing how a
  three-letter/two-byte checkpoint becomes a full password.
- Original-source replay is a positive implementation control, not transfer
  evidence.
- Stop after all nine applicability cells and the three independent outcomes.

## Gap effect

Only `seed1_transfer_supported` can add calibrated grammar support, and even
then it cannot select the rule at its unresolved boundary or provide a
consumer. `insufficient_comparable_boundaries` leaves `G-PRIME-001`,
`G-ARCH-001`, and `G-MATPROD-001` unchanged.
