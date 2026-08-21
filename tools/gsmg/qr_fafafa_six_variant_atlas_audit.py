#!/usr/bin/env python3
"""Phase 360: model the six QR #FAFAFA module variants without collapsing them.

The sixteen 7x7 white-ring modules form the observed perimeter of a 5x5
module matrix.  For each of the 49 subpixel coordinates, fit a frozen
two-way additive model (module-row effect + module-column effect) to the
binary exact-#FAFAFA occupancy.  Rotate a held-out module over the perimeter,
then compare the aggregate exact-bit score with controls that permute the
six observed patch variants among the sixteen perimeter positions.

Only after cross-validation, fit all observed modules and predict the hidden
3x3 center.  That continuation is a model-derived counterfactual: the real
finder center is black and supplies no observations there.
"""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from qr_fafafa_module_lock_audit import (
    EXPECTED_SHA256,
    IMAGE_PATH,
    load_eyes,
    sha256_of,
    white_ring_modules,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_IMAGE = REPO_ROOT / "doc" / "img" / "gsmg_qr_fafafa_phase360_center_prediction.png"
NULL_TRIALS = 500
NULL_SEED = 20260821
EXPECTED_VARIANT_MULTIPLICITIES = [4, 1, 2, 4, 1, 4]
EXPECTED_VARIANT_SHA256 = [
    "b62977c7c6ced19719d675f484852fd2b031ff16363bbfebf706172918bf8d08",
    "600d428c4d514744f4b369853d003fb7bd4f93bc96ec012a19e3fd176d4b282f",
    "ff22dd92f95b383fae88dfa6fba228cfce41d292e63d6b0cad3fd190edb26ad4",
    "3a733caa98a048e820d2e20d94b7680faacdcdd77feae0a05ad2c99dc27b54c8",
    "1699e06624da4c1d0c2df163deb9846ea2c665628dee57a68df724e84ac621b0",
    "e2b0687d93ab628fb794b548ffa5afd59017b804d8fb555ada78e3329d1c4f5e",
]
EXPECTED_LOO_EXACT = 773
EXPECTED_FULL_EXACT = 784
EXPECTED_NULL_GE = 2


def grayscale_patches():
    eye = load_eyes()[0][:, :, 0]
    return np.stack(
        [eye[my * 7:(my + 1) * 7, mx * 7:(mx + 1) * 7]
         for my, mx in white_ring_modules()]
    )


def variant_atlas(patches):
    groups = []
    for module, patch in zip(white_ring_modules(), patches):
        for group in groups:
            if np.array_equal(group["patch"], patch):
                group["modules"].append(module)
                break
        else:
            groups.append({"patch": patch.copy(), "modules": [module]})
    return [
        {
            "variant": index + 1,
            "sha256": hashlib.sha256(group["patch"].tobytes()).hexdigest(),
            "modules": group["modules"],
            "multiplicity": len(group["modules"]),
            "fafafa_count": int(np.sum(group["patch"] == 250)),
            "values": [int(v) for v in np.unique(group["patch"])],
            "rows": [[int(v) for v in row] for row in group["patch"]],
        }
        for index, group in enumerate(groups)
    ]


def design_matrix(modules):
    """Intercept + row 2..5 indicators + column 2..5 indicators.

    Row 1 and column 1 are reference levels.  This is a fixed nine-parameter
    additive design for each subpixel; no interaction or position lookup is
    allowed.
    """
    return np.asarray([
        [1.0]
        + [float(my == row) for row in range(2, 6)]
        + [float(mx == col) for col in range(2, 6)]
        for my, mx in modules
    ])


def predict_scores(train_modules, train_patches, test_modules):
    x_train = design_matrix(train_modules)
    x_test = design_matrix(test_modules)
    coefficients = np.linalg.pinv(x_train) @ train_patches.reshape(len(train_modules), -1)
    return (x_test @ coefficients).reshape(len(test_modules), 7, 7)


def predict_bits(train_modules, train_patches, test_modules):
    return predict_scores(train_modules, train_patches, test_modules) >= 0.5


def cross_validate(patches):
    modules = white_ring_modules()
    actual, predicted, folds = [], [], []
    for held_index, held_module in enumerate(modules):
        train_modules = [m for i, m in enumerate(modules) if i != held_index]
        train_patches = np.delete(patches, held_index, axis=0)
        pred = predict_bits(train_modules, train_patches, [held_module])[0]
        truth = patches[held_index]
        errors = list(zip(*np.where(pred != truth)))
        folds.append({
            "held_out_module": held_module,
            "exact": int(49 - len(errors)),
            "errors": [[int(y), int(x)] for y, x in errors],
        })
        actual.append(truth)
        predicted.append(pred)
    actual = np.stack(actual)
    predicted = np.stack(predicted)
    return {
        "exact": int(np.sum(actual == predicted)),
        "total": int(actual.size),
        "accuracy": float(np.mean(actual == predicted)),
        "folds": folds,
    }


def fit_and_predict_center(patches):
    modules = white_ring_modules()
    fitted = predict_bits(modules, patches, modules)
    center_modules = [(my, mx) for my in range(2, 5) for mx in range(2, 5)]
    center_scores = predict_scores(modules, patches, center_modules)
    center = center_scores >= 0.5
    return {
        "observed_fit_exact": int(np.sum(fitted == patches)),
        "observed_fit_total": int(patches.size),
        "center_modules": center_modules,
        "center_patches": center,
        "center_scores": center_scores,
        "center_fafafa_count": int(center.sum()),
        "center_distinct_patches": len({patch.tobytes() for patch in center}),
    }


def permutation_calibration(patches, trials=NULL_TRIALS):
    real = cross_validate(patches)["exact"]
    rng = np.random.default_rng(NULL_SEED)
    null = []
    for _ in range(trials):
        null.append(cross_validate(patches[rng.permutation(len(patches))])["exact"])
    null = np.asarray(null)
    return {
        "real_exact": real,
        "null_trials": trials,
        "null_seed": NULL_SEED,
        "null_mean": float(null.mean()),
        "null_min": int(null.min()),
        "null_max": int(null.max()),
        "null_ge_real": int(np.sum(null >= real)),
        "p_ge_real": float((1 + np.sum(null >= real)) / (trials + 1)),
    }


def report(trials=NULL_TRIALS):
    gray = grayscale_patches()
    bits = gray == 250
    center = fit_and_predict_center(bits)
    return {
        "source": str(IMAGE_PATH.relative_to(REPO_ROOT)),
        "source_sha256": sha256_of(IMAGE_PATH),
        "variant_atlas": variant_atlas(gray),
        "model": "per-subpixel intercept + module-row effect + module-column effect; threshold 0.5",
        "cross_validation": cross_validate(bits),
        "calibration": permutation_calibration(bits, trials),
        "full_observed_fit": {
            "exact": center["observed_fit_exact"],
            "total": center["observed_fit_total"],
        },
        "counterfactual_center": {
            "modules": center["center_modules"],
            "fafafa_count": center["center_fafafa_count"],
            "distinct_patches": center["center_distinct_patches"],
            "rows_by_module": [
                ["".join("1" if value else "0" for value in row) for row in patch]
                for patch in center["center_patches"]
            ],
            "warning": "model-derived prediction; the real black center provides no observations",
        },
    }


def render_center_prediction(path=OUTPUT_IMAGE):
    gray = grayscale_patches()
    bits = gray == 250
    center = fit_and_predict_center(bits)
    real_eye = load_eyes()[0].copy()
    predicted_eye = real_eye.copy()
    for (my, mx), patch in zip(center["center_modules"], center["center_patches"]):
        values = np.where(patch, 250, 255).astype(np.uint8)
        predicted_eye[my * 7:(my + 1) * 7, mx * 7:(mx + 1) * 7] = values[:, :, None]

    scale = 9
    panel_w, panel_h = 49 * scale, 49 * scale
    margin, title_h, footer_h, gap = 28, 54, 62, 38
    canvas = Image.new("RGB", (margin * 2 + panel_w * 3 + gap * 2,
                               margin * 2 + title_h + panel_h + footer_h), "white")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    false_color = np.full_like(predicted_eye, 255)
    luminance = predicted_eye[:, :, 0]
    false_color[luminance == 0] = (25, 25, 25)
    false_color[luminance == 250] = (20, 135, 230)
    unusual = ~np.isin(luminance, (0, 250, 255))
    false_color[unusual] = (245, 145, 35)
    panels = [
        ("Observed finder (black center)", real_eye),
        ("Row + column model prediction", predicted_eye),
        ("False color: blue = exact #FAFAFA", false_color),
    ]
    for index, (title, array) in enumerate(panels):
        x = margin + index * (panel_w + gap)
        y = margin + title_h
        enlarged = Image.fromarray(array).resize((panel_w, panel_h), Image.Resampling.NEAREST)
        canvas.paste(enlarged, (x, y))
        draw.text((x, margin + 16), title, fill="black", font=font)
        for module_line in range(8):
            position = module_line * 7 * scale
            draw.line((x + position, y, x + position, y + panel_h), fill=(210, 60, 60), width=1)
            draw.line((x, y + position, x + panel_w, y + position), fill=(210, 60, 60), width=1)
    footer = ("Counterfactual only: predicted from the 16 observed white-ring modules. "
              "1 = exact #FAFAFA; predicted center is rendered as #FAFAFA/white.")
    draw.text((margin, margin + title_h + panel_h + 23), footer, fill="black", font=font)
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path)
    return path


