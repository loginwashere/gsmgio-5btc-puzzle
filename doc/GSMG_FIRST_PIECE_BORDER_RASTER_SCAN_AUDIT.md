# GSMG First-Piece Border/Raster Scan Audit

**Date:** 2026-08-09
**Status:** Closed negative. No side-based reading rivals the spiral construction.

## Question

Does reading the authenticated 14x14 grid from each of its four sides —
rather than the established counterclockwise spiral — produce anything
comparably tight? Three bounded readings were tested, from the most literal
to the most exhaustive.

`tools/gsmg/first_piece_border_raster_scan_audit.py` implements all three
directly against the same majority-vote grid classifier the verified spiral
reconstruction uses. No word list, cipher, or blob oracle is run.

## 1. Border-only reading

The literal outer row/column facing each side, without scanning inward:

```text
top:    WWKKWBWWKWKKWY   (blue=1, yellow=1)
bottom: WKBWKKWKKWBWKK   (blue=2, yellow=0)
left:   WKKWWKKBWKKKWW   (blue=1, yellow=0)
right:  YKKKWKWWBKKWWK   (blue=1, yellow=1)
```

Each edge carries only 1-2 colored cells; the top-right corner cell is
shared between the `top` and `right` readings, not two independent hits.
The 24 informative colored cells are concentrated in the grid's interior,
not its border, so this reading carries almost no signal.

## 2. Nearest-inward reading

For each row/column, the first blue/yellow/FEFE cell encountered scanning
in from that side:

```text
from_left:   blue=12  yellow=2  fefe=0
from_right:  blue=6   yellow=8  fefe=0
from_top:    blue=9   yellow=5  fefe=0
from_bottom: blue=8   yellow=5  fefe=1
```

The only point of note: FEFE (grid position row 8, column 5, one-based) is
the nearest colored cell to the bottom edge in its column — no other
colored cell lies below it there. This is a single positional fact about
one column among fourteen; it is not treated as a discovery-grade rarity.

## 3. Full-raster reading

The whole grid read as a straight top-to-bottom or left-to-right raster
(and their reverses), keeping only colored cells in encounter order — the
same "keep only colored cells" rule the verified spiral reading uses, with
a raster path substituted for the spiral path. Values below drop the FEFE
marker and read blue=1/yellow=0 across the remaining 24 bits, exactly as
the authenticated construction does:

```text
top_to_bottom: BYBBBBBYYYBYBFYBBBYYBBYBB -> 0xBE2B9B  (not prime)
bottom_to_top: BBBYBYBYBBBFYBYYYBYBBBBBY -> 0xEAE8BE  (not prime)
left_to_right: BBBBBBBBFBBYYBYBYYBYBYYYB -> 0xFFCA51  (16763473, prime)
right_to_left: YBYYBYBYYBBYYYBBBFBBBBBBB -> 0x4A63FF  (not prime)
```

None of the four raster strings is a rotation or reflection of the
authenticated spiral answer `BBBBYBBBYYBBBBYBBYYBYYBY`; each is a genuinely
different permutation of the same 15-blue/9-yellow/1-FEFE multiset.

## Calibration of the one prime hit

`left_to_right` lands on a prime, `0xFFCA51 = 16763473`. With four
directions tried and a roughly 1-in-16-to-1-in-17 base rate for a random
24-bit value to be prime, one hit in four attempts is unremarkable
(descriptive, not a discovery p-value — `posthoc_valid_p_value: False` in
the audit output). This is unlike the authenticated `574061`, which is
independently anchored by the `yellowblueprime` clue text rather than
selected after the fact from a small family of candidate orderings.

## Verdict

Close all three readings. Retain only as negative controls:

1. the border is signal-poor — the puzzle's colored cells are interior, not
   edge-concentrated;
2. FEFE's nearest-from-bottom position in its own column is a real but
   single, unremarkable fact;
3. no raster direction reproduces or resembles the spiral answer, and the
   one prime hit among four raster directions has no independent selector.

Reopen only if another clue explicitly names a side-based or raster
traversal of this grid.

## Reproduction

```bash
python3 tools/gsmg/first_piece_border_raster_scan_audit.py --self-test
```
