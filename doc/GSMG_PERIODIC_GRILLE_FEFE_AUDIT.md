# Periodic 49-Aperture Grille and `FEFEFE` Audit

**Date:** 2026-09-01  
**Verdict:** bounded negative for a full-grille prime or `FEFEFE` selector;
one additional unconsumed 25-bit prime is unsurprising and does not promote

## Scope

The 24 colored URL-LSB apertures all lie in the congruence class:

```text
(row - column) mod 4 = 3
```

Extending that visible every-eighth-spiral pattern to every fourth spiral bit
creates a natural 49-aperture turning grille. Its four rotations partition all
196 cells. The extension adds exactly:

```text
18 white + 6 black + 1 FEFEFE = 25 cells
```

The audit keeps the two rails separate for each physical rotation:

- `C`: the established 24 colored apertures;
- `M`: the 25 added/missing apertures;
- `F`: the complete 49-aperture union.

It tests the proven spiral order and an ordinary row-major control, with raw
and complementary polarity. `FEFEFE` is first treated by the established
dark/blue=`1`, light=`0` convention, then toggled alone to `1` as the only
sensitivity test. There is no padding, byte alignment, text decoding,
language scoring, candidate generation, or oracle.

## Baseline spiral results

`FEFEFE=0` gives:

| Turn | Colored raw / inverse | Added raw / inverse | Full raw / inverse |
|---:|---:|---:|---:|
| 0° | `16203154 / 574061*` | `8462728 / 25091703` | `257470650106440 / 305479303314871` |
| 90° | `16466188 / 311027*` | `29105716 / 4448715` | `553991210863056 / 8958742558255` |
| 180° | `11382767 / 5394448` | `33291838 / 262593` | `526510880284158 / 36439073137153` |
| 270° | `3141761 / 13635454` | `139760 / 33414671*` | `9549155325060 / 553400798096251` |

An asterisk marks a prime. Across the fixed family of four turns × three
rails × two polarities, the spiral order has three primes in 24 tested
numbers:

```text
colored inverse, 0°:    574061     (already established)
colored inverse, 90°:   311027     (already established)
added inverse, 270°:    33414671   = 0x1FDDE0F
```

All eight complete 49-bit values are composite. The row-major control has
zero primes across the corresponding 24 numbers.

The new 25-bit prime has no occurrence or consumer elsewhere in the local
project or indexed Denis corpus. It is also not inherently surprising: among
four odd numbers near 25 bits, the ordinary prime-density expectation already
makes at least one prime reasonably common. This observation is descriptive,
not a calibrated p-value because the four values are structured and related.

## What `FEFEFE` changes

The anomaly belongs to the base-orientation added rail. In spiral order it is:

```text
added-rail position: 20 zero-based of 25
full-grille position: 40 zero-based of 49
```

Changing only `FEFEFE` from `0` to `1` produces:

| Order | Turn | Rail | Integer XOR delta | Prime status changed? |
|---|---:|:---:|---:|:---:|
| Spiral | 0° | Added | `16` | no |
| Spiral | 0° | Full | `256` | no |
| Row-major | 0° | Added | `4096` | no |
| Row-major | 0° | Full | `8388608` | no |

It never changes a colored reading and changes no raw or inverse primality
result. In particular, the extra `33414671` prime occurs at 270°, whose
apertures do not land on `FEFEFE`; it therefore cannot explain the anomaly.

## Rail relationship

For every turn and order, the full reading projects exactly back to its 24-
and 25-bit component rails, as it must. Only the base spiral orientation has
strict alternation:

```text
M C M C ... M C M
```

This is a construction identity: the base completion uses every fourth spiral
position while the colored apertures use every eighth. It is not counted as
an independent discovery. The other physical rotations do not preserve that
linear alternation in the fixed spiral order.

No further arithmetic relationship between the unequal-length rails is
licensed by the source, so the audit does not manufacture one by truncating,
padding, shifting, or splitting the 49-bit values.

## Conclusion

Including the 25 added cells and `FEFEFE` does not extend the two-prime matrix
chain. The complete grille supplies no prime, and toggling the anomaly changes
no primality result. The lone additional missing-rail prime has no consumer
and is independent of the FE cell.

The 49-aperture branch should therefore be parked unless another artifact
independently names `33414671`, `1FDDE0F`, a 25-bit rail, or a consumer for the
complete grille.

## Reproduction

```bash
python3 tools/gsmg/periodic_grille_fefe_audit.py
python3 -m unittest discover -s tools/gsmg -p 'test_periodic_grille_fefe_audit.py'
```
