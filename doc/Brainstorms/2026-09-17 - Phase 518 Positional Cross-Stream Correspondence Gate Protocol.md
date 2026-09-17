---
type: hypothesis
phase: 518
date: 2026-09-17
status: frozen-before-real-scoring
topics:
  - calibration
  - dual-stream
  - DBBI
  - FAED
  - mutual-information
  - held-out
  - G-YIN-001
---

# Phase 518 — Positional Cross-Stream Correspondence Gate Protocol

## Question

The Post-Phase-452 Portfolio's item 1 ("asymmetric DBBI/FAED generator
tournament") proposes a closed six-way tournament between independent
generators, a shared-latent-alphabet model, DBBI-parameterizes-FAED,
FAED-parameterizes-DBBI, alternating control/data channels, and a common
source through two encoders. Before that six-way tournament can be built,
it needs a single prior gate: is there **any** detectable positional
correspondence between DBBI and FAED at all, beyond what each stream's own
internal structure already explains? If this gate does not promote, none of
the five non-independent branches has anything to be built on, and the
tournament collapses to "independent generators, not otherwise
distinguished" without needing five separate directional constructions.

This is explicitly **not** a new cross-stream coupling operator in the sense
of Phases 271–321's ~50 tested ciphers/transforms (which each asked "does
operator X decode one stream from the other"). It is a pure statistical
dependency test — no operator is proposed, no plaintext, password, or key
material is generated, and no AES oracle or English-language score is used.
Per the portfolio's own scoping and per `G-YIN-001`'s registry disposition,
**any outcome of this phase is corroboration_only and cannot reopen or close
`G-YIN-001`, select an operator, or supersede Phases 271–321, 371, 412, or
451.** `G-YIN-001`'s own closure condition ("a creator source, or a
structurally forced single reading not already ruled out by Phase 238,
selects an operator") is unchanged regardless of result.

## Frozen inputs and universe

- authenticated raw streams: `DBBI` (91 symbols) and `FAED` (570 symbols),
  alphabet `abcdefghi`. Pinned digests in
  `tools/gsmg/phase518_manifest.json`:
  - `DBBI` SHA-256 `71fe46259e270c113529dfaded4b59c59a9dffd826a7202ab07fc498b6a2c5ca`
  - `FAED` SHA-256 `066191b4aafc114fbca7f0d168382f40129c4ff18490375b689741081d5ef3c2`
- two frozen granularities, both DBBI-native factors of 91:
  - primary `K=91` (block size 1 on DBBI; each raw DBBI symbol is its own
    block);
  - secondary `K=13` (block size 7 on DBBI, an exact division of 91).
- for each `K`, both streams are partitioned into `K` contiguous blocks by
  proportional position: block `j` of a length-`N` stream covers indices
  `[floor(j*N/K), floor((j+1)*N/K))`. This gives DBBI exact equal-size blocks
  at both `K` values and gives FAED near-equal blocks (`570/91 ≈ 6.26`,
  `570/13 ≈ 43.8`).
- block feature: the block's mode symbol (the most frequent raw symbol in
  that block; ties broken by fixed alphabetical order `a<b<...<i`). At
  `K=91` this reduces DBBI's feature to its own raw symbol at that position.
- statistic: plug-in mutual information (bits) between the `K` paired
  `(DBBI_block_mode, FAED_block_mode)` values, using the existing validated
  `mutual_information()` implementation in
  `tools/gsmg/dbbi_faed_base81_token_audit.py` (already self-tested to rank
  a planted-dependent pair set above an independent one). No smoothing or
  bias correction is applied to the observed statistic; the same uncorrected
  estimator is applied identically inside every null replicate, so small-
  sample bias cancels in the empirical comparison.
- this statistic is symmetric (`I(X;Y) = I(Y;X)`); it detects *any*
  positional correspondence, not a specific direction. It cannot by itself
  discriminate DBBI-parameterizes-FAED from FAED-parameterizes-DBBI from a
  common-source model — that discrimination is explicitly out of scope and
  deferred to a follow-up phase only if this gate promotes.

No period, alphabet completion, checkerboard layout, escape-pair selection,
output text, or semantic target is admitted.

## Matched nulls

Exactly 20,000 paired replicates per null, master seed `51820260917`
(`518` concatenated with the frozen date `20260917`).

### Primary: exact directed-transition Euler surrogates

