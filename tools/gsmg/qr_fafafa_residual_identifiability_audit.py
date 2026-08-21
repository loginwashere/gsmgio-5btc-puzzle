#!/usr/bin/env python3
"""Phase 361: audit Phase 360's residual compactness and center identifiability.

The registered residual is the union of exact-#FAFAFA mistakes from the
sixteen leave-one-module-out folds of Phase 360's row-plus-column model.  Test
whether its subpixel support is unusually compact under the same deterministic
patch-position permutation controls.

Separately, prove the missing center is not identified by perimeter evidence:
add one shared center-interaction scalar to every Phase-360 center score.  The
term is identically zero on every observed or held-out perimeter module, so it
cannot change the 773/784 cross-validation result, but it can change the
unobserved center completion.  The displayed alternatives are therefore
equally scoring counterfactuals, not recovered pixels.
"""

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from qr_fafafa_module_lock_audit import EXPECTED_SHA256, IMAGE_PATH, load_eyes, sha256_of, white_ring_modules
from qr_fafafa_six_variant_atlas_audit import grayscale_patches, predict_bits, predict_scores

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_IMAGE = REPO_ROOT / "doc" / "img" / "gsmg_qr_fafafa_phase361_residual_and_ambiguity.png"
NULL_TRIALS = 500
NULL_SEED = 20260821
LAMBDAS = (-0.25, 0.0, 0.25)
EXPECTED_ERRORS = [
    ((1, 1), (2, 4), 1, 0),
    ((1, 2), (2, 0), 1, 0),
    ((1, 3), (2, 0), 0, 1),
    ((1, 4), (2, 0), 0, 1),
    ((1, 5), (2, 4), 1, 0),
    ((5, 1), (2, 0), 0, 1),
    ((5, 2), (2, 4), 1, 0),
    ((5, 3), (2, 0), 1, 0),
    ((5, 3), (2, 4), 1, 0),
    ((5, 4), (2, 0), 1, 0),
    ((5, 5), (2, 0), 1, 0),
]


def loo_errors(patches):
    modules = white_ring_modules()
    errors = []
    for held_index, held_module in enumerate(modules):
        train_modules = [m for index, m in enumerate(modules) if index != held_index]
        prediction = predict_bits(
            train_modules, np.delete(patches, held_index, axis=0), [held_module]
        )[0]
        for sy, sx in zip(*np.where(prediction != patches[held_index])):
            errors.append({
                "module": held_module,
                "subpixel": (int(sy), int(sx)),
                "finder_coordinate": (held_module[0] * 7 + int(sy), held_module[1] * 7 + int(sx)),
                "actual": int(patches[held_index, sy, sx]),
                "predicted": int(prediction[sy, sx]),
                "signed": int(patches[held_index, sy, sx]) - int(prediction[sy, sx]),
            })
    return errors


def support_stats(errors):
    sub_rows = Counter(error["subpixel"][0] for error in errors)
    sub_cols = Counter(error["subpixel"][1] for error in errors)
    module_rows = {error["module"][0] for error in errors}
    module_cols = {error["module"][1] for error in errors}
    return {
        "errors": len(errors),
        "unique_subpixel_rows": len(sub_rows),
        "unique_subpixel_columns": len(sub_cols),
        "subpixel_support_area": len(sub_rows) * len(sub_cols),
        "max_subpixel_row_fraction": max(sub_rows.values()) / len(errors),
        "max_subpixel_column_fraction": max(sub_cols.values()) / len(errors),
        "unique_module_rows": len(module_rows),
        "unique_module_columns": len(module_cols),
    }


def calibrate(patches, trials=NULL_TRIALS):
    real_errors = loo_errors(patches)
    real = support_stats(real_errors)
    rng = np.random.default_rng(NULL_SEED)
    controls = []
    for _ in range(trials):
        permuted = patches[rng.permutation(len(patches))]
        controls.append(support_stats(loo_errors(permuted)))

    def summary(key):
        values = np.asarray([control[key] for control in controls], dtype=float)
        return {"mean": float(values.mean()), "min": float(values.min()), "max": float(values.max())}

    compact_count = sum(
        control["subpixel_support_area"] <= real["subpixel_support_area"]
        for control in controls
    )
    return {
        "real": real,
        "null_trials": trials,
        "null_seed": NULL_SEED,
        "null_errors": summary("errors"),
        "null_unique_subpixel_rows": summary("unique_subpixel_rows"),
        "null_unique_subpixel_columns": summary("unique_subpixel_columns"),
        "null_subpixel_support_area": summary("subpixel_support_area"),
        "null_support_area_le_real": compact_count,
        "p_support_area_le_real": float((1 + compact_count) / (trials + 1)),
    }


