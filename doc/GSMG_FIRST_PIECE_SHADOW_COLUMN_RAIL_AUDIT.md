# GSMG Two Shadow-Rail Column Audit

**Date:** 2026-08-09  
**Status:** Predeclared column operations exhausted; no selected payload or consumer.

## Source rails

The exact `#383838` glyph streams and per-glyph pixel counts are:

```text
upper: G S G O 5 B C P U C G
       4 1 4 4 2 1 1 1 2 1 4

lower: G M G C 9 g 2 c P B e
       2 1 2 2 1 3 1 1 1 2 2
```

Both contain 11 selected glyphs. Point 17 proposed pairing them ordinally and
using only larger/smaller count choice, equality, sums, and differences.

`tools/gsmg/first_piece_shadow_column_rail_audit.py` resamples the authenticated
image and freezes exactly that operation family. It does not add a cipher,
word list, element-symbol parse, DBBI/FAED assignment, or password oracle.

## Ordinal versus physical alignment

The two streams have equal length, but they are not physical vertical columns
in the image. Their selected source-glyph ordinals are:

```text
upper: 1,2,4,6,7,8,10,11,12,17,24
lower: 2,4,5,8,9,19,21,23,26,33,34
```

For each proposed ordinal pair:

- zero of 11 x-coordinate glyph boxes overlap;
- center offsets vary from 21.5 to 214 pixels;
- there is no constant horizontal translation between the rows.

Thus “column” means selected-glyph rank only. Equal `11/11` length makes that
pairing possible, but the raster does not independently enforce it.

## Larger and smaller count selection

The exact comparison table is:

| Col | Upper | Lower | Relation | Sum | Signed difference |
|---:|---|---|---|---:|---:|
| 1 | `G:4` | `G:2` | upper | 6 | 2 |
| 2 | `S:1` | `M:1` | tie | 2 | 0 |
| 3 | `G:4` | `G:2` | upper | 6 | 2 |
| 4 | `O:4` | `C:2` | upper | 6 | 2 |
| 5 | `5:2` | `9:1` | upper | 3 | 1 |
| 6 | `B:1` | `g:3` | lower | 4 | -2 |
| 7 | `C:1` | `2:1` | tie | 2 | 0 |
| 8 | `P:1` | `c:1` | tie | 2 | 0 |
| 9 | `U:2` | `P:1` | upper | 3 | 1 |
| 10 | `C:1` | `B:2` | lower | 3 | -1 |
| 11 | `G:4` | `e:2` | upper | 6 | 2 |

Ignoring ties, the strict outputs are:

```text
larger-count characters:  GGO5gUBG
smaller-count characters: GGC9BPCe
```

The tied pairs are:

```text
column 2: S / M
column 7: C / 2
column 8: P / c
```

Keeping ties explicit gives templates:

```text
larger:  G=GO5g==UBG
smaller: G=GC9B==PCe
```

Resolving each of the three ties upper/lower creates eight variants per rail.
Every larger variant contains `5`; every smaller variant contains `9`; none is
a plain alphabetic word or self-validating instruction. There is no justified
tie-breaking rule among the eight variants.

## Equality and comparison masks

The signed comparison sequence and equality mask are:

```text
signs:         +0+++-00+-+
equality mask: 01000011000
equality cols: 2,7,8
mask integer:  536
```

The profile is:

```text
upper wins: 6
lower wins: 2
ties:       3
```

Neither `536`, the `6/2/3` profile, nor the tied glyph pairs connects to an
independently selected consumer.

## Column sums and differences

The predeclared numeric lists are:

```text
sums:       6,2,6,6,3,4,2,2,3,3,6
digits:     62663422336
A1Z26:      FBFFCDBBCCF

signed:     2,0,2,2,1,-2,0,0,1,-1,2
absolute:   2,0,2,2,1,2,0,0,1,1,2
digits:     20221200112
```

Their aggregate totals are:

```text
sum of column sums       = 43
sum of signed differences = 7
sum of absolute differences = 13
```

The first two are forced restatements of the already verified row totals:

```text
25 + 18 = 43
25 - 18 = 7
```

The absolute total `13` happens to equal the prior row-local G-consumer residue
count. It is not forced, but it is not rare under the bounded alignment
control below and was recognized post hoc.

## Fixed-multiset alignment calibration

Keep the upper count row fixed and reassign the lower count multiset
`{1×5,2×5,3×1}` over the 11 ordinal positions. There are 2,772 unique
assignments:

| Observed property | Assignments | Rate |
|---|---:|---:|
| Absolute total `13` | 900 | `25/77 ≈ 0.3247` |
| Three ties | 840 | `10/33 ≈ 0.3030` |
| Both of the above | 340 | `85/693 ≈ 0.1227` |
| Full aggregate `(abs=13,ties=3,upper=6,lower=2)` | 20 | `5/693 ≈ 0.0072` |

The full profile is more selective, but it was assembled after inspecting the
result and is not a valid discovery p-value. The individual `13` and
three-tie properties are ordinary.

## Verdict

Promote the exact larger/smaller candidate families, masks, sums, and
differences as exhausted bounded outputs. Do not promote any as plaintext,
selector list, DBBI/FAED assignment, or key material.

Most importantly, downgrade the “11 physical columns” premise: the raster
supports two equal-length selected sequences, but only ordinal rank pairs them.
The existing row-local invariant-G rule yielding `OCBe → 8,6,4` remains a much
better-grounded consumer because it does not require cross-row alignment.

Point 17 is closed unless another clue explicitly says to zip the two rows,
breaks the three ties, or assigns the rails to named consumers.

## Reproduction

```bash
python3 tools/gsmg/first_piece_shadow_column_rail_audit.py --self-test
```
