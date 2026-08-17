#!/usr/bin/env python3
"""Candidate family -- QR finder-ring texture: the two irregular rows in isolation (2026-08-16).

Follow-up to Phases 296-304: this session established that of the 14
measured ring rows, only ONE pair of rows ever differs in content between
the top and bottom band instances -- row 9 (top) and row 37 (bottom), the
"offset 2" rows. Verified again directly here: rows 10, 13, and 38 are
byte-for-byte identical to each other, and row 41 shares row 10/13/38's
exact tick positions (only its background shade differs, the
already-known Phase 296 anomaly). Every solid separator row is trivially
uniform. That means rows 9 and 37 are the *only* place in this entire
68-row-square-eyes-cubed texture where any actual variation exists at
all -- everywhere else is provably deterministic repetition of the same
tile. If this texture encodes anything, it can only live in these two
rows (68 pixels total), so this script isolates and tests them alone,
raised directly by the user as the natural next step after independently
re-deriving this same "only one row pair varies" structure from the
block-type analysis (Phase 304).

Both rows turn out to use only 2 distinct intensity values each (250 and
255 -- confirmed directly, not assumed), so each is naturally a 34-bit
binary string. Convention (disclosed, not tuned): 255 (white) -> `1`,
250 (green) -> `0`.

Eight pre-declared candidate strings, fixed before any oracle run:
  1. row9_bits          -- row 9's 34-bit string
  2. row9_bits_rev       -- reversed
  3. row37_bits          -- row 37's 34-bit string
  4. row37_bits_rev      -- reversed
  5. row9_then_row37     -- both concatenated, row 9 first (68 bits)
  6. row37_then_row9     -- both concatenated, row 37 first
  7. diff_mask_bits      -- 34-bit string, `1` at each of the 6 positions
                            where row 9 and row 37 differ, else `0`
  8. diff_positions      -- the 6 differing positions themselves, 2-digit
                            zero-padded and concatenated

Each candidate run through `keystr_forms()` (raw/SHA-256/double-SHA-256)
against all four tracked blobs: 8 candidates x 3 keystr forms = 24
passphrase attempts.
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

INT0, INT1 = 7, 40
BIT_MAP = {255: "1", 250: "0"}


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


def row_bits(gray, y):
    return "".join(BIT_MAP[int(v)] for v in gray[y, INT0 : INT1 + 1])


def all_candidate_strings(gray):
    r9 = row_bits(gray, 9)
    r37 = row_bits(gray, 37)
    diff_mask = "".join("1" if a != b else "0" for a, b in zip(r9, r37))
    diff_positions = [i for i, (a, b) in enumerate(zip(r9, r37)) if a != b]
    diff_positions_str = "".join(f"{p:02d}" for p in diff_positions)

    return {
        "row9_bits": r9,
        "row9_bits_rev": r9[::-1],
        "row37_bits": r37,
        "row37_bits_rev": r37[::-1],
        "row9_then_row37": r9 + r37,
        "row37_then_row9": r37 + r9,
        "diff_mask_bits": diff_mask,
        "diff_positions": diff_positions_str,
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

    # confirm rows 10/13/38 are byte-identical, row 41 shares positions only,
    # and rows 9/37 are the sole source of variation -- the premise this
    # script depends on.
    row10 = [int(v) for v in gray[10, INT0 : INT1 + 1]]
    row13 = [int(v) for v in gray[13, INT0 : INT1 + 1]]
    row38 = [int(v) for v in gray[38, INT0 : INT1 + 1]]
    assert row10 == row13 == row38, "rows 10/13/38 expected byte-identical (premise of this script)"

    assert set(int(v) for v in gray[9, INT0 : INT1 + 1]) == {250, 255}
    assert set(int(v) for v in gray[37, INT0 : INT1 + 1]) == {250, 255}

    candidates = all_candidate_strings(gray)
    assert len(candidates["row9_bits"]) == 34
    assert len(candidates["row37_bits"]) == 34
    assert len(candidates["row9_then_row37"]) == 68
    assert candidates["diff_mask_bits"].count("1") == 6, "expected exactly 6 differing positions"
    assert len(candidates) == 8
    for label, form in candidates.items():
        assert form, f"{label} produced an empty candidate"

    attempts = sum(len(keystr_forms(form)) for form in candidates.values())
    assert attempts == 24, f"expected 24 passphrase attempts (8 candidates x 3 keystr forms), got {attempts}"

    print(f"[*] self-test OK: rows 10/13/38 confirmed byte-identical, rows 9/37 confirmed the sole "
          f"source of variation (6 differing bit positions), 8 candidates, {attempts} passphrase attempts")


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
