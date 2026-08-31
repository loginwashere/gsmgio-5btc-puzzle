# Denis Golovkin Rotation-Grille Lead Audit

**Date:** 2026-08-31  
**Verdict:** exact geometry; promising second inverse prime; no consumer yet

## Result

Denis's geometric observation is exact but his phrase "perfect matrix for
grille cipher" overstates it. The 24 colored cells and their four 90-degree
rotations are pairwise disjoint, as he said, but they cover only 96 of the
14x14 grid's 196 cells. A complete 14x14 turning grille requires 49 apertures,
not 24.

Continuing the lead with the creator-established counter-clockwise spiral
produces a new, fixed result. Reading the base bit under each rotated aperture
set gives four 24-bit words:

| Rotation | Dark=1 word | Inverse | Decimal | Prime? |
|---:|---:|---:|---:|:---:|
| 0 degrees | `F73D92` | `08C26D` | 574061 | yes |
| 90 degrees | `FB410C` | `04BEF3` | 311027 | yes |
| 180 degrees | `ADAFEF` | `525010` | 5394448 | no |
| 270 degrees | `2FF081` | `D00F7E` | 13635454 | no |

Thus the same aperture/rotation/spiral/inverse rule that recovers `574061`
also yields a second prime, **311027**. Clockwise versus counter-clockwise and
the starting rotation only reorder this four-word set; they do not change it.
The executable audit checks counter-clockwise rotation independently with
`(row, column) -> (13 - column, row)` and asserts the reversed cycle
`F73D92, 2FF081, ADAFEF, FB410C` and its corresponding inverse words.

This is the strongest unclosed continuation found in Denis's grille lead. It
is compatible with the plural creator token `yellowblueprimes` and with Nik's
earlier message `37409` speculation, acknowledged by Denis in reply `37410`,
that `yinyang` might mean "primes / inv primes." It is not creator-confirmed,
and no occurrence or consumer for `311027` / `04BEF3` was found in the local
project or Denis corpus.

## Provenance

The relevant community messages are:

- `65935`, Denis Golovkin, 2026-06-25: unwind the spiral into a line and note
  that the marks are periodic/equidistant;
- `65938`, Denis: cutting out the colored cells gives a grille matrix;
- `65939`, Denis: the cells do not interfere under four 90-degree rotations;
- `37409`, Nik, 2025-03-29: proposes "yin-yang" as "primes / inv primes";
- `37410`, Denis: calls Nik's interpretation brilliant, while specifically
  highlighting Nik's separate `oo`/OEIS observation rather than explicitly
  endorsing the inverse-prime clause.

These are community hypotheses, not creator-authored instructions.

## Geometry

The colored cells are the 24 URL-character endpoints. In the proven spiral
indexing they are exactly:

```text
7, 15, 23, ..., 191        (zero-based; every eighth bit)
```

They occupy 24 distinct four-cell rotation orbits, hence the clean 96-cell
union. Each 7x7 quadrant contains six apertures, another consequence of that
periodic layout.

All 24 colored cells also satisfy:

```text
(row - column) mod 4 = 3
```

That congruence class contains 49 cells and is a complete turning grille: its
four rotations partition all 196 cells. Its spiral indices are every fourth
bit, `3, 7, 11, ..., 195`. The 25 cells needed to extend Denis's mask are the
interleaved positions `3, 11, 19, ..., 195`: 18 white, 6 black, and the one
`FEFEFE` cell.

This periodic completion is elegant, but it is not uniquely forced. The 24
colored apertures leave 25 untouched rotation orbits, and independently
choosing one of four cells from each gives:

```text
4^25 = 1,125,899,906,842,624
```

possible complete turning grilles. The congruence completion is distinguished
only by extending the visible every-fourth-bit pattern.

## Controls and interpretation

The spiral order is not an arbitrary language-score choice: it is the order
that already decodes `gsmg.io/theseedisplanted`. Under ordinary row-major
grille reading, the four words are:

```text
BE2B9B  5861D3  DBCFBD  6A81A7
```

Neither these words nor their 24-bit inverses are prime. This makes the spiral
result more interesting than a generic grille observation.

It is still not enough to promote `311027` into a solved stage. Once the known
`574061` result has selected spiral order and inverse polarity, only one other
odd inverse candidate remains, and an arbitrary odd 24-bit number has roughly
a one-in-eight chance of being prime. The second hit is suggestive, not an
authentication event. Reopen this path if another artifact independently
names `311027`, `04BEF3`, a 90-degree turn, or a consumer for a list of two
primes.

## Reproduction

```bash
python3 tools/gsmg/denis_rotation_grille_audit.py
python3 -m unittest discover -s tools/gsmg -p 'test_denis_rotation_grille_audit.py'
```
