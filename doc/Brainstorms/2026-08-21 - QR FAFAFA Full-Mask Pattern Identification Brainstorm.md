---
type: hypothesis
status: live
date: 2026-08-21
topics:
  - brainstorm
  - qr-code
  - image-forensics
  - pattern-identification
  - steganalysis
---

# QR `#FAFAFA` full-mask pattern identification brainstorm

> [!caution] Incubation note
> This session is exploratory, not a finding or canonical evidence. Do not add
> it to `GSMG_HOME.md`'s canonical list. Promote surviving work through the
> governed path under [Promotion](#promotion).

## Desired outcome

Treat the exact `#FAFAFA` layer in one complete QR finder square as a new,
well-defined object and determine which analysis can best distinguish among:

1. a generator/rendering fingerprint;
2. a repeated decorative raster tile;
3. an intentionally encoded but replicated message; and
4. ordinary structured antialiasing with no payload.

The immediate goal is a ranked portfolio of small, falsifiable experiments,
not another unconstrained transform search.

## Current understanding

### Established by Phases 296--306

- The three 48x49-pixel finder squares are byte-for-byte identical. Any pixel
  payload is therefore one message copied three times, not three fragments.
- All non-binary pixels in the QR are confined to the finder squares; the data
  modules are pure black/white.
- Exact values are grayscale only; there is no independent RGB-channel signal.
- The texture is Y-dominant, strongly periodic, and nearly repeats between the
  top and bottom bands.
- Full-palette rendering, intensity alphabets, row types, block types, tick
  gaps, the two irregular rows, and one user-specified seven-color-to-bit map
  were negative. QR Code Monkey's style catalog and two other generators did
  not reproduce the texture.
- The earlier perimeter-unroll idea was skipped because choosing one of seven
  band depths after observing the data would be arbitrary.

### New preliminary measurements for this session

These are incubation measurements, not promoted findings:

- Each finder square contains exactly **345 `#FAFAFA` pixels** (14.6684% of
  the full 48x49 box), at identical coordinates in all three copies.
- The `#FAFAFA` mask has **16 connected components** under both 4- and
  8-neighbor connectivity. Sorted sizes are:
  `71,65,43,43,14x3,11x3,9x3,7x3`.
- Spatially, the top full-width components have sizes `65,43`; the bottom
  full-width components have sizes `71,43`. The left/right side components
  repeat as three copies of paired families (`11/14` and `7/9`).
- Horizontal-flip agreement is 93.28%, vertical-flip agreement is 91.16%, and
  180-degree agreement is 88.35%. The mask is close to symmetric but not
  exactly symmetric.
- Vertical self-agreement is locally strongest at offsets 4, 7, and 14; the
  offset-14 agreement is 86.79%. This supports a nested 7/14-row cadence.
- The active `#FAFAFA` crop is x=7..40, y=8..41 relative to the finder box.
  Rows 8, 12, 36, and 40 are solid 34-pixel runs; intervening rows contain
  repeated tooth shapes. This looks much more like a reusable raster primitive
  than a high-entropy ciphertext bitmap.

### Constraints

- Repeating the same transform on all three eyes is not independent evidence;
  they are literal copies.
- A clean AES-oracle negative is useful only after a representation is selected
  by geometry or source evidence. It cannot choose among arbitrary traversals.
- Regularity alone is expected from dithering, resampling, scan conversion, and
  tiled fills. A proposed payload needs a parser-valid output, exact external
  match, or independently selected downstream consumer.
- Any new decode pass must explicitly state which previous phase it differs
  from. “Another bit mapping” is not enough.

## Framing questions

1. What is the smallest generative description of the mask?
2. Which deviations remain after subtracting that description?
3. Do those deviations behave like authored data, or like boundary conditions
   of a renderer/tile?
4. Can a known tool, asset, font, rasterizer, or scaling history reproduce the
   mask exactly rather than merely look similar?

## Idea portfolio

### Lane A — identify the generative pattern first

#### A1. Minimum-description tile inference

> [!info] Executed as Phase 354 (2026-08-21)
> The leakage-prone per-connected-component phase reset was removed before the
> real run. The proposed row+column-sum-preserving switch null was also found
> by self-test to be degenerate (zero legal switches in every band), so two
> separately disclosed row-sum- and column-sum-preserving null families were
> used instead. All four held-out folds independently selected one global 7x7
> tile. Aggregate held-out prediction was 721/749 pixels, MCC 0.9264, above
> both 200-control null families at empirical `p=1/201`. A full fit leaves 23
> residual pixels, all confined to the already-known boundary column and two
> irregular rows. Positive structural identification of a global 7x7 raster
> primitive; no payload claim. See `tools/gsmg/FINDINGS.md` Phase 354 and
> `tools/gsmg/qr_fafafa_tile_predictability_audit.py`.

Fit the full binary mask using a small grammar: horizontal runs, a repeating
tooth tile, 7-row blocks, mirrored side bands, and explicit boundary rules.
Score models by description length plus residual pixels. Search only bounded
tile widths 1--14 and heights 1--14, with phase reset either global, per band,
or per connected component.

Why useful: a very short exact grammar would identify the pattern as mechanical
and expose the small residual where any message would have to live.

Smallest test: freeze the model family and compare its exact residual count to
shuffled masks preserving row/column sums. Success is not “low error”; it is a
substantially shorter exact description than controls.

#### A2. Seven-track ring unroll

Resolve the old arbitrary-depth blocker by unrolling **all seven depth tracks**
clockwise from the same QR-native corner. Treat the result as a 7-channel
sequence rather than selecting one favorable track. Measure cross-track
agreement, phase, and whether one track is exceptional.

Why distinct: Phase 306 scanned only top/bottom rectangular bands row-major;
this uses the entire ring geometry without choosing a depth after the fact.

Stop rule: report structure only. Decode text or query the oracle only if a
mechanical collapse (unanimous bit, majority bit, or one demonstrably distinct
track) is selected before viewing decoded output.

#### A3. Dihedral residual atlas

Compute XOR residuals against horizontal flip, vertical flip, 180-degree
rotation, and the valid rectangular transpose/90-degree comparisons after a
declared 48x49 alignment rule. Render all transforms in one fixed atlas and
record residual component sizes and coordinates.

Why useful: decorative finder rings are conceptually symmetric. The deviations
from symmetry are a better candidate signal than the large deterministic fill.

Control: perform the same analysis on synthetic resampled finder rings matched
for dimensions and density. A puzzle residual is interesting only if it is more
compact or symbol-like under a predeclared metric than the controls.

#### A4. Component graph and repeated-family model

Represent the 16 components as a spatial graph with attributes `(bbox width,
height, area, edge/corner role)`. Determine whether the `3x` repeated sizes are
exactly the three side-band repetitions predicted by a 7-row tile. Then encode
only unmatched nodes or attribute deltas.

Promising observation: the raw sizes include ASCII-looking 65/71, but treating
those directly as `A/G` is post-hoc and inadmissible. The valid question is
whether a geometry-selected ordering and baseline leave a small delta sequence.

#### A5. QR-module normalization

> [!info] Executed as Phase 356 (2026-08-21)
> Recovering the complete logical eyes corrects the earlier pure-black-component
> boxes from 48x49 to exactly 49x49 pixels: 7x7 QR modules at exactly 7 pixels
> per module. Eye origins differ by 182 pixels = 26 modules x 7 in both axes.
> All 345 `#FAFAFA` pixels lie in the finder pattern's sixteen logical white-
> ring modules. Leave-one-module-out fitting of one shared 7x7 subpixel tile
> predicts 751/784 sites (95.79%, MCC 0.9168), versus 500 per-module-count-
> preserving controls with mean MCC 0.002 and `p=1/501`. Positive: the texture
> is exactly module-grid-locked, strongly supporting a module-sized stamped/
> tiled rendering primitive. No payload claim. See FINDINGS Phase 356 and
> `tools/gsmg/qr_fafafa_module_lock_audit.py`.

> [!warning] Scope correction after module-variant enumeration
> “One shared tile” is an over-compressed description. The sixteen logical
> white-ring modules contain **six byte-distinct 7x7 grayscale patches**, with
> multiplicities `4,4,4,2,1,1`, arranged by spatial role (left vertical, right
> vertical, bottom, and distinct top/corner cases). Phase 356's majority tile
> predicts the atlas well, but is not identical everywhere. What is exact is
> the 7x7 **module-grid lock**, not a single repeated bitmap. Subsequent work
> must preserve the six variants rather than collapsing them to the canonical
> right-side patch.

Estimate the native module pitch from the 33x33 QR and remap each finder box to
an ideal 7x7 module coordinate system with submodule phase bins. Test whether
`#FAFAFA` occupancy is determined by `(module row, module col, subpixel x,
subpixel y)` and a fractional pitch.

Why useful: 48x49 pixels is not a clean multiple of seven. A fractional module
pitch plus a repeated vector primitive could naturally create the 7/14 cadence.
An exact reconstruction would strongly favor rendering over payload.

#### A6. Spectral/lattice fingerprint

Compute the 2D autocorrelation and discrete Fourier spectrum of the mask, then
fit dominant periods without interpreting them as characters. Compare against
nearest-neighbor, bilinear, bicubic, Lanczos, ordered-dither, and vector-edge
controls at the same dimensions.

Success criterion: a control family reproduces the same dominant peaks and
phase relationships, narrowing the mechanism. Spectral peaks alone are not a
decode.

#### A7. Six-variant compositional atlas and center prediction

> [!info] Executed as Phase 360 (2026-08-21)
> The sixteen white-ring modules were preserved as six exact grayscale
> variants and modeled as the observed perimeter of a 5x5 module matrix. A
> per-subpixel row-plus-column model predicts 773/784 exact `#FAFAFA` bits in
> leave-one-module-out testing, versus position-permuted controls with mean
> 735.418 and empirical `p=3/501`. Its full observed fit is 784/784; all 11
> held-out errors lie on the already-known irregular subpixel row 2. Applying
> that frozen model to the black center predicts 210/441 `#FAFAFA` sites in
> two patch forms. The continuation is explicitly counterfactual: the center
> is unobserved and alternative model classes could fill it differently. See
> FINDINGS Phase 360 and
> `tools/gsmg/qr_fafafa_six_variant_atlas_audit.py`.

> [!warning] Center identifiability correction — Phase 361
> Phase 360's eleven held-out errors are exceptionally compact: every error is
> on subpixel row 2 and columns 0/4 (support area 2), versus support area 15 in
> all 500 patch-position controls, `p=1/501`. This supports a mechanical
> irregular-row correction. But adding one scalar interaction that is zero on
> the observed perimeter and nonzero only in the hidden center preserves the
> exact 773/784 validation score while producing center totals 198, 210, or
> 213. Therefore the perimeter does not identify a unique center. Treat every
> continuation image as counterfactual unless source evidence selects a model.

Treat the white ring as the perimeter of a missing-data problem, rather than
as sixteen samples of one universal bitmap. Fit only simple module-row and
module-column corrections and require held-out perimeter prediction before
using the model to visualize the hidden center. Preserve exact grayscale
variants separately from the binary `#FAFAFA` target.

#### A8. Compositing and flat-tone dither inversion

> [!info] Executed as Phase 364 (2026-08-21)
> Black-over-white equal-area coverage cannot reproduce all five light grays
> on any 2×2 through 15×15 binary sample grid; 16×16 is first exact and merely
> recovers ordinary 8-bit luminance deficits `21,19,5,3,0`. Two exhaustive
> 1,113,024-candidate Bayer searches (global and module-reset coordinates) have
> zero exact models; best module-reset MCC is 0.4635 with 227/784 errors.
> Nineteen thousand four hundred fifty-six Floyd–Steinberg/Atkinson constant-
> tone candidates also have zero exact models; best has 310 errors. Standard
> flat-tone spatial quantization is rejected. A custom 7x7 opacity/threshold
> asset remains possible but is itself the unexplained patterned primitive.
> See FINDINGS Phase 364 and
> `tools/gsmg/qr_fafafa_compositing_dither_inversion_audit.py`.

Invert the light grayscale values as possible coverage/alpha weights, but
require a small independently defined quantization grid or standard dither
algorithm to reproduce the full atlas. Do not treat the tautological mapping
`alpha = 255 - gray` as recovered metadata in an opaque PNG.

### Lane B — identify the producing tool or asset

#### B1. Exact render-calibration matrix

> [!info] Local matrix executed as Phase 359 (2026-08-21)
> One ideal 49x49 finder with a constant `#FAFAFA` ring was rendered through
> Pillow, OpenCV (hard/AA), and Cairo (four AA modes x four subpixel phases): 19
> variants, zero exact module tiles. Best is uniform 250 and misses 26/49 bytes;
> AA variants have at most two distinct row patterns versus the real tile's
> four. This matches the geometry invariant: a constant vertical strip cannot
> create the observed Y-varying interior away from corners. Browser SVG/canvas
> was not counted because the local synthetic page was blocked by browser URL
> policy. Constant-fill renderer class closed; an explicit patterned 7x7 asset
> remains the working mechanism. See FINDINGS Phase 359 and
> `tools/gsmg/qr_fafafa_renderer_calibration_audit.py`.

Render one ideal finder primitive at the inferred fractional pitch through a
bounded matrix of engines already available or easy to pin: browser SVG/canvas,
Cairo, ImageMagick SVG, resvg, and selected font rasterizers. Freeze dimensions,
fill colors, and resampling filters. Compare exact masks, not screenshots by eye.

Use A5 to reduce the parameter space first. Do not sweep engines and sizes
open-endedly.

#### B2. Scale-history inversion

> [!info] Executed as Phase 357 (2026-08-21)
> The canonical two-level 7x7 grayscale patch (identical in four right-side
> modules) was tested against all 216 smaller 1..6 x 1..6 raster sizes through
> Pillow nearest/box/bilinear/hamming/bicubic/Lanczos. Unconstrained continuous
> least squares supplied a generous lower bound, followed by clipped 8-bit real
> rendering. Zero continuous-exact and zero byte-exact models. Best is a nearly
> full-size 6x6 Hamming source (36 DOF), RMSE 0.754 but 22/49 byte mismatches.
> The target is more compressible than 500 same-density shuffled tiles
> (`p=0.00998`), confirming regularity but not a scale history. Negative for a
> simple smaller-source resize; favors a native 7x7 primitive. See FINDINGS
> Phase 357 and `tools/gsmg/qr_fafafa_scale_inversion_audit.py`.

> [!warning] Scope
> Phase 357 tests only the four-copy canonical right-side variant, not the five
> other module patches. Its negative does not establish the scale history of
> the full six-variant atlas.

Search for a plausible small source sprite which, after one declared upscale or
downscale, produces the mask. Candidate native widths should come from QR module
geometry, not every integer. For each candidate, solve the inverse using the
same small filter catalog already used in earlier controls.

The key discriminator is whether one source sprite reproduces all grayscale
levels and exact coordinates, including the two irregular rows.

#### B3. PNG scanline/filter provenance

> [!info] Executed as Phase 363 (2026-08-21)
> QR-specific filtered-byte comparison shows the repeated eyes exist as
> identical pixels before final whole-image PNG filtering. Horizontal-eye
> differences occur only in the first RGBA pixel of six Sub-filtered rows,
> caused by pixels outside the box; the vertical pair is byte-identical on
> 48/49 filtered rows and differs once because the global encoder chose Up on
> one row and Sub on the other. Stage-0 and the rabbit asset share the same
> chunk order, `785e` zlib header, and Sub/Up-only filter family. None of 70
> Pillow/OpenCV re-encodes matches the source filter sequence (best differs on
> 92 rows and adds Paeth). Partial provenance: one final composed-image export,
> exporter unidentified; PNG bytes cannot distinguish earlier stamping from
> procedural drawing. See FINDINGS Phase 363 and
> `tools/gsmg/qr_fafafa_png_scanline_provenance_audit.py`.

Inspect PNG color type, per-row filters after IDAT inflation, and byte contexts
around the three identical pixel regions. Ask whether the eyes were stamped as
one raster asset before final encoding, or whether identical pixels arose from
procedural drawing. This cannot prove authorship, but may distinguish a copied
sprite from a later whole-image transformation.

Important limit: DEFLATE similarities are encoder behavior, not a hidden
message. Treat this as provenance only.

#### B4. Repository/archive asset fingerprint

> [!info] Local repository executed as Phase 358 (2026-08-21)
> Every one of 129 repository rasters was searched for byte-exact 7x7 copies;
> 35 flat/lossless graphics were additionally searched for an exact two-color
> geometry match under all eight symmetries, permitting arbitrary palette
> remapping. The only 36 hits are the expected twelve module copies in each of
> `puzzle.png`, its byte-identical `doc/img/gsmg_puzzle_stage1.png` copy, and a
> derived red-highlight visualization. Zero independent or palette-remapped
> asset hits. Local branch closed negative; external/historical archives remain
> open only if a genuinely new bundle is acquired. See FINDINGS Phase 358 and
> `tools/gsmg/qr_fafafa_asset_fingerprint_audit.py`.

> [!warning] Scope
> The Phase-358 fingerprint is the canonical right-side variant only. The other
> five exact module variants have not yet received the same repository-wide
> fingerprint search, so the broader local-asset branch is not fully closed.

> [!info] All-six continuation executed as Phase 362 (2026-08-21)
> All 133 repository rasters received byte-exact search for all six targets;
> 10 asset-sized flat/lossless rasters (at most 10,000 pixels) also received
> exact equality-partition palette-remap search for the two/four/five-class
> variants. The only 144 hits are the expected 48 patches in each of the same
> three known/derived Stage-0 files. Zero independent or small-asset remapped
> hits. Repository-wide byte-exact scope is closed; large-raster remapping of
> the five noncanonical variants remains explicitly open because of the
> disclosed computational cap. See FINDINGS Phase 362 and
> `tools/gsmg/qr_fafafa_six_variant_fingerprint_audit.py`.

Search historical source bundles, CSS/SVG, icon fonts, design exports, cached
generator assets, and community attachments for the exact 48x49 mask or its
smaller inferred tile. Use exact hashes and normalized binary-mask hashes before
perceptual matching.

This is the highest-evidence source-identification route because an exact asset
predating the puzzle would settle the mechanism without interpreting pixels.

#### B5. Cross-image rendering fingerprint

Search other puzzle-native computer graphics for the same tooth tile, same
`#FAFAFA`/edge-value palette, or same 7-row cadence at other boundaries. Match
geometry and relative phase, not just color occurrence. A repeated renderer
fingerprint elsewhere would weaken the steganographic reading.

### Lane C — bounded decode attempts after baseline subtraction

#### C1. Full `#FAFAFA` bitmap recognition

Render only the 48x49 mask in black/white under a frozen set of four views:
native, horizontal flip, vertical flip, and 180 degrees. Apply one declared
morphological closing radius (or none) selected from the inferred tooth width,
not by visual tuning. Run OCR/barcode recognition and compare against random
row/column-sum-preserving controls.

This is the most direct version of the user's observation and has not been run
as a full-square `#FAFAFA`-only experiment.

#### C2. Symmetry-residual glyph test

Render the fixed D4 residuals from A3 at nearest-neighbor scale and run the same
recognizers. The residual is allowed to count as a hit only if one exact symbol
is stable across at least two independently defined residual views or matches a
known downstream token without tuning.

#### C3. Generative-model residual stream

If A1 produces a compact exact baseline, order only the residual coordinates by
the baseline's own band/component traversal. Test: coordinate deltas, signed
tooth-phase deltas, and presence/absence bits. No alternative mappings after
results are seen.

This is preferable to reading all 345 pixels: authored information, if present,
should live in departures from the repeated tile.

#### C4. Context-derived three-eye overlay

Although the eyes are identical in page orientation, their QR roles provide
three non-arbitrary local orientations: top-left, top-right, and bottom-left.
Rotate each copy so its outer QR corner maps to a common direction, then compute
AND, OR, XOR, and majority overlays. Because inputs are identical but transforms
are context-selected, the output tests rotational structure rather than adding
fake independent evidence.

Risk: this can manufacture symmetry art from any asymmetric stamp. Require a
predeclared recognizable-output metric and synthetic controls.

#### C5. QR threshold/decode ladder

Replace only `#FAFAFA` with black or white under a small threshold ladder, then
attempt QR, Micro QR, Data Matrix, and generic barcode recognition on (a) the
whole QR and (b) the isolated eye mask. Record whether any second payload is
stable over adjacent thresholds.

Expectation is negative: finder-ring pixels are outside data modules. Stability
across thresholds is required to prevent a one-off detector false positive.

#### C6. Row/column and component-delta number channels

Use the geometry to define three short sequences before interpreting numbers:
row counts, column counts, and paired left/right component-area deltas. Test only
standard direct forms justified by range: A1Z26 if all values are 1--26, ASCII
only if all are printable, and QR-native base 2/7 if mechanically binary/base-7.
Reject modulo folding or arbitrary offsets.

This explicitly prevents the tempting but unsupported `65 -> A`, `71 -> G`
reading from becoming a fishing expedition.

#### C7. Braille-cell interpretation

> [!info] Executed as Phase 355 (2026-08-21)
> All 112 direct readings (6-/8-dot, every grid phase, both polarities, four
> rectangle-preserving orientations) were run on both the full mask and Phase
> 354's frozen 23-pixel residual. The best full-mask transliteration had 319
> unknown cells, zero common English bigrams, and scored below row-sum and
> column-sum controls (`p=0.995` and `p=1.0`). The residual scored below its
> density-matched controls (`p=0.965`). Closed negative. Phase 354's 7x7 tile
> does not independently select a 2x3/2x4 dot lattice, so the stronger lattice-
> selected variant remains unlicensed rather than untested. See FINDINGS Phase
> 355 and `tools/gsmg/qr_fafafa_braille_audit.py`.

Test whether the mask's repeated teeth or a mechanically inferred lattice form
6-dot Braille (2x3) or 8-dot Braille (2x4) cells. This is plausible enough to
test because the active mask is 34 pixels wide (exactly divisible by two), its
tooth spacing alternates around 3/4 pixels, and its vertical organization has a
7/14-row cadence. It is not evidence by itself: any arbitrary 2x3 binary block
maps to a valid Unicode Braille character.

Use two separate, predeclared readings:

1. **Direct-pixel control.** Exhaust all grid origins only (2x3 gives six;
   2x4 gives eight), both polarities, and the four non-transposing orientations
   that preserve the 49x48 rectangle. Do not crop differently per origin.
   Decode with the standard Braille dot ordering and score the complete output
   against English/known-token models plus row/column-sum-preserving masks.
2. **Geometry-selected lattice.** Run only if A1/A5 independently identifies
   repeated tooth centers or submodule sample points. Treat those inferred
   centers as dots, then group them into 2x3/2x4 cells using the inferred phase.
   This is the stronger test because the pattern, rather than the desired text,
   selects the dot grid.

Required reporting: exact origin, orientation, polarity, cell boundaries,
Unicode Braille sequence, Grade-1 transliteration, untranslated-cell count, and
rank among controls. Contracted Grade-2 Braille is excluded from the first pass
because its language-dependent contractions greatly increase interpretive
freedom. A hit must be stable under a neighboring reasonable crop or selected
by the inferred lattice; one suggestive word in one hand-picked alignment is a
negative.

Useful falsification: real Braille should resemble separated dot centers after
lattice reduction. The present `#FAFAFA` mask instead contains long connected
runs (including four 34-pixel solid rows), so a literal one-pixel-one-dot Braille
reading starts with a substantial structural mismatch. The geometry-selected
tooth-center version is therefore more credible than direct raster grouping.

### Lane D — adversarial controls and falsification

#### D1. Compression/randomness tests are secondary

Estimate entropy and compressibility only relative to masks preserving the same
row/column sums and connected-component size distribution. Raw low entropy is
not evidence; the pattern is visibly repetitive.

#### D2. Synthetic rendering control bank

Every symbol/glyph score used above should be run against a control bank of
mechanically generated finder textures at 48x49. If comparable “letters” appear
frequently, the recognition criterion is invalid.

#### D3. Held-out prediction

Fit any generative tile on only the top and side bands, then predict the bottom
band before inspecting its residual (and rotate the holdout across bands). A
model that explains only the region it was fitted to is description, not
mechanism.

## Connections and challenges

### Combinations

- **A1 + C3** is the cleanest decode route: infer a mechanical baseline, then
  inspect only its selected residual.
- **A5 + B1/B2** is the cleanest source-identification route: infer native QR
  geometry before spending a render sweep.
- **A3 + C2 + D2** gives the fastest bounded visual-symbol test with controls.
- **A4 + D3** can determine whether the 16 components are completely explained
  by repeated band tiles before their sizes are interpreted numerically.

### Contradictions to resolve

- Exact identity across three page positions favors a stamped sprite; strong
  7/14 cadence favors a raster/tile algorithm. These may be the same mechanism:
  a procedurally generated eye exported once, then stamped three times.
- Near-symmetry makes symmetry residuals attractive, but asymmetric raster
  boundary conditions naturally create residuals too. Controls are mandatory.
- The two irregular rows are the only obvious non-repetition in the earlier
  top/bottom analysis, yet their negative Phase-305 bit readings do not prove
  they are meaningless; they may be boundary signatures rather than a linear
  payload.

### Ideas deliberately not reopened

- arbitrary color-to-bit remappings;
- RGB-channel steganography;
- Game of Life, Morse, or repeated row/block alphabets;
- open-ended generator-site trials;
- arbitrary single-depth perimeter walks;
- treating three identical eyes as three independent ciphertext fragments.

## Promising directions

Ranked by information gain, discipline, and effort:

1. **Generator-specific patterned-fill tests.** Phases 361/364 show that source
   evidence—not perimeter extrapolation or standard flat-tone dithering—is
   required to select a center rule.
2. **Historical/source bundle acquisition.** Phases 358/362 find no independent
   local raster asset; new provenance now requires genuinely new material.
3. **A3 + C2 + D2 — symmetry-residual atlas with synthetic controls.** Small,
   visual, and genuinely different from Phases 300--306.
4. **A2 — seven-track ring unroll.** Resolves the old depth-selection blocker
   without cherry-picking one track.
5. **C1 — full `#FAFAFA`-only bitmap recognition.** Cheap and directly answers
   the user's proposed object, but high pareidolia risk without D2 controls.
6. ~~**C7 — Braille-cell interpretation.**~~ Direct-pixel and frozen-residual
   variants executed Phase 355, closed negative. Phase 354 selected a 7x7 tile,
   not a Braille-compatible 2x3/2x4 lattice; do not manufacture a new lattice
   without external selection.

With B1/B2/B4 partly executed, the surviving renderer account is narrower but
plural: a position-dependent **six-variant 7x7 module atlas** or patterned fill.
Constant fill is negative. Smaller-source inversion and local fingerprinting
are negative only for the canonical right-side variant; the other five exact
patches remain to be handled as an atlas.

## Proposed first experiment contract

> [!info] Executed as Phase 354
> The structural gate passed: a global 7x7 tile generalizes across all four
> held-out bands and leaves a frozen 23-pixel residual. The original dual-
> projection null was corrected before the real run because it admitted no
> legal shuffle. Decoding the residual remains a separate phase.

Do **A1 + D3**, not a decoder sweep:

1. Freeze the 48x49 Boolean input as equality to exact RGB `(250,250,250)`.
2. Enumerate tile widths/heights 1--14 and only three phase-reset models:
   global, per ring band, per connected component.
3. Fit on three of four bands and predict the held-out band; rotate holdout.
4. Report exact residual coordinates, model description length, and control
   distribution from row/column-sum-preserving shuffled masks.
5. Promote only if one model predicts held-out pixels materially better than
   controls and leaves a stable residual under all four holdouts.
6. Do not interpret residual bits in the same phase. Freeze the residual object
   first; decoding it, if warranted, becomes a separate phase.

## Open questions

- Is the one-pixel 48x49 asymmetry (rather than 49x49 or 48x48) caused by QR
  module pitch, crop bounds, or the source sprite itself?
- Do the size families `14/11` and `9/7` equal a common tooth primitive plus
  predictable edge clipping?
- Why does the bottom full-width component contain 71 pixels versus 65 at the
  top while the next component is 43 in both places?
- Is Phase 360's separable row-plus-column continuation historical, or can an
  evidenced patterned renderer select a different center model?
- Can a historical generator or patterned asset independently explain why the
  only model residual lives on subpixel row 2 at columns 0/4?
- Can any archived source asset identify the pattern before further decoding?

## Promotion

`Brainstorms/` is an incubation area, not a second knowledge store.

- Keep these ideas here until one has frozen inputs, controls, and stop rules.
- Record an executed experiment as a new phase in `tools/gsmg/FINDINGS.md`
  using [GSMG_PHASE_TEMPLATE](../GSMG_PHASE_TEMPLATE.md).
- Do not update the Fact Ledger or `GSMG_HOME.md` merely because the mask looks
  structured.

## Related notes

- [QR Finder-Pattern Ring Texture Investigation](2026-08-16%20-%20QR%20Finder-Pattern%20Ring%20Texture%20Investigation.md)
- [GSMG phase index](../GSMG_PHASE_INDEX.md)
- [Strict transition worksheet](../GSMG_STRICT_TRANSITION_WORKSHEET.md)
