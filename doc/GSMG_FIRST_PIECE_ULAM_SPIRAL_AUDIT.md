# GSMG First-Piece Ulam-Spiral Audit

**Date:** 2026-08-27
**Status:** Closed negative under one predeclared convention. Not a claim that no Ulam-spiral numbering of this grid could ever work.

## Prompt

A community post (`x.com/Math_files/status/2092632301415047597`) proposes
numbering the cells of the first-piece image using an Ulam prime spiral,
rather than the established counterclockwise-from-corner spiral that already
decodes to `gsmg.io/theseedisplanted`. The tweet's image itself could not be
fetched (X returns HTTP 402 to non-browser tools), so the exact starting
cell/direction it depicts is unknown. The user asked to proceed with the
textbook Ulam-spiral convention instead of guessing at the tweet's specific
variant.

## Predeclared convention

Per the [Ulam spiral](https://en.wikipedia.org/wiki/Ulam_spiral) construction:
value `1` at the center, first step to the right, turning counterclockwise
(right, up, left, down), run lengths `1,1,2,2,3,3,...`.

The 14x14 grid has no single center cell (14 is even). Value `1` is fixed at
the 0-indexed cell `(6, 6)` — flagged as an assumption before running, not
chosen after seeing results. This is one specific, reasonable choice among
several possible center cells for an even-sized grid; it is not the only
one, and it is not confirmed as the tweet's own choice.

`tools/gsmg/first_piece_ulam_spiral_audit.py` implements this against the
same majority-vote grid the verified spiral reconstruction uses. No word
list, cipher, or blob oracle is run.

## Predeclared checks and results

1. **Label sanity** — every grid cell has a unique Ulam label. Because this is
   a crop of an infinite spiral, the labels are not contiguous: this window
   contains `1..181` and `212..225` (maximum `225`). Pass.
2. **FEFE's Ulam number** — the established corner-spiral reading found
   FEFE's zero-based spiral index (163) is prime. Under this Ulam numbering,
   FEFE (grid row 8, column 5, one-based) gets number `20`, which is not
   prime. No echo of the established fact under this convention.
3. **Colored-cells-only sequence**, encountered in increasing-Ulam-number
   order:

   ```text
   YFBYBBYYBBYYBBBBYBBBYBYBB
   ```

   Dropping the `F`, this is `YBYBBYYBBYYBBBBYBBBYBYBB` — it matches neither
   the authenticated `BBBBYBBBYYBBBBYBBYYBYYBY` nor its reverse.
4. **Full 196-bit stream** in increasing-Ulam-number order: the first 192
   bits, framed the same way as the verified construction (8-bit ASCII
   chunks), are not printable ASCII. The full 196-bit integer is not prime.
5. **Prime-numbered cells only** (43 cells whose true Ulam labels are prime),
   bits taken in increasing order and read as one integer: not prime.

## Verdict

Under this one predeclared convention (center `(6,6)`, right-first,
counterclockwise), no check reproduces or echoes the established spiral
construction or its verified facts. This closes *this specific numbering*
as a negative result — it does not establish that no Ulam-style numbering of
this grid could ever produce something, and it does not rule in or out the
convention the original tweet actually depicts, which remains unseen.

Reopen if the tweet's image (or another source) is obtained and specifies a
different starting cell or turn direction, or if a new clue explicitly names
an Ulam/prime-spiral numbering as the intended reading.

## Reproduction

```bash
python3 tools/gsmg/first_piece_ulam_spiral_audit.py --self-test
python3 tools/gsmg/first_piece_ulam_spiral_audit.py
```
