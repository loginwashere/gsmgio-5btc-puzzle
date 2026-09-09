---
type: protocol
phase: 482
date: 2026-09-06
status: frozen-before-real-scan
topics:
  - faed
  - plaintext-identification
  - frequency-signature
  - closed-system
---

# Phase 482A — FAED plaintext frequency-signature protocol

## Question

Is the 436-symbol plaintext implied by FAED's `{g,i}` checkerboard
segmentation a verbatim passage in a closed corpus already present in this
project?

Under Phase 477A's Model A, a monoalphabetic board only renames symbols and a
transposition only reorders them. Both operations preserve the complete
multiset of symbol counts. An exact plaintext passage must therefore have the
same sorted frequency signature as the 25 FAED code types. This is a necessary
condition independent of the unknown board, width, direction and column order.

## Frozen FAED object

Segment `data.FAED` once with ordered escapes `g,i`, using
`checkerboard_code_ic_oracle.segment_codes`. The assertions are:

```text
raw symbols: 570
tokens:      436
types:        25
signature:   54,45,45,42,40,38,38,21,11,10,10,10,9,8,8,7,6,5,5,5,5,4,4,4,2
```

The signature sorts counts descending and discards token names. No other
escape pair is tested in this phase.

## Frozen closed corpus

Every source is an existing local project artifact. Documents remain separate;
no window may cross a source boundary.

### Puzzle-native tier

1. Solved Phase-2 plaintext, freshly decrypted from the pinned authenticated
   Wayback textarea with its established password and profile.
2. Solved Phase-3 plaintext, derived the same way.
3. Solved Phase-3.2 plaintext up to, but excluding, the trailing P32 encrypted
   envelope. The Base64/encoded material inside that plaintext remains because
   it is literally part of the solved creator-authored plaintext.
4. The independently decoded Phase-3.2.1 Architect answer, freshly reproduced
   through the existing CP1141/Beaufort path.

### Referenced-text tier

5. The locally stored 1,326-word Matrix screenplay scene from "I am the
   Architect" through "the problem is choice". Its leading provenance comment
   is metadata and is excluded.

### Book tier

6. The existing local *Cosmic Duality* full-text transcription, using the
   exact prose-section exclusions already frozen by Phase 477A: front matter,
   contents, index, acknowledgments, colophon, back matter and transcription
   metadata are excluded.

Telegram/chat text, project analysis documents, password dictionaries, generic
wordlists, newly produced OCR and the unresolved ciphertext strings are outside
the corpus. The book tier is a verbatim-plaintext screen, not a password-list
construction, and is reported separately from the stronger puzzle-native tier.

Before the real scan, the execution lock records each source's provenance tier,
raw source dependencies, normalized length, and normalized-content SHA-256.

## Frozen normalization lanes

Each logical document is converted to uppercase ASCII `A..Z`, deleting every
other byte without inserting separators.

1. `ji_merged` (primary): replace `J` with `I`, matching Phase 477A's classical
   25-letter convention.
2. `raw_az_25_present` (secondary): retain A..Z unchanged. A window can match
   only if its count signature already has exactly 25 positive classes, so one
   ordinary letter is naturally absent. No letter is deleted or substituted to
   force that condition.

Every contiguous 436-symbol window is tested in each lane. Reversal and
transposition variants are unnecessary because they preserve the signature.
There are no circular windows, line-local restarts, case variants, spaces as
symbols, other letter merges, approximate spellings or edit-distance matches.

## Matcher and controls

The matcher maintains a rolling 26-bin count vector and compares its sorted
positive counts to the frozen FAED signature. Before the lock it must prove:

- exact FAED token count, type count and signature;
- source extraction and normalized-content hashes are deterministic;
- rolling signatures equal a simple brute-force count at the first, middle and
  last windows of every eligible source/lane;
- deterministic relabeling and permutation preserve a planted passage's
  signature;
- source boundaries cannot be crossed;
- the two normalization lanes differ on a J-bearing fixture and agree where no
  J occurs.

For context, report per source/lane: window count, distinct-signature count,
number of signatures occurring more than once, and maximum signature
multiplicity. These are descriptive collision diagnostics, not a p-value.

## Decision and stop rule

Only complete equality of all 25 sorted counts is a match. A nearest signature,
partial count agreement or manually edited passage is not a candidate.

- Zero exact matches: bounded negative for a verbatim 436-symbol passage in the
  frozen corpus under the two normalization lanes. Phase 482B does not run.
- One or more exact matches: retain every unique normalized passage with every
  provenance location, freeze them, and start Phase 482B as a separate exact
  equality-pattern/board/transposition reconstruction. No language-score
  ranking chooses among matches.

An exact signature match alone is not a solve. Phase 482B must reproduce all
436 token/letter equality relations and re-encode to the exact FAED raw stream.

## Limits

A negative does not reject Model A generally. It excludes only verbatim
passages from these sources. Constructed prose, abbreviations, spelling edits,
spaces or punctuation as encoded symbols, other alphabet conventions,
non-English material, and Model B's post-checkerboard raw-digit transposition
remain outside this phase.
