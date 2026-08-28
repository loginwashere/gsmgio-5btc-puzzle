---
type: audit
phase: 437
date: 2026-08-28
status: complete
result: no-eligible-referent
disposition: gated
script: tools/gsmg/phase437_source_codes_referent_eligibility_corrected_audit.py
---

# Phase 437 — Corrected `SOURCE CODES` Referent Eligibility Audit

No currently authenticated `SOURCE CODES` referent is sufficiently specified
to authorize a new extraction or password run.

Phase 437 corrects Phase 436's documentary assertion only. Phase 436 required
a completed Phase 418 finding that does not exist; Phase 437 instead verifies
the Phase 418 preregistration artifact and uses completed Phase 416/417/421/423
findings for execution history. The eleven referents and seven eligibility
gates were unchanged.

## Referent matrix

| Referent | Existing coverage | Decisive failed gates | Disposition |
|---|---|---|---|
| Matrix film/screenplay difference | Phase 118 word-LCS plus base-0/base-1 prime family negative | representation, exact operator/unit, consumer | covered and non-unique |
| Raw 1,539-byte Phase 3.2.1 block | Pinned as evidence, absent from Phase 270 candidates | local selection, representation, operator, unit/boundary | **uncovered but ineligible** |
| CP1141 1,539-letter Beaufort ciphertext | Pinned as evidence, absent from Phase 270 candidates | local selection, representation, operator, unit/boundary | **uncovered but ineligible** |
| Decoded Phase 3.2.1 answer | Direct/line/word/reverse/whole-block families negative | self-reference, representation, operator/unit | direct use covered |
| Raw 149-digit Phase 3.2.2 number | Phase 265 and Phase 416 candidate negative | raw-vs-decoded choice, operator/unit | covered direct material |
| Decoded 91-letter Phase 3.2.2 answer | Phase 270 pure primes, prime walk, guide projections, and compositions negative | raw-vs-decoded choice; no remaining fixed operator | grounded families covered |
| Exact parent prefix before P32 | Both exact separator boundaries negative in Phase 270 | novelty only | fully specified but already closed |
| First-piece/Stage-0 material | Phase 270 prime/color/projection families negative | not selected by this clause; grid/consumer ambiguity | covered grounded projections |
| Split-final-`BE` guide | Phase 270 direct prime/token/raw endpoint consumers negative | source mapping, direction, AND/OR serialization | checkpoint, consumer unbound |
| `X2SH4Y0QB15` | Phases 268–269 full bounded family negative | distant, no creator edge, representation/operator | covered distant reading |
| Repository source files | Not creator-authored puzzle bytes | authentication plus every operational gate | provenance-excluded |

## The real remaining gap

The raw Phase 3.2.1 encoded block and its CP1141-transcoded Beaufort
ciphertext have not been used individually as prime-selection sources. This is
now recorded explicitly so it is not mistaken for already-tested coverage.

It is still not a runnable hypothesis. At minimum, new evidence must decide:

- raw encoded bytes versus CP1141 letters versus decoded letters;
- byte, letter, word, or event units;
- zero- or one-based primes;
- forward or reverse direction;
- prime-retained or complement rail;
- full stream or another authenticated boundary;
- how the result is serialized for its consumer.

Running this Cartesian product now would test analyst choices rather than an
instruction supplied by the puzzle.

## Verdict

`SOURCE CODES` does not resolve the source object required by the blue/yellow
`AND/OR` proposal. Zero of eleven referents passes all seven gates. The exact
raw/ciphertext gap stays registered as `authenticated_uncovered_but_ineligible`,
not silently closed and not promoted.

No password material was generated, no oracle call occurred, and the GPU run
was untouched.

Reproduce:

```bash
python3 tools/gsmg/phase437_source_codes_referent_eligibility_corrected_audit.py --self-test
python3 tools/gsmg/phase437_source_codes_referent_eligibility_corrected_audit.py \
  --output tools/gsmg/phase437_result.json
```
