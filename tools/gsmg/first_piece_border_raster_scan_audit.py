#!/usr/bin/env python3
"""Test whether reading the first-piece 14x14 grid from its four sides
produces anything as tight as the established spiral construction.

Three bounded, predeclared readings are checked against the authenticated
grid (the same majority-vote classifier used by the verified spiral
reconstruction):

1. border-only: the literal outer row/column facing each side;
2. nearest-inward: for each row/column, the first blue/yellow/FEFE cell
   encountered scanning in from that side;
3. full-raster: the whole grid read as a top-to-bottom or left-to-right
   raster (and their reverses), keeping only colored cells in encounter
   order, exactly as the spiral reading keeps only colored cells along its
   own path.

No word list, cipher, or blob oracle is used.
"""

import argparse

from first_piece_color_reconstruction import (
    DEFAULT_IMAGE,
    EXPECTED_COLOR_SEQUENCE,
    N,
    BLUE,
    YELLOW,
    FEFE,
    COLOR_NAMES,
    is_prime,
    load_grid,
)

COLORED = {BLUE, YELLOW, FEFE}
SHORT = {"black": "K", "white": "W", "blue": "B", "yellow": "Y", "fefefe": "F"}
SYMBOL = {BLUE: "B", YELLOW: "Y", FEFE: "F"}


def _short(cells):
    return "".join(SHORT[COLOR_NAMES[cell]] for cell in cells)


def _counts(cells):
    cells = tuple(cells)
    return {
        "blue": sum(1 for cell in cells if cell == BLUE),
        "yellow": sum(1 for cell in cells if cell == YELLOW),
        "fefe": sum(1 for cell in cells if cell == FEFE),
    }


def _first_colored(cells):
    for cell in cells:
        if cell in COLORED:
            return cell
    return None


def _raster_value(cells):
    text = "".join(SYMBOL[cell] for cell in cells if cell in COLORED)
    bits = "".join("1" if ch == "B" else "0" for ch in text if ch != "F")
    value = int(bits, 2) if bits else None
    return {
        "text": text,
        "length_with_fefe": len(text),
        "bit_length": len(bits),
        "value": value,
        "hex": f"{value:06X}" if value is not None else None,
        "is_prime": is_prime(value) if value is not None else False,
    }


def audit(image_path=DEFAULT_IMAGE):
    grid = load_grid(image_path)
    rows = [grid[r] for r in range(N)]
    cols = [[grid[r][c] for r in range(N)] for c in range(N)]

    border = {
        "top": {"cells": _short(rows[0]), "counts": _counts(rows[0])},
        "bottom": {"cells": _short(rows[N - 1]), "counts": _counts(rows[N - 1])},
        "left": {
            "cells": _short(row[0] for row in rows),
            "counts": _counts(row[0] for row in rows),
        },
        "right": {
            "cells": _short(row[N - 1] for row in rows),
            "counts": _counts(row[N - 1] for row in rows),
        },
    }

    nearest = {
        "from_left": _counts(_first_colored(row) for row in rows),
        "from_right": _counts(_first_colored(row[::-1]) for row in rows),
        "from_top": _counts(_first_colored(col) for col in cols),
        "from_bottom": _counts(_first_colored(col[::-1]) for col in cols),
    }

    fefe_position = next(
        (r, c) for r in range(N) for c in range(N) if grid[r][c] == FEFE
    )
    fefe_note = {
        "row0": fefe_position[0],
        "col0": fefe_position[1],
        "rows_below_in_its_column": sum(
            1 for r in range(fefe_position[0] + 1, N) if cols[fefe_position[1]][r] in COLORED
        ),
        "nearest_from_bottom_in_its_column": _first_colored(
            cols[fefe_position[1]][::-1]
        )
        == FEFE,
    }

    raster = {
        "top_to_bottom": _raster_value(
            grid[r][c] for r in range(N) for c in range(N)
        ),
        "bottom_to_top": _raster_value(
            grid[r][c] for r in range(N - 1, -1, -1) for c in range(N)
        ),
        "left_to_right": _raster_value(
            grid[r][c] for c in range(N) for r in range(N)
        ),
        "right_to_left": _raster_value(
            grid[r][c] for c in range(N - 1, -1, -1) for r in range(N)
        ),
    }

    matches_spiral = {
        direction: (
            values["text"].replace("F", "") == EXPECTED_COLOR_SEQUENCE
            or values["text"].replace("F", "")[::-1] == EXPECTED_COLOR_SEQUENCE
        )
        for direction, values in raster.items()
    }

    prime_directions = [d for d, v in raster.items() if v["is_prime"]]

    return {
        "border": border,
        "nearest_inward": nearest,
        "fefe": fefe_note,
        "raster": raster,
        "matches_spiral": matches_spiral,
        "prime_directions": prime_directions,
        "prime_hit_rate": f"{len(prime_directions)}/4",
        "posthoc_valid_p_value": False,
    }


