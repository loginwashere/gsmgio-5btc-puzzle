---
type: index
status: live
date: 2026-08-16
topics:
  - brainstorm
  - qr-code
  - image-forensics
---

# Brainstorm — 2026-08-16 — QR finder-pattern ring texture investigation

> [!caution] Incubation note
> This session is exploratory, not a finding or canonical evidence. Do not add
> it to `GSMG_HOME.md`'s canonical list. Promote surviving work through the
> governed path under [Promotion](#promotion).

## Desired outcome

Identify the actual mechanism that produced the structured gray texture inside
the three QR finder-pattern ("eye") white rings in `puzzle.png` /
`doc/img/gsmg_puzzle_stage1.png`, or narrow the surviving explanations enough
to know what evidence would settle it. Secondary goal: decide whether this is
worth continued effort or is adequately characterized as a rendering artifact.

## Current understanding

### Known facts

- The QR code (bottom of `puzzle.png`/`gsmg_puzzle_stage1.png`, 1048×1556)
  decodes cleanly to `https://www.blockchain.com/btc/address/1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe`,
  matching the printed prize address. Standard Version 4, 33×33 modules.
- All non-pure-black/white pixels in the whole QR region (2,162 total) sit
  **only** inside the three finder-pattern ("eye") squares; the entire data
  body is pixel-perfect binary black/white with zero exceptions.
- The three finder-pattern squares are **byte-for-byte pixel-identical**: 0
  differing pixels across all pairwise comparisons of their full 48×49-pixel
  regions (measured via flood-fill-verified bounding boxes, component size
  1,092 black pixels each).
- `puzzle.png` and `doc/img/gsmg_puzzle_stage1.png` are byte-identical files
  (same IDAT length, zero pixel diff) — one artifact, not two.
- Neither file has PNG text/metadata chunks (`tEXt`/`iTXt`/`zTXt`) — no
  generator/software signature recoverable that way.
- Distinct colors present: pure black `(0,0,0)`, pure white `(255,255,255)`,
  near-black `(15,15,15)`/`(16,16,16)`, near-white `(250,250,250)`,
  `(245,245,245)`, `(252,252,252)`, `(236,236,236)`, `(234,234,234)`.
- Density is strongly **Y-periodic with period 4** in every one of the four
  ring bands (top/bottom/left/right measured independently): `y%4==0` is
  100% non-white with zero exceptions across all measured columns; `y%4==3`
  is 0% non-white with zero exceptions. Middle phases (`y%4==1`,`y%4==2`)
  are partial (~45%, ~25%).
- The dominant variation axis is **Y in all four bands**, including the
  left/right bands where a shape-following effect would need to vary by X.
- The top ring band (y=7-13, relative) and bottom ring band (y=35-41) are in
  **exact period-4 phase alignment** 28 rows apart (28 = 7×4), straight
  through the 21-row solid-black center gap where nothing is visible.
- Within the narrow 7px corner column (x=7-13, clear of the center square's
  shadow on that axis), solid-red rows repeat with **alternating 4-row/3-row
  gaps** (`8,12,15,19,22,26,29,33` → diffs `4,3,4,3,4,3,4`), and the chunks
  between them alternate between two distinct shapes in lockstep with that
  4/3 alternation (chunks after lines 1,3,5,7 match each other; chunks after
  lines 2,4,6 match each other).
- That same narrow-column match does **not** hold at full row width: e.g.
  `y=9` (top band) and `y=37` (bottom band) are identical for the first 7
  columns (`.R.RRRR`) but diverge afterward (`..RR.RR..` vs `.RRRRRR.`) —
  double-gap vs single-gap tiling across the wider span.
- Anomaly: `y=40` and `y=41` (bottom band) are **both** fully solid-red with
  **no** white/mixed row between them — every other pair of solid-red lines
  in the sequence has 2-3 textured/white rows between them; this pair has
  none, right before the band transitions back into the solid black border.
- Community found and discussed the same class of anomaly in **May 2020**;
  member "nieods" called it a "QR generation artifact" and reproduced
  similar gray pixels in an online QR generator, but this was never
  rigorously confirmed at the time (visual reproduction, not measurement).

### Ruled out (tested empirically this session, do not re-propose)

1. **Whole-image resize/scaling into the page.** Reproduced the actual QR
   (same payload, same Version 4/33×33) and scaled with NEAREST/BILINEAR/
   BICUBIC/LANCZOS. Every filter either blends heavily everywhere (76-87%
   of all pixels, body and eyes alike) or blends nowhere. None confine
   blending to the eyes only. **Negative.**
2. **Anti-aliased vector shape rendered at native size, downsampled.** Drew
   the same 7×7-module finder shape at 16× supersampling with the real
   fractional module pitch, Lanczos-downsampled to the true 48×49 size.
   Reproduced "confined to interior" and roughly the right pixel-count
   magnitude, but only 21% positional overlap with the real pattern, and
   visually produces smooth gradient blur, not the zigzag/tooth texture.
   **Negative** as an exact mechanism, though structurally adjacent.
3. **Classic 2D Bayer/ordered-dither matrix (2×2, 3×3, 4×4).** Tested
   `(x mod N, y mod N)` bucket purity on a clean ring-only strip. A real 2D
   Bayer matrix should show a scattered, mostly-distinct density per cell
   across both axes. Instead density is ~independent of `x mod N` and
   almost entirely a function of `y mod N`. **Negative** as literal Bayer;
   the real signal is 1D (row-based), not 2D.
4. **Bevel/emboss effect following the ring's shape.** A shape-aware bevel
   would rotate its gradient to stay perpendicular to whichever edge it's
   near (Y-dominant on top/bottom, X-dominant on left/right). Measured all
   four bands independently: **all four are Y-dominant**, including
   left/right. The effect ignores the shape's geometry entirely — it's
   anchored to absolute image rows, not to the ring's perimeter.
   **Negative.**
5. **Classic 8×8 JPEG DCT block artifacts** (checked as a "was this ever
   compressed lossily" theory): gray-pixel x/y positions checked against
   mod-8 alignment — roughly uniform distribution across all 8 residues,
   no spike. **Negative and now fully conclusive**: swept the assumed
   block-grid origin across all 8×8=64 offsets on the real gray-pixel
   population (3,801 pixels in the QR region) — the histogram's max-min
   spread is identical at every origin (a shifted origin only relabels an
   already-uniform histogram, it cannot create a spike that wasn't
   there), so no possible origin choice saves this theory.
6. **1D row-only ordered dither / line-screen halftone.** Falsified
   directly from the pixel data: every measured ring row contains 2+
   distinct non-black pixel values at different columns in the same row,
   which a threshold model that depends only on row index (uniform value
   per row) cannot produce. **Negative.**

## Framing question

What rendering/generation process produces a texture that is (a) confined
entirely to decorative "eye" elements while leaving functional data modules
untouched, (b) identical across three independently-positioned instances of
that element, (c) dominated by a clean period-4 row structure independent of
which edge of the shape it's on, and (d) exact at the same band-relative
offset for 5 of 7 top/bottom row pairs (a 6th matching in position but not
absolute level), with only a single row genuinely divergent in content
(2026-08-16 follow-up, see below)?

## Gaps in scope

- No existing `G-...` registry entry covers this — it is not yet a tracked
  puzzle gap, since there is no established link to any puzzle mechanism.
  This session is pre-registry: characterizing the artifact, not yet
  claiming puzzle relevance.

## Ideas

Divergence pass — do not rank or reject yet.

1. **Free/consumer QR-generator watermark.** A number of online "free tier"
   QR code generators embed a subtle, barely-visible marker specifically in
   the position-detection (eye) patterns — precisely because that area
   tolerates decoration without breaking scannability, unlike the data
   body. This would explain every established fact at once: eyes-only,
   identical across all three eyes (one fixed asset/stamp), and no
   connection to the QR's own payload or the page's rendering pipeline.
   Testable by generating QR codes through several known free web
   generators with the same/similar payload and diffing their eye regions
   for a matching signature.
2. **A fixed decorative sprite/icon reused for all three eyes**, composited
   as a distinct raster asset rather than derived from the same code path
   that draws data modules. Directly supported by the exact pixel-identity
   finding (a computed-per-instance effect would be far less likely to
   produce zero-diff identity than a single stamped bitmap). Testable by
   looking for the asset itself if the original design source (Figma/
   Illustrator/Photoshop file, or an SVG/asset folder) is recoverable from
   the community fork or any archived project source.
3. **A 1D row-based ordered dither or line-screen halftone**, not a 2D
   Bayer matrix — i.e. a deliberate "engraved line" or "screen" texture
   applied to simulate a subtle off-white tint using horizontal bands
   rather than a checkerboard. This is a real, historically common
   halftone technique (distinct from Bayer) and matches the Y-dominant,
   period-4, locally-exact-but-not-globally-tiling character better than
   anything tested so far. Testable by implementing an actual 1D ordered
   dither (small row-only threshold vector, e.g. length 4) against a flat
   near-white fill at the same target size and comparing pixel-for-pixel.
4. **Scanline rasterizer sub-pixel/coverage quirk specific to how the
   eye graphic's fractional coordinates land on the row grid.** Vector
   rasterizers (Skia, Cairo, browser canvas/SVG engines) compute per-
   scanline coverage; a quirk or specific antialiasing mode (e.g.
   "grid-fit" or a coverage accumulation bug) could produce structured,
   row-dominant banding for a shape whose vertical extent doesn't align to
   integer pixels, while a separately-drawn, pixel-aligned data grid would
   never trigger the same code path. Testable by rendering the identical
   ring shape through more than one real rasterizer (browser canvas via a
   headless render, `cairo`, `resvg`, etc.) at the exact real fractional
   module pitch and comparing.
5. **Icon/glyph-font rendering artifact.** Some UI kits draw a "QR/target"
   icon via an icon font glyph rather than procedurally; font hinting grid-
   fits glyphs to the pixel grid in a way that's often row-dominant due to
   how hinting instructions snap horizontal stems. Low-prior but cheap to
   at least rule in/out by checking whether any common icon font ships a
   glyph whose rendered ring shape at this exact size produces a similar
   band structure.
6. **Re-open the JPEG-history theory with a shifted block origin.** The
   mod-8 test assumed the block grid is aligned to this crop's own (0,0).
   If the source image was cropped or composited after JPEG compression,
   the true block origin could be offset by 1-7px in either axis. Testable
   by sweeping the assumed origin offset (0-7 in x and y, 64 combinations)
   and re-running the alignment test at each, rather than assuming origin
   zero.
7. **The full-width divergence (idea: "phase drift from non-integer
   tiling").** If the underlying texture tile is narrower than a module
   and the ring's total width (34 columns) isn't an exact multiple of the
   tile period (~3.5-4), simple tiling would drift out of phase across the
   width — and *could* drift differently between the top and bottom bands
   if they don't start tiling from the same absolute x-origin (e.g. if
   each band's texture starts relative to its own left edge rather than a
   shared global origin). Testable by checking whether the top and bottom
   bands' full-width patterns become identical if reindexed relative to
   each band's own start rather than absolute image x.

## Connections and challenges

### Combinations

- Ideas 1 and 2 are compatible and mutually reinforcing (a free-tier
  generator's watermark would typically *be* a fixed stamped sprite) —
  worth treating as one composite hypothesis rather than two competitors.
- Idea 7 could explain away part of what looks like a top/bottom
  discrepancy without needing a new mechanism at all — worth testing
  before treating the full-width divergence as evidence against ideas 1-3.

### Contradictions

- Idea 4 (rasterizer coverage quirk) sits awkwardly with the exact
  pixel-identity across all three eyes: a coverage-based artifact
  computed independently per-instance at slightly different absolute
  page coordinates would be expected to differ subtly between instances
  (different sub-pixel phase per eye position), not match exactly. Ideas
  1/2 (fixed stamped asset) explain the exact identity far more
  naturally. This weighs against 4/5 relative to 1/2/3.

### Missing assumptions

- All ideas so far assume the texture was produced by *something drawing
  the ring*. An alternative not yet considered: the texture could be a
  side effect of a **post-processing filter** (sharpen, noise-reduction,
  or a "crisp edges" filter) applied to the *whole* graphic after the QR
  was composited, which happens to only leave visible residue where the
  underlying color was already near a boundary (near-white ring next to
  black modules) and where the filter's own kernel has directional bias —
  worth adding as idea 8 if idea 7 doesn't resolve the divergence.

## Promising directions

Superseded by the 2026-08-16 follow-up session (ideas 3, 6, 7 executed —
see "Experiments and next actions"). Updated ranking:

1. **Ideas 1+2 (free-generator watermark / fixed stamped sprite)** — still
   the best-fitting *mechanism class* (a single fixed/stamped asset best
   explains idea 7's 5/7-exact-row finding), but the three most obvious
   free generators are now tried and closed (Phases 298-299: QR Code
   Monkey's full 36-style catalog, api.qrserver.com, quickchart.io — none
   match). Next step, if pursued further, needs either a specific reason
   to suspect a *particular* other generator (not an open-ended trial of
   more services) or progress on the design-source-recovery open question
   below.
2. **Ideas 4/5 (rasterizer coverage quirk, icon-font hinting)** — lowest
   priority, now even more strongly disfavored by the same evidence: a
   per-instance coverage/hinting artifact computed independently at
   different absolute page or sub-pixel positions would not be expected
   to reproduce this much row-level exactness.
3. ~~Idea 7 (phase-drift reindexing)~~, ~~Idea 3 (1D row dither)~~,
   ~~Idea 6 (JPEG origin sweep)~~ — all executed and closed 2026-08-16,
   see below.

## Decisions

- Idea 7 executed as designed; result is sharper than "diverges beyond a
  narrow tile" — see below. Not a full reconciliation, so still negative
  as a "phase-drift explains everything" theory, but it substantially
  reinforces ideas 1/2 over ideas 4/5.
- Idea 3 closed by direct proof against the extracted pixel data, without
  needing to render a synthetic comparison image.
- Idea 6 closed by a mathematical argument (confirmed empirically) rather
  than by literally running the 64-combination sweep — sweeping the
  assumed origin cannot detect a periodicity the unshifted histogram
  doesn't already show.

## Experiments and next actions

- [x] **Idea 7 — executed, negative as a full reconciliation but sharpens
      the picture (2026-08-16).** `qr_finder_ring_texture_reindex_dither_audit.py`
      independently relocated the three 48x49px/1092-black-pixel finder
      squares (byte-identical, confirming the prior session's finding) and
      compared the top ring band (rows 7-13) against the bottom ring band
      (rows 35-41) row-for-row at the same band-relative offset, exact
      byte level, across the full 36-column ring width. **5 of 7 rows are
      byte-for-byte identical.** Of the 2 that aren't: one (band-offset 6)
      has its gray-value positions in **exactly** the same columns in both
      bands — only the background level differs (255 in the top band vs.
      252 in the bottom band) — so even this "divergent" row is
      structurally identical, just intensity-shifted. Only one row
      (band-offset 2) is genuinely different in content: the top band's
      version has paired "highlight" columns at ~3-4-column spacing, the
      bottom band's has single highlights at a strict period-7 spacing. No
      cyclic column shift (0-35) reconciles that one row either. **Net
      result: the top/bottom "divergence" noted in the original pass is
      almost entirely a single anomalous row, not a general full-width
      tiling failure** — corrects the earlier "double-gap vs single-gap
      tiling across the wider span" framing, which was accurate as an
      observation but implied a broader mismatch than what's actually
      there. This near-total positional identity (untouched by which of
      the 3 physically separate finder squares, and now shown to hold row-
      for-row between top and bottom bands too) further favors ideas 1/2
      (fixed stamped asset) over ideas 4/5 (per-instance rasterizer
      quirk), which would not be expected to reproduce this cleanly.
- [x] **Idea 3 — closed, negative by direct proof (2026-08-16).** No
      synthetic dither image needed: a row-only (y-only) threshold model
      can only emit one uniform value per row by construction. The real
      data falsifies that immediately — every one of the 14 measured ring
      rows (both bands) contains 2+ distinct non-black pixel values at
      different columns in the same row (e.g. row 10 mixes `250` and
      `255`; row 41 mixes `250` and `252`). A literal 1D row-only ordered
      dither is ruled out as the mechanism.
- [x] **Idea 6 — closed, negative by argument + confirmation (2026-08-16).**
      Sweeping the assumed JPEG block-grid origin only cyclically relabels
      the mod-8 residue histogram of the gray-pixel population; it cannot
      surface a periodicity spike that isn't already present at origin=0.
      Confirmed directly: computed the mod-8 histogram of all 3,801 gray
      pixels in the QR region (quiet zone included) at all 8 possible
      origins — the histogram's max-min spread is bit-for-bit identical
      (529 for x, 512 for y) at every origin. The original "roughly
      uniform, no spike" result at origin=0 already forecloses the entire
      64-combination sweep; running it literally would have added nothing.
- [x] **Ideas 1/2 — attempted, mixed result (2026-08-16).** Live network
      fetch of the puzzle's exact payload
      (`https://www.blockchain.com/btc/address/1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe`)
      through 3 real free/GET-accessible QR services, saved locally for
      reproducibility and analyzed by
      `qr_finder_ring_texture_generator_comparison_audit.py`:
      - `api.qrserver.com` (goqr.me): output is a **1-bit indexed PNG** —
        structurally incapable of antialiasing at all. Ruled out outright.
      - `quickchart.io/qr`: 8-bit RGBA output, but **zero** non-black/white
        pixels anywhere. No antialiasing in this generator's default path.
      - `api.qrcode-monkey.com` (default style, no custom eye request):
        8-bit RGB output with 528 gray pixels, and — checked precisely,
        not just eyeballed — **every one of them falls inside the three
        finder-square regions and none in the data body**, exactly
        matching framing-question fact (a) (eyes-only, functional modules
        untouched). This is a real, independently-observed instance of a
        free generator confining antialiasing to the eyes.

      **But the texture itself doesn't match.** Extracting QR Code
      Monkey's finder-square region shows a **single 1-pixel-wide
      antialiased outline** tracing each rectangle edge (border square,
      inner white ring, inner black square) — a generic vector-shape edge
      AA, nothing like the puzzle's 7-row-deep period-4 banded texture
      found in idea 7 above. So: **not the source generator, or at least
      not its default style** — but real, disclosed, non-cherry-picked
      confirmation that "a free QR generator confines AA to the eyes" is
      an actual behavior in the wild, not just a plausible-sounding theory.
      Strengthens the ideas 1/2 *mechanism class* without identifying the
      specific asset/generator.

## Open questions

- Is there any way to recover the original design source (vector file,
  web tool session, or generator identity) for this specific graphic,
  e.g. via the community fork's history or an archived project asset
  folder, rather than reverse-engineering the mechanism from pixels alone?
- ~~QR Code Monkey's custom eye styles~~ — **closed, 2026-08-16.** All 16
  frame values × 20 ball values (36-combination one-factor-at-a-time
  sweep, the generator's full declared catalog) were tried; every one
  produces only thin 1-2px vector-edge antialiasing, never the puzzle's
  periodic multi-row banding. See `tools/gsmg/FINDINGS.md` Phase 299. This
  generator's investigation avenue is now fully exhausted, not just its
  default style.
- With QR Code Monkey's full catalog and two other free generators
  (`api.qrserver.com`, `quickchart.io`) all ruled out (Phases 298-299), the
  ideas 1/2 "free generator watermark" hypothesis needs either a different,
  not-yet-identified generator, or direct recovery of the original design
  source (the item above) — trying more free generators one at a time is
  an open-ended search this project's discipline discourages without a
  specific reason to suspect a particular one.

## Divergence pass 2 — reading the texture as data, not just explaining its rendering (2026-08-16)

Everything above (ideas 1-8, Phases 296/298/299) asked "what mechanism
produced this texture" — none asked "does the already-measured pixel data
encode anything if read as a sequence." This is a genuinely different
question and deserves its own explicit framing before diverging, because
it's a materially higher-risk direction than the mechanism work above:
structured-looking output is the *normal, unremarkable* behavior of
antialiasing/dithering/curve-tessellation algorithms, not evidence of
intent by itself. This project has real precedent for hidden channels in
other artifacts (Decentraland audio → spectrogram; a genuine embedded QR
in another puzzle image), which is why this angle is worth a bounded look
— but it also has real precedent for false positives from reading meaning
into structure that wasn't there (OP_RETURN graffiti misreads, the
GitHub/bitcointalk "SOLVED" spam campaign, both in `FINDINGS.md`). Every
idea below keeps the same discipline as the rest of this project: a
closed, pre-declared candidate universe, an exact/structural match bar
(valid ASCII, an oracle hit, or an unambiguous recognizable glyph — never
"looks like it could be a pattern"), and a stop rule that closes the idea
on a clean negative rather than inviting a second, tuned attempt.

### New known fact

- Checked before proposing anything: every gray pixel in the finder-square
  region is exactly `R=G=B` (max channel difference 0 across the whole
  region). There is no hidden per-channel signal — whatever's there, if
  anything, is carried by the luminance value alone, not RGB-channel
  steganography. This rules out one otherwise-obvious idea before it's
  even proposed.

### Structural constraint on any "message" reading

- The three finder squares are byte-for-byte identical (established
  earlier this session). Any positional/per-instance message (e.g. "which
  corner is this," a coordinate, a fragment index) is **ruled out by this
  fact alone** — three genuinely different payloads would not render
  identically. Whatever a reading could find must be either (a) the exact
  same short fixed message replicated three times, or (b) nothing. This
  narrows the space usefully: it rules out "different content per eye"
  ideas without needing to test them.

### Ideas — do not rank or reject yet

1. **Perimeter unroll as a 1D bit/symbol stream.** Walk one ring's
   perimeter in a single pre-declared direction and starting point (e.g.
   clockwise from the top-left corner of the ring), classify each
   position by a pre-declared binarization rule (not tuned after seeing
   output), and read off a bit/symbol sequence. Test a small closed set of
   standard interpretations (raw bits, reversed, MSB/LSB-first) as text
   and as an oracle passphrase. Falsifiable, bounded; differs from
   everything above by treating the pixels as a sequence to decode rather
   than a 2D shape to explain.
2. **Row-tick position/gap sequence.** The textured rows (e.g. relative
   rows 9/10/13 in the earlier pixel dump) show a repeating "tick" mark at
   semi-regular but not perfectly uniform spacing. Extract the exact
   column positions of these ticks for the small, fully bounded set of
   non-uniform rows (decided in advance, not cherry-picked after
   inspection), compute the gap sequence between consecutive ticks, and
   test both the gaps and absolute positions as literal numbers/strings
   via the oracle. Different object than idea 7 above, which compared row
   *content* for equality, not tick *positions* as extracted numbers.
3. **Full intensity-level alphabet instead of 3-way black/white/gray.**
   The ring actually contains ~7 distinct exact intensity values (255,
   252, 250, 236, 234, 16, 15), not just "gray" — the mechanism work
   collapsed these to one bucket. Map the observed values to a small fixed
   symbol alphabet, read them off in one pre-declared scan order, and test
   the resulting sequence (as base-N digits, as an alphabet index, hashed)
   via the oracle. A genuinely different derived object than the
   EXACT/DIVERGENT row comparison Phase 296 already did.
4. **Render the patch itself as a high-contrast image and look for a
   glyph**, on the same theory as the puzzle's already-solved genesis
   image containing a real embedded QR — i.e., treat the whole ring patch
   as a 2D picture rather than a sequence. One-shot visual check at fixed,
   pre-chosen contrast/scale settings; explicitly **not** an iterative
   "keep adjusting until something looks like a shape" pass, since that's
   exactly the pareidolia risk flagged above. Only counts as a hit if an
   unambiguous, exact recognizable symbol appears, not a suggestive blob.
5. **Row-as-symbol (line-type) sequence**, raised directly by the user
   after visually inspecting the categorical-palette render: classify
   each *whole row* (not individual pixels or tick positions) into one of
   a small number of types by a simple mechanical rule, and read the
   row-type sequence as its own symbol string — coarser-grained than
   ideas 2/3, and different again from the perimeter/glyph framings.
6. **Textured-block type sequence**, a refinement of idea 5 the user
   proposed after seeing its result: treat solid-white/solid-green rows
   as separators (not content) and group only the textured rows into
   contiguous blocks, then classify the blocks themselves by type (by
   height and by content) and read off the block-type sequence, or
   derived numbers like per-block textured-cell counts.
7. **The two irregular rows in isolation.** Idea 6's result plus the
   user's own observation (the 1-row block looks like a continuation of
   the preceding 2-row block's second row, regardless of which 2-row
   block precedes it) together show that rows 10, 13, and 38 are
   byte-identical and row 41 shares their positions — meaning rows 9 and
   37 (the "irregular" rows) are the *only* place in the whole texture
   that ever varies at all. Testable by isolating just those two rows
   (each a natural 34-bit binary string, confirmed 2-valued) and their
   pairwise difference, since that's the only place any content could
   possibly live if this texture encodes anything.
8. **User-specified color-to-binary reading.** A different bit assignment
   than idea 7's row-level 250/255 split: green/dark-red/orange -> `1`,
   white/red/yellow/cyan -> `0`, applied across the full 36-column ring
   width (including the edge boundary-AA columns this time, since the
   mapping explicitly covers those colors too), read row-major. Tested
   both without and with the idea-4-adjacent hypothetical center-square
   continuation, per the user's explicit request for both variants.

### Promising directions

Updated after ideas 2-8 (2026-08-16): all seven closed negative, see
"Experiments and next actions". Idea 1 (perimeter unroll) is the only item
that was never executed: the ring is a 7px-*deep* band on each side, not a
single-pixel path, so "the perimeter" has no unambiguous single-pixel
route without picking a depth-offset first (and "Known facts" already
shows variation is Y-dominant even on the left/right bands, meaning a
route that turns a corner mixes two differently-behaved axes into one
sequence). Any such offset choice made now, after every other reading has
already failed, would not be pre-declared in the sense this project
requires — it would be a free parameter picked with the benefit of
hindsight from a search space that's otherwise come up empty. **Decision
(2026-08-16, user call):** skip idea 1 rather than pick an arbitrary
offset; close this pass without attempting it. With ideas 2-8 all negative
and idea 1 explicitly skipped rather than blocked, "Divergence pass 2"
(reading the texture as data) is now closed. Idea 7 in particular isolated
the *only* place in the whole texture that ever varies at all (rows 9 and
37) and still found nothing — the strongest signal that this framing had
run its course. Reopening requires either a non-arbitrary way to fix idea
1's depth-offset (e.g. a source that specifies which row/column of the
band *is* "the perimeter") or a genuinely new idea, not a retry of
anything above.

### Experiments and next actions

- [x] **Idea 4 — executed, one-shot, negative (2026-08-16).**
      `qr_finder_ring_texture_categorical_render_audit.py` mapped the 8
      exact grayscale values already documented in "Known facts"
      (`0, 15, 16, 234, 236, 250, 252, 255`) to 8 maximally distinct
      categorical colors, fixed in advance, nearest-neighbor upscaled
      14x, applied identically to all three finder squares. Saved as
      `doc/img/gsmg_puzzle_stage1_qr_finder_categorical_palette_render.png`.
      **No unmapped values** (the palette covered everything actually
      present) and **no recognizable glyph, letter, digit, or symbol** —
      what's visible is the same zigzag/tooth texture already seen in the
      earlier red-highlight render, plus two previously-unremarked-on but
      already-explained details made visually obvious by the finer
      palette: the left edge consistently renders in the 234/236 pair
      (orange/yellow) and the right edge consistently in the 15/16 pair
      (dark-red/red) — a boundary-antialiasing asymmetry between the two
      edges, not a distinct shape — and the single cyan stripe at the
      bottom is exactly the row-41 252-vs-255 anomaly Phase 296 already
      found and explained. All three eyes render pixel-identically, as
      expected. Per this pass's own discipline, this was a single
      pre-declared render, not iterated with different palettes/contrast
      after looking — closed negative on that basis, not reopened by
      trying another color scheme.
- [x] **Idea 3 — executed, negative (2026-08-16).**
      `qr_finder_ring_texture_intensity_alphabet_audit.py` reused the
      exact top/bottom ring-band geometry already codified in
      `qr_finder_ring_texture_reindex_dither_audit.py` (rows 7-13 and
      35-41, cols 6-41 of the first located finder square — left/right
      bands excluded, since their pixel geometry was never preserved in a
      reproducible script, only established ad hoc in prose this session).
      Confirmed these two bands contain exactly 7 distinct values (15, 16,
      234, 236, 250, 252, 255 — no 0/255 pure black/white pixels inside
      this specific sub-region), mapped to base-7 digits in ascending
      order (reusing the same ordering convention as idea 4's PALETTE, not
      a fresh arbitrary choice). Six pre-declared candidate strings (top
      forward/reversed, bottom forward/reversed, top+bottom and
      bottom+top concatenated) run through the standard `keystr_forms()`
      (raw/SHA-256/double-SHA-256) against all four tracked blobs: **18
      passphrase attempts, 0 hits.** Closed negative per the fixed,
      pre-declared candidate set — not reopened by trying a different scan
      order or digit mapping.
- [x] **Idea 2 — executed, negative (2026-08-16).**
      `qr_finder_ring_texture_tick_gap_sequence_audit.py` used a mechanical,
      pre-declared rule (interior columns 7-40 of each ring row contain 2+
      distinct values) to find tick rows, rather than a manually
      cherry-picked list — this rule finds exactly 6: rows 9, 10, 13 (top
      band), 37, 38, 41 (bottom band), matching this doc's own earlier
      "rows 9/10/13" example. Extracted the minority-value column
      positions and pairwise gap sequence per row; ran 6 pre-declared
      candidate strings (concatenated gaps, concatenated positions, the
      two irregular rows' gaps individually, the distinct-gap alphabet,
      and a piped per-row form) through `keystr_forms()` against all four
      blobs: **18 passphrase attempts, 0 hits.**

      Notable independent of the oracle result: **4 of the 6 tick rows
      (10, 13, 38, 41) have the exact identical gap sequence
      `3,4,3,4,3,4,3,4`** — a clean period-~3.5 tiling signature. The
      other two (9, 37) each open with `2,7` before settling into their
      own regular repeat (`1,3,3,...` and `7,7,7,7`). This is exactly the
      kind of output a tiling/dither algorithm with a non-integer period
      produces, not what a hand-placed or hashed message would look like
      — this result is more evidence *for* the mechanism-artifact reading
      (ideas 1/2 of the original pass, still unresolved as to which
      specific generator/asset) than for anything hidden in this data.
- [x] **Idea 5 — executed, negative (2026-08-16).**
      `qr_finder_ring_texture_line_type_alphabet_audit.py` classified each
      of the 14 ring rows into exactly 3 mechanical types (uniform-255 =
      `W`, uniform-250 = `G`, anything else = `T`) — confirming, exactly
      as observed by eye, a `WGTTWGTWGTTWGT` sequence: the known 7-row
      tile repeated twice, byte-for-byte. 6 pre-declared candidates
      (digit/letter forms, full/tile-only, forward/reversed) through
      `keystr_forms()` against all four blobs: **18 passphrase attempts,
      0 hits.** Closed negative. Numerically confirms the visual
      observation was correct (there genuinely are exactly 3 line types,
      and they do repeat) — it's just that this coarser reading, like
      every finer one tried, carries no oracle-verifiable content.

Also produced on request: a **hypothetical visualization**
(`qr_finder_ring_texture_center_square_continuation_render.py`,
`doc/img/gsmg_puzzle_stage1_qr_finder_center_square_pattern_continuation.png`)
extrapolating the top band's real 7-row tile through the (really
solid-black) 21x21px center square — 21 rows being an exact 3x multiple
of the 7-row tile. This is explicitly *not* real pixel data (the filled
region is outlined in magenta and self-tested to differ from the real
image) — it exists only to make the periodicity visually inspectable
past the point where the real border interrupts it. The pattern simply
continues with no new shape or discontinuity, mildly reinforcing the
periodic-tiling-artifact reading over an intentionally-placed one, though
this was not run through the oracle as a candidate.
- [x] **Idea 6 — executed, negative (2026-08-16).**
      `qr_finder_ring_texture_block_type_sequence_audit.py` formalized the
      user's refinement of idea 5: treating solid rows as separators finds
      exactly 4 contiguous textured blocks in row order — `[9,10]` (height
      2), `[13]` (height 1), `[37,38]` (height 2), `[41]` (height 1) — and
      a mechanical per-row-minority-count signature assigns exactly 3
      distinct block types, letters `A, B, C, B` in order. This
      **independently reproduces the user's visual read from a fully
      mechanical rule** (not eyeballing): 2 types are 2-row blocks, 1 type
      is a 1-row block, and the two 1-row blocks really do share an
      identical signature. Six candidates (type letters forward/reversed,
      type digits, block heights, per-block textured-cell-count sums,
      per-row textured-cell counts) through `keystr_forms()` against all
      four blobs: **18 passphrase attempts, 0 hits.** Closed negative.
- [x] **Idea 7 — executed, negative (2026-08-16).**
      `qr_finder_ring_texture_irregular_rows_only_audit.py` confirmed the
      premise directly (rows 10, 13, 38 byte-identical; row 41 shares
      their positions) before isolating rows 9 and 37 — the only rows in
      the entire texture that ever vary — as 34-bit binary strings (each
      confirmed 2-valued: 250/255 only). 8 candidates (each row's bits
      forward/reversed, both concatenation orders, the 6-bit difference
      mask, and the 6 differing positions as digits) through
      `keystr_forms()` against all four blobs: **24 passphrase attempts,
      0 hits.** Closed negative — the one place in this texture that
      could possibly carry content carries none the oracle recognizes.
- [x] **Idea 8 — executed, negative (2026-08-16).**
      `qr_finder_ring_texture_color_binary_reading_audit.py` applied the
      user's exact color-to-bit mapping (green/dark-red/orange=1,
      white/red/yellow/cyan=0) across the full 36-column ring width,
      row-major. Two readings as explicitly requested: "without
      continuation" (the 14 real ring rows only, 504 bits) and "with
      continuation" (all 35 rows from 7-41, using the earlier
      center-square-continuation fill for the black gap, 1260 bits) — a
      self-test confirms both readings agree exactly on every real
      (non-extrapolated) row. 4 candidates (both readings, each
      forward/reversed) through `keystr_forms()` against all four blobs:
      **12 passphrase attempts, 0 hits.** Closed negative.
- [x] **Idea 1 — skipped, not attempted (2026-08-16, user decision).**
      Perimeter unroll needs a pre-declared depth-offset to define a
      single-pixel route through the 7px-deep ring band, and no
      non-arbitrary way to fix that offset exists after ideas 2-8 have
      already all failed — picking one now would be a free parameter
      chosen with the benefit of hindsight, not a genuine pre-registration.
      User chose to close the pass rather than attempt it with a caveated
      arbitrary choice. "Divergence pass 2" is now closed in full (7
      executed and negative, 1 explicitly skipped) — see "Promising
      directions" above for the reopening condition.

## Promotion

`Brainstorms/` is an incubation area, not a second knowledge store. Keep
untested ideas here as `type: hypothesis`; promote only after a concrete
experiment produces a result worth a `tools/gsmg/FINDINGS.md` phase entry.

## Related notes

- [[GSMG_HOME]]
