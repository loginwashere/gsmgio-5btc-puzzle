---
type: audit
phase: 466
date: 2026-09-01
status: closed
result: negative
disposition: rejected
evidence_level: authenticated-artifact
script: tools/gsmg/phase466_phase1_credential_crib_audit.py
---

# Phase 466 — Phase-1 Credential Exact-Crib Audit

## Question

Does the authenticated 53-letter Stage-1 credential, or its 44-letter
continuation after `THEFLOWER`, occur as plaintext inside DBBI/FAED under the
registered straddling-checkerboard segmentations?

The exact bijective repetition-pattern matcher from the earlier macro crib
attack was applied to DBBI `{b,e}` and FAED `{g,i}`/`{h,e}`. Every nonzero
cyclic rotation of each crib was checked as a matched control. No reversal,
substring, fuzzy match, alphabet guess, or oracle was allowed.

## Result and verdict

Across six crib/target/pair families:

```text
authentic offset-zero matches: 0
nonzero cyclic-control matches: 0
promoted families: 0
```

`exact_crib_negative`. The known credential is not embedded as monoalphabetic
checkerboard plaintext in DBBI or FAED under the current segmentations.

Zero password candidates, decryptions, or oracle calls were made.

Artifacts: preregistration, `tools/gsmg/phase466_result.json`, audit script,
and test.