def self_test():
    report = audit()

    border = report["border"]
    assert border["top"]["cells"] == "WWKKWBWWKWKKWY"
    assert border["bottom"]["cells"] == "WKBWKKWKKWBWKK"
    assert border["left"]["cells"] == "WKKWWKKBWKKKWW"
    assert border["right"]["cells"] == "YKKKWKWWBKKWWK"
    assert border["top"]["counts"] == {"blue": 1, "yellow": 1, "fefe": 0}
    assert border["bottom"]["counts"] == {"blue": 2, "yellow": 0, "fefe": 0}
    assert border["left"]["counts"] == {"blue": 1, "yellow": 0, "fefe": 0}
    assert border["right"]["counts"] == {"blue": 1, "yellow": 1, "fefe": 0}

    nearest = report["nearest_inward"]
    assert nearest["from_left"] == {"blue": 12, "yellow": 2, "fefe": 0}
    assert nearest["from_right"] == {"blue": 6, "yellow": 8, "fefe": 0}
    assert nearest["from_top"] == {"blue": 9, "yellow": 5, "fefe": 0}
    assert nearest["from_bottom"] == {"blue": 8, "yellow": 5, "fefe": 1}

    fefe = report["fefe"]
    assert (fefe["row0"], fefe["col0"]) == (7, 4)
    assert fefe["rows_below_in_its_column"] == 0
    assert fefe["nearest_from_bottom_in_its_column"] is True

    raster = report["raster"]
    assert raster["top_to_bottom"]["value"] == 12463003
    assert raster["top_to_bottom"]["is_prime"] is False
    assert raster["bottom_to_top"]["value"] == 15395006
    assert raster["bottom_to_top"]["is_prime"] is False
    assert raster["left_to_right"]["value"] == 16763473
    assert raster["left_to_right"]["hex"] == "FFCA51"
    assert raster["left_to_right"]["is_prime"] is True
    assert raster["right_to_left"]["value"] == 4875263
    assert raster["right_to_left"]["is_prime"] is False

    assert not any(report["matches_spiral"].values())
    assert report["prime_directions"] == ["left_to_right"]
    assert report["prime_hit_rate"] == "1/4"
    assert report["posthoc_valid_p_value"] is False

    print("[*] self-test OK: border/nearest/raster readings reproduce; no reading rivals the spiral construction")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return

    report = audit()
    print(f"[*] border readings: {report['border']}")
    print(f"[*] nearest-inward counts: {report['nearest_inward']}")
    print(f"[*] FEFE position/context: {report['fefe']}")
    for direction, values in report["raster"].items():
        print(
            f"[*] raster {direction}: {values['text']} -> "
            f"0x{values['hex']} prime={values['is_prime']}"
        )
    print(f"[*] matches spiral (any direction/reversal): {report['matches_spiral']}")
    print(
        f"[*] prime hit rate across 4 raster directions: {report['prime_hit_rate']} "
        "(descriptive, not a discovery p-value)"
    )
    print(
        "[*] verdict: no border, nearest-inward, or raster reading reproduces "
        "or rivals the spiral construction; retained only as a negative control"
    )


if __name__ == "__main__":
    main()
