#!/usr/bin/env python3
"""Treat the first-piece grid's black/blue=1, white/yellow/FEFE=0 partition
as a binary maze (wall/open) and check the "path from rabbit nest to border"
hypothesis: does the FEFE marker cell connect through open space to the edge
of the 14x14 board, and is any single cell load-bearing along the way?

This follows a user-proposed hypothesis (not a creator-authored clue) and a
user-reported result. Every reported fact below was independently
reproduced from the actual puzzle image before being accepted:

* exactly 3 border cells are reachable from FEFE at all;
* the nearest is (1,10) [1-indexed] at distance 14, and it is uniquely
  shortest (exactly one shortest path, verified by dynamic-programming path
  count, not just BFS distance);
* that unique shortest path's move string is exactly ``RRUULUURRRURUU``;
* cell (6,7) [1-indexed] is colored yellow and lies on that path; removing
  it disconnects the FEFE cell from all 3 reachable border cells, not just
  the nearest one.

The shuffle-null calibration is NOT reproduced to the same exactness. A
fixed-FEFE-position, count-preserving reshuffle of the other 195 cells,
scored by the same three-part criterion (unique shortest border route +
a yellow cell on it + that cell a full border cut vertex), lands at 8.2%
over 100,000 trials here -- the same rough order of magnitude as the
originally reported 9.8%, not an exact match. The two figures likely differ
in some unstated methodological choice (e.g. whether FEFE's own position is
held fixed or also reshuffled); neither is precise enough to support a
specific significance claim on its own.
"""

import argparse
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from first_piece_color_reconstruction import (
    BLACK,
    BLUE,
    COLOR_NAMES,
    DEFAULT_IMAGE,
    FEFE,
    N,
    WHITE,
    YELLOW,
    load_grid,
)
from grid_spiral import bitval

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "doc" / "img" / "gsmg_rabbit_nest_maze_audit.png"

FEFE_1_INDEXED = (8, 5)
CELL_SIZE = 60
DEFAULT_TRIALS = 100_000
DEFAULT_SEED = 20260728

MOVE_DELTAS = {"U": (-1, 0), "D": (1, 0), "L": (0, -1), "R": (0, 1)}


def is_border(row, column):
    return row == 0 or row == N - 1 or column == 0 or column == N - 1


def open_and_yellow_sets(grid):
    open_cells = set()
    yellow_cells = set()
    for row in range(N):
        for column in range(N):
            color = tuple(grid[row][column])
            if bitval(color) == 0:
                open_cells.add((row, column))
            if color == YELLOW:
                yellow_cells.add((row, column))
    return open_cells, yellow_cells


def bfs(start, open_cells, blocked=frozenset()):
    dist = {start: 0}
    parent = {start: None}
    queue = deque([start])
    while queue:
        row, column = queue.popleft()
        for dr, dc in MOVE_DELTAS.values():
            nr, nc = row + dr, column + dc
            if (
                0 <= nr < N
                and 0 <= nc < N
                and (nr, nc) in open_cells
                and (nr, nc) not in blocked
                and (nr, nc) not in dist
            ):
                dist[(nr, nc)] = dist[(row, column)] + 1
                parent[(nr, nc)] = (row, column)
                queue.append((nr, nc))
    return dist, parent


def shortest_path_count(start, target, dist):
    order = sorted(dist, key=lambda cell: dist[cell])
    counts = {start: 1}
    for cell in order:
        if cell == start:
            continue
        row, column = cell
        total = 0
        for dr, dc in MOVE_DELTAS.values():
            prev = (row - dr, column - dc)
            if prev in dist and dist[prev] == dist[cell] - 1:
                total += counts.get(prev, 0)
        counts[cell] = total
    return counts.get(target, 0)


def reconstruct_path(target, parent):
    path = []
    cell = target
    while cell is not None:
        path.append(cell)
        cell = parent[cell]
    path.reverse()
    return path


def path_to_moves(path):
    moves = []
    for (r0, c0), (r1, c1) in zip(path, path[1:]):
        dr, dc = r1 - r0, c1 - c0
        for move, (mdr, mdc) in MOVE_DELTAS.items():
            if (dr, dc) == (mdr, mdc):
                moves.append(move)
                break
    return "".join(moves)


