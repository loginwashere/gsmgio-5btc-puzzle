#!/usr/bin/env python3
"""Phase 362: repository fingerprint search for all six QR module variants.

Extends Phase 358 from the canonical two-color right-side patch to all six
byte-distinct 7x7 grayscale patches. Every raster receives byte-exact RGB
search. Flat lossless rasters additionally receive an exact equality-partition
search under all dihedral transforms: each source grayscale class must map to
one constant RGB color, and different source classes must remain different.
This supports two-, four-, and five-class variants without reducing them to the
shared binary #FAFAFA geometry.
"""

import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from qr_fafafa_module_lock_audit import EXPECTED_SHA256, IMAGE_PATH, sha256_of, white_ring_modules
from qr_fafafa_six_variant_atlas_audit import grayscale_patches, variant_atlas

REPO_ROOT = Path(__file__).resolve().parents[2]
RASTER_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".gif", ".tif", ".tiff"}
SKIP_PARTS = {".git", "target", "__pycache__"}
MAX_GEOMETRY_PIXELS = 10_000


def raster_paths():
    return sorted(
        path for path in REPO_ROOT.rglob("*")
        if path.is_file()
        and path.suffix.lower() in RASTER_SUFFIXES
        and not any(part in SKIP_PARTS for part in path.relative_to(REPO_ROOT).parts)
    )


def transforms(labels):
    candidates = []
    for rotation in range(4):
        rotated = np.rot90(labels, rotation)
        candidates.append((f"rot{rotation * 90}", rotated))
        candidates.append((f"rot{rotation * 90}_hflip", np.fliplr(rotated)))
    unique, seen = [], set()
    for name, transformed in candidates:
        key = transformed.tobytes()
        if key not in seen:
            seen.add(key)
            unique.append((name, transformed))
    return unique


def constant_class_candidates(channel, class_mask):
    source = channel.astype(np.float32)
    kernel = class_mask.astype(np.float32)
    count = int(class_mask.sum())
    sums = cv2.matchTemplate(source, kernel, cv2.TM_CCORR)
    sum_squares = cv2.matchTemplate(source * source, kernel, cv2.TM_CCORR)
    return np.abs(count * sum_squares - sums * sums) < 32.0


def scan_array(rgb, target, geometry=True):
    height, width = rgb.shape[:2]
    if height < 7 or width < 7:
        return []
    matches = []
    exact_target = np.repeat(target[:, :, None], 3, axis=2).astype(np.uint8)
    exact_score = cv2.matchTemplate(rgb, exact_target, cv2.TM_SQDIFF)
    for y, x in zip(*np.where(exact_score < 128.0)):
        if np.array_equal(rgb[y:y + 7, x:x + 7], exact_target):
            matches.append({
                "kind": "byte_exact", "x": int(x), "y": int(y),
                "transform": "identity",
                "class_colors": {
                    str(int(value)): [int(value)] * 3 for value in np.unique(target)
                },
            })
    if not geometry:
        return matches

    values = np.unique(target)
    labels = np.searchsorted(values, target)
    for transform_name, transformed in transforms(labels):
        valid = np.ones((height - 6, width - 6), dtype=bool)
        class_masks = [transformed == index for index in range(len(values))]
        # A candidate must make every target class constant. Use the two
        # largest classes in one channel as a safe broad prefilter, then exact-
        # verify every class and RGB channel only at surviving coordinates.
        # If a very flat image leaves many candidates, progressively add the
        # same safe constancy constraints in the other channels.
        prefilter_masks = sorted(class_masks, key=lambda mask: int(mask.sum()), reverse=True)[:2]
        for class_mask in prefilter_masks:
            valid &= constant_class_candidates(rgb[:, :, 0], class_mask)
        if int(valid.sum()) > 100_000:
            for class_mask in prefilter_masks:
                valid &= constant_class_candidates(rgb[:, :, 1], class_mask)
        if int(valid.sum()) > 100_000:
            for class_mask in prefilter_masks:
                valid &= constant_class_candidates(rgb[:, :, 2], class_mask)
        for y, x in zip(*np.where(valid)):
            window = rgb[y:y + 7, x:x + 7]
            colors = []
            exact = True
            for class_mask in class_masks:
                pixels = window[class_mask]
                if not np.all(pixels == pixels[0]):
                    exact = False
                    break
                colors.append(tuple(int(value) for value in pixels[0]))
            if not exact or len(set(colors)) != len(colors):
                continue
            matches.append({
                "kind": "geometry_exact", "x": int(x), "y": int(y),
                "transform": transform_name,
                "class_colors": {
                    str(int(source_value)): list(color)
                    for source_value, color in zip(values, colors)
                },
            })

    # Prefer byte-exact over remapped and collapse symmetry duplicates.
    deduplicated = {}
    for match in matches:
        key = (match["x"], match["y"], tuple(sorted(
            (label, tuple(color)) for label, color in match["class_colors"].items()
        )))
        prior = deduplicated.get(key)
        if prior is None or match["kind"] == "byte_exact":
            deduplicated[key] = match
    return sorted(
        deduplicated.values(),
        key=lambda match: (match["y"], match["x"], match["kind"], match["transform"]),
    )


