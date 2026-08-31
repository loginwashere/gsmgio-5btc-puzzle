---
type: audit
phase: 459
date: 2026-08-30
status: complete
result: protocol-invalid-token-boundary-confound
disposition: superseded-by-phase-460-no-inference
script: tools/gsmg/phase459_dual_stream_escape_pair_calibration.py
---

# Phase 459 — Dual-Stream Escape-Pair Calibration (Protocol Invalid)

Phase 459 attempted a held-out comparison of one shared versus two independent
DBBI/FAED escape pairs. Its protocol was frozen before scoring and its output is
reproducible, but a post-run methodological check found that its raw-position
splits (`45|46`, `285|285`) were not guaranteed token boundaries.

In the right-to-left FAED direction, `{g,i}` is valid on the complete stream,
but the artificial left half ends on an escape whose consumed symbol lies at
the start of the other half. The protocol assigned the resulting truncated
half loss `1.0`. Thus the reported contrast `-0.4844868` partly measures an
invalid split through a two-symbol code, not held-out model failure.

This is a design defect, not a failed integrity control or an implementation
deviation from the manifest. The raw result
(`tools/gsmg/phase459_result.json`, SHA-256
`9fa56fd664f803e1b7febab8fc36660cda08c4c10fc8bc6e2019fcfb0b0c5d12`)
is retained for auditability but licenses **no** inference about shared or
specialized pairs and must not be quoted as a negative calibration result.

The protocol was not repaired after seeing output. Phase 460 versioned the
correction: tokenize each complete stream under each pair first, then split the
resulting complete token sequence. See
[GSMG_P460_BOUNDARY_SAFE_DUAL_STREAM_CALIBRATION](GSMG_P460_BOUNDARY_SAFE_DUAL_STREAM_CALIBRATION.md).

No plaintext, password, decryption, oracle, GPU, Docker, network, or external
agent was used. `G-ESC-001` and `G-YIN-001` are unchanged.

