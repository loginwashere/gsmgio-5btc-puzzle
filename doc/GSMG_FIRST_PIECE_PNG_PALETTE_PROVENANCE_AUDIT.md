# GSMG First-Piece PNG Palette/Alpha Provenance Audit

**Date:** 2026-08-09  
**Status:** Point 9 closed negative; FEFEFE has no source palette index or alpha anomaly.

## Question

Point 9 proposed that the unusual `#FEFEFE` grid cell might have an
author-chosen PNG palette-entry index—a fifth coordinate in addition to its
cell count, bit position, character position, and spiral position.

That hypothesis is meaningful only if the source PNG stores pixels as indexed
color (`IHDR` color type 3) or otherwise carries a palette that indexes the
actual pixel samples.

`tools/gsmg/first_piece_png_palette_provenance_audit.py` parses the raw bytes
of both relevant PNGs:

- the authenticated full Stage-0 image;
- the 350×350 rabbit-grid asset used by the first-piece reconstruction.

The parser verifies every chunk CRC, IHDR field, chunk boundary, terminal
`IEND`, IDAT decompression, PNG scanline filters, and decoded RGBA samples.

## Raw PNG structure

Both files have the same chunk-type sequence:

```text
IHDR, sRGB, gAMA, pHYs, IDAT, IEND
```

Both have:

```text
bit depth:          8
color type:         6 (RGBA truecolor with alpha)
compression:        0
filter method:      0
interlace method:   0
PLTE:               absent
tRNS:               absent
text/EXIF chunks:   absent
bytes after IEND:   0
all chunk CRCs:     valid
```

Their dimensions and hashes are:

| Artifact | Dimensions | SHA-256 |
|---|---:|---|
| Full Stage-0 PNG | 1048×1556 | `38125bbdf1ea58b9b30b075bc6bf71e4089d04bba37098317e47097e2f2a1830` |
| Rabbit asset | 350×350 | `5e8d84b88f8f829428df5d2a8bf36c7268346f169b799ac7570b6223990d204f` |

The repository-root `puzzle.png` is byte-for-byte identical to the full
Stage-0 copy.

## Consequence for palette indexing

PNG color type 6 stores each pixel directly as four channel samples:

```text
R, G, B, A
```

The FEFE marker is decoded from the source bytes as:

```text
FE FE FE FF
```

There is no `PLTE` chunk, and the pixel format does not refer to palette
entries. Therefore FEFEFE has no author-defined palette index in either PNG.

Converting either file to indexed color afterward could assign FEFEFE an
index, but that index would be chosen by the conversion software and its
palette-sorting policy. It would not be provenance-bearing puzzle data.

## Alpha channel

Although color type 6 structurally includes an alpha byte, both complete alpha
planes are constant:

```text
full image:   alpha FF for all 1,630,688 pixels
rabbit asset: alpha FF for all   122,500 pixels
```

Thus FEFEFE is fully opaque and has no distinct alpha value. There is no alpha
selector, alpha bit, transparency index, or hidden `tRNS` state to consume.

## Marker geometry across assets

The decoded marker remains internally consistent:

```text
full image:
  bbox  = x 300..374, y 525..599
  size  = 75×75
  count = 5,625 pixels

rabbit asset:
  bbox  = x 100..124, y 175..199
  size  = 25×25
  count = 625 pixels
```

The full marker coordinates and dimensions are exactly three times the rabbit
asset's, with the expected ninefold pixel-count ratio. Both rectangles are
completely filled with the explicit opaque sample `FEFEFEFF`. This supports
the marker's RGB/location provenance while supplying no new metadata channel.

## Verdict

Reject palette index and alpha as additional FEFE coordinates:

- both PNGs are RGBA8 truecolor, not indexed color;
- neither contains `PLTE` or `tRNS`;
- FEFE is the direct sample `FEFEFEFF`;
- every pixel in both images is fully opaque;
- no text, EXIF, or trailing chunk data supplies a replacement coordinate.

Point 9 is closed. Retain FEFE's explicit RGB value, location, size, and
previously verified bit/character/spiral descriptors. Do not construct or
interpret a palette index from a later format conversion.

## Reproduction

```bash
python3 tools/gsmg/first_piece_png_palette_provenance_audit.py --self-test
```
