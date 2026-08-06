#!/usr/bin/env python3
"""Stage-0 grid (follow_the_white_rabbit.png) spiral decode + blue/yellow characterization.

Verified 2026-07-13: the counterclockwise spiral from the top-left corner (README's
documented reading order) reproduces "gsmg.io/theseedisplanted" exactly when black/blue
cells count as bit=1 and white/yellow/FEFE cells count as bit=0. Under that reading, the
24 blue/yellow-colored cells fall exactly on spiral positions i % 8 == 7 -- i.e. the LSB
of each of the 24 decoded ASCII characters -- and the color (blue vs yellow) exactly
equals that bit's value (odd/even ASCII). This is a complete, tautological explanation
for the blue/yellow cell selection: fully redundant with the black/white channel, zero
extra information. It also reproduces the previously-known partial characterization
((row - col) % 4 == 3) as a geometric byproduct of the spiral shape, not an independent
rule.
"""
import argparse
from pathlib import Path

import numpy as np
from PIL import Image

DEFAULT_IMG_PATH = (
    Path.home()
    / "projects"
    / "gsmg-site-mirror"
    / "img"
    / "follow_the_white_rabbit.png"
)

BLACK, WHITE, BLUE, YELLOW, FEFE = (0, 0, 0), (255, 255, 255), (63, 72, 204), (255, 242, 0), (254, 254, 254)
COLOR_NAME = {BLACK: "K", WHITE: "W", BLUE: "B", YELLOW: "Y", FEFE: "F"}
N = 14
TARGET = "gsmg.io/theseedisplanted"


def load_grid(path=DEFAULT_IMG_PATH):
    """Majority pixel color per cell (see first_piece_color_reconstruction.load_grid
    docstring: single center-pixel sampling misclassifies the one cell where the
    overlaid rabbit line-art crosses the sample point)."""
    im = Image.open(path).convert("RGB")
    cell = im.size[0] // N
    pixels = np.asarray(im.convert("RGB"))
    grid = []
    for r in range(N):
        row = []
        for c in range(N):
            block = pixels[r * cell : (r + 1) * cell, c * cell : (c + 1) * cell]
            colors, counts = np.unique(block.reshape(-1, 3), axis=0, return_counts=True)
            row.append(tuple(int(value) for value in colors[np.argmax(counts)]))
        grid.append(row)
    return grid


def bitval(px):
    return 1 if px in (BLACK, BLUE) else 0


def spiral_tl_ccw(n=N):
    """Top-left start, counter-clockwise, matching the community README's reading order."""
    visited = [[False] * n for _ in range(n)]
    r, c, dr, dc = 0, 0, 0, -1  # 'left' from (0,0) degenerates to 'down' on first turn
    coords = []
    for _ in range(n * n):
        coords.append((r, c))
        visited[r][c] = True
        nr, nc = r + dr, c + dc
        if not (0 <= nr < n and 0 <= nc < n) or visited[nr][nc]:
            dr, dc = -dc, dr  # turn left (CCW)
            nr, nc = r + dr, c + dc
            if not (0 <= nr < n and 0 <= nc < n) or visited[nr][nc]:
                break
        r, c = nr, nc
    return coords


def decode(path=DEFAULT_IMG_PATH):
    grid = load_grid(path)
    coords = spiral_tl_ccw()
    bits = "".join(str(bitval(grid[r][c])) for r, c in coords)
    chars = "".join(chr(int(bits[i : i + 8], 2)) for i in range(0, 192, 8))
    assert chars == TARGET, f"decode mismatch: {chars!r} != {TARGET!r}"
    return grid, coords, bits, chars


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--image",
        type=Path,
        default=DEFAULT_IMG_PATH,
        help=f"path to follow_the_white_rabbit.png (default: {DEFAULT_IMG_PATH})",
    )
    args = parser.parse_args()
    grid, coords, bits, chars = decode(args.image)
    print("decoded:", chars)

    boundary_positions = [i for i in range(196) if i % 8 == 7][:24]
    print(f"\n{len(boundary_positions)} blue/yellow boundary cells (spiral pos i%8==7):")
    all_match = True
    for idx, i in enumerate(boundary_positions):
        r, c = coords[i]
        px = grid[r][c]
        ch = TARGET[idx]
        expect = "B" if ord(ch) % 2 else "Y"
        actual = COLOR_NAME[px]
        ok = actual == expect
        all_match &= ok
        diag = (r - c) % 4
        print(
            f"  char={ch!r} ord={ord(ch):3d} spiralpos={i:3d} rc=({r:2d},{c:2d}) "
            f"(r-c)%4={diag} color={actual} expected={expect} {'OK' if ok else 'MISMATCH'}"
        )
    print(f"\nall 24 positions match parity prediction: {all_match}")
