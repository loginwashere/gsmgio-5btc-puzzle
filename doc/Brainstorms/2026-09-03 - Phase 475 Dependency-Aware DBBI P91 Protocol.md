# Phase 475 dependency-aware DBBI/P91 protocol

Date frozen: 2026-09-03

## Question

Does the 91-character block immediately after `BTCSEED`, including the
terminal `Z`, have an unusually English-like direct algebraic relationship to
the 91-character `DBBI` string?

## Fixed inputs and extraction

- Build the 5x5 square from `DBBI[:13]` exactly as in Phase 386.
- Bifid-decrypt the complete 570-character `FAED` stream as one block, using
  row-column coordinate order.
- Set `P91 = decoded[7:98]`. No alternate boundary is eligible.
- Normalize `J -> I` only for 5x5-coordinate operations.

## Frozen six-member family

Alphabet arithmetic uses `A=0,...,Z=25`, position by position:

1. `P91 - DBBI (mod 26)`
2. `P91 + DBBI (mod 26)`
3. `DBBI - P91 (mod 26)`

Coordinate arithmetic maps both strings through the same DBBI-derived 5x5
square, operates independently on row and column modulo 5, and maps back:

4. `coords(P91) - coords(DBBI) (mod 5)`
5. `coords(P91) + coords(DBBI) (mod 5)`
6. `coords(DBBI) - coords(P91) (mod 5)`

No shifts, reversals, transpositions, routes, alternate squares, `M91`, or
cross-spliced row/column variants are eligible.

## Statistic and null

The sole decision statistic is the maximum whole-string English quadgram
score across the six outputs, using the project's frozen quadgram table.

For each of 100,000 trials, deterministically permute the exact 570-letter
`FAED` multiset, rerun the same full-block Bifid extraction, construct all six
outputs against fixed `DBBI`, and retain the family maximum. This upstream
null preserves the dual role of DBBI as both square source and comparison
string; it does not incorrectly treat observed P91 as an independent bag of
letters.

Use seed `0x475`. Report both the raw exceedance fraction and the add-one
empirical p-value `(tail+1)/(trials+1)`. Promote only at add-one `p <= 0.005`.
Exact hits from the already-frozen Phase 396 keyword list are descriptive and
cannot promote the family.

## Controls and exclusions

- Assert byte-for-byte agreement with Phase 386's observed `P91`.
- Assert inverse identities for both subtraction representations.
- Include a synthetic English planted positive through one eligible operation.
- Make zero password, ciphertext-oracle, or cryptocurrency endpoint calls.

This test is conditional on the already-selected Phase 386 decoder and fixed
`[7:98]` boundary. It does not include the historical search that discovered
`BTCSEED`, and it cannot establish creator intent even if it promotes.
