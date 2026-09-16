# Phase 510A — closed-system vocabulary manifest protocol

Date: 2026-09-15
Status: frozen before vocabulary construction

## Purpose

Construct and measure a closed vocabulary for a possible FAED search
objective. This phase does not score FAED, build a search objective, fit a
checkerboard, or run a GPU solver.

## Eligible sources

1. Literal text regions from the three solved AES plaintexts verified and
   byte-for-byte re-encrypted by Phase 410.
2. The authenticated `CIAO BELLA O` page text recorded by Phase 468.
3. Exact solved preimage/output sequences are recorded separately as exact
   sequence controls, not silently split into guessed word boundaries.

For Phase 3, the following embedded Base64 ciphertext is excluded. For Phase
3.2, the known binary sub-block and final embedded Base64 ciphertext are
excluded using the already-recorded literal-region boundaries. Only literal
plaintext regions contribute words.

## Mechanical construction

- Extract maximal ASCII `[A-Za-z]+` runs.
- Lowercase them.
- Retain length at least 5.
- Deduplicate by exact normalized bytes.
- Record occurrence count and source-document membership.
- Precompute the proposed length weight `(length - 4)^2` but perform no
  matching or scoring in this phase.

If later used, matches must be selected by maximum-weight non-overlapping
intervals and normalized by decoded length. Phase 510B must freeze and test
that rule separately; this manifest does not authorize it automatically.

## Explicit exclusions

- findings and brainstorm prose;
- solver-generated FAED plaintexts;
- community suggestions and recognition-only terms;
- dictionaries, password lists, synonyms, stemming, typo repair, OCR, and
  fresh source harvesting;
- inferred word boundaries inside unspaced solved answers/preimages;
- Base58/hex syntax mixed into the letter vocabulary without a compatible
  representation rule.

## Gate reported by this phase

For each source document, report the fraction of its retained token
occurrences whose term occurs in at least one other eligible document. This is
a leave-one-document-out coverage diagnostic. Low coverage does not disprove
term reuse in FAED, but it prevents a same-corpus planted test from being
misrepresented as evidence that the vocabulary generalizes.

