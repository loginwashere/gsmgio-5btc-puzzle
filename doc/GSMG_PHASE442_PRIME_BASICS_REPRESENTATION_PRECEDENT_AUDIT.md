---
type: audit
phase: 442
date: 2026-08-28
status: complete
result: precedent-narrowed-negative
disposition: gated
script: tools/gsmg/phase442_prime_basics_representation_precedent_audit.py
related_phases:
  - 236
  - 270
  - 434
  - 437
---

# Phase 442 — `PRIME BASICS` Representation Precedent Audit

> **Correction (Phase 443):** The closure claim below was too narrow.
> answer_321 is also a pure single-case 1,539-letter stream and had not
> received this exact split-final-BE prime-selection rule. Phase 443 runs
> that omitted symmetric case. Read Phase 442 and Phase 443 together: the
> corrected precedent-bound set has two eligible representations, and both
> are negative.

Phase 437 registered two genuinely untested candidate representations for
`RETURN TO THE SOURCE CODES ... REINSERTING THE PRIME BASICS`: the raw
1,539-byte Phase 3.2.1 block, and its CP1141-transcoded 1,539-letter
Beaufort ciphertext. Neither was promoted, because nothing fixed which
representation, unit, base, direction, or boundary applies -- described
there as a Cartesian product too large to test without inventing analyst
choices.

This phase asks a narrower question: does the puzzle's *own* prior use of
"prime" operations already fix some of those parameters by precedent,
rather than by guess?

## The three established "prime" mechanisms

| Mechanism | Rule | Reused? |
|---|---|---|
| First-piece prime walk | sequential primes (2,3,5,...) assigned by spiral-ordered event rank; position = prime + cumulative prior-yellow offset; 1-based; forward; validated against DBBI | yes -- identical mechanics reused for the split-final-`BE` retarget |
| Stage-0 "prime cells" | keep spiral-position events whose index *itself* is prime; 0-based; no offset | no -- used once, to derive DBBI/FAED themselves, not as a reinsertion step |
| Split-final-`BE` guide retarget (Phase 270) | **verbatim reuse of the first-piece walk's mechanics**, replaying the guide's own 23-endpoint color sequence, selecting from Phase 3.2.2's answer instead of DBBI | this is itself the one prior reuse |

Only one mechanism has ever been picked up a second time and reapplied
unchanged: the sequential-prime-plus-prior-yellow rule. Every one of its
applications -- original and retargeted -- has selected from a pure
single-case *letter* stream (DBBI, then the Phase 3.2.2 answer). The
Stage-0 index-is-prime rule was never used as a "reinsert into a new
source" operation at all, so it supplies no precedent for this clause.

## Representation elimination by precedent

```text
raw Phase 3.2.1 block:  1,539 bytes, charset includes %,/:>?[_` and
                         high Latin-1 bytes (Ç, É, Ñ, ...) -- not letters
CP1141 ciphertext:       1,539 bytes, pure lowercase a-z
```

The raw block fails the one precedent that exists (every established use of
the reused rule selects from a letter-only stream); the CP1141 ciphertext
matches it exactly. This does not invent a new rule -- it applies the
existing one's own track record to eliminate one of Phase 437's two
registered candidates on evidence, not preference.

## The one candidate this licenses

Reusing the split-final-`BE` guide's already-established 23-endpoint color
sequence and the identical sequential-prime-plus-prior-yellow positioning
rule -- zero new parameters chosen -- but selecting from the CP1141
ciphertext instead of the already-tested Phase 3.2.2 answer:

```text
colors:     BBBBYBBBYYBBBBYBBYYBBYB
selection:  tkpmhlwzjputuzfytnlfajfkloewwu  (30 characters)
```

Three candidates were built, mirroring the exact sibling-order pattern
Phase 270 already used for the answer_322-sourced version of this rule: the
selection alone, selection-then-322, and 321-then-selection. Diffed against
Phase 270's own 25-candidate/50-material inventory: **zero overlap** -- this
is genuinely new material, not a resubmission.

## Result

```text
new candidates:        3
new password materials: 6 (raw + SHA-256-hex per candidate)
overlap with Phase 270: 0
structural oracle trials: 36 (6 materials x 6 KDF/cipher-size specs)
hits: 0
```

The same two-private-key padding oracle used throughout this family
(P32TRAILING's five ciphertext blocks; a hit requires the exact trailing
block of sixteen `0x10` PKCS7 bytes, false-positive probability 2^-128).

## Verdict

Precedent resolves representation (letters, not raw bytes) and, by
requiring zero deviation from the one mechanism the puzzle has ever reused,
collapses every other previously-open parameter (unit, base, direction,
boundary, serialization) to the values already fixed by that mechanism --
no analyst choice was exercised. The resulting minimal, non-arbitrary
candidate family is negative.

This closes the *representation* question raised in Phase 437 as far as
precedent can settle it. It does not close Phase 437's broader referent
question: "reuse the existing rule with zero deviation" is itself a
principle, not a certainty, and nothing rules out a genuinely different
prime rule never yet used in this puzzle. Reopening requires either new
evidence for a different rule, or a new representation candidate this
comparison did not consider.

No GPU work occurred. No live-leader or P32TRAILING mutation occurred --
this is a read-only decrypt attempt against the already-authenticated
ciphertext.

Reproduce:

```bash
python3 tools/gsmg/phase442_prime_basics_representation_precedent_audit.py --self-test
python3 tools/gsmg/phase442_prime_basics_representation_precedent_audit.py \
  --json tools/gsmg/phase442_result.json
```
