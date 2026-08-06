#!/usr/bin/env python3
"""Compare a user-drawn lower rabbit with the puzzle's explicit rabbit sprite.

The edited image proposes a second line-art rabbit directly beneath/right of
the visible rabbit.  This script treats that drawing as a hypothesis mask,
not primary evidence.  It measures whether the edit is approximately a simple
same-scale rotation/reflection of the explicit source rabbit and reports a
small exploratory scale family separately.

Corrected 2026-07-28 (Phase 127): `explicit_rabbit_crop`'s source depends on
`first_piece_color_reconstruction.load_grid`, which now classifies cells by
majority color instead of a single center-pixel sample (see that module's
docstring). The rabbit crop shrank from (65,80) to (65,70) once a spuriously
included background region was removed. Under the corrected crop, the best
same-scale fit ties exactly between rotate_180 and rotate_270 (F1=0.3757,
down from the previous, bugged 0.4587) -- there is no longer a single
preferred orientation, so the earlier "180-degree rotation, thematically
compatible with duality" framing does not hold as stated.
"""

import argparse
import hashlib
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from first_piece_color_reconstruction import DEFAULT_IMAGE, N, load_grid

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BASE = ROOT / "doc" / "img" / "gsmg_rabbit_hint_254marker_fullres.png"
DEFAULT_EDITED = (
    ROOT / "doc" / "img" / "gsmg_rabbit_hint_254marker_fullres_edited.png"
)
DEFAULT_OUTPUT = (
    ROOT / "doc" / "img" / "gsmg_rabbit_hint_black_drawn_fit_audit.png"
)
BASE_SHA256 = "64e9a180f8002ac55a7f681ec69e0ecf085065ce4aa5d7aeb59156c855f00033"
EDITED_SHA256 = "1c651a1cde402eb774546586bf387b04dfbd4b851f6c48d8449c7d174d1369fc"
PRIMARY_SCALE = 3.0
EXPLORATORY_SCALES = tuple(round(2.5 + index * 0.1, 1) for index in range(11))


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def explicit_rabbit_crop(image_path=DEFAULT_IMAGE):
    image = np.asarray(Image.open(image_path).convert("RGB"))
    grid = load_grid(image_path)
    flat = np.zeros_like(image)
    cell_size = image.shape[0] // N
    for row in range(N):
        for column in range(N):
            flat[
                row * cell_size : (row + 1) * cell_size,
                column * cell_size : (column + 1) * cell_size,
            ] = grid[row][column]
    mask = np.any(image != flat, axis=2).astype(np.uint8)
    rows, columns = np.where(mask)
    return mask[
        rows.min() : rows.max() + 1,
        columns.min() : columns.max() + 1,
    ]


def edit_mask(base_path=DEFAULT_BASE, edited_path=DEFAULT_EDITED):
    base = np.asarray(Image.open(base_path).convert("RGB"))
    edited = np.asarray(Image.open(edited_path).convert("RGB"))
    if base.shape != edited.shape:
        raise ValueError(f"image-size mismatch: {base.shape} != {edited.shape}")
    return base, edited, np.any(base != edited, axis=2).astype(np.uint8)


def dihedral_variants(mask):
    variants = []
    for turns in range(4):
        rotated = np.rot90(mask, turns).copy()
        variants.append((f"rotate_{turns * 90}", rotated))
        variants.append(
            (f"rotate_{turns * 90}_mirror", np.fliplr(rotated).copy())
        )
    return tuple(variants)


def best_fit(source, target, scales):
    target_float = target.astype(np.float32)
    target_area = int(np.sum(target))
    results = []
    for scale in scales:
        scaled = cv2.resize(
            source,
            None,
            fx=scale,
            fy=scale,
            interpolation=cv2.INTER_NEAREST,
        )
        for orientation, template in dihedral_variants(scaled):
            response = cv2.matchTemplate(
                target_float, template.astype(np.float32), cv2.TM_CCORR
            )
            _, maximum, _, location = cv2.minMaxLoc(response)
            overlap = int(round(maximum))
            template_area = int(np.sum(template))
            precision = overlap / template_area
            recall = overlap / target_area
            f1 = 2 * overlap / (template_area + target_area)
            results.append(
                {
                    "scale": scale,
                    "orientation": orientation,
                    "x": location[0],
                    "y": location[1],
                    "width": template.shape[1],
                    "height": template.shape[0],
                    "overlap": overlap,
                    "template_area": template_area,
                    "target_area": target_area,
                    "precision": precision,
                    "recall": recall,
                    "f1": f1,
                    "template": template,
                }
            )
    return max(
        results,
        key=lambda result: (
            result["f1"],
            result["precision"],
            result["recall"],
            -result["scale"],
            result["orientation"],
        ),
    )


