#!/usr/bin/env python3
"""Visualization -- continue the ring texture's known Y-periodic tile through the
inner black center square (2026-08-16), on user request during the
"Divergence pass 2" follow-up conversation in
doc/Brainstorms/2026-08-16 - QR Finder-Pattern Ring Texture Investigation.md.

This is explicitly a HYPOTHETICAL EXTRAPOLATION, not a claim about the real
image: the real `gsmg_puzzle_stage1.png` has a solid pure-black `(0,0,0)`
21x21px center square at bbox-relative rows 14-34, cols 13-33 (confirmed by
direct pixel dump -- Phase reference: same finder-square bbox used
throughout this investigation). This script asks "what would it look like
if the already-established ring tile just kept going instead of stopping at
the center square," purely as a visual aid -- it does not modify, and is not
evidence about, the real artifact.

Extrapolation rule (mechanical, fully disclosed, no new free parameters):
Phase 296/297 established the top ring band (rows 7-13) is a 7-row
repeating tile (band-relative offsets 0-6) with known, mostly-shared content
per offset:
  offset 0 (row 7):  solid white (255)
  offset 1 (row 8):  solid green (250)
  offset 2 (row 9):  irregular tick pattern -- the one row Phase 296 found
                      genuinely divergent between top/bottom bands; there is
                      no single canonical version, so this script discloses
                      its choice: the top band's (row 9) instance, not an
                      average or a new invention.
  offset 3 (row 10): regular tick pattern, byte-identical between top/bottom
  offset 4 (row 11): solid white (255)
  offset 5 (row 12): solid green (250)
  offset 6 (row 13): regular tick pattern, same positions as offset 3; the
                      top band's (row 13) 255-background version is used
                      rather than the bottom band's row 41, since row 41 was
                      itself flagged as the one background-level anomaly --
                      propagating the outlier would misrepresent "the known
                      pattern" the user asked to continue.

21 rows (14-34) = exactly 3 full repeats of this 7-row tile (21/7=3, no
remainder -- a clean fit, not a truncated cycle). For each of those 3
repeats, this script copies the REAL, already-measured pixel values from
the top band's rows 7-13 at columns 13-33 (the exact center-square column
span) directly into the corresponding center-square row -- i.e. it reuses
real observed data rather than synthesizing new values, since columns
13-33 are already part of the top band's normal (non-black) ring texture
one row up.

Everything outside the center square (rows 14-34, cols 13-33) is left
completely untouched -- the real left/right ring-band texture already
visible in that row range, and the whole rest of the image, is unchanged.
The filled region is outlined in magenta in the render so the hypothetical
portion is never mistaken for real pixel data.
"""

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
IMAGE_PATH = REPO_ROOT / "doc" / "img" / "gsmg_puzzle_stage1.png"
OUT_PATH = REPO_ROOT / "doc" / "img" / "gsmg_puzzle_stage1_qr_finder_center_square_pattern_continuation.png"

PALETTE = {
    0: (0, 0, 0),
    15: (127, 0, 0),
    16: (255, 0, 0),
    234: (255, 128, 0),
    236: (255, 255, 0),
    250: (0, 200, 0),
    252: (0, 255, 255),
    255: (255, 255, 255),
}
SCALE = 14

FINDER_BOX = (2, 1289, 49, 1337)  # top_left, same instance used throughout this investigation
TEMPLATE_ROWS = range(7, 14)  # top band, the 7-row source tile
CENTER_ROW_LO, CENTER_ROW_HI = 14, 34  # inclusive, the real solid-black center square
CENTER_COL_LO, CENTER_COL_HI = 13, 33  # inclusive


def load_gray():
    im = Image.open(IMAGE_PATH).convert("RGB")
    arr = np.array(im)
    x0, y0, x1, y1 = FINDER_BOX
    region = arr[y0 : y1 + 1, x0 : x1 + 1]
    return region.mean(axis=2).astype(int)


def build_continued_grid(gray):
    """Copy of the real grid with the center square filled by tiling the
    top band's real row-7..13 / col-13..33 slice 3x vertically."""
    grid = gray.copy()
    template = gray[list(TEMPLATE_ROWS), CENTER_COL_LO : CENTER_COL_HI + 1]  # 7x21
    n_center_rows = CENTER_ROW_HI - CENTER_ROW_LO + 1
    assert n_center_rows % len(template) == 0, "center square height must be an exact multiple of the 7-row tile"
    n_repeats = n_center_rows // len(template)
    for rep in range(n_repeats):
        for i in range(len(template)):
            y = CENTER_ROW_LO + rep * len(template) + i
            grid[y, CENTER_COL_LO : CENTER_COL_HI + 1] = template[i]
    return grid, n_repeats


def render(grid):
    h, w = grid.shape
    out = np.zeros((h, w, 3), dtype=np.uint8)
    for yy in range(h):
        for xx in range(w):
            out[yy, xx] = PALETTE[int(grid[yy, xx])]
    img = Image.fromarray(out, "RGB").resize((w * SCALE, h * SCALE), Image.NEAREST)
    draw = ImageDraw.Draw(img)
    x0 = CENTER_COL_LO * SCALE
    y0 = CENTER_ROW_LO * SCALE
    x1 = (CENTER_COL_HI + 1) * SCALE - 1
    y1 = (CENTER_ROW_HI + 1) * SCALE - 1
    draw.rectangle([x0, y0, x1, y1], outline=(255, 0, 255), width=3)
    return img


def self_test():
    gray = load_gray()
    real_center = gray[CENTER_ROW_LO : CENTER_ROW_HI + 1, CENTER_COL_LO : CENTER_COL_HI + 1]
    assert (real_center == 0).all(), "expected the real center square to be pure black before extrapolation"

    grid, n_repeats = build_continued_grid(gray)
    assert n_repeats == 3, f"expected exactly 3 tile repeats, got {n_repeats}"

    outside_mask = np.ones_like(gray, dtype=bool)
    outside_mask[CENTER_ROW_LO : CENTER_ROW_HI + 1, CENTER_COL_LO : CENTER_COL_HI + 1] = False
    assert np.array_equal(grid[outside_mask], gray[outside_mask]), "must not alter any pixel outside the center square"

    filled = grid[CENTER_ROW_LO : CENTER_ROW_HI + 1, CENTER_COL_LO : CENTER_COL_HI + 1]
    template = gray[list(TEMPLATE_ROWS), CENTER_COL_LO : CENTER_COL_HI + 1]
    for rep in range(3):
        chunk = filled[rep * 7 : (rep + 1) * 7]
        assert np.array_equal(chunk, template), f"repeat {rep} must exactly match the real top-band template"
    assert set(np.unique(filled)) <= set(PALETTE), "filled region must only use already-observed palette values"

    img = render(grid)
    assert OUT_PATH.exists(), f"missing saved reference render: {OUT_PATH}"
    saved = Image.open(OUT_PATH).convert("RGB")
    assert np.array_equal(np.array(saved), np.array(img)), "saved reference render must match a fresh render"

    print(f"[*] self-test OK: real center square was pure black, 3x 7-row tile repeats fill it exactly, "
          f"0 pixels altered outside the center square, saved render matches")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--render", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return

    if args.render:
        gray = load_gray()
        grid, n_repeats = build_continued_grid(gray)
        img = render(grid)
        img.save(OUT_PATH)
        print(f"[*] saved {OUT_PATH} ({n_repeats} tile repeats)")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
