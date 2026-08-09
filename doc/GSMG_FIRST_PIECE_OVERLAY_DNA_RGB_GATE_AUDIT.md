# First-Piece Overlay, DNA, and RGB-Vector Gate Audit

## Scope

This final ranked audit covers Points 3, 5, and 6 using only bounded,
predeclared convention families:

- the yellow/FEFE coordinates as a 14×14 overlay under the eight rectangle
  symmetries;
- all distinct blue/yellow assignments to two DNA bases, two directions, and
  three circular codon frames;
- ordinary signed/absolute differences, vector quantities, modulo-26 reads,
  and `[23,16,7]` shifts for `F73D92` and `FEFEFE`.

No visual-feature interpretation, language scoring, password test, or blob
oracle is run because no branch passes its selection gate.

## Point 3: Cardan-grille overlay

The grid supplies exact aperture sets:

```text
yellow cells: 9
FEFE cell:    1
union:       10
```

Each set has eight distinct D4 orientations. The three targets named in the
brainstorm have dimensions:

```text
phase2.png                       812 × 415
phase3.png                       812 × 893
SalPhaselonCosmicDuality.png     668 × 619
```

None has both dimensions divisible by 14, so none supplies a native equal-cell
14×14 registration. Merely choosing target × aperture set × orientation gives
`3 × (8+8+8) = 72` variants under one normalized full-image fit. This is a
minimum: crop/contain/cover rules, offsets, center-vs-area sampling, color
channels, and the conversion of sampled image features into characters remain
unspecified.

**Verdict:** close. The aperture coordinates are real, but an overlay is not a
consumer until another artifact identifies a target, registration, orientation,
sampling rule, and feature decoder.

## Point 5: DNA/genetic cipher

The proposed 24-symbol endpoint stream contains only blue and yellow, not all
four ordinary grid colors:

```text
BBBBYBBBYYBBBBYBBYYBYYBY
```

It therefore carries 24 binary bits, or 3 packed bytes. Even if it contained
four equally used palette states and encoded two bits per symbol, 24 symbols
would carry 48 bits, or 6 bytes—not the claimed 12-byte key. Encoding each
color name/base as a byte would produce 24 bytes but would be a different,
ASCII-level convention.

Using the full 14×14 grid does not fix this: black, white, blue, and yellow are
joined by the distinct FEFE marker, creating a fifth state that must be folded
or discarded.

For the endpoint stream, assigning distinct DNA bases to blue/yellow gives
`4P2 = 12` mappings. Combining two directions and three circular codon frames
gives 72 translations, all with distinct DNA strings and distinct amino-acid
strings. Reverse complement adds no independent family because complementing
the two assigned bases is already represented among the twelve mappings.

The brainstorm's explicit `blue=G, yellow=T`, forward, frame-zero convention
gives:

```text
DNA:   GGGGTGGGTTGGGGTGGTTGTTGT
codons GGG GTG GGT TGG GGT GGT TGT TGT
amino: G V G W G G C C
```

It is exact but not self-selecting, and `seed/planted` supplies theme rather
than a genetic-code instruction.

**Verdict:** close. Reopen only with an explicit base assignment, treatment of
FEFE, direction/frame, and amino/byte consumer.

## Point 6: RGB-vector geometry

The signed anomaly-minus-rose difference reproduces exactly:

```text
(254,254,254) - (247,61,146) = (7,193,108)
sum                                  = 308
squared Euclidean norm               = 48,962
Euclidean norm                        = 221.2735863134...
```

Its component observations are also exact:

- `7` matches the third term of `[23,16,7]`;
- `193` is prime;
- `108` is printable ASCII `l`.

Across all 256 repeated-gray bytes with the rose fixed, exactly one produces
signed red difference 7, and that same row also has prime green difference and
printable blue difference. This is a fixed-family description, not a valid
post-hoc p-value: subtraction direction, channel properties, and the choice to
interpret only the third channel as ASCII were identified after seeing the
tuple. The exact red-channel 7 can be retained as a recognition coincidence,
but it does not choose a consumer.

The modulo claim needs correction:

```text
(247,61,146) mod 26 = (13,9,16)
A=0 -> NJQ
A=1 -> MIP
```

`NIQ` mixes conventions and is not a consistent mapping. Under `A=0`, the
difference vector gives `HLE`; adding `[23,16,7]` gives `KZX`, and subtracting
it gives `QTJ`. None is selected or recognizable instruction text.

**Verdict:** retain `(7,193,108)` and especially the red-channel `7` as exact
arithmetic. Close modulo-letter and shift consumers pending a clue selecting
subtraction direction, channel interpretation, indexing, and downstream role.

## Overall result

All three ideas are mechanically possible but underdetermined at their first
consumer boundary. Their failures are structural rather than failed password
guesses, so no oracle expansion is warranted.

Reproduce with:

```bash
python3 tools/gsmg/first_piece_overlay_dna_rgb_gate_audit.py --self-test
```
