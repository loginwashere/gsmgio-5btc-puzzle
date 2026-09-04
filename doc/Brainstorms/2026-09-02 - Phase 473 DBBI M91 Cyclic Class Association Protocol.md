---
type: preregistration
status: frozen
date: 2026-09-02
phase: 473
topics:
  - DBBI
  - plaintext-alignment
  - cyclic-correlation
  - class-association
  - permutation-null
---

# Phase 473 — DBBI/M91 Cyclic Class Association Protocol

## Question

Even though Phase 472 found no exceptional direct mod-9 equality under its
19,686-route family, does DBBI have any route-independent categorical
association with structural classes of the equal-length authenticated
Phase-3.2.2 plaintext at one of the 91 cyclic offsets?

This executes catalog items 191–193 and 198. It does not repeat the already
covered cellwise mod-26 arithmetic (items 189–190), matrix selectors/sorts
(194–197), full geometric-route equality (199), or unselected masks/extrema
(200–201). Item 202's held-out learner is reserved for a separately frozen
Phase 474 only if this phase clears its complete screening gate; separating
discovery from validation prevents a feature/offset discovered here from being
claimed as independently confirmed on the same data.

## Frozen inputs

- Canonical `DBBI` and `VALIDATION_ANSWER` from `tools/gsmg/data.py`.
- Four fixed 91-character controls from Phase 472: the exact normalized
  windows beginning at offsets `0, 273, 546, 819` in the already-pinned
  Phase-421 long corpus record.
- Exactly 91 cyclic offsets. At offset `o`, DBBI position `(i+o) mod 91` is
  paired with plaintext position `i`.
- DBBI representations:
  1. raw nine-symbol categorical values `a..i`;
  2. binary `{b,e}` versus all other symbols.
- Plaintext representations:
  1. vowel/non-vowel, vowels exactly `AEIOU` (`Y` is non-vowel);
  2. A0Z25 modulo `2`;
  3. modulo `3`;
  4. modulo `7`;
  5. modulo `9`;
  6. modulo `13`.
- This gives `2 × 6 × 91 = 1,092` frozen cells per target.
- RNG: NumPy `default_rng`, seeds `473..477` for the real target and four
  controls respectively; `N_NULL = 5,000` independent permutations of DBBI's
  exact symbol multiset per target.

## Frozen statistic

For every representation/feature/offset cell, compute empirical categorical
mutual information in natural-log units from its complete contingency table.
No numeric equality mapping between the categories is assumed.

Because raw mutual information has different finite-sample baselines for
binary and multi-category tables, standardize each of the 1,092 cells against
that cell's own 5,000 null values:

```text
z_cell = (MI_cell - mean_null_cell) / sd_null_cell
```

The single decision-bearing statistic is the maximum `z_cell` across the
1,092-cell family. Every null replicate is standardized by those same frozen
null means/SDs and reduced to its own 1,092-cell maximum. The global upper-tail
plus-one p-value is:

```text
p_global = (1 + count(null_max >= real_max)) / 5001
```

The implementation may use FFT circular contingency counts, but structural
tests must verify the FFT offset-zero result against a direct contingency
calculation. Computation method does not change the family.

## Decision rule

A Phase-473 screening lead requires all of:

1. real-target global `p < 0.001`;
2. real-target maximum z strictly exceeds every fixed control maximum z;
3. real-target global p is strictly smaller than every control global p;
4. the winning cell's raw-MI upper-tail plus-one p is `< 0.001` as a
   diagnostic guard;
5. input, family-size, multiset, and synthetic/direct-vs-FFT invariants pass.

If all gates pass, record only the selected representation, plaintext class,
and offset, and stop. A separately preregistered Phase 474 may then test that
frozen relation out of sample. Phase 473 itself licenses no interpretation or
downstream use.

Anything else is `bounded_negative` for items 191–193 and 198 at this scope.

## Stop rule

- One decision-bearing execution after protocol/script hashing and lock.
- No added letter classes, moduli, offsets, mappings, reversals, routes,
  controls, scores, or neighborhoods after output inspection.
- No serialization of match letters, mismatch letters, arithmetic streams, or
  candidate plaintext.
- No password generation, hashes, FAED usage, decryptions, Bitcoin checks, or
  oracle calls.
- Items 200–202 and `G-MSL-001` remain unchanged unless their own independent
  prerequisites are later met.
