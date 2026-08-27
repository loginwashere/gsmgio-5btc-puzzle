# Phase 425 — BTCSEED Family-Wide Significance Audit Pre-Registration

## Question

Does Phase 386's exact `BTCSEED` prefix remain unusual after correcting for a
bounded family of page-local Bifid keyword sources, block schedules, and common
orientation conventions, rather than evaluating only the configuration in
which the prefix was first noticed?

This is a significance audit of an existing checkpoint. It is not a search for
a new plaintext, password, or blob key.

## Frozen inputs

- ciphertext: authenticated 570-letter `FAED`;
- target: exact uppercase `BTCSEED`, fixed at seven letters;
- Bifid alphabet: the standard 25-letter alphabet with `J` folded into `I`;
- Bifid primitives: the round-trip-verified Phase 408 implementation;
- null: exact-multiset shuffles of `FAED`, using one fixed RNG seed;
- no cipher oracle calls.

## Keyword-source family

Only literal, page-local objects with a direct structural relationship to the
two SalPhaseIon textareas are eligible:

1. `DBBI`;
2. `FAED`;
3. `matrixsumlist`;
4. `lastwordsbeforearchichoice`;
5. `thispassword`;
6. `enter`;
7. `sha256 our first hint is your last command`;
8. `sha256 + unresolved literal anstoo`;
9. `SalPhaseIon`;
10. `Cosmic Duality`.

For every source, two keyword scopes are declared: its first 13 normalized
letters and all normalized letters. Identical keyed squares are deduplicated
before evaluation. No word found in an output may become a new keyword.

The authenticated Phase-3.2.2 validation answer is excluded: it is not
page-local and its two scopes were already closed separately by Phase 419.

## Convention family

Every distinct keyed square is evaluated under the Cartesian product of:

- Phase 408's eight schedules: periods `7`, `13`, `49`, `91`, `98`, `472`,
  `570`, plus the custom `[98,472]` split;
- operation: Bifid decrypt or its proven encryption inverse;
- coordinate-stream order: row-then-column (`rc`) or column-then-row (`cr`);
- ciphertext orientation: forward or reversed;
- decoded-output orientation: forward or reversed.

Semantically duplicate configurations, if any, remain in the manifest but are
deduplicated by their complete decoded output before family-level counts are
reported. The primary family correction uses distinct outputs.

## Observed statistics

For every distinct output:

- longest common prefix with exact `BTCSEED`;
- exact `BTCSEED` at the prefix;
- exact `BTCSEED` anywhere in the 570-letter output;
- output SHA-256 and first 32 characters.

The family-level statistics are the maximum prefix length, the number of exact
prefix hits, and the number of anywhere hits. The original Phase 386
configuration must be reproduced byte-for-byte as a regression gate.

## Matched null

Run 10,000 deterministic exact-multiset shuffles of `FAED`. For each shuffle,
apply the complete frozen family and retain the family-maximum prefix length
against `BTCSEED`. Report the add-one empirical tail probability

`p = (1 + count(null_max >= observed_max)) / (trials + 1)`.

Also report the null histogram of maximum prefix lengths. A planted positive
must prove that the prefix detector and family maximum can recover an exact
seven-letter target.

The primary null statistic is prefix-only. Anywhere hits are descriptive,
because scanning 570 overlapping windows adds a different multiplicity layer
and Phase 386's claim specifically concerns the prefix.

## Gates and interpretation

- **Family-corrected positive:** observed maximum is seven and empirical
  `p <= 0.01`.
- **Suggestive only:** observed maximum is seven and `0.01 < p <= 0.05`.
- **Not exceptional:** `p > 0.05`, or a null maximum commonly reaches seven.
- **Regression failure:** the original Phase 386 output is not reproduced;
  no inference is permitted.

Even a family-corrected positive is only evidence for the checkpoint. It does
not promote the 563-character continuation, `KMODEST`, a password, or a FAED
decoder. Advancement still requires independent held-out structure.

## Exclusions

- arbitrary dictionary-derived or output-derived keywords;
- arbitrary keyed-square permutations or reversed alphabets;
- periods outside the eight Phase 408 schedules;
- second cipher passes, autokeys, transpositions, or language-model tuning;
- password generation, Bitcoin derivation, or AES/blob oracle calls;
- semantic variants of `BTCSEED`.

