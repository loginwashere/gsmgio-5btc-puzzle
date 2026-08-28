---
type: audit
phase: 443
date: 2026-08-28
status: complete
result: two-representation-precedent-family-negative
disposition: gated
script: tools/gsmg/phase443_answer321_prime_basics_followup.py
related_phases:
  - 270
  - 437
  - 442
---

# Phase 443 — answer_321 PRIME BASICS Precedent-Gap Follow-up

## Correction to Phase 442

Phase 442's representation argument was too narrow. Its actual precedent was
that every established application of the reused sequential-prime rule selects
from a pure single-case letter stream. That eliminates the raw 1,539-byte
Phase-3.2.1 block, but it does not uniquely select the CP1141 ciphertext.
The decoded Phase-3.2.1 Architect plaintext (answer_321) is also a pure
single-case 1,539-letter stream.

Phase 270 tested whole-text, line, word, reverse, concatenated, and several
prime-derived readings involving answer_321, but never applied this exact
split-final-BE sequential-prime-plus-prior-yellow rule to answer_321.
Therefore the honest precedent-bound representation set contains two members:

| Representation | Length | Pure single-case letters | Exact rule previously tested? |
|---|---:|---:|---:|
| CP1141 ciphertext | 1,539 | yes, lowercase | yes, Phase 442 |
| decoded answer_321 | 1,539 | yes, uppercase | no, before this phase |

## Frozen method

Only the selected source changes. Everything else is inherited unchanged from
Phase 442:

- split-final-BE colors: BBBBYBBBYYBBBBYBBYYBBYB;
- sequential primes 2, 3, 5, ... by event rank;
- position = prime + cumulative prior-yellow offset;
- 1-based, forward, widths 1 for blue and 2 for yellow;
- every position revalidated against DBBI as B or BE;
- exact three-candidate grammar: selection alone, selection then 3.2.2, and
  3.2.1 then selection;
- raw and SHA-256-hex treatments;
- the same six KDF/cipher-size specifications and two-key structural padding
  oracle.

No reverse, alternate base, different prime rule, extra concatenation, or
new boundary is admitted.

## Deterministic selection

    source:     decoded answer_321
    length:     1,539 uppercase letters
    colors:     BBBBYBBBYYBBBBYBBYYBBYB
    selection:  OULFTHSFRINANNCQANINEROINTILEA
    length:     30 letters

The selection reads suggestively in fragments, but it is not coherent
plaintext and was not promoted on appearance. The predeclared structural
oracle is decisive for this bounded family.

## Result

    new candidates:                   3
    new password materials:           6
    overlap with Phase 270 materials: 0
    overlap with Phase 442 materials: 0
    structural oracle trials:         36
    hits:                              0

The three candidates have lengths 30, 121, and 1,569 bytes. A hit required
the exact final AES block of sixteen 0x10 bytes in the authenticated
P32TRAILING envelope; none occurred.

## Verdict

Phase 442's claimed one-representation closure is corrected. Under its stated
pure-single-case-letter precedent, there are exactly two locally identified
eligible Phase-3.2.1 representations. Phase 442 tested the CP1141 ciphertext;
Phase 443 tests the omitted decoded answer_321 with identical mechanics. Both
are negative.

The corrected closure is therefore limited but now complete: the
two-representation, zero-deviation precedent family is exhausted. This still
does not prove that PRIME BASICS must use that rule, nor close the broader
SOURCE CODES referent question. Reopening requires independent evidence for
another source representation or another prime operator—not a third
representation selected merely by analyst preference.

No GPU work occurred. No live-leader or P32TRAILING state was mutated; this was
a read-only decrypt attempt against already-authenticated ciphertext.

Reproduce:

    python3 tools/gsmg/phase443_answer321_prime_basics_followup.py --self-test
    python3 tools/gsmg/phase443_answer321_prime_basics_followup.py \
      --json tools/gsmg/phase443_result.json
