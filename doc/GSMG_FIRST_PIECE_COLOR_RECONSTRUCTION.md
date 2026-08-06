# GSMG First-Piece Yellow/Blue Reconstruction

## Result

The creator's `yellowblueprime` instruction now has an exact reconstruction
from the original first-piece image:

```text
validated spiral colors:
BBBBYBBBYYBBBBYBBYYBYYBY

blue=1, yellow=0:
111101110011110110010010 = 0xF73D92 = RGB(247,61,146)

yellow=1, blue=0:
000010001100001001101101 = 0x08C26D = 574061
574061 is prime
```

The direct polarity produces a rose/pink RGB color, matching “Roses are White
but often Red.” The complementary polarity produces a prime, matching the
creator's later ordered token `yellowblueprime`.

## Provenance

- Original full puzzle PNG:
  `doc/img/gsmg_puzzle_stage1.png`
- SHA-256:
  `38125bbdf1ea58b9b30b075bc6bf71e4089d04bba37098317e47097e2f2a1830`
- Archived embedded rabbit grid:
  `doc/img/gsmg_rabbit_hint.png`
- SHA-256:
  `5e8d84b88f8f829428df5d2a8bf36c7268346f169b799ac7570b6223990d204f`
- The embedded grid is byte-identical to the independently mirrored
  `follow_the_white_rabbit.png`.

The reading order was not selected for primality. It was already fixed by the
independently verified Stage-0 solution: top-left start, counter-clockwise
spiral, black/blue=1 and white/yellow=0, which decodes exactly to
`gsmg.io/theseedisplanted`.

## Exact objects

The 24 yellow/blue cells are exactly the last bit of each decoded URL
character. There are 15 blue and 9 yellow cells.

| 1-index | 0-index | URL char | ASCII | Color | B=1 bit | Y=1 bit | Grid row | Grid column | Spiral position |
|---:|---:|:---:|---:|:---:|---:|---:|---:|---:|---:|
| 1 | 0 | g | 103 | blue | 1 | 0 | 8 | 1 | 8 |
| 2 | 1 | s | 115 | blue | 1 | 0 | 14 | 3 | 16 |
| 3 | 2 | m | 109 | blue | 1 | 0 | 14 | 11 | 24 |
| 4 | 3 | g | 103 | blue | 1 | 0 | 9 | 14 | 32 |
| 5 | 4 | . | 46 | yellow | 0 | 1 | 1 | 14 | 40 |
| 6 | 5 | i | 105 | blue | 1 | 0 | 1 | 6 | 48 |
| 7 | 6 | o | 111 | blue | 1 | 0 | 5 | 2 | 56 |
| 8 | 7 | / | 47 | blue | 1 | 0 | 13 | 2 | 64 |
| 9 | 8 | t | 116 | yellow | 0 | 1 | 13 | 10 | 72 |
| 10 | 9 | h | 104 | yellow | 0 | 1 | 8 | 13 | 80 |
| 11 | 10 | e | 101 | blue | 1 | 0 | 2 | 11 | 88 |
| 12 | 11 | s | 115 | blue | 1 | 0 | 2 | 3 | 96 |
| 13 | 12 | e | 101 | blue | 1 | 0 | 10 | 3 | 104 |
| 14 | 13 | e | 101 | blue | 1 | 0 | 12 | 9 | 112 |
| 15 | 14 | d | 100 | yellow | 0 | 1 | 7 | 12 | 120 |
| 16 | 15 | i | 105 | blue | 1 | 0 | 3 | 8 | 128 |
| 17 | 16 | s | 115 | blue | 1 | 0 | 7 | 4 | 136 |
| 18 | 17 | p | 112 | yellow | 0 | 1 | 11 | 8 | 144 |
| 19 | 18 | l | 108 | yellow | 0 | 1 | 6 | 11 | 152 |
| 20 | 19 | a | 97 | blue | 1 | 0 | 4 | 5 | 160 |
| 21 | 20 | n | 110 | yellow | 0 | 1 | 10 | 7 | 168 |
| 22 | 21 | t | 116 | yellow | 0 | 1 | 5 | 10 | 176 |
| 23 | 22 | e | 101 | blue | 1 | 0 | 9 | 6 | 184 |
| 24 | 23 | d | 100 | yellow | 0 | 1 | 6 | 7 | 192 |

