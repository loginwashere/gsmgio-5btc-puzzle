---
type: audit
phase: 239
date: 2026-08-11
status: stable
result: positive
disposition: provenance-only
evidence_level: authenticated-artifact
topics:
  - favicon
  - raster-analysis
  - phase-186
related_phases:
  - 186
  - 187
  - 188
  - 240
  - 241
  - 242
script: tools/gsmg/native_favicon_shadow_audit.py
aliases:
  - Phase 239
---

# GSMG Native Favicon Shadow Audit

**Date:** 2026-08-11  
**Status:** Native C9 shadow and rendered CE provenance verified; no selected consumer.

## Why this asset is in scope

Phase 187 compared the served 48x48 `favicon_small.png` with its 3x rendered
copy in the Stage-0 page, but only to explain why one source edge pixel became
the reported `CECECE` block. It did not inventory the native favicon under the
repeated-gray rule or recover the surrounding Telegram provenance.

The complete solver export supplies that missing provenance. In messages
47334-47368, community annotator VoVaM—the source of the later Phase-188
G-shadow clarification—responds to the native favicon comparison with:

```text
47335  favicon_small.png - БИНГО!
47336  You're getting close
47356  Take a fucking look at this ...favicon_small.png
47367  FEFEFE
47368  no one sees beyond FEFEFE
```

This is an explicit community selection of the native asset, not creator
authorship or confirmation.

## Native repeated-gray inventory

The pinned asset is `doc/img/icons/favicon_small.png`, SHA-256
`934f46d6...be1423`, 48x48 RGBA. Among its 233 visible RGB values, exactly one
is grayscale:

```text
native gray RGB:             C9 C9 C9
all C9 RGB pixels:                  264
C9 pixels with nonzero alpha:        96
opaque C9 pixels:                     0
distinct visible alpha values:       72
visible C9 bounding box:       (4,12)..(42,46)
```

The C9 points form fragmented antialiased edge coverage, not a solid hidden
glyph: 56 four-connected components, largest size three. C9 is therefore a
native shadow/edge material, not a second FE-style flat-color anomaly.

The 32x32 favicon control has the same sole gray and the same texture at the
expected lower resolution: 48 visible C9 pixels, zero opaque, 42 alpha values.
The large branding raster also uses C9 extensively. This makes C9 a stable
branding-export ingredient, but not an anomalous color unique to one puzzle
asset.

## Exact C9 to CE provenance

Alpha-compositing every native favicon pixel over the authenticated Stage-0
background `F5F5F5` identifies exactly one source pixel that becomes CE:

```text
source coordinate, zero-based: (27,26)
source RGBA:                    C9 C9 C9 E0
composited RGB:                 CE CE CE
```

Nearest-neighbor 3x enlargement turns it into the observed 3x3/nine-pixel CE
block. Reconstructing the complete 144x144 page logo gives nine CE pixels,
matching the actual Stage-0 crop; the maximum per-channel difference anywhere
in the reconstruction remains one.

The native C9 alpha family composites to 37 grayscale output bytes spanning
204-245. CE is thus a uniquely traceable opacity slice, but not an independent
creator-authored byte. The more source-faithful relationship is:

```text
native C9 shadow --alpha E0 over F5--> rendered CE
```

## SVG and large-logo controls

The served `favicon_small.svg` contains two blue-gradient paths with literal
colors `0B285C`, `2F529D`, `3374E4`, and `679EFD`. It contains no C9 literal,
filter, or shadow declaration. The night SVG behaves the same way with a
different blue palette. The raster PNG's C9 edge is therefore export/render
material absent from the simplified vector definition.

A Phase-186-style exact-layer sweep over the large `G S M G` wordmark is not
discriminating:

```text
visible RGBA colors: G1=449, S=434, M=504, G2=453
layers touching both Gs:                         116
layers touching both Gs but neither S nor M:      42
same-count members of that G-only family:          36
pixel differences between the two G crops:        688
```

C9 itself touches every letter, with visible counts `370/408/240/371` for
`G/S/M/G`. Thus the larger logo is a useful false-positive/base-rate control,
not a clean second G-checksum carrier.

## Bounded alpha stream

The 96 visible native C9 pixels define one finite row-major alpha sequence.
Recording one and two low bits gives:

```text
alpha bytes SHA-256: 3a885335d394a1b2186316b329d371d40caaea4ca4a8f19bfaaeac12cf3e9f1e
1 LSB, 12 bytes:     a1639090a78be66e3d74f366  (5 printable)
2 LSB, 24 bytes:     e603162f6102e12a6ebf48c5fcb69edca7dbbf12f5071e16
                                               (5 printable)
```

Neither has a recognized file/text signature. More importantly, the annotator
selects repeated RGB while the separate LSB/traversal suggestion came from
another community member and was never implemented or creator-confirmed.
Reversal, alternate traversals, SVG-edge registration, decryption, and blob
oracles are therefore not authorized by this audit.

## Metadata correction

The string `2017/07/13-01:06:39` discussed in message 47355 is not an asset
creation timestamp. It is embedded in the generic toolkit identifier:

```text
Adobe XMP Core 5.6-c142 79.160924, 2017/07/13-01:06:39
```

The identical empty XMP packet occurs in both favicon and large-logo exports.
VoVaM's reply “This is the clue” to the timestamp message cannot promote
`7x13`, the date, or the time as authored puzzle data.

## Verdict

Promote the community selection of the native favicon, its unique visible C9
gray, and the exact `(27,26,C9C9C9E0) -> CECECE` composition path as structural
facts. Correct the conceptual model from an unexplained CE byte to a native C9
shadow producing CE at one opacity.

Do not promote C9/CE, the coordinate, alpha E0, or the row-major LSB streams as
passwords, instructions, or cryptographic operands. The large-logo control
shows that G-only exact layers are abundant, while the SVG and smaller favicon
show C9 is ordinary raster-edge branding material. Reopen only with a source
selecting alpha, traversal, or a recognizable independent output.

Reproduce with:

```bash
python3 tools/gsmg/native_favicon_shadow_audit.py --self-test
```
