# GSMG Minimal Creator-Macro Chain Audit

## Result

The creator-authored macro begins with the continuous four-step sequence:

```text
yellowblueprimes -> matrixsumlist -> lastwordsbeforearchichoice -> yinyang
```

That prefix can already be consumed by the short prime-digit reconstruction:

```text
yellow=1 / blue=0
-> 574061
-> `[[5,7,4],[0,6,1]]`
-> total and row sums [23,16,7]
-> Architect words BOTH / ULTIMATELY / THE
-> beginnings BUT; endings HYE
-> a-i symbols b / he
-> mirror9: b <-> h, while e is fixed
```

The new two-source boundary audit strengthens the middle of this chain. The
film and frozen screenplay have different full scopes (69 versus 72 words),
yet forward one-based `[23,16,7]` selects the same three words in both. `BUT`
is also the literal first spoken word after `choice`, so the beginnings rail
has a source-native boundary check.

This is a recognition path, not a decryption. In particular, it does **not**
show that `{h,e}` decrypts FAED, and it does not make the alphabetical
adjacency `g-h-i` relevant. The actual bounded involution here is only
`b <-> h` with `e` fixed in the `a-i` alphabet.

Two previously proposed continuations are deliberately excluded:

- `H | YE | BUT` chooses the initials of “your eyes” after `HYE` is already
  known. The resulting equality is circular and supplies no independent check.
- `VAT -> SALVATION` is the pre-existing Phase 96 rebus. Its word subset and
  removal rule were motivated after noticing the title relation, and its direct
  oracle family produced zero hits. It remains an oracle-negative curiosity,
  not a checkpoint in this chain.

## What this changes

The exact 31-character DBBI selection
`ncsyangcahiriasogaleafayanestve` remains real, but treating it as the operand
of `matrixsumlist` is not the only macro grammar. That branch still lacks
matrix dimensions, placement, letter values, aggregation, and serialization.

By contrast, the six-digit-prime branch reaches the robust BUT/HYE checkpoint
using a short sequence and no ciphertext oracle. Phase 223 subsequently showed
that the partial mirror9 reading is not distinctive enough to establish the
macro's next named state, `yinyang`: its strict positional form fails, and its
set form is invariant under all six word permutations. The branch remains the
better current explanation of the path through `lastwordsbeforearchichoice`,
but not of `yinyang` itself. The selected 31 characters
should not remain the default operand merely because they were recovered more
recently.

This does not upgrade the whole chain to creator-confirmed. Three judgment
calls remain visible:

1. arranging the six decimal digits as the forward 2x3 matrix;
2. reading “sum list” as total followed by row sums;
3. taking both beginnings and endings of the selected words.

The film/screenplay agreement and literal `BUT` boundary substantially check
the result, but they do not retroactively turn those conventions into explicit
instructions.

## Revised boundary

The narrow supported comparison is:

```text
six-digit prime operand
-> reaches the BUT/HYE boundary checkpoint
-> yinyang interpretation remains unverified

31-character DBBI operand
-> stops at matrixsumlist because its consumer is unspecified
```

Therefore the six-digit-prime route should be the default working hypothesis
for the creator macro. This audit does not determine the next instruction or
password role. Existing direct-password negatives remain in force and neither
VAT/SALVATION nor `H | YE | BUT` should anchor the next investigation.

## Reproduction

```bash
python3 tools/gsmg/minimal_macro_chain_audit.py --self-test
```
