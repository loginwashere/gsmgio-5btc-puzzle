#!/usr/bin/env python3
"""Candidate family -- QR finder-ring texture: reindex/dither/JPEG-origin checks (2026-08-16).

Executes ideas 3, 6, and 7 from
doc/Brainstorms/2026-08-16 - QR Finder-Pattern Ring Texture Investigation.md
against the real pixel data in doc/img/gsmg_puzzle_stage1.png. This is image
forensics, not a passphrase-oracle test -- there is no AES blob attempt here,
only pixel-exact structural comparison, matching this project's usual
exact-match bar applied to a non-cryptographic artifact.

Idea 7 -- phase-drift reindexing. The three finder squares are located by
flood-filling pure-black (0,0,0) connected components and keeping the three
48x49-pixel, 1092-black-pixel bounding boxes (reproducing the prior session's
measurement independently). The top ring band (bbox-relative rows 7-13) and
bottom ring band (rows 35-41) are compared row-for-row at the same
band-relative offset, exact byte-for-byte, across the full 36-column ring
width.

Idea 3 -- 1D row-only ordered dither. A dither model whose threshold depends
only on row index y (uniform value across the row) can only ever emit a
single value per row. This is falsified directly from the extracted pixel
data: several ring rows contain two distinct non-black/white values at
different columns in the same row, which is impossible under a row-only
(x-independent) model. No synthetic rendering is needed to reach this verdict
-- it is a direct proof from the measured data, cheaper than the originally
planned generate-and-diff experiment.

Idea 6 -- JPEG block-origin sweep. Sweeping the assumed 8x8 block-grid origin
over the gray (non-pure-black/white) pixel population only cyclically
relabels the mod-8 residue histogram; it cannot reveal a periodicity spike
that is not already present at origin=0. This is confirmed directly on the
real gray-pixel population within the QR region: the histogram's max-min
spread is bit-for-bit identical across all 8 possible origins. The
already-existing "roughly uniform, no spike" result at origin=0 therefore
forecloses the entire 64-combination sweep without needing to run it as a
literal search.
"""

import argparse
import json
import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
IMAGE_PATH = REPO_ROOT / "doc" / "img" / "gsmg_puzzle_stage1.png"

TOP_ROWS = list(range(7, 14))
BOT_ROWS = list(range(35, 42))
COL0, COL1 = 6, 41  # ring-only columns, excludes the 6px outer black border
QR_REGION_BOX = (0, 1287, 235, 1524)  # x0, y0, x1, y1 (exclusive), whole QR incl. quiet zone


def _flood(x0, y0, mask, visited):
    H, W = mask.shape
    q = deque([(x0, y0)])
    visited[y0, x0] = True
    minx = maxx = x0
    miny = maxy = y0
    size = 0
    while q:
        cx, cy = q.popleft()
        size += 1
        minx, maxx = min(minx, cx), max(maxx, cx)
        miny, maxy = min(miny, cy), max(maxy, cy)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < W and 0 <= ny < H and mask[ny, nx] and not visited[ny, nx]:
                visited[ny, nx] = True
                q.append((nx, ny))
    return size, (minx, miny, maxx, maxy)


def locate_finder_squares(arr):
    """Independently relocate the three 48x49px / 1092-black-pixel finder squares."""
    H, W, _ = arr.shape
    is_black = np.all(arr == 0, axis=2)
    visited = np.zeros((H, W), dtype=bool)
    found = []
    y_lo, y_hi = 1200, min(1600, H)
    x_lo, x_hi = 0, min(300, W)
    for y in range(y_lo, y_hi):
        for x in range(x_lo, x_hi):
            if is_black[y, x] and not visited[y, x]:
                size, bbox = _flood(x, y, is_black, visited)
                if size == 1092 and (bbox[2] - bbox[0] + 1, bbox[3] - bbox[1] + 1) == (48, 49):
                    found.append(bbox)
    return found


def load_image():
    im = Image.open(IMAGE_PATH).convert("RGB")
    return np.array(im)


def idea7_reindex(arr, bbox):
    x0, y0, x1, y1 = bbox
    r = arr[y0 : y1 + 1, x0 : x1 + 1]
    gray = r.mean(axis=2).astype(int)
    top = [gray[y, COL0 : COL1 + 1].tolist() for y in TOP_ROWS]
    bot = [gray[y, COL0 : COL1 + 1].tolist() for y in BOT_ROWS]

    rows = []
    for i in range(len(TOP_ROWS)):
        t, b = top[i], bot[i]
        exact = t == b
        same_positions = [v == 250 for v in t] == [v == 250 for v in b]
        rows.append(
            {
                "top_row": TOP_ROWS[i],
                "bot_row": BOT_ROWS[i],
                "exact_match": exact,
                "same_texture_positions_diff_level": (not exact) and same_positions,
            }
        )
    return rows


