#!/usr/bin/env python3
"""QR finder `#FAFAFA` full-mask tile predictability audit (2026-08-21).

Origin: `doc/Brainstorms/2026-08-21 - QR FAFAFA Full-Mask Pattern
Identification Brainstorm.md`, proposed experiment A1 + D3.

Question: can a small periodic binary tile learned from three predeclared ring
bands predict the fourth, or is the apparent 7/14-row structure no more
predictive than binary masks with the same per-band row and column sums?

Input is one exact 48x49 finder-square crop from the pinned Stage-0 PNG,
binarized by exact RGB equality to (250,250,250).  The other two finder eyes
are used only to assert byte identity, never as independent observations.

Four disjoint bands define the ring domain (finder-relative coordinates):
  top    y=7..13,  x=7..40   (7x34)
  bottom y=35..41, x=7..40   (7x34)
  left   y=14..34, x=7..12   (21x6)
  right  y=14..34, x=34..40  (21x7)

For every held-out band, tile height/width 1..14 and two non-leaking phase
models are selected using training data only:
  global     residue coordinates use absolute finder x/y;
  band_local residue coordinates reset at each predeclared band origin.

The tile cell is the training majority for its residue. Model selection uses
a frozen two-part MDL proxy: h*w literal tile bits plus the enumerative code
length log2(C(n, errors)) + log2(n+1) for residual positions/count. Ties are
resolved by (MDL, tile area, h, w, model order). The selected model predicts
the held-out band with no refit. Aggregate accuracy, balanced accuracy, and
Matthews correlation are reported over the four held-out predictions.

The originally proposed null preserved both row and column sums through 2x2
checkerboard switches. Pre-run self-test found zero legal switches in every
band: these masks are Ferrers-like enough that both projections freeze the
matrix, making that null identical to the real input. The corrected disclosed
control therefore uses two separate families: independently permute pixels
within every row (preserves every band row sum) and independently permute
pixels within every column (preserves every band column sum). Each control
undergoes the same tile/model selection and four-fold prediction as the real
mask. Results are reported separately; neither family is misrepresented as
preserving both projections.

The brainstorm's third proposed phase model, "per connected component", is
deliberately excluded: determining component boundaries requires seeing which
held-out pixels are `#FAFAFA`, leaking the target into the predictor. It can be
used descriptively later, but not as held-out evidence.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
IMAGE_PATH = REPO_ROOT / "doc" / "img" / "gsmg_puzzle_stage1.png"
EXPECTED_IMAGE_SHA256 = (
    "38125bbdf1ea58b9b30b075bc6bf71e4089d04bba37098317e47097e2f2a1830"
)
FAFAFA = np.array([250, 250, 250], dtype=np.uint8)
FINDER_BOXES = (
    (2, 1289, 49, 1337),
    (184, 1289, 231, 1337),
    (2, 1471, 49, 1519),
)
BANDS = {
    "top": (7, 14, 7, 41),
    "bottom": (35, 42, 7, 41),
    "left": (14, 35, 7, 13),
    "right": (14, 35, 34, 41),
}
MODELS = ("global", "band_local")
MAX_TILE = 14
NULL_TRIALS = 200
NULL_SEED = 20260821
EXPECTED_REAL_AGGREGATE = {"tp": 341, "tn": 380, "fp": 24, "fn": 4}
EXPECTED_FULL_TILE = "0000000111111111011101000100000000011111111000100"
EXPECTED_FULL_RESIDUAL_COUNT = 23


def sha256_of(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_finders():
    arr = np.array(Image.open(IMAGE_PATH).convert("RGB"))
    out = []
    for x0, y0, x1, y1 in FINDER_BOXES:
        out.append(arr[y0 : y1 + 1, x0 : x1 + 1])
    return out


def load_mask():
    finders = load_finders()
    assert all(np.array_equal(finders[0], f) for f in finders[1:])
    return np.all(finders[0] == FAFAFA, axis=2)


def band_points(mask, name):
    y0, y1, x0, x1 = BANDS[name]
    ys, xs = np.mgrid[y0:y1, x0:x1]
    return ys.ravel(), xs.ravel(), mask[y0:y1, x0:x1].ravel().astype(np.uint8)


def model_residues(ys, xs, band_names, h, w, model):
    if model == "global":
        return (ys % h) * w + (xs % w)
    if model != "band_local":
        raise ValueError(model)
    out = np.empty(len(ys), dtype=np.int32)
    for name in BANDS:
        take = band_names == name
        y0, _, x0, _ = BANDS[name]
        out[take] = ((ys[take] - y0) % h) * w + ((xs[take] - x0) % w)
    return out


def collect(mask, names):
    chunks = []
    for name in names:
        ys, xs, vals = band_points(mask, name)
        bands = np.full(len(ys), name, dtype=object)
        chunks.append((ys, xs, vals, bands))
    return tuple(np.concatenate([c[i] for c in chunks]) for i in range(4))


def mdl_bits(n, errors, tile_area):
    # Enumerative residual code: choose error count, then its positions.
    if errors < 0 or errors > n:
        raise ValueError((n, errors))
    choose = 0.0
    if 0 < errors < n:
        choose = (
            math.lgamma(n + 1) - math.lgamma(errors + 1)
            - math.lgamma(n - errors + 1)
        ) / math.log(2)
    return tile_area + math.log2(n + 1) + choose


def fit_candidate(ys, xs, vals, bands, h, w, model):
    residues = model_residues(ys, xs, bands, h, w, model)
    total = np.bincount(residues, minlength=h * w)
    ones = np.bincount(residues, weights=vals, minlength=h * w).astype(int)
    # Zero wins exact ties. This is fixed and conservative for the sparse mask.
    tile = (ones * 2 > total).astype(np.uint8)
    pred = tile[residues]
    errors = int(np.count_nonzero(pred != vals))
    return {
        "model": model,
        "h": h,
        "w": w,
        "tile": tile,
        "train_n": len(vals),
        "train_errors": errors,
        "mdl_bits": mdl_bits(len(vals), errors, h * w),
    }


def select_model(mask, train_names):
    ys, xs, vals, bands = collect(mask, train_names)
    candidates = []
    for model_i, model in enumerate(MODELS):
        for h in range(1, MAX_TILE + 1):
            for w in range(1, MAX_TILE + 1):
                fit = fit_candidate(ys, xs, vals, bands, h, w, model)
                fit["model_i"] = model_i
                candidates.append(fit)
    return min(
        candidates,
        key=lambda f: (f["mdl_bits"], f["h"] * f["w"], f["h"], f["w"], f["model_i"]),
    )


def predict_fit(fit, mask, names):
    ys, xs, vals, bands = collect(mask, names)
    residues = model_residues(ys, xs, bands, fit["h"], fit["w"], fit["model"])
    pred = fit["tile"][residues]
    return vals, pred, ys, xs, bands


def confusion_metrics(actual, pred):
    actual = np.asarray(actual, dtype=np.uint8)
    pred = np.asarray(pred, dtype=np.uint8)
    tp = int(np.sum((actual == 1) & (pred == 1)))
    tn = int(np.sum((actual == 0) & (pred == 0)))
    fp = int(np.sum((actual == 0) & (pred == 1)))
    fn = int(np.sum((actual == 1) & (pred == 0)))
    n = len(actual)
    accuracy = (tp + tn) / n
    tpr = tp / (tp + fn) if tp + fn else 0.0
    tnr = tn / (tn + fp) if tn + fp else 0.0
    balanced = (tpr + tnr) / 2
    denom = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    mcc = ((tp * tn - fp * fn) / denom) if denom else 0.0
    return {
        "n": n, "tp": tp, "tn": tn, "fp": fp, "fn": fn,
        "accuracy": accuracy, "balanced_accuracy": balanced, "mcc": mcc,
    }


def cross_validate(mask):
    fold_reports = []
    all_actual = []
    all_pred = []
    for held_out in BANDS:
        train = tuple(name for name in BANDS if name != held_out)
        fit = select_model(mask, train)
        actual, pred, ys, xs, _ = predict_fit(fit, mask, (held_out,))
        metrics = confusion_metrics(actual, pred)
        fold_reports.append({
            "held_out": held_out,
            "selected_model": fit["model"],
            "tile_h": fit["h"],
            "tile_w": fit["w"],
            "train_n": fit["train_n"],
            "train_errors": fit["train_errors"],
            "train_mdl_bits": fit["mdl_bits"],
            "heldout_metrics": metrics,
            "heldout_residual_coords": [
                [int(y), int(x)] for y, x, a, p in zip(ys, xs, actual, pred) if a != p
            ],
        })
        all_actual.append(actual)
        all_pred.append(pred)
    return {
        "folds": fold_reports,
        "aggregate": confusion_metrics(np.concatenate(all_actual), np.concatenate(all_pred)),
    }


def full_fit(mask):
    fit = select_model(mask, tuple(BANDS))
    actual, pred, ys, xs, _ = predict_fit(fit, mask, tuple(BANDS))
    residual = [[int(y), int(x)] for y, x, a, p in zip(ys, xs, actual, pred) if a != p]
    return {
        "model": fit["model"], "tile_h": fit["h"], "tile_w": fit["w"],
        "train_n": fit["train_n"], "errors": fit["train_errors"],
        "mdl_bits": fit["mdl_bits"], "metrics": confusion_metrics(actual, pred),
        "tile_bits_row_major": "".join(str(int(v)) for v in fit["tile"]),
        "residual_coords": residual,
    }


def shuffled_mask(mask, rng, preserve):
    if preserve not in ("row_sums", "column_sums"):
        raise ValueError(preserve)
    out = np.zeros_like(mask, dtype=bool)
    for name, (y0, y1, x0, x1) in BANDS.items():
        original = mask[y0:y1, x0:x1].astype(np.uint8)
        shuffled = original.copy()
        if preserve == "row_sums":
            for row in shuffled:
                rng.shuffle(row)
            assert np.array_equal(original.sum(axis=1), shuffled.sum(axis=1))
        else:
            for x in range(shuffled.shape[1]):
                rng.shuffle(shuffled[:, x])
            assert np.array_equal(original.sum(axis=0), shuffled.sum(axis=0))
        out[y0:y1, x0:x1] = shuffled.astype(bool)
    return out


def null_calibrate(mask, trials=NULL_TRIALS, seed=NULL_SEED):
    rng = np.random.default_rng(seed)
    families = {}
    for preserve in ("row_sums", "column_sums"):
        rows = []
        for _ in range(trials):
            control = shuffled_mask(mask, rng, preserve)
            cv = cross_validate(control)
            rows.append({
                "mcc": cv["aggregate"]["mcc"],
                "balanced_accuracy": cv["aggregate"]["balanced_accuracy"],
                "accuracy": cv["aggregate"]["accuracy"],
            })
        families[preserve] = rows
    return families


def summarize_null(real_cv, controls_by_family):
    out = {}
    for family, controls in controls_by_family.items():
        out[family] = {}
        for metric in ("mcc", "balanced_accuracy", "accuracy"):
            real = real_cv["aggregate"][metric]
            vals = np.array([row[metric] for row in controls], dtype=float)
            out[family][metric] = {
                "real": real,
                "null_mean": float(vals.mean()),
                "null_min": float(vals.min()),
                "null_max": float(vals.max()),
                "p_ge_real": float((1 + np.sum(vals >= real)) / (len(vals) + 1)),
            }
    return out


def run(trials=NULL_TRIALS):
    mask = load_mask()
    cv = cross_validate(mask)
    controls = null_calibrate(mask, trials=trials)
    return {
        "image_sha256": sha256_of(IMAGE_PATH),
        "finder_boxes": FINDER_BOXES,
        "fafafa_count_per_eye": int(mask.sum()),
        "ring_fafafa_count": int(sum(band_points(mask, n)[2].sum() for n in BANDS)),
        "cross_validation": cv,
        "full_fit": full_fit(mask),
        "null_trials": trials,
        "null_seed": NULL_SEED,
        "null_summary": summarize_null(cv, controls),
    }


def self_test():
    assert sha256_of(IMAGE_PATH) == EXPECTED_IMAGE_SHA256
    finders = load_finders()
    assert [f.shape for f in finders] == [(49, 48, 3)] * 3
    assert all(np.array_equal(finders[0], f) for f in finders[1:])
    mask = load_mask()
    assert int(mask.sum()) == 345
    assert int(sum(band_points(mask, n)[2].sum() for n in BANDS)) == 345

    # Corrected projection controls preserve exactly the projection they name.
    for preserve, axis in (("row_sums", 1), ("column_sums", 0)):
        shuffled = shuffled_mask(mask, np.random.default_rng(12345), preserve)
        for name, (y0, y1, x0, x1) in BANDS.items():
            a = mask[y0:y1, x0:x1]
            b = shuffled[y0:y1, x0:x1]
            assert np.array_equal(a.sum(axis), b.sum(axis))

    # A planted globally periodic mask must be predictably recovered.
    planted = np.zeros_like(mask)
    for name, (y0, y1, x0, x1) in BANDS.items():
        ys, xs = np.mgrid[y0:y1, x0:x1]
        planted[y0:y1, x0:x1] = ((ys % 4 == 0) | ((ys % 4 == 1) & (xs % 3 == 0)))
    planted_cv = cross_validate(planted)
    assert planted_cv["aggregate"]["mcc"] > 0.95, planted_cv["aggregate"]

    real_cv = cross_validate(mask)
    assert len(real_cv["folds"]) == 4
    assert real_cv["aggregate"]["n"] == 749
    assert all(
        (f["selected_model"], f["tile_h"], f["tile_w"]) == ("global", 7, 7)
        for f in real_cv["folds"]
    ), real_cv["folds"]
    for key, expected in EXPECTED_REAL_AGGREGATE.items():
        assert real_cv["aggregate"][key] == expected, real_cv["aggregate"]
    fitted = full_fit(mask)
    assert fitted["tile_bits_row_major"] == EXPECTED_FULL_TILE
    assert len(fitted["residual_coords"]) == EXPECTED_FULL_RESIDUAL_COUNT
    print(
        "[*] self-test OK: source hash and three identical eyes pinned; 345 "
        "#FAFAFA pixels exactly cover the four declared ring bands; corrected "
        "controls preserve their declared row or column projection; planted periodic "
        "positive recovers at MCC > 0.95; the real four-fold 7x7 global-tile "
        "selection, confusion counts, full tile, and 23-pixel residual are pinned."
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--trials", type=int, default=NULL_TRIALS)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    self_test()
    if args.self_test:
        return
    report = run(trials=args.trials)
    if args.json:
        print(json.dumps(report, indent=2))
        return
    print(f"[*] #FAFAFA pixels per eye/ring: {report['fafafa_count_per_eye']}")
    for fold in report["cross_validation"]["folds"]:
        m = fold["heldout_metrics"]
        print(
            f"[*] held_out={fold['held_out']}: {fold['selected_model']} "
            f"tile={fold['tile_h']}x{fold['tile_w']} "
            f"train_errors={fold['train_errors']}/{fold['train_n']} "
            f"heldout_acc={m['accuracy']:.4f} bal={m['balanced_accuracy']:.4f} "
            f"mcc={m['mcc']:.4f}"
        )
    print("[*] aggregate:", report["cross_validation"]["aggregate"])
    print("[*] full fit:", {k: v for k, v in report["full_fit"].items() if k not in ("residual_coords",)})
    print("[*] null summary:", report["null_summary"])


if __name__ == "__main__":
    main()
