#!/usr/bin/env python3
"""Cross-check a 2020 community diagram's "rabbit hole"/"rabbit nest" markings
against this project's own independently-reconstructed first-piece grid.

On 2020-03-24 (old `chat_transcript.txt:6848`; recovered in the complete
Telegram export as message `2899`, sender anonymized, photo
`photos/photo_41@25-03-2020_01-44-49.jpg`,
sha256=`550f34830161baea93414ce116f07407c164657ffaa3fc9061a149324238f9ee`), a
community member posted a hand-transcribed 14x14 grid with three annotations:

    1. rabbit hole marked (rabbit looking to this point).
    2. usual spiral solve showed.
    3. rabbit nest is white box at center.

nieods replied "that's a really good image!" immediately after. This predates
almost all of this project's own reconstruction work by over five years and
was never previously cross-referenced against it -- Phase 40 only cited the
recurring "rabbits nest" catchphrase, not this specific diagram's exact
marked cells.

Pixel-level reading of the diagram (zoomed 3x) places the single highlighted
("rabbit hole") cell at row 8, column 5 (1-indexed), and the white unlabeled
("rabbit nest") box at rows 7-8, columns 7-8. This module checks both against
this project's own `first_piece_color_reconstruction.py` output, computed
from the actual puzzle image via a completely independent method (RGB pixel
classification, not hand-transcription).
"""

import argparse

from first_piece_color_reconstruction import (
    COLOR_NAMES,
    DEFAULT_IMAGE,
    FEFE,
    load_grid,
    reconstruct,
    spiral_top_left_counterclockwise,
)

TELEGRAM_MESSAGE_ID = 2899
TELEGRAM_PHOTO = "photos/photo_41@25-03-2020_01-44-49.jpg"
TELEGRAM_PHOTO_SHA256 = "550f34830161baea93414ce116f07407c164657ffaa3fc9061a149324238f9ee"
OLD_TRANSCRIPT_LINE = 6848

DIAGRAM_HOLE_1_INDEXED = (8, 5)
DIAGRAM_NEST_1_INDEXED = ((7, 7), (8, 7), (8, 8), (7, 8))

CHARACTERS_DECODED = 24
BITS_PER_CHARACTER = 8


def hole_matches_fefe(image_path=DEFAULT_IMAGE):
    image = reconstruct(image_path)
    fefe_spiral_0 = image["fefe"]["spiral_0"]
    coords = spiral_top_left_counterclockwise()
    row_0, col_0 = coords[fefe_spiral_0]
    fefe_1_indexed = (row_0 + 1, col_0 + 1)

    grid = load_grid(image_path)
    diagram_row, diagram_col = DIAGRAM_HOLE_1_INDEXED
    diagram_rgb = grid[diagram_row - 1][diagram_col - 1]

    return {
        "fefe_spiral_0": fefe_spiral_0,
        "fefe_1_indexed": fefe_1_indexed,
        "diagram_hole_1_indexed": DIAGRAM_HOLE_1_INDEXED,
        "coordinates_match": fefe_1_indexed == DIAGRAM_HOLE_1_INDEXED,
        "diagram_hole_rgb": diagram_rgb,
        "diagram_hole_is_fefe_color": diagram_rgb == FEFE,
    }


def nest_cells(image_path=DEFAULT_IMAGE):
    coords = spiral_top_left_counterclockwise()
    used = CHARACTERS_DECODED * BITS_PER_CHARACTER
    leftover_0_indexed = coords[used:]
    leftover_1_indexed = tuple((row + 1, col + 1) for row, col in leftover_0_indexed)

    grid = load_grid(image_path)
    colors = tuple(
        COLOR_NAMES.get(grid[row - 1][col - 1], grid[row - 1][col - 1])
        for row, col in leftover_1_indexed
    )
    return {
        "total_spiral_cells": len(coords),
        "cells_consumed_by_decode": used,
        "leftover_count": len(leftover_1_indexed),
        "leftover_1_indexed": leftover_1_indexed,
        "leftover_colors": colors,
        "matches_diagram_nest": set(leftover_1_indexed) == set(DIAGRAM_NEST_1_INDEXED),
    }


def audit(image_path=DEFAULT_IMAGE):
    return {
        "telegram_message_id": TELEGRAM_MESSAGE_ID,
        "telegram_photo": TELEGRAM_PHOTO,
        "telegram_photo_sha256": TELEGRAM_PHOTO_SHA256,
        "hole": hole_matches_fefe(image_path),
        "nest": nest_cells(image_path),
    }


def self_test(image_path=DEFAULT_IMAGE):
    report = audit(image_path)
    hole = report["hole"]
    assert hole["fefe_1_indexed"] == (8, 5)
    assert hole["coordinates_match"] is True
    assert hole["diagram_hole_is_fefe_color"] is True

    nest = report["nest"]
    assert nest["total_spiral_cells"] == 196
    assert nest["cells_consumed_by_decode"] == 192
    assert nest["leftover_count"] == 4
    assert nest["matches_diagram_nest"] is True
    assert nest["leftover_colors"] == ("white", "white", "white", "white")

    print(
        "[*] self-test OK: the 2020 diagram's 'rabbit hole' cell (row 8, col 5) "
        "is exactly the FEFE cell, and its 'rabbit nest' box (rows 7-8, cols "
        "7-8) is exactly the 4 spiral cells left over after the 192-bit/"
        "24-character decode (all 4 white, matching the diagram exactly)"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--image", default=DEFAULT_IMAGE)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    self_test(args.image)
    if args.self_test:
        return

    report = audit(args.image)
    print(f"[*] provenance: Telegram message {report['telegram_message_id']}, "
          f"photo {report['telegram_photo']}, sha256={report['telegram_photo_sha256']}")
    print(f"[*] old transcript citation: chat_transcript.txt:{OLD_TRANSCRIPT_LINE}")
    hole = report["hole"]
    print(f"[*] FEFE cell: spiral_0={hole['fefe_spiral_0']} -> {hole['fefe_1_indexed']} (1-indexed)")
    print(f"[*] diagram 'rabbit hole' cell: {hole['diagram_hole_1_indexed']} "
          f"rgb={hole['diagram_hole_rgb']} matches_fefe={hole['diagram_hole_is_fefe_color']}")
    nest = report["nest"]
    print(f"[*] leftover spiral cells beyond the 192-bit decode: {nest['leftover_1_indexed']}")
    print(f"[*] their colors: {nest['leftover_colors']}")
    print(f"[*] matches diagram's 'rabbit nest' box: {nest['matches_diagram_nest']}")
    print(
        "[*] verdict: the 2020 community diagram's two annotations are exact, "
        "independent corroboration of this project's own reconstruction -- "
        "'rabbit hole' names the FEFE marker cell, and 'rabbit nest' names the "
        "4 cells the spiral traversal passes but the 24-character decode never "
        "consumes. Neither annotation supplies a new operation: FEFE's role is "
        "already established (Phase 48), and all 4 nest cells are genuinely "
        "white background (corrected -- see Phase 127; a single-pixel sampler "
        "previously misread one of them as black due to overlaid rabbit ink), "
        "carrying no signal beyond ordinary background."
    )


if __name__ == "__main__":
    main()
