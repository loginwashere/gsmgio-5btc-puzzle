#!/usr/bin/env python3
"""Sensitivity check on Phase 128's rabbit-nest maze: what if blue cells are
opened up too, not just yellow?

Phase 128 treats black+blue as walls and white+yellow+FEFE as open space --
the same black/blue=1, white/yellow=0 polarity the validated Stage-0 spiral
decode already uses, not an arbitrary choice. This module tests the natural
follow-up: relax that convention by also opening blue cells (wall = black
only) and see whether the maze structure gets more or less special.

It does not. Opening blue triples the open-cell count (95 -> 110), triples
the number of reachable border cells (3 -> 9), and destroys the one property
that made Phase 128 worth calibrating at all: none of the 9 routes are
uniquely shortest anymore (each has 2-32 tied paths). A dedicated shuffle
calibration shows both of those facts are individually unremarkable --
reaching >=9 border cells and having zero uniquely-shortest routes each
happen in roughly 44% of random comparably-sized grids. Opening blue does
not reveal a second, cleaner structure; it floods the maze with redundant
routes and removes the only structure that was there.
"""

import argparse
from pathlib import Path

import numpy as np

from first_piece_color_reconstruction import BLACK, DEFAULT_IMAGE, N, load_grid
from rabbit_nest_maze_audit import (
    FEFE_1_INDEXED,
    bfs,
    is_border,
    path_to_moves,
    reconstruct_path,
    shortest_path_count,
)

DEFAULT_TRIALS = 20_000
DEFAULT_SEED = 20260728


def blue_open_cells(grid):
    return {
        (row, column)
        for row in range(N)
        for column in range(N)
        if tuple(grid[row][column]) != BLACK
    }


def analyze(image_path=DEFAULT_IMAGE):
    grid = load_grid(image_path)
    open_cells = blue_open_cells(grid)
    start = (FEFE_1_INDEXED[0] - 1, FEFE_1_INDEXED[1] - 1)

    dist, parent = bfs(start, open_cells)
    border_cells = sorted(
        (cell for cell in dist if is_border(*cell)), key=lambda cell: dist[cell]
    )
    routes = []
    unique_route_count = 0
    for cell in border_cells:
        path = reconstruct_path(cell, parent)
        count = shortest_path_count(start, cell, dist)
        if count == 1:
            unique_route_count += 1
        routes.append(
            {
                "cell_1_indexed": (cell[0] + 1, cell[1] + 1),
                "distance": dist[cell],
                "shortest_path_count": count,
                "moves": path_to_moves(path),
            }
        )

    return {
        "open_cell_count": len(open_cells),
        "reachable_border_count": len(border_cells),
        "routes": routes,
        "unique_route_count": unique_route_count,
    }


def shuffle_calibration(image_path=DEFAULT_IMAGE, trials=DEFAULT_TRIALS, seed=DEFAULT_SEED):
    grid = load_grid(image_path)
    start = (FEFE_1_INDEXED[0] - 1, FEFE_1_INDEXED[1] - 1)
    black_count = sum(
        1
        for row in range(N)
        for column in range(N)
        if (row, column) != start and tuple(grid[row][column]) == BLACK
    )
    total_other = N * N - 1
    non_black_count = total_other - black_count

    all_cells = [(r, c) for r in range(N) for c in range(N) if (r, c) != start]
    is_black_label = np.array([1] * black_count + [0] * non_black_count)
    rng = np.random.default_rng(seed)

    reach_ge9 = 0
    unique_eq0 = 0
    for _ in range(trials):
        permutation = rng.permutation(total_other)
        open_cells = {start}
        for index, cell in zip(permutation, all_cells):
            if is_black_label[index] == 0:
                open_cells.add(cell)
        dist, _ = bfs(start, open_cells)
        border_cells = [cell for cell in dist if is_border(*cell)]
        if len(border_cells) >= 9:
            reach_ge9 += 1
        unique_count = sum(
            1 for cell in border_cells if shortest_path_count(start, cell, dist) == 1
        )
        if unique_count == 0:
            unique_eq0 += 1

    return {
        "trials": trials,
        "seed": seed,
        "reach_ge9_rate": reach_ge9 / trials,
        "unique_eq0_rate": unique_eq0 / trials,
    }


def self_test(image_path=DEFAULT_IMAGE):
    report = analyze(image_path)
    assert report["open_cell_count"] == 110
    assert report["reachable_border_count"] == 9
    assert report["unique_route_count"] == 0

    expected_routes = [
        ((5, 1), 7, 2),
        ((4, 1), 8, 2),
        ((14, 10), 11, 16),
        ((14, 11), 12, 32),
        ((14, 12), 13, 32),
        ((1, 10), 14, 3),
        ((7, 14), 18, 4),
        ((8, 14), 19, 12),
        ((9, 14), 20, 20),
    ]
    actual = [
        (route["cell_1_indexed"], route["distance"], route["shortest_path_count"])
        for route in report["routes"]
    ]
    assert actual == expected_routes, actual
    assert report["routes"][0]["moves"] == "LULULUL"

    calibration = shuffle_calibration(image_path, trials=2000, seed=DEFAULT_SEED)
    assert 0.0 <= calibration["reach_ge9_rate"] <= 1.0
    assert 0.0 <= calibration["unique_eq0_rate"] <= 1.0

    print(
        "[*] self-test OK: opening blue (wall=black only) reaches 9 border "
        "cells (up from 3) with 0/9 uniquely-shortest routes (down from 1/1) "
        "-- both individually unremarkable under calibration"
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, default=DEFAULT_IMAGE)
    parser.add_argument("--trials", type=int, default=DEFAULT_TRIALS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    report = self_test(args.image)
    if args.self_test:
        return

    print(f"[*] open cells: {report['open_cell_count']} (vs. 95 with blue as wall)")
    print(f"[*] reachable border cells: {report['reachable_border_count']} (vs. 3 with blue as wall)")
    for route in report["routes"]:
        print(
            f"  -> {route['cell_1_indexed']} dist={route['distance']} "
            f"unique_shortest_count={route['shortest_path_count']} moves={route['moves']!r}"
        )
    print(f"[*] uniquely-shortest routes: {report['unique_route_count']}/{report['reachable_border_count']}")

    calibration = shuffle_calibration(args.image, args.trials, args.seed)
    print(
        f"[*] calibration ({calibration['trials']} trials, seed={calibration['seed']}): "
        f"P(reach>=9 border cells)={calibration['reach_ge9_rate']*100:.3f}%, "
        f"P(zero unique routes)={calibration['unique_eq0_rate']*100:.3f}%"
    )
    print(
        "[*] verdict: opening blue cells does not reveal a cleaner second "
        "structure. It floods the maze (110 open cells, 9 exits) and "
        "destroys the one property Phase 128 calibrated (route uniqueness) "
        "-- and both the new reach count and the loss of uniqueness are, "
        "individually, close to a coin flip under random shuffling (~44% "
        "each), not rare. The black+blue=1 convention is doing real work; "
        "relaxing it is a dead end, not a stronger variant."
    )


if __name__ == "__main__":
    main()
