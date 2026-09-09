# Phase 484B powered small-width raw-symbol VIC audit

Date: 2026-09-07

## Outcome

No solve. The locked real FAED search over the Phase-484A-powered widths
2, 3, 5, and 6 found no coherent plaintext and did not reach the frozen
synthetic-score trigger.

The family maximum was `-5.209997256189395` per quadgram window, at width 5,
escape pair `{a,b}`, spectral rank 1,208. The weakest winning score among the
80 locked Phase 484A holdout fixtures was `-4.571151156706407`; the real
maximum is 0.6388461 lower. Its plaintext and every other retained output are
gibberish.

Disposition: `no_powered_family_solve_no_calibrated_null_claim`.

## Powered basis

Phase 484A froze and passed an 80-fixture blind synthetic holdout: 10/10 in
each width/pool cell, 80/80 exact pair/order recoveries, minimum plaintext
accuracy 0.9908, and minimum board accuracy 0.84. This demonstrated that the
locked 1,536-hypothesis shortlist plus board solver can recover the planted
construction at these widths without being supplied the escape pair.

## Locked real family

- FAED: 570 ASCII symbols, SHA-256
  `066191b4aafc114fbca7f0d168382f40129c4ff18490375b689741081d5ef3c2`.
- Widths: 2, 3, 5, 6.
- Escape pairs: all 36 unordered pairs over `a` through `i`.
- First 1,536 valid pair/order hypotheses per width under the frozen spectral
  statistic.
- Two 6,000-proposal board anneals per hypothesis, `T 20 -> 1`.
- Selection: maximum normalized 25-letter quadgram score.
- Output: ten candidates per width and one family maximum.

| Width | Pair | Score per window | Decoded length | Readability |
|---:|---|---:|---:|---|
| 2 | `{b,d}` | -5.291062 | 487 | gibberish |
| 3 | `{c,f}` | -5.219916 | 477 | gibberish |
| 5 | `{a,b}` | -5.209997 | 485 | gibberish |
| 6 | `{c,i}` | -5.304953 | 463 | gibberish |

The best output begins:
`TSIIKDTNNIISIERISHEIHAEAMEITSESISAIERRTARSERUARKRYNIERNENEGREIVI...`
This has local English-looking fragments produced by quadgram optimization
but no coherent words, syntax, or message. Inspection of all 40 retained
candidates found no readable outlier.

## Verification

The verifier passed after the one real run. It checked the pinned inputs and
implementation hashes, exact width family, hypothesis totals, ten sorted
candidates per width, pair/index mappings, plaintext lengths, normalized
scores, family maximum, and frozen trigger/disposition mapping.

- Execution lock SHA-256:
  `9171522dc907e758d7fac1790d6509719529b35fc4b344ef54161be53da5c71c`
- Result SHA-256:
  `059bed33951da5c70c7334d98837152c3807afd4cef2dd5f52f6c78770d4d6e9`

## Limits

This is a bounded no-solve result, not a family-wide statistical negative.
No raw-symbol-shuffle null was run, so the real score has no multiplicity-
calibrated p-value. The test retires the powered small-width search as a
practical solution path under its frozen model; it does not cover widths
7--40, disrupted/double transposition, another language model, or another
checkerboard topology.
