#!/usr/bin/env python3
"""Candidate family -- QR finder-ring texture: textured-block type sequence (2026-08-16).

New idea raised directly by the user, refining idea 5
(`qr_finder_ring_texture_line_type_alphabet_audit.py`, FINDINGS.md Phase
303): rather than treating solid-white/solid-green rows as content
symbols alongside textured rows, treat them as SEPARATORS and look only
at the textured ("T") rows, grouped into contiguous blocks between
separators, as the actual content. The user's own visual read: there are
3 distinct block types, 2 of them 2-rows-tall and 1 of them 1-row-tall.

Block identification (mechanical): among the 14 already-established ring
rows, a maximal contiguous run of `T`-classified rows (Phase 303's
classifier: interior cols 7-40 not uniformly 255 or 250) is one block.
This finds exactly 4 blocks in row order: rows [9,10] (height 2), [13]
(height 1), [37,38] (height 2), [41] (height 1) -- matching the user's
"2 types are 2-cell, one is 1-cell" observation on height alone.

Block *type* (distinct from height) is assigned mechanically, not by eye:
two blocks share a type iff their per-row minority-pixel counts (already
established methodology, Phase 302) match exactly, row-for-row, in order.
This gives signatures (12,9), (9,), (6,9), (9,) for the 4 blocks -- three
distinct signatures, letters assigned in first-appearance order A, B, C:
block sequence **A, B, C, B**. This independently reproduces the user's
"3 types, 2 of one height + 1 of the other, and the two 1-row blocks look
like the same type" observation from a fully mechanical rule, not eyeballing
-- blocks 2 and 4 (both height 1) really do have identical signatures.

Six pre-declared candidate strings, fixed before any oracle run:
  1. type_letters        -- "ABCB", the block-type sequence
  2. type_letters_rev    -- reversed
  3. type_digits          -- "0121" (A=0,B=1,C=2)
  4. block_heights        -- "2121", height of each block in order
  5. block_tick_sum       -- total minority-pixel count per block, 2-digit
                             zero-padded and concatenated ("21091509")
  6. per_row_tick_counts  -- minority-pixel count per individual textured
                             row (not summed per block), 2-digit zero-padded
                             and concatenated ("120909060909")

Each run through `keystr_forms()` (raw/SHA-256/double-SHA-256) against all
four tracked blobs: 6 candidates x 3 keystr forms = 18 passphrase attempts.
"""

import argparse
import json
import sys
from collections import Counter, deque
from itertools import groupby
from pathlib import Path

import numpy as np
from PIL import Image

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
REPO_ROOT = SCRIPT_DIR.parent.parent
IMAGE_PATH = REPO_ROOT / "doc" / "img" / "gsmg_puzzle_stage1.png"

from cb_common import BLOBS, aes_try_open_bytes, keystr_forms  # noqa: E402

RING_ROWS = list(range(7, 14)) + list(range(35, 42))
INT0, INT1 = 7, 40


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


def row_tick_count(gray, y):
    row = [int(v) for v in gray[y, INT0 : INT1 + 1]]
    c = Counter(row)
    assert len(c) > 1, f"row {y} expected to be a textured (multi-valued) row"
    minority_val = min(c, key=lambda k: c[k])
    return c[minority_val]


def find_blocks(gray):
    """Contiguous runs of T-type rows among RING_ROWS, in row order."""
    types = [(y, row_type(gray, y)) for y in RING_ROWS]
    blocks = []
    idx = 0
    for is_t, group in groupby(types, key=lambda item: item[1] == "T"):
        group = list(group)
        if is_t:
            blocks.append([y for y, _ in group])
    return blocks


def block_signatures(gray, blocks):
    return [tuple(row_tick_count(gray, y) for y in block) for block in blocks]


def assign_type_letters(signatures):
    seen = {}
    letters = []
    for sig in signatures:
        if sig not in seen:
            seen[sig] = chr(ord("A") + len(seen))
        letters.append(seen[sig])
    return letters


def all_candidate_strings(gray):
    blocks = find_blocks(gray)
    sigs = block_signatures(gray, blocks)
    letters = assign_type_letters(sigs)
    heights = [len(b) for b in blocks]
    block_sums = [sum(sig) for sig in sigs]
    per_row_counts = [c for sig in sigs for c in sig]

    letter_map = {"A": "0", "B": "1", "C": "2", "D": "3"}
    type_letters = "".join(letters)
    type_digits = "".join(letter_map[c] for c in letters)
    block_heights = "".join(str(h) for h in heights)
    block_tick_sum = "".join(f"{v:02d}" for v in block_sums)
    per_row_tick_counts = "".join(f"{v:02d}" for v in per_row_counts)

    return {
        "type_letters": type_letters,
        "type_letters_rev": type_letters[::-1],
        "type_digits": type_digits,
        "block_heights": block_heights,
        "block_tick_sum": block_tick_sum,
        "per_row_tick_counts": per_row_tick_counts,
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
    blocks = find_blocks(gray)
    assert blocks == [[9, 10], [13], [37, 38], [41]], f"unexpected block structure: {blocks}"

    sigs = block_signatures(gray, blocks)
    assert sigs == [(12, 9), (9,), (6, 9), (9,)], f"unexpected block signatures: {sigs}"

    letters = assign_type_letters(sigs)
    assert letters == ["A", "B", "C", "B"], f"unexpected type letters: {letters}"
    heights = [len(b) for b in blocks]
    assert heights == [2, 1, 2, 1], f"unexpected block heights: {heights}"
    assert sum(1 for h in heights if h == 2) == 2, "expected 2 height-2 blocks"
    assert sum(1 for h in heights if h == 1) == 2, "expected 2 height-1 blocks"
    assert len(set(sigs)) == 3, "expected exactly 3 distinct block types, matching the user's visual read"

    candidates = all_candidate_strings(gray)
    assert candidates["type_letters"] == "ABCB"
    assert candidates["block_heights"] == "2121"
    assert len(candidates) == 6
    for label, form in candidates.items():
        assert form, f"{label} produced an empty candidate"

    attempts = sum(len(keystr_forms(form)) for form in candidates.values())
    assert attempts == 18, f"expected 18 passphrase attempts (6 candidates x 3 keystr forms), got {attempts}"

    print(f"[*] self-test OK: 3 finder squares byte-identical, 4 textured blocks found "
          f"(heights 2,1,2,1; types A,B,C,B; 3 distinct types confirmed), 6 candidates, "
          f"{attempts} passphrase attempts")


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