def center_alternatives(patches):
    modules = white_ring_modules()
    center_modules = [(my, mx) for my in range(2, 5) for mx in range(2, 5)]
    scores = predict_scores(modules, patches, center_modules)
    alternatives = []
    for interaction in LAMBDAS:
        bits = scores + interaction >= 0.5
        alternatives.append({
            "center_interaction": interaction,
            "fafafa_count": int(bits.sum()),
            "distinct_patches": len({patch.tobytes() for patch in bits}),
            "patches": bits,
        })
    return center_modules, alternatives


def report(trials=NULL_TRIALS):
    patches = grayscale_patches() == 250
    errors = loo_errors(patches)
    center_modules, alternatives = center_alternatives(patches)
    return {
        "source": str(IMAGE_PATH.relative_to(REPO_ROOT)),
        "source_sha256": sha256_of(IMAGE_PATH),
        "residual_definition": "union of Phase-360 leave-one-module-out prediction errors",
        "errors": errors,
        "signed_sequence_module_row_major": "".join("+" if error["signed"] > 0 else "-" for error in errors),
        "actual_bit_sequence_module_row_major": "".join(str(error["actual"]) for error in errors),
        "calibration": calibrate(patches, trials),
        "irregular_row_relation": {
            "finder_rows": sorted({error["finder_coordinate"][0] for error in errors}),
            "subpixel_rows": sorted({error["subpixel"][0] for error in errors}),
            "subpixel_columns": sorted({error["subpixel"][1] for error in errors}),
            "phase_305_scope": "both finder rows 9 and 37 were already tested as complete 34-bit rows, reversals, concatenations, difference mask, and differing positions",
        },
        "center_identifiability": {
            "center_modules": center_modules,
            "interaction_definition": "one scalar multiplied by an indicator that is 1 only in the unobserved 3x3 center and 0 on the perimeter",
            "cross_validation_exact_for_every_interaction": 773,
            "alternatives": [
                {
                    "center_interaction": alternative["center_interaction"],
                    "fafafa_count": alternative["fafafa_count"],
                    "distinct_patches": alternative["distinct_patches"],
                    "rows_by_module": [
                        ["".join("1" if value else "0" for value in row) for row in patch]
                        for patch in alternative["patches"]
                    ],
                }
                for alternative in alternatives
            ],
            "conclusion": "perimeter evidence cannot select a unique center continuation without forbidding center-only interactions",
        },
    }


def false_color_eye(center_modules=None, center_patches=None):
    eye = load_eyes()[0].copy()
    if center_modules is not None:
        for (my, mx), patch in zip(center_modules, center_patches):
            values = np.where(patch, 250, 255).astype(np.uint8)
            eye[my * 7:(my + 1) * 7, mx * 7:(mx + 1) * 7] = values[:, :, None]
    luminance = eye[:, :, 0]
    colored = np.full_like(eye, 255)
    colored[luminance == 0] = (25, 25, 25)
    colored[luminance == 250] = (20, 135, 230)
    colored[~np.isin(luminance, (0, 250, 255))] = (245, 145, 35)
    return colored


