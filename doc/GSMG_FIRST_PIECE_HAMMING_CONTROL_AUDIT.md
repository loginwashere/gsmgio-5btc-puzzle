# GSMG First-Piece Hamming/Control-Language Audit

**Date:** 2026-08-09  
**Status:** Exact structural facts verified; constructor-language interpretation remains unconfirmed.

## Scope

This audit tests the strongest low-parameter claims from
`GSMG_FIRST_PIECE_PIXEL_BRAINSTORM.md`. It composes existing authenticated
extractors rather than resampling the images independently:

- `first_piece_color_reconstruction.py` supplies `08C26D`, `F73D92`, the
  9/15 color counts, and the unique FEFE cell;
- `stage0_footer_palette_layer_audit.py` supplies the externally selected
  `#383838` shadow layer;
- `first_piece_hamming_control_audit.py` computes bit weights, the declared
  nibble matrices, the FE mask operation, and bounded family counts.

No password, cipher, or Bitcoin-address oracle is used in this phase.

## Verified identities

### Complementary color masks

```text
yellow=1 mask: 08C26D  popcount  9
blue=1 mask:   F73D92  popcount 15

08C26D XOR F73D92 = FFFFFF
08C26D +   F73D92 = FFFFFF
```

The 9/15 totals reproduce the yellow/blue source populations, but this is a
re-expression of how the masks were constructed, not independent evidence.

### Nibble-weight matrices

Counting set bits in each hexadecimal nibble and preserving the fixed
six-nibble order gives:

```text
08C / 26D       F73 / D92

0 1 2           4 3 2
1 2 3           3 2 1
```

The matrices complement cellwise to four. Their sums are:

```text
08C26D: rows (3,6), columns (1,3,5), total 9
F73D92: rows (9,6), columns (7,5,3), total 15
```

The `1,3,5` odd-number rail is therefore an exact property of the recovered
prime mask, not something generated from `86420`.

### Repeated-gray weights

```text
383838: 3 one-bits per byte,  9 total
C7C7C7: 5 one-bits per byte, 15 total
FEFEFE: 7 one-bits per byte, 21 total, 3 zeroes
```

`C7C7C7` is the computed complement of the authenticated `#383838` layer; it
is not claimed to be another selected image layer.

### FEFEFE as an executable mask

```text
FE = 11111110
```

Repeated across three bytes, `FEFEFE` is the unique mask that preserves each
byte's upper seven bits while clearing only its LSB. Applying it to the
prime-valued color mask gives:

```text
08 C2 6D
FE FE FE  AND
--------
08 C2 6C = 574060
```

Only the final source byte has an LSB of one, so the operation decrements the
prime by exactly one. Conversely:

```text
FEFEFE OR 010101 = FFFFFF
```

This verifies a concrete mechanical bridge among FEFE, the colored LSB plane,
the creator's zeroing language, and the observed off-by-one motif. It does not
yet prove that the creator intended this AND/OR operation downstream.

## Structural `21` cluster

The audit reproduces these exact facts:

```text
FEFEFE popcount                           = 21
FEFE character position                  = 21
FEFE source character                    = n
URL positions 1,4,21                     = g,g,n
24 ASCII characters x 7 retained bits    = 168 bits = 21 bytes
```

The `ggn -> G,G,n -> secp256k1` reading remains semantic speculation. This
phase verifies only the extraction and counts, not that lowercase URL letters
are intended as elliptic-curve notation.

## Calibration and evidentiary limits

The exact ordered nibble-weight profile `(0,1,2,1,2,3)` occurs in `2,304` of
the `C(24,9) = 1,307,504` 24-bit masks having weight nine:

```text
2304 / 1307504 = 144 / 81719 ~= 0.001762136
```

This is a descriptive conditional rate, not a discovery p-value: the
staircase/profile was recognized after viewing the real output, and no
orientation/profile family was preregistered.

The repeated-gray weight match is much less selective. Among all 256 repeated
byte values:

```text
C(8,3) = 56 bytes produce total 24-bit weight 9
C(8,5) = 56 bytes produce total 24-bit weight 15
C(8,7) =  8 bytes produce total 24-bit weight 21
```

Thus `383838 -> weight 9` is exact but not rare by itself. Its relevance comes
from the separate annotator-supplied G-shadow predicate that selected `38`,
not from Hamming weight alone.

## Verdict

Promote the following from brainstorm to verified structural facts:

1. the ordered nibble-weight matrices and their `1,3,5` / `7,5,3` column
   sums;
2. the repeated-gray weights `9`, `15`, and `21`;
3. FEFEFE's exact bytewise LSB-clearing behavior;
4. `08C26D & FEFEFE = 08C26C = 574060`, a decrement of one;
5. the exact `ggn` and 21-byte residual extractions.

Do not yet promote “Hamming weights are the constructor's control language,”
`ggn` as secp256k1 notation, or `igecabdfh` as the final alphabet. The best
next verification edge is whether the independently established prime-walk
token/list structure uses the same off-by-one/bit-clearing grammar without
introducing a new selector.

## Reproduction

```bash
python3 tools/gsmg/first_piece_hamming_control_audit.py --self-test
python3 -m unittest \
  tools.gsmg.test_recent_audits.CorrectedClaimTests.test_first_piece_hamming_control_language
```
