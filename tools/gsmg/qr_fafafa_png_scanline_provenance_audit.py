#!/usr/bin/env python3
"""Phase 363: QR-eye-specific PNG scanline and encoder provenance audit.

Phases 73/202 already validate the Stage-0 PNG's chunks, CRCs, filters, RGBA
samples, and lone filter-0 row. This audit asks only what the three identical
49x49 QR eyes contribute:

* compare their bytes before unfiltering, including the effect of pixels just
  outside each box and of global scanline filter selection;
* compare the PNG chunk/filter profile with the separately exported 350x350
  rabbit asset; and
* re-encode the exact Stage-0 RGBA pixels through a bounded local matrix of
  Pillow and OpenCV compression settings/strategies.

PNG filtering and DEFLATE operate after whole-image composition. They can
fingerprint the final exporter but cannot distinguish whether an identical
pixel region was originally stamped, copied, or drawn procedurally.
"""

import argparse
import hashlib
import json
import struct
import tempfile
import zlib
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from first_piece_png_palette_provenance_audit import (
    EXPECTED_FULL_SHA256,
    EXPECTED_RABBIT_SHA256,
    FULL_IMAGE,
    RABBIT_IMAGE,
    decode_rgba8,
    parse_png,
)
from qr_fafafa_module_lock_audit import EYE_BOXES

REPO_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_SOURCE_FILTERS = {0: 1, 1: 91, 2: 1464}
EXPECTED_RABBIT_FILTERS = {1: 14, 2: 336}
EXPECTED_PAIR_ROWS = {
    "top_left__top_right": {"exact_rows": 43, "exact_after_first_pixel_rows": 49, "equal_bytes": 9586, "same_filter_rows": 49},
    "top_left__bottom_left": {"exact_rows": 48, "exact_after_first_pixel_rows": 48, "equal_bytes": 9514, "same_filter_rows": 48},
    "top_right__bottom_left": {"exact_rows": 42, "exact_after_first_pixel_rows": 48, "equal_bytes": 9496, "same_filter_rows": 48},
}
OPENCV_STRATEGIES = (
    ("default", cv2.IMWRITE_PNG_STRATEGY_DEFAULT),
    ("filtered", cv2.IMWRITE_PNG_STRATEGY_FILTERED),
    ("huffman", cv2.IMWRITE_PNG_STRATEGY_HUFFMAN_ONLY),
    ("rle", cv2.IMWRITE_PNG_STRATEGY_RLE),
    ("fixed", cv2.IMWRITE_PNG_STRATEGY_FIXED),
)