def save_comparison(edited, target, fit, output_path=DEFAULT_OUTPUT):
    overlay = np.zeros((*target.shape, 4), dtype=np.uint8)
    template_canvas = np.zeros_like(target)
    y0, x0 = fit["y"], fit["x"]
    template_canvas[
        y0 : y0 + fit["height"], x0 : x0 + fit["width"]
    ] = fit["template"]
    overlap = target.astype(bool) & template_canvas.astype(bool)
    target_only = target.astype(bool) & ~template_canvas.astype(bool)
    template_only = template_canvas.astype(bool) & ~target.astype(bool)
    overlay[target_only] = (255, 0, 255, 95)
    overlay[template_only] = (0, 255, 255, 190)
    overlay[overlap] = (0, 255, 0, 190)
    annotated = Image.alpha_composite(
        Image.fromarray(edited, "RGB").convert("RGBA"),
        Image.fromarray(overlay, "RGBA"),
    )
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    annotated.convert("RGB").save(output_path)


def audit(
    base_path=DEFAULT_BASE,
    edited_path=DEFAULT_EDITED,
    output_path=DEFAULT_OUTPUT,
):
    if file_sha256(base_path) != BASE_SHA256:
        raise AssertionError("base full-resolution image hash changed")
    if file_sha256(edited_path) != EDITED_SHA256:
        raise AssertionError("edited hypothesis image hash changed")
    source = explicit_rabbit_crop()
    base, edited, target = edit_mask(base_path, edited_path)
    rows, columns = np.where(target)
    edit_bbox = (
        int(columns.min()),
        int(rows.min()),
        int(columns.max() + 1),
        int(rows.max() + 1),
    )
    primary = best_fit(source, target, (PRIMARY_SCALE,))
    exploratory = best_fit(source, target, EXPLORATORY_SCALES)
    save_comparison(edited, target, primary, output_path)
    return {
        "base_shape": base.shape,
        "source_shape": source.shape,
        "edit_pixels": int(np.sum(target)),
        "edit_bbox": edit_bbox,
        "edit_bbox_area": (
            (edit_bbox[2] - edit_bbox[0]) * (edit_bbox[3] - edit_bbox[1])
        ),
        "primary": primary,
        "exploratory": exploratory,
        "output_path": Path(output_path),
    }


def self_test(
    base_path=DEFAULT_BASE,
    edited_path=DEFAULT_EDITED,
    output_path=DEFAULT_OUTPUT,
):
    report = audit(base_path, edited_path, output_path)
    assert report["source_shape"] == (65, 70)
    assert report["edit_pixels"] == 26333
    assert report["edit_bbox"] == (566, 560, 779, 752)
    primary = report["primary"]
    assert (
        primary["scale"],
        primary["orientation"],
        primary["x"],
        primary["y"],
        primary["width"],
        primary["height"],
    ) == (3.0, "rotate_270", 567, 540, 195, 210)
    assert abs(primary["precision"] - 0.781981981981982) < 1e-12
    assert abs(primary["recall"] - 0.24721831921923063) < 1e-12
    assert abs(primary["f1"] - 0.3756708407871199) < 1e-12
    # rotate_180 at the same scale/position-class scores identically (see
    # Phase 127 correction) -- the tie-break in best_fit's max() key prefers
    # the lexicographically later orientation name, so this is not a genuine
    # single preferred orientation.
    exploratory = report["exploratory"]
    assert exploratory["scale"] == 3.1
    assert exploratory["orientation"] == "rotate_180"
    assert abs(exploratory["f1"] - 0.37630839928516724) < 1e-12
    assert report["output_path"].is_file()
    print(
        "[*] self-test OK: user edit changes 26,333 pixels; best same-scale "
        "fit ties exactly between rotate_180 and rotate_270 with "
        "precision=0.7820, recall=0.2472, F1=0.3757 (corrected -- see Phase 127)"
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--edited", type=Path, default=DEFAULT_EDITED)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    report = self_test(args.base, args.edited, args.output)
    if args.self_test:
        return
    print(f"edited-mask bbox: {report['edit_bbox']}")
    print(f"edited pixels: {report['edit_pixels']}")
    for label in ("primary", "exploratory"):
        fit = report[label]
        print(
            f"{label}: scale={fit['scale']}, orientation={fit['orientation']}, "
            f"position=({fit['x']},{fit['y']}), precision={fit['precision']:.6f}, "
            f"recall={fit['recall']:.6f}, F1={fit['f1']:.6f}"
        )
    print(f"comparison image: {report['output_path']}")
    print(
        "verdict (corrected 2026-07-28, Phase 127): the edit overlaps a "
        "quarter/half-turn copy of the explicit rabbit, but rotate_180 and "
        "rotate_270 tie exactly at the best score -- there is no single "
        "preferred orientation. Most edited pixels are still not explained "
        "by any tested transform; the source does not mechanically reveal "
        "the full drawn rabbit"
    )


if __name__ == "__main__":
    main()
