---
type: protocol
phase: 444
date: 2026-08-29
status: frozen-before-execution
topics:
  - phase-3.2
  - architect
  - prime-basics
  - and-or
  - p32-trailing
---

# Phase 444 — Source-Bound AND/OR Rail Protocol

## Question

Phases 434, 435, and 437 left the blue/yellow AND/OR string branch gated
until a source representation, endpoint mapping, direction, boundary, and
serialization were fixed. Phases 442 and 443 now fix two precedent-eligible
Phase-3.2.1 letter streams and replay the same split-final-BE prime mechanics
over each. Does the smallest source-bound reading of

    SIXTEEN ENCRYPTIONS
    AND OR
    SEVEN INTERTWINED PASSWORDS

produce a P32TRAILING structural hit?

## Frozen inputs

Exactly two source strings are admitted:

| Source | Length | SHA-256 |
|---|---:|---|
| CP1141 Beaufort ciphertext | 1,539 | 6d66e0e0e2dfdb812d5ecee2be6f54c1f3b8c84b0d74580686cf2053d76a200e |
| decoded answer_321 | 1,539 | 56c43a300e28b86bb43b8dcbae74c43c76bde90b3e1190620fb656f2c94b2241 |

The exact split-final-BE color profile is:

    BBBBYBBBYYBBBBYBBYYBBYB

It contains 16 blue events and 7 yellow events. Positions use sequential
primes by event rank, plus the cumulative number of prior yellow events,
1-based and forward. Blue widths are one character; yellow widths are two.
Every event must revalidate against DBBI as B or BE before source selection.

## Frozen serialization

For each source, construct:

1. blue-only: concatenate the 16 one-character blue event selections;
2. yellow-only: concatenate the seven two-character yellow event selections;
3. blue-then-yellow: concatenate those two rails in the sentence's stated
   16-then-7 order.

This is the minimal conventional interpretation:

- OR admits blue alone or yellow alone;
- AND admits blue followed by yellow;
- INTERTWINED is the original event-order weave already tested by Phases 442
  and 443 and is retained only as a regression assertion, not resubmitted.

No reverse, yellow-first, alternating reconstruction, case conversion,
alternate base, alternate prime rule, endpoint projection, wraparound, or
additional source is admitted.

## Frozen candidate grammar

Apply Phase 442's exact three-candidate outer grammar to each new rail:

1. rail alone;
2. rail followed by answer_322;
3. answer_321 followed by rail.

The sealed inventory is therefore:

    2 sources x 3 rail serializations x 3 outer forms = 18 candidates
    18 candidates x 2 treatments = 36 password materials
    36 materials x 6 KDF/cipher-size specifications = 216 trials

Treatments are raw bytes and the chain-native lowercase SHA-256 hex string.
No double hash, separator, encoding variant, or extra KDF is admitted.

## Prior-overlap gate

Before oracle evaluation, the 36 material values must be diffed against the
complete material inventories of:

- Phase 270;
- Phase 442;
- Phase 443.

Any overlap is reported and removed from the new-trial count. The expected
intertwined regressions must equal the Phase 442 and Phase 443 selections but
are never included among Phase 444 candidates.

## Oracle and decision rule

Use the unchanged authenticated P32TRAILING OpenSSL envelope and the same six
KDF/cipher-size specifications. Promotion requires the exact fifth plaintext
block of sixteen 0x10 PKCS7 bytes, corresponding to a 64-byte two-key payload.

- One or more exact padding hits: report and independently reproduce before
  inspecting keys or addresses.
- Zero hits: close only this bounded two-source AND/OR rail family.
- English-looking rail fragments without a padding hit: no promotion.

No GPU work, live-leader mutation, or broad password generation is authorized.
