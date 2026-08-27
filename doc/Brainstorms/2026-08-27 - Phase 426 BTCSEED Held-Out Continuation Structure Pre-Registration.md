# Phase 426 — BTCSEED Held-Out Continuation Structure Pre-Registration

## Question

With Phase 386's decoder and the seven-character `BTCSEED` checkpoint frozen,
does the untouched 563-character continuation contain sequential structure that
is exceptional relative to exact-multiset reorderings of that continuation?

This is a checkpoint-consumer gate. It does not search for another decoder,
word, key, boundary, or password.

## Frozen observed object

- reproduce Phase 386 byte-for-byte: `FAED`, the DBBI-first-13 keyed square
  `DBIFHCEGAKLMNOPQRSTUVWXYZ`, Bifid decrypt, one 570-character block,
  row-then-column convention, forward input and output;
- require the full output SHA-256 and exact `BTCSEED` prefix to match the
  Phase-425 artifact;
- remove exactly decoded positions `0:7`; the only tested object is
  `decoded[7:]`, length 563;
- do not inspect subwindows, alternate cut points, rails, reversals, squares,
  periods, operations, or coordinate conventions.

The boundary at seven is fixed by the already-audited target, not selected from
the continuation. Results are evidence about tail ordering only. They cannot
make the prefix more or less significant.

## Four frozen statistics

All statistics are one-sided, with larger values treated as more structured.

1. **English quadgram mean:** average log10 likelihood per overlapping
   quadgram under the repository's frozen `english_quadgrams.txt` table.
2. **Raw-DEFLATE saving:** `len(tail) - len(zlib.compress(tail, level=9,
   wbits=-15))`. This tests broad repeated/compressible structure without a
   plaintext assumption.
3. **Lag-1 mutual information:** plug-in mutual information in bits between
   adjacent letters, using the observed 25-letter alphabet and all 562
   adjacent pairs.
4. **Longest repeated substring:** maximum `k` for which two (overlap allowed)
   length-`k` substrings of the tail are identical.

Dictionary-word density, target-keyword scans, the `Z@97` geometry, and
`KMODEST` are excluded because earlier phases already inspected them. No
statistic or direction may be added after the observed result is calculated.

## Conditional exact-multiset null

Run 10,000 deterministic permutations of the 563 tail characters with seed
`0x426`. Each trial preserves the tail's exact character multiset and length,
but destroys its ordering. The `BTCSEED` prefix is held fixed conceptually and
never enters a statistic.

For each statistic, report an add-one upper-tail empirical p-value. Correct the
four-statistic family by an exact permutation rank-max procedure:

1. combine the observed row and all null rows;
2. within each statistic, assign every row its inclusive upper-tail fraction
   (ties share the conservative `>=` fraction);
3. define each row's extremeness as the maximum `-log10(p)` over the four
   statistics;
4. report the fraction of null-row extremeness values greater than or equal to
   the observed extremeness, with the observed row included in the denominator.

This calibration retains dependence between the four statistics. Also report
which statistic supplies the observed maximum, all null summaries, and the
number of ties.

## Gates

- **Continuation structure positive:** corrected `p <= 0.01`.
- **Suggestive only:** `0.01 < p <= 0.05`.
- **Null-like continuation:** corrected `p > 0.05`.
- **Regression failure:** decoder, prefix, length, or frozen-data hash differs;
  no inference is permitted.

A positive result promotes only the claim that the tail ordering is unusual
under this conditional permutation null. It does not prove English plaintext,
select an interpretation, or authorize password/blob/Bitcoin oracle calls. A
null result means this four-statistic continuation gate supplies no forward
edge; it cannot disprove every possible encoding.

## Validation

- pin hashes of the decoded stream and quadgram table;
- independently verify lag-1 mutual information is nonnegative;
- cross-check the longest-repeated-substring implementation against a brute
  force implementation on short deterministic strings;
- planted English/repetition controls must improve their intended detectors;
- deterministic replay must reproduce the complete JSON artifact.
