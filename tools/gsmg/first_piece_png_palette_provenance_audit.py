#!/usr/bin/env python3
"""Audit whether the FEFEFE cell has PNG palette-index or alpha metadata.

The authenticated full Stage-0 PNG and the 350x350 rabbit-grid asset are parsed
from raw bytes: every chunk CRC, IHDR field, chunk order, trailing data, IDAT
decompression, and PNG scanline unfiltering are checked.  This determines
whether FEFEFE is an indexed palette entry or an explicit truecolor sample and
whether its alpha differs from surrounding pixels.
"""

import argparse
import hashlib
import struct
import zlib
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FULL_IMAGE = REPO_ROOT / "doc" / "img" / "gsmg_puzzle_stage1.png"
ROOT_COPY = REPO_ROOT / "puzzle.png"
RABBIT_IMAGE = REPO_ROOT / "doc" / "img" / "gsmg_rabbit_hint.png"

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
EXPECTED_FULL_SHA256 = "38125bbdf1ea58b9b30b075bc6bf71e4089d04bba37098317e47097e2f2a1830"
EXPECTED_RABBIT_SHA256 = "5e8d84b88f8f829428df5d2a8bf36c7268346f169b799ac7570b6223990d204f"
FE_RGBA = (254, 254, 254, 255)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def paeth(left, above, upper_left):
    estimate = left + above - upper_left
    left_distance = abs(estimate - left)
    above_distance = abs(estimate - above)
    upper_left_distance = abs(estimate - upper_left)
    if left_distance <= above_distance and left_distance <= upper_left_distance:
        return left
    if above_distance <= upper_left_distance:
        return above
    return upper_left


def parse_png(path):
    data = path.read_bytes()
    if data[:8] != PNG_SIGNATURE:
        raise AssertionError(f"invalid PNG signature: {path}")
    offset = 8
    chunks = []
    idat_parts = []
    ihdr = None
    while offset < len(data):
        if offset + 12 > len(data):
            raise AssertionError("truncated PNG chunk header")
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        chunk_type = data[offset + 4:offset + 8]
        end = offset + 12 + length
        if end > len(data):
            raise AssertionError(f"truncated {chunk_type!r} chunk")
        payload = data[offset + 8:offset + 8 + length]
        stored_crc = struct.unpack(">I", data[offset + 8 + length:end])[0]
        computed_crc = zlib.crc32(chunk_type + payload) & 0xFFFFFFFF
        if stored_crc != computed_crc:
            raise AssertionError(f"CRC mismatch in {chunk_type!r}")
        chunks.append(
            {
                "type": chunk_type.decode("ascii"),
                "length": length,
                "crc_ok": True,
            }
        )
        if chunk_type == b"IHDR":
            if ihdr is not None or length != 13:
                raise AssertionError("invalid IHDR multiplicity/length")
            values = struct.unpack(">IIBBBBB", payload)
            ihdr = dict(
                zip(
                    (
                        "width", "height", "bit_depth", "color_type",
                        "compression_method", "filter_method", "interlace_method",
                    ),
                    values,
                )
            )
        elif chunk_type == b"IDAT":
            idat_parts.append(payload)
        offset = end
        if chunk_type == b"IEND":
            break
    if ihdr is None or not idat_parts or chunks[-1]["type"] != "IEND":
        raise AssertionError("PNG is missing IHDR, IDAT, or IEND")
    if offset != len(data):
        raise AssertionError("bytes trail IEND")
    return {
        "path": str(path),
        "sha256": sha256(data),
        "byte_length": len(data),
        "ihdr": ihdr,
        "chunks": tuple(chunks),
        "chunk_types": tuple(chunk["type"] for chunk in chunks),
        "idat": b"".join(idat_parts),
        "trailing_byte_count": len(data) - offset,
    }


