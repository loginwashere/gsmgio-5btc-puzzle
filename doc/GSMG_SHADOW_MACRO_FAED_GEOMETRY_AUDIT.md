---
type: audit
phase: 240
date: 2026-08-11
status: closed
result: negative
disposition: structural-only
evidence_level: authenticated-artifact
topics:
  - favicon
  - raster-analysis
  - phase-186
  - matrixsumlist
  - calibration
related_phases:
  - 186
  - 239
  - 241
  - 242
script: tools/gsmg/shadow_macro_faed_geometry_audit.py
aliases:
  - Phase 240
---

# Shadow-Macro Length and FAED Geometry Calibration

**Date:** 2026-08-11  
**Status:** Nested identity retained as recognition texture; width 38 not selected by raw-stream geometry.

## Scope

This audit tests two linked questions without decoding FAED or invoking a
password/blob oracle:

1. How unusual is the Phase-186 shadow layer's apparent match to contiguous
   lengths in the known macro island?
2. Does width 38 behave as a privileged dimension of FAED's raw 570-symbol
   stream when compared fairly with every other exact factor?

The numeric calibration extends
`tools/gsmg/small_number_coincidence_calibration.py`'s exact pairwise-sum
method. The geometry pass predeclares four row/column statistics and three
matched nulls before interpreting the results.

## Exact nested-length inventory

The authenticated token lengths are:

```text
M = matrixsumlist                 13
E = enter                          5
L = lastwordsbeforearchichoice    26
T = thispassword                  12
```

Their ten contiguous spans, in native order, are:

```text
13, 18, 44, 56, 5, 31, 43, 26, 38, 12
```

All ten are distinct. Four of the five shadow measurements land on this set:

```text
18 = lower shadow-row sum          = len(M+E)
38 = collapsed hexadecimal #38     = len(L+T)
43 = total shadow pixels           = len(E+L+T)
56 = decimal value of 0x38         = len(M+E+L+T)
25 = upper shadow-row sum          = no contiguous span
```

The dependencies are load-bearing: 38/56 are two representations of one
color byte, 43 is forced by 25+18, and 56 is necessarily the total token
length.

Permuting the four fixed token lengths gives a bounded order control:

```text
permutations retaining 4/5 span hits:       8/24
permutations retaining 3/5:                 8/24
permutations retaining 2/5:                 8/24
permutations retaining the exact unlabeled
  prefix18 / suffix38 / suffix43 / total56: 2/24 = 1/12
```

The native named order is one of those two; swapping the 26/12 suffix retains
all sums. This is real ordered structure, but not a low enough descriptive
rate to authenticate an operation.

## Extended small-number base rate

The pre-existing 18-number calibration has 12 pairwise sums among 153 pairs
that land on another pool member (`7.8%`). Adding only the newly relevant
token/span/shadow values produces:

```text
26 distinct numbers
325 unordered pairs
44 pairwise-sum hits
hit rate 13.54%
```

Several hits are forced definitions, but that is the point of retaining them:
this particular number family is dependency-dense. The extended rate is
higher, not lower, than the already-unremarkable precedent. Isolated equations
such as `18+38=56` cannot be counted as independent confirmations.

## Factor asymmetry

DBBI's raw length is semiprime:

```text
91 = 1x91 = 7x13
```

Its only nontrivial rectangle is 7x13. The connection to the 13-letter
`matrixsumlist` token is new, but `91=7x13` itself predates this audit.

FAED has eight factor pairs:

```text
1x570, 2x285, 3x190, 5x114,
6x95, 10x57, 15x38, 19x30
```

Among the four primitive token lengths, `enter=5` also divides 570. Thus the
FAED leg has at least two token-length divisor matches, 5 and 38; it is not
symmetric with DBBI's uniquely factored 13.

## FAED geometry family

All 16 oriented widths were tested:

```text
1,2,3,5,6,10,15,19,30,38,57,95,114,190,285,570
```

For every width, the raw stream was reshaped row-major and measured under:

1. full nine-symbol frequency χ² across columns;
2. full nine-symbol frequency χ² across rows;
3. combined `{g,i}` escape-density χ² across columns;
4. combined `{g,i}` escape-density χ² across rows.

This gives a declared family of `16x4=64` cells per null. The controls are:

- 2,000 raw-symbol shuffles preserving FAED's complete symbol multiset;
- 2,000 `{g,i}`-token shuffles preserving all 436 checkerboard tokens and
  their internal symbol order;
- all 570 cyclic origins, preserving the circular raw symbol/digram sequence.

The cyclic control is phase-sensitive for row partitions. Column frequency
statistics are invariant under cyclic origin up to column permutation, which
correctly yields `p=1` rather than false evidence.

## Width 38 result

For the proposed 15x38 grid:

```text
column symbol χ²: 264.380507
row symbol χ²:    141.275283
column {g,i} χ²:   21.780220
row {g,i} χ²:       7.560440
```

The minimum p-value for width 38 under each control is:

```text
raw-symbol shuffle:    0.03848  (row-symbol χ²)
{g,i}-token shuffle:   0.04398  (row-symbol χ²)
cyclic origin:         0.26316  (row-symbol χ²)
```

The first two are nominal curiosities, not corrected hits. Across the declared
64-cell family, both Bonferroni values cap at 1.0. The cyclic-origin result also
shows that the authored starting phase is ordinary for this width.

Width 5 supplies the requested control. Its raw-shuffle row-symbol result is
similarly nominal (`p=0.04298`), while token shuffle gives `p=0.12744` and
cyclic origin `p=0.20`. Therefore an independently fixed token role can produce
the same class of weak raw-grid effect without being a plausible matrix width.

## Family winners

Width 38 is not the strongest member under any control:

```text
raw shuffle:       width 30, row-symbol χ², p=0.004998, corrected p=0.31984
token shuffle:     width 30, row-symbol χ², p=0.006497, corrected p=0.41579
cyclic origin:     width 285, row-symbol χ², p=0.007018, corrected p=0.44912
```

No cell survives the fixed family correction. The nominal width-30 agreement
between both shuffle families is descriptive only and fails the independent
cyclic-origin control and the declared correction; it does not open a new
dimension hypothesis.

## Verdict

Retain the `18/38/43/56` nesting as a compact recognition curiosity, with its
dependencies and `2/24` unlabeled-order control attached. Do not describe the
DBBI and FAED factor legs as symmetric: 13 is DBBI's only nontrivial
co-dimension, while 570 has eight factor pairs and both 5 and 38 are token
length divisors.

The direct measurement does not select 38 as FAED's width. Its nominal
row-symbol effect is family-wise negative, phase-ordinary, comparable to the
width-5 control, and weaker than unselected widths elsewhere in the factor
family. No decoder, transposition, alpha stream, credential, or blob oracle is
authorized.

Reproduce with:

```bash
python3 tools/gsmg/shadow_macro_faed_geometry_audit.py --self-test
```