def sha256_path(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def raw_scanlines(parsed):
    ihdr = parsed["ihdr"]
    assert ihdr["bit_depth"] == 8 and ihdr["color_type"] == 6 and ihdr["interlace_method"] == 0
    stride = ihdr["width"] * 4
    raw = zlib.decompress(parsed["idat"])
    filters, payloads = [], []
    for y in range(ihdr["height"]):
        offset = y * (stride + 1)
        filters.append(raw[offset])
        payloads.append(raw[offset + 1:offset + 1 + stride])
    return tuple(filters), tuple(payloads)


def png_profile(path):
    parsed = parse_png(path)
    _, filters = decode_rgba8(parsed)
    return {
        "path": str(path.relative_to(REPO_ROOT)),
        "sha256": parsed["sha256"],
        "byte_length": parsed["byte_length"],
        "ihdr": parsed["ihdr"],
        "chunk_types": parsed["chunk_types"],
        "chunk_lengths": [chunk["length"] for chunk in parsed["chunks"]],
        "idat_length": len(parsed["idat"]),
        "zlib_header": parsed["idat"][:2].hex(),
        "filter_histogram": dict(sorted(Counter(filters).items())),
    }


def filtered_eye_comparison():
    parsed = parse_png(FULL_IMAGE)
    filters, payloads = raw_scanlines(parsed)
    names = ("top_left", "top_right", "bottom_left")
    origins = [(x0, y0) for x0, y0, _, _ in EYE_BOXES]
    rows = {}
    for first, second in ((0, 1), (0, 2), (1, 2)):
        exact_rows = 0
        exact_after_first = 0
        equal_bytes = 0
        same_filter_rows = 0
        differing_rows = []
        for dy in range(49):
            ax, ay = origins[first][0], origins[first][1] + dy
            bx, by = origins[second][0], origins[second][1] + dy
            left = payloads[ay][ax * 4:(ax + 49) * 4]
            right = payloads[by][bx * 4:(bx + 49) * 4]
            row_exact = left == right
            tail_exact = left[4:] == right[4:]
            equal = sum(a == b for a, b in zip(left, right))
            same_filter = filters[ay] == filters[by]
            exact_rows += int(row_exact)
            exact_after_first += int(tail_exact)
            equal_bytes += equal
            same_filter_rows += int(same_filter)
            if not row_exact:
                differing_rows.append({
                    "eye_relative_row": dy,
                    "global_rows": (ay, by),
                    "filters": (filters[ay], filters[by]),
                    "equal_bytes": equal,
                    "equal_after_first_pixel": tail_exact,
                })
        rows[f"{names[first]}__{names[second]}"] = {
            "exact_rows": exact_rows,
            "exact_after_first_pixel_rows": exact_after_first,
            "equal_bytes": equal_bytes,
            "total_bytes": 49 * 49 * 4,
            "same_filter_rows": same_filter_rows,
            "differing_rows": differing_rows,
        }
    return rows


def encoded_profile(path, width, height):
    data = path.read_bytes()
    offset, idat, chunks, color_type = 8, b"", [], None
    while offset < len(data):
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        chunk_type = data[offset + 4:offset + 8].decode("ascii")
        payload = data[offset + 8:offset + 8 + length]
        chunks.append((chunk_type, length))
        if chunk_type == "IHDR":
            _, _, _, color_type, _, _, _ = struct.unpack(">IIBBBBB", payload)
        elif chunk_type == "IDAT":
            idat += payload
        offset += 12 + length
    bpp = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color_type]
    raw = zlib.decompress(idat)
    stride = width * bpp
    filters = tuple(raw[y * (stride + 1)] for y in range(height))
    return {
        "byte_length": len(data),
        "chunks": chunks,
        "zlib_header": idat[:2].hex(),
        "color_type": color_type,
        "filters": filters,
        "filter_histogram": dict(sorted(Counter(filters).items())),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def encoder_calibration():
    source_image = Image.open(FULL_IMAGE).convert("RGBA")
    rgba = np.asarray(source_image)
    width, height = source_image.size
    source_parsed = parse_png(FULL_IMAGE)
    source_filters, _ = raw_scanlines(source_parsed)
    variants = []
    with tempfile.TemporaryDirectory(prefix="gsmg_qr_png_") as temp_name:
        temp = Path(temp_name)
        for optimize in (False, True):
            for level in range(10):
                path = temp / f"pillow_{int(optimize)}_{level}.png"
                source_image.save(path, compress_level=level, optimize=optimize)
                profile = encoded_profile(path, width, height)
                variants.append({
                    "label": f"pillow_optimize_{int(optimize)}_level_{level}",
                    "filter_mismatches": sum(a != b for a, b in zip(profile["filters"], source_filters)),
                    **{key: value for key, value in profile.items() if key != "filters"},
                })
        bgra = cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA)
        for strategy_name, strategy in OPENCV_STRATEGIES:
            for level in range(10):
                path = temp / f"opencv_{strategy_name}_{level}.png"
                cv2.imwrite(
                    str(path), bgra,
                    [cv2.IMWRITE_PNG_COMPRESSION, level, cv2.IMWRITE_PNG_STRATEGY, strategy],
                )
                profile = encoded_profile(path, width, height)
                variants.append({
                    "label": f"opencv_{strategy_name}_level_{level}",
                    "filter_mismatches": sum(a != b for a, b in zip(profile["filters"], source_filters)),
                    **{key: value for key, value in profile.items() if key != "filters"},
                })
    source_hash = source_parsed["sha256"]
    best_mismatch = min(row["filter_mismatches"] for row in variants)
    return {
        "pillow_version": Image.__version__,
        "opencv_version": cv2.__version__,
        "variants": len(variants),
        "byte_exact_matches": sum(row["sha256"] == source_hash for row in variants),
        "filter_exact_matches": sum(row["filter_mismatches"] == 0 for row in variants),
        "best_filter_mismatches": best_mismatch,
        "best": [row for row in variants if row["filter_mismatches"] == best_mismatch],
    }


