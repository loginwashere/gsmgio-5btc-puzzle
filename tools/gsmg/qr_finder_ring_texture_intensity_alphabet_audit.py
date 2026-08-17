#!/usr/bin/env python3
"""Candidate family -- QR finder-ring texture: full intensity-alphabet sequence (2026-08-16).

Executes idea 3 from the "Divergence pass 2" section of
doc/Brainstorms/2026-08-16 - QR Finder-Pattern Ring Texture Investigation.md:
read the ring texture's exact intensity values off as a symbol sequence,
instead of the collapsed black/white/gray bucketing every mechanism-focused
idea in this doc used.

Region (pre-declared, reusing the exact geometry already codified in
`qr_finder_ring_texture_reindex_dither_audit.py`, not a new judgment call):
the top ring band (bbox-relative rows 7-13) and bottom ring band (rows
35-41), both columns 6-41, of the first located 48x49px/1092-black-pixel
finder square (all three are already established byte-identical, so which
instance is used cannot matter). Left/right bands are explicitly OUT OF
SCOPE for this experiment: their exact pixel geometry was only ever
established via ad hoc analysis in this session's prose, not preserved in
a reproducible script, so including them here would require a fresh,
untested geometric judgment call this idea's own discipline (pre-declare
before looking) rules out.

Measured directly: these two bands together contain exactly 7 distinct
grayscale values (15, 16, 234, 236, 250, 252, 255 -- no pure black or pure
white 0-of-8 gap from the doc's broader 8-value "Known facts" list, since
0 does not occur inside this specific sub-region). Mapped to base-7 digits
0-6 in ascending intensity order -- the same ascending-order convention
already used by `qr_finder_ring_texture_categorical_render_audit.py`'s
PALETTE, reused rather than re-invented.

Six candidate strings, pre-declared and fixed before any oracle run (closed
set, not tuned after a negative result):
  1. top band,    row-major left-to-right top-to-bottom (standard reading order)
  2. top band,    reversed
  3. bottom band, row-major (same order)
  4. bottom band, reversed
  5. top+bottom concatenated, in that order
  6. bottom+top concatenated, in that order

Each candidate string is run through `keystr_forms()` (raw / SHA-256 /
double-SHA-256, this project's standard hash-of-a-computed-artifact
convention) against all four tracked blobs via the standard CBC oracle:
6 candidates x 3 keystr forms = 18 passphrase attempts.
"""

import argparse
import json
import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
REPO_ROOT = SCRIPT_DIR.parent.parent
IMAGE_PATH = REPO_ROOT / "doc" / "img" / "gsmg_puzzle_stage1.png"

from cb_common import BLOBS, aes_try_open_bytes, keystr_forms  # noqa: E402

TOP_ROWS = list(range(7, 14))
BOT_ROWS = list(range(35, 42))
COL0, COL1 = 6, 41

# Ascending-order alphabet, matching PALETTE's key order in
# qr_finder_ring_texture_categorical_render_audit.py.
SYMBOL_MAP = {15: "0", 16: "1", 234: "2", 236: "3", 250: "4", 252: "5", 255: "6"}


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


def band_digits(gray, rows):
    out = []
    for y in rows:
        for x in range(COL0, COL1 + 1):
            v = int(gray[y, x])
            out.append(SYMBOL_MAP[v])
    return "".join(out)


def all_candidate_strings(gray):
    top = band_digits(gray, TOP_ROWS)
    bot = band_digits(gray, BOT_ROWS)
    return {
        "top_forward": top,
        "top_reversed": top[::-1],
        "bottom_forward": bot,
        "bottom_reversed": bot[::-1],
        "top_then_bottom": top + bot,
        "bottom_then_top": bot + top,
    }


def run():
    arr = load_image()
    boxes = locate_finder_squares(arr)
    x0, y0, x1, y1 = boxes[0]
    r = arr[y0 : y1 + 1, x0 : x1 + 1]
    gray = r.mean(axis=2).astype(int)

    candidates = all_candidate_strings(gray)
    attempts = []
    hits = []
    for label, form in candidates.items():
        for keystr in keystr_forms(form):
            result = aes_try_open_bytes(keystr.encode())
            attempts.append({"label": label, "keystr": keystr})
            if result:
                tag, body, kdf_label, key_len = result
                hits.append({
                    "label": label,
                    "form": form,
                    "keystr": keystr,
                    "blob": tag,
                    "kdf": f"{kdf_label}/aes{key_len * 8}",
                    "plaintext_hex": body.hex(),
                })
    return {
        "finder_square_bbox": boxes[0],
        "candidate_labels": list(candidates.keys()),
        "candidate_lengths": {k: len(v) for k, v in candidates.items()},
        "passphrase_attempts": len(attempts),
        "blobs": tuple(BLOBS),
        "hits": hits,
        "total_hits": len(hits),
    }


def self_test():
    arr = load_image()
    boxes = locate_finder_squares(arr)
    assert len(boxes) == 3, f"expected 3 finder squares, found {len(boxes)}"
    r0 = arr[boxes[0][1] : boxes[0][3] + 1, boxes[0][0] : boxes[0][2] + 1]
    for b in boxes[1:]:
        r = arr[b[1] : b[3] + 1, b[0] : b[2] + 1]
        assert np.array_equal(r0, r), "finder squares expected to be byte-identical"

    gray = r0.mean(axis=2).astype(int)
    seen = set()
    for y in TOP_ROWS + BOT_ROWS:
        for x in range(COL0, COL1 + 1):
            seen.add(int(gray[y, x]))
    assert seen == set(SYMBOL_MAP), f"unexpected value set in ring bands: {sorted(seen)} vs {sorted(SYMBOL_MAP)}"

    candidates = all_candidate_strings(gray)
    assert len(candidates) == 6
    assert len(candidates["top_forward"]) == 252, f"expected 252 digits, got {len(candidates['top_forward'])}"
    assert len(candidates["bottom_forward"]) == 252
    assert len(candidates["top_then_bottom"]) == 504
    assert candidates["top_reversed"] == candidates["top_forward"][::-1]
    assert set(candidates["top_forward"]) <= set("0123456")

    attempts = sum(len(keystr_forms(form)) for form in candidates.values())
    assert attempts == 18, f"expected 18 passphrase attempts (6 candidates x 3 keystr forms), got {attempts}"

    print(f"[*] self-test OK: 3 finder squares byte-identical, 7-value alphabet confirmed, "
          f"6 candidates (252/252/504-digit), {attempts} passphrase attempts")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--show", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return

    if args.show:
        arr = load_image()
        boxes = locate_finder_squares(arr)
        x0, y0, x1, y1 = boxes[0]
        gray = arr[y0 : y1 + 1, x0 : x1 + 1].mean(axis=2).astype(int)
        for label, form in all_candidate_strings(gray).items():
            print(f"{label} ({len(form)}): {form}")
        return

    if not args.run:
        parser.print_help()
        return

    report = run()
    if args.json:
        print(json.dumps(report, indent=2, default=repr))
    else:
        for key, value in report.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
