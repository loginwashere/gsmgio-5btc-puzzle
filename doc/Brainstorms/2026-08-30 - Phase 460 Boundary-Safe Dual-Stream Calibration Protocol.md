---
type: hypothesis
phase: 460
date: 2026-08-30
status: frozen-before-real-scoring
topics: [calibration, dual-stream, DBBI, FAED, escape-pair, held-out]
---

# Phase 460 — Boundary-Safe Dual-Stream Calibration Protocol

## Correction motivating this version

Phase 459 split raw streams at positions `45|46` and `285|285` before
tokenization. Escape-code units can cross those arbitrary cuts. Its
right-to-left FAED `{g,i}` validation ended on an apparent dangling escape only
because the escape's consumed symbol was placed in the training half. The
frozen loss `1.0` therefore measured split misalignment, not held-out failure.
Phase 459 is `protocol_invalid` for inference; its reproducible output remains
an audit artifact and is not repaired in place.

## Question and fixed procedure

Does per-stream escape-pair specialization improve held-out code-IC prediction
over one shared pair after respecting each candidate tokenizer's own complete
code boundaries?

For every unordered pair in all `C(9,2)=36` pairs:

1. tokenize each complete authenticated stream; a pair that cannot segment the
   complete stream is ineligible for that stream;
2. split the resulting complete token sequence at `floor(token_count/2)`;
3. fit shared and independent pair models on the left token halves and score
   only right token halves, then reverse direction;
4. use equal-stream absolute IC distance from the fixed `0.067` reference;
5. report the mean contrast `shared held loss - independent held loss`.

Token counts and split positions vary mechanically with the candidate pair.
They are not optimized. All equal-best training ties are retained; the
lexicographically first pair supplies deterministic held-out scoring.

## Nulls, inference, and controls

Use the same two preservation families as Phase 459, but rerun the corrected
token-first scorer inside every replicate:

- 20,000 independent randomized Euler traversals preserving exact directed
  bigram multigraphs, lengths, unigrams, endpoints, self-transitions/runs and
  lag-1 structure;
- 20,000 endpoint-fixed interior shuffles preserving lengths, exact unigrams,
  endpoints and evaluation direction.

Master seed: `46020260830`. One-sided plus-one high-tail p-values. Decision is
`robust_specialization` only for positive contrast and `p<=0.005` under both;
one passing null is `null_sensitive`; otherwise
`no_calibrated_specialization`. The two nulls are an intersection rule, not two
promotion opportunities.

Controls must verify: manifest/source/precedent digests; Phase 106 tokenization
and IC; all 36 pairs/ties; exact null invariants and determinism; planted shared
and specialized fixtures; complete-stream invalid-pair exclusion; and a
boundary-crossing fixture proving an escape at the token-half neighborhood is
kept with its consumed symbol rather than declared dangling.

Null populations complete before the real score. No feature, pair, score,
split, null, seed, or trial count changes afterward. Maximum inference is
`corroboration_only`: no pair/role selection, plaintext, password, oracle, or
gap closure. Phase 412 remains the stronger emission-profile comparison.

