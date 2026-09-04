---
type: preregistration
status: frozen
date: 2026-09-02
phase: 474
topics:
  - selected-31
  - anagram
  - exact-cover
  - lexical-calibration
---

# Phase 474 — Selected-31 Exact-Cover Anagram Protocol

## Question

Does the exact multiset of `ncsyangcahiriasogaleafayanestve` admit an
unusually compact full-word decomposition under an independent frozen
lexicon, and what bounded exact-cover bags are available under the broader
pre-existing puzzle/chat vocabulary?

This closes the reproducibility gap left by the historical report of a few
trillion unsuccessful raw permutations. It does not treat arbitrary word
ordering as evidence and does not test any output as a password.

## Frozen inputs

- Target: `ncsyangcahiriasogaleafayanestve`, cross-checked against
  `denis_prime_extraction_audit.TARGET`.
- Source for controls: canonical 91-character `VALIDATION_ANSWER` from
  `tools/gsmg/data.py`.
- Independent lexicon: `wordlists/bip39/english.txt`, plus only the two
  grammatical one-letter words `a` and `i`.
- Discovery lexicon: the independent tier plus lines of
  `wordlists/gsmg/chat_mined_words.txt` that, after whitespace stripping and
  lowercasing, match `[a-z]{3,12}` exactly.
- The discovery lexicon is explicitly contaminated: it was mined from the
  discussion that contains the historical anagram attempts. It can inventory
  decompositions but cannot confirm them.

## Frozen exact-cover grammar

- Ignore spaces and case; consume all 31 letters exactly once.
- A solution is an unordered multiset (bag) of 1–8 lexicon words.
- Words may repeat when the target has enough letters.
- No proper-name additions, inflections, spelling repairs, abbreviations,
  phonetics, substitutions, deletions, or unused letters.
- The literal 31-character target is forbidden as a lexicon word.
- The decision-bearing score is the exact minimum number of independent-tier
  words needed for a full cover, or infinity if no cover of at most eight
  words exists.
- Up to 200 distinct minimum-cardinality bags are serialized, ordered
  lexicographically. This is a bounded inventory, not a claim that word order
  or sentence grammar selects one bag.
- The four already-recorded manual phrases are checked only for exact letters
  and discovery-lexicon coverage. They are historical positive controls, not
  discoveries.

The solver uses memoized exact multiset subtraction. At every state it chooses
the remaining letter having the fewest currently fitting words, then branches
over every fitting word containing that letter. This is an exact recurrence
for minimum cover cardinality; solution bags are canonicalized and deduplicated.

## Frozen calibration

- NumPy `default_rng(474)`.
- 200 controls, each a uniformly sampled set of 31 distinct positions from
  the same 91-character plaintext. Positions are sorted only to construct a
  reproducible control string; order is irrelevant to the anagram statistic.
- Each control is evaluated from scratch under the same independent lexicon,
  eight-word cap, and exact solver.
- Lower minimum cover cardinality is better; infinity is worse than every
  finite score.
- One-sided plus-one p-value:

```text
p = (1 + count(control_min_words <= target_min_words)) / 201
```

## Decision rule

An independent lexical-compressibility lead requires all of:

1. an independent-tier exact cover in at most eight words;
2. `p < 0.005` against the complete 200-control family;
3. the target score is strictly better than every control score;
4. all input hashes, multiset checks, exact-cover checks, and synthetic solver
   tests pass.

Even if all gates pass, the result selects only unusual independent-lexicon
compressibility. It does not select a phrase or ordering. Discovery-tier bags
never participate in promotion.

## Stop rule

- One decision-bearing execution after protocol/script/input hashing and lock.
- No lexicon changes, word-length changes, score changes, control changes,
  semantic reranking, or phrase ordering after output inspection.
- No passwords, hashes, decryptions, Bitcoin checks, FAED transforms, or
  oracle calls.
- Any semantic or language-model reranking requires a new preregistration and
  a genuinely independent scoring resource.
