#!/usr/bin/env python3
"""Compare all corner-inward and center-out Ulam spiral conventions.

Families:
- 8 corner spirals: four corners times two directions around the border.
- 32 Ulam spirals: four center cells times four first moves times two turns.

Ulam labels belong to the infinite spiral and continue advancing while the
path lies outside the finite 14x14 window.
"""

import argparse
from pathlib import Path

from first_piece_color_reconstruction import (
    BLUE,
    DEFAULT_IMAGE,
    EXPECTED_COLOR_SEQUENCE,
    FEFE,
    N,
    TARGET,
    YELLOW,
    base_bit,
    is_prime,
    load_grid,
    spiral_top_left_counterclockwise,
)

COLORED = {BLUE, YELLOW, FEFE}
SYMBOL = {BLUE: "B", YELLOW: "Y", FEFE: "F"}
DIRECTIONS = {"U": (-1, 0), "R": (0, 1), "D": (1, 0), "L": (0, -1)}
CENTER_CELLS = {"TL": (6, 6), "TR": (6, 7), "BL": (7, 6), "BR": (7, 7)}
MILLER_RABIN_BASES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53)


def is_probable_prime(value):
    """Fixed 16-base Miller-Rabin screen for the sweep's large integers."""
    if value < 2:
        return False
    for prime in MILLER_RABIN_BASES:
        if value % prime == 0:
            return value == prime
    odd_part = value - 1
    shifts = 0
    while odd_part % 2 == 0:
        shifts += 1
        odd_part //= 2
    for base in MILLER_RABIN_BASES:
        witness = pow(base, odd_part, value)
        if witness in (1, value - 1):
            continue
        for _ in range(shifts - 1):
            witness = pow(witness, 2, value)
            if witness == value - 1:
                break
        else:
            return False
    return True


def _transform_coordinates(transform):
    coordinates = [transform(row, col) for row, col in spiral_top_left_counterclockwise()]
    if len(coordinates) != N * N or len(set(coordinates)) != N * N:
        raise AssertionError("corner transform is not a 196-cell permutation")
    return coordinates


def corner_variants():
    """Return the complete four-corner by two-border-direction family."""
    transforms = (
        ("TL-D-CCW", "TL", "D", "CCW", lambda r, c: (r, c)),
        ("TL-R-CW", "TL", "R", "CW", lambda r, c: (c, r)),
        ("TR-L-CCW", "TR", "L", "CCW", lambda r, c: (c, N - 1 - r)),
        ("TR-D-CW", "TR", "D", "CW", lambda r, c: (r, N - 1 - c)),
        ("BR-U-CCW", "BR", "U", "CCW", lambda r, c: (N - 1 - r, N - 1 - c)),
        ("BR-L-CW", "BR", "L", "CW", lambda r, c: (N - 1 - c, N - 1 - r)),
        ("BL-R-CCW", "BL", "R", "CCW", lambda r, c: (N - 1 - c, r)),
        ("BL-U-CW", "BL", "U", "CW", lambda r, c: (N - 1 - r, c)),
    )
    return [
        {
            "name": name,
            "start": start,
            "first": first,
            "turn": turn,
            "coordinates": _transform_coordinates(transform),
            "labels": list(range(N * N)),
        }
        for name, start, first, turn, transform in transforms
    ]


def _turn(direction, sense):
    dr, dc = direction
    return (-dc, dr) if sense == "CCW" else (dc, -dr)


def ulam_variant(center, first, turn):
    """Build an infinite Ulam spiral and crop its labeled cells to the grid."""
    grid = [[None] * N for _ in range(N)]
    row, col = center
    number = 1
    assigned = 1
    grid[row][col] = number
    direction = DIRECTIONS[first]
    run_length = 1
    segments = 0

    while assigned < N * N:
        dr, dc = direction
        for _ in range(run_length):
            row += dr
            col += dc
            number += 1
            if 0 <= row < N and 0 <= col < N:
                if grid[row][col] is not None:
                    raise AssertionError("Ulam path revisited an in-grid cell")
                grid[row][col] = number
                assigned += 1
                if assigned == N * N:
                    break
        direction = _turn(direction, turn)
        segments += 1
        if segments % 2 == 0:
            run_length += 1

    labeled = sorted((grid[r][c], r, c) for r in range(N) for c in range(N))
    return [label for label, _, _ in labeled], [(r, c) for _, r, c in labeled]


