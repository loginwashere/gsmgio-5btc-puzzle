# GSMG `matrixsumlist` Historical Code Audit

**Date:** 2026-08-09  
**Cutoff:** Telegram message `60333`, 2026-03-04 03:39:06, the first
publication found for the exact 31-character selection
`ncsyangcahiriasogaleafayanestve`.

## Question

Did any repository, notebook, or shared code artifact predating that output
already define all of the following?

1. matrix dimensions;
2. where the 31 selected characters enter;
3. row/column traversal;
4. summation or indexing rules;
5. the next expected artifact.

The cutoff matters. Code written after the selected string became public can
reproduce or elaborate it, but cannot independently establish the intended
transition.

## Result

No. The historical record contains partial mechanics, but no pre-output
artifact consumes the 31 characters. The closest code fixes a 14x14 positional
spiral and row/column sums, yet those sums ignore both the puzzle bits and the
letters displayed on prime positions. Its output was already fixed before the
31-character selection existed.

Therefore the strict worksheet remains:

```text
G1 source justification: PARTIAL for historical community mechanics
G2 exact input:          PASS
G3 complete operation:  FAIL
G4 next artifact:       FAIL
```

## Chronological worksheet

| Date | Artifact | Dimensions | Where the 31 characters enter | Traversal | Sum/index rule | Next artifact | Verdict |
|---|---|---|---|---|---|---|---|
| 2021-05-20 | Public walkthrough, commit `a7041aac` | None for a consumer | Nowhere; only the standalone binary token is decoded | None | None | None | Establishes `matrixsumlist` text only |
| 2023-08-31 commit date | Naddiseo `salphaseion.ipynb`, commit `dcb66952` | None for a consumer | Nowhere; notebook ends with DBBI/FAED undecoded | Page segments only | Decodes the instruction islands | None | No transition mechanic |
| 2024-12-10 | Telegram `33950`, `696783482-puzzle-1.txt` | Intended `1 x 1539` character row | Nowhere; uses a different 1,539-character ciphertext | Python row order; columns follow `zip(*)` | `row_sums + col_sums` over character ordinals | None | Real community definition of “matrix sum list,” but wrong input and no dimensions suitable for 31 |
| 2025-03-02 | Telegram `36612/36617`, `puzzlegrid copy.html`; reposted at `37705` | Fixed 14x14 macro grid; seven 5x5 rabbit grids | Nowhere | Ten selectable macro traversals: two row, two column, Z, diagonal, random, center-distance, CW spiral, CCW spiral | Binary-to-ASCII only; no sums | None | Explicit evidence that traversal was *not* fixed |
| 2025-04-20 | Telegram `38464`, `salphaseion.html` | None for a consumer | Nowhere | Draggable page sections | Generic SHA-256 helper | None | Interface/visualizer, not an algorithm |
| 2025-04-20 | Telegram `38470`, `14x14 Grid Tool Version.html` | Fixed 14x14 | Nowhere; embeds a different 44-letter instruction string | Fixed counterclockwise spiral, starting top-left and moving down the left edge | Sum positional prime numbers by physical row and column, then `(sum-1) mod 26` | A nearby `56 letters -> 140 squares` thematic echo, not a generated artifact | Strongest partial mechanic, but output is independent of grid bits and letters |
| 2025-04-20 | Denis `matrix-animation.patch`, message `38473` | None | Nowhere | None | None; three CSS animation-line changes only | None | Adjacent code, but no matrix-mechanic change |
| 2025-06 to 2025-10 | Historical-chat file, Hush scripts, `MISC.txt`, status notes | None relevant | Nowhere | None | Password enumeration/status notes | None | No consumer |
| 2025-11-26 | Nathansenn fork, commit `2ec5c553` | Mentions seven row sums for an a-i grid | Nowhere | Unspecified | Reports `57,75,74,57,63,71,25`; recommends trying alternatives | None | Post-hoc analysis, not a fixed implementation |
| 2025-12-08 | Deramatamara fork unique commits | None relevant | Nowhere | None | Password database/AES attempts | None | No consumer |
| 2026-03-04 | Denis message `60333` | N/A | First observed exact 31-character output | N/A | Prime/color extraction creates the input | N/A | Historical cutoff |

Public commit anchors:

