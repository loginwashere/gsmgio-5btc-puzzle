---
type: audit
phase: 465
date: 2026-09-01
status: closed
result: negative
disposition: rejected
evidence_level: authenticated-artifact
script: tools/gsmg/phase465_phase1_running_key_audit.py
---

# Phase 465 — Phase-1 Credential Running-Key Audit

## Question

Does Phase 461's `THEFLOWER` checkpoint route the full authenticated Stage-1
credential—or its exact continuation after `THEFLOWER`—back into DBBI/FAED as
a modular running key?

The protocol froze two already-implemented mechanisms: raw base-9 shifting
before segmentation (Phase 320) and code-slot modulo-25 shifting after
segmentation (Phase 310), both signs, current target-specific escape pairs,
and both registered topologies. Every cyclic key offset was a matched control;
offset zero was the prediction because that is the authentic `THEFLOWER`
boundary.

## Result

Offset zero never ranked first for FAED in any of the eight configurations:

```text
full credential: 50/53, 23/53, 9/53, 7/53
post-THEFLOWER continuation: 30/44, 27/44, 44/44, 21/44
```

The preregistered structural gate therefore failed. The language-decoding
tier did not run. DBBI likewise produced no joint support: its valid
offset-zero ranks were `8/53`, `17/53`, `35/36`, `7/33`, `30/44`, and
`31/44`; two full-credential raw-base9 variants could not segment at offset
zero.

## Verdict

`no_offset_zero_structural_gate`. The full Phase-1 credential is not
privileged as an inherited Phase-310/320 running key over DBBI/FAED. This
closes only that exact family; it does not weaken `THEFLOWER` as a recognition
checkpoint.

Zero password candidates, decryptions, or oracle calls were made.

Artifacts: preregistration and manifest, `tools/gsmg/phase465_result.json`,
audit script, and test.
