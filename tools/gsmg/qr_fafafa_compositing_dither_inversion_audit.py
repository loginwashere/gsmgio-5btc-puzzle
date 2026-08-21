#!/usr/bin/env python3
"""Phase 364: bounded compositing and flat-tone dither inversion for QR texture.

Tests three concrete mechanism classes against the complete sixteen-module
exact-#FAFAFA atlas:

1. black-over-white straight-alpha coverage quantized by an N x N binary
   supersampling grid, N=2..32, for all observed light grays;
2. standard recursive Bayer ordered dither matrices 2/4/8/16, all unique
   dihedral transforms, phases, thresholds, and polarities, both in global-eye
   coordinates and with phase reset inside every 7x7 QR module; and
3. constant-tone Floyd-Steinberg/Atkinson error diffusion, raster/serpentine,
   input levels 250.25..254.75 by 0.25, across a fixed 16x16 crop-phase window.

These are standard flat-tone mechanisms, not arbitrary learned 7x7 threshold
matrices. A learned 7x7 matrix would reproduce the already-known module tile by
construction and would not identify a source process.
"""

import argparse
import json
import math
from pathlib import Path

import numpy as np

from qr_fafafa_module_lock_audit import EXPECTED_SHA256, IMAGE_PATH, load_eyes, load_mask, sha256_of, white_ring_modules

REPO_ROOT = Path(__file__).resolve().parents[2]
LIGHT_VALUES = (234, 236, 250, 252, 255)
SUPERSAMPLE_SIDES = tuple(range(2, 33))
BAYER_SIZES = (2, 4, 8, 16)
DIFFUSION_TONES = tuple(float(value) for value in np.arange(250.25, 255.0, 0.25))
DIFFUSION_PHASES = tuple(range(24, 40))
EXPECTED_BAYER = {
    "global": {"mcc": 0.24533661821391375, "exact_bits": 495, "dark_bits": 136,
               "size": 16, "transform": 0, "phase_y": 3, "phase_x": 10,
               "threshold": 209, "polarity": 1},
    "module_reset": {"mcc": 0.46352205678966013, "exact_bits": 557, "dark_bits": 128,
                     "size": 4, "transform": 0, "phase_y": 2, "phase_x": 1,
                     "threshold": 13, "polarity": 1},
}
EXPECTED_DIFFUSION = {
    "mcc": 0.17287854484378679, "exact_bits": 474, "dark_bits": 181,
    "algorithm": "floyd_steinberg", "serpentine": True, "tone": 253.75,
    "phase_y": 25, "phase_x": 25,
}


def target_object():
    mask = load_mask()
    coordinates, truth = [], []
    for my, mx in white_ring_modules():
        for sy in range(7):
            for sx in range(7):
                coordinates.append((my * 7 + sy, mx * 7 + sx, sy, sx))
                truth.append(bool(mask[my * 7 + sy, mx * 7 + sx]))
    return np.asarray(coordinates, dtype=int), np.asarray(truth, dtype=bool)


def confusion(truth, prediction):
    tp = int(np.sum(truth & prediction)); tn = int(np.sum(~truth & ~prediction))
    fp = int(np.sum(~truth & prediction)); fn = int(np.sum(truth & ~prediction))
    denominator = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    return {
        "tp": tp, "tn": tn, "fp": fp, "fn": fn,
        "exact_bits": tp + tn,
        "dark_bits": int(prediction.sum()),
        "mcc": (tp * tn - fp * fn) / denominator if denominator else 0.0,
    }


def alpha_render(levels, denominator):
    rendered, numerators = [], []
    for level in levels:
        numerator = min(
            range(denominator + 1),
            key=lambda value: abs(round(255 * (1 - value / denominator)) - level),
        )
        numerators.append(numerator)
        rendered.append(round(255 * (1 - numerator / denominator)))
    return numerators, rendered


