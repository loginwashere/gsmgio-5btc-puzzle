#!/usr/bin/env python3
"""Audit Denis Golovkin's four-rotation grille observation.

The 24 colored LSB cells are treated as apertures.  This module checks their
90-degree rotation geometry and reads each aperture set in the already-proven
counter-clockwise spiral order used by ``gsmg.io/theseedisplanted``.
"""

from collections import Counter

from first_piece_color_reconstruction import (
    COLOR_NAMES,
    DEFAULT_IMAGE,
    N,
    base_bit,
    is_prime,
    load_grid,
    reconstruct,
    spiral_top_left_counterclockwise,
)


EXPECTED_SPIRAL_WORDS = ("F73D92", "FB410C", "ADAFEF", "2FF081")
EXPECTED_INVERSE_WORDS = ("08C26D", "04BEF3", "525010", "D00F7E")
EXPECTED_INVERSE_VALUES = (574061, 311027, 5394448, 13635454)
EXPECTED_ROW_MAJOR_WORDS = ("BE2B9B", "5861D3", "DBCFBD", "6A81A7")


def rotate_cw(cells):
    """Rotate zero-based 14x14 coordinates clockwise."""
    return {(column, N - 1 - row) for row, column in cells}


def rotate_ccw(cells):
    """Rotate zero-based 14x14 coordinates counter-clockwise."""
    return {(N - 1 - column, row) for row, column in cells}


def rotations(cells, rotate=rotate_cw):
    result = []
    current = set(cells)
    for _ in range(4):
        result.append(current)
        current = rotate(current)
    return tuple(result)


def word_at_cells(grid, cells, order_key):
    bits = "".join(
        str(base_bit(grid[row][column]))
        for row, column in sorted(cells, key=order_key)
    )
    if len(bits) != 24:
        raise AssertionError(f"expected a 24-bit aperture word, got {len(bits)}")
    return bits, int(bits, 2)