def decode_rgba8(parsed):
    ihdr = parsed["ihdr"]
    if not (
        ihdr["bit_depth"] == 8
        and ihdr["color_type"] == 6
        and ihdr["interlace_method"] == 0
    ):
        raise ValueError("audit decoder supports only non-interlaced RGBA8")
    width, height = ihdr["width"], ihdr["height"]
    bytes_per_pixel = 4
    stride = width * bytes_per_pixel
    raw = zlib.decompress(parsed["idat"])
    if len(raw) != height * (stride + 1):
        raise AssertionError("unexpected decompressed scanline size")

    rows = []
    filters = []
    offset = 0
    prior = bytearray(stride)
    for _ in range(height):
        filter_type = raw[offset]
        filtered = raw[offset + 1:offset + 1 + stride]
        offset += stride + 1
        if filter_type not in range(5):
            raise AssertionError(f"invalid PNG filter: {filter_type}")
        current = bytearray(stride)
        for index, encoded in enumerate(filtered):
            left = current[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
            above = prior[index]
            upper_left = prior[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
            if filter_type == 0:
                predictor = 0
            elif filter_type == 1:
                predictor = left
            elif filter_type == 2:
                predictor = above
            elif filter_type == 3:
                predictor = (left + above) // 2
            else:
                predictor = paeth(left, above, upper_left)
            current[index] = (encoded + predictor) & 0xFF
        rows.append(bytes(current))
        filters.append(filter_type)
        prior = current
    return tuple(rows), tuple(filters)


def pixel_report(parsed):
    rows, filters = decode_rgba8(parsed)
    width, height = parsed["ihdr"]["width"], parsed["ihdr"]["height"]
    fe_points = []
    alpha_counts = Counter()
    for y, row in enumerate(rows):
        for x in range(width):
            pixel = tuple(row[x * 4:(x + 1) * 4])
            alpha_counts[pixel[3]] += 1
            if pixel == FE_RGBA:
                fe_points.append((x, y))
    if not fe_points:
        raise AssertionError("FEFEFE/opaque sample is absent")
    xs = tuple(point[0] for point in fe_points)
    ys = tuple(point[1] for point in fe_points)
    bbox = (min(xs), min(ys), max(xs), max(ys))
    bbox_width = bbox[2] - bbox[0] + 1
    bbox_height = bbox[3] - bbox[1] + 1
    return {
        "fe_rgba": FE_RGBA,
        "fe_pixel_count": len(fe_points),
        "fe_bbox_inclusive": bbox,
        "fe_bbox_width": bbox_width,
        "fe_bbox_height": bbox_height,
        "fe_fills_bbox": len(fe_points) == bbox_width * bbox_height,
        "alpha_histogram": dict(sorted(alpha_counts.items())),
        "all_pixels_opaque": alpha_counts == Counter({255: width * height}),
        "filter_histogram": dict(sorted(Counter(filters).items())),
    }


def inspect(path):
    parsed = parse_png(path)
    pixels = pixel_report(parsed)
    chunk_types = parsed["chunk_types"]
    return {
        "path": parsed["path"],
        "sha256": parsed["sha256"],
        "byte_length": parsed["byte_length"],
        "ihdr": parsed["ihdr"],
        "chunks": parsed["chunks"],
        "chunk_types": chunk_types,
        "plte_present": "PLTE" in chunk_types,
        "trns_present": "tRNS" in chunk_types,
        "text_or_exif_chunks": tuple(
            value for value in chunk_types if value in ("tEXt", "zTXt", "iTXt", "eXIf")
        ),
        "trailing_byte_count": parsed["trailing_byte_count"],
        "pixels": pixels,
    }


def audit():
    full = inspect(FULL_IMAGE)
    rabbit = inspect(RABBIT_IMAGE)
    root_bytes = ROOT_COPY.read_bytes()
    full_bytes = FULL_IMAGE.read_bytes()
    full_bbox = full["pixels"]["fe_bbox_inclusive"]
    rabbit_bbox = rabbit["pixels"]["fe_bbox_inclusive"]
    scale = full["pixels"]["fe_bbox_width"] // rabbit["pixels"]["fe_bbox_width"]
    return {
        "full": full,
        "rabbit": rabbit,
        "root_copy_byte_identical": root_bytes == full_bytes,
        "root_copy_sha256": sha256(root_bytes),
        "format_verdict": {
            "full_is_rgba8_truecolor": full["ihdr"]["color_type"] == 6 and full["ihdr"]["bit_depth"] == 8,
            "rabbit_is_rgba8_truecolor": rabbit["ihdr"]["color_type"] == 6 and rabbit["ihdr"]["bit_depth"] == 8,
            "palette_index_exists": False,
            "fe_has_distinct_alpha": not (
                full["pixels"]["all_pixels_opaque"] and rabbit["pixels"]["all_pixels_opaque"]
            ),
            "decoded_fe_sample_hex": "FEFEFEFF",
        },
        "marker_scaling": {
            "linear_scale_full_to_rabbit": scale,
            "full_bbox_equals_scaled_rabbit_bbox": full_bbox == tuple(value * scale + (scale - 1 if index >= 2 else 0) for index, value in enumerate(rabbit_bbox)),
            "pixel_count_ratio": full["pixels"]["fe_pixel_count"] // rabbit["pixels"]["fe_pixel_count"],
        },
    }


def self_test():
    report = audit()
    full, rabbit = report["full"], report["rabbit"]
    verdict = report["format_verdict"]
    scaling = report["marker_scaling"]
    expected_chunks = ("IHDR", "sRGB", "gAMA", "pHYs", "IDAT", "IEND")

    assert full["sha256"] == EXPECTED_FULL_SHA256
    assert rabbit["sha256"] == EXPECTED_RABBIT_SHA256
    assert report["root_copy_byte_identical"] is True
    assert report["root_copy_sha256"] == EXPECTED_FULL_SHA256
    assert full["ihdr"] == {
        "width": 1048, "height": 1556, "bit_depth": 8, "color_type": 6,
        "compression_method": 0, "filter_method": 0, "interlace_method": 0,
    }
    assert rabbit["ihdr"] == {
        "width": 350, "height": 350, "bit_depth": 8, "color_type": 6,
        "compression_method": 0, "filter_method": 0, "interlace_method": 0,
    }
    assert full["chunk_types"] == rabbit["chunk_types"] == expected_chunks
    assert full["plte_present"] is rabbit["plte_present"] is False
    assert full["trns_present"] is rabbit["trns_present"] is False
    assert full["text_or_exif_chunks"] == rabbit["text_or_exif_chunks"] == ()
    assert full["trailing_byte_count"] == rabbit["trailing_byte_count"] == 0
    assert full["pixels"]["fe_pixel_count"] == 5625
    assert full["pixels"]["fe_bbox_inclusive"] == (300, 525, 374, 599)
    assert full["pixels"]["fe_bbox_width"] == full["pixels"]["fe_bbox_height"] == 75
    assert rabbit["pixels"]["fe_pixel_count"] == 625
    assert rabbit["pixels"]["fe_bbox_inclusive"] == (100, 175, 124, 199)
    assert rabbit["pixels"]["fe_bbox_width"] == rabbit["pixels"]["fe_bbox_height"] == 25
    assert full["pixels"]["fe_fills_bbox"] is rabbit["pixels"]["fe_fills_bbox"] is True
    assert full["pixels"]["alpha_histogram"] == {255: 1048 * 1556}
    assert rabbit["pixels"]["alpha_histogram"] == {255: 350 * 350}
    assert verdict == {
        "full_is_rgba8_truecolor": True,
        "rabbit_is_rgba8_truecolor": True,
        "palette_index_exists": False,
        "fe_has_distinct_alpha": False,
        "decoded_fe_sample_hex": "FEFEFEFF",
    }
    assert scaling == {
        "linear_scale_full_to_rabbit": 3,
        "full_bbox_equals_scaled_rabbit_bbox": True,
        "pixel_count_ratio": 9,
    }
    print("[*] self-test OK: PNGs are opaque RGBA8 truecolor; FE has no palette index/alpha channel data")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    report = audit()
    for label in ("full", "rabbit"):
        item = report[label]
        print(f"[*] {label}: IHDR={item['ihdr']}; chunks={item['chunk_types']}")
        print(f"    FE={item['pixels']['fe_pixel_count']} pixels, bbox={item['pixels']['fe_bbox_inclusive']}, alpha={item['pixels']['alpha_histogram']}")
    print(f"[*] verdict: {report['format_verdict']}")
    print(f"[*] marker scaling: {report['marker_scaling']}")
    if args.self_test:
        self_test()


if __name__ == "__main__":
    main()