def idea3_row_only_dither_falsification(arr, bbox):
    x0, y0, x1, y1 = bbox
    r = arr[y0 : y1 + 1, x0 : x1 + 1]
    gray = r.mean(axis=2).astype(int)
    multi_valued_rows = []
    for y in list(range(7, 14)) + list(range(35, 42)):
        row = gray[y, COL0 : COL1 + 1]
        distinct = sorted(set(int(v) for v in row if int(v) not in (0,)))
        if len(distinct) > 1:
            multi_valued_rows.append({"row": y, "distinct_nonblack_values": distinct})
    return multi_valued_rows


def idea6_jpeg_origin_invariance(arr):
    x0, y0, x1, y1 = QR_REGION_BOX
    region = arr[y0:y1, x0:x1]
    gray = region.mean(axis=2)
    is_gray_pixel = (gray != 0) & (gray != 255)
    ys, xs = np.where(is_gray_pixel)
    spreads = []
    for o in range(8):
        hx = np.bincount((xs - o) % 8, minlength=8)
        hy = np.bincount((ys - o) % 8, minlength=8)
        spreads.append(
            {"origin": o, "x_max_minus_min": int(hx.max() - hx.min()), "y_max_minus_min": int(hy.max() - hy.min())}
        )
    all_x_equal = len({s["x_max_minus_min"] for s in spreads}) == 1
    all_y_equal = len({s["y_max_minus_min"] for s in spreads}) == 1
    return {"gray_pixel_count": int(len(xs)), "spreads": spreads, "origin_invariant": all_x_equal and all_y_equal}


def self_test():
    arr = load_image()
    boxes = locate_finder_squares(arr)
    assert len(boxes) == 3, f"expected 3 finder squares, found {len(boxes)}: {boxes}"
    r0 = arr[boxes[0][1] : boxes[0][3] + 1, boxes[0][0] : boxes[0][2] + 1]
    for b in boxes[1:]:
        r = arr[b[1] : b[3] + 1, b[0] : b[2] + 1]
        assert np.array_equal(r0, r), "finder squares expected to be byte-identical (prior session's own finding)"

    rows7 = idea7_reindex(arr, boxes[0])
    exact_count = sum(1 for row in rows7 if row["exact_match"])
    assert exact_count == 5, f"expected 5/7 exact-match rows at same band offset, got {exact_count}"

    mv = idea3_row_only_dither_falsification(arr, boxes[0])
    assert len(mv) >= 1, "expected at least one intra-row multi-valued ring row (falsifies row-only dither)"

    j = idea6_jpeg_origin_invariance(arr)
    assert j["origin_invariant"], "origin sweep must be a pure relabeling of the same histogram"

    print("[*] self-test OK: 3 finder squares relocated, 5/7 rows exact at same offset, "
          f"{len(mv)} multi-valued ring rows found, JPEG-origin spread invariant across all 8 origins")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return

    if not args.run:
        parser.print_help()
        return

    arr = load_image()
    boxes = locate_finder_squares(arr)
    report = {
        "finder_square_bboxes": boxes,
        "idea7_reindex_top_vs_bottom_same_offset": idea7_reindex(arr, boxes[0]),
        "idea3_multi_valued_ring_rows": idea3_row_only_dither_falsification(arr, boxes[0]),
        "idea6_jpeg_origin_sweep": idea6_jpeg_origin_invariance(arr),
    }

    if args.json:
        print(json.dumps(report, indent=2))
        return

    print(f"Finder squares: {boxes}")
    print()
    print("Idea 7 -- same-band-offset row comparison (top rows 7-13 vs bottom rows 35-41):")
    for row in report["idea7_reindex_top_vs_bottom_same_offset"]:
        tag = "EXACT" if row["exact_match"] else (
            "SAME POSITIONS, DIFF LEVEL" if row["same_texture_positions_diff_level"] else "DIVERGENT"
        )
        print(f"  top row {row['top_row']:2d} vs bot row {row['bot_row']:2d}: {tag}")
    exact_n = sum(1 for r in report["idea7_reindex_top_vs_bottom_same_offset"] if r["exact_match"])
    print(f"  -> {exact_n}/7 rows byte-for-byte identical at the same band-relative offset")
    print()
    print("Idea 3 -- ring rows with more than one distinct non-black value (falsifies row-only dither):")
    for row in report["idea3_multi_valued_ring_rows"]:
        print(f"  row {row['row']:2d}: {row['distinct_nonblack_values']}")
    print()
    j = report["idea6_jpeg_origin_sweep"]
    print(f"Idea 6 -- JPEG origin sweep over {j['gray_pixel_count']} gray pixels in the QR region:")
    print(f"  origin-invariant (all 8 origins give identical histogram spread): {j['origin_invariant']}")


if __name__ == "__main__":
    main()
