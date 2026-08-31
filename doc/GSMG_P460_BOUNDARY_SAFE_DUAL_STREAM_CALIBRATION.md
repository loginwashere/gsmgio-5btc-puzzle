---
type: audit
phase: 460
date: 2026-08-30
status: complete
result: no-calibrated-escape-pair-specialization
disposition: calibration-only-no-gap-closure
script: tools/gsmg/phase460_boundary_safe_dual_stream_calibration.py
---

# Phase 460 — Boundary-Safe Dual-Stream Calibration

## Question and correction

Does selecting separate DBBI/FAED escape pairs improve held-out code-IC loss
over one shared pair after respecting every candidate tokenizer's complete code
boundaries?

Phase 459 split raw streams before tokenization and was declared protocol
invalid when an artificial split cut an escape code. Phase 460 was separately
frozen before corrected scoring. For every one of all 36 unordered pairs, it
tokenizes the complete stream first and splits that pair's complete token
sequence at `floor(n/2)`. Full-stream-invalid pairs are ineligible.

Protocol:
[Phase 460 Boundary-Safe Protocol](Brainstorms/2026-08-30%20-%20Phase%20460%20Boundary-Safe%20Dual-Stream%20Calibration%20Protocol.md), SHA-256
`3021d114d72166e3cb4bcf8e35554270965494d40cba19bc28ca635626d1d19c`.
Manifest SHA-256:
`c1a1c09b4859caab39b42a1b8010cdb57492ed3e2cc75980ae96bac0dc66b9e6`.

## Frozen method

In both token-half directions, fit either one shared pair or one pair per
stream on training tokens and score only the opposite tokens. Loss is
equal-stream absolute distance from the historically fixed code IC `0.067`.
The sole statistic is mean `shared held loss - independent held loss`, positive
for specialization.

Two 20,000-replicate nulls repeat all fitting:

- randomized Euler traversals preserving exact lengths, unigrams, all directed
  bigrams, endpoints, self-transitions/runs and lag-1 structure;
- endpoint-fixed exact-multiset shuffles as sensitivity.

`robust_specialization` required a positive contrast and one-sided plus-one
`p<=0.005` under both nulls. All digest, tokenizer/IC, pair-universe, tie,
boundary-crossing, planted shared/specialized, determinism, and null-invariant
controls passed.

## Result

| Direction | Shared pair / loss | Independent DBBI/FAED pairs / loss | Contrast |
|---|---:|---:|---:|
| left tokens → right tokens | `{b,g}` / 0.022724 | `{b,i}` / `{e,g}` / 0.022456 | +0.000267 |
| right tokens → left tokens | `{b,i}` / 0.024976 | `{b,c}` / `{g,i}` / 0.010724 | +0.014252 |
| **mean** | **0.023850** | **0.016590** | **+0.007260** |

| Null | Extreme / 20,000 | One-sided p | Median | 5th–95th percentile |
|---|---:|---:|---:|---:|
| exact-transition Euler | 2,750 | 0.137543 | −0.000148 | −0.007905 to 0.012794 |
| endpoint-fixed shuffle | 6,958 | 0.347933 | 0.003544 | −0.007441 to 0.022054 |

Decision: `no_calibrated_specialization`.

The positive held-out advantage is small and common under both matched nulls.
The two directions also choose different pair identities; only one recovers
the standing FAED `{g,i}` candidate. This supplies no stable role assignment.

## Disposition

The portfolio's two-role escape experiment required a held-out prediction and
a win over a pre-registered dual-stream null. That admission gate fails.
Role-story execution is deferred unless a new primary source fixes a
deterministic role split and supplies a genuinely new held-out observable.

This does not select a shared pair, reject `{g,i}` or `{h,e}`, or override Phase
449. It also is not independent source evidence from Phase 412's emission
profile result. `G-ESC-001` and `G-YIN-001` remain parked unchanged.

Artifacts:

- `tools/gsmg/phase460_dual_stream_manifest.json`;
- `tools/gsmg/phase460_boundary_safe_dual_stream_calibration.py`;
- `tools/gsmg/test_phase460_boundary_safe_dual_stream_calibration.py`;
- `tools/gsmg/phase460_result.json`, SHA-256
  `57733be90fb9bdefc394859c884a83d4783838f5e59ba9910d9faac686117c20`.

No plaintext, password, keystring, decryption, oracle, GPU, Docker, network, or
external agent was used.

