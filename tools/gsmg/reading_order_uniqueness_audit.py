#!/usr/bin/env python3
"""HISTORICAL PHASE-47 FOLLOW-UP, superseded by Phase 48.

The alternate-order result remains mechanically correct, but the discrepancy
it investigated was created by omitting FEFE from the event stream. It is not
a current transition hypothesis.

Check whether the first-piece grid's character-ordinal ordering is
uniquely determined, or merely one arbitrary convention among several
equally-valid ones.

Phase 47 (FINDINGS.md) found a near-exact match between the first-piece
color sequence (encoded ``B -> b``, ``Y -> be``) and one of Denis Golovkin's
recovered DBBI masks, differing only by an adjacent swap of objects 22/23.
That swap has no creator-authored justification. Before treating it as an
unresolved gap that can only be closed with Denis's missing image, this
checks the one thing that *is* fully under our control: is
``first_piece_color_reconstruction.py``'s counterclockwise-top-left-spiral
convention for mapping object ordinal -> grid pixel actually forced by the
data, or could a different, equally legitimate convention assign colors to
objects 22/23 in the other order?

Pre-registered family: the 8 dihedral symmetries of the square (identity,
rotations by 90/180/270 degrees, and the 4 reflections -- horizontal,
vertical, and both diagonals) applied to the already-validated spiral's
traversal ORDER, plus row-major, column-major, and boustrophedon
(row-zigzag) order as non-spiral alternatives. The dihedral family is the
mathematically complete set of "start from any of the 4 corners, spiral in
either rotational direction" conventions -- an earlier version of this
audit tried to build that family directly as corner/first-move/turn-
direction combinations and only implemented 5 of the 8 (effectively 2 of
the 4 corners), which its own docstring incorrectly described as covering
all 4; that corner-based construction also had a latent bug (a single
forced turn is not always enough to find a valid next cell near a corner,
which the untested corners would have hit). Applying the 8 dihedral
transforms directly to the established spiral's coordinate order sidesteps
both problems and is complete by construction.

A traversal only counts as a candidate if it decodes the full 24-character
target string (`gsmg.io/theseedisplanted`) exactly -- not merely
"printable". Exactly one is expected to pass, which would mean the object
ordinal -> pixel mapping is not a free parameter and the 22/23 discrepancy
cannot be explained by an alternate reading-order convention on our side.
"""
import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from first_piece_color_reconstruction import (  # noqa: E402
    DEFAULT_IMAGE,
    N,
    TARGET,
    base_bit,
    load_grid,
    spiral_top_left_counterclockwise,
)

DIHEDRAL_TRANSFORMS = {
    "identity": lambda row, column: (row, column),
    "rotate_90": lambda row, column: (column, N - 1 - row),
    "rotate_180": lambda row, column: (N - 1 - row, N - 1 - column),
    "rotate_270": lambda row, column: (N - 1 - column, row),
    "flip_horizontal": lambda row, column: (row, N - 1 - column),
    "flip_vertical": lambda row, column: (N - 1 - row, column),
    "transpose": lambda row, column: (column, row),
    "anti_transpose": lambda row, column: (N - 1 - column, N - 1 - row),
}


def _dihedral_spiral(transform):
    base_coordinates = spiral_top_left_counterclockwise()
    coordinates = [transform(row, column) for row, column in base_coordinates]
    if len(set(coordinates)) != N * N:
        raise AssertionError(f"transform did not produce a valid permutation of all {N * N} cells")
    return coordinates


def _row_major():
    return [(row, column) for row in range(N) for column in range(N)]


def _column_major():
    return [(row, column) for column in range(N) for row in range(N)]


def _boustrophedon_rows():
    return [
        (row, column)
        for row in range(N)
        for column in (range(N) if row % 2 == 0 else range(N - 1, -1, -1))
    ]


CANDIDATE_CONVENTIONS = tuple(
    (f"dihedral_{name}", (lambda transform=transform: _dihedral_spiral(transform)))
    for name, transform in DIHEDRAL_TRANSFORMS.items()
) + (
    ("row_major", _row_major),
    ("column_major", _column_major),
    ("boustrophedon_rows", _boustrophedon_rows),
)


def decode_first_24(grid, coordinates):
    bits = "".join(str(base_bit(grid[row][column])) for row, column in coordinates)
    return "".join(
        chr(int(bits[offset : offset + 8], 2)) for offset in range(0, len(TARGET) * 8, 8)
    )


def audit(image_path):
    grid = load_grid(image_path)
    results = []
    coordinate_sets = {}
    for name, build_coordinates in CANDIDATE_CONVENTIONS:
        coordinates = tuple(build_coordinates())
        decoded = decode_first_24(grid, coordinates)
        results.append((name, decoded, decoded == TARGET))
        coordinate_sets.setdefault(coordinates, []).append(name)
    matches = [name for name, _, ok in results if ok]
    unique_paths = len(coordinate_sets)
    matching_unique_paths = {
        coordinates for coordinates, names in coordinate_sets.items()
        if any(name in matches for name in names)
    }
    duplicate_groups = {
        names[0]: names for names in coordinate_sets.values() if len(names) > 1
    }
    return {
        "results": results,
        "matches": matches,
        "unique_paths": unique_paths,
        "matching_unique_paths": len(matching_unique_paths),
        "duplicate_groups": duplicate_groups,
    }


def self_test():
    report = audit(DEFAULT_IMAGE)
    assert not report["duplicate_groups"], (
        f"expected all 8 dihedral transforms plus the 3 non-spiral orders to "
        f"be distinct paths, got duplicates: {report['duplicate_groups']}"
    )
    assert report["unique_paths"] == len(CANDIDATE_CONVENTIONS) == 11
    assert report["matching_unique_paths"] == 1, (
        f"expected exactly 1 of {report['unique_paths']} distinct paths to "
        f"decode the target text, got matches {report['matches']}"
    )
    assert report["matches"] == ["dihedral_identity"], (
        f"unexpected sole match: {report['matches']}"
    )
    print(
        "[*] self-test OK: of the 8 dihedral spiral symmetries plus 3 "
        "non-spiral orders (11 distinct paths total), only the established "
        "identity spiral decodes the known text -- the ordinal->pixel "
        "mapping is not a free parameter"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--image", type=Path, default=DEFAULT_IMAGE)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    print(
        "[!] HISTORICAL PHASE-47 FOLLOW-UP: the ordering result is valid, "
        "but the swap premise is superseded"
    )
    self_test()
    if args.self_test:
        return

    report = audit(args.image)
    print(f"[*] tested {len(CANDIDATE_CONVENTIONS)} pre-registered reading-order conventions "
          f"({report['unique_paths']} distinct paths):")
    for name, decoded, ok in report["results"]:
        marker = "MATCH" if ok else "no match"
        print(f"    {name:20s} {marker:9s} first24={decoded!r}")
    print(f"\n[*] conventions matching the known target text: {report['matches']}")
    print(
        "[*] verdict: the object-ordinal -> pixel mapping is uniquely determined "
        "by the requirement to decode readable text, not a free convention choice. "
        "The Phase 47 object-22/23 discrepancy cannot be explained by an alternate "
        "reading order on our side; it can only be resolved with independent "
        "evidence from Denis's side (his missing guide image)."
    )


if __name__ == "__main__":
    main()
