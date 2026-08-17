#!/usr/bin/env python3
"""Candidate family -- QR finder-ring texture: 3-symbol line-type sequence (2026-08-16).

New idea raised directly by the user during the "Divergence pass 2"
follow-up conversation in
doc/Brainstorms/2026-08-16 - QR Finder-Pattern Ring Texture Investigation.md:
instead of reading individual pixels (idea 3, Phase 301) or tick gaps
(idea 2, Phase 302), classify each *row as a whole* into one of a small
number of line "types" and read the row-type sequence itself as a symbol
string -- a coarser, different-granularity derived object than either
prior idea.

Classification rule (mechanical, pre-declared, exactly 3 types -- matches
the user's own observation of "3 unique line types" before this script
confirmed it numerically): for each of the 14 already-established ring
rows (top band 7-13, bottom band 35-41), look at the interior columns
(7-40, excluding the two edge boundary-AA columns, same region used by
Phase 301/302):
  - all pixels exactly 255            -> type W (solid white)
  - all pixels exactly 250            -> type G (solid green/gray)
  - anything else (2+ distinct values) -> type T (textured/tick row)

Applying this rule to the real pixel data gives the row-type sequence
`WGTTWGTWGTTWGT` (14 rows) -- which is exactly the already-known 7-row
tile (`WGTTWGT`, rows 7-13) repeated twice (rows 35-41 reproduce it
exactly), not new structure by itself, but a legitimately different
candidate object for the oracle than the pixel- or gap-level reads
already tried.

Six pre-declared candidate strings, fixed before any oracle run:
  1. digit_full       -- 14-symbol sequence, W=0/G=1/T=2, forward
  2. digit_full_rev    -- same, reversed
  3. digit_tile        -- the 7-symbol deduplicated tile, forward
  4. digit_tile_rev    -- same, reversed
  5. letter_full        -- the literal WGT... string as ASCII text
  6. letter_tile         -- the 7-character deduplicated tile as ASCII text

Each run through `keystr_forms()` (raw/SHA-256/double-SHA-256) against all
four tracked blobs: 6 candidates x 3 keystr forms = 18 passphrase attempts.
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

RING_ROWS = list(range(7, 14)) + list(range(35, 42))
TILE_ROWS = list(range(7, 14))
INT0, INT1 = 7, 40
DIGIT_MAP = {"W": "0", "G": "1", "T": "2"}


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


def row_type(gray, y):
    vals = set(int(v) for v in gray[y, INT0 : INT1 + 1])
    if vals == {255}:
        return "W"
    if vals == {250}:
        return "G"
    return "T"


def type_sequence(gray, rows):
    return "".join(row_type(gray, y) for y in rows)


def all_candidate_strings(gray):
    full = type_sequence(gray, RING_ROWS)
    tile = type_sequence(gray, TILE_ROWS)
    digit_full = "".join(DIGIT_MAP[c] for c in full)
    digit_tile = "".join(DIGIT_MAP[c] for c in tile)
    return {
        "digit_full": digit_full,
        "digit_full_rev": digit_full[::-1],
        "digit_tile": digit_tile,
        "digit_tile_rev": digit_tile[::-1],
        "letter_full": full,
        "letter_tile": tile,
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
        "candidates": candidates,
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
    full = type_sequence(gray, RING_ROWS)
    tile = type_sequence(gray, TILE_ROWS)
    assert full == "WGTTWGTWGTTWGT", f"unexpected type sequence: {full}"
    assert tile == "WGTTWGT", f"unexpected tile: {tile}"
    assert full == tile + tile, "the 14-row sequence must be exactly the 7-row tile repeated twice"
    assert set(full) == {"W", "G", "T"}, "expected exactly 3 line types"

    candidates = all_candidate_strings(gray)
    assert len(candidates) == 6
    for label, form in candidates.items():
        assert form, f"{label} produced an empty candidate"

    attempts = sum(len(keystr_forms(form)) for form in candidates.values())
    assert attempts == 18, f"expected 18 passphrase attempts (6 candidates x 3 keystr forms), got {attempts}"

    print(f"[*] self-test OK: 3 finder squares byte-identical, type sequence 'WGTTWGTWGTTWGT' confirmed "
          f"(7-row tile repeated twice, exactly 3 line types), 6 candidates, {attempts} passphrase attempts")


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
            print(f"{label}: {form}")
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
