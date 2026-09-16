# Phase 511 closed-corpus character-signal audit

Date: 2026-09-15

## Outcome

The closed puzzle corpus contains transferable character-order signal, but it
does not improve on the existing generic-English quadgram model. Phase 511
therefore stops before FAED and before any checkerboard or GPU integration.

| held-out plaintext | bigram coverage | trigram coverage | closed-corpus family z | generic quadgram z | null exceedances | incremental gate |
|---|---:|---:|---:|---:|---:|---|
| Phase 2 | 91.1162% | 42.9224% | 11.6464 | 12.0773 | 0/200 | fail |
| Phase 3 | 89.8687% | 43.6090% | 11.8185 | 12.0868 | 0/200 | fail |
| Phase 3.2 | 86.5639% | 41.2804% | 11.5816 | 12.3502 | 0/200 | fail |

The order-2/3 family beat every exact-letter-multiset shuffle for all three
authentic held-out texts. That establishes ordinary sequential-language
transfer. However, the generic quadgram comparator had a larger standardized
real-versus-null separation on all three fixtures. The frozen conjunctive gate
therefore failed 0/3 on incremental value even though transfer passed 3/3.

## Method

The phase reused only Phase 510A's byte-verified literal regions. Each substantial
solved plaintext was held out in turn; the other texts plus authenticated `CIAO
BELLA O` trained add-one-smoothed conditional bigram and trigram models. Source
boundaries were kept separate. A pre-score sparsity scan excluded unigrams,
which are invariant under the null, and four-grams, whose held-out observed
coverage was only 12.8–17.9%.

For each fixture, the real text and 200 PCG32 shuffles of its exact letter
multiset were scored by both closed-corpus models and the frozen generic-English
quadgram table. Each scorer was standardized symmetrically over its 201-member
ensemble. The closed-corpus statistic was the maximum order-2/order-3 z-score,
placing model selection inside every null comparison.

## Interpretation

This result distinguishes two ideas that would otherwise be easy to conflate:

- the tiny corpus can recognize that authentic texts have non-random character
  order;
- it cannot show a puzzle-specific advantage beyond an ordinary English model.

Adding this model to the FAED solver would therefore add correlated Englishness,
not demonstrated closed-system information. It would not repair the objective
mismatch exposed by Phases 433 and 508.

## Disposition and limits

Do not score FAED with this model and do not build a character-model GPU lane.
The negative is bounded to the frozen add-one order-2/3 family and three
held-out documents. It does not establish that FAED is non-English or non-text,
and it does not close all possible structural objectives.

The useful direction change is away from inventing another prose score. Future
work should target a mechanically distinct observable of Model B—one that can
be calibrated against real-vs-null data before it selects expensive runs—or
test a different plaintext class with its own exact consumer rather than
optimizing fluent English again.

## Verification

The verifier rebuilt all three models from the pinned literal regions,
regenerated all 600 shuffles, recomputed every raw score and standardized family
statistic, and reproduced the result exactly.

- Execution-lock SHA-256:
  `764e6d7282350ac70dd837df6c7d35a93abddb0719a40213fcc9e6fc72b7a328`
- Result SHA-256:
  `46c1c6ba16cec24ab5ec08f7e5edd11613d6011ee260e8897f749b3fc8373f22`