def analyze(image_path=DEFAULT_IMAGE):
    grid = load_grid(image_path)
    open_cells, yellow_cells = open_and_yellow_sets(grid)
    start = (FEFE_1_INDEXED[0] - 1, FEFE_1_INDEXED[1] - 1)
    assert tuple(grid[start[0]][start[1]]) == FEFE

    dist, parent = bfs(start, open_cells)
    border_cells = sorted(
        (cell for cell in dist if is_border(*cell)), key=lambda cell: dist[cell]
    )
    routes = []
    for cell in border_cells:
        path = reconstruct_path(cell, parent)
        routes.append(
            {
                "cell_1_indexed": (cell[0] + 1, cell[1] + 1),
                "distance": dist[cell],
                "path": path,
                "moves": path_to_moves(path),
            }
        )

    nearest = routes[0]
    unique_count = shortest_path_count(start, border_cells[0], dist)
    nearest["shortest_path_count"] = unique_count

    yellow_gateway = next(
        (cell for cell in nearest["path"] if cell in yellow_cells), None
    )
    gateway_cuts_all_borders = False
    if yellow_gateway is not None:
        blocked_dist, _ = bfs(start, open_cells, blocked={yellow_gateway})
        still_reachable = [cell for cell in border_cells if cell in blocked_dist]
        gateway_cuts_all_borders = len(still_reachable) == 0

    return {
        "start": start,
        "reachable_border_count": len(border_cells),
        "routes": routes,
        "unique_shortest": unique_count == 1,
        "yellow_gateway_1_indexed": (
            (yellow_gateway[0] + 1, yellow_gateway[1] + 1)
            if yellow_gateway is not None
            else None
        ),
        "yellow_gateway_cuts_all_borders": gateway_cuts_all_borders,
    }


def shuffle_calibration(image_path=DEFAULT_IMAGE, trials=DEFAULT_TRIALS, seed=DEFAULT_SEED):
    grid = load_grid(image_path)
    start = (FEFE_1_INDEXED[0] - 1, FEFE_1_INDEXED[1] - 1)
    counts = {"black": 0, "white": 0, "blue": 0, "yellow": 0}
    name_by_color = {BLACK: "black", WHITE: "white", BLUE: "blue", YELLOW: "yellow"}
    for row in range(N):
        for column in range(N):
            color = tuple(grid[row][column])
            if (row, column) == start:
                continue
            counts[name_by_color[color]] += 1

    all_cells = [(r, c) for r in range(N) for c in range(N) if (r, c) != start]
    is_wall = np.array(
        [1] * counts["black"] + [0] * counts["white"] + [1] * counts["blue"] + [0] * counts["yellow"]
    )
    is_yellow = np.array(
        [0] * counts["black"] + [0] * counts["white"] + [0] * counts["blue"] + [1] * counts["yellow"]
    )
    rng = np.random.default_rng(seed)

    hits = 0
    for _ in range(trials):
        permutation = rng.permutation(len(all_cells))
        open_cells = {start}
        yellow_cells = set()
        for index, cell in zip(permutation, all_cells):
            if is_wall[index] == 0:
                open_cells.add(cell)
            if is_yellow[index] == 1:
                yellow_cells.add(cell)

        dist, parent = bfs(start, open_cells)
        border_cells = [cell for cell in dist if is_border(*cell)]
        if not border_cells:
            continue
        min_dist = min(dist[cell] for cell in border_cells)
        nearest = [cell for cell in border_cells if dist[cell] == min_dist]
        if len(nearest) != 1:
            continue
        target = nearest[0]
        if shortest_path_count(start, target, dist) != 1:
            continue
        path = reconstruct_path(target, parent)
        gateway = next((cell for cell in path if cell in yellow_cells), None)
        if gateway is None:
            continue
        blocked_dist, _ = bfs(start, open_cells, blocked={gateway})
        if any(cell in blocked_dist for cell in border_cells):
            continue
        hits += 1

    return {"trials": trials, "seed": seed, "hits": hits, "empirical_rate": hits / trials}


