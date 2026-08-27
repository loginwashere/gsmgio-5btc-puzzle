#!/usr/bin/env python3
"""Test an Ulam-spiral cell numbering against the authenticated first-piece grid.

Predeclared before inspection of any output:

- numbering: classic Ulam spiral (Wikipedia convention) -- value 1 at a
  center cell, first step to the right, turning counterclockwise
  (right, up, left, down), run lengths 1,1,2,2,3,3,... Since the 14x14 grid
  has no single center cell (14 is even), value 1 is fixed at the 0-indexed
  cell (6, 6) -- the assumption flagged to the user before running this, not
  chosen after seeing results.
- checks, all against the same majority-vote grid the verified spiral
  reconstruction uses:
  1. label sanity: every grid cell gets one unique infinite-spiral label;
     labels need not be contiguous in an even-sized crop.
  2. FEFE's Ulam number and its primality (parallel to the established
     corner-spiral fact that FEFE's zero-based spiral index, 163, is prime).
  3. colored-cells-only sequence encountered in increasing-Ulam-number order,
     compared against the authenticated spiral color sequence and its
     reverse (same comparison the raster/border audit used).
  4. full 196-bit stream in increasing-Ulam-number order, first 192 bits
     decoded as ASCII (same framing as the verified construction).
  5. bits at prime-numbered cells only, taken in increasing order, as a
     compact integer -- checked for primality, no other post-hoc framing.

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
    base_bit,
    is_prime,
    load_grid,
)

CENTER = (6, 6)  # 0-indexed; flagged assumption, not tuned after results
COLORED = {BLUE, YELLOW, FEFE}
SYMBOL = {BLUE: "B", YELLOW: "Y", FEFE: "F"}


def ulam_numbering(start_row=CENTER[0], start_col=CENTER[1]):
    """Classic infinite center-out spiral, cropped to the 14x14 grid.

    The Ulam label advances even while the infinite path is outside the
    finite grid. This matters for an even-sized window: with center (6, 6),
    the bottom row receives labels 212..225 rather than being compressed to
    182..196.
    """
    grid = [[None] * N for _ in range(N)]
    directions = [(0, 1), (-1, 0), (0, -1), (1, 0)]  # right, up, left, down
    row, col = start_row, start_col
    grid[row][col] = 1
    number = 1
    assigned = 1
    dir_idx = 0
    step = 1
    while assigned < N * N:
        dr, dc = directions[dir_idx % 4]
        for _ in range(step):
            row += dr
            col += dc
            number += 1
            if 0 <= row < N and 0 <= col < N:
                grid[row][col] = number
                assigned += 1
                if assigned == N * N:
                    break
        dir_idx += 1
        if dir_idx % 2 == 0:
            step += 1
    return grid


def audit(image_path=DEFAULT_IMAGE):
    pixel_grid = load_grid(image_path)
    numbering = ulam_numbering()

    flat_numbers = [numbering[r][c] for r in range(N) for c in range(N)]
    bijection_ok = len(flat_numbers) == len(set(flat_numbers)) == N * N
    labels_contiguous = sorted(flat_numbers) == list(range(1, N * N + 1))

    order = sorted(
        ((numbering[r][c], r, c) for r in range(N) for c in range(N)),
        key=lambda item: item[0],
    )

    fefe_row, fefe_col = next(
        (r, c) for r in range(N) for c in range(N) if pixel_grid[r][c] == FEFE
    )
    fefe_number = numbering[fefe_row][fefe_col]

    colored_sequence = "".join(
        SYMBOL[pixel_grid[r][c]]
        for _, r, c in order
        if pixel_grid[r][c] in COLORED
    )
    matches_established = colored_sequence.replace("F", "") == EXPECTED_COLOR_SEQUENCE
    matches_established_reversed = (
        colored_sequence.replace("F", "")[::-1] == EXPECTED_COLOR_SEQUENCE
    )

    full_bits = "".join(str(base_bit(pixel_grid[r][c])) for _, r, c in order)
    full_value = int(full_bits, 2)
    decoded_ascii = "".join(
        chr(int(full_bits[offset : offset + 8], 2)) for offset in range(0, 192, 8)
    )
    decoded_printable = all(32 <= ord(ch) < 127 for ch in decoded_ascii)

    prime_cells = [(num, r, c) for num, r, c in order if is_prime(num)]
    prime_bits = "".join(str(base_bit(pixel_grid[r][c])) for _, r, c in prime_cells)
    prime_value = int(prime_bits, 2) if prime_bits else None

    return {
        "center": CENTER,
        "bijection_ok": bijection_ok,
        "labels_contiguous": labels_contiguous,
        "maximum_ulam_number": max(flat_numbers),
        "fefe_row0": fefe_row,
        "fefe_col0": fefe_col,
        "fefe_ulam_number": fefe_number,
        "fefe_ulam_number_is_prime": is_prime(fefe_number),
        "colored_sequence": colored_sequence,
        "matches_established": matches_established,
        "matches_established_reversed": matches_established_reversed,
        "full_bits": full_bits,
        "full_value": full_value,
        "full_value_is_prime": is_prime(full_value),
        "decoded_ascii": decoded_ascii,
        "decoded_printable": decoded_printable,
        "prime_cell_count": len(prime_cells),
        "prime_bits": prime_bits,
        "prime_value": prime_value,
        "prime_value_is_prime": is_prime(prime_value) if prime_value is not None else False,
    }


def self_test():
    report = audit()
    assert report["bijection_ok"] is True
    assert report["labels_contiguous"] is False
    assert report["maximum_ulam_number"] == 225
    assert report["center"] == (6, 6)
    assert (report["fefe_row0"], report["fefe_col0"]) == (7, 4)
    assert report["fefe_ulam_number"] == 20
    assert report["fefe_ulam_number_is_prime"] is False
    assert not report["matches_established"]
    assert not report["matches_established_reversed"]
    assert report["decoded_printable"] is False
    assert report["full_value_is_prime"] is False
    assert report["prime_cell_count"] == 43
    assert report["prime_value_is_prime"] is False
    print(
        "[*] self-test OK: Ulam-spiral numbering (center=(6,6), right-first, "
        "CCW) is a valid bijection; no reading rivals the established spiral"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return

    report = audit()
    print(f"[*] center cell (0-indexed): {report['center']}")
    print(f"[*] unique Ulam label per cell: {report['bijection_ok']}")
    print(
        f"[*] labels contiguous 1..196: {report['labels_contiguous']} "
        f"(maximum label={report['maximum_ulam_number']})"
    )
    print(
        f"[*] FEFE cell (row0={report['fefe_row0']}, col0={report['fefe_col0']}) "
        f"Ulam number = {report['fefe_ulam_number']} "
        f"(prime={report['fefe_ulam_number_is_prime']})"
    )
    print(f"[*] colored-cells-only sequence in Ulam order: {report['colored_sequence']}")
    print(
        f"[*] matches established spiral sequence: {report['matches_established']} "
        f"(reversed: {report['matches_established_reversed']})"
    )
    print(
        f"[*] full 196-bit stream (first 192 bits as ASCII): "
        f"{report['decoded_ascii']!r} printable={report['decoded_printable']}"
    )
    print(f"[*] full 196-bit value prime: {report['full_value_is_prime']}")
    print(
        f"[*] {report['prime_cell_count']} prime-numbered cells -> "
        f"integer prime={report['prime_value_is_prime']}"
    )
    print(
        "[*] verdict: Ulam-spiral numbering (this convention) reproduces "
        "nothing comparable to the established counterclockwise-corner spiral"
    )


if __name__ == "__main__":
    main()
