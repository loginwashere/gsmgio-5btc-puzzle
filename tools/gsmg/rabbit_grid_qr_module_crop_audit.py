#!/usr/bin/env python3
"""Is the Stage-0 14x14 grid (`follow_the_white_rabbit.png`) an enlarged crop
of the real embedded QR code in the footer of the same puzzle page
(`doc/img/gsmg_puzzle_stage1.png`)?

Both artifacts are real, independently confirmed structures in this
project's own material (grid_spiral.py's spiral decode; the QR's clean
decode to the blockchain.com prize address in
stage0_png_filter_anomaly_audit.py). This module asks a narrow, distinct
question: does the 14x14 grid's black/white pattern structurally match any
14x14 crop of the QR code's real 33x33 module matrix, under any of the 8
dihedral orientations?

Method: extract the QR's actual module matrix from the source PNG (not a
freshly-generated QR -- the real embedded one, straightened and thresholded
by OpenCV), extract the rabbit grid's per-cell majority color, then search
every possible 14x14 window x 8 orientations for the best match. A shuffled-
null control (same bit multiset, positions permuted) calibrates whether the
best real match is anything but chance -- a real "enlarged crop" would score
close to 100%, not cluster with random shuffles of its own bits.

Three cell-scoring variants for the grid's 24 non-black/white (blue/yellow)
cells are checked, since there is no a priori reason to prefer one:
  - "exclude": blue/yellow cells are not scored (172 of 196 cells compared).
  - "spiral_rule": blue=black(1), yellow=white(0) -- the polarity already
    established for these cells by grid_spiral.py's independent spiral
    decode of gsmg.io/theseedisplanted (196 cells compared).
  - "both_white": blue and yellow both scored as white(0) (196 cells
    compared) -- the naive alternative with no encoding assumption at all.
"""

import argparse
import hashlib
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from grid_spiral import BLACK, WHITE, BLUE, YELLOW, FEFE, N, load_grid  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE1_IMAGE = REPO_ROOT / "doc" / "img" / "gsmg_puzzle_stage1.png"
RABBIT_IMAGE = REPO_ROOT / "doc" / "img" / "gsmg_rabbit_hint.png"

EXPECTED_STAGE1_SHA256 = (
    "38125bbdf1ea58b9b30b075bc6bf71e4089d04bba37098317e47097e2f2a1830"
)
EXPECTED_RABBIT_SHA256 = (
    "5e8d84b88f8f829428df5d2a8bf36c7268346f169b799ac7570b6223990d204f"
)
EXPECTED_QR_PAYLOAD = (
    "https://www.blockchain.com/btc/address/1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe"
)
EXPECTED_QR_MODULE_SHAPE = (33, 33)
EXPECTED_QR_BLACK_COUNT = 547
EXPECTED_GRID_COUNTS = {"black": 86, "white": 86, "blue": 15, "yellow": 9}

NULL_TRIALS = 500
NULL_SEED = 20260821

VARIANT_EXPECTED = {
    "exclude": {"n_known": 172, "best_ratio": 107 / 172, "window": (3, 12), "t": 0,
                "null_mean": 0.6344, "p_max": 1.0},
    "spiral_rule": {"n_known": 196, "best_ratio": 122 / 196, "window": (11, 10), "t": 4,
                     "null_mean": 0.6261, "p_max": 1.0},
    "both_white": {"n_known": 196, "best_ratio": 123 / 196, "window": (12, 3), "t": 4,
                    "null_mean": 0.6249, "p_max": 1.0},
}