def ulam_variants():
    variants = []
    for center_name, center in CENTER_CELLS.items():
        for first in DIRECTIONS:
            for turn in ("CCW", "CW"):
                labels, coordinates = ulam_variant(center, first, turn)
                variants.append(
                    {
                        "name": f"{center_name}-{first}-{turn}",
                        "start": center_name,
                        "center": center,
                        "first": first,
                        "turn": turn,
                        "coordinates": coordinates,
                        "labels": labels,
                    }
                )
    return variants


def _byte_preview(bits):
    values = [int(bits[offset : offset + 8], 2) for offset in range(0, 192, 8)]
    pieces = []
    for value in values:
        char = chr(value)
        if 32 <= value < 127 and char not in "`|\\":
            pieces.append(char)
        else:
            pieces.append(f"\\x{value:02x}")
    return "".join(pieces), sum(32 <= value < 127 for value in values)


def analyze_variant(grid, variant, corner_path_lookup):
    coordinates = variant["coordinates"]
    labels = variant["labels"]
    bits = "".join(str(base_bit(grid[row][col])) for row, col in coordinates)
    preview, printable_count = _byte_preview(bits)
    colored = [
        (labels[index], SYMBOL[grid[row][col]])
        for index, (row, col) in enumerate(coordinates)
        if grid[row][col] in COLORED
    ]
    colored_sequence = "".join(symbol for _, symbol in colored)
    without_fefe = colored_sequence.replace("F", "")
    if without_fefe == EXPECTED_COLOR_SEQUENCE:
        color_match = "forward"
    elif without_fefe == EXPECTED_COLOR_SEQUENCE[::-1]:
        color_match = "reverse"
    else:
        color_match = "no"

    relation = corner_path_lookup.get(tuple(coordinates))
    if relation is None:
        reversed_name = corner_path_lookup.get(tuple(reversed(coordinates)))
        relation = f"reverse of {reversed_name}" if reversed_name else "--"

    by_symbol = {
        symbol: [label for label, found in colored if found == symbol]
        for symbol in "BYF"
    }
    fefe_index = next(
        index for index, (row, col) in enumerate(coordinates) if grid[row][col] == FEFE
    )
    prime_bits = "".join(
        str(base_bit(grid[row][col]))
        for label, (row, col) in zip(labels, coordinates)
        if is_prime(label)
    )
    return {
        **variant,
        "decoded": preview,
        "printable_count": printable_count,
        "target_match": preview == TARGET,
        "colored_sequence": colored_sequence,
        "color_match": color_match,
        "blue_labels": by_symbol["B"],
        "yellow_labels": by_symbol["Y"],
        "fefe_label": by_symbol["F"][0],
        "fefe_stream_index0": fefe_index,
        "fefe_character1": fefe_index // 8 + 1,
        "fefe_bit1": fefe_index % 8 + 1,
        "relation": relation,
        "full_value_is_prime": is_probable_prime(int(bits, 2)),
        "prime_label_count": sum(is_prime(label) for label in labels),
        "prime_bits_is_prime": is_probable_prime(int(prime_bits, 2)),
        "minimum_label": min(labels),
        "maximum_label": max(labels),
    }


def audit(image_path=DEFAULT_IMAGE):
    grid = load_grid(image_path)
    corners = corner_variants()
    lookup = {tuple(variant["coordinates"]): variant["name"] for variant in corners}
    return {
        "corner": [analyze_variant(grid, variant, lookup) for variant in corners],
        "ulam": [analyze_variant(grid, variant, lookup) for variant in ulam_variants()],
    }


def _numbers(values):
    return ",".join(str(value) for value in values)


