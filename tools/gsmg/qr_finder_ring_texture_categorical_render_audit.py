#!/usr/bin/env python3
"""Candidate family -- QR finder-ring texture: one-shot categorical-palette render (2026-08-16).

Executes idea 4 from the "Divergence pass 2" section of
doc/Brainstorms/2026-08-16 - QR Finder-Pattern Ring Texture Investigation.md:
render each finder square's exact pixel data as a high-contrast image and
look once for a recognizable glyph, on the same "hidden picture inside a
QR-adjacent graphic" theory the puzzle's own genesis image already used
(the embedded real QR code) -- but treating this ring patch as a 2D picture
to inspect, not a mechanism to explain.

Per that document's explicit discipline, this MUST be a one-shot check with
parameters fixed before inspecting output, not an iterative "try palettes
until something looks like a shape" search (the exact pareidolia risk
flagged going in). The palette below is fixed in advance from the 8 exact
grayscale values already measured and documented in this project's own
"Known facts" (0, 15, 16, 234, 236, 250, 252, 255), mapped to 8 maximally
distinguishable categorical colors in ascending value order. Any pixel
value outside that pre-declared set renders magenta so an incomplete
palette would be visible rather than silently mis-rendered. Nearest-
neighbor upscaling only -- no interpolation, so no new visual information
is invented.

Applied identically to all three finder squares (already established
byte-identical elsewhere in this investigation) for confirmation, not
because a different result was expected.
"""

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
IMAGE_PATH = REPO_ROOT / "doc" / "img" / "gsmg_puzzle_stage1.png"
SAVED_RENDER = REPO_ROOT / "doc" / "img" / "gsmg_puzzle_stage1_qr_finder_categorical_palette_render.png"

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
UNMAPPED_COLOR = (255, 0, 255)
SCALE = 14

FINDER_BOXES = {
    "top_left": (2, 1289, 49, 1337),
    "top_right": (184, 1289, 231, 1337),
    "bottom_left": (2, 1471, 49, 1519),
}


def render(arr, bbox):
    x0, y0, x1, y1 = bbox
    region = arr[y0 : y1 + 1, x0 : x1 + 1]
    gray = region.mean(axis=2).astype(int)
    h, w = gray.shape
    out = np.zeros((h, w, 3), dtype=np.uint8)
    unmapped = set()
    for yy in range(h):
        for xx in range(w):
            v = int(gray[yy, xx])
            if v in PALETTE:
                out[yy, xx] = PALETTE[v]
            else:
                unmapped.add(v)
                out[yy, xx] = UNMAPPED_COLOR
    big = Image.fromarray(out, "RGB").resize((w * SCALE, h * SCALE), Image.NEAREST)
    return big, unmapped


def load_image():
    im = Image.open(IMAGE_PATH).convert("RGB")
    return np.array(im)


def self_test():
    arr = load_image()
    all_unmapped = set()
    renders = {}
    for name, bbox in FINDER_BOXES.items():
        img, unmapped = render(arr, bbox)
        renders[name] = img
        all_unmapped |= unmapped
    assert not all_unmapped, f"unexpected grayscale values outside the pre-declared palette: {sorted(all_unmapped)}"

    ref = np.array(renders["top_left"])
    for name in ("top_right", "bottom_left"):
        assert np.array_equal(ref, np.array(renders[name])), f"{name} render must match top_left (already-established byte identity)"

    assert SAVED_RENDER.exists(), f"missing saved reference render: {SAVED_RENDER}"
    saved = np.array(Image.open(SAVED_RENDER).convert("RGB"))
    assert np.array_equal(saved, ref), "saved reference render must match a fresh render of top_left"

    print(f"[*] self-test OK: all 8 palette values covered, 0 unmapped, "
          f"all 3 finder squares render identically, matches saved reference")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    parser.print_help()


if __name__ == "__main__":
    main()
