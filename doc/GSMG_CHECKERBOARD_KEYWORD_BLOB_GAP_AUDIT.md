---
type: audit
phase: 237
date: 2026-08-11
status: closed-negative
disposition: recognition-only
topics:
  - checkerboard
  - bye
  - ciao
  - p32trailing
  - urlblob
related_phases:
  - 232
  - 234
  - 235
script: tools/gsmg/checkerboard_keyword_blob_gap_audit.py
aliases:
  - Phase 237
---

# GSMG Checkerboard-Keyword New-Blob Gap Audit

Phase 237 closes the explicitly retained Phase-234/235 coverage gap: the
CIAO/BELLA/BYE and KEY/NOTE/SELF candidate families had legacy checkerboard-
keyword coverage against SALPH/COSMIC, wholly or in part, but not against the
later-tracked P32TRAILING and URLBLOB targets.

Reproduce the audit with:

```bash
python3 tools/gsmg/checkerboard_keyword_blob_gap_audit.py --self-test
```

## Frozen route

The audit copies the Phase-2 `cosmic_sweep.py` semantics rather than inventing
a new checkerboard family:

```text
candidate
  -> pad28(candidate)
  -> decode DBBI and FAED
     under {a0i8, a1i9} x all 45 decimal escape pairs
  -> answer_forms
  -> keystr_forms (raw, SHA-256 hex, double-SHA-256 hex)
  -> legacy AES-CBC oracle
     under {SHA-256, MD5, SHA-1} x {AES-256, AES-128}
  -> {P32TRAILING, URLBLOB}
```

SALPH/COSMIC were not rerun. Native base-9 `pad25`, transforms, newline or
whitespace variants, extended ciphers/KDFs, autokey, and chain addition were
excluded. URLBLOB remains provenance-labeled; including it closes coverage
without promoting it to an authenticated peer of P32TRAILING.

The exact candidate set was frozen before execution:

| Family | Candidates |
|---|---|
| CIAO/BELLA/BYE | `bye`, `ciao`, `bella`, `ciaobella`, `ciaobellao`, `obellaciao`, `bellaciao` |
| KEY/NOTE/SELF | `key`, `note`, `self`, `keynote`, `selfself` |

Spaces, punctuation, and case do not create additional `pad28` alphabets, so
forms such as `CIAO BELLA O` are already represented by `ciaobellao`.
`goodbye` was not added: the authenticated structural output is `BYE`, while
`goodbye` appeared only as a generic corpus-search synonym.

## Result

| Measure | Count |
|---|---:|
| Exact candidates | 12 |
| Candidate x stream tests | 24 |
| Decoder configurations | 2,160 |
| Valid decodes | 1,776 |
| Normalized keystring calls | 14,328 |
| Blob x KDF primitive decryptions | 171,936 |
| Strong hits | **0** |
| Weak telemetry records | **0** |

The self-test independently checks the known Phase-3.2.2 checkerboard vector
and the known Phase-3.2 AES-CBC password/plaintext vector before running the
open-target audit. Weak-candidate logging is retained but redirected to a
temporary file, preventing the bounded audit from mutating the repository.

## Interpretation

This is a clean negative result for one inherited route. It closes the named
P32TRAILING/URLBLOB checkerboard-keyword gap, including the previously wholly
untested `selfself` keyword. It does not weaken the structural
`BUT/HYE -> BYE -> CIAO BELLA O` recognition checkpoint: it shows only that
these words do not yield a consumer through the frozen Phase-2 legacy board
and AES-CBC path.

No password, plaintext, or authenticated consumer was found. The recognition
row remains parked, and no broader checkerboard, autokey, or chain-addition
sweep follows from this result.
