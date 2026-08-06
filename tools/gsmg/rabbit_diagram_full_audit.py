#!/usr/bin/env python3
"""Audit every encoded cell and byte separator in the 2020 rabbit diagram.

The diagram is Telegram message 2899's photo.  Its left panel transcribes the
real 14x14 first-piece image with:

    black -> "*", white -> blank, blue -> "b", yellow -> "y"

The FEFE cell is highlighted but blank, and the central four-cell "nest" is
also blank.  The right panel writes the 24 decoded characters in three
eight-character spiral rings; punctuation is expanded as "dot" and "slash".

Cell symbols and red separators are checked from pixels.  The scattered
right-panel letters are a manual 4x transcription tied to the exact image
hash; this script deliberately does not present that transcription as OCR.
"""

import argparse
import hashlib
from pathlib import Path

from PIL import Image

from first_piece_color_reconstruction import (
    BLACK,
    BLUE,
    DEFAULT_IMAGE,
    FEFE,
    TARGET,
    WHITE,
    YELLOW,
    load_grid,
    spiral_top_left_counterclockwise,
)

DIAGRAM_SHA256 = "550f34830161baea93414ce116f07407c164657ffaa3fc9061a149324238f9ee"
DEFAULT_DIAGRAM = Path(
    "/home/loginwashere/Downloads/photo_2020-03-25_02-10-57.jpg"
)

ROWS = COLUMNS = 14
LEFT_X = 0
RIGHT_X = 390
GRID_Y = 27
CELL_WIDTH = 26
CELL_HEIGHT = 27

NEST_CELLS_0 = frozenset(((6, 6), (7, 6), (7, 7), (6, 7)))
RIGHT_RING_TRANSCRIPTION = ("gsmg.io/", "theseedi", "splanted")
RIGHT_DISPLAY_TRANSCRIPTION = ("gsmg dot io slash", "theseedi", "splanted")


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dark_pixel_count(image, row, column):
    """Count glyph pixels in a cell-center box that excludes all grid lines."""
    x0 = LEFT_X + column * CELL_WIDTH
    y0 = GRID_Y + row * CELL_HEIGHT
    return sum(
        max(image.getpixel((x, y))) < 100
        for y in range(y0 + 5, y0 + 22)
        for x in range(x0 + 5, x0 + 22)
    )


def observed_symbol(image, row, column):
    count = dark_pixel_count(image, row, column)
    if count == 0:
        return ""
    if count <= 12:
        return "*"
    if count <= 20:
        return "y"
    return "b"


def expected_symbol(pixel, row, column):
    if (row, column) in NEST_CELLS_0:
        return ""
    return {
        BLACK: "*",
        WHITE: "",
        BLUE: "b",
        YELLOW: "y",
        FEFE: "",
    }[pixel]


def orange_highlight_count(image, row, column):
    x0 = LEFT_X + column * CELL_WIDTH
    y0 = GRID_Y + row * CELL_HEIGHT
    return sum(
        red > 240 and red - green > 10 and green - blue > 15
        for y in range(y0 + 2, y0 + 25)
        for x in range(x0 + 2, x0 + 24)
        for red, green, blue in (image.getpixel((x, y)),)
    )


def transcribe_left(image, source_image=DEFAULT_IMAGE):
    source = load_grid(source_image)
    observed = []
    expected = []
    mismatches = []
    for row in range(ROWS):
        observed_row = []
        expected_row = []
        for column in range(COLUMNS):
            actual = observed_symbol(image, row, column)
            wanted = expected_symbol(source[row][column], row, column)
            observed_row.append(actual or ".")
            expected_row.append(wanted or ".")
            if actual != wanted:
                mismatches.append(
                    {
                        "row_1": row + 1,
                        "column_1": column + 1,
                        "observed": actual or "blank",
                        "expected": wanted or "blank",
                        "dark_pixels": dark_pixel_count(image, row, column),
                    }
                )
        observed.append("".join(observed_row))
        expected.append("".join(expected_row))

    highlighted = []
    for row in range(ROWS):
        for column in range(COLUMNS):
            count = orange_highlight_count(image, row, column)
            if count > 100:
                highlighted.append((row + 1, column + 1, count))

    return {
        "observed_rows": tuple(observed),
        "expected_rows": tuple(expected),
        "mismatches": tuple(mismatches),
        "orange_highlights": tuple(highlighted),
    }


def is_red(pixel):
    red, green, blue = pixel
    return red > 80 and red - green > 50 and red - blue > 40


