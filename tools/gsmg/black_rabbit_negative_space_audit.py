#!/usr/bin/env python3
"""Audit the proposed black rabbit immediately below/right of the white rabbit.

The first audit of this idea incorrectly represented the explicit rabbit by
only its largest connected contour.  That omitted visible disconnected marks
in the white cell below its head/body.  This corrected audit:

* recovers every visible rabbit pixel as the exact difference between the
  source PNG and its mechanically rebuilt 14x14 flat-color grid;
* freezes the proposed adjacent black shape as rows 8-10, columns 8-12
  (1-indexed), the 3x5 block immediately below/right of the visible rabbit;
* searches that complete black/non-black pattern and all eight dihedral
  variants at every valid position in the real 14x14 grid;
* calibrates the family-wise occurrence rate under uniform shuffles that
  preserve the real grid's 86-black/110-non-black multiset.

The shuffle result is descriptive, not a discovery p-value.  The 3x5 region
and its rabbit interpretation were selected after viewing the image.

Corrected 2026-07-28 (Phase 127): the underlying `load_grid` cell classifier
now uses per-cell majority color instead of a single center-pixel sample (a
rabbit-nest cell was previously misread as black because rabbit ink happened
to cross its exact center). The rebuilt flat-color grid changed at that one
cell, so the visible-rabbit-pixel mask dropped from 1,250 to 925 (925 is the
correct count: real ink pixels only, not the true white background that a
wrong flat reconstruction had spuriously flagged as "different"). The
candidate 3x5 pattern itself does not touch that cell, so its shape, its
single occurrence, and the qualitative verdict are all unchanged.
"""

import argparse
import hashlib
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from first_piece_color_reconstruction import BLACK, DEFAULT_IMAGE, N, load_grid

SOURCE_SHA256 = "5e8d84b88f8f829428df5d2a8bf36c7268346f169b799ac7570b6223990d204f"
DEFAULT_OUTPUT = (
    Path(__file__).resolve().parents[2]
    / "doc"
    / "img"
    / "gsmg_rabbit_hint_black_candidate_annotated.png"
)
CELL_SIZE = 25
CANDIDATE_ROWS_0 = slice(7, 10)
CANDIDATE_COLUMNS_0 = slice(7, 12)
DEFAULT_TRIALS = 100_000
DEFAULT_SEED = 20260728


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rebuild_flat_grid(image_path=DEFAULT_IMAGE):
    image = Image.open(image_path).convert("RGB")
    if image.size != (N * CELL_SIZE, N * CELL_SIZE):
        raise ValueError(f"unexpected image geometry: {image.size}")
    grid = load_grid(image_path)
    flat = np.zeros((image.height, image.width, 3), dtype=np.uint8)
    for row in range(N):
        for column in range(N):
            flat[
                row * CELL_SIZE : (row + 1) * CELL_SIZE,
                column * CELL_SIZE : (column + 1) * CELL_SIZE,
            ] = grid[row][column]
    return image, grid, flat


def visible_rabbit_mask(image_path=DEFAULT_IMAGE):
    image, grid, flat = rebuild_flat_grid(image_path)
    pixels = np.asarray(image)
    mask = np.any(pixels != flat, axis=2)
    rows, columns = np.where(mask)
    bbox = (
        int(columns.min()),
        int(rows.min()),
        int(columns.max() + 1),
        int(rows.max() + 1),
    )
    return image, grid, mask, bbox


def candidate_pattern(grid):
    black = np.asarray(
        [[pixel == BLACK for pixel in row] for row in grid], dtype=np.uint8
    )
    return black, black[CANDIDATE_ROWS_0, CANDIDATE_COLUMNS_0].copy()


def dihedral_variants(pattern):
    variants = []
    for turns in range(4):
        rotated = np.rot90(pattern, turns)
        for candidate in (rotated, np.fliplr(rotated)):
            if not any(
                candidate.shape == existing.shape
                and np.array_equal(candidate, existing)
                for existing in variants
            ):
                variants.append(candidate.copy())
    return tuple(variants)


def exact_occurrences(board, variants):
    occurrences = []
    for variant_index, pattern in enumerate(variants):
        height, width = pattern.shape
        windows = np.lib.stride_tricks.sliding_window_view(
            board, (height, width)
        )
        matches = np.argwhere(np.all(windows == pattern, axis=(-1, -2)))
        for row, column in matches:
            occurrences.append(
                {
                    "variant": variant_index,
                    "row_1": int(row + 1),
                    "column_1": int(column + 1),
                    "height": height,
                    "width": width,
                }
            )
    return tuple(occurrences)


