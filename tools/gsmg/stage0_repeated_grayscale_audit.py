#!/usr/bin/env python3
"""Audit the proposed repeated-byte grayscale rule in the Stage-0 image.

Claimed rule: an exact grayscale RGB triplet ``XYXYXY`` collapses to the
single byte ``XY``; in particular, the rendered logo supplies CECECE -> CE
and the rabbit grid supplies FEFEFE -> FE.

This audit inventories the entire declared family rather than inspecting CE
alone, measures exact connected-component geometry, and (when the sibling
Wayback mirror is available) reconstructs the displayed logo from its actual
48x48 RGBA favicon source.
"""

import argparse
import hashlib
from collections import Counter
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
IMAGE_PATH = REPO_ROOT / "doc" / "img" / "gsmg_puzzle_stage1.png"
FAVICON_PATH = REPO_ROOT.parent / "gsmg-site-mirror" / "img" / "favicon_small.png"

EXPECTED_IMAGE_SHA256 = "38125bbdf1ea58b9b30b075bc6bf71e4089d04bba37098317e47097e2f2a1830"
GRID_BOX = (0, 0, 1048, 1063)
LOGO_BOX = (35, 1095, 175, 1265)
FAVICON_RENDER_ORIGIN = (33, 1112)
FAVICON_RENDER_SIZE = (144, 144)
PAGE_BACKGROUND = (245, 245, 245, 255)

EXPECTED_LOGO_BYTES = (
    "CC", "CD", "CE", "CF", "D0", "D1", "D2", "D3", "D4", "D5",
    "D8", "D9", "DB", "DC", "DD", "DF", "E0", "E1", "E2", "E3",
    "E4", "E5", "E7", "EA", "EB", "EC", "ED", "EE", "EF", "F0",
    "F1", "F2", "F3", "F4",
)
EXPECTED_SINGLE_SOURCE_PIXEL_BYTES = (
    "CE", "D3", "D5", "DB", "DF", "E1", "EC", "ED", "F1", "F2",
)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def repeated_grayscale_histogram(image):
    colors = Counter(image.getdata())
    return {
        value: colors[(value, value, value)]
        for value in range(256)
        if colors[(value, value, value)]
    }


