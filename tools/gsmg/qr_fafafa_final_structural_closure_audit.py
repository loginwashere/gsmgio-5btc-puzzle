#!/usr/bin/env python3
"""Phase 365: final bounded structural closure of the QR #FAFAFA branch.

Executes the three remaining local, geometry-selected analyses from the
full-mask brainstorm:

* unroll all seven subpixel-depth tracks around the sixteen-module white ring;
* compare the complete 49x49 mask with every non-identity square symmetry;
* measure the exact seven-pixel Fourier lattice against matched shuffles and
  repeated-tile controls.

The fixed clockwise ring starts at module (1,1).  Top and bottom modules are
read horizontally; the three non-corner modules on each side are read
vertically.  Every track therefore contains 16*7=112 bits.  No depth is chosen
after viewing output.  Controls shuffle pixels independently within each real
7x7 module, preserving all sixteen exact #FAFAFA counts and the QR geometry.
"""

import argparse
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from qr_fafafa_module_lock_audit import (
    EXPECTED_SHA256,
    IMAGE_PATH,
    fit_tile,
    load_mask,
    module_patch,
    sha256_of,
    white_ring_modules,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_IMAGE = REPO_ROOT / "doc" / "img" / "gsmg_qr_fafafa_phase365_final_closure.png"
NULL_TRIALS = 500
NULL_SEED = 20260821 + 365

RING_MODULES = (
    *((1, mx) for mx in range(1, 6)),
    *((my, 5) for my in range(2, 5)),
    *((5, mx) for mx in range(5, 0, -1)),
    *((my, 1) for my in range(4, 1, -1)),
)

TRANSFORMS = {
    "horizontal_flip": lambda array: array[:, ::-1],
    "vertical_flip": lambda array: array[::-1, :],
    "rotation_180": lambda array: array[::-1, ::-1],
    "transpose": lambda array: array.T,
    "anti_transpose": lambda array: np.fliplr(np.flipud(array)).T,
    "rotation_90": lambda array: np.rot90(array, 1),
    "rotation_270": lambda array: np.rot90(array, 3),
}

EXPECTED_TRACK_COUNTS = [19, 87, 43, 30, 43, 96, 27]
EXPECTED_TRACK_MAJORITY_DISTANCES = [18, 56, 20, 7, 24, 59, 10]
EXPECTED_MAJORITY_HEX = "048912244c993264891224099326"
# The 112-bit majority stream is 16 modules x 7 depth bits, not 14 arbitrary
# bytes: an 8-bit split crosses module boundaries. This is the module-aligned
# regrouping (one 7-bit value per RING_MODULES position).
EXPECTED_MODULE_MAJORITY_VALUES = [2, 34, 34, 34, 34, 50, 50, 50, 50, 34, 34, 34, 32, 38, 38, 38]
EXPECTED_SYMMETRY_RESIDUALS = {
    "horizontal_flip": 78,
    "vertical_flip": 208,
    "rotation_180": 238,
    "transpose": 206,
    "anti_transpose": 254,
    "rotation_90": 230,
    "rotation_270": 230,
}
EXPECTED_LATTICE_POWER = 0.1880307900524446
EXPECTED_AXIAL_POWER = 0.15087971578413129
EXPECTED_TRACK_NULL_MEANS = {
    "pairwise_agreement_mean": 0.5022551020408164,
    "pairwise_agreement_max": 0.5909642857142858,
    "unanimous_positions": 1.824,
    "minimum_majority_distance": 31.328,
}
EXPECTED_SPECTRAL_NULL_MEANS = {
    "seven_pixel_lattice_power_fraction": 0.013135081486494109,
    "seven_pixel_axial_power_fraction": 0.0032048609936277,
    "strongest_peak_power_fraction": 0.03381089223909547,
}


def shuffled_modules(mask, rng):
    output = mask.copy()
    for module in white_ring_modules():
        patch = module_patch(output, module)
        values = patch.ravel().copy()
        rng.shuffle(values)
        patch[:] = values.reshape(7, 7)
    return output


def ring_tracks(mask):
    tracks = []
    for depth in range(7):
        values = []
        for my, mx in RING_MODULES:
            patch = module_patch(mask, (my, mx))
            if my == 1:
                segment = patch[depth, :]
            elif mx == 5:
                segment = patch[:, 6 - depth]
            elif my == 5:
                segment = patch[6 - depth, ::-1]
            else:
                segment = patch[::-1, depth]
            values.extend(bool(value) for value in segment)
        tracks.append(values)
    return np.asarray(tracks, dtype=bool)


def bits_to_bytes(bits):
    assert len(bits) % 8 == 0
    return bytes(
        sum(int(value) << (7 - offset)
            for offset, value in enumerate(bits[index:index + 8]))
        for index in range(0, len(bits), 8)
    )


def module_majority_values(majority):
    assert len(majority) == 112
    return [
        int("".join("1" if value else "0" for value in majority[index * 7:index * 7 + 7]), 2)
        for index in range(16)
    ]


def module_majority_roles():
    # RING_MODULES order: 5 top (incl. both top corners), 3 right (non-corner),
    # 5 bottom reversed (incl. both bottom corners), 3 left (non-corner). A
    # corner's 7-bit value can coincide with its adjacent run by chance; label
    # each position by its actual (row, col) role rather than by value.
    roles = []
    for index, (my, mx) in enumerate(RING_MODULES):
        is_corner = (my, mx) in {(1, 1), (1, 5), (5, 5), (5, 1)}
        roles.append(f"{'corner' if is_corner else 'edge'}({my},{mx})")
    return roles


def track_statistics(tracks):
    majority = np.sum(tracks, axis=0) >= 4
    pairwise = [float(np.mean(tracks[left] == tracks[right]))
                for left in range(7) for right in range(left)]
    unanimous = (np.sum(tracks, axis=0) == 0) | (np.sum(tracks, axis=0) == 7)
    return {
        "shape": list(tracks.shape),
        "one_counts": [int(track.sum()) for track in tracks],
        "pairwise_agreement_mean": float(np.mean(pairwise)),
        "pairwise_agreement_max": float(np.max(pairwise)),
        "unanimous_positions": int(unanimous.sum()),
        "majority_distances": [int(np.sum(track != majority)) for track in tracks],
        "majority_bits": "".join("1" if value else "0" for value in majority),
        "majority_hex": bits_to_bytes(majority).hex(),
        "majority_module_values": module_majority_values(majority),
        "majority_module_roles": module_majority_roles(),
        "track_hex": [bits_to_bytes(track).hex() for track in tracks],
        "printable_ascii_tracks": [
            bits_to_bytes(track).decode("ascii")
            if all(32 <= value <= 126 for value in bits_to_bytes(track)) else None
            for track in tracks
        ],
    }


def track_calibration(mask, trials=NULL_TRIALS):
    real = track_statistics(ring_tracks(mask))
    rng = np.random.default_rng(NULL_SEED)
    controls = []
    for _ in range(trials):
        controls.append(track_statistics(ring_tracks(shuffled_modules(mask, rng))))

    def high_tail(key):
        values = np.asarray([row[key] for row in controls], dtype=float)
        observed = float(real[key])
        return {
            "real": observed,
            "null_mean": float(values.mean()),
            "null_min": float(values.min()),
            "null_max": float(values.max()),
            "p_ge_real": float((1 + np.sum(values >= observed)) / (trials + 1)),
        }

    minimum_distances = np.asarray([min(row["majority_distances"]) for row in controls])
    observed_minimum = min(real["majority_distances"])
    return {
        "geometry": "16 clockwise modules x 7 tangent pixels at every one of 7 depths",
        "start": "top-left white-ring module (1,1), top edge left-to-right",
        "real": real,
        "null_trials": trials,
        "null_seed": NULL_SEED,
        "null": {
            "pairwise_agreement_mean": high_tail("pairwise_agreement_mean"),
            "pairwise_agreement_max": high_tail("pairwise_agreement_max"),
            "unanimous_positions": high_tail("unanimous_positions"),
            "minimum_majority_distance": {
                "real": observed_minimum,
                "null_mean": float(minimum_distances.mean()),
                "null_min": int(minimum_distances.min()),
                "null_max": int(minimum_distances.max()),
                "p_le_real": float((1 + np.sum(minimum_distances <= observed_minimum)) /
                                   (trials + 1)),
            },
        },
    }


def connected_components(mask):
    seen = np.zeros(mask.shape, dtype=bool)
    components = []
    for start_y, start_x in zip(*np.where(mask)):
        if seen[start_y, start_x]:
            continue
        stack = [(int(start_y), int(start_x))]
        seen[start_y, start_x] = True
        coordinates = []
        while stack:
            y, x = stack.pop()
            coordinates.append((y, x))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                yy, xx = y + dy, x + dx
                if (0 <= yy < mask.shape[0] and 0 <= xx < mask.shape[1]
                        and mask[yy, xx] and not seen[yy, xx]):
                    seen[yy, xx] = True
                    stack.append((yy, xx))
        components.append(coordinates)
    return components


def symmetry_statistics(mask):
    rows = {}
    for name, transform in TRANSFORMS.items():
        residual = mask ^ transform(mask)
        components = connected_components(residual)
        sizes = sorted((len(component) for component in components), reverse=True)
        rows[name] = {
            "residual_pixels": int(residual.sum()),
            "agreement": float(np.mean(mask == transform(mask))),
            "components_4_neighbor": len(components),
            "largest_component": sizes[0] if sizes else 0,
            "active_rows": int(np.sum(np.any(residual, axis=1))),
            "active_columns": int(np.sum(np.any(residual, axis=0))),
        }
    return rows


def symmetry_calibration(mask, trials=NULL_TRIALS):
    real = symmetry_statistics(mask)
    real_sorted = sorted(row["residual_pixels"] for row in real.values())
    rng = np.random.default_rng(NULL_SEED + 1)
    controls = []
    for _ in range(trials):
        rows = symmetry_statistics(shuffled_modules(mask, rng))
        controls.append(sorted(row["residual_pixels"] for row in rows.values()))
    controls = np.asarray(controls)
    ranks = []
    for index, observed in enumerate(real_sorted):
        values = controls[:, index]
        ranks.append({
            "rank": index + 1,
            "real_residual_pixels": observed,
            "null_mean": float(values.mean()),
            "null_min": int(values.min()),
            "null_max": int(values.max()),
            "p_le_real": float((1 + np.sum(values <= observed)) / (trials + 1)),
        })
    return {
        "real": real,
        "ordered_residual_calibration": ranks,
        "interpretation_limit": "compact residuals establish symmetry, not glyphs or text",
    }


def spectral_statistics(mask):
    centered = mask.astype(float) - float(np.mean(mask))
    power = np.abs(np.fft.fftshift(np.fft.fft2(centered))) ** 2
    center = mask.shape[0] // 2
    power[center, center] = 0.0
    total = float(power.sum())
    yy, xx = np.indices(mask.shape)
    ky, kx = yy - center, xx - center
    lattice = ((kx % 7 == 0) & (ky % 7 == 0)
               & ~((kx == 0) & (ky == 0)))
    axial = ((((kx == 0) & (ky % 7 == 0))
              | ((ky == 0) & (kx % 7 == 0)))
             & ~((kx == 0) & (ky == 0)))
    peak_indices = np.argsort(power.ravel())[::-1][:12]
    peaks = [
        {
            "ky": int(ky.ravel()[index]),
            "kx": int(kx.ravel()[index]),
            "power_fraction": float(power.ravel()[index] / total),
        }
        for index in peak_indices
    ]
    return {
        "seven_pixel_lattice_power_fraction": float(power[lattice].sum() / total),
        "seven_pixel_axial_power_fraction": float(power[axial].sum() / total),
        "strongest_peak_power_fraction": float(power.max() / total),
        "strongest_peaks": peaks,
    }


def repeated_tile_mask(tile):
    output = np.zeros((49, 49), dtype=bool)
    for module in white_ring_modules():
        module_patch(output, module)[:] = tile
    return output


def spectral_calibration(mask, trials=NULL_TRIALS):
    real = spectral_statistics(mask)
    rng = np.random.default_rng(NULL_SEED + 2)
    shuffles = []
    for _ in range(trials):
        shuffles.append(spectral_statistics(shuffled_modules(mask, rng)))

    shared_tile = fit_tile(mask, white_ring_modules())
    shared = spectral_statistics(repeated_tile_mask(shared_tile))
    repeated_random = []
    for _ in range(trials):
        flat = np.zeros(49, dtype=bool)
        flat[rng.choice(49, int(shared_tile.sum()), replace=False)] = True
        repeated_random.append(spectral_statistics(repeated_tile_mask(flat.reshape(7, 7))))

    def summary(key, controls, tail="high"):
        values = np.asarray([row[key] for row in controls])
        observed = real[key]
        result = {
            "real": observed,
            "null_mean": float(values.mean()),
            "null_min": float(values.min()),
            "null_max": float(values.max()),
        }
        if tail == "high":
            result["p_ge_real"] = float((1 + np.sum(values >= observed)) / (len(values) + 1))
        return result

    return {
        "real": real,
        "module_count_preserving_shuffle": {
            key: summary(key, shuffles)
            for key in ("seven_pixel_lattice_power_fraction",
                        "seven_pixel_axial_power_fraction",
                        "strongest_peak_power_fraction")
        },
        "shared_real_majority_tile": shared,
        "random_repeated_23_of_49_tile": {
            key: summary(key, repeated_random)
            for key in ("seven_pixel_lattice_power_fraction",
                        "seven_pixel_axial_power_fraction")
        },
        "interpretation_limit": (
            "a repeated 7x7 tile generically produces equal or greater lattice power; "
            "the spectrum confirms module locking but does not select a decoder"
        ),
    }


def render(path=OUTPUT_IMAGE):
    mask = load_mask()
    tracks = ring_tracks(mask)
    majority = np.sum(tracks, axis=0) >= 4
    residuals = {
        name: mask ^ transform(mask)
        for name, transform in list(TRANSFORMS.items())[:3]
    }

    scale = 7
    panel = 49 * scale
    margin, gap, title_height = 24, 28, 38
    width = margin * 2 + panel * 4 + gap * 3
    track_height = 8 * 18
    height = margin * 2 + title_height + panel + 50 + track_height
    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    views = [("Exact #FAFAFA mask", mask)] + [
        (name.replace("_", " "), residual) for name, residual in residuals.items()
    ]
    for index, (title, view) in enumerate(views):
        x = margin + index * (panel + gap)
        y = margin + title_height
        image = Image.fromarray(np.where(view, 0, 255).astype(np.uint8), "L")
        canvas.paste(image.resize((panel, panel), Image.Resampling.NEAREST).convert("RGB"), (x, y))
        draw.text((x, margin + 12), title, fill="black", font=font)

    y0 = margin + title_height + panel + 42
    draw.text((margin, y0 - 24), "Seven clockwise depth tracks; M = fixed majority", fill="black", font=font)
    for row_index, values in enumerate(list(tracks) + [majority]):
        label = f"{row_index}" if row_index < 7 else "M"
        draw.text((margin, y0 + row_index * 18 + 3), label, fill="black", font=font)
        x0 = margin + 22
        for bit_index, value in enumerate(values):
            color = (25, 25, 25) if value else (238, 238, 238)
            draw.rectangle((x0 + bit_index * 8, y0 + row_index * 18,
                            x0 + bit_index * 8 + 6, y0 + row_index * 18 + 12), fill=color)
            if bit_index % 7 == 0:
                draw.line((x0 + bit_index * 8 - 1, y0 + row_index * 18,
                           x0 + bit_index * 8 - 1, y0 + row_index * 18 + 12), fill=(200, 60, 60))
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path)
    return path