def black_subset_occurrences(board, variants):
    occurrences = []
    for variant_index, pattern in enumerate(variants):
        height, width = pattern.shape
        windows = np.lib.stride_tricks.sliding_window_view(
            board, (height, width)
        )
        required_black = pattern.astype(bool)
        matches = np.argwhere(
            np.all(windows[..., required_black] == 1, axis=-1)
        )
        for row, column in matches:
            occurrences.append(
                {
                    "variant": variant_index,
                    "row_1": int(row + 1),
                    "column_1": int(column + 1),
                    "height": height,
                    "width": width,
                }
            )
    return tuple(occurrences)


def shuffled_family_rate(
    variants,
    black_count,
    trials=DEFAULT_TRIALS,
    seed=DEFAULT_SEED,
    batch_size=1_000,
):
    rng = np.random.default_rng(seed)
    hits = 0
    for offset in range(0, trials, batch_size):
        count = min(batch_size, trials - offset)
        ranks = rng.random((count, N * N))
        selected = np.argpartition(ranks, black_count, axis=1)[:, :black_count]
        boards = np.zeros((count, N * N), dtype=np.uint8)
        np.put_along_axis(boards, selected, 1, axis=1)
        boards = boards.reshape(count, N, N)

        matched = np.zeros(count, dtype=bool)
        for pattern in variants:
            height, width = pattern.shape
            windows = np.lib.stride_tricks.sliding_window_view(
                boards, (height, width), axis=(1, 2)
            )
            matched |= np.any(
                np.all(windows == pattern, axis=(-1, -2)), axis=(1, 2)
            )
        hits += int(np.sum(matched))
    return {
        "trials": trials,
        "seed": seed,
        "hits": hits,
        "empirical_p": (hits + 1) / (trials + 1),
    }


def pattern_rows(pattern):
    return tuple(
        "".join("#" if value else "." for value in row) for row in pattern
    )


def save_annotation(image, grid, visible_mask, output_path=DEFAULT_OUTPUT):
    annotated = image.convert("RGBA")
    pixels = np.zeros((image.height, image.width, 4), dtype=np.uint8)

    mask_image = Image.fromarray((visible_mask * 255).astype(np.uint8), "L")
    expanded = np.asarray(mask_image.filter(ImageFilter.MaxFilter(5))) > 0
    cyan_border = expanded & ~visible_mask
    pixels[cyan_border] = (0, 255, 255, 255)

    row_start = CANDIDATE_ROWS_0.start * CELL_SIZE
    row_stop = CANDIDATE_ROWS_0.stop * CELL_SIZE
    column_start = CANDIDATE_COLUMNS_0.start * CELL_SIZE
    column_stop = CANDIDATE_COLUMNS_0.stop * CELL_SIZE
    board, pattern = candidate_pattern(grid)
    for local_row in range(pattern.shape[0]):
        for local_column in range(pattern.shape[1]):
            if not pattern[local_row, local_column]:
                continue
            y0 = row_start + local_row * CELL_SIZE
            x0 = column_start + local_column * CELL_SIZE
            pixels[y0 : y0 + CELL_SIZE, x0 : x0 + CELL_SIZE] = (
                255,
                0,
                255,
                45,
            )

    annotated = Image.alpha_composite(
        annotated, Image.fromarray(pixels, "RGBA")
    )
    draw = ImageDraw.Draw(annotated)
    for local_row in range(pattern.shape[0]):
        for local_column in range(pattern.shape[1]):
            if not board[
                CANDIDATE_ROWS_0.start + local_row,
                CANDIDATE_COLUMNS_0.start + local_column,
            ]:
                continue
            x0 = column_start + local_column * CELL_SIZE
            y0 = row_start + local_row * CELL_SIZE
            draw.rectangle(
                (x0, y0, x0 + CELL_SIZE - 1, y0 + CELL_SIZE - 1),
                outline=(255, 0, 255, 255),
                width=2,
            )
    draw.rectangle(
        (column_start, row_start, column_stop - 1, row_stop - 1),
        outline=(255, 0, 255, 255),
        width=2,
    )
    draw.rectangle((143, 132, 256, 147), fill=(0, 0, 0, 210))
    draw.text((146, 134), "cyan: all visible rabbit pixels", fill=(0, 255, 255, 255))
    draw.rectangle((172, 226, 331, 241), fill=(0, 0, 0, 210))
    draw.text((175, 228), "magenta: adjacent 3x5 candidate", fill=(255, 0, 255, 255))

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    annotated.convert("RGB").resize(
        (image.width * 3, image.height * 3), Image.Resampling.NEAREST
    ).save(output_path)


