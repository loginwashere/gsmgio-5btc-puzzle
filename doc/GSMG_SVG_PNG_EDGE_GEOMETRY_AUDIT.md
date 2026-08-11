---
type: audit
phase: 242
date: 2026-08-11
status: closed-negative
disposition: provenance-only
topics:
  - favicon
  - raster-analysis
  - phase-186
related_phases:
  - 186
  - 187
  - 239
script: tools/gsmg/svg_png_edge_geometry_audit.py
aliases:
  - Phase 242
---

# GSMG SVG/PNG edge-geometry audit

Date: 2026-08-11  
Phase: 242  
Status: all native C9 pixels explained by registered SVG contours; no spatial residue

## Question

Phase 239 showed that `favicon_small.svg` contains no literal C9 color while
the native 48x48 PNG contains 96 visible C9 pixels. Absence from the SVG color
palette does not itself make C9 hidden data: a raster export can attach a
matte/shadow color to ordinary vector boundaries.

The bounded test is therefore geometric. After registering the SVG artwork to
the PNG, do all C9 pixels lie within the same contour-error envelope as
ordinary non-C9 antialias pixels, or does any C9 remain away from the expected
SVG paths?

## Registration without C9

The assets do not share a canvas: the SVG is 55x60 while the PNG is 48x48 and
cropped/scaled differently. Literal coordinate comparison would be invalid.
The audit parses the SVG's two M/L/V/Z paths into 19 line segments and freezes
an affine registration fitted only to PNG pixels with alpha at least 250.

This fit cannot use the target channel: all visible C9 pixels have alpha below
255, and zero enter the opaque registration mask.

At native resolution the transformed vector body gives:

```text
predicted SVG-body pixel centers: 1122
opaque PNG target pixels:         1112
intersection / union:             1101 / 1133
binary IoU:                       0.971756
disagreements:                    32 pixels
```

The fitted transform is effectively scale-and-translation. Its off-diagonal
terms are below 0.003, so the match does not depend on a material rotation or
shear.

## Matched edge envelope

For every pixel, distance is measured from its center to the nearest
transformed SVG segment. The control envelope is not chosen from C9: it is the
maximum distance among the PNG's 135 ordinary visible non-C9 silhouette-edge
pixels.

```text
ordinary non-C9 edge maximum: 1.321956 px
native C9 maximum:            1.004656 px
C9 pixels inside envelope:    96 / 96
C9 pixels outside envelope:    0 / 96
```

Every C9 pixel also has a four-neighbor belonging to the non-C9 image body,
and every C9 pixel has an eight-neighbor in the opaque core. They are not
detached islands. Nearest-segment attribution spans both SVG shapes: 85 C9
pixels trace the main path and 11 trace the inset path.

This is stronger than merely observing that C9 looks edge-like. The vector
registration was fixed without C9, ordinary blue antialias pixels establish a
looser matched envelope, and all C9 points fall inside it.

## Independent size control

The separately served 32x32 `favicon.png` repeats the behavior after its own
opaque-body registration:

```text
visible C9 pixels:                       48
adjacent to non-C9 by four-neighborhood: 48
adjacent to opaque body by eight-neighborhood: 48
maximum SVG-segment distance:            1.266629 px
```

The lower-resolution export therefore carries the same contour-bound C9
material. It is not unique to the 48x48 asset or the Stage-0 compositing path.

## Verdict

**Close C9 as a hidden spatial channel.** All 96 visible native C9 pixels are
accounted for by ordinary SVG-derived boundaries under a registration that
does not consume C9. There is zero off-contour residue.

Retain C9 and the C9/E0-to-CE compositing path as exact raster provenance, but
do not treat the C9 layout, components, coordinates, alpha order, or CE slice
as an authored payload. No traversal, decoding operation, credential, or blob
oracle follows.

Reopen only if an independently sourced rendering leaves a stable off-contour
residue, or primary evidence explicitly selects raster alpha/edge traversal.

Reproduce with:

```bash
python3 tools/gsmg/svg_png_edge_geometry_audit.py --self-test
```
