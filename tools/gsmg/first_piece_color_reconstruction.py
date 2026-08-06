#!/usr/bin/env python3
"""Reconstruct the creator-clued yellow/blue numbers in the first puzzle piece."""

import argparse
import csv
import sys
from pathlib import Path

import numpy as np
from PIL import Image

N = 14
TARGET = "gsmg.io/theseedisplanted"
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (63, 72, 204)
YELLOW = (255, 242, 0)
FEFE = (254, 254, 254)
COLOR_NAMES = {
    BLACK: "black",
    WHITE: "white",
    BLUE: "blue",
    YELLOW: "yellow",
    FEFE: "fefefe",
}
EXPECTED_COLOR_SEQUENCE = "BBBBYBBBYYBBBBYBBYYBYYBY"
EXPECTED_ROSE_HEX = "F73D92"
EXPECTED_PRIME = 574061
DEFAULT_IMAGE = (
    Path(__file__).resolve().parents[2] / "doc" / "img" / "gsmg_rabbit_hint.png"
)


def is_prime(value):
    if value < 2:
        return False
    if value % 2 == 0:
        return value == 2
    divisor = 3
    while divisor * divisor <= value:
        if value % divisor == 0:
            return False
        divisor += 2
    return True


def load_grid(path):
    """Classify each cell by its majority pixel color, not a single sample point.

    A single center-pixel sample silently misclassifies a cell whenever the
    overlaid rabbit line-art happens to cross that exact point: cell (row 8,
    column 7, 1-indexed) is 76% white background with a rabbit-ink stroke
    through its center, but center-sampling read it as solid black. Majority
    vote across the whole cell is the only sampling rule immune to that.
    """
    image = Image.open(path).convert("RGB")
    if image.width != image.height or image.width % N:
        raise ValueError(f"expected a square image divisible into {N} cells: {image.size}")
    cell_size = image.width // N
    pixels = np.asarray(image)
    grid = []
    for row in range(N):
        grid_row = []
        for column in range(N):
            block = pixels[
                row * cell_size : (row + 1) * cell_size,
                column * cell_size : (column + 1) * cell_size,
            ]
            colors, counts = np.unique(block.reshape(-1, 3), axis=0, return_counts=True)
            grid_row.append(tuple(int(value) for value in colors[np.argmax(counts)]))
        grid.append(grid_row)
    unknown = sorted({pixel for row in grid for pixel in row} - set(COLOR_NAMES))
    if unknown:
        raise ValueError(f"unexpected sampled grid colors: {unknown}")
    return grid


def spiral_top_left_counterclockwise():
    visited = [[False] * N for _ in range(N)]
    row, column = 0, 0
    delta_row, delta_column = 0, -1
    coordinates = []
    for _ in range(N * N):
        coordinates.append((row, column))
        visited[row][column] = True
        next_row = row + delta_row
        next_column = column + delta_column
        if (
            not (0 <= next_row < N and 0 <= next_column < N)
            or visited[next_row][next_column]
        ):
            delta_row, delta_column = -delta_column, delta_row
            next_row = row + delta_row
            next_column = column + delta_column
        row, column = next_row, next_column
    return coordinates


def base_bit(pixel):
    return 1 if pixel in (BLACK, BLUE) else 0