def audit(
    image_path=DEFAULT_IMAGE,
    output_path=DEFAULT_OUTPUT,
    trials=DEFAULT_TRIALS,
    seed=DEFAULT_SEED,
):
    if file_sha256(image_path) != SOURCE_SHA256:
        raise AssertionError("source rabbit image hash changed")
    image, grid, visible_mask, visible_bbox = visible_rabbit_mask(image_path)
    board, pattern = candidate_pattern(grid)
    variants = dihedral_variants(pattern)
    occurrences = exact_occurrences(board, variants)
    subset_occurrences = black_subset_occurrences(board, variants)
    black_count = int(np.sum(board))
    fixed_probability = (
        math.comb(N * N - pattern.size, black_count - int(np.sum(pattern)))
        / math.comb(N * N, black_count)
    )
    shuffle = shuffled_family_rate(variants, black_count, trials, seed)
    save_annotation(image, grid, visible_mask, output_path)
    return {
        "visible_pixels": int(np.sum(visible_mask)),
        "visible_bbox": visible_bbox,
        "black_count": black_count,
        "pattern": pattern,
        "pattern_rows": pattern_rows(pattern),
        "pattern_black_count": int(np.sum(pattern)),
        "variant_count": len(variants),
        "occurrences": occurrences,
        "subset_occurrences": subset_occurrences,
        "fixed_probability": fixed_probability,
        "shuffle": shuffle,
        "output_path": Path(output_path),
    }


def self_test(
    image_path=DEFAULT_IMAGE,
    output_path=DEFAULT_OUTPUT,
    trials=DEFAULT_TRIALS,
    seed=DEFAULT_SEED,
):
    report = audit(image_path, output_path, trials, seed)
    assert report["visible_pixels"] == 925
    assert report["visible_bbox"] == (160, 150, 230, 215)
    assert report["black_count"] == 86
    assert report["pattern_rows"] == ("...#.", "#####", ".##..")
    assert report["pattern_black_count"] == 8
    assert report["variant_count"] == 8
    assert report["occurrences"] == (
        {
            "variant": 0,
            "row_1": 8,
            "column_1": 8,
            "height": 3,
            "width": 5,
        },
    )
    assert report["subset_occurrences"] == report["occurrences"]
    assert abs(report["fixed_probability"] - 2.4559627356526598e-05) < 1e-18
    assert 0.02 < report["shuffle"]["empirical_p"] < 0.03
    assert report["output_path"].is_file()
    print(
        "[*] self-test OK: 925 visible rabbit pixels retained (corrected -- "
        "see Phase 127); adjacent pattern ...#./#####/.##.. occurs exactly "
        f"once under all 8 dihedral variants; shuffle-family "
        f"p={report['shuffle']['empirical_p']:.6f}"
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

    report = self_test(args.image, args.output, args.trials, args.seed)
    if args.self_test:
        return
    print(f"visible rabbit bbox: {report['visible_bbox']}")
    print(f"visible rabbit pixels: {report['visible_pixels']}")
    print("adjacent 3x5 pattern:", "/".join(report["pattern_rows"]))
    print(
        f"exact real-grid occurrences across {report['variant_count']} "
        f"dihedral variants: {len(report['occurrences'])}"
    )
    print(
        f"fixed-location exact probability: {report['fixed_probability']:.8f}"
    )
    shuffle = report["shuffle"]
    print(
        f"uniform-shuffle family rate: {shuffle['hits']}/{shuffle['trials']}, "
        f"empirical_p={shuffle['empirical_p']:.6f}, seed={shuffle['seed']}"
    )
    print(f"annotated copy: {report['output_path']}")
    print(
        "verdict: the immediately adjacent black cells form a unique, "
        "rabbit-like block pattern and merit retention as a visual lead; "
        "because the region and interpretation were selected after viewing "
        "the image, this is not creator confirmation or a discovery p-value"
    )


if __name__ == "__main__":
    main()