Reuse `euler_surrogate()` from
`tools/gsmg/phase459_dual_stream_escape_pair_calibration.py` unmodified,
applied **independently** to DBBI and FAED (separate RNG draws, so any real
cross-stream alignment is destroyed while each stream's own structure is
kept). Each surrogate preserves exactly: length, alphabet, complete unigram
counts, all directed bigram counts, first/last symbol, self-transition count
(hence length-2 runs), and every lag-1 statistic. This is the "runs and
autocorrelation" preservation the portfolio doc requires.

### Sensitivity: endpoint-fixed exact-multiset shuffles

Reuse `endpoint_fixed_shuffle()` from the same module, again applied
independently to each stream. Preserves length, exact unigram counts, and
endpoints only; deliberately destroys transition/run structure. Asks whether
the decision depends on the stricter local-structure conditioning.

## Decision rule

For each `K`, compute the one-sided plus-one empirical probability
`(1 + count(null MI >= observed MI)) / 20001` under each null. Mirroring
Phase 460's rule:

- `robust_correspondence` at a given `K` requires observed MI greater than
  both null medians and `p <= 0.005` under **both** nulls;
- `null_sensitive` if exactly one null passes;
- `no_calibrated_correspondence` otherwise.

The phase-level decision is `robust_correspondence` only if **both** `K=91`
and `K=13` independently reach `robust_correspondence`. Any lesser outcome
at either `K` yields `no_calibrated_correspondence` (or `null_sensitive` if
one `K` is null-sensitive and the other passes) as the phase-level result.
`K=13` is a full second gate, not a diagnostic-only sensitivity check —
matching the conservative "AND across granularities" bar already established
by requiring both nulls to agree.

## Required pre-interpretation controls

1. `mutual_information()` reproduces its existing self-test (planted
   dependent pairs score higher than independent pairs).
2. Euler surrogates preserve exact unigrams/bigrams/endpoints/runs/length;
   endpoint-fixed shuffles preserve their declared weaker invariants
   (reusing `assert_primary_preservation` / `assert_sensitivity_preservation`
   from `phase459_dual_stream_escape_pair_calibration.py`).
3. Deterministic replay under the frozen seed.
4. An **independent-fixture negative control**: two synthetic streams of
   matching lengths (91, 570) and matching per-symbol marginal weights but
   built with independent RNG state and no positional relationship — the
   phase-level decision on this fixture must be `no_calibrated_correspondence`.
5. A **planted-correspondence positive control**: a synthetic DBBI-like
   91-symbol stream and a synthetic FAED-like 570-symbol stream built by
   deterministically expanding each DBBI-fixture symbol into its
   proportional FAED-fixture block (so a real positional correspondence
   exists by construction) — the phase-level decision on this fixture must
   reach `robust_correspondence` at both `K` values, demonstrating the test
   has power to detect the exact class of relationship it is built to find.
6. Block-partition determinism: the `[floor(j*N/K), floor((j+1)*N/K))`
   boundaries tile each stream exactly with no gap or overlap, at both `K`
   values, for both stream lengths.

Any failed control yields `harness_failure` and bars interpretation.

## Stop and interpretation rules

- Null populations complete before the real statistic is computed.
- No new granularity, feature, null, or control may be added after viewing
  the real result.
- No plaintext generation, password/key material, blob/address oracle, GPU,
  Docker, network, or external agent.
- Phase 412 remains the existing test of shared-vs-independent marginal and
  first-order Markov structure (symmetric, whole-stream); this phase asks a
  narrower positional-alignment question at coarse granularity and must not
  be presented as superseding or repeating Phase 412.
- Phases 271–321 and 451 remain the existing tests of specific coupling
  operators/constructions; this phase asks whether *any* undirected
  statistical correspondence survives matched nulls, not whether a specific
  operator decodes one stream from the other, and must not be presented as
  repeating or superseding them.
- `G-YIN-001` and `G-ESC-001` closure conditions and priorities remain
  unchanged under every possible Phase 518 result, promote or not.
- A promotion at this gate authorizes, at most, scoping a follow-up
  directional-discrimination phase (distinguishing H3/H4/H5/H6 from each
  other) as a separate, separately frozen protocol. It does not itself
  authorize that follow-up's execution.

## Planned artifacts

```text
tools/gsmg/phase518_manifest.json
tools/gsmg/phase518_positional_cross_stream_correspondence_gate.py
tools/gsmg/test_phase518_positional_cross_stream_correspondence_gate.py
tools/gsmg/phase518_result.json
doc/GSMG_PHASE518_POSITIONAL_CROSS_STREAM_CORRESPONDENCE_GATE_AUDIT.md
tools/gsmg/findings/P00518.md
```
