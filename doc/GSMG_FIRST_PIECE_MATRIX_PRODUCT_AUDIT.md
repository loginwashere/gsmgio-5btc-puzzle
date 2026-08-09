# GSMG First-Piece `[255,103]` Matrix-Product Audit

**Date:** 2026-08-09  
**Status:** Arithmetic verified; `FF67` consumer not selected.

## Construction

The authenticated first-piece color prime is:

```text
574061
```

The established `matrixsumlist` reconstruction writes its decimal digits
row-major as:

```text
M = [5 7 4]
    [0 6 1]
```

Its total and row sums are:

```text
v = [23,16,7] = [total, row-1 sum, row-2 sum]
```

Point 1 proposes feeding that list back as a column vector:

```text
M v = [5*23 + 7*16 + 4*7] = [255]
      [0*23 + 6*16 + 1*7]   [103]
```

The identities are exact:

```text
255 = 0xFF
103 = 0x67 = ASCII 'g'
byte serialization = FF67
```

The `g` is the first character of `gsmg.io/theseedisplanted`, and `FF` is a
full-white byte, one above the anomalous `FE` byte.

`tools/gsmg/first_piece_matrix_product_audit.py` reproduces this directly from
the existing authenticated `matrixsumlist` implementation. It does not run a
password, salt, ciphertext, or Bitcoin-address oracle.

## Fixed matrix, all vector orders

Keeping the row-major matrix fixed and permuting only the three established
vector components gives the complete six-member family:

| Vector | Output |
|---|---|
| `(23,16,7)` | `(255,103)` = `FF`, `g` |
| `(23,7,16)` | `(228,58)` = byte, `:` |
| `(16,23,7)` | `(269,145)` |
| `(16,7,23)` | `(221,65)` = byte, `A` |
| `(7,23,16)` | `(260,154)` |
| `(7,16,23)` | `(239,119)` = byte, `w` |

The authenticated order is the only one of six that yields `255` plus an
ASCII letter. It is also the only exact `(255,103)` result. Four of six orders
nevertheless fit both outputs into unsigned bytes and give a printable second
byte, so “byte plus readable character” by itself is not unusual.

The vector order is not arbitrary: `matrixsumlist` already fixes it as total,
first row, second row. Accordingly, the six-member permutation family is a
sensitivity analysis, not a claim that the solver may freely reorder it.

## Rectangle-orientation calibration

Crossing the four 2x3 rectangle symmetries with all six vector orders creates
24 raw rows but only 12 distinct ordered output pairs and six distinct
unordered pairs:

```text
{58,228}
{65,221}
{103,255}
{119,239}
{145,269}
{154,260}
```

`{103,255}` is one of those six pairs. The raw table contains `(255,103)`
twice because simultaneously reversing the matrix columns and vector order
does not change either dot product. Vertically flipping the matrix only swaps
the output order. Those are bookkeeping symmetries, not independent hits.

The source reconstruction independently selects forward row-major order, so
the geometric family does not invalidate the fixed product. It shows that the
visual interpretation is not orientation-free.

## Expanded digit-assignment control

As a deliberately broad descriptive control, the audit also allows arbitrary
assignment of the six distinct digits to the 2x3 matrix and every vector
order. There are 4,320 raw arrangements. Quotienting the six simultaneous
column relabelings—which preserve every dot product—leaves 720 operation
classes:

| Property | Classes | Rate |
|---|---:|---:|
| Exact ordered `(255,103)` | 1 | `1/720` |
| Exact pair in either order | 2 | `1/360` |
| Contains `255` plus any ASCII letter | 6 | `1/120` |

This is not the primary null: the image fixes digit order, and the semantic
categories were recognized after seeing the output. These rates describe the
arithmetic landscape; they are not discovery p-values.

## Dependency and assumption ledger

The two apparent operands are not statistically independent. `[23,16,7]` has
strong external provenance in the Architect dialogue and related puzzle text,
but inside this numerical construction it is also a deterministic function of
the matrix: total and row sums of the same six digits.

Moving from the established checkpoint to `FF67` requires additional steps:

1. reuse the output of `matrixsumlist` as a new column vector;
2. choose multiplication after the clue has already specified summation;
3. align `[total,row1,row2]` with the three matrix columns despite the unlike
   meanings of those dimensions;
4. interpret the first output as byte/white `FF`;
5. interpret the second output as ASCII `g`;
6. serialize the pair in listed byte order as `FF67`.

The byte interpretation is coherent—both fixed outputs are within 0–255—but
no authenticated instruction currently selects this second operation or says
to consume the pair as a key prefix, salt, IV, or password.

## Verdict

Promote:

1. the exact product `(255,103)`;
2. its exact byte reading `FF67` and ASCII/white associations;
3. uniqueness under the six fixed-matrix vector orders;
4. the orientation/permutation calibration and dependency warning.

Treat the result as a strong constructor-style recognition checkpoint, not as
independent statistical confirmation and not yet as executable key material.
Do not test `FF67` across authenticated blobs without a separate clue selecting
multiplication and a concrete consumer role.

## Reproduction

```bash
python3 tools/gsmg/first_piece_matrix_product_audit.py --self-test
```
