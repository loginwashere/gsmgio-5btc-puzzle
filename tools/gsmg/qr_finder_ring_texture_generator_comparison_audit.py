#!/usr/bin/env python3
"""Candidate family -- QR finder-ring texture: real free-generator comparison (2026-08-16).

Executes ideas 1/2 (the last open item) from
doc/Brainstorms/2026-08-16 - QR Finder-Pattern Ring Texture Investigation.md:
generate the puzzle's own payload through real free QR-generator services and
check whether any reproduces the eyes-only gray antialiasing texture found in
`doc/img/gsmg_puzzle_stage1.png`.

Three real services were queried live with the puzzle's exact payload
(`https://www.blockchain.com/btc/address/1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe`)
on 2026-08-16 and their output PNGs saved locally so this script is
reproducible without a network dependency at analysis time:

  - `doc/img/qr_generator_comparison_qrserver_goqrme.png`
    (api.qrserver.com / goqr.me, GET API, size=250x250)
  - `doc/img/qr_generator_comparison_quickchart_io.png`
    (quickchart.io/qr, GET API, size=250)
  - `doc/img/qr_generator_comparison_qrcode_monkey_default.png`
    (api.qrcode-monkey.com/qr/custom, POST API, default style, size=300)

For each, this script locates the finder-square black-border connected
components (same flood-fill method as
`qr_finder_ring_texture_reindex_dither_audit.py`) and reports (a) whether
any non-pure-black/white pixels exist at all, and (b) if so, whether they
are confined to the three finder-square regions only (matching fact (a) of
the puzzle's own framing question) or scattered through the data body too.
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
IMG_DIR = REPO_ROOT / "doc" / "img"

GENERATORS = {
    "qrserver_goqrme": IMG_DIR / "qr_generator_comparison_qrserver_goqrme.png",
    "quickchart_io": IMG_DIR / "qr_generator_comparison_quickchart_io.png",
    "qrcode_monkey_default": IMG_DIR / "qr_generator_comparison_qrcode_monkey_default.png",
}


def _flood(x0, y0, mask, visited):
    H, W = mask.shape
    q = deque([(x0, y0)])
    visited[y0, x0] = True
    pix = [(x0, y0)]
    minx = maxx = x0
    miny = maxy = y0
    while q:
        cx, cy = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < W and 0 <= ny < H and mask[ny, nx] and not visited[ny, nx]:
                visited[ny, nx] = True
                pix.append((nx, ny))
                q.append((nx, ny))
                minx, maxx = min(minx, nx), max(maxx, nx)
                miny, maxy = min(miny, ny), max(maxy, ny)
    return len(pix), (minx, miny, maxx, maxy)


def find_finder_like_components(arr, min_size=500):
    """Locate large near-square pure-black connected components (candidate finder borders)."""
    H, W, _ = arr.shape
    is_black = np.all(arr < 20, axis=2)
    visited = np.zeros((H, W), dtype=bool)
    comps = []
    for y in range(H):
        for x in range(W):
            if is_black[y, x] and not visited[y, x]:
                size, bbox = _flood(x, y, is_black, visited)
                w, h = bbox[2] - bbox[0] + 1, bbox[3] - bbox[1] + 1
                if size >= min_size and 0.85 <= w / h <= 1.15:
                    comps.append({"size": size, "bbox": bbox})
    comps.sort(key=lambda c: -c["size"])
    return comps


def analyze_generator(path):
    im = Image.open(path).convert("RGB")
    arr = np.array(im)
    H, W, _ = arr.shape
    gray = arr.mean(axis=2)
    is_gray_pixel = (gray != 0) & (gray != 255)
    ys, xs = np.where(is_gray_pixel)

    finder_boxes = find_finder_like_components(arr)[:3]
    in_finder = np.zeros(len(xs), dtype=bool)
    for box in finder_boxes:
        bx0, by0, bx1, by1 = box["bbox"]
        pad = 3
        in_finder |= (
            (xs >= bx0 - pad) & (xs <= bx1 + pad) & (ys >= by0 - pad) & (ys <= by1 + pad)
        )

    return {
        "image_size": [W, H],
        "gray_pixel_count": int(len(xs)),
        "finder_boxes_found": len(finder_boxes),
        "gray_pixels_confined_to_finder_regions": bool(len(xs) == 0 or in_finder.all()),
        "gray_pixels_outside_finder_regions": int((~in_finder).sum()) if len(xs) else 0,
    }


def run():
    report = {}
    for name, path in GENERATORS.items():
        if not path.exists():
            report[name] = {"error": f"missing local file {path}"}
            continue
        report[name] = analyze_generator(path)
    return report


def self_test():
    for name, path in GENERATORS.items():
        assert path.exists(), f"missing saved comparison image for {name}: {path}"
    report = run()
    assert report["qrserver_goqrme"]["gray_pixel_count"] == 0
    assert report["quickchart_io"]["gray_pixel_count"] == 0
    assert report["qrcode_monkey_default"]["gray_pixel_count"] > 0
    assert report["qrcode_monkey_default"]["gray_pixels_confined_to_finder_regions"] is True
    print("[*] self-test OK: 3 saved generator images present; qrserver/quickchart pure "
          "black-white, qrcode-monkey has eyes-confined gray pixels")


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

    report = run()
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        for name, stats in report.items():
            print(f"{name}: {stats}")


if __name__ == "__main__":
    main()
