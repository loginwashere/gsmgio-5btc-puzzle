# Phase 510B — held-out vocabulary signal protocol

Date: 2026-09-15
Status: frozen before scoring

## Question

Before checkerboard or transposition work, can the Phase-510A exact vocabulary
recognize an eligible solved plaintext when that plaintext's own document is
excluded from vocabulary construction?

## Frozen method

- Fixtures: the Phase 2, Phase 3, and Phase 3.2 literal plaintext regions in
  the Phase-510A manifest. `CIAO BELLA O` is vocabulary input but is too short
  to be an evaluation fixture under the five-letter minimum.
- For each held-out fixture, retain every manifest term occurring in at least
  one *other* source document.
- Normalize the fixture to lowercase ASCII letters only.
- Find the maximum-weight set of non-overlapping exact term occurrences by
  dynamic programming. Term weight is the manifest's frozen `(length-4)^2`.
- Normalize total weight by plaintext length and report matched-character
  coverage.
- Gate A: at least 5% of normalized plaintext characters must be covered by
  selected matches. If any fixture fails, stop without null trials.
- Gate B, conditional on Gate A: compare each real score with 200 PCG32
  Fisher-Yates shuffles of that fixture's exact letter multiset. Ties are
  exceedances. Every fixture must have 0/200 exceedances.

The scorer must pass both gates on all three held-out documents. Failure stops
the exact-vocabulary objective before pair/board identifiability, FAED scoring,
or GPU integration. Passing would only license the next known-order ceiling;
it would not license a real FAED run.