def report():
    full = png_profile(FULL_IMAGE)
    rabbit = png_profile(RABBIT_IMAGE)
    return {
        "full": full,
        "rabbit": rabbit,
        "shared_export_profile": {
            "same_chunk_types": full["chunk_types"] == rabbit["chunk_types"],
            "same_zlib_header": full["zlib_header"] == rabbit["zlib_header"],
            "only_none_sub_up_filters": set(full["filter_histogram"]) <= {0, 1, 2}
            and set(rabbit["filter_histogram"]) <= {0, 1, 2},
        },
        "filtered_eye_comparison": filtered_eye_comparison(),
        "encoder_calibration": encoder_calibration(),
        "interpretive_limit": "scanline filters and DEFLATE encode the final composed raster and cannot identify the earlier drawing/stamping operation",
    }


def self_test():
    assert sha256_path(FULL_IMAGE) == EXPECTED_FULL_SHA256
    assert sha256_path(RABBIT_IMAGE) == EXPECTED_RABBIT_SHA256
    full = png_profile(FULL_IMAGE)
    rabbit = png_profile(RABBIT_IMAGE)
    assert full["filter_histogram"] == EXPECTED_SOURCE_FILTERS
    assert rabbit["filter_histogram"] == EXPECTED_RABBIT_FILTERS
    assert full["chunk_types"] == rabbit["chunk_types"] == ("IHDR", "sRGB", "gAMA", "pHYs", "IDAT", "IEND")
    assert full["zlib_header"] == rabbit["zlib_header"] == "785e"
    comparisons = filtered_eye_comparison()
    for pair, expected in EXPECTED_PAIR_ROWS.items():
        for key, value in expected.items():
            assert comparisons[pair][key] == value
    assert comparisons["top_left__bottom_left"]["differing_rows"] == [{
        "eye_relative_row": 14,
        "global_rows": (1303, 1485),
        "filters": (2, 1),
        "equal_bytes": 106,
        "equal_after_first_pixel": False,
    }]
    calibration = encoder_calibration()
    assert calibration["variants"] == 70
    assert calibration["byte_exact_matches"] == 0
    assert calibration["filter_exact_matches"] == 0
    assert calibration["best_filter_mismatches"] == 92
    assert all(row["filter_histogram"] == {0: 1, 1: 47, 2: 1416, 4: 92}
               for row in calibration["best"])
    print("[*] self-test OK: source/rabbit PNG profiles pinned; all three QR-eye filtered-byte "
          "comparisons pinned; sole vertical mismatch is a global filter-choice change; 70 local "
          "Pillow/OpenCV encodes yield zero byte/filter matches and best mismatch 92 rows.")


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
        print("[*] full filters:", result["full"]["filter_histogram"])
        print("[*] rabbit filters:", result["rabbit"]["filter_histogram"])
        print("[*] eye pairs:", {
            key: {field: value for field, value in row.items() if field != "differing_rows"}
            for key, row in result["filtered_eye_comparison"].items()
        })
        calibration = result["encoder_calibration"]
        print(f"[*] encoders={calibration['variants']} byte_exact={calibration['byte_exact_matches']} "
              f"filter_exact={calibration['filter_exact_matches']} "
              f"best_filter_mismatches={calibration['best_filter_mismatches']}")


if __name__ == "__main__":
    main()
