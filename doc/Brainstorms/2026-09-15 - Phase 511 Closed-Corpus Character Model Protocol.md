# Phase 511 — closed-corpus character-model transfer protocol

Date: 2026-09-15

Status: frozen design; no FAED scoring is authorized by this phase.

## Question

Can character-order statistics learned only from independently authenticated
puzzle plaintext transfer to a held-out solved plaintext, and do they add
discrimination beyond the repository's generic English quadgram model?

Phase 510 showed that exact words are too sparse. Phase 511 tests the narrower
remaining idea: shared character transitions may transfer even when exact words
do not. This is a calibration experiment, not a claim that FAED is prose.

## Corpus and normalization

Reuse Phase 510A's byte-verified literal regions without adding material:

- Phase 2 solved plaintext;
- Phase 3 literal plaintext before its embedded ciphertext;
- Phase 3.2 literal regions outside its binary and embedded ciphertext;
- authenticated `CIAO BELLA O`.

Normalize each region independently to lowercase ASCII letters. Do not form
n-grams across source boundaries. For each of the three substantial texts,
hold it out and train on the other substantial texts plus `CIAO BELLA O`.

No findings prose, brainstorms, solver output, community material, recognition
terms, dictionaries, password lists, OCR, inferred word boundaries, or FAED
data enter this phase.

## Frozen model family

A pre-score structural scan found held-out coverage of 86.6–91.1% for observed
bigrams, 41.3–43.6% for observed trigrams, and only 12.8–17.9% for observed
four-grams. Therefore the frozen closed-corpus family is orders 2 and 3 only.
Unigrams are excluded because the null preserves their counts exactly;
four-grams and higher are excluded for sparsity.

For order `n`, use an order-`n-1` Markov model with add-one smoothing over the
26-letter next-character alphabet:

`P(x | context) = (count(context+x)+1)/(count(context)+26)`.

Score by mean base-10 log probability per observed n-gram. No interpolation,
weight tuning, backoff tuning, vocabulary bonus, or post-result model changes
are allowed.

## Controls and comparable family statistic

For each held-out text generate exactly 200 PCG32 Fisher–Yates shuffles of its
exact normalized letter multiset. Score the real text and every shuffle under:

- the held-out order-2 model;
- the held-out order-3 model;
- the frozen generic-English quadgram table.

Raw scores from different model orders are not comparable. For each scorer,
standardize all 201 sequences symmetrically using that scorer's population mean
and population standard deviation. The closed-corpus family statistic for each
sequence is the maximum of its order-2 and order-3 z-scores. Because the same
transform and family maximum are applied to the real sequence and every null,
model-order selection is inside the null comparison.

The generic comparator statistic is its standardized quadgram score. Ties are
exceedances.

## Frozen gates

Phase 511 promotes only if both gates pass on all three held-out texts:

1. **Transfer:** zero of 200 null family maxima reaches or exceeds the real
   closed-corpus family maximum.
2. **Incremental value:** the real closed-corpus family z-score exceeds the real
   generic-English z-score.

The second gate prevents an ordinary, weaker English model trained on too little
text from being relabelled as puzzle-specific signal. With only three authentic
held-out documents, even a pass is developmental evidence, not strong power.

## Stop rule and scope

If either gate fails on any fixture, stop. Do not score FAED and do not integrate
the model into a checkerboard or transposition solver. A pass licenses only a
separately frozen known-order pair/board identifiability ceiling. It does not
license a GPU search or an expensive real decode.

A negative closes only this exact order-2/3 add-one closed-corpus model. It does
not show that FAED is non-text, non-English, or outside Model B.
