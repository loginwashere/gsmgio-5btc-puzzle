# GSMG First-Piece Color Pixels — Creative Brainstorming & Cross-Phase Integration

**Date**: 2026-08-09  
**Status**: Creative Brainstorm (Postponed Verification)  
**Objective**: Explore imaginative, structural, and cross-phase hypotheses connecting the **24 yellow/blue color pixels**, the **#FEFEFE anomaly**, and **574061** from the first image (`puzzle.png` / Stage 0) to downstream puzzle phases.

---

## Executive Overview of First-Image Color Data

| Data Object | Raw Extraction / Derivation | Key Properties & Meanings |
| :--- | :--- | :--- |
| **24 Color Pixels** | `BBBBYBBBYYBBBBYBBYYBYYBY` (15 Blue, 9 Yellow) | Last bit of each 24 URL chars in `gsmg.io/theseedisplanted` |
| **Direct Polarity (`B=1, Y=0`)** | `111101110011110110010010` = `0xF73D92` | `RGB(247, 61, 146)` — Rose/Pink ("Roses are White but often Red") |
| **Complement Polarity (`Y=1, B=0`)**| `000010001100001001101101` = `0x08C26D` | **`574061`** (PRIME) — matching clue `yellowblueprime` |
| **2×3 Matrix Representation** | $\begin{pmatrix} 5 & 7 & 4 \\ 0 & 6 & 1 \end{pmatrix}$ | Row sums: **16, 7** \| Total sum: **23** (`matrixsumlist`) |
| **Anomalous Pixel `#FEFEFE`** | Spiral Pos 163 (0-indexed), Char 21 (`n`), Bit 4 | `{1,4,21}` tuple; cell hex `FEFEFE` vs pure `FFFFFF` white |
| **4-Color Palette** | Black (`00`), White (`01`), Blue (`10`), Yellow (`11`) | 4 discrete palette states forming a 2-bit/pixel color depth |

---

## Creative Hypotheses: Connecting First-Piece Color Data to Downstream Phases

### 1. Matrix Multiplication Convergence: `574061` × `[23, 16, 7]^T` = `[255, 103]^T`
> [!TIP]
> **Verified in Phase 199; consumer remains unselected.**  
> Multiplying the 2×3 matrix derived from `574061` by the column vector $(23, 16, 7)^T$ yields exact values:
> $$\begin{pmatrix} 5 & 7 & 4 \\ 0 & 6 & 1 \end{pmatrix} \begin{pmatrix} 23 \\ 16 \\ 7 \end{pmatrix} = \begin{pmatrix} 5(23) + 7(16) + 4(7) \\ 0(23) + 6(16) + 1(7) \end{pmatrix} = \begin{pmatrix} 255 \\ 103 \end{pmatrix}$$
> - **255 (`0xFF`)**: Max byte value / pure white color intensity in RGB.
> - **103**: ASCII decimal for **`'g'`**, the exact first character of `gsmg.io/theseedisplanted`.

**Brainstorming Applications**:
- **Key Byte Generation**: $255$ and $103$ could serve as a 2-byte header, key prefix, or KDF salt for Phase 3 decryption (`0xFF 0x67`).
- **Phase Loop Closure**: Returning to `'g'` (ASCII 103) creates a self-referential loop where the end of the Matrix operation points back to the origin of the seed.
- **Calibration result:** with the matrix fixed, the authenticated vector order
  is the only one of six permutations yielding `FF + ASCII letter`. Across
  rectangle symmetries and vector orders there are only six distinct unordered
  output pairs, with `{103,255}` one of six. The operands are also linked:
  `[23,16,7]` is the total and row sums of this same matrix, so this is not an
  independent numerical confirmation.
- **Current restriction:** preserve `(255,103)` / `FF67` as a recognition
  checkpoint, but do not use it as a key prefix, salt, IV, or password until an
  independent clue selects multiplication and a consumer.

---

### 2. The 15/9 Dual-Stream Multiplexer (Yin-Yang Rail Interleaving)
> [!NOTE]
> **Audited in Phase 201.** The complete endpoint mask is genuinely `15/9`,
> but it is not the same object as the DBBI-fitting `14/8/1` event inventory.
> The two literal DBBI/FAED next-character assignments produce
> `dbbifbfbaehccbdegggbeeid` and `faeddggebbedfcibdbfabhbc`; both merely copy
> their selected stream's name under the initial `BBBB` and neither continues
> as plaintext. A two-stream MUX also cannot preserve FEFE as a third class
> without a new rail or an explicit fold.
>
> In Phase 3, the puzzle focuses heavily on two parallel texts/matrices: **DBBI** (Yin) and **FAED** (Yang).

**Brainstorming Applications**:
- **Stream Selector (MUX)**: Treat `BBBBYBBBYYBBBBYBBYYBYYBY` (15 Blue, 9 Yellow) as a binary multiplexer clock signal.
  - **Blue (`1`)**: Pull next character from DBBI stream.
  - **Yellow (`0`)**: Pull next character from FAED stream.
- **Resulting Hybrid Stream**: Generates a 24-character interleaved passphrase combining Yin and Yang into one balanced entity, directly fulfilling the "Cosmic Duality / Yin Yang" theme.

---

### 3. Optical Cardan Grille (2D Spatial Image Overlay)
> [!IMPORTANT]
> The 14×14 grid embedded in Stage 0 contains 196 cells, with 9 Yellow cells and 1 `#FEFEFE` cell.

**Phase 207 gate audit:** yellow, FEFE, and union aperture sets have sizes
`9/1/10`, and each has eight distinct D4 orientations. The three proposed
target images are `812x415`, `812x893`, and `668x619`; none has both dimensions
divisible by 14, so none supplies a native equal-cell registration. Even one
full-image normalized-fit convention leaves 72 target/aperture/orientation
variants, before crop/contain/cover, offsets, sampler, channel, and visual-to-
character rules.

