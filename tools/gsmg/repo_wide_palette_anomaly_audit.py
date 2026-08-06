#!/usr/bin/env python3
"""Item 8 (`doc/GSMG_FRESH_BRAINSTORM_2026-08-06.md`): the FEFEFE "zeroing"
marker (Phases 37-48) was found by manually noticing one anomalous
near-white pixel in `doc/img/gsmg_rabbit_hint.png`'s otherwise 4-color
palette. The creator's phrasing ("some characters need to be zeroed out")
may be genuinely plural. This script generalizes that discovery method --
extract every distinct color per image and flag minority/out-of-palette
values -- across every image in the repo, rather than assuming the rabbit
grid is the only place such a marker could occur.

Two passes:

1. Full color histogram per image (distinct color count, top colors by
   frequency). This alone separates the small set of flat, computer-
   generated graphics (where an anomaly test is meaningful) from
   photographs/screenshots (hundreds to tens of thousands of distinct
   colors from natural antialiasing/compression -- no clean "expected
   palette" exists there, so a minority-color test is not diagnostic).
2. For every image, a structural filter for FEFEFE-*shaped* anomalies
   specifically: grayscale pixels (R == G == B) that are near-white/near-
   black but not exactly 0 or 255 -- the same shape of anomaly the
   original marker was (a repeated-byte near-white value sitting inside a
   pure-black/pure-white/saturated-color palette).

Excludes `doc/telegram_shortlist_*` (community-shared chat screenshots, a
different corpus, not the creator-authored puzzle images item 8 is about).
"""

import argparse
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

EXCLUDE_DIR_MARKERS = ("telegram_shortlist",)


def find_images():
    exts = ("*.png", "*.jpg", "*.jpeg", "*.gif", "*.bmp")
    paths = set()
    for pattern in exts:
        paths |= set(REPO_ROOT.glob(pattern))
        paths |= set((REPO_ROOT / "doc" / "img").glob(pattern))
    return sorted(
        p for p in paths if not any(m in str(p) for m in EXCLUDE_DIR_MARKERS)
    )


def histogram(path):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    total = w * h
    colors = im.getcolors(maxcolors=total + 1) or []
    colors.sort(key=lambda c: -c[0])
    return w, h, total, colors


def near_white_black_grayscale_anomalies(colors, total, near_threshold=8, max_share=0.02):
    """Grayscale (R==G==B) pixels within `near_threshold` of 0 or 255 but not
    exactly 0/255, occupying less than `max_share` of the image -- the same
    shape as the FEFEFE marker (near-white, minority, structurally simple)."""
    found = []
    for cnt, rgb in colors:
        r, g, b = rgb
        if r != g or g != b:
            continue
        if r in (0, 255):
            continue
        if not (r <= near_threshold or r >= 255 - near_threshold):
            continue
        if cnt / total > max_share:
            continue
        found.append((cnt, rgb))
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top", type=int, default=6, help="top-N colors to print per image")
    args = parser.parse_args()

    images = find_images()
    print(f"[*] scanning {len(images)} images (excluding telegram_shortlist corpus)\n")

    flat_graphics = []
    for path in images:
        w, h, total, colors = histogram(path)
        distinct = len(colors)
        rel = path.relative_to(REPO_ROOT)
        print(f"{rel}  {w}x{h}  distinct_colors={distinct}")
        anomalies = near_white_black_grayscale_anomalies(colors, total)
        if anomalies:
            for cnt, rgb in anomalies:
                pct = 100 * cnt / total
                print(f"    ANOMALY  #{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}  count={cnt} ({pct:.4f}%)")
        if distinct <= 20:
            flat_graphics.append((rel, distinct, colors))

    print("\n[*] flat/computer-generated graphics (<=20 distinct colors -- where a")
    print("    minority-color anomaly test is actually diagnostic):")
    for rel, distinct, colors in flat_graphics:
        print(f"\n  {rel} ({distinct} colors):")
        for cnt, rgb in colors:
            print(f"    #{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}  count={cnt}")


if __name__ == "__main__":
    main()