def coverage_grid_audit():
    rows = []
    for side in SUPERSAMPLE_SIDES:
        denominator = side * side
        numerators, rendered = alpha_render(LIGHT_VALUES, denominator)
        errors = [abs(actual - predicted) for actual, predicted in zip(LIGHT_VALUES, rendered)]
        rows.append({
            "side": side, "denominator": denominator,
            "coverage_numerators": numerators, "rendered": rendered,
            "max_error": max(errors), "total_error": sum(errors),
            "exact": not any(errors),
        })
    return {
        "model": "round(255 * (1 - k/N^2)), black over white, binary equal-area samples",
        "observed_levels": LIGHT_VALUES,
        "straight_alpha_8bit_numerators_over_255": [255 - value for value in LIGHT_VALUES],
        "first_exact_square_grid": next(row for row in rows if row["exact"]),
        "smaller_grid_best": min((row for row in rows if row["side"] < 16),
                                 key=lambda row: (row["max_error"], row["total_error"], row["side"])),
        "rows": rows,
    }


def bayer_matrix(size):
    matrix = np.asarray([[0]], dtype=int)
    while len(matrix) < size:
        matrix = np.block([[4 * matrix, 4 * matrix + 2],
                           [4 * matrix + 3, 4 * matrix + 1]])
    return matrix


def unique_transforms(matrix):
    output, seen = [], set()
    for rotation in range(4):
        rotated = np.rot90(matrix, rotation)
        for transformed in (rotated, np.fliplr(rotated)):
            key = transformed.tobytes()
            if key not in seen:
                seen.add(key)
                output.append(transformed)
    return output


def bayer_search(mode):
    coordinates, truth = target_object()
    y = coordinates[:, 0] if mode == "global" else coordinates[:, 2]
    x = coordinates[:, 1] if mode == "global" else coordinates[:, 3]
    best = None
    exact_matches = 0
    candidates = 0
    for size in BAYER_SIZES:
        for transform_index, matrix in enumerate(unique_transforms(bayer_matrix(size))):
            for phase_y in range(size):
                for phase_x in range(size):
                    values = matrix[(y + phase_y) % size, (x + phase_x) % size]
                    for threshold in range(1, size * size):
                        base = values < threshold
                        for polarity in (0, 1):
                            prediction = ~base if polarity else base
                            metrics = confusion(truth, prediction)
                            candidates += 1
                            exact_matches += int(metrics["exact_bits"] == len(truth))
                            row = {
                                **metrics, "size": size, "transform": transform_index,
                                "phase_y": phase_y, "phase_x": phase_x,
                                "threshold": threshold, "polarity": polarity,
                            }
                            if best is None or (row["mcc"], row["exact_bits"]) > (best["mcc"], best["exact_bits"]):
                                best = row
    return {"mode": mode, "candidates": candidates, "exact_matches": exact_matches, "best": best}


def diffuse_constant(tone, algorithm, serpentine, size=112):
    work = np.full((size, size), tone, dtype=float)
    dark = np.zeros((size, size), dtype=bool)
    if algorithm == "floyd_steinberg":
        weights = ((1, 0, 7 / 16), (-1, 1, 3 / 16), (0, 1, 5 / 16), (1, 1, 1 / 16))
    elif algorithm == "atkinson":
        weights = ((1, 0, 1 / 8), (2, 0, 1 / 8), (-1, 1, 1 / 8),
                   (0, 1, 1 / 8), (1, 1, 1 / 8), (0, 2, 1 / 8))
    else:
        raise ValueError(algorithm)
    for y in range(size):
        reverse = serpentine and y % 2 == 1
        xs = range(size - 1, -1, -1) if reverse else range(size)
        for x in xs:
            old = work[y, x]
            is_dark = abs(old - 250.0) <= abs(old - 255.0)
            new = 250.0 if is_dark else 255.0
            dark[y, x] = is_dark
            error = old - new
            for dx, dy, weight in weights:
                if reverse:
                    dx = -dx
                xx, yy = x + dx, y + dy
                if 0 <= xx < size and yy < size:
                    work[yy, xx] += error * weight
    return dark