**Status:** close pending an explicit target, registration, orientation,
sampler, and feature decoder. Full audit:
[doc/GSMG_FIRST_PIECE_OVERLAY_DNA_RGB_GATE_AUDIT.md](GSMG_FIRST_PIECE_OVERLAY_DNA_RGB_GATE_AUDIT.md).

**Brainstorming Applications**:
- **Spatial Stencil**: Treat the 14×14 grid not as a 1D sequence, but as a physical 2D mask (Cardan Grille).
- **Cross-Phase Overlay**: Superimpose the 14×14 grid onto `phase2.png`, `phase3.png`, or `SalPhaseIonCosmicDuality.png`.
- **Target Extraction**: The 9 Yellow pixel coordinates (or cell 163 `#FEFEFE`) act as optical aperture windows. The characters or visual features visible through these 9 windows on the later phase images form the hidden key.

---

### 4. Character Partitioning: "The Yellow Rail" vs. "The Blue Rail"
> [!NOTE]
> **Audited in Phase 201.** Preserve two distinct inventories. The complete URL
> endpoint rails are `15/9`, as tabulated below. The fitted prime-walk event
> rails are instead blue `gsmgio/eseeisa` (14 singleton `b` events), yellow
> `.thdplnt` (8 digraph `be` events), and FEFE `n` (one singleton `b` event).
> They represent 22 distinct URL objects plus the internal FEFE cell—not a
> flat 23-character URL partition.
>
> Partitioning the 24 URL characters of `gsmg.io/theseedisplanted` by their underlying pixel color yields two distinct string sets:

| Partition | Count | Extracted Characters |
| :--- | :--- | :--- |
| **Yellow Rail (`0`)** | 9 | `. t h d p l n t d` |
| **Blue Rail (`1`)** | 15 | `g s m g i o / e s e e i s a e` |

**Brainstorming Applications**:
- **Yellow Anagram / Sub-key**: The 9 Yellow characters contain 8 letters (`t h d p l n t d`) + 1 dot. Anagramming or shifting these 8 letters (e.g. using `23, 16, 7`) could yield a secondary keyword.
- **Blue Salt / IV**: The 15 Blue characters contain the core domain `gsmgio` plus vowels `e, e, e, i, a, o`. This can act as a natural 15-byte initialization vector (IV) or salt in AES encryption.
- The 14 fitted blue events do **not** map one-to-one onto the 14 grid rows:
  they cover only 12, duplicate rows 2/14, and miss rows 6/11. Do not zip them
  to rows 1–14 by event order; that invents a traversal contrary to the native
  coordinates.
- All 23 fitted events together do cover all 14 native rows, with bucket sizes
  `2,2,1,1,2,1,2,3,1,2,1,1,2,2`. Keep this all-event row bucketing as the
  remaining spatial structure, pending a grounded within-row consumer.
- Flattening the fitted `b`/`be` tokens gives 31 symbols but erases the blue
  versus FEFE distinction because both singleton classes emit `b`; preserve
  event boundaries and metadata.

---

### 5. Genetic / DNA Cipher (The Planted Seed's Genome)
> [!NOTE]
> Stage 0 is titled `theseedisplanted`. Plants grow from seeds via DNA (4 nucleotide bases).

**Phase 207 gate audit:** the 24 endpoint symbols use only blue/yellow, so they
carry 24 bits = 3 packed bytes, not 12 bytes. A true four-state two-bit stream
would carry 48 bits = 6 bytes. The full grid additionally has FEFE as a fifth
state. Exhausting `4P2=12` blue/yellow base assignments, two directions, and
three circular codon frames gives 72 distinct DNA and 72 distinct amino-acid
outputs. The proposed `blue=G/yellow=T`, forward frame zero route gives
`GGG GTG GGT TGG GGT GGT TGT TGT -> GVGWGGCC`, with no selector or consumer.

**Status:** close pending an explicit base map, FEFE rule, direction/frame, and
amino/byte consumer. Full audit:
[doc/GSMG_FIRST_PIECE_OVERLAY_DNA_RGB_GATE_AUDIT.md](GSMG_FIRST_PIECE_OVERLAY_DNA_RGB_GATE_AUDIT.md).

**Brainstorming Applications**:
- **4-Color Palette Mapping**: The first image relies on 4 discrete color states:
  - **Black (`00`)** $\rightarrow$ Adenine (A)
  - **White (`01`)** $\rightarrow$ Cytosine (C)
  - **Blue (`10`)** $\rightarrow$ Guanine (G)
  - **Yellow (`11`)** $\rightarrow$ Thymine (T)
- **Codon Extraction**: Grouping the 24 color pixels into 8 3-pixel triplets (codons) or 12 2-pixel pairs translates the "seed" into a genetic amino acid sequence or a 12-byte cryptographic key.

---

### 6. Vector Geometry from `#F73D92` (Rose) & `#FEFEFE` (Anomaly)
> [!NOTE]
> The color channels provide exact RGB triplets:
> - Direct Rose Color: $R=247, G=61, B=146$
> - Anomaly Pixel: $R=254, G=254, B=254$

**Brainstorming Applications**:
- **Difference Vector**: Subtracting Rose from Anomaly gives:
  $$(254-247, 254-61, 254-146) = (7, 193, 108)$$
  - **7**: Matches the third term in `[23, 16, 7]`.
  - **193**: Prime number!
  - **108**: ASCII decimal for **`'l'`** (or $108 \pmod{26} = 4 = \text{'E'}$).
- **Alphabet Modulo Shifts**: $(247, 61, 146) \pmod{26} = (13, 9, 16) \rightarrow \text{N, I, Q}$. Shifting these by `[23, 16, 7]` yields downstream rotational targets.

**Phase 207 gate audit:** the difference `(7,193,108)` is exact; 193 is prime
and 108 is ASCII `l`. With the rose fixed, FE is the only one of 256 gray bytes
whose signed red difference is 7, but the prime/ASCII channel predicates are
post-hoc and no clue selects vector subtraction as a consumer. The modulo read
above is also inconsistent: `(13,9,16)` gives `NJQ` under `A=0` or `MIP` under
`A=1`, never `NIQ` under one convention. Under `A=0`, the difference gives
`HLE`; adding/subtracting `[23,16,7]` gives `KZX/QTJ`, with no selected result.

