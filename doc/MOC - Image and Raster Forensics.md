---
type: moc
topics:
  - raster-analysis
  - stage0
  - favicon
  - first-piece
---

# MOC — Image and Raster Forensics

Pixel-level, color-layer, and geometry work on the puzzle's authenticated
images: the Stage-0 grid/footer, the GSMG favicon/logo family, and the
"first piece" 24-cell grid.

## Stage-0 footer `#383838` thread

- [GSMG_NATIVE_FAVICON_SHADOW_AUDIT](GSMG_NATIVE_FAVICON_SHADOW_AUDIT.md) — Phase 239, native C9 shadow -> rendered CE provenance.
- [GSMG_SHADOW_MACRO_FAED_GEOMETRY_AUDIT](GSMG_SHADOW_MACRO_FAED_GEOMETRY_AUDIT.md) — Phase 240, nested macro-length calibration.
- [GSMG_FAVICON_WAYBACK_CHRONOLOGY_AUDIT](GSMG_FAVICON_WAYBACK_CHRONOLOGY_AUDIT.md) — Phase 241, sole 2019-04-28 capture.
- [GSMG_SVG_PNG_EDGE_GEOMETRY_AUDIT](GSMG_SVG_PNG_EDGE_GEOMETRY_AUDIT.md) — Phase 242, C9 closed as a spatial channel.

(Note: `doc/GSMG_..._AUDIT.md` files above cover the *native favicon* thread.
The original `#383838` Stage-0 footer discovery itself is Phase 186 in
[tools/gsmg/FINDINGS.md](../tools/gsmg/FINDINGS.md) — see
[GSMG_PHASE_INDEX](GSMG_PHASE_INDEX.md) for the direct anchor; it predates
this documents' individual-audit convention and has no standalone doc file.)

## First-piece (24-cell yellow/blue grid)

- [GSMG_FIRST_PIECE_PIXEL_BRAINSTORM](GSMG_FIRST_PIECE_PIXEL_BRAINSTORM.md)
- [GSMG_FIRST_PIECE_COLOR_RECONSTRUCTION](GSMG_FIRST_PIECE_COLOR_RECONSTRUCTION.md)
- [GSMG_FIRST_PIECE_PNG_PALETTE_PROVENANCE_AUDIT](GSMG_FIRST_PIECE_PNG_PALETTE_PROVENANCE_AUDIT.md)
- [GSMG_FIRST_PIECE_PRIME_SUM_VERIFICATION](GSMG_FIRST_PIECE_PRIME_SUM_VERIFICATION.md)
- [GSMG_FIRST_PIECE_BITPLANE_VERIFICATION](GSMG_FIRST_PIECE_BITPLANE_VERIFICATION.md)
- [GSMG_FIRST_PIECE_BORDER_RASTER_SCAN_AUDIT](GSMG_FIRST_PIECE_BORDER_RASTER_SCAN_AUDIT.md)
- [GSMG_FIRST_PIECE_EVENT_RAIL_PRESERVATION_AUDIT](GSMG_FIRST_PIECE_EVENT_RAIL_PRESERVATION_AUDIT.md)
- [GSMG_FIRST_PIECE_SHADOW_COLUMN_RAIL_AUDIT](GSMG_FIRST_PIECE_SHADOW_COLUMN_RAIL_AUDIT.md)
- [GSMG_FIRST_PIECE_EVEN_ODD_ALPHABET_GATE_AUDIT](GSMG_FIRST_PIECE_EVEN_ODD_ALPHABET_GATE_AUDIT.md)
- [GSMG_FIRST_PIECE_BATCH_REBUS_GATE_AUDIT](GSMG_FIRST_PIECE_BATCH_REBUS_GATE_AUDIT.md)
- [GSMG_FIRST_PIECE_CEFE_CHECKERBOARD_GATE_AUDIT](GSMG_FIRST_PIECE_CEFE_CHECKERBOARD_GATE_AUDIT.md)
- [GSMG_FIRST_PIECE_OVERLAY_DNA_RGB_GATE_AUDIT](GSMG_FIRST_PIECE_OVERLAY_DNA_RGB_GATE_AUDIT.md)
- [GSMG_FIRST_PIECE_MATRIX_PRODUCT_AUDIT](GSMG_FIRST_PIECE_MATRIX_PRODUCT_AUDIT.md)
- [GSMG_FIRST_PIECE_SECOND_MATRIXSUMLIST_AUDIT](GSMG_FIRST_PIECE_SECOND_MATRIXSUMLIST_AUDIT.md)
- [GSMG_FIRST_PIECE_GGN_DISTINCTIVENESS_AUDIT](GSMG_FIRST_PIECE_GGN_DISTINCTIVENESS_AUDIT.md)
- [GSMG_FIRST_PIECE_HAMMING_CONTROL_AUDIT](GSMG_FIRST_PIECE_HAMMING_CONTROL_AUDIT.md)

## SalPhaseIon page presentation

- [GSMG_SALPHASEION_PRESENTATION_BINDING_AUDIT](GSMG_SALPHASEION_PRESENTATION_BINDING_AUDIT.md)
- [GSMG_SALPHASEION_RESPONSIVE_WRAP_AUDIT](GSMG_SALPHASEION_RESPONSIVE_WRAP_AUDIT.md)

## Method note

The exact-color/pixel-layer technique used throughout this thread is only
methodologically valid on **lossless, discrete-palette sources** (PNG/SVG).
It has been explicitly checked and found inapplicable or negative on: the
GSMG icon PNGs (no marker reuse), and a lossy JPEG Decentraland screenshot
(compression noise; superseded by fetching the live scene source instead of
scanning the render).
