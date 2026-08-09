# GSMG `matrixsumlist` Reconstruction Checkpoint

> **Supersession note (Phases 216–217):** the film/screenplay-stable result is
> BUT/HYE and the bounded `b <-> h`, `e`-fixed mirror state. This document's
> later `H` + initials-of-“your eyes” + `BUT` rebus was removed as circular and
> must not anchor subsequent work. VAT/SALVATION is likewise post-hoc and
> oracle-negative.

## Strong finding

The creator's raw binary message decodes exactly to:

```text
yellowblueprimesmatrixsumlistlastwordsbeforearchichoiceyinyang...
```

The first-piece reconstruction gives the complementary yellow/blue number:

```text
000010001100001001101101 = 0x08C26D = 574061
```

`574061` is prime. Writing its decimal digits as the natural 2×3 matrix:

```text
5 7 4
0 6 1
```

produces:

```text
row sums: 16, 7
matrix total: 23
```

Therefore the literal operation `matrix sum list` yields:

```text
23, 16, 7
```

Those are exactly the three conspicuous values in the already-solved,
creator-authored Architect plaintext:

```text
...select from over twenty-three ciphers,
sixteen encryptions and or seven intertwined passwords...
```

This is substantially stronger than previous speculative uses of `23/16/7`.
It is derived directly and sequentially from the creator's clue chain:

```text
yellow/blue polarity -> prime 574061
prime digits -> 2×3 matrix
matrix total + row-sum list -> 23,16,7
```

The earlier cross-phase construction involving these numbers was correctly
debunked because its `yang` validation and token mask were apophenic. That does
not invalidate this new derivation, which does not use that mask or its null
model.

## Why 2×3 is bounded

- The prime has exactly six decimal digits.
- Two rows follow the two complementary yellow/blue polarities.
- Three columns match the RGB/three-channel representation that produced the
  rose-colored complement.
- The alternative 3×2 orientation does not produce row sums `16,7`.
- The known Architect plaintext independently supplies `23,16,7` as a
  validation target; the orientation was not selected for English-looking
  output.

This rationale still needs to be encoded in an assertion-backed script and
checked for uniqueness across the complete bounded orientation family.

## Continued reconstruction

The next token is:

```text
lastwordsbeforearchichoice
```

The exact source is now frozen to the Architect scene in
`wordlists/matrix/the-matrix-reloaded-2003.pdf` (SHA-256
`2b9d43c9bb32fe85b1ed7651b095855e6ea7a25a236853d7823ea92b211d0db4`).
Only the Architect's two dialogue blocks before the word `choice` are
tokenized; screenplay labels and stage directions are excluded.