def render(path=OUTPUT_IMAGE):
    patches = grayscale_patches() == 250
    errors = loo_errors(patches)
    center_modules, alternatives = center_alternatives(patches)
    scale = 8
    eye_size = 49 * scale
    center_size = 21 * scale
    margin, gap, title_h, footer_h = 28, 34, 56, 76
    widths = [eye_size] + [center_size] * len(alternatives)
    canvas = Image.new(
        "RGB",
        (margin * 2 + sum(widths) + gap * len(alternatives),
         margin * 2 + title_h + eye_size + footer_h),
        "white",
    )
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()

    observed = Image.fromarray(false_color_eye()).resize((eye_size, eye_size), Image.Resampling.NEAREST)
    x0, y0 = margin, margin + title_h
    canvas.paste(observed, (x0, y0))
    draw.text((x0, margin + 14), "11 held-out errors (green +1, magenta -1)", fill="black", font=font)
    for error in errors:
        fy, fx = error["finder_coordinate"]
        color = (20, 185, 80) if error["signed"] > 0 else (220, 40, 170)
        draw.rectangle(
            (x0 + fx * scale, y0 + fy * scale,
             x0 + (fx + 1) * scale - 1, y0 + (fy + 1) * scale - 1),
            outline=color,
            width=3,
        )

    x = x0 + eye_size + gap
    for alternative in alternatives:
        complete = false_color_eye(center_modules, alternative["patches"])
        center = complete[14:35, 14:35]
        enlarged = Image.fromarray(center).resize((center_size, center_size), Image.Resampling.NEAREST)
        canvas.paste(enlarged, (x, y0))
        label = f"center interaction {alternative['center_interaction']:+.2f}: {alternative['fafafa_count']} blue"
        draw.text((x, margin + 14), label, fill="black", font=font)
        for line in range(4):
            pos = line * 7 * scale
            draw.line((x + pos, y0, x + pos, y0 + center_size), fill=(210, 60, 60), width=1)
            draw.line((x, y0 + pos, x + center_size, y0 + pos), fill=(210, 60, 60), width=1)
        x += center_size + gap

    footer = ("All three center completions retain the identical 773/784 perimeter cross-validation score. "
              "Blue = exact #FAFAFA; orange = other grayscale edge values. Center pixels are hypothetical.")
    draw.text((margin, margin + title_h + eye_size + 28), footer, fill="black", font=font)
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path)
    return path


def self_test():
    assert sha256_of(IMAGE_PATH) == EXPECTED_SHA256
    patches = grayscale_patches() == 250
    errors = loo_errors(patches)
    observed = [
        (error["module"], error["subpixel"], error["actual"], error["predicted"])
        for error in errors
    ]
    assert observed == EXPECTED_ERRORS
    real = support_stats(errors)
    assert real == {
        "errors": 11,
        "unique_subpixel_rows": 1,
        "unique_subpixel_columns": 2,
        "subpixel_support_area": 2,
        "max_subpixel_row_fraction": 1.0,
        "max_subpixel_column_fraction": 7 / 11,
        "unique_module_rows": 2,
        "unique_module_columns": 5,
    }
    calibration = calibrate(patches)
    assert calibration["null_support_area_le_real"] == 0
    assert calibration["null_subpixel_support_area"] == {"mean": 15.0, "min": 15.0, "max": 15.0}
    _, alternatives = center_alternatives(patches)
    assert [alternative["fafafa_count"] for alternative in alternatives] == [198, 210, 213]
    assert [alternative["distinct_patches"] for alternative in alternatives] == [1, 2, 2]
    print("[*] self-test OK: 11 signed residual sites pinned; all occupy subpixel row 2 and "
          "columns 0/4; 500 permutation controls pin support area 15 versus real 2; three "
          "equally perimeter-scoring center interactions yield 198/210/213 #FAFAFA sites.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--trials", type=int, default=NULL_TRIALS)
    parser.add_argument("--render", action="store_true")
    args = parser.parse_args()
    self_test()
    if args.self_test:
        return
    result = report(args.trials)
    if args.render:
        result["rendered"] = str(render().relative_to(REPO_ROOT))
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        calibration = result["calibration"]
        alternatives = result["center_identifiability"]["alternatives"]
        print(f"[*] residual={calibration['real']}; null support="
              f"{calibration['null_subpixel_support_area']}; "
              f"p={calibration['p_support_area_le_real']:.6f}")
        print("[*] equally scoring center counts:",
              [(row["center_interaction"], row["fafafa_count"]) for row in alternatives])
        if args.render:
            print(f"[*] rendered {result['rendered']}")


if __name__ == "__main__":
    main()