The reconstruction is executable and assertion-backed:

```bash
python3 tools/gsmg/first_piece_color_reconstruction.py --table markdown
```

## Alternatives checked

- **Raw cell RGB numbers:** blue is `3F48CC` / `(63,72,204)` and yellow is
  `FFF200` / `(255,242,0)`. These are exact source facts but do not explain
  the ordered word `prime`.
- **Color counts:** blue=15 and yellow=9 are exact but likewise do not produce
  the creator's rose/prime dual result.
- **Resistor color values:** the poem's four named colors can evoke the
  resistor code (white=9, red=2, yellow=4, blue=6), but the resulting
  yellow/blue stream is even and does not explain `yellowblueprime`.
- **Raster/reversed orders:** these are unnecessary degrees of freedom. The
  known Stage-0 plaintext fixes the spiral order before this extraction.

## `{1,4,21}` resolved

Applying the later creator values directly to these 24 objects gives:

| Index convention | URL characters | Colors | B=1 bits | Y=1 bits |
|---|---|---|---|---|
| One-based | `ggn` | `BBY` | `110` | `001` |
| Zero-based | `s.t` | `BYY` | `100` | `011` |

Neither flat extraction supplies a self-validating door because the tuple is
hierarchical, not three peer indices. The clue was posted on `01.04.2021`,
giving it an April-Fools camouflage, while the same-day `18-1-2 + BIT =
RABBIT` wordplay points to the rabbit grid. In that grid:

```text
1   = exactly one FEFE cell
4   = its one-based bit position within its byte
21  = its one-based character position in gsmg.io/theseedisplanted
```

The marked cell is bit value `0` inside character 21, `n`. Its zero-based
spiral position is `163`, which is prime; its one-based position `164` is not.
This simultaneously explains the creator's first/zero ambiguity, prime
requirement, and later “zeroed out” wording without selecting a convention
after the fact. `first_piece_color_reconstruction.py` asserts every part of
this descriptor directly from the archived image.

Literal follow-ups are negative. Exact raw/SHA-256 route forms and
extended-CBC/Key-Wrap checks for `163`, `FEFEFE`, `n`, `1812bit`, `rabbit`,
and zero/remove/flip forms of character 21 produce no hit. Zeroing every
zero-based prime-indexed spiral bit yields
`Bc,b*(k+d(e3 a$hc hanpad`; extracting the 44 prime-indexed bits yields
non-text binary. The locator is real, but those direct consumption rules are
closed.

## Direct-oracle check

Saved the exact grounded forms in
`wordlists/gsmg/first_piece_color_candidates.txt` and tested them against all
three authenticated blobs plus quarantined `URLBLOB`:

```text
CBC:
  20 candidates
  261 unique keystrings
  24 original+extended cipher/KDF variants
  4 blobs
  0 hits

AES Key Wrap:
  20 candidates
  540 generated passphrase attempts
  4 blobs
  0 unwrap hits
```

The values are therefore an intermediate instruction/output, not a direct
password under the currently supported oracle families.

## Next operation

The creator's ordered chain now begins with a concrete value:

```text
yellowblueprime = 574061
next instruction = matrixsumlist
```

The remaining question is no longer “what numbers belong to yellow and
blue?” It is: **what creator-supported matrix and sum/list operation consumes
the prime `574061`?** The formerly missing creator-validated `barrystyle` post
is now identified from transcript context as the already-investigated
*Cosmic Duality* book discovery, so it does not independently specify that
operation.

A separate community observation treats the complete 14x14 yellow occupancy
mask as 196 bits, then reverses and inverts it. It reproducibly yields the
60-digit prime
`100433436204244105573859228564110291168344943733122168512511`, but a
profile-preserving family-wise shuffle test gives stable `p≈0.059`. It remains
unpromoted and does not replace the compact `574061` chain; see
`tools/gsmg/first_piece_full_mask_audit.py`.