**Provenance caveat (2026-08-04):** the frozen PDF is a draft screenplay, not
a film transcript, and its wording is not always identical to what was
actually shot. Block 1 (the "moment of truth ... both beginning and end"
monologue) was checked word-for-word against an independent quote source
(quotes.net/mquote/121335) and matches the PDF exactly. Block 2 (the "two
doors" speech) does *not* match: the PDF reads "the door on your right will
take you to the Source", while the actual film line, independently confirmed
via quotes.net/mquote/121335 and a user-supplied transcript, is "The door to
your right leads to the Source." This does not affect the selected chain
below, since positions `7/16/23` (`both`/`ultimately`/`the`) all fall inside
block 1, which is unaffected by the drift. It does mean the *backward*-indexed
alternates in the table below (`your to as`, `to matrix species`), which were
never adopted, were computed against the wrong wording for block 2 and would
change under the real film text — flagged here so nobody builds on them later
without re-deriving from the correct wording.

Applied `23,16,7` under the preregistered conventions:

| Convention | Selected words | Initials | Final letters |
|---|---|---|---|
| Forward, one-based | `both ultimately the` | `BUT` | `HYE` |
| Forward, zero-based | `beginning expressed moment` | `BEM` | `GDT` |
| Backward, one-based | `your to as` | `YTA` | `ROS` |
| Backward, zero-based | `to matrix species` | `TMS` | `OXS` |

The forward one-based result has an objective boundary check: `BUT` is exactly
the Architect's first spoken word after `choice`. None of the other three
bounded conventions has that property.

The selected source sentence itself contains the “both beginning and end”
language. Reading both ends of the selected words gives the complementary
rails:

```text
beginnings: B U T
ends:       H Y E
```

This now has a concrete yin-yang reading in the puzzle's own `a`-through-`i`
symbol alphabet:

```text
B <-> H    mirror opposites across E
E -> E     fixed center
```

Filtering the two rails to valid 9-ary symbols gives `B` and `HE`. Thus the
rails derive the previously hypothesized complementary escape pairs `{b,e}`
and `{h,e}` rather than merely borrowing them from a generic symbolism guess.

Reading the end rail before the beginning rail also gives:

```text
HYE BUT = H | YE | BUT
```

This is a compact rebus for the creator's immediately following wording:
`H` is in front of the initials of “your eyes,” followed by literal `BUT`.
It makes `H` a grounded candidate, though not yet a confirmed password.
As a secondary standard operation, ordering the end rail by the alphabetical
order of the beginning rail (`BUT` as a three-column key) changes `HYE` to
`HEY`.

Applying the same matrix sum list as direct Caesar additions to the end rail:

```text
H + 23 = E
Y + 16 = O
E +  7 = L
```

produces **`EOL`**, the conventional abbreviation for “end of line.” This
independently agrees with the final page's embedded `enter` instruction and
newline-sensitive command grammar.

`tools/gsmg/prime_matrixsum_reconstruction.py` extracts the relevant PDF
blocks locally and asserts:

- `574061`;
- unique `forward_2x3_rows` orientation for row sums `16,7`;
- total/list `23,16,7`;
- unique forward one-based boundary match;
- `BUT` / `HYE`;
- `B <-> H` with fixed center `E` under `mirror9`;
- `HYE + BUT = H | YE | BUT`;
- beginning-keyed ordering `HYE -> HEY`;
- `HYE + [23,16,7] = EOL`.

An exact enumeration of all `72P3 = 357,840` ordered triples in the frozen
Architect source found:

- 160 triples whose initials equal the fixed boundary word `BUT`;
- 24 whose endings shifted by their own indices equal observed marker `EOL`;
- 4 satisfying both, including independently derived `(23,16,7)`;
- 12 satisfying `BUT` plus observed beginning-keyed end word `HEY`, again
  including `(23,16,7)`.

These are descriptive source-internal counts, not preregistered p-values:
`EOL` and `HEY` were recognized after seeing the selected output.

## Direct-oracle result

Tested 12 bounded forms from the selected phrase, both edge rails, `EOL`, and
“end of line” against all three authenticated blobs plus quarantined URLBLOB:

```text
CBC: 216 unique keystrings x 24 original+extended variants x 4 blobs, 0 hits
Key Wrap: 306 generated passphrase attempts x 4 blobs, 0 unwrap hits
```

Therefore `BUT`, `HYE`, and `EOL` are not direct blob passwords under the
supported oracle families.

Follow-up checks:

- direct extended-CBC and Key-Wrap tests of newly implied single-letter `H`
  against all four tracked blobs: 0 hits;
- SHA-256 route forms of `H`, `HEY`, `HYE`, and `HYEBUT`: no match in the
  local site mirror or archived path inventory;
- exact Architect-derived alphabet seeds under `dbbi/{b,e}` and
  `faed/{h,e}`, both escape orders and topologies, all 26 drop letters, all
  three tail fills, both merge directions, and all six standard AES KDF
  variants: 10,608 structural configurations per target, 0 hits.
- complete curated product sweeps under `faed/{h,e}`: 280 alphabet candidates
  x 280 keystream candidates, both escape orders; chain-addition 78,400 pairs /
  627,200 decode attempts, 0 hits; autokey 78,400 pairs, 0 hits.

## Next steps

1. Treat `BUT` as a boundary checksum, not a password.
2. Treat `EOL` as an operation (`Enter`/newline), not another wordlist seed.
3. Apply newline semantics only after a grounded `dbbi` or `faed` plaintext is
   recovered; generic newline variants have already been exhausted.
4. Treat `B <-> H` around fixed `E` as the strongest current candidate for the
   promised yin-yang state. The curated `{h,e}` checkerboard,
   chain-addition, and autokey branches are now negative; only the much larger
   dictionary autokey continuation remains incomplete.
5. Determine which non-blob lock, if any, the `H | YE | BUT` rebus addresses.
6. Do not treat the formerly missing `barrystyle` post as an unknown
   acceptance criterion. Transcript context identifies it as the already
   investigated *Cosmic Duality* book discovery; only that book's physical
   pages 57-58 remain unavailable.

## Status

The chain is now strongly reconstructed through:

```text
yellowblueprimes
-> 574061
-> matrixsumlist [23,16,7]
-> words before Architect choice: BOTH / ULTIMATELY / THE
-> beginning/end rails: BUT / HYE
-> yin-yang symbols: B <-> H around fixed E
-> rebus: H | YE | BUT
-> end rail + sum list: EOL
-> Enter/newline
```

This is a coherent instruction chain with internal checks, but it has not yet
opened a blob or produced a Bitcoin private key.
