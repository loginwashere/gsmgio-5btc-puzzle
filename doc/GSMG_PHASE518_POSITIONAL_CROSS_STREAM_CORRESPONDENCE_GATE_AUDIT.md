---
type: audit
phase: 518
date: 2026-09-17
status: complete
result: no-calibrated-correspondence
disposition: corroboration-only-no-gap-closure
script: tools/gsmg/phase518_positional_cross_stream_correspondence_gate.py
---

# GSMG Phase 518 — Positional Cross-Stream Correspondence Gate

## Question

The Post-Phase-452 Portfolio's item 1 proposes a closed six-way tournament
of DBBI/FAED generator hypotheses (independent generators, shared latent
alphabet, DBBI-parameterizes-FAED, FAED-parameterizes-DBBI, alternating
control/data channels, common source through two encoders). This phase is
the tournament's prerequisite gate: is there **any** detectable positional
correspondence between DBBI and FAED at all, beyond what each stream's own
internal structure already explains? If none survives, the five
non-independent branches have nothing to be built on.

This is a pure statistical dependency test, not a new coupling operator in
the sense of Phases 271–321's ~50 tested ciphers/transforms. No operator is
proposed, no plaintext/password/key material is generated, and no AES oracle
or English-language score is used.

## Correction before real scoring

Protocol:
[Phase 518 Positional Cross-Stream Correspondence Gate Protocol](Brainstorms/2026-09-17%20-%20Phase%20518%20Positional%20Cross-Stream%20Correspondence%20Gate%20Protocol.md),
committed before implementation. Its required pre-interpretation controls
(run on synthetic fixtures, before DBBI/FAED were ever touched) found the
original "`K=91` AND `K=13` both required" promotion rule was underpowered:
a fixture with total, by-construction correspondence at `K=91` did not
reliably clear `p<=0.005` at `K=13`, because 13 aligned data points is too
small a sample for the mutual-information estimator to separate real signal
from a noisy null at that threshold, regardless of true relationship
strength. Corrected same day, before any real score was computed: `K=91` is
the sole primary promotion gate; `K=13` is reported as a directional
sensitivity diagnostic only. Manifest SHA-256 pins both the corrected
protocol text and every precedent script this phase reuses.

## Method

`tools/gsmg/phase518_positional_cross_stream_correspondence_gate.py`. Both
DBBI (91 symbols) and FAED (570 symbols) are partitioned into `K` contiguous
proportional blocks (`K=91`, `K=13` — both exact divisors of 91); each
block's feature is its mode raw symbol (alphabetical tie-break). The
statistic is the plug-in mutual information (bits) between the `K` aligned
`(DBBI_block_mode, FAED_block_mode)` pairs, reusing the already-validated
`mutual_information()` from `dbbi_faed_base81_token_audit.py`. At `K=91`
this reduces to DBBI's own raw symbol at each position.

Two matched nulls, 20,000 replicates each, reusing the exact null generators
validated in Phases 459/460: independent Euler-traversal surrogates
(preserving each stream's own length, unigrams, all directed bigrams,
endpoints, self-transitions/runs) and independent endpoint-fixed
exact-multiset shuffles (preserving length/unigrams/endpoints only, breaking
transition structure as a sensitivity check). Both streams are shuffled with
independent RNG state, destroying any real cross-stream alignment while
preserving each stream's own internal statistics — exactly the "matched
nulls preserve lengths, symbol counts, ... runs, autocorrelation" bar the
portfolio doc requires.

## Controls

- `mutual_information()` reproduces its existing planted-vs-independent
  self-test.
- Euler/endpoint-shuffle surrogates preserve their declared invariants
  (reused assertions from Phase 459).
- Deterministic replay under the frozen seed `51820260917`.
- Independent-fixture negative control (two synthetic streams, matching
  lengths/marginals, no real relationship): `no_calibrated_correspondence`.
- Planted-correspondence positive control (a synthetic FAED-like stream
  built by deterministically expanding each synthetic DBBI-like symbol into
  its proportional block): `robust_correspondence` at `K=91`, demonstrating
  the test has power to detect the exact class of relationship it targets.
- Block-partition tiling is exact (no gap/overlap) at both `K` values, both
  stream lengths.

All controls passed before the real streams were scored.

## Result

| K | Observed MI (bits) | Euler-null median / p | Endpoint-shuffle-null median / p | Decision |
|---:|---:|---|---|---|
| 91 (primary) | 0.595332 | 0.560510 / `p=0.317034` | 0.561145 / `p=0.318134` | `no_calibrated_correspondence` |
| 13 (sensitivity, diagnostic only) | 0.677134 | 0.774144 / `p=0.632618` | 0.708394 / `p=0.549023` | `no_calibrated_correspondence` |

At `K=91`, the real observed statistic sits almost exactly on both nulls'
medians — statistically unremarkable. At `K=13`, the observed statistic is
actually *below* both null medians. Neither granularity shows any hint of
positional correspondence under either null.

**Phase-level decision: `no_calibrated_correspondence`** (determined solely
by `K=91` per the same-day correction; `K=13` independently agrees).

## Disposition

No detectable positional correspondence survives between DBBI and FAED at
either DBBI-native block granularity, under either matched null. This
closes the prerequisite gate for the Post-Phase-452 Portfolio's item 1: none
of the five non-independent branches (shared latent alphabet,
DBBI-parameterizes-FAED, FAED-parameterizes-DBBI, alternating control/data
channels, common source through two encoders) has a positional-alignment
signal to build a directional follow-up on. Only "independent generators,
not otherwise distinguished" remains uncontradicted by this test — consistent
with, and now statistically corroborating at a coarser positional-alignment
level, Phase 412's existing finding that independent per-stream symbol
profiles beat a shared profile, and Phase 371's structural finding that
neither stream's adjacent page instruction embeds the other's raw content.

This is **corroboration_only**. It does not select a generator model, does
not test a specific coupling operator (unlike Phases 271–321/451), does not
repeat or supersede Phase 412's distributional test, and per the frozen
protocol cannot reopen or close `G-YIN-001` or `G-ESC-001` under any
outcome. `G-YIN-001`'s own closure condition (a creator source, or a
structurally forced single reading not already ruled out by Phase 238,
selecting an operator) is unchanged. The item-1 tournament's five
directional/coupling branches are not authorized for execution by this
result; a genuinely new primary source or structurally forced reading would
still be required before any of them could proceed.

## Facts affected

None.

## Supersedes/corrects

None against prior phases. Corrects its own same-day protocol draft's
promotion rule before any real score was computed (see "Correction before
real scoring" above).

## Artifacts

- `doc/Brainstorms/2026-09-17 - Phase 518 Positional Cross-Stream Correspondence Gate Protocol.md`
  — frozen (and same-day corrected) pre-registration.
- `tools/gsmg/phase518_manifest.json` — pinned digests, seed, decision rule.
- `tools/gsmg/phase518_positional_cross_stream_correspondence_gate.py` —
  implementation, self-test, fixture controls.
- `tools/gsmg/test_phase518_positional_cross_stream_correspondence_gate.py`
  — 7 tests (~10s).
- `tools/gsmg/phase518_result.json` — full real-data result.

## Reopen condition

Only on a new primary source, recovered creator artifact, or structurally
forced reading that licenses a specific DBBI/FAED coupling operator or
generator relationship — not on re-running this or a similar undirected
statistical dependency test again. A different block feature, alignment, or
granularity family would need its own separately frozen protocol, not a
repeat of this one.