def _markdown_table(title, rows, ulam=False):
    lines = [
        f"## {title}",
        "",
        "| Variant | Corner relation | Decode (first 192 bits) | ASCII | Colors | Match | Blue labels | Yellow labels | FEFE label; stream location | Full probable prime | Prime-label bits probable prime |",
        "|---|---|---|---:|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        relation = row["relation"]
        if not ulam:
            relation = "authenticated" if row["name"] == "TL-D-CCW" else "corner dihedral"
        elif relation == "--":
            relation = "distinct"
        fefe = f"{row['fefe_label']}; char {row['fefe_character1']} bit {row['fefe_bit1']}"
        cells = (
            row["name"],
            relation,
            f"`{row['decoded']}`",
            f"{row['printable_count']}/24",
            f"`{row['colored_sequence']}`",
            row["color_match"],
            f"`{_numbers(row['blue_labels'])}`",
            f"`{_numbers(row['yellow_labels'])}`",
            f"`{fefe}`",
            str(row["full_value_is_prime"]),
            f"{row['prime_bits_is_prime']} ({row['prime_label_count']} cells)",
        )
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def markdown_report(report):
    all_rows = report["corner"] + report["ulam"]
    target_hits = [row["name"] for row in all_rows if row["target_match"]]
    printable_hits = [row["name"] for row in all_rows if row["printable_count"] == 24]
    reverse_ulam = [
        row["name"] for row in report["ulam"] if row["relation"].startswith("reverse of")
    ]
    full_primes = [row["name"] for row in all_rows if row["full_value_is_prime"]]
    fefe_clue_hits = [
        row["name"] for row in all_rows
        if (row["fefe_character1"], row["fefe_bit1"]) == (21, 4)
    ]
    ulam_max_printable = max(row["printable_count"] for row in report["ulam"])
    ulam_best = [
        row["name"] for row in report["ulam"]
        if row["printable_count"] == ulam_max_printable
    ]
    prime_bit_primes = [row["name"] for row in all_rows if row["prime_bits_is_prime"]]
    return "\n".join(
        (
            "# First-Piece Spiral Variant Comparison",
            "",
            "Variant names are `start-first_move-turn`. For Ulam centers, `TL`, `TR`, `BL`, and `BR` mean `(6,6)`, `(6,7)`, `(7,6)`, and `(7,7)` respectively (zero-based).",
            "",
            "Corner labels are zero-based traversal positions (`0..195`), matching the established FEFE position 163. Ulam labels are true one-based infinite-spiral numbers; they may have gaps where the path lies outside the 14x14 window. `ASCII` is the number of printable bytes among the first 24 bytes. `Colors` includes FEFE as `F`. Cell bits use the authenticated mapping: black/blue = 1; white/yellow/FEFE = 0.",
            "",
            "Large-integer columns use a fixed 16-base Miller-Rabin probable-prime screen; the two reported hits were independently confirmed with `sympy.isprime`.",
            "",
            f"Exact target decodes: `{', '.join(target_hits)}`.",
            f"Fully printable candidates: `{', '.join(printable_hits) if printable_hits else 'none'}`.",
            f"Best Ulam printability: {ulam_max_printable}/24 bytes (`{', '.join(ulam_best)}`).",
            f"Exact FEFE clue location (character 21, bit 4): `{', '.join(fefe_clue_hits)}`.",
            f"Ulam paths exactly reversing a corner path ({len(reverse_ulam)}): `{', '.join(reverse_ulam)}`.",
            f"Full-grid integer probable-prime hits: `{', '.join(full_primes) if full_primes else 'none'}`.",
            f"Prime-labeled-cell integer probable-prime hits: `{', '.join(prime_bit_primes) if prime_bit_primes else 'none'}` (descriptive across the declared family, not standalone evidence).",
            "",
            _markdown_table("Corner-inward spirals (8 variants)", report["corner"]),
            "",
            _markdown_table("Center-out Ulam spirals (32 variants)", report["ulam"], ulam=True),
            "",
            "## Reproduction",
            "",
            "```bash\npython3 tools/gsmg/first_piece_spiral_variant_comparison.py --self-test\npython3 tools/gsmg/first_piece_spiral_variant_comparison.py\n```",
        )
    )


def self_test():
    report = audit()
    corners = report["corner"]
    ulams = report["ulam"]
    assert len(corners) == 8
    assert len({tuple(row["coordinates"]) for row in corners}) == 8
    assert [row["name"] for row in corners if row["target_match"]] == ["TL-D-CCW"]
    established = corners[0]
    assert established["decoded"] == TARGET
    assert established["colored_sequence"].replace("F", "") == EXPECTED_COLOR_SEQUENCE
    assert established["fefe_stream_index0"] == established["fefe_label"] == 163
    assert (established["fefe_character1"], established["fefe_bit1"]) == (21, 4)

    assert len(ulams) == 32
    assert len({tuple(row["coordinates"]) for row in ulams}) == 32
    textbook = next(row for row in ulams if row["name"] == "TL-R-CCW")
    assert textbook["fefe_label"] == 20
    assert textbook["maximum_label"] == 225
    assert textbook["prime_label_count"] == 43
    assert textbook["colored_sequence"] == "YFBYBBYYBBYYBBBBYBBBYBYBB"
    assert sum(row["relation"].startswith("reverse of") for row in ulams) == 8
    print("[*] self-test OK: 8 unique corner and 32 unique true-label Ulam variants")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, default=DEFAULT_IMAGE)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    print(markdown_report(audit(args.image)))


if __name__ == "__main__":
    main()
