---
type: audit
phase: 456
date: 2026-08-30
status: complete
result: zero-of-nine-transfer-cells-applicable
disposition: calibration-not-applicable-output-and-instruction-mismatch
script: tools/gsmg/phase456_seed1_unresolved_rule_transfer.py
---

# Phase 456 — Seed-1 Transfer to Three Unresolved Rules

## Question

Do the Roman/title-`C`, Architect beginnings/endings plus mirror9, or matrix
product/`FF67` rules transfer to Phase 341's solved boundaries under the same
local-instruction discipline that recovered all three known AES preimages at
rank 1?

Protocol:
[Phase 456 Seed-1 Transfer to Three Unresolved Rules Protocol](Brainstorms/2026-08-30%20-%20Phase%20456%20Seed-1%20Transfer%20to%20Three%20Unresolved%20Rules%20Protocol.md).

## Method

Each subtest had two independent stages:

1. replay the exact rule on its original source boundary as a positive
   implementation control; and
2. check every Phase 2/3/3.2 boundary for native input type, a local operation
   license, and a directly comparable password-preimage output.

Only cells passing all three gates could enumerate or hash-compare candidates.
Missing types or instructions could not be repaired by extracting digits,
converting words to numbers, importing Cosmic Duality's title `C`, or
inventing a serialization from a short checkpoint to password bytes.

The frozen contract is:

    tools/gsmg/phase456_seed1_transfer_manifest.json
    SHA-256 3cee27de78483877025a48ba4c2bb5cd537f461ee45730f342306fbc9c8cd9dc

## Source replay controls

All three exact constructions still reproduce:

| Rule | Fixed output | Frozen main family | Exact rows | Ties at fixed rank |
|---|---|---:|---:|---:|
| Roman filtering + title `C` | `CDI/CD = 401/400` | 14 | 1 | 0 |
| Architect edges + partial mirror9 | `BUT/HYE -> BYE` | 6 fixed-word orders | 1 | 0 |
| Matrix × sum-list + byte serialization | `(255,103) -> FF67` | 6 vector orders | 1 | 0 |

These controls prove that the implementations did not fail. They do not count
as solved-boundary transfer evidence because each replays the same material
that originally defined its rule.

## Transfer matrix

| Rule | Phase 2 | Phase 3 | Phase 3.2 |
|---|---|---|---|
| Roman/title-`C` | not applicable: operation and serialization absent | not applicable: operation and serialization absent | not applicable: operation and serialization absent |
| Architect edges/mirror | not applicable: input arity, operation, and output role absent | not applicable: selector/operation and output role absent | not applicable: selector/operation and output role absent |
| Matrix product/`FF67` | not applicable: native type, operation, and serialization absent | not applicable: native type, operation, and serialization absent | not applicable: native type, operation, and serialization absent |

The important details are:

- all three boundaries contain text, but none says to retain Roman-numeral
  letters, select a title initial, or serialize numeral values as its password;
- Phase 3 and Phase 3.2 contain at least three components, but neither supplies
  a three-index selector or an edges/mirror instruction;
- Phase 3's numeric component is `11110`, five digits—not a native six-digit
  2×3 matrix source—and digit extraction from its hex/FEN components was
  forbidden; and
- none specifies how `BYE` or two bytes such as `FF67` become the full
  boundary preimage.

Accordingly, every transfer cell records:

- candidate count `0`;
- branching factor `0`;
- exact recovery `false`;
- rank `null`;
- ties `0`; and
- shuffled/order-preserving controls `not_run_no_eligible_main`.

## Verdict

`all_three_insufficient_comparable_boundaries`.

Each rule's independent outcome is `insufficient_comparable_boundaries`.
Zero of nine cells are applicable. This is not
`seed1_transfer_rejected`: no eligible prediction failed. It instead shows
that Phase 341 calibrates assembly grammar only where a boundary locally binds
the needed components, operation, and output role; these three checkpoint
rules have no comparable solved GSMG boundary.

- Seed-1 support added: no;
- rules rejected: no;
- gap closures: 0;
- new password candidates: 0;
- oracle calls: 0; and
- decryptions attempted: 0.

The deterministic result is:

    tools/gsmg/phase456_result.json
    SHA-256 51b5f3515ca4182655f6ce996f6d7643085e8cd452eaa7a7c7fe6cd4e243ac90

Reproduce:

    python3 tools/gsmg/phase456_seed1_unresolved_rule_transfer.py --self-test
    python3 tools/gsmg/phase456_seed1_unresolved_rule_transfer.py --run
    python3 -m unittest tools/gsmg/test_phase456_seed1_unresolved_rule_transfer.py

## Disposition

`calibration_not_applicable_output_and_instruction_mismatch`.

`G-PRIME-001`, `G-ARCH-001`, and `G-MATPROD-001` remain unchanged. A
future transfer becomes informative only when a genuinely solved boundary
contains the same native input type, a local instruction selecting the same
operation, and a comparable output role. Re-running against the same three
boundaries with invented conversions would violate the Phase-341 precedent.