**Status:** retain the exact difference and red-channel 7 as a recognition
coincidence; close letter/shift consumers pending direction, indexing, and
role instructions. Full audit:
[doc/GSMG_FIRST_PIECE_OVERLAY_DNA_RGB_GATE_AUDIT.md](GSMG_FIRST_PIECE_OVERLAY_DNA_RGB_GATE_AUDIT.md).

---

### 7. Marker-color channel values as literal data, not just booleans
> [!NOTE]
> `#FEFEFE` (`0xFE` = 254) and the G-shadow selector `#383838` (`0x38` = 56, Phase 189) are both "repeat one byte three times" grayscale constants used as exact-match selectors on two regions/layers of the **same** Stage-0 PNG — the embedded grid vs. the footer below the red divider bar — not two unrelated images (corrected 2026-08-09; see point 21). Neither 254 nor 56 has been fed into the numeric-coincidence triage tool's registry (`574061`, `23`, `16`, `7`, `163`, `91`, `570`, `1075`, `104`, `80`, `31`, `21`).

**Brainstorming Applications**:
- Add `254` and `56` (and hex/ASCII forms) to the triage registry and let the existing null-model-gated pairwise sweep run, rather than hand-picking relationships.
- One cheap arithmetic fact worth queuing, flagged as likely numerology until gated: `254 − 163` (FEFE's own zero-based spiral position) `= 91`, already load-bearing (`91 = 7×13`).

---

### 8. A second, image-native reading of `matrixsumlist`
> [!NOTE]
> **Partly verified in Phase 200.** The literal 14x14 row/column-popcount idea
> remains untested, but a separate image-native matrix is now verified in point
> 11: the two exact `#383838` count rows reproduce `[43,25,18]` directly.
>
> The current strongest `matrixsumlist` chain reshapes `574061`'s *decimal digits* into a 2×3 matrix to get `23,16,7`. That's a derived surrogate matrix. The puzzle also handed us an actual 14×14 matrix directly — the grid itself — and the ink/non-ink bit rule is now cleanly established (black/blue=1, white/yellow/fefefe=0).

**Brainstorming Applications**:
- Take the 14×14 ink-bit matrix as-is (no reverse/invert, distinct from the unpromoted full-mask-reverse-invert transform) and compute plain row-popcounts and column-popcounts — two literal 14-item "sum lists" from the actual matrix.
- Given the puzzle's repeated paired dualities (direct vs. complementary polarity giving rose color vs. prime), a *numeric* matrixsumlist (23/16/7) and an *image* matrixsumlist (row/column sums of the literal grid) may both be intended.

---

### 9. PNG palette-index of the FEFEFE entry as an unexamined coordinate
> [!NOTE]
> **Closed negative in Phase 202.** Raw chunk parsing shows both the full
> authenticated Stage-0 PNG and the 350×350 rabbit asset are 8-bit RGBA
> truecolor (`IHDR` color type 6), not indexed color. Their exact chunk sequence
> is `IHDR,sRGB,gAMA,pHYs,IDAT,IEND`; neither has `PLTE`, `tRNS`, text/EXIF, or
> trailing bytes. FEFE is stored as the direct sample `FEFEFEFF`, and every
> alpha byte in both images is `FF`. Therefore no source palette index or alpha
> anomaly exists.

**Brainstorming Applications**:
- Inspect the raw PNG chunk structure for a `PLTE` table; if present, check FEFEFE's index against `{1,4,21}`, `163`, and `8,6,4,2`.
- Check while inspecting raw chunks whether the image carries an alpha channel, and whether the FEFE cell's stored alpha differs from the rest of the palette.
- **Result:** the alpha channel exists structurally but is uniformly opaque.
  The full PNG's 75×75 FE block and rabbit asset's 25×25 block have exactly
  scaled coordinates and a 9:1 pixel-count ratio, confirming RGB/location
  provenance but adding no metadata coordinate.
- Do not convert the PNG to indexed color and interpret the resulting FEFE
  index: that index would be synthesized by the converter, not authored data.

---

### 10. Strategic reallocation, not another wide scan
> [!IMPORTANT]
> Phase 194 weakens the case that Cosmic Duality's Base64 formatting is an intentional secondary channel (a known-solved control blob reproduces the same texture at chance rate). A full repo-wide palette scan (Phase 157) already closed off "more anomalous pixels elsewhere" — `#FEFEFE` is confirmed the only marker in any repo image, so that avenue is not reproposed here.

**Brainstorming Applications**:
- Go *deeper* on the single confirmed `FEFEFE` marker (palette index, alpha, exact stored bytes around it — items 7-9) rather than *wider* (more images, more text-formatting tricks); the wide search already ran and came back empty.
- Not a viable direct replay: the G-shadow "row-local invariant count" technique (`OCBe -> 8,6,4`, Phase 189) doesn't transfer to the grid as-is, since `FEFE` occurs exactly once — a per-row count is degenerate (0 or 1 everywhere), unlike `#383838`'s many per-row occurrences. The abstraction that carries over is item 7: the marker's own channel *value* as data, not the counting mechanism.

---

### 11. The `#383838` Count Rows as a Second `matrixsumlist`
> [!NOTE]
> **Verified in Phase 200.** Direct resampling of the authenticated Stage-0 PNG
> reproduces both 11-entry rows, row sums `25/18`, total `43`, and therefore
> `[43,25,18]` under the same total-followed-by-row-sums grammar.
>
> The two equal-length G-shadow count rows form a literal 2x11 matrix:
>
> ```text
> 4 1 4 4 2 1 1 1 2 1 4   -> sum 25
> 2 1 2 2 1 3 1 1 1 2 2   -> sum 18
>                               total 43
> ```

**Brainstorming Applications**:
- Reuse the established total-followed-by-row-sums grammar and read this as a second `matrix sum list`: **`[43,25,18]`**.
- `43` is prime and is also the 14th prime, potentially pointing back to the 14x14 rabbit grid.
- `25` matches the complete first-piece event inventory: 24 yellow/blue endpoints plus FEFE.
- `18` is `R` in the creator's `R=18, A=1, B=2 -> RABBIT` wordplay.
- The row difference `25-18=7` returns to the recurring `7` in `[23,16,7]` and the elemental `PH -> V` difference.
- Treat `[43,25,18]` first as a cross-phase checksum or routing triple, not necessarily as a password.
- Componentwise subtraction is exact:
  `[43,25,18]-[23,16,7]=[20,9,11]`. Those values match 20 events before
  FEFE, nine yellow endpoints, and the 11-glyph width of each shadow row.
- Direct A1Z26 gives `TIK`; reversing gives `KIT`, a young rabbit. Phase 200
  finds `KIT` once in the bounded eight-member row-order/traversal family, but
  subtraction, A1Z26, and reversal remain unselected post-hoc operations.
- Do not count `20=9+11` as another check: it is forced because both source
  triples already satisfy total = row1 + row2.

---

### 12. Cross-Phase Completion of `O / C / Be / He / Zero -> 86420`
> [!TIP]
> **Gate audited in Phase 204: fails strict promotion.** Every value is
> measurable (`OCBe -> 8,6,4`, G references `4,2`, FEFE bit `0`), and the
> Architect `hye -> he -> He -> 2` route supplies a weaker second `2`.
> However, the sequence mixes atomic numbers, a pixel count, and a binary class
> bit; no clue selects their concatenation. FEFE's zero is also shared by white
> and yellow under the same base-bit rule, so it is a near-default plug rather
> than a marker-specific fifth digit.
>
> The Stage-0 G-shadow consumer produces `O/C/Be -> 8/6/4`. A later phase may supply the missing `2` more meaningfully than the small-font G count does:
>
> ```text
> G-shadow payload:       O / C / Be -> 8 / 6 / 4
> Architect end rail:     HYE -> HE  -> He -> 2
> exceptional grid bit:   FEFE zero  -> 0
> combined:                           8 / 6 / 4 / 2 / 0
> ```

**Brainstorming Applications**:
- Interpret `86420` as a value assembled across phases rather than contained wholly in Stage 0.
- Let the first image provide the initial element symbols, the Architect phase provide `He`, and the rabbit marker supply the terminal zero.
- Read the construction as evidence that early artifacts are control data reused later, rather than independent password candidates.
- Keep `8,6,4,2` as the strongest part of the convergence. Treat `86420` as a
  conditional recognition string, not an independently recovered instruction;
  Phase 191's direct blob oracle is already negative and was not rerun.

---

### 13. `86420` and `13579` as Yin-Yang Digit Halves
> [!NOTE]
> **Conditionally verified but not promoted in Phase 204.** `13579` is the
> exact nine's complement once `86420` and decimal complement are chosen, so it
> adds no evidence. Under `a=0`, `86420 -> igeca` but terminal `9` is invalid;
> dropping it gives `bdfh` and `igecabdfh`. Under `a=1`, the symmetric choice
> drops terminal `0` instead and gives `hfdbacegi`. After dropping either
> invalid terminal, an a-i permutation is forced, with eight natural rail
> order/direction variants and no selected winner.
>
> The nine's-complement partner of `86420` is `13579`; corresponding digits sum to nine:
>
> ```text
> 8 6 4 2 0
> 1 3 5 7 9
> ---------
> 9 9 9 9 9
> ```

**Brainstorming Applications**:
- Treat even and odd digits as the two halves promised by `yinyang` or “half and better half.”
- Use `86420` and `13579` as complementary checkerboard column orders, stream selectors, or transposition keys.
- Interleave the rails to obtain `8163452709`, or reverse one rail before interleaving if a later clue selects facing/opposing orientation.
- In a 0-through-8 nine-symbol system, split the alphabet into five even positions and four odd positions, naturally partitioning the native `a-i` alphabet.
- View the digitwise sum-to-nine relation as the decimal analogue of the first-piece color masks summing/XORing to `FFFFFF`.
- Do not treat out-of-range `9` as Enter/delimiter/escape without a new clue;
  that interpretation was introduced only to rescue the nine-symbol mapping.
- Park `13579`, `8163452709`, and `igecabdfh` as conditional algebra. Reopen
  only if another artifact selects decimal complement, indexing convention,
  orientation, or a control role for the invalid terminal.

---

### 14. Elemental Pixel Word `BaTcH`
> [!IMPORTANT]
> The selected gray layer offers two exact numbers, while the Architect rail offers a letter/element:
>
> ```text
> #383838 channel value: 0x38 = decimal 56 -> Ba
> total #383838 pixels:                    43 -> Tc
> H | YE | BUT:                                  H
> concatenated element symbols:             BaTcH
> ```

**Phase 205 gate audit**: the construction reproduces exactly. The selected
`#383838` layer has channel value `56` and `25+18=43` pixels; inverse atomic
lookup gives `Ba,Tc`. The established Architect selection gives `but/hye`, and
taking the initial `H` yields exact-case `BaTcH`, case-insensitively `BATCH`.
Among all six symbol orders only one spells `batch` (`1/6` fixed-target rate,
not a post-hoc p-value); even if stage order forces `H` last, `BaTcH/TcBaH`
remain and no clue selects value before count.

The later exact-case `OCBe -> O,C,Be -> 8,6,4` result establishes element
symbols as native puzzle vocabulary, improving this rebus's plausibility. It
does not select the inverse operation used here: every integer 1-118 maps to an
element once atomic lookup is chosen. Nor does an authenticated clue select
the source order, discard `YE/BUT` to retain only `H`, or name `BATCH` as an
execution grammar. `EOL` and decoded `enter` make the semantics coherent, but
the decoded instruction vocabulary contains no literal `batch`.

**Status:** retain as a strong recognition/checkpoint rebus, but close it as an
executable instruction pending an explicit inverse-element, ordering,
singleton-H, or batch/command clue. Full audit:
[doc/GSMG_FIRST_PIECE_BATCH_REBUS_GATE_AUDIT.md](GSMG_FIRST_PIECE_BATCH_REBUS_GATE_AUDIT.md).

**Brainstorming Applications**:
- Read `BaTcH` as the literal instruction **BATCH**.
- Connect `BATCH` with `matrixsumlist`, multi-item processing, and the two parallel DBBI/FAED streams.
- Combine it with the already reconstructed `EOL -> Enter/newline` chain: the final operation may resemble assembling and executing a batch/command rather than typing another password.
- Treat the pixel value (`56`) and occurrence count (`43`) as paired operands, not unrelated coincidences.

---

### 15. `G` as the Bitcoin Elliptic-Curve Generator
> [!NOTE]
> In Bitcoin/secp256k1 notation, `G` conventionally denotes the elliptic-curve generator point, with a public key derived as `private scalar x G`.

**Brainstorming Applications**:
- Read “G in the shadows and the text” simultaneously as a raster selector and a cryptographic operator clue.
- Treat visible G glyphs as multiplication/operator anchors and surrounding non-G characters as scalar material.
- Use the invariant G-shadow counts `4` and `2` as coefficients, strides, chunk sizes, or selectors rather than plaintext digits.
- Assign the banner and Bitcoin-address rows to two key halves, two private scalars, or SALPH/COSMIC channels.
- Consider removing G from a candidate stream as removing the operator after it has specified how the remaining operand should be consumed.

---

### 16. `Ce / Fe` as Private-Key Size and “Half” Arithmetic
> [!NOTE]
> Preserving `CEFE` as element symbols gives `Ce=58` and `Fe=26`.

**Phase 206 audit:** the arithmetic is exact and extends cleanly:

```text
[Ce+Fe,Ce,Fe] / 2 = [84,58,26] / 2 = [42,29,13]
Ce-Fe = 32 = secp256k1 scalar width in bytes
574061 = 0x08C26D = 3 bytes; 32-3 = 29 = Ce/2
len("matrixsumlist") = 13 = Fe/2
```

The `42=29+13` checksum is forced by halving an additive sum-list, and the
29-byte padding role requires an unselected decision to serialize the prime as
a private scalar. More decisively, `CE` is absent from the original 48x48
favicon (`0` pixels) and appears as a 3x3 block (`9` pixels) only after scaling
and alpha compositing. It is one of ten such rendered singleton grays; only
`CE/Ce` and `DB/Db` title-case as elements, and choosing Ce by its even/half
properties uses the desired result as selector.

**Status:** retain the arithmetic as a recognition hypothesis, but close it as
a source/consumer chain pending a native or explicitly selected CE and an
instruction choosing difference, halving, or scalar serialization. Full audit:
[doc/GSMG_FIRST_PIECE_CEFE_CHECKERBOARD_GATE_AUDIT.md](GSMG_FIRST_PIECE_CEFE_CHECKERBOARD_GATE_AUDIT.md).

**Brainstorming Applications**:
- Their difference is `58-26=32`, exactly the byte length of a regular Bitcoin private scalar.
- Halving both atomic numbers gives `29` and `13`, both prime; their sum is `42`, a conspicuously Matrix-themed checkpoint.
- Read `CEFE` as an instruction about output size, halving, or splitting rather than as literal password text.
- Keep the transformations bounded to the explicit dual operations suggested by the puzzle: difference, half, and sum-list.

---

### 17. The Two 11-Column Shadow Rows as Dual Rails
> [!NOTE]
> **Audited in Phase 203.** The rows are equal-length ordinal sequences, not
> physical image columns: zero of 11 paired x-boxes overlap, and their center
> offsets are nonconstant. The bounded larger/smaller, tie-mask, sum, and
> difference family produces exact but non-language outputs; no consumer or
> tie rule is selected.
>
> The selected glyph streams and their counts align column-for-column:
>
> ```text
> G S G O 5 B C P U C G     4 1 4 4 2 1 1 1 2 1 4
> G M G C 9 g 2 c P B e     2 1 2 2 1 3 1 1 1 2 2
> ```

**Brainstorming Applications**:
- Choose the upper or lower glyph according to the larger count in each column.
- Treat equal-count columns as fixed centers and unequal columns as yin-yang polarities.
- Convert column sums or differences into an 11-item selector list.
- Assign one rail to DBBI and the other to FAED, preserving their aligned dual structure.
- Apply the creator's “zeroed out” language by retaining only characters whose count equals that row's G reference count; then discard the G calibration symbols, yielding the provisional `OCBe` payload.
- Interpret the equal 11/11 length as a structural reason to combine the rows columnwise instead of concatenating them.
- **Larger/smaller results:** strict unequal-column outputs are `GGO5gUBG` and
  `GGC9BPCe`; ties occur at columns 2/7/8 (`S/M`, `C/2`, `P/c`), producing
  eight unresolved variants per side.
- **Numeric results:** sums `62663422336` (`FBFFCDBBCCF` under A1Z26), absolute
  differences `20221200112`, equality mask `01000011000` (`536`), and sign
  profile `6 upper / 2 lower / 3 ties`. None is plaintext or self-selecting.
- Totals `43` and `7` are forced by `25±18`. Absolute-difference total `13`
  matches the earlier residue count but occurs in 900/2,772 fixed-multiset
  lower-row alignments (`25/77`), so it is weak and post hoc.
- Keep the already verified row-local `G → OCBe → 8,6,4` consumer above this
  ordinal cross-row pairing. Reopen Point 17 only with a clue that explicitly
  zips rows, breaks ties, or names rail consumers.

---

### 18. Element Symbols as a Hand-Built Checkerboard Alphabet Seed
> [!NOTE]
> The cross-phase elemental inventory now includes plausible ordered fragments such as:
>
> ```text
> Ba Tc H | O C Be He | Ce Fe | P H V
> ```
>
> The solved Phase-3.2 checkerboard alphabet was constructed by interpreting and concatenating riddle fragments, deduplicating their letters, and appending unused letters—not by applying a generic keyword formula.

**Phase 206 gate audit:** native-order concatenation and first-occurrence
deduplication reproduce:

```text
BaTcH | OCBeHe | CeFe | PHV -> BaTcHOCBeHeCeFePHV
uppercase first-dedupe                    -> BATCHOEFPV
```

But the fragments are not equally grounded: `OCBe` and `PH->V` are exact;
`BaTcH` failed its execution gate; `He` requires an unselected filter/case
promotion; and `Ce` is render-generated. All 24 fragment orders give 24
different seeds. Adding only the already-declared 26 drop choices, three tail
presets, and two merge directions produces 3,744 parameter rows and 2,430
unique boards. Even the fixed native seed produces 105 boards. With a fixed J
drop, arbitrary ordering of the 15 unused letters alone gives `15!` possible
tails; the known Phase-3.2 board supplies no reusable tail formula.

**Status:** close as underdetermined. `BATCHOEFPV` is a reproducible provisional
seed, not a selected alphabet. Reopen only with explicit fragment order,
deduplication, missing-letter/merge, tail-order, escape, and topology rules.
Full audit: [doc/GSMG_FIRST_PIECE_CEFE_CHECKERBOARD_GATE_AUDIT.md](GSMG_FIRST_PIECE_CEFE_CHECKERBOARD_GATE_AUDIT.md).

**Brainstorming Applications**:
- Preserve element symbols and their case/order instead of immediately reducing everything to atomic numbers.
- Concatenate the independently derived symbols in puzzle-phase order, then deduplicate letters by first occurrence.
- Append unused alphabet letters using an independently selected tail rule to create a candidate DBBI/FAED checkerboard alphabet.
- Let the numeric readings (`56`, `43`, `8,6,4,2,0`, `58,26`) specify ordering or partitioning while the symbols supply actual alphabet letters.
- Treat this as a possible analogue of the earlier hand-parsed checkerboard riddle: the pixel layer may provide alphabet-construction fragments rather than a password.

---

### 19. CE/FE "dual operation" is one identity, not two confirmations
> [!NOTE]
> Splitting `CEFE` into bytes `CE` and `FE` gives `FE − CE = 0x30` and `FE XOR CE = 0x30`, both ASCII `'0'`. These are not independent: `CE`'s set bits (`11001110`) are a strict subset of `FE`'s (`11111110`), so subtraction-without-borrow and XOR are mathematically forced to agree whenever that containment holds. This weakens point 16's "dual operation" framing to one fact stated two ways.

**Brainstorming Applications**:
- Keep the `0x30` = `'0'` observation, but count it once, not twice, when weighing evidence.
- Before treating any future gray-byte-pair agreement as two independent hits, check bit containment first.

---

### 20. A three-way `21` convergence — real dimension match, but not three independent hits
> [!IMPORTANT]
> **Verified in Phase 195, recalibrated in Phase 197** (`tools/gsmg/first_piece_hamming_control_audit.py`, `tools/gsmg/first_piece_bitplane_audit.py`). Three values land on `21`:
> ```text
> FEFEFE popcount                                       = 21
> 24 URL bytes x 7 retained bits (bit-plane residual)   = 168 bits = 21 bytes
> established {1,4,21} character index                 = 21 (predates both of the above)
> ```
> Phase 197 shows the bit-plane `21` is **algebraically forced**, not a free third hit: a 7-bit residual has an integral byte length only when the source length is a multiple of 8, and `21*8/7=24` uniquely ties it back to the already-fixed 24-byte URL and the already-fixed LSB removal. So this is a real, exact dimensional restatement of facts already on the table — not three independently-arrived-at coincidences. Downgrade accordingly: still worth noting, no longer the doc's strongest convergence claim.

**Brainstorming Applications**:
- Keep citing the `21` match as clean and exact, but describe it as "one convergence with a forced restatement," not "three independent hits."
- Use this as the doc's own cautionary example of the calibration discipline urged elsewhere (points 19, 24): dimensional/length matches that follow mechanically from an already-fixed construction don't add new evidence, however tidy they look.

---

### 21. Bit-plane transposition — verification complete: LSB is uniquely prime and staircase-bearing, but weight-9 and "seven passwords" don't hold up
> [!TIP]
> **Verified in Phase 197** ([doc/GSMG_FIRST_PIECE_BITPLANE_VERIFICATION.md](GSMG_FIRST_PIECE_BITPLANE_VERIFICATION.md)). All 8 bit-planes of the 24-byte URL, plus their complements, were computed and inventoried:
> ```text
> bit  direct  weight   complement  weight
>  7   000000     0     FFFFFF        24
>  6   F6FFFF    22     090000         2
>  5   FFFFFF    24     000000         0
>  4   4090C4     6     BF6F3B        18
>  3   2F4128     9     D0BED7        15
>  2   BBAE2F    16     4451D0         8
>  1   DB1088     9     24EF77        15
>  0   F73D92    15     08C26D         9   <- image-selected LSB / its complement
> ```
> Within this bounded 16-member family: **only** bit 0's complement is prime (`574061`), and **only** bit 0 direct/complement has the unit nibble-weight staircase — both properties uniquely mark the image-selected plane. But Hamming weight 9 is **not** unique to it: bit 3 direct and bit 1 direct also have weight 9 (and correspondingly 15 at their complements), so `#383838`'s weight-9 match (points 7, 20) cannot by itself identify the colored plane inside the full URL bit-plane family — it only becomes meaningful *after* the color extraction has already picked bit 0 by other means.
>
> The 7-plane, 21-byte residual is exact but, per point 20, length-forced. Its two natural traversals (plane-major, character-major) are different byte strings and neither is plaintext (5/21 and 7/21 printable bytes respectively). The "seven passwords" reading (point 11) does not survive inspection: bit 7 is all-zero, bit 5 is all-one, bit 6 is 22/24 ones, and none of the seven planes (direct or complement) is prime.

**Brainstorming Applications**:
- Promote: the full plane inventory, LSB/image equality, and prime+staircase uniqueness at bit 0 — these are now structural facts, not brainstorm.
- Retire the "seven remaining planes = seven passwords" framing from point 11; the planes are structured but not password-shaped on inspection.
- Note for point 7/14 (the `#383838` weight-9 match): its evidentiary weight rests entirely on the independently-supplied G-shadow selector (Phase 188), not on Hamming weight being distinctive — this pass confirms that dependency directly rather than just asserting it.
- Next queued target (per the verification's own next-step note): measure whether `{1,4,21} -> ggn` is structurally distinctive among comparable index triples, ahead of any secp256k1 reading (point 22).

---

### 22. `{1,4,21} -> ggn` — verification complete: exact and uniquely located, but not distinctive enough to force secp256k1
> [!NOTE]
> Phase 198 ran the distinctiveness check this point called for. `{1,4,21}` one-based flattens to `ggn` (colors `BBY`); zero-based gives `s.t` (colors `BYY`) — so the reading is convention-dependent, not convention-free. Across all `C(24,3)=2,024` increasing index triples of `gsmg.io/theseedisplanted`, exact `ggn` is unique (1/2,024), but that kind of uniqueness is common: 519/2,024 triples (25.6%) emit a string no other triple emits. The `xxy` repeated-first-symbol shape occurs 85/2,024 (4.2%); requiring the third character to also be globally unique in the URL narrows it to 36/2,024 (1.8%) — still not rare enough to select `ggn` on its own. The color channel doesn't independently confirm the indexing choice either: `BBY` (546/2,024) and `BYY` (311/2,024) are both ordinary patterns. Turning literal `ggn` into `kG`/`(n-k)G` further requires promoting `g`->`G`, parsing repeats as group operations, reading `n` as curve order, *introducing* an absent scalar `k`, and picking secp256k1 over any other cyclic group — none of which is forced by the extraction itself. The underlying group identity `(n-k)G = -kG` is correct but generic, so verifying it would confirm textbook group theory, not that `ggn` is an instruction.

**Brainstorming Applications**:
- Retain `ggn` as an interesting, exactly-located structural side-reading — do not discard it — but park the secp256k1/`kG` theory until an independent clue explicitly supplies a scalar `k` or a negation/order operation.
- The G-shadow hindsight risk flagged in the original version of this point is now compounded by a second finding: even setting hindsight aside, `ggn`'s brand of "exact and unique" is unremarkable within its own comparison family (~1 in 4 triples share that property), so exactness alone can't carry the interpretation.
- Do not use `ggn`/`G,G,n` to select or justify any oracle candidate.

---

### 23. `400/401/73` independently reconstructed, with the cutoff externally fixed
> [!IMPORTANT]
> **Verified in Phase 196** (`tools/gsmg/first_piece_prime_sum_reconstruction.py`, [doc/GSMG_FIRST_PIECE_PRIME_SUM_VERIFICATION.md](GSMG_FIRST_PIECE_PRIME_SUM_VERIFICATION.md)). Assigning the first 25 sequential primes to the 24 color events plus FEFE in spiral order, under the sourced `b`/`be` DBBI token grammar, gives blue sum `401`, yellow sum `400`, and FEFE (the 21st prime) `73`. The 23-event cutoff isn't a balance chosen after the fact — event 23 is the last one that fits inside the 91-symbol DBBI stream before event 24 overruns it, and prefix 23 is independently the *only* prefix with `|blue−yellow| ≤ 1`.

**Brainstorming Applications**:
- Treat `400/401/73` as load-bearing rather than speculative going forward — it survived independent re-derivation without importing the original color-prime sum audit.
- Note the dependency: the result requires keeping FEFE as its own third event type (folding it into blue instead gives `474/400`, breaking the split) and requires the specific `b`/`be` token grammar — both are real assumptions, not free.
- Descriptive calibration: 813/319,770 fixed-profile assignments (≈0.0025) reproduce `|B−Y|≤1`; recognized post hoc, not preregistered — same caveat class as the nibble-staircase rate in point 20.

---

### 24. `144/144/72`: FE-mask composition is real but adds no independent evidence
> [!NOTE]
> Applying the Phase 195 FE byte-mask uniformly to `401/400/73` (no byte or value selected) gives `144/144/72` — the two color rails become exactly equal, and FEFE's channel becomes exactly half of either. It's encoding-robust (invariant to byte width and endianness) and depends specifically on the repeated-`FEFE` byte semantics, not just clearing one bit. **But** calibration shows this is not a second confirmation: conditioned on FEFE fixed at prime `73`, the same 813 assignments that produce the `400/401` near-balance are *exactly* the ones that produce `144/144/72` — it's a deterministic normalization of point 23's structure, not new statistical support.

**Brainstorming Applications**:
- Keep `144/144/72` as a documented mechanical fact, but do not count it alongside `400/401/73` as if they were two independent hits — this is the same trap flagged in point 19 (CE/FE), now confirmed at the composition-calibration level rather than by inspection.
- Do not promote `144/144/72` as a password/key candidate on its own; its best current reading is "FE equalizes the rails," a property statement about the mask, not a new derived secret.

---

### 25. Border and raster grid-scan readings — closed negative, no side-based reading rivals the spiral

> [!NOTE]
> **Audited in Phase 208.** Tested whether reading the 14x14 grid from its
> four sides (rather than the established counterclockwise spiral) produces
> anything comparable, at three levels of literalness.

**Brainstorming Applications**:
- **Border-only** (just the outer row/column facing each side): carries
  almost no signal — `top=WWKKWBWWKWKKWY`, `bottom=WKBWKKWKKWBWKK`,
  `left=WKKWWKKBWKKKWW`, `right=YKKKWKWWBKKWWK`, each with only 1-2 colored
  cells. The 24 informative cells are interior, not edge-concentrated.
- **Nearest-inward** (first colored cell scanning in from each side, per
  row/column): `blue/yellow` = `12/2` (left), `6/8` (right), `9/5` (top),
  `8/5`+1 FEFE (bottom). One fact worth remembering: FEFE (row 8, column 5,
  one-based) is the nearest colored cell to the bottom edge in its own
  column — a single positional fact, not treated as rare.
- **Full-raster** (whole grid read top-down/bottom-up/left-right/right-left,
  keeping only colored cells, the same "colored-cells-only" rule the spiral
  reading uses but with a raster path): gives four distinct 24-bit blue=1
  values — `0xBE2B9B`, `0xEAE8BE`, `0xFFCA51` (prime, `16763473`), and
  `0x4A63FF`. None matches or reverses into the authenticated spiral answer
  `BBBBYBBBYYBBBBYBBYYBYYBY`. The one prime hit is unremarkable at a 1-in-4
  try rate against a ~1-in-16 base rate — unlike `574061`, which is
  independently anchored by the `yellowblueprime` clue text rather than
  selected after the fact from a small ordering family.
- **Status:** close all three readings as negative controls. Reopen only if
  another clue explicitly names a side-based or raster traversal of this
  grid. Full audit: [doc/GSMG_FIRST_PIECE_BORDER_RASTER_SCAN_AUDIT.md](GSMG_FIRST_PIECE_BORDER_RASTER_SCAN_AUDIT.md).

---

## Summary Matrix of Proposed Next Steps

```mermaid
graph TD
    A["Stage 0 First Image Color Data"] --> B["574061 2x3 Matrix"]
    A --> C["24-Bit Yellow/Blue Mask"]
    A --> D["14x14 Grid Geometry"]
    A --> E["#F73D92 & #FEFEFE RGB Tuples"]

    B -->|x [23,16,7]^T| B1["Vector [255, 103] -> White + 'g' Key Prefix"]
    C -->|MUX Stream| C1["Interleave DBBI (Blue) & FAED (Yellow)"]
    C -->|Partition| C2["Extract 9-char Yellow Rail & 15-char Blue Rail"]
    D -->|2D Stencil| D1["Cardan Grille Overlay on Phase 2/3 Images"]
    E -->|RGB Diff| E1["Difference Vector (7, 193, 108) -> Modular Keys"]
```

---

## Recommended Sequence for Future Verification Phases

**Superseded 2026-08-09**: the four phases originally listed here predate
points 7-24 and Phases 195-198. `[255,103]` has not yet been tested against
ciphertext blobs — that step is intentionally deferred below, not skipped.

Already handled (Phases 195-198, folded into points 19-24):

- Points 19-20: CE/FE arithmetic redundancy; the `21` convergence downgraded
  from three independent hits to one convergence with a forced restatement.
- Point 21: complete 8-plane bit-plane audit (LSB uniquely prime/staircase;
  weight-9 not unique; "seven passwords" retired).
- Point 22: `{1,4,21} -> ggn` distinctiveness audit (exact and unique, but
  that flavor of uniqueness is common; secp256k1 reading parked).
- Points 23-24: `400/401/73` prime-walk reconstruction and its FE-mask
  composition (`144/144/72`, not independent evidence).

Current ranked queue, bounded structural audits first, oracle/blob tests
deferred until a candidate earns them:

1. **Point 1 — `[255,103]` matrix product.** Independently-established
   inputs (`574061`, `[23,16,7]`). Verify orientation sensitivity, the
   permutation family, and how often comparable outputs resemble
   `FF + printable ASCII`, before testing `0xFF67` against any blob.
2. **Points 8 and 11 — second `matrixsumlist`.** Independently reconstruct
   `[43,25,18]`, then audit `[43,25,18]-[23,16,7]=[20,9,11]`, reversed
   `[11,9,20] -> KIT`, and whether `20=9+11` reflects real additive grammar
   or a free choice.
3. **Points 2 and 4 — preserve the `14/8/1` event rails.** Test
   token-preserving structures (14 blue singleton events, 8 yellow digraph
   events, 1 FEFE event) rather than flattening; check whether the 14 blue
   events map onto the 14 matrix rows without inventing a traversal.
4. **Point 9 — PNG palette/index provenance.** Cheap and decisive: does the
   FEFE cell have a real palette index, or is the PNG truecolor (in which
   case this idea has no native footing)?
5. **Point 17 — aligned 11-column shadow rails.** Only predeclared column
   operations: upper/lower by count, equality mask, sums, differences. No
   free-form mixing.
6. **Points 12-13 — `86420`, `13579`, `igecabdfh`.** Weakened because the
   trailing zero was previously supplied too freely; needs independent
   recovery of all five even digits before testing the alphabet permutation.
7. **Point 14 — `BaTcH`/BATCH.** Phase 205 reproduces the exact rebus and the
   later `OCBe` result now establishes element vocabulary, but the inverse
   atomic lookup, value-before-count order, singleton `H`, and batch execution
   grammar remain unselected. Closed as an instruction; retained as a strong
   recognition/checkpoint hypothesis.
8. **Points 16 and 18 — `Ce/Fe` and checkerboard seed.** Phase 206 confirms
   the exact arithmetic and provisional `BATCHOEFPV` seed, but CE is a rendered
   composite gray rather than a source-favicon pixel and the board has 2,430
   bounded variants before arbitrary tail order. Both points are closed
   pending explicit source and construction rules.
9. **Points 3, 5, 6 — overlays, DNA cipher, RGB-vector geometry.** Phase 207
   closes all three gates: at least 72 overlay variants before registration
   choices, 72 distinct DNA translations, and no RGB-vector consumer. Retain
   only the exact `(7,193,108)` difference/red-channel 7; correct the DNA byte
   count and the inconsistent `NIQ` mapping.

**Ranked queue complete as of Phase 207.** Every item above is verified,
closed, or explicitly retained as a recognition-only hypothesis; nothing on
this list remains open. Phase 208 (point 25) ran one unranked supplementary
check — border/raster readings of the 14x14 grid — and also closed negative.
No first-piece pixel-data idea currently selects an oracle test; any further
work here needs a new external clue, not another internal-structure sweep.