def diffusion_search():
    coordinates, truth = target_object()
    best = None
    exact_matches = 0
    candidates = 0
    for algorithm in ("floyd_steinberg", "atkinson"):
        for serpentine in (False, True):
            for tone in DIFFUSION_TONES:
                field = diffuse_constant(tone, algorithm, serpentine)
                for phase_y in DIFFUSION_PHASES:
                    for phase_x in DIFFUSION_PHASES:
                        prediction = np.asarray([
                            field[phase_y + y, phase_x + x] for y, x in coordinates[:, :2]
                        ], dtype=bool)
                        metrics = confusion(truth, prediction)
                        candidates += 1
                        exact_matches += int(metrics["exact_bits"] == len(truth))
                        row = {
                            **metrics, "algorithm": algorithm, "serpentine": serpentine,
                            "tone": tone, "phase_y": phase_y, "phase_x": phase_x,
                        }
                        if best is None or (row["mcc"], row["exact_bits"]) > (best["mcc"], best["exact_bits"]):
                            best = row
    return {"candidates": candidates, "exact_matches": exact_matches, "best": best}


def report():
    eye = load_eyes()[0][:, :, 0]
    ring_values = sorted({int(value) for my, mx in white_ring_modules()
                          for value in eye[my * 7:(my + 1) * 7, mx * 7:(mx + 1) * 7].ravel()})
    return {
        "source": str(IMAGE_PATH.relative_to(REPO_ROOT)),
        "source_sha256": sha256_of(IMAGE_PATH),
        "white_ring_grayscale_values": ring_values,
        "coverage_grid": coverage_grid_audit(),
        "bayer": {mode: bayer_search(mode) for mode in ("global", "module_reset")},
        "error_diffusion": diffusion_search(),
        "scope": "standard flat-tone mechanisms only; no learned 7x7 threshold matrix",
    }


def self_test():
    assert sha256_of(IMAGE_PATH) == EXPECTED_SHA256
    coverage = coverage_grid_audit()
    assert coverage["straight_alpha_8bit_numerators_over_255"] == [21, 19, 5, 3, 0]
    assert coverage["first_exact_square_grid"] == {
        "side": 16, "denominator": 256,
        "coverage_numerators": [21, 19, 5, 3, 0],
        "rendered": [234, 236, 250, 252, 255],
        "max_error": 0, "total_error": 0, "exact": True,
    }
    planted = bayer_matrix(4)
    assert planted.tolist() == [[0, 8, 2, 10], [12, 4, 14, 6],
                                [3, 11, 1, 9], [15, 7, 13, 5]]
    bayer = {mode: bayer_search(mode) for mode in ("global", "module_reset")}
    for mode, expected in EXPECTED_BAYER.items():
        assert bayer[mode]["exact_matches"] == 0
        for key, value in expected.items():
            assert math.isclose(bayer[mode]["best"][key], value, abs_tol=1e-12) if isinstance(value, float) else bayer[mode]["best"][key] == value
    diffusion = diffusion_search()
    assert diffusion["exact_matches"] == 0
    for key, value in EXPECTED_DIFFUSION.items():
        assert math.isclose(diffusion["best"][key], value, abs_tol=1e-12) if isinstance(value, float) else diffusion["best"][key] == value
    print("[*] self-test OK: five light levels and 16x16 first exact coverage grid pinned; "
          "Bayer global/module-reset searches and Floyd-Steinberg/Atkinson searches pin zero "
          "exact models and their best low-MCC approximations.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    self_test()
    if args.self_test:
        return
    result = report()
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("[*] coverage first exact:", result["coverage_grid"]["first_exact_square_grid"])
        for mode, row in result["bayer"].items():
            print(f"[*] Bayer {mode}: candidates={row['candidates']} exact={row['exact_matches']} best={row['best']}")
        row = result["error_diffusion"]
        print(f"[*] diffusion: candidates={row['candidates']} exact={row['exact_matches']} best={row['best']}")


if __name__ == "__main__":
    main()