def save_annotation(image_path=DEFAULT_IMAGE, report=None, output_path=DEFAULT_OUTPUT):
    grid = load_grid(image_path)
    canvas = Image.new("RGB", (N * CELL_SIZE, N * CELL_SIZE), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    for row in range(N):
        for column in range(N):
            color = tuple(grid[row][column])
            x0, y0 = column * CELL_SIZE, row * CELL_SIZE
            draw.rectangle((x0, y0, x0 + CELL_SIZE - 1, y0 + CELL_SIZE - 1), fill=color)
    for i in range(N + 1):
        draw.line((0, i * CELL_SIZE, N * CELL_SIZE, i * CELL_SIZE), fill=(120, 120, 120))
        draw.line((i * CELL_SIZE, 0, i * CELL_SIZE, N * CELL_SIZE), fill=(120, 120, 120))

    def center(cell):
        row, column = cell
        return (column * CELL_SIZE + CELL_SIZE // 2, row * CELL_SIZE + CELL_SIZE // 2)

    route_colors = [(0, 200, 0), (255, 140, 0), (0, 160, 255)]
    for route, color in zip(report["routes"], route_colors):
        points = [center(cell) for cell in route["path"]]
        draw.line(points, fill=color, width=4)

    gateway_1idx = report["yellow_gateway_1_indexed"]
    if gateway_1idx is not None:
        gr, gc = gateway_1idx[0] - 1, gateway_1idx[1] - 1
        x0, y0 = gc * CELL_SIZE, gr * CELL_SIZE
        draw.rectangle(
            (x0 + 3, y0 + 3, x0 + CELL_SIZE - 4, y0 + CELL_SIZE - 4),
            outline=(255, 0, 255),
            width=4,
        )

    start_row, start_column = report["start"]
    x0, y0 = start_column * CELL_SIZE, start_row * CELL_SIZE
    draw.rectangle((x0 + 3, y0 + 3, x0 + CELL_SIZE - 4, y0 + CELL_SIZE - 4), outline=(255, 0, 0), width=4)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.resize((canvas.width * 2, canvas.height * 2), Image.Resampling.NEAREST).save(output_path)
    return output_path


def self_test(image_path=DEFAULT_IMAGE, output_path=DEFAULT_OUTPUT):
    report = analyze(image_path)
    assert report["reachable_border_count"] == 3
    routes = report["routes"]
    assert routes[0]["cell_1_indexed"] == (1, 10)
    assert routes[0]["distance"] == 14
    assert routes[0]["moves"] == "RRUULUURRRURUU"
    assert routes[0]["shortest_path_count"] == 1
    assert report["unique_shortest"] is True
    assert routes[1]["cell_1_indexed"] == (7, 14)
    assert routes[1]["distance"] == 18
    assert routes[2]["cell_1_indexed"] == (8, 14)
    assert routes[2]["distance"] == 19
    assert report["yellow_gateway_1_indexed"] == (6, 7)
    assert report["yellow_gateway_cuts_all_borders"] is True

    output = save_annotation(image_path, report, output_path)
    assert output.is_file()

    calibration = shuffle_calibration(image_path, trials=2000, seed=DEFAULT_SEED)
    assert 0.0 <= calibration["empirical_rate"] <= 1.0

    print(
        "[*] self-test OK: FEFE reaches exactly 3 border cells; unique 14-move "
        "shortest route RRUULUURRRURUU to (1,10); yellow cell (6,7) is a "
        "mandatory gateway cutting off all 3 border cells when removed"
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, default=DEFAULT_IMAGE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--trials", type=int, default=DEFAULT_TRIALS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    report = self_test(args.image, args.output)
    if args.self_test:
        return

    print(f"[*] reachable border cells: {report['reachable_border_count']}")
    for index, route in enumerate(report["routes"]):
        print(
            f"  route {index}: -> {route['cell_1_indexed']} (1-indexed), "
            f"distance={route['distance']}, moves={route['moves']!r}"
        )
    print(f"[*] unique shortest route: {report['unique_shortest']}")
    print(f"[*] yellow gateway: {report['yellow_gateway_1_indexed']} (1-indexed)")
    print(f"[*] gateway cuts off all border cells when removed: {report['yellow_gateway_cuts_all_borders']}")
    print(f"[*] annotated maze: {report['start']}")

    calibration = shuffle_calibration(args.image, args.trials, args.seed)
    print(
        f"[*] shuffle calibration: {calibration['hits']}/{calibration['trials']} = "
        f"{calibration['empirical_rate']*100:.3f}% (seed={calibration['seed']})"
    )
    print(
        "[*] verdict: the maze structure and mandatory yellow gateway are real, "
        "exact facts about this grid, not approximations. But a comparable "
        "random grid reproduces the same qualitative property roughly 1 time "
        "in 10-12 by this script's own calibration, and the route's move "
        "string is not language. This is a legitimate bounded lead, not a "
        "solved 'extra door' -- it does not license expanding into arbitrary "
        "path encodings or a new cipher/password sweep without further "
        "creator-backed evidence."
    )


if __name__ == "__main__":
    main()