def sha256_of(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def get_qr_module_matrix(path=STAGE1_IMAGE):
    """Rectify and threshold the source PNG's real embedded QR code, returning
    its 33x33 module matrix as a 0/1 array (1 = black module). Mirrors the
    rectification already validated in stage0_png_filter_anomaly_audit.py."""
    image = cv2.imread(str(path))
    detector = cv2.QRCodeDetector()
    ok, points = detector.detect(image)
    assert ok, "QR code not detected in the source image"
    corners = points[0].astype(np.float32)
    size = 400
    destination = np.array(
        [[0, 0], [size, 0], [size, size], [0, size]], dtype=np.float32
    )
    matrix = cv2.getPerspectiveTransform(corners, destination)
    warped = cv2.warpPerspective(image, matrix, (size, size))
    gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
    padded = cv2.copyMakeBorder(thresh, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=255)
    bgr = cv2.cvtColor(padded, cv2.COLOR_GRAY2BGR)
    ok2, quad = detector.detect(bgr)
    assert ok2, "QR re-detection on the rectified crop failed"
    payload, straight = detector.decode(bgr, quad)
    assert payload == EXPECTED_QR_PAYLOAD, payload
    assert straight is not None and straight.shape == EXPECTED_QR_MODULE_SHAPE, straight.shape
    return (straight == 0).astype(np.int8)  # 1 = black module


def get_rabbit_color_grid(path=RABBIT_IMAGE):
    return load_grid(path)


def bits_for_variant(color_grid, variant):
    """Returns (bits, known_mask) where bits has -1 for unscored cells."""
    bits = np.zeros((N, N), dtype=np.int8)
    mask = np.ones((N, N), dtype=bool)
    for r in range(N):
        for c in range(N):
            px = color_grid[r][c]
            if px == BLACK:
                bits[r, c] = 1
            elif px in (WHITE, FEFE):
                bits[r, c] = 0
            elif px == BLUE:
                if variant == "exclude":
                    mask[r, c] = False
                elif variant == "spiral_rule":
                    bits[r, c] = 1
                elif variant == "both_white":
                    bits[r, c] = 0
            elif px == YELLOW:
                if variant == "exclude":
                    mask[r, c] = False
                else:
                    bits[r, c] = 0
            else:
                raise ValueError(f"unexpected grid color {px!r} at ({r},{c})")
    return bits, mask


def dihedral_transforms(mat):
    """8 symmetries of a square matrix: 4 rotations x optional horizontal flip."""
    out = []
    m = mat
    for _ in range(4):
        out.append(m)
        out.append(np.fliplr(m))
        m = np.rot90(m)
    return out


def best_match(qr_bits, bits, mask):
    qh, qw = qr_bits.shape
    n_known = int(mask.sum())
    best_ratio, best_r0, best_c0, best_t = -1.0, None, None, None
    for r0 in range(qh - N + 1):
        for c0 in range(qw - N + 1):
            window = qr_bits[r0 : r0 + N, c0 : c0 + N]
            for ti, tw in enumerate(dihedral_transforms(window)):
                matches = int(((tw == bits) & mask).sum())
                ratio = matches / n_known
                if ratio > best_ratio:
                    best_ratio, best_r0, best_c0, best_t = ratio, r0, c0, ti
    return best_ratio, best_r0, best_c0, best_t, n_known


def null_calibrate(qr_bits, bits, mask, trials=NULL_TRIALS, seed=NULL_SEED):
    """Shuffle the grid's own known bit values among their own positions
    (unknown/excluded positions held fixed) and re-run the full exhaustive
    search each time. Tests whether the real grid's best match beats what its
    own bit composition would produce by chance under any window/orientation."""
    rng = np.random.default_rng(seed)
    known_positions = np.argwhere(mask)
    known_values = bits[mask].copy()
    out = np.empty(trials)
    for t in range(trials):
        shuffled = bits.copy()
        perm = rng.permutation(known_values)
        for (pr, pc), val in zip(known_positions, perm):
            shuffled[pr, pc] = val
        ratio, *_ = best_match(qr_bits, shuffled, mask)
        out[t] = ratio
    return out


def run_variant(qr_bits, color_grid, variant, trials=NULL_TRIALS):
    bits, mask = bits_for_variant(color_grid, variant)
    ratio, r0, c0, t, n_known = best_match(qr_bits, bits, mask)
    null = null_calibrate(qr_bits, bits, mask, trials=trials)
    p_value = float((null >= ratio).sum() / len(null))
    return {
        "variant": variant,
        "n_known": n_known,
        "best_ratio": ratio,
        "best_matches": round(ratio * n_known),
        "window": (r0, c0),
        "transform": t,
        "null_mean": float(null.mean()),
        "null_min": float(null.min()),
        "null_max": float(null.max()),
        "p_value": p_value,
    }


def self_test():
    stage1_sha = sha256_of(STAGE1_IMAGE)
    assert stage1_sha == EXPECTED_STAGE1_SHA256, stage1_sha
    rabbit_sha = sha256_of(RABBIT_IMAGE)
    assert rabbit_sha == EXPECTED_RABBIT_SHA256, rabbit_sha

    qr_bits = get_qr_module_matrix()
    assert qr_bits.shape == EXPECTED_QR_MODULE_SHAPE, qr_bits.shape
    assert int(qr_bits.sum()) == EXPECTED_QR_BLACK_COUNT, int(qr_bits.sum())

    color_grid = get_rabbit_color_grid()
    counts = {"black": 0, "white": 0, "blue": 0, "yellow": 0}
    for r in range(N):
        for c in range(N):
            px = color_grid[r][c]
            if px == BLACK:
                counts["black"] += 1
            elif px in (WHITE, FEFE):
                counts["white"] += 1
            elif px == BLUE:
                counts["blue"] += 1
            elif px == YELLOW:
                counts["yellow"] += 1
    assert counts == EXPECTED_GRID_COUNTS, counts

    for variant, expected in VARIANT_EXPECTED.items():
        result = run_variant(qr_bits, color_grid, variant)
        assert result["n_known"] == expected["n_known"], (variant, result)
        assert abs(result["best_ratio"] - expected["best_ratio"]) < 1e-9, (variant, result)
        assert result["window"] == expected["window"], (variant, result)
        assert result["transform"] == expected["t"], (variant, result)
        # p-value uses a fixed seed so it is exactly reproducible; only assert
        # it stays clearly non-significant (this project's negative bar),
        # not the exact float, in case of numpy RNG-stream changes upstream.
        assert result["p_value"] > 0.05, (variant, result)

    print(
        "[*] self-test OK: source hashes pinned, QR module matrix (33x33, "
        f"{EXPECTED_QR_BLACK_COUNT} black modules) decodes to the expected "
        "blockchain.com payload, rabbit-grid color counts match, and all "
        "three blue/yellow-scoring variants reproduce their pinned best-"
        "match window/orientation/ratio with p > 0.05 against the shuffled-"
        "bit null."
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--trials", type=int, default=NULL_TRIALS)
    args = parser.parse_args()

    self_test()
    if args.self_test:
        return

    qr_bits = get_qr_module_matrix()
    color_grid = get_rabbit_color_grid()
    print(f"[*] QR module matrix: {qr_bits.shape}, black modules = {int(qr_bits.sum())}")

    for variant in ("exclude", "spiral_rule", "both_white"):
        result = run_variant(qr_bits, color_grid, variant, trials=args.trials)
        print(
            f"[*] variant={variant}: best={result['best_ratio']:.4f} "
            f"({result['best_matches']}/{result['n_known']}) "
            f"window={result['window']} transform#{result['transform']} | "
            f"null mean={result['null_mean']:.4f} "
            f"[{result['null_min']:.4f}, {result['null_max']:.4f}] "
            f"p={result['p_value']:.4f}"
        )


if __name__ == "__main__":
    main()