def self_test():
    assert sha256_of(IMAGE_PATH) == EXPECTED_SHA256
    gray = grayscale_patches()
    assert gray.shape == (16, 7, 7)
    atlas = variant_atlas(gray)
    assert [v["multiplicity"] for v in atlas] == EXPECTED_VARIANT_MULTIPLICITIES
    assert [v["sha256"] for v in atlas] == EXPECTED_VARIANT_SHA256
    bits = gray == 250

    # A planted additive score field must be reconstructed exactly.
    modules = white_ring_modules()
    rng = np.random.default_rng(360)
    row_effect = rng.normal(0, 0.04, (5, 7, 7))
    col_effect = rng.normal(0, 0.04, (5, 7, 7))
    base = rng.choice([0.2, 0.8], (7, 7))
    planted = np.stack([(base + row_effect[my - 1] + col_effect[mx - 1]) >= 0.5
                        for my, mx in modules])
    assert fit_and_predict_center(planted)["observed_fit_exact"] == 16 * 49

    real_cv = cross_validate(bits)
    assert real_cv["exact"] == EXPECTED_LOO_EXACT
    assert all(y == 2 for fold in real_cv["folds"] for y, _ in fold["errors"])
    center = fit_and_predict_center(bits)
    assert center["observed_fit_exact"] == EXPECTED_FULL_EXACT
    assert center["center_fafafa_count"] == 210
    assert center["center_distinct_patches"] == 2
    calibration = permutation_calibration(bits)
    assert calibration["null_ge_real"] == EXPECTED_NULL_GE
    print("[*] self-test OK: source and six exact grayscale variants pinned; planted additive "
          "model fits exactly; real binary atlas fits 784/784 in-sample and 773/784 held-out; "
          "all 11 held-out errors are on subpixel row 2; deterministic null pinned.")


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
        result["rendered"] = str(render_center_prediction().relative_to(REPO_ROOT))
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        cv = result["cross_validation"]
        cal = result["calibration"]
        center = result["counterfactual_center"]
        print(f"[*] variants={len(result['variant_atlas'])} multiplicities="
              f"{[v['multiplicity'] for v in result['variant_atlas']]}")
        print(f"[*] held-out={cv['exact']}/{cv['total']} ({cv['accuracy']:.4%}); "
              f"null mean={cal['null_mean']:.3f}, range={cal['null_min']}..{cal['null_max']}, "
              f"p={cal['p_ge_real']:.6f}")
        print(f"[*] full observed fit={result['full_observed_fit']['exact']}/"
              f"{result['full_observed_fit']['total']}; predicted center #FAFAFA="
              f"{center['fafafa_count']}/441 in {center['distinct_patches']} patches")
        if args.render:
            print(f"[*] rendered {result['rendered']}")


if __name__ == "__main__":
    main()