def reconstruct(path):
    grid = load_grid(path)
    coordinates = spiral_top_left_counterclockwise()
    bits = "".join(str(base_bit(grid[row][column])) for row, column in coordinates)
    decoded = "".join(
        chr(int(bits[offset : offset + 8], 2)) for offset in range(0, 192, 8)
    )
    if decoded != TARGET:
        raise AssertionError(f"spiral decode mismatch: {decoded!r}")

    objects = []
    for character_index in range(len(TARGET)):
        spiral_index = character_index * 8 + 7
        row, column = coordinates[spiral_index]
        pixel = grid[row][column]
        if pixel not in (BLUE, YELLOW):
            raise AssertionError(
                f"character {character_index + 1} LSB is not colored: {pixel}"
            )
        color = "B" if pixel == BLUE else "Y"
        objects.append(
            {
                "ordinal_1": character_index + 1,
                "ordinal_0": character_index,
                "character": TARGET[character_index],
                "ascii": ord(TARGET[character_index]),
                "color": "blue" if color == "B" else "yellow",
                "blue_1_bit": 1 if color == "B" else 0,
                "yellow_1_bit": 1 if color == "Y" else 0,
                "row_1": row + 1,
                "column_1": column + 1,
                "row_0": row,
                "column_0": column,
                "spiral_1": spiral_index + 1,
                "spiral_0": spiral_index,
            }
        )

    color_sequence = "".join(
        "B" if item["color"] == "blue" else "Y" for item in objects
    )
    if color_sequence != EXPECTED_COLOR_SEQUENCE:
        raise AssertionError(f"colored sequence mismatch: {color_sequence}")

    blue_one_bits = "".join(str(item["blue_1_bit"]) for item in objects)
    yellow_one_bits = "".join(str(item["yellow_1_bit"]) for item in objects)
    rose_hex = f"{int(blue_one_bits, 2):06X}"
    prime_value = int(yellow_one_bits, 2)
    if rose_hex != EXPECTED_ROSE_HEX:
        raise AssertionError(f"rose RGB mismatch: {rose_hex}")
    if prime_value != EXPECTED_PRIME or not is_prime(prime_value):
        raise AssertionError(f"complement is not the expected prime: {prime_value}")

    fefe_cells = []
    for row in range(N):
        for column in range(N):
            if grid[row][column] != FEFE:
                continue
            spiral_index = coordinates.index((row, column))
            character_index, bit_index = divmod(spiral_index, 8)
            fefe_cells.append(
                {
                    "row_1": row + 1,
                    "column_1": column + 1,
                    "spiral_0": spiral_index,
                    "spiral_1": spiral_index + 1,
                    "character_0": character_index,
                    "character_1": character_index + 1,
                    "character": TARGET[character_index],
                    "bit_0": bit_index,
                    "bit_1": bit_index + 1,
                    "value": base_bit(FEFE),
                }
            )
    if len(fefe_cells) != 1:
        raise AssertionError(f"expected one FEFE cell, found {len(fefe_cells)}")
    fefe = fefe_cells[0]
    if (len(fefe_cells), fefe["bit_1"], fefe["character_1"]) != (1, 4, 21):
        raise AssertionError(f"FEFE descriptor does not match 1/4/21: {fefe}")
    if fefe["spiral_0"] != 163 or not is_prime(fefe["spiral_0"]):
        raise AssertionError(f"FEFE zero-based spiral index is not prime: {fefe}")
    if fefe["character"] != "n" or fefe["value"] != 0:
        raise AssertionError(f"unexpected FEFE source character/value: {fefe}")

    return {
        "objects": objects,
        "color_sequence": color_sequence,
        "blue_one_bits": blue_one_bits,
        "yellow_one_bits": yellow_one_bits,
        "rose_hex": rose_hex,
        "rose_rgb": tuple(bytes.fromhex(rose_hex)),
        "prime_hex": f"{prime_value:06X}",
        "prime_value": prime_value,
        "blue_count": color_sequence.count("B"),
        "yellow_count": color_sequence.count("Y"),
        "fefe": fefe,
    }


def print_summary(result):
    print(f"source: {TARGET}")
    print(
        f"objects: {len(result['objects'])} "
        f"(blue={result['blue_count']}, yellow={result['yellow_count']})"
    )
    print(f"spiral colors: {result['color_sequence']}")
    print(
        f"blue=1 yellow=0: {result['blue_one_bits']} "
        f"= 0x{result['rose_hex']} = RGB{result['rose_rgb']}"
    )
    print(
        f"yellow=1 blue=0: {result['yellow_one_bits']} "
        f"= 0x{result['prime_hex']} = {result['prime_value']} "
        f"(prime={is_prime(result['prime_value'])})"
    )
    fefe = result["fefe"]
    print(
        "FEFE:",
        f"count/bit/character=1/{fefe['bit_1']}/{fefe['character_1']}",
        f"character={fefe['character']!r}",
        f"value={fefe['value']}",
        f"spiral0={fefe['spiral_0']}",
        f"prime={is_prime(fefe['spiral_0'])}",
    )


def print_table(result, output_format):
    fields = list(result["objects"][0])
    if output_format == "csv":
        writer = csv.DictWriter(sys.stdout, fieldnames=fields)
        writer.writeheader()
        writer.writerows(result["objects"])
        return

    print("| " + " | ".join(fields) + " |")
    print("|" + "|".join("---" for _ in fields) + "|")
    for item in result["objects"]:
        print("| " + " | ".join(str(item[field]) for field in fields) + " |")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, default=DEFAULT_IMAGE)
    parser.add_argument("--table", choices=("markdown", "csv"))
    args = parser.parse_args()

    result = reconstruct(args.image)
    print_summary(result)
    if args.table:
        print()
        print_table(result, args.table)


if __name__ == "__main__":
    main()