def edge_red_score(image, first, second, panel_x):
    row_1, column_1 = first
    row_2, column_2 = second
    if row_1 == row_2:
        x = panel_x + CELL_WIDTH * max(column_1, column_2)
        y0 = GRID_Y + CELL_HEIGHT * row_1
        points = (
            (x + delta, y)
            for delta in range(-3, 4)
            for y in range(y0 + 2, y0 + 25)
        )
    else:
        y = GRID_Y + CELL_HEIGHT * max(row_1, row_2)
        x0 = panel_x + CELL_WIDTH * column_1
        points = (
            (x, y + delta)
            for delta in range(-3, 4)
            for x in range(x0 + 2, x0 + 24)
        )
    return sum(is_red(image.getpixel(point)) for point in points)


def all_internal_edges():
    for row in range(ROWS):
        for column in range(COLUMNS - 1):
            yield (row, column), (row, column + 1)
    for row in range(ROWS - 1):
        for column in range(COLUMNS):
            yield (row, column), (row + 1, column)


def separator_audit(image, panel_x):
    coordinates = spiral_top_left_counterclockwise()
    expected_with_nest_boundary = tuple(
        (coordinates[index], coordinates[index + 1])
        for index in range(7, 192, 8)
    )
    visible_expected = frozenset(
        frozenset(edge) for edge in expected_with_nest_boundary[:-1]
    )
    detected = frozenset(
        frozenset((first, second))
        for first, second in all_internal_edges()
        if edge_red_score(image, first, second, panel_x) > 20
    )
    final_edge = expected_with_nest_boundary[-1]
    return {
        "expected_visible_count": len(visible_expected),
        "detected_count": len(detected),
        "missing": visible_expected - detected,
        "extra": detected - visible_expected,
        "final_nest_boundary": final_edge,
        "final_nest_boundary_red_score": edge_red_score(
            image, *final_edge, panel_x
        ),
    }


def audit(diagram_path=DEFAULT_DIAGRAM, source_image=DEFAULT_IMAGE):
    image = Image.open(diagram_path).convert("RGB")
    if image.size != (781, 433):
        raise AssertionError(f"unexpected diagram dimensions: {image.size}")
    return {
        "sha256": file_sha256(diagram_path),
        "left": transcribe_left(image, source_image),
        "left_separators": separator_audit(image, LEFT_X),
        "right_separators": separator_audit(image, RIGHT_X),
        "right_ring_transcription": RIGHT_RING_TRANSCRIPTION,
        "right_display_transcription": RIGHT_DISPLAY_TRANSCRIPTION,
        "right_decoded": "".join(RIGHT_RING_TRANSCRIPTION),
    }


def self_test(diagram_path=DEFAULT_DIAGRAM, source_image=DEFAULT_IMAGE):
    report = audit(diagram_path, source_image)
    assert report["sha256"] == DIAGRAM_SHA256

    left = report["left"]
    assert not left["mismatches"], left["mismatches"]
    assert left["observed_rows"] == left["expected_rows"]
    assert left["orange_highlights"] == ((8, 5, 412),)

    for key in ("left_separators", "right_separators"):
        separators = report[key]
        assert separators["expected_visible_count"] == 23
        assert separators["detected_count"] == 23
        assert not separators["missing"]
        assert not separators["extra"]
        assert separators["final_nest_boundary"] == ((5, 6), (6, 6))
        assert separators["final_nest_boundary_red_score"] == 0

    assert report["right_decoded"] == TARGET
    print(
        "[*] self-test OK: all 196 left-panel symbols match the real grid; "
        "the sole orange highlight is FEFE at (8,5); both panels contain "
        "exactly the same 23 visible red byte separators; and the manually "
        "transcribed right rings read gsmg.io/ + theseedi + splanted"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--diagram", type=Path, default=DEFAULT_DIAGRAM)
    parser.add_argument("--source-image", type=Path, default=DEFAULT_IMAGE)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    self_test(args.diagram, args.source_image)
    if args.self_test:
        return

    report = audit(args.diagram, args.source_image)
    print(f"diagram sha256: {report['sha256']}")
    print("left-panel transcription (. = blank):")
    for row_number, row in enumerate(report["left"]["observed_rows"], 1):
        print(f"  {row_number:2}: {row}")
    print(f"orange highlights: {report['left']['orange_highlights']}")
    for name in ("left_separators", "right_separators"):
        separators = report[name]
        print(
            f"{name}: detected={separators['detected_count']} "
            f"missing={len(separators['missing'])} "
            f"extra={len(separators['extra'])} "
            f"final_nest_edge_red={separators['final_nest_boundary_red_score']}"
        )
    print(f"right rings (manual): {report['right_ring_transcription']}")
    print(f"right display (manual): {report['right_display_transcription']}")
    print(f"decoded: {report['right_decoded']}")
    print(
        "verdict: the diagram is an exact independent transcription and "
        "visual explanation of the already-validated spiral decode. It adds "
        "the useful names 'rabbit hole' for FEFE and 'rabbit nest' for the "
        "four unused center cells, but it does not add another hidden layer "
        "or an operation beyond those already audited."
    )


if __name__ == "__main__":
    main()
