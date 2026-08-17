#!/usr/bin/env python3
"""Visualization -- mark exactly which cells were counted in the last
"3 types" pixel tally (2026-08-16), on user request during the
"Divergence pass 2" follow-up conversation, to confirm mutual
understanding of scope before any further derived-count discussion.

Counted cells = the 6 textured ring rows (9, 10, 13, 37, 38, 41),
interior columns 7-40, kept fully intact (204 pixels total, in 4
contiguous row-blocks: [9,10], [13], [37,38], [41]). NOT counted = the 8
solid separator rows (7, 11, 35, 39 all-white; 8, 12, 36, 40 all-green),
the two edge boundary-AA columns (6, 41), and the rest of the finder
square (border, center square).

Renders the same 8-value categorical palette used throughout this
investigation, then overlays a solid blue tint on exactly the counted
204 cells so the boundary between counted/not-counted is unambiguous at a
glance -- no other pixel is modified.
"""

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
IMAGE_PATH = REPO_ROOT / "doc" / "img" / "gsmg_puzzle_stage1.png"
OUT_PATH = REPO_ROOT / "doc" / "img" / "gsmg_puzzle_stage1_qr_finder_counted_cells_highlighted.png"

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
FINDER_BOX = (2, 1289, 49, 1337)
INT0, INT1 = 7, 40  # interior columns

COUNTED_ROW_BLOCKS = [[9, 10], [13], [37, 38], [41]]  # matches Phase 304's 4 blocks
TINT = (30, 60, 255)
TINT_ALPHA = 0.55


def load_gray():
    im = Image.open(IMAGE_PATH).convert("RGB")
    arr = np.array(im)
    x0, y0, x1, y1 = FINDER_BOX
    region = arr[y0 : y1 + 1, x0 : x1 + 1]
    return region.mean(axis=2).astype(int)


def counted_rows():
    return [y for block in COUNTED_ROW_BLOCKS for y in block]


def render(gray):
    h, w = gray.shape
    out = np.zeros((h, w, 3), dtype=np.uint8)
    for yy in range(h):
        for xx in range(w):
            out[yy, xx] = PALETTE[int(gray[yy, xx])]
    img = Image.fromarray(out, "RGB").resize((w * SCALE, h * SCALE), Image.NEAREST)
    draw = ImageDraw.Draw(img, "RGBA")
    for block in COUNTED_ROW_BLOCKS:
        y_lo, y_hi = block[0], block[-1]
        x0 = INT0 * SCALE
        y0 = y_lo * SCALE
        x1 = (INT1 + 1) * SCALE - 1
        y1 = (y_hi + 1) * SCALE - 1
        draw.rectangle([x0, y0, x1, y1], fill=(*TINT, int(255 * TINT_ALPHA)))
        draw.rectangle([x0, y0, x1, y1], outline=(255, 255, 255), width=2)
    return img


def self_test():
    gray = load_gray()
    rows = counted_rows()
    assert rows == [9, 10, 13, 37, 38, 41], f"unexpected counted rows: {rows}"
    total_cells = sum((INT1 - INT0 + 1) for _ in rows)
    assert total_cells == 204, f"expected 204 counted cells, got {total_cells}"

    img = render(gray)
    assert OUT_PATH.exists(), f"missing saved reference render: {OUT_PATH}"
    saved = Image.open(OUT_PATH).convert("RGB")
    assert np.array_equal(np.array(saved), np.array(img)), "saved reference render must match a fresh render"
    print(f"[*] self-test OK: 204 counted cells across 4 row-blocks (rows {rows}), saved render matches")


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
        img = render(gray)
        img.save(OUT_PATH)
        print(f"[*] saved {OUT_PATH}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
