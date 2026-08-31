---
type: hypothesis
phase: 459
date: 2026-08-30
status: frozen-before-real-scoring
topics:
  - calibration
  - dual-stream
  - DBBI
  - FAED
  - escape-pair
  - held-out
---

# Phase 459 — Dual-Stream Escape-Pair Calibration Protocol

## Question

When the complete 36-pair escape-tokenization procedure is fit on one half of
DBBI/FAED and evaluated only on the opposite half, do separately selected
per-stream pairs generalize better than one shared pair by more than matched
surrogate streams ordinarily permit?

This is extension D of Phase 453's false-discovery harness and the prerequisite
calibration for the portfolio's later two-role escape-pair experiment. It does
not test any plaintext alphabet, topology, decoder, consumer, password, or
cryptographic oracle. A positive result is `corroboration_only`; it cannot
select `{g,i}` or `{h,e}` or close `G-ESC-001`/`G-YIN-001`.

## Frozen inputs and universe

- authenticated raw streams: DBBI (91 symbols) and FAED (570 symbols), exact
  SHA-256 values pinned in `phase459_dual_stream_manifest.json`;
- alphabet: literal `abcdefghi`;
- candidate universe: all `C(9,2) = 36` unordered escape pairs, lexicographic;
- tokenization: a non-escape is a one-symbol code; an escape consumes itself
  plus the next raw symbol; a final dangling escape makes that pair invalid;
- statistic: token-stream index of coincidence, compared to the historically
  fixed `0.067` ordinary-English reference used by Phase 106/112/449;
- two fixed contiguous halves per stream: `DBBI 45|46`, `FAED 285|285`;
- both directions: left trains/right validates and right trains/left validates.

No period, alphabet completion, checkerboard layout, pair order, output text,
or semantic target is admitted.

## Competing models and held-out score

For each direction:

1. `SHARED`: choose one of all 36 pairs minimizing the equal-stream mean
   absolute training IC distance from `0.067`.
2. `INDEPENDENT`: choose one pair for DBBI and one for FAED, each minimizing
   its own training IC distance.
3. Freeze the selected pair(s), apply them to the untouched validation halves,
   and compute equal-stream mean absolute IC distance. A pair invalid on its
   validation half receives loss `1.0`; ties are retained in diagnostics and
   resolved lexicographically only to make replay deterministic.

The sole inferential statistic is:

```text
contrast = mean_direction(SHARED held-out loss - INDEPENDENT held-out loss)
```

A positive contrast favors per-stream specialization. Full-data `{b,e}`/
`{g,i}` ranks, fold-selected pair identities, tie counts, and the standing
`{h,e}` rival are diagnostics only and cannot change the statistic.

## Matched nulls

Exactly 20,000 paired replicates per null, master seed `45920260830`.

### Primary: exact directed-transition Euler surrogates

For each stream independently, randomize an Euler traversal of the directed
multigraph formed by its adjacent-symbol edges while fixing its first symbol.
Every accepted surrogate must preserve exactly:

- length and alphabet;
- complete unigram counts;
- all 81 directed bigram counts;
- first and last symbols;
- self-transition count and therefore all length-2 runs;
- every lag-1 statistic induced by any fixed numeric symbol mapping; and
- the fixed 45|46 and 285|285 evaluation boundaries.

This null destroys placement of the preserved transitions across halves and
higher-order ordering. Duplicate traversals remain valid draws; changing the
seed or trial count after observing the real statistic is prohibited.

### Sensitivity: endpoint-fixed exact-multiset shuffles

Independently shuffle each stream's interior symbols while fixing its first and
last symbols. This exactly preserves length, full unigram counts, endpoints,
and evaluation boundaries, but intentionally destroys transition/run and
autocorrelation structure. It asks whether the decision depends on the
stricter local-structure conditioning.

Token distributions are outputs of the 36 disputed hypotheses and therefore
cannot all be fixed without preserving the object being tested. Instead, the
complete pair search is repeated inside every real and null score.

## Inference and controls

Use the plus-one one-sided empirical probability
`(1 + count(null contrast >= real contrast)) / 20001`. There is one frozen
inferential contrast. The two nulls are not two chances to promote: the result
is `robust_specialization` only if the contrast is positive and `p <= 0.005`
under both. One passing null is `null_sensitive`; neither is
`no_calibrated_specialization`.

Required pre-interpretation controls:

1. tokenization and IC agree with the established Phase 106 implementation;
2. all 36 pairs are enumerated and every equal-best training tie is retained;
3. Euler surrogates preserve exact unigrams, bigrams, endpoints, runs and
   length; sensitivity surrogates preserve their declared invariants;
4. deterministic replay under the frozen seed;
5. a planted shared-pair fixture does not manufacture specialization;
6. a planted two-pair fixture yields a positive held-out specialization
   contrast; and
7. a deliberately dangling validation escape receives the frozen loss `1.0`.

Any failed control yields `harness_failure` and bars interpretation.

## Stop and interpretation rules

- Null populations complete before the real contrast is computed.
- No new feature, split, pair family, null, direction, score, or control may be
  added after viewing the real result.
- No plaintext generation, password/key material, blob/address oracle, GPU,
  Docker, network, or external agent.
- Phase 412 remains the stronger existing test of shared versus independent
  emission profiles; Phase 459 asks the narrower escape-tokenizer
  generalization question and must not be presented as independent source
  evidence.
- BTCSEED is the standing negative control on interpretation: reproducibility
  and a local checkpoint do not authenticate a selector.
- `G-ESC-001` and `G-YIN-001` closure conditions and priorities remain
  unchanged under every possible Phase 459 result.

## Planned artifacts

```text
tools/gsmg/phase459_dual_stream_manifest.json
tools/gsmg/phase459_dual_stream_escape_pair_calibration.py
tools/gsmg/test_phase459_dual_stream_escape_pair_calibration.py
tools/gsmg/phase459_result.json
doc/GSMG_P459_DUAL_STREAM_ESCAPE_PAIR_CALIBRATION.md
tools/gsmg/findings/P00459.md
```