def audit(image_path=DEFAULT_IMAGE):
    reconstruction = reconstruct(image_path)
    grid = load_grid(image_path)
    colored = {
        (item["row_0"], item["column_0"])
        for item in reconstruction["objects"]
    }
    aperture_rotations = rotations(colored)
    spiral = spiral_top_left_counterclockwise()
    spiral_index = {coordinate: index for index, coordinate in enumerate(spiral)}

    pairwise_intersections = tuple(
        tuple(len(left & right) for right in aperture_rotations)
        for left in aperture_rotations
    )
    aperture_union = set().union(*aperture_rotations)

    quadrants = Counter((row // 7, column // 7) for row, column in colored)
    palette_by_rotation = tuple(
        Counter(COLOR_NAMES[grid[row][column]] for row, column in cells)
        for cells in aperture_rotations
    )

    spiral_words = []
    inverse_words = []
    inverse_values = []
    inverse_prime_flags = []
    for cells in aperture_rotations:
        _, value = word_at_cells(grid, cells, spiral_index.__getitem__)
        inverse = value ^ 0xFFFFFF
        spiral_words.append(f"{value:06X}")
        inverse_words.append(f"{inverse:06X}")
        inverse_values.append(inverse)
        inverse_prime_flags.append(is_prime(inverse))

    ccw_spiral_words = []
    ccw_inverse_words = []
    for cells in rotations(colored, rotate_ccw):
        _, value = word_at_cells(grid, cells, spiral_index.__getitem__)
        ccw_spiral_words.append(f"{value:06X}")
        ccw_inverse_words.append(f"{value ^ 0xFFFFFF:06X}")

    row_major_words = []
    row_major_prime_flags = []
    row_major_inverse_prime_flags = []
    for cells in aperture_rotations:
        _, value = word_at_cells(grid, cells, lambda coordinate: coordinate)
        inverse = value ^ 0xFFFFFF
        row_major_words.append(f"{value:06X}")
        row_major_prime_flags.append(is_prime(value))
        row_major_inverse_prime_flags.append(is_prime(inverse))

    # Every colored endpoint lies in this simple periodic completion.  It is
    # only one of many possible completions of the remaining rotation orbits.
    periodic_completion = {
        (row, column)
        for row in range(N)
        for column in range(N)
        if (row - column) % 4 == 3
    }
    completion_rotations = rotations(periodic_completion)
    missing = periodic_completion - colored
    missing_palette = Counter(
        COLOR_NAMES[grid[row][column]] for row, column in missing
    )

    return {
        "colored": colored,
        "rotations": aperture_rotations,
        "pairwise_intersections": pairwise_intersections,
        "union_size": len(aperture_union),
        "uncovered_size": N * N - len(aperture_union),
        "quadrants": quadrants,
        "palette_by_rotation": palette_by_rotation,
        "spiral_words": tuple(spiral_words),
        "inverse_words": tuple(inverse_words),
        "inverse_values": tuple(inverse_values),
        "inverse_prime_flags": tuple(inverse_prime_flags),
        "ccw_spiral_words": tuple(ccw_spiral_words),
        "ccw_inverse_words": tuple(ccw_inverse_words),
        "row_major_words": tuple(row_major_words),
        "row_major_prime_flags": tuple(row_major_prime_flags),
        "row_major_inverse_prime_flags": tuple(row_major_inverse_prime_flags),
        "periodic_completion": periodic_completion,
        "completion_rotations": completion_rotations,
        "completion_union_size": len(set().union(*completion_rotations)),
        "missing": missing,
        "missing_palette": missing_palette,
        "colored_spiral_indices": tuple(sorted(spiral_index[cell] for cell in colored)),
        "completion_spiral_indices": tuple(
            sorted(spiral_index[cell] for cell in periodic_completion)
        ),
        "missing_spiral_indices": tuple(sorted(spiral_index[cell] for cell in missing)),
        "possible_full_completions": 4 ** 25,
    }


def self_test():
    result = audit()
    identity = tuple(
        tuple(24 if row == column else 0 for column in range(4))
        for row in range(4)
    )
    assert len(result["colored"]) == 24
    assert result["pairwise_intersections"] == identity
    assert result["union_size"] == 96
    assert result["uncovered_size"] == 100
    assert result["quadrants"] == Counter(
        {(0, 0): 6, (0, 1): 6, (1, 0): 6, (1, 1): 6}
    )
    assert result["spiral_words"] == EXPECTED_SPIRAL_WORDS
    assert result["inverse_words"] == EXPECTED_INVERSE_WORDS
    assert result["inverse_values"] == EXPECTED_INVERSE_VALUES
    assert result["inverse_prime_flags"] == (True, True, False, False)
    assert result["ccw_spiral_words"] == (
        EXPECTED_SPIRAL_WORDS[0],
        EXPECTED_SPIRAL_WORDS[3],
        EXPECTED_SPIRAL_WORDS[2],
        EXPECTED_SPIRAL_WORDS[1],
    )
    assert result["ccw_inverse_words"] == (
        EXPECTED_INVERSE_WORDS[0],
        EXPECTED_INVERSE_WORDS[3],
        EXPECTED_INVERSE_WORDS[2],
        EXPECTED_INVERSE_WORDS[1],
    )
    assert set(result["ccw_spiral_words"]) == set(result["spiral_words"])
    assert set(result["ccw_inverse_words"]) == set(result["inverse_words"])
    assert result["row_major_words"] == EXPECTED_ROW_MAJOR_WORDS
    assert not any(result["row_major_prime_flags"])
    assert not any(result["row_major_inverse_prime_flags"])
    assert len(result["periodic_completion"]) == 49
    assert len(result["missing"]) == 25
    assert result["completion_union_size"] == 196
    assert result["colored_spiral_indices"] == tuple(range(7, 192, 8))
    assert result["completion_spiral_indices"] == tuple(range(3, 196, 4))
    assert result["missing_spiral_indices"] == tuple(range(3, 196, 8))
    assert result["missing_palette"] == Counter(white=18, black=6, fefefe=1)
    assert result["possible_full_completions"] == 1125899906842624


def main():
    self_test()
    result = audit()
    print("colored apertures: 24")
    print("quadrants: 6 / 6 / 6 / 6")
    print(
        "four rotations: pairwise disjoint; "
        f"cover {result['union_size']}/196 cells"
    )
    print("spiral read:")
    for turn, (word, inverse, value, prime) in enumerate(
        zip(
            result["spiral_words"],
            result["inverse_words"],
            result["inverse_values"],
            result["inverse_prime_flags"],
        )
    ):
        print(
            f"  {turn * 90:3d} deg: {word} -> inverse {inverse} "
            f"= {value} (prime={prime})"
        )
    print("row-major control:", " ".join(result["row_major_words"]))
    print("row-major primes (either polarity): 0")
    print(
        "periodic full grille: 49 apertures; "
        "25 missing; four rotations cover 196/196"
    )
    print("arbitrary valid completions of the 24 apertures: 4^25")


if __name__ == "__main__":
    main()
