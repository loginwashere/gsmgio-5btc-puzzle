#!/usr/bin/env python3
"""Candidate family -- QR finder-ring texture: row-tick position/gap sequence (2026-08-16).

Executes idea 2 from the "Divergence pass 2" section of
doc/Brainstorms/2026-08-16 - QR Finder-Pattern Ring Texture Investigation.md.
Idea 3 (`qr_finder_ring_texture_intensity_alphabet_audit.py`, FINDINGS.md
Phase 301) read every ring pixel as a flat symbol sequence; this idea is a
different derived object -- it isolates just the "tick" rows (rows whose
interior contains two distinct intensity values rather than one uniform
background) and reads off the *positions* of the minority value as a
number sequence, not row content wholesale.

Region and tick-row selection (mechanical rule, fixed before extraction,
not a cherry-picked row list): same top/bottom band geometry as Phase 296/
297/301 (rows 7-13 and 35-41, cols 6-41 of the first located finder
square). Within each row, the two edge columns (absolute col 6 and col 41)
are excluded -- they carry the already-explained, separately-documented
boundary-antialiasing value (234/236 on the left edge, 15/16 on the
right), not the interior tick texture. A row qualifies as a "tick row" iff
its remaining 34 interior columns (7-40) contain 2+ distinct values. This
mechanical rule (not manual inspection) finds exactly 6 tick rows: 9, 10,
13 (top band), 37, 38, 41 (bottom band) -- matching the doc's own earlier
"rows 9/10/13" example.

Per tick row, the "tick" value is defined as whichever of the row's two
interior values occurs less often (a majority background + minority tick
pattern in every one of the 6 rows, confirmed directly, not assumed).
Column positions (0-indexed within the 34-wide interior) of the tick value
are extracted, and the gap sequence is the pairwise differences between
consecutive positions.

Six pre-declared candidate strings, fixed before any oracle run:
  1. all 6 rows' gap sequences concatenated (row order 9,10,13,37,38,41),
     each gap as a single base-36 digit
  2. all 6 rows' absolute tick positions concatenated, 2-digit zero-padded
  3. row 9's gap sequence alone (the most irregular row)
  4. row 37's gap sequence alone (the other irregular row)
  5. the sorted set of distinct gap values seen across all 6 rows, as a
     string (captures a "gap alphabet" reading)
  6. all 6 rows' gap sequences joined with "|" separators (preserves row
     boundaries, unlike candidate 1)

Each candidate is run through `keystr_forms()` (raw/SHA-256/double-SHA-256)
against all four tracked blobs: 6 candidates x 3 keystr forms = 18
passphrase attempts.
"""

import argparse
import json
import sys
from collections import Counter, deque
from pathlib import Path

import numpy as np
from PIL import Image

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
REPO_ROOT = SCRIPT_DIR.parent.parent
IMAGE_PATH = REPO_ROOT / "doc" / "img" / "gsmg_puzzle_stage1.png"

from cb_common import BLOBS, aes_try_open_bytes, keystr_forms  # noqa: E402

RING_ROWS = list(range(7, 14)) + list(range(35, 42))
INT0, INT1 = 7, 40  # interior columns, excludes the two edge boundary-AA columns


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


def find_tick_rows(gray):
    """Mechanical rule: interior (cols 7-40) has 2+ distinct values."""
    tick_rows = {}
    for y in RING_ROWS:
        row = [int(v) for v in gray[y, INT0 : INT1 + 1]]
        distinct = set(row)
        if len(distinct) > 1:
            tick_rows[y] = row
    return tick_rows


def tick_positions_and_gaps(row):
    c = Counter(row)
    minority_val = min(c, key=lambda k: c[k])
    positions = [i for i, v in enumerate(row) if v == minority_val]
    gaps = [positions[i + 1] - positions[i] for i in range(len(positions) - 1)]
    return minority_val, positions, gaps


def build_report(gray):
    tick_rows = find_tick_rows(gray)
    per_row = {}
    for y, row in tick_rows.items():
        minority_val, positions, gaps = tick_positions_and_gaps(row)
        per_row[y] = {"minority_value": minority_val, "positions": positions, "gaps": gaps}
    return per_row


def all_candidate_strings(per_row):
    order = sorted(per_row)
    all_gaps = [g for y in order for g in per_row[y]["gaps"]]
    all_positions = [p for y in order for p in per_row[y]["positions"]]

    def b36(n):
        digits = "0123456789abcdefghijklmnopqrstuvwxyz"
        return digits[n] if n < 36 else "z"

    cand1 = "".join(b36(g) for g in all_gaps)
    cand2 = "".join(f"{p:02d}" for p in all_positions)
    cand3 = "".join(b36(g) for g in per_row[9]["gaps"])
    cand4 = "".join(b36(g) for g in per_row[37]["gaps"])
    cand5 = "".join(str(g) for g in sorted(set(all_gaps)))
    cand6 = "|".join("".join(b36(g) for g in per_row[y]["gaps"]) for y in order)

    return {
        "all_gaps_concat": cand1,
        "all_positions_concat": cand2,
        "row9_gaps": cand3,
        "row37_gaps": cand4,
        "distinct_gap_alphabet": cand5,
        "per_row_gaps_piped": cand6,
    }


def run():
    arr = load_image()
    boxes = locate_finder_squares(arr)
    x0, y0, x1, y1 = boxes[0]
    r = arr[y0 : y1 + 1, x0 : x1 + 1]
    gray = r.mean(axis=2).astype(int)

    per_row = build_report(gray)
    candidates = all_candidate_strings(per_row)

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
        "tick_rows": {y: v for y, v in per_row.items()},
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
    per_row = build_report(gray)
    assert set(per_row) == {9, 10, 13, 37, 38, 41}, f"expected exactly 6 tick rows, got {sorted(per_row)}"
    for y, info in per_row.items():
        assert len(info["positions"]) >= 2, f"row {y} tick row must have 2+ minority positions"
        assert len(info["gaps"]) == len(info["positions"]) - 1

    candidates = all_candidate_strings(per_row)
    assert len(candidates) == 6
    for label, form in candidates.items():
        assert form, f"{label} produced an empty candidate"

    attempts = sum(len(keystr_forms(form)) for form in candidates.values())
    assert attempts == 18, f"expected 18 passphrase attempts (6 candidates x 3 keystr forms), got {attempts}"

    print(f"[*] self-test OK: 3 finder squares byte-identical, 6 tick rows found (9,10,13,37,38,41), "
          f"6 candidates, {attempts} passphrase attempts")


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
        per_row = build_report(gray)
        for y, info in per_row.items():
            print(f"row {y}: minority={info['minority_value']} positions={info['positions']} gaps={info['gaps']}")
        print()
        for label, form in all_candidate_strings(per_row).items():
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