def components(image, value):
    """Return 4-connected exact-color components as size/bounding-box rows."""
    target = (value, value, value)
    pixels = image.load()
    width, height = image.size
    seen = set()
    found = []
    for y in range(height):
        for x in range(width):
            if (x, y) in seen or pixels[x, y] != target:
                continue
            stack = [(x, y)]
            seen.add((x, y))
            points = []
            while stack:
                px, py = stack.pop()
                points.append((px, py))
                for neighbor in (
                    (px - 1, py), (px + 1, py),
                    (px, py - 1), (px, py + 1),
                ):
                    nx, ny = neighbor
                    if (
                        0 <= nx < width
                        and 0 <= ny < height
                        and neighbor not in seen
                        and pixels[nx, ny] == target
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            xs = [point[0] for point in points]
            ys = [point[1] for point in points]
            found.append(
                {
                    "size": len(points),
                    "bbox": (min(xs), min(ys), max(xs), max(ys)),
                    "width": max(xs) - min(xs) + 1,
                    "height": max(ys) - min(ys) + 1,
                }
            )
    return tuple(sorted(found, key=lambda row: (-row["size"], row["bbox"])))


def region_report(image, box):
    crop = image.crop(box)
    histogram = repeated_grayscale_histogram(crop)
    rows = []
    for value, count in sorted(histogram.items()):
        if value in (0, 245, 255):
            continue
        rows.append(
            {
                "byte": f"{value:02X}",
                "value": value,
                "pixel_count": count,
                "components": components(crop, value),
            }
        )
    return tuple(rows)


def favicon_provenance(image):
    if not FAVICON_PATH.exists():
        return None
    favicon = Image.open(FAVICON_PATH).convert("RGBA")
    source_ce_count = sum(
        pixel[:3] == (206, 206, 206) for pixel in favicon.getdata()
    )
    enlarged = favicon.resize(FAVICON_RENDER_SIZE, Image.Resampling.NEAREST)
    rendered = Image.new("RGBA", FAVICON_RENDER_SIZE, PAGE_BACKGROUND)
    rendered.alpha_composite(enlarged)
    rendered = rendered.convert("RGB")
    x, y = FAVICON_RENDER_ORIGIN
    actual = image.crop((x, y, x + rendered.width, y + rendered.height))

    channel_differences = []
    for expected_pixel, actual_pixel in zip(rendered.getdata(), actual.getdata()):
        channel_differences.extend(
            abs(expected - observed)
            for expected, observed in zip(expected_pixel, actual_pixel)
        )
    reconstructed_ce_count = sum(
        pixel == (206, 206, 206) for pixel in rendered.getdata()
    )
    return {
        "source_size": favicon.size,
        "source_ce_count": source_ce_count,
        "rendered_ce_count": reconstructed_ce_count,
        "nonzero_channel_differences": sum(value != 0 for value in channel_differences),
        "maximum_channel_difference": max(channel_differences),
        "total_absolute_difference": sum(channel_differences),
    }


def audit():
    assert sha256(IMAGE_PATH) == EXPECTED_IMAGE_SHA256
    image = Image.open(IMAGE_PATH).convert("RGB")
    assert image.size == (1048, 1556)
    grid = region_report(image, GRID_BOX)
    logo = region_report(image, LOGO_BOX)
    ce = next(row for row in logo if row["byte"] == "CE")
    fe = next(row for row in grid if row["byte"] == "FE")
    singleton_blocks = tuple(
        row["byte"]
        for row in logo
        if row["pixel_count"] == 9
        and len(row["components"]) == 1
        and row["components"][0]["width"] == 3
        and row["components"][0]["height"] == 3
    )
    return {
        "grid": grid,
        "logo": logo,
        "ce": ce,
        "fe": fe,
        "logo_bytes": tuple(row["byte"] for row in logo),
        "logo_single_3x3_bytes": singleton_blocks,
        "collapsed_claim": ("CE", "FE"),
        "concatenated_claim": "CEFE",
        "concatenated_hex_integer": int("CEFE", 16),
        "favicon": favicon_provenance(image),
    }


def self_test():
    report = audit()
    assert report["logo_bytes"] == EXPECTED_LOGO_BYTES
    assert report["logo_single_3x3_bytes"] == EXPECTED_SINGLE_SOURCE_PIXEL_BYTES
    assert report["ce"]["pixel_count"] == 9
    assert report["ce"]["components"] == (
        {"size": 9, "bbox": (67, 155, 69, 157), "width": 3, "height": 3},
    )
    assert report["fe"]["pixel_count"] == 5625
    assert report["fe"]["components"] == (
        {"size": 5625, "bbox": (300, 525, 374, 599), "width": 75, "height": 75},
    )
    assert report["concatenated_hex_integer"] == 52990
    if report["favicon"] is not None:
        assert report["favicon"]["source_size"] == (48, 48)
        assert report["favicon"]["source_ce_count"] == 0
        assert report["favicon"]["rendered_ce_count"] == 9
        assert report["favicon"]["maximum_channel_difference"] == 1
    print("[*] self-test OK: repeated-byte CE/FE geometry and null family reproduce")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    self_test()
    if args.self_test:
        return
    report = audit()
    print(f"[*] collapsed claim: {report['collapsed_claim']} -> {report['concatenated_claim']}")
    print(f"[*] CE: {report['ce']['pixel_count']} pixels, {report['ce']['components']}")
    print(f"[*] FE: {report['fe']['pixel_count']} pixels, {report['fe']['components']}")
    print(f"[*] logo repeated-byte family ({len(report['logo_bytes'])}): {report['logo_bytes']}")
    print(
        "[*] logo colors with exactly one 3x3 component: "
        f"{report['logo_single_3x3_bytes']}"
    )
    if report["favicon"] is not None:
        print(f"[*] favicon provenance: {report['favicon']}")


if __name__ == "__main__":
    main()
