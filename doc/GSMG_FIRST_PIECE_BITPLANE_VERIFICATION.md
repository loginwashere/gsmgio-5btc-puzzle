# GSMG First-Piece Complete Bit-Plane Verification

**Date:** 2026-08-09  
**Status:** Full 192-bit transpose verified; 21-byte residual is exact but length-forced.

## Construction

The authenticated Stage-0 plaintext is the 24-byte ASCII string:

```text
gsmg.io/theseedisplanted
```

The first-piece image independently proves that each colored endpoint is the
LSB of the corresponding character. Transposing all 24 bytes produces an
8x24 binary matrix: one 24-bit row for each bit position from bit 7 (MSB) to
bit 0 (LSB).

`tools/gsmg/first_piece_bitplane_audit.py` constructs the matrix directly from
the authenticated plaintext, verifies bit 0 against the image extraction, and
reconstructs the original plaintext losslessly from all eight planes.

## Complete plane inventory

```text
bit  direct  weight   complement  weight
 7   000000     0     FFFFFF        24
 6   F6FFFF    22     090000         2
 5   FFFFFF    24     000000         0
 4   4090C4     6     BF6F3B        18
 3   2F4128     9     D0BED7        15
 2   BBAE2F    16     4451D0         8
 1   DB1088     9     24EF77        15
 0   F73D92    15     08C26D         9
```

Bit 0 reproduces the image-derived color masks exactly:

```text
blue=1/yellow=0 -> F73D92
yellow=1/blue=0 -> 08C26D
```

## What is and is not unique

Across the bounded 16-member family of eight planes and their complements:

- only bit 0's complement is prime: `08C26D = 574061`;
- only bit 0 and its forced complement have the unit nibble-weight staircase;
- Hamming weight 9 is **not** unique: bit 3 direct, bit 1 direct, and bit 0
  complement all have weight 9;
- correspondingly, weight 15 occurs at bit 3 complement, bit 1 complement, and
  bit 0 direct.

Thus the `#383838 -> weight 9` match cannot identify the colored LSB plane
inside the complete URL bit-plane family. The independently visible colored
endpoints select bit 0. The prime and staircase properties then distinguish
its polarity/structure after that selection.

The fact that exactly one of 16 values is prime is not presented as a rare
event; numbers near 24-bit scale have prime density on the order of one per
logarithmic-sized neighborhood. Its value is positional: the sole prime is at
the independently selected colored plane and complementary polarity.

## Seven-plane residual

Removing bit 0 leaves a 7x24 matrix:

```text
7 x 24 = 168 bits = 21 bytes
```

There are two immediate traversal conventions:

1. **Plane-major:** concatenate bit planes 7 through 1.
2. **Character-major:** retain bits 7 through 1 from each source character.

Their exact bytes are:

```text
plane-major:
000000F6FFFFFFFFFF4090C42F4128BBAE2FDB1088

character-major:
66E5B332ED1B9774D193964C993472E1B306EE9932
```

Neither is plaintext:

```text
plane-major:     5/21 printable bytes, longest run 3
character-major: 7/21 printable bytes, longest run 2
```

Both are lossless when combined with the authenticated LSB plane, but they are
different byte strings related by transposing the same 7x24 matrix. Therefore
“the 21-byte residual” has a fixed size but not one uniquely specified byte
serialization without an additional row/column traversal instruction.

## Calibration of the `21` convergence

The residual byte count is exact:

```text
24 source bytes x 7 retained bits / 8 = 21 bytes
```

But it is algebraically forced once the independently fixed 24-character
source and LSB removal are chosen. In the range of source lengths 1 through
64, a seven-bit residual has an integral byte length exactly when the source
length is a multiple of eight. A 21-byte result uniquely corresponds to a
24-byte source because `21*8/7=24`.

Accordingly, this is a real three-way numerical convergence with FEFE's
popcount 21 and the creator's character index 21, but it is not three
independent random hits. The residual `21` contributes a clean structural
restatement of the authenticated source length and selected LSB operation.

## Seven-password hypothesis

The residual does provide seven 24-bit planes, but their inventory argues
against treating them immediately as seven password-like secrets:

- bit 7 is all zero;
- bit 5 is all one;
- bit 6 contains 22 ones;
- none of the seven direct/complement values is prime;
- the two natural packed traversals are non-text.

The seven planes remain valid structured inputs, but “seven passwords” is not
verified by this pass.

## Verdict

Promote:

1. the complete eight-plane inventory;
2. the exact image/LSB equality;
3. the lossless 21-byte residual dimension;
4. prime uniqueness at bit 0 complement within the bounded plane family;
5. unit-staircase uniqueness at bit 0 direct/complement;
6. the non-uniqueness of weight 9 and 15 across other planes.

Do not promote either packed residual as a key/password, the residual length
as independent statistical evidence, or the seven planes as seven passwords.
The next bounded target is `{1,4,21} -> ggn`: determine whether the tuple has
distinctive structural status among comparably sourced triples before applying
secp256k1 semantics.

## Reproduction

```bash
python3 tools/gsmg/first_piece_bitplane_audit.py --self-test
```
