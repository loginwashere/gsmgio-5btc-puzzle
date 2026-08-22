#!/usr/bin/env python3
"""Audit the 196-cell yellow/blue mask primality observation."""

import argparse
import math
import random

from sympy import isprime

from first_piece_color_reconstruction import (
    BLUE,
    DEFAULT_IMAGE,
    N,
    YELLOW,
    load_grid,
    spiral_top_left_counterclockwise,
)

EXPECTED_YELLOW_REVERSE_INVERT = (
    100433436204244105573859228564110291168344943733122168512511
)


def mask_bits(grid, color):
    return "".join(
        "1" if grid[row][column] == color else "0"
        for row in range(N)
        for column in range(N)
    )


def variants(bits):
    for reversed_order in (False, True):
        ordered = bits[::-1] if reversed_order else bits
        for inverted in (False, True):
            transformed = (
                "".join("1" if bit == "0" else "0" for bit in ordered)
                if inverted
                else ordered
            )
            yield reversed_order, inverted, int(transformed, 2)


def prime_variants(grid):
    matches = []
    for color_name, color in (("yellow", YELLOW), ("blue", BLUE)):
        for reversed_order, inverted, value in variants(mask_bits(grid, color)):
            if isprime(value):
                matches.append((color_name, reversed_order, inverted, value))
    return matches


def colored_boundary_indices(grid):
    coordinates = spiral_top_left_counterclockwise()
    indices = []
    yellow_positions = []
    for spiral_index in range(7, 192, 8):
        row, column = coordinates[spiral_index]
        color = grid[row][column]
        if color not in (BLUE, YELLOW):
            raise AssertionError("expected every character boundary to be colored")
        row_major_index = row * N + column
        indices.append(row_major_index)
        if color == YELLOW:
            yellow_positions.append(row_major_index)
    return indices, yellow_positions


def grid_from_yellow_positions(boundary_indices, yellow_positions):
    yellow_set = set(yellow_positions)
    boundary_set = set(boundary_indices)
    return [
        [
            (
                YELLOW
                if row * N + column in yellow_set
                else BLUE
                if row * N + column in boundary_set
                else (255, 255, 255)
            )
            for column in range(N)
        ]
        for row in range(N)
    ]


def shuffle_gate(grid, trials, seed):
    boundary_indices, yellow_positions = colored_boundary_indices(grid)
    yellow_count = len(yellow_positions)
    rng = random.Random(seed)
    at_least_as_good = 0
    for _ in range(trials):
        shuffled_yellow = rng.sample(boundary_indices, yellow_count)
        shuffled_grid = grid_from_yellow_positions(
            boundary_indices,
            shuffled_yellow,
        )
        at_least_as_good += bool(prime_variants(shuffled_grid))
    return at_least_as_good, (at_least_as_good + 1) / (trials + 1)


def exact_profile_count():
    return math.comb(24, 9)


def audit(image=DEFAULT_IMAGE, trials=50_000, seed=20260725):
    grid = load_grid(image)
    matches = prime_variants(grid)
    expected = [
        ("yellow", True, True, EXPECTED_YELLOW_REVERSE_INVERT),
    ]
    if matches != expected:
        raise AssertionError(f"unexpected real prime family: {matches}")

    boundary_indices, yellow_positions = colored_boundary_indices(grid)
    if len(boundary_indices) != 24 or len(yellow_positions) != 9:
        raise AssertionError("unexpected colored-cell profile")

    count, empirical_p = shuffle_gate(grid, trials, seed)
    return {
        "matches": matches,
        "boundary_indices": boundary_indices,
        "yellow_positions": yellow_positions,
        "profile_count": exact_profile_count(),
        "trials": trials,
        "seed": seed,
        "at_least_as_good": count,
        "empirical_p": empirical_p,
    }


def self_test():
    report = audit(trials=50_000, seed=20260725)
    assert report["matches"] == [
        ("yellow", True, True, EXPECTED_YELLOW_REVERSE_INVERT)
    ]
    assert len(report["boundary_indices"]) == 24
    assert len(report["yellow_positions"]) == 9
    assert report["profile_count"] == 1_307_504
    assert abs(report["empirical_p"] - 0.060099) < 1e-6
    print(
        "[*] self-test OK: 60-digit yellow/reverse/invert prime reproduced, "
        "24-cell/9-yellow profile confirmed, seed=20260725/50000-trial "
        f"shuffle gate p={report['empirical_p']:.6f}"
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", default=DEFAULT_IMAGE)
    parser.add_argument("--trials", type=int, default=50_000)
    parser.add_argument("--seed", type=int, default=20260725)
    args = parser.parse_args()

    report = audit(args.image, args.trials, args.seed)
    print("real prime variants:")
    for color_name, reversed_order, inverted, value in report["matches"]:
        print(
            f"  color={color_name} reverse={reversed_order} "
            f"invert={inverted} digits={len(str(value))} value={value}"
        )
    print(
        "null profile:",
        f"choose {len(report['yellow_positions'])} yellow positions among "
        f"{len(report['boundary_indices'])} fixed colored boundaries",
        f"({report['profile_count']} possible assignments)",
    )
    print(
        "family-wise shuffle gate:",
        f"seed={report['seed']}",
        f"trials={report['trials']}",
        f"at_least_as_good={report['at_least_as_good']}",
        f"p={report['empirical_p']:.6f}",
    )


if __name__ == "__main__":
    main()
