#!/usr/bin/env python3
"""Candidate family -- QR finder-ring texture: user-specified color-to-binary
reading, with and without center-square continuation (2026-08-16).

New idea specified directly by the user during the "Divergence pass 2"
follow-up conversation: read the ring using the same 8-color categorical
palette from Phase 300 (`qr_finder_ring_texture_categorical_render_audit.py`),
but this time map colors to bits (not the earlier 3-way W/G/T bucketing):

  bit 1: green (250), dark red (15), orange (234)
  bit 0: white (255), red (16), yellow (236), cyan (252)

(pure black, 0, never occurs inside the ring band or the continued fill,
so it needs no mapping here.) Read row-major, top-to-bottom left-to-right,
across the full 36-column ring width (cols 6-41, including the two edge
boundary-AA columns this time -- unlike Phases 301/302/305, since the
user's mapping explicitly assigns bits to the edge colors orange/yellow/
dark-red/red too).

Two readings, both requested explicitly:
  1. "without continuation" -- only the 14 real, measured ring rows
     (top band 7-13, bottom band 35-41). 14 x 36 = 504 bits.
  2. "with continuation" -- all 35 rows from 7 to 41 inclusive, using the
     Phase-300-adjacent hypothetical fill from
     `qr_finder_ring_texture_center_square_continuation_render.py` (the
     real top-band 7-row tile copied 3x into the actually-solid-black
     21x21px center square, cols 13-33). This is NOT real pixel data for
     rows 14-34's center columns -- it's the same disclosed extrapolation
     used earlier, included here only because the user explicitly asked
     for a reading that continues through the black square. 35 x 36 =
     1260 bits.

Four candidates, fixed before any oracle run: each reading's bit string,
forward and reversed. Each run through `keystr_forms()`
(raw/SHA-256/double-SHA-256) against all four tracked blobs: 4 candidates
x 3 keystr forms = 12 passphrase attempts.
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

FINDER_BOX = (2, 1289, 49, 1337)
COL0, COL1 = 6, 41  # full ring width, including the two edge AA columns
WITHOUT_ROWS = list(range(7, 14)) + list(range(35, 42))
WITH_ROWS = list(range(7, 42))  # 7-41 inclusive, continuous span
TEMPLATE_ROWS = range(7, 14)
CENTER_ROW_LO, CENTER_ROW_HI = 14, 34
CENTER_COL_LO, CENTER_COL_HI = 13, 33

BIT_MAP = {
    250: "1",  # green
    15: "1",   # dark red
    234: "1",  # orange
    255: "0",  # white
    16: "0",   # red
    236: "0",  # yellow
    252: "0",  # cyan
}


def load_gray():
    im = Image.open(IMAGE_PATH).convert("RGB")
    arr = np.array(im)
    x0, y0, x1, y1 = FINDER_BOX
    region = arr[y0 : y1 + 1, x0 : x1 + 1]
    return region.mean(axis=2).astype(int)


def build_continued_grid(gray):
    grid = gray.copy()
    template = gray[list(TEMPLATE_ROWS), CENTER_COL_LO : CENTER_COL_HI + 1]
    n_center_rows = CENTER_ROW_HI - CENTER_ROW_LO + 1
    assert n_center_rows % len(template) == 0
    n_repeats = n_center_rows // len(template)
    for rep in range(n_repeats):
        for i in range(len(template)):
            y = CENTER_ROW_LO + rep * len(template) + i
            grid[y, CENTER_COL_LO : CENTER_COL_HI + 1] = template[i]
    return grid


def bits_for_rows(grid, rows):
    out = []
    for y in rows:
        for x in range(COL0, COL1 + 1):
            v = int(grid[y, x])
            out.append(BIT_MAP[v])
    return "".join(out)


def all_candidate_strings(gray):
    without = bits_for_rows(gray, WITHOUT_ROWS)
    continued = build_continued_grid(gray)
    withc = bits_for_rows(continued, WITH_ROWS)
    return {
        "without_continuation": without,
        "without_continuation_rev": without[::-1],
        "with_continuation": withc,
        "with_continuation_rev": withc[::-1],
    }


def run():
    gray = load_gray()
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
        "finder_square_bbox": FINDER_BOX,
        "candidate_lengths": {k: len(v) for k, v in candidates.items()},
        "passphrase_attempts": len(attempts),
        "blobs": tuple(BLOBS),
        "hits": hits,
        "total_hits": len(hits),
    }


def self_test():
    gray = load_gray()
    seen = set()
    for y in WITHOUT_ROWS:
        for x in range(COL0, COL1 + 1):
            seen.add(int(gray[y, x]))
    assert seen <= set(BIT_MAP), f"unmapped value(s) found in ring rows: {seen - set(BIT_MAP)}"

    candidates = all_candidate_strings(gray)
    assert len(candidates["without_continuation"]) == 504, "expected 14x36=504 bits"
    assert len(candidates["with_continuation"]) == 1260, "expected 35x36=1260 bits"
    assert candidates["without_continuation_rev"] == candidates["without_continuation"][::-1]
    assert candidates["with_continuation_rev"] == candidates["with_continuation"][::-1]
    assert set(candidates["without_continuation"]) <= {"0", "1"}
    assert set(candidates["with_continuation"]) <= {"0", "1"}

    # the two readings must agree on the real (non-extrapolated) rows
    without = candidates["without_continuation"]
    withc = candidates["with_continuation"]
    top_from_with = withc[: 7 * 36]
    bot_from_with = withc[-7 * 36 :]
    assert without[: 7 * 36] == top_from_with, "top band bits must match between the two readings"
    assert without[-7 * 36 :] == bot_from_with, "bottom band bits must match between the two readings"

    attempts = sum(len(keystr_forms(form)) for form in candidates.values())
    assert attempts == 12, f"expected 12 passphrase attempts (4 candidates x 3 keystr forms), got {attempts}"

    print(f"[*] self-test OK: all ring values mapped, without=504 bits, with=1260 bits, "
          f"both readings agree on real rows, {attempts} passphrase attempts")


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
        gray = load_gray()
        for label, form in all_candidate_strings(gray).items():
            print(f"{label} ({len(form)} bits): {form}")
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