- [puzzlehunt walkthrough commit `a7041aac`](https://github.com/puzzlehunt/gsmgio-5btc-puzzle/commit/a7041aac0b920bb207c071d92386e096204eab6d)
- [Naddiseo notebook commit `dcb66952`](https://github.com/Naddiseo/gsmgio-5btc-puzzle/commit/dcb66952de3157f6e68cb00aa047dd2e4ff8ae39)
- [Nathansenn analysis commit `2ec5c553`](https://github.com/nathansenn/gsmgio-5btc-puzzle/commit/2ec5c553fb918b0977e893dc25c7f43b7b4fa053)

## The March 2025 explorer

The earliest local code that fixes a 14x14 representation is not a decoder
with one traversal. Its UI exposes this ten-member family:

```text
rowMajorL2R
rowMajorR2L
colMajorT2B
colMajorB2T
zPattern
diagonalDownRight
randomOrder
distanceCenter
spiralCW
spiralCCW
```

The same byte-identical file appears in messages `36612`, `36617`, and
`37705`, SHA-256:

```text
3c04f68491dd2f586ee129d52e340bcb75145f1914d20edd334a61ea8d55bfab
```

This supports 14x14 as a community model of the source image. It does the
opposite of selecting G3: orientation is an interactive choice, and the random
option makes clear that the tool is exploratory.

## The April 2025 prime-sum tool

The strongest candidate is Telegram message `38470`, SHA-256:

```text
707e747a8bc4786aa0a6b8ed6df2c0de3adcab3cfe268fcfceb3548a9d5ee7c0
```

It plants the integers `1..196` in a counterclockwise spiral beginning at the
top-left corner, assigns the 44-character string
`matrixsumlistlastwordsbeforearchichoiceenter` to prime ordinal positions, and
offers a “prime sums” display.

The immediate conversation explains why the author was looking at 14x14, but
not why the sum function should be used. In messages `38468–38469`, the author
counts all “readable passwords” as 56 letters, subtracts them from 196 to get
140 squares, and links that to “worth one hundred fourty of the investment.”
Message `38471` advertises prime-position toggles and other features. This is
useful authorship context, not a next-stage output: the code's actual
`letterString` is only 44 characters (it omits the 12-character
`thispassword`), and the surrounding messages never select the positional
row/column-sum routine or identify what its result should open.

Reimplementing its exact code gives:

```text
row sums:
131 144 358 194 267 372 615 369 331 398 11 358 224 59

row letters:
ANTLGHQESHKTPG

column sums:
41 173 301 400 361 476 419 348 198 398 416 0 203 97

column letters:
OQOJWHCJPHZ-US
```

The decisive implementation detail is in `calculatePrimeSums`: for each cell,
it reads only `cell.dataset.positional` and adds that positional number when it
is prime. It never reads:

- the cell's binary value;
- yellow/blue state;
- `letterString`;
- the later 31-character selection.

Consequently these 28 sums are constants of a 14x14 counterclockwise numbering
scheme. Changing every image bit or every displayed letter leaves the output
unchanged. The tool supplies dimensions, traversal, and one sum convention,
but no input binding and no recognizable or authenticated next artifact.

## Attachment and fork coverage

Denis posted `matrix-animation.patch` three minutes after the tool. Its exact
three changes remove the black page background and change the Matrix-rain CSS
animation from `-100%` to `0`; it does not touch grid, traversal, prime, sum, or
letter logic. Its SHA-256 is
`c64e21ee07b11a5ee60a1b1b4d621183265c061f61b7599506e65e5a0a99d8ac`.

The reproducible scan checked all 83 pre-cutoff Telegram attachments recognized
as text or code, including patch/C/C++/CUDA/header/Pyx and text-MIME files.
Eleven contained at least one of `matrixsumlist`,
row/column-sum vocabulary, or an explicit 14x14 reference. Zero contained the
31-character selection.

The GitHub fork comparison additionally checked pre-cutoff forks whose push
dates differed from inherited upstream history. Five accessible forks had
unique commits before the cutoff: `tanonen`, `Sazapz`, `hethsnow`,
`nathansenn`, and `deramatamara-lab`. Only Nathansenn added a numerical matrix
discussion; none supplied code binding the 31 characters to a fixed matrix
consumer. Repositories first created in June/July 2026 were retained only as
post-output controls and cannot provide independent provenance.

## Implication

The audit closes one tempting shortcut: we should not import the April 2025
counterclockwise positional-prime sums as the missing `matrixsumlist`
operation. They never accept the relevant input.

It does leave a narrower historical clue worth remembering: community tooling
converged on a 14x14 physical grid, and one author later preferred a top-left
counterclockwise positional spiral. If primary evidence independently says
“use the old grid tool” or identifies that exact authoring convention, those
facts can be reopened. Without that bridge, they remain community provenance,
not creator selection.

Reproduce the local evidence with:

```bash
python3 tools/gsmg/matrixsumlist_historical_code_audit.py --self-test
```