def targets():
    gray = grayscale_patches()
    atlas = variant_atlas(gray)
    modules = white_ring_modules()
    return [
        {
            "variant": row["variant"],
            "sha256": row["sha256"],
            "source_modules": row["modules"],
            "source_multiplicity": row["multiplicity"],
            "values": row["values"],
            "patch": gray[modules.index(tuple(row["modules"][0]))],
        }
        for row in atlas
    ]


def run():
    target_rows = targets()
    paths = raster_paths()
    results, errors = [], []
    geometry_scanned = 0
    geometry_skipped_large = []
    for path in paths:
        try:
            image = Image.open(path).convert("RGB")
            rgb = np.asarray(image)
        except Exception as error:
            errors.append({"file": str(path.relative_to(REPO_ROOT)), "error": repr(error)})
            continue
        flat_lossless = (
            path.suffix.lower() in {".png", ".bmp", ".gif", ".tif", ".tiff"}
            and image.getcolors(maxcolors=257) is not None
        )
        exact_by_variant = {
            target_row["variant"]: scan_array(rgb, target_row["patch"], geometry=False)
            for target_row in target_rows
        }
        complete_exact_atlas = all(exact_by_variant[row["variant"]] for row in target_rows)
        within_geometry_cap = rgb.shape[0] * rgb.shape[1] <= MAX_GEOMETRY_PIXELS
        do_geometry = flat_lossless and within_geometry_cap and not complete_exact_atlas
        if flat_lossless and not within_geometry_cap:
            geometry_skipped_large.append({
                "file": str(path.relative_to(REPO_ROOT)),
                "pixels": int(rgb.shape[0] * rgb.shape[1]),
            })
        geometry_scanned += int(do_geometry)
        variant_hits = []
        for target_row in target_rows:
            hits = (
                scan_array(rgb, target_row["patch"], geometry=True)
                if do_geometry else exact_by_variant[target_row["variant"]]
            )
            if hits:
                variant_hits.append({
                    "variant": target_row["variant"],
                    "target_sha256": target_row["sha256"],
                    "hits": hits,
                    "hit_count": len(hits),
                })
        if variant_hits:
            results.append({
                "file": str(path.relative_to(REPO_ROOT)),
                "width": int(rgb.shape[1]), "height": int(rgb.shape[0]),
                "variants": variant_hits,
                "hit_count": sum(row["hit_count"] for row in variant_hits),
            })
    return {
        "source_sha256": sha256_of(IMAGE_PATH),
        "targets": [
            {key: value for key, value in row.items() if key != "patch"}
            for row in target_rows
        ],
        "raster_files_scanned": len(paths),
        "flat_lossless_geometry_files_scanned": geometry_scanned,
        "geometry_max_pixels": MAX_GEOMETRY_PIXELS,
        "geometry_skipped_large": geometry_skipped_large,
        "geometry_skip_rule": "skip remap search above the disclosed pixel cap or when the file already contains byte-exact hits for all six variants",
        "files_with_hits": len(results),
        "total_hits": sum(row["hit_count"] for row in results),
        "results": results,
        "read_errors": errors,
    }


def self_test():
    assert sha256_of(IMAGE_PATH) == EXPECTED_SHA256
    target_rows = targets()
    assert len(target_rows) == 6
    assert [row["source_multiplicity"] for row in target_rows] == [4, 1, 2, 4, 1, 4]

    for target_row in target_rows:
        target = target_row["patch"]
        source_values = np.unique(target)
        planted_colors = [
            ((37 * index + 11) % 256, (73 * index + 29) % 256, (109 * index + 47) % 256)
            for index in range(len(source_values))
        ]
        planted = np.zeros((12, 13, 3), dtype=np.uint8)
        planted[:] = (3, 5, 7)
        patch = np.empty((7, 7, 3), dtype=np.uint8)
        for value, color in zip(source_values, planted_colors):
            patch[target == value] = color
        planted[3:10, 4:11] = patch
        hits = scan_array(planted, target)
        assert any(hit["x"] == 4 and hit["y"] == 3 for hit in hits), (target_row["variant"], hits)

    blank = np.full((10, 10, 3), 99, dtype=np.uint8)
    assert all(not scan_array(blank, row["patch"]) for row in target_rows)
    source = np.asarray(Image.open(IMAGE_PATH).convert("RGB"))
    counts = [len(scan_array(source, row["patch"], geometry=False)) for row in target_rows]
    assert counts == [12, 3, 6, 12, 3, 12], counts
    print("[*] self-test OK: source and six targets pinned; arbitrary palette remaps planted and "
          "found for every 2/4/5-class variant; uniform negatives rejected; source hit counts "
          "pin exactly 48 modules across three finder eyes.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    self_test()
    if args.self_test:
        return
    result = run()
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"[*] scanned={result['raster_files_scanned']} geometry="
              f"{result['flat_lossless_geometry_files_scanned']} files_with_hits="
              f"{result['files_with_hits']} total_hits={result['total_hits']}")
        for row in result["results"]:
            counts = [(variant["variant"], variant["hit_count"]) for variant in row["variants"]]
            print(f"  {row['file']}: {row['hit_count']} {counts}")


if __name__ == "__main__":
    main()
