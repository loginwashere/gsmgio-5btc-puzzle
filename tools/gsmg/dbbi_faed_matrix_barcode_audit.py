#!/usr/bin/env python3
"""Bounded standard-matrix-barcode render audit for DBBI and FAED.

The brainstorm's 182/1140 "bits" are corrected here: those counts are trits.
The only lossless binary bridge used is the whole forward base-9 integer.
Candidates use the nearest standard grid that can hold that bit string, two
fixed-width zero-extension sides, three canonical fills, and both polarities.
"""

import argparse
import json
import tempfile
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from data import DBBI, FAED


SOURCES = {"dbbi": DBBI, "faed": FAED}
FILL_ORDERS = ("row_major", "column_major", "boustrophedon")
PAD_SIDES = ("leading", "trailing")
POLARITIES = ("normal", "inverted")
QR_SIZES = tuple(21 + 4 * version for version in range(40))
DATAMATRIX_SQUARE_SIZES = (
    10, 12, 14, 16, 18, 20, 22, 24, 26, 32, 36, 40, 44, 48,
    52, 64, 72, 80, 88, 96, 104, 120, 132, 144,
)


def aztec_specs():
    specs = []
    for layers in range(1, 5):
        specs.append((f"compact_l{layers}", 11 + 4 * layers, 5))
    for layers in range(1, 33):
        base = 14 + 4 * layers
        size = base + 1 + 2 * ((base // 2 - 1) // 15)
        specs.append((f"full_l{layers}", size, 7))
    return tuple(specs)


AZTEC_SPECS = aztec_specs()


def base9_bits(stream):
    value = 0
    for symbol in stream:
        digit = ord(symbol) - ord("a")
        if not 0 <= digit < 9:
            raise ValueError("stream must use a-i")
        value = value * 9 + digit
    return bin(value)[2:] if value else "0"


def nearest_fitting_size(bit_length, sizes):
    return next(size for size in sizes if size * size >= bit_length)


def candidate_specs(source, bit_length):
    qr_size = nearest_fitting_size(bit_length, QR_SIZES)
    dm_size = nearest_fitting_size(bit_length, DATAMATRIX_SQUARE_SIZES)
    fitting_aztec_size = nearest_fitting_size(
        bit_length, tuple(sorted(set(size for _name, size, _bull in AZTEC_SPECS)))
    )
    aztec = tuple(
        ("aztec", name, size, bull)
        for name, size, bull in AZTEC_SPECS if size == fitting_aztec_size
    )
    return (
        ("qr", f"version_{(qr_size - 17) // 4}", qr_size, None),
        ("datamatrix", f"ecc200_{dm_size}", dm_size, None),
    ) + aztec


def make_grid(bits, size, pad_side, fill_order, polarity):
    padding = size * size - len(bits)
    if padding < 0:
        raise ValueError("grid is too small")
    extended = ("0" * padding + bits) if pad_side == "leading" else (
        bits + "0" * padding
    )
    values = np.fromiter((character == "1" for character in extended), dtype=np.uint8)
    grid = values.reshape(size, size)
    if fill_order == "column_major":
        grid = grid.T.copy()
    elif fill_order == "boustrophedon":
        grid = grid.copy()
        grid[1::2] = grid[1::2, ::-1]
    elif fill_order != "row_major":
        raise ValueError(fill_order)
    if polarity == "inverted":
        grid ^= 1
    return grid


def qr_finder_score(grid):
    size = len(grid)
    expected = np.zeros((7, 7), dtype=np.uint8)
    expected[0, :] = expected[6, :] = 1
    expected[:, 0] = expected[:, 6] = 1
    expected[2:5, 2:5] = 1
    blocks = (grid[:7, :7], grid[:7, size - 7:], grid[size - 7:, :7])
    matched = sum(int(np.sum(block == expected)) for block in blocks)
    total = 3 * 49
    return matched, total, matched == total


def datamatrix_finder_score(grid):
    size = len(grid)
    checks = []
    checks.extend(grid[:, 0] == 1)       # solid left
    checks.extend(grid[size - 1, :] == 1)  # solid bottom
    checks.extend(grid[0, :] == (np.arange(size) % 2 == 0))
    checks.extend(grid[:, size - 1] == (np.arange(size) % 2 == 1))
    matched = sum(bool(value) for value in checks)
    return matched, len(checks), matched == len(checks)


def aztec_bullseye_score(grid, bullseye_size):
    center = len(grid) // 2
    radius = bullseye_size - 1
    matched = total = 0
    for row in range(center - radius, center + radius + 1):
        for col in range(center - radius, center + radius + 1):
            ring = max(abs(row - center), abs(col - center))
            expected = int(ring % 2 == 0)
            matched += int(grid[row, col] == expected)
            total += 1
    return matched, total, matched == total


def render_image(grid, quiet=4, scale=8):
    padded = np.pad(grid, quiet, constant_values=0)
    pixels = np.where(padded, 0, 255).astype(np.uint8)
    return Image.fromarray(pixels, mode="L").resize(
        (pixels.shape[1] * scale, pixels.shape[0] * scale),
        Image.Resampling.NEAREST,
    )


def qr_decode(image):
    array = np.array(image)
    payload, points, _straight = cv2.QRCodeDetector().detectAndDecode(array)
    return points is not None, payload


def audit(output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    source_rows = []
    for source_name, stream in SOURCES.items():
        bits = base9_bits(stream)
        specs = candidate_specs(source_name, len(bits))
        source_rows.append({
            "source": source_name,
            "symbols": len(stream),
            "trits": 2 * len(stream),
            "binary_bit_length": len(bits),
            "specs": tuple((kind, name, size) for kind, name, size, _ in specs),
        })
        for kind, spec_name, size, bullseye_size in specs:
            for pad_side in PAD_SIDES:
                for fill_order in FILL_ORDERS:
                    for polarity in POLARITIES:
                        grid = make_grid(bits, size, pad_side, fill_order, polarity)
                        if kind == "qr":
                            matched, total, finder_passed = qr_finder_score(grid)
                        elif kind == "datamatrix":
                            matched, total, finder_passed = datamatrix_finder_score(grid)
                        else:
                            matched, total, finder_passed = aztec_bullseye_score(
                                grid, bullseye_size
                            )
                        stem = "_".join((
                            source_name, kind, spec_name, pad_side, fill_order, polarity
                        ))
                        image_path = output_dir / f"{stem}.png"
                        image = render_image(grid)
                        image.save(image_path, format="PNG", optimize=False)
                        qr_detected = False
                        payload = ""
                        if kind == "qr":
                            qr_detected, payload = qr_decode(image)
                        rows.append({
                            "source": source_name,
                            "format": kind,
                            "spec": spec_name,
                            "size": size,
                            "padding_bits": size * size - len(bits),
                            "pad_side": pad_side,
                            "fill_order": fill_order,
                            "polarity": polarity,
                            "finder_matched": matched,
                            "finder_total": total,
                            "finder_ratio": matched / total,
                            "finder_passed": finder_passed,
                            "qr_detector_detected": qr_detected,
                            "decoded_payload": payload,
                            "image_path": str(image_path),
                        })
    finder_hits = tuple(row for row in rows if row["finder_passed"])
    decoded_hits = tuple(row for row in rows if row["decoded_payload"])
    return {
        "representation_correction": {
            "brainstorm_182_1140_bits_is_wrong": True,
            "correct_units": "182 and 1140 trits",
            "binary_bridge": "minimal whole-forward-base9 integer bits",
        },
        "sources": tuple(source_rows),
        "family": {
            "fill_orders": FILL_ORDERS,
            "pad_sides": PAD_SIDES,
            "polarities": POLARITIES,
            "candidate_count": len(rows),
            "padding_is_generous_fixed_width_control": True,
        },
        "rows": tuple(rows),
        "finder_hit_count": len(finder_hits),
        "decoded_hit_count": len(decoded_hits),
        "qr_detected_count": sum(row["qr_detector_detected"] for row in rows),
        "maximum_finder_rows": tuple(
            max((row for row in rows if row["source"] == source
                 and row["format"] == kind), key=lambda row: row["finder_ratio"])
            for source in SOURCES for kind in ("qr", "datamatrix", "aztec")
        ),
        "non_qr_decoder_needed": bool(
            any(row["finder_passed"] and row["format"] != "qr" for row in rows)
        ),
        "candidate_text_generated": False,
        "password_oracle_run": False,
    }


def self_test():
    import qrcode

    assert len(base9_bits(DBBI)) == 287
    assert len(base9_bits(FAED)) == 1807
    qr = qrcode.QRCode(version=1, border=0, box_size=1)
    qr.add_data("GSMG")
    qr.make(fit=False)
    qr_grid = np.array(qr.get_matrix(), dtype=np.uint8)
    assert qr_grid.shape == (21, 21)
    assert qr_finder_score(qr_grid)[2]
    detected, payload = qr_decode(render_image(qr_grid))
    assert detected and payload == "GSMG"

    dm = np.zeros((18, 18), dtype=np.uint8)
    dm[:, 0] = 1
    dm[-1, :] = 1
    dm[0, ::2] = 1
    dm[1::2, -1] = 1
    assert datamatrix_finder_score(dm)[2]

    aztec = np.zeros((19, 19), dtype=np.uint8)
    center = 9
    for row in range(5, 14):
        for col in range(5, 14):
            aztec[row, col] = int(max(abs(row-center), abs(col-center)) % 2 == 0)
    assert aztec_bullseye_score(aztec, 5)[2]

    with tempfile.TemporaryDirectory(prefix="gsmg-barcode-selftest-") as directory:
        report = audit(directory)
        assert report["family"]["candidate_count"] == 84
        assert report["finder_hit_count"] == 0
        assert report["decoded_hit_count"] == 0
        assert not report["non_qr_decoder_needed"]
    print("[*] self-test OK: format finders, real QR decode, and 84-candidate family verified")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="/tmp/gsmg-dbbi-faed-barcodes")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    report = audit(args.output_dir)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    print("[*] correction:", report["representation_correction"])
    print("[*] sources:", report["sources"])
    print("[*] family:", report["family"])
    for row in report["maximum_finder_rows"]:
        print(
            f"[*] best finder {row['source']}/{row['format']}: "
            f"{row['finder_matched']}/{row['finder_total']} "
            f"({row['finder_ratio']:.6f}) {row['spec']} {row['pad_side']} "
            f"{row['fill_order']} {row['polarity']}"
        )
    print("[*] exact finder hits:", report["finder_hit_count"])
    print("[*] QR detections / decoded hits:",
          report["qr_detected_count"], report["decoded_hit_count"])
    print("[*] non-QR decoder needed:", report["non_qr_decoder_needed"])
    print("[*] no candidate text or password oracle was used")


if __name__ == "__main__":
    main()