def report(trials=NULL_TRIALS):
    mask = load_mask()
    return {
        "source": str(IMAGE_PATH.relative_to(REPO_ROOT)),
        "source_sha256": sha256_of(IMAGE_PATH),
        "scope": "A2 seven-track unroll + A3 symmetry residuals + A6 spectral lattice",
        "track_unroll": track_calibration(mask, trials),
        "symmetry": symmetry_calibration(mask, trials),
        "spectral": spectral_calibration(mask, trials),
    }


def self_test():
    assert sha256_of(IMAGE_PATH) == EXPECTED_SHA256
    assert len(RING_MODULES) == 16 and len(set(RING_MODULES)) == 16
    assert set(RING_MODULES) == set(white_ring_modules())
    mask = load_mask()
    tracks = ring_tracks(mask)
    assert tracks.shape == (7, 112)
    statistics = track_statistics(tracks)
    assert statistics["one_counts"] == EXPECTED_TRACK_COUNTS
    assert statistics["majority_distances"] == EXPECTED_TRACK_MAJORITY_DISTANCES
    assert statistics["majority_hex"] == EXPECTED_MAJORITY_HEX
    assert statistics["majority_module_values"] == EXPECTED_MODULE_MAJORITY_VALUES
    assert len(statistics["majority_module_roles"]) == 16
    assert all(value is None for value in statistics["printable_ascii_tracks"])

    planted = np.zeros((49, 49), dtype=bool)
    planted_tile = np.asarray([[(x + 2 * y) % 5 < 2 for x in range(7)] for y in range(7)])
    for module in white_ring_modules():
        module_patch(planted, module)[:] = planted_tile
    assert ring_tracks(planted).shape == (7, 112)
    assert spectral_statistics(planted)["seven_pixel_lattice_power_fraction"] > 0.1

    symmetries = symmetry_statistics(mask)
    assert {name: row["residual_pixels"] for name, row in symmetries.items()} == EXPECTED_SYMMETRY_RESIDUALS
    spectrum = spectral_statistics(mask)
    assert math.isclose(spectrum["seven_pixel_lattice_power_fraction"], EXPECTED_LATTICE_POWER,
                        abs_tol=1e-15)
    assert math.isclose(spectrum["seven_pixel_axial_power_fraction"], EXPECTED_AXIAL_POWER,
                        abs_tol=1e-15)

    track_null = track_calibration(mask)["null"]
    for key, expected in EXPECTED_TRACK_NULL_MEANS.items():
        assert math.isclose(track_null[key]["null_mean"], expected, abs_tol=1e-15)
        p_key = "p_le_real" if key == "minimum_majority_distance" else "p_ge_real"
        assert track_null[key][p_key] == 1 / 501
    symmetry_null = symmetry_calibration(mask)["ordered_residual_calibration"]
    assert [row["real_residual_pixels"] for row in symmetry_null] == [78, 206, 208, 230, 230, 238, 254]
    assert all(row["p_le_real"] == 1 / 501 for row in symmetry_null)
    spectral_null = spectral_calibration(mask)
    for key, expected in EXPECTED_SPECTRAL_NULL_MEANS.items():
        row = spectral_null["module_count_preserving_shuffle"][key]
        assert math.isclose(row["null_mean"], expected, abs_tol=1e-15)
        assert row["p_ge_real"] == 1 / 501
    repeated = spectral_null["random_repeated_23_of_49_tile"]
    assert repeated["seven_pixel_lattice_power_fraction"]["p_ge_real"] == 1.0
    print("[*] self-test OK: source, ring order, seven 112-bit tracks, majority bytes, "
          "all three 500-control null families, D4 residual counts, and seven-pixel "
          "spectral power are pinned; planted repeated-tile control is detected.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--trials", type=int, default=NULL_TRIALS)
    args = parser.parse_args()
    self_test()
    if args.self_test:
        return
    result = report(args.trials)
    if args.render:
        result["rendered"] = str(render().relative_to(REPO_ROOT))
    if args.json:
        print(json.dumps(result, indent=2))
        return
    track = result["track_unroll"]
    print("[*] track unroll:", track["real"])
    print("[*] track null:", track["null"])
    print("[*] symmetry:", result["symmetry"])
    print("[*] spectral:", result["spectral"])


if __name__ == "__main__":
    main()
