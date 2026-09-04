#!/usr/bin/env python3
"""Phase 473: calibrated cyclic class association between DBBI and M91.

No derived texts, passwords, FAED, decryptions, or oracle calls. See the
frozen Phase 473 protocol.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from data import DBBI, VALIDATION_ANSWER
from phase472_dbbi_route_plaintext_alignment_audit import normalized_control_windows

SCRIPT_DIR = Path(__file__).resolve().parent
RESULT_PATH = SCRIPT_DIR / "phase473_result.json"

N = 91
N_NULL = 5000
BATCH_SIZE = 250
RNG_SEEDS = (473, 474, 475, 476, 477)
MODULI = (2, 3, 7, 9, 13)
REPRESENTATIONS = ("raw9", "be_binary")
FEATURES = ("vowel",) + tuple(f"mod{m}" for m in MODULI)
FAMILY_SIZE = len(REPRESENTATIONS) * len(FEATURES) * N
LEAD_ALPHA = 0.001


def plaintext_features(text: str) -> list[tuple[str, np.ndarray, int]]:
    if len(text) != N or not text.isupper() or not text.isalpha():
        raise AssertionError("plaintext target must be exactly 91 uppercase A-Z letters")
    a0 = np.fromiter((ord(c) - ord("A") for c in text), dtype=np.uint8, count=N)
    rows = [("vowel", np.fromiter((c in "AEIOU" for c in text), dtype=np.uint8, count=N), 2)]
    rows.extend((f"mod{m}", a0 % m, m) for m in MODULI)
    return rows


def representation_rows(symbol_rows: np.ndarray) -> list[tuple[str, np.ndarray, int]]:
    return [
        ("raw9", symbol_rows, 9),
        ("be_binary", np.isin(symbol_rows, (1, 4)).astype(np.uint8), 2),
    ]


def direct_mutual_information(x: np.ndarray, y: np.ndarray, kx: int, ky: int) -> float:
    counts = np.bincount(x.astype(int) * ky + y.astype(int), minlength=kx * ky).reshape(kx, ky)
    row = counts.sum(axis=1)
    column = counts.sum(axis=0)
    value = 0.0
    for i in range(kx):
        for j in range(ky):
            count = counts[i, j]
            if count:
                value += (count / N) * np.log((count * N) / (row[i] * column[j]))
    return float(value)


def fft_mi_offsets(x_rows: np.ndarray, y: np.ndarray, kx: int, ky: int) -> np.ndarray:
    """Return Bx91 MI; offset o pairs x[(i+o)%N] with y[i]."""
    onehot_x = (x_rows[:, None, :] == np.arange(kx, dtype=np.uint8)[None, :, None])
    onehot_y = (y[None, :] == np.arange(ky, dtype=np.uint8)[:, None])
    fx = np.fft.fft(onehot_x, axis=-1)
    fy = np.fft.fft(onehot_y, axis=-1)
    contingency = np.rint(
        np.fft.ifft(fx[:, :, None, :] * np.conj(fy[None, None, :, :]), axis=-1).real
    )
    row = contingency.sum(axis=2)[:, :, None, :]
    column = contingency.sum(axis=1)[:, None, :, :]
    denominator = row * column
    valid = contingency > 0
    ratio = np.ones_like(contingency, dtype=np.float64)
    ratio[valid] = contingency[valid] * N / denominator[valid]
    terms = np.zeros_like(contingency, dtype=np.float64)
    terms[valid] = (contingency[valid] / N) * np.log(ratio[valid])
    return terms.sum(axis=(1, 2))


def cell_labels() -> list[dict]:
    return [
        {"representation": rep, "plaintext_feature": feature, "offset": offset}
        for rep in REPRESENTATIONS
        for feature in FEATURES
        for offset in range(N)
    ]


def association_matrix(symbol_rows: np.ndarray, text: str) -> np.ndarray:
    if symbol_rows.ndim != 2 or symbol_rows.shape[1] != N:
        raise AssertionError("symbol matrix must be Bx91")
    blocks = []
    for _rep_name, represented, kx in representation_rows(symbol_rows):
        for _feature_name, feature, ky in plaintext_features(text):
            blocks.append(fft_mi_offsets(represented, feature, kx, ky))
    matrix = np.concatenate(blocks, axis=1)
    if matrix.shape != (symbol_rows.shape[0], FAMILY_SIZE):
        raise AssertionError(f"association family changed: {matrix.shape}")
    return matrix


def shuffled_symbol_matrix(seed: int) -> np.ndarray:
    base = np.fromiter((ord(c) - ord("a") for c in DBBI), dtype=np.uint8, count=N)
    rng = np.random.default_rng(seed)
    rows = np.empty((N_NULL, N), dtype=np.uint8)
    for i in range(N_NULL):
        rows[i] = rng.permutation(base)
    return rows


def evaluate_target(name: str, text: str, seed: int) -> dict:
    observed_symbols = np.fromiter((ord(c) - ord("a") for c in DBBI), dtype=np.uint8, count=N)[None, :]
    observed = association_matrix(observed_symbols, text)[0]
    null_symbols = shuffled_symbol_matrix(seed)
    null_parts = [
        association_matrix(null_symbols[start:start + BATCH_SIZE], text)
        for start in range(0, N_NULL, BATCH_SIZE)
    ]
    null = np.concatenate(null_parts, axis=0)
    means = null.mean(axis=0)
    sds = null.std(axis=0)
    usable = sds > 1e-12
    observed_z = np.zeros(FAMILY_SIZE, dtype=np.float64)
    null_z = np.zeros_like(null, dtype=np.float64)
    observed_z[usable] = (observed[usable] - means[usable]) / sds[usable]
    null_z[:, usable] = (null[:, usable] - means[usable]) / sds[usable]
    winner = int(np.argmax(observed_z))
    global_max = float(observed_z[winner])
    null_maxima = null_z.max(axis=1)
    global_exceedances = int(np.count_nonzero(null_maxima >= global_max))
    global_p = (1 + global_exceedances) / (N_NULL + 1)
    raw_exceedances = int(np.count_nonzero(null[:, winner] >= observed[winner]))
    raw_p = (1 + raw_exceedances) / (N_NULL + 1)
    labels = cell_labels()
    top_indices = sorted(
        range(FAMILY_SIZE),
        key=lambda i: (-float(observed_z[i]), labels[i]["representation"],
                       labels[i]["plaintext_feature"], labels[i]["offset"]),
    )[:20]
    return {
        "name": name,
        "text_sha256": hashlib.sha256(text.encode("ascii")).hexdigest(),
        "global_max_z": global_max,
        "global_null_exceedances": global_exceedances,
        "global_p_upper_plus_one": global_p,
        "null_max_min": float(null_maxima.min()),
        "null_max_max": float(null_maxima.max()),
        "null_max_mean": float(null_maxima.mean()),
        "null_max_sd": float(null_maxima.std()),
        "winning_cell": {
            **labels[winner],
            "raw_mi_nats": float(observed[winner]),
            "null_mean_mi": float(means[winner]),
            "null_sd_mi": float(sds[winner]),
            "z": global_max,
            "raw_mi_p_upper_plus_one": raw_p,
            "raw_mi_null_exceedances": raw_exceedances,
        },
        "top_cells": [
            {**labels[i], "raw_mi_nats": float(observed[i]), "z": float(observed_z[i])}
            for i in top_indices
        ],
    }


def build_report() -> dict:
    if len(DBBI) != N or set(DBBI) != set("abcdefghi") or len(VALIDATION_ANSWER) != N:
        raise AssertionError("canonical input changed")
    targets = [("real_validation_answer", VALIDATION_ANSWER)] + normalized_control_windows()
    evaluations = [evaluate_target(name, text, seed) for (name, text), seed in zip(targets, RNG_SEEDS)]
    real, controls = evaluations[0], evaluations[1:]
    gates = {
        "real_global_p_below_alpha": real["global_p_upper_plus_one"] < LEAD_ALPHA,
        "real_max_z_strictly_above_all_controls": all(
            real["global_max_z"] > control["global_max_z"] for control in controls
        ),
        "real_global_p_strictly_below_all_controls": all(
            real["global_p_upper_plus_one"] < control["global_p_upper_plus_one"]
            for control in controls
        ),
        "winning_raw_mi_p_below_alpha":
            real["winning_cell"]["raw_mi_p_upper_plus_one"] < LEAD_ALPHA,
    }
    gates["lead"] = all(gates.values())
    return {
        "phase": 473,
        "family_size": FAMILY_SIZE,
        "representations": list(REPRESENTATIONS),
        "plaintext_features": list(FEATURES),
        "cyclic_offsets": N,
        "n_null_per_target": N_NULL,
        "rng_seeds": list(RNG_SEEDS),
        "evaluations": evaluations,
        "decision_gates": gates,
        "phase474_heldout_validation_licensed": gates["lead"],
        "derived_texts_serialized": 0,
        "password_materials_generated": 0,
        "faed_uses": 0,
        "decryptions_attempted": 0,
        "oracle_calls": 0,
    }


def structural_self_test() -> None:
    assert FAMILY_SIZE == 1092
    assert len(cell_labels()) == len({
        (x["representation"], x["plaintext_feature"], x["offset"])
        for x in cell_labels()
    }) == FAMILY_SIZE
    base = np.fromiter((ord(c) - ord("a") for c in DBBI), dtype=np.uint8, count=N)
    feature_name, feature, ky = plaintext_features(VALIDATION_ANSWER)[2]  # mod3
    assert feature_name == "mod3"
    fft = fft_mi_offsets(base[None, :], feature, 9, ky)[0]
    direct = direct_mutual_information(base, feature, 9, ky)
    assert abs(float(fft[0]) - direct) < 1e-12
    shifted = np.roll(base, -17)
    assert abs(float(fft[17]) - direct_mutual_information(shifted, feature, 9, ky)) < 1e-12
    synthetic = np.tile(np.arange(3, dtype=np.uint8), 31)[:N]
    synthetic_feature = synthetic.copy()
    perfect = fft_mi_offsets(synthetic[None, :], synthetic_feature, 3, 3)[0]
    assert int(np.argmax(perfect)) in {0, 3, 6, 9, 12, 15, 18, 21, 24, 27, 30,
                                       33, 36, 39, 42, 45, 48, 51, 54, 57, 60,
                                       63, 66, 69, 72, 75, 78, 81, 84, 87, 90}
    assert abs(
        float(perfect[0])
        - direct_mutual_information(synthetic, synthetic_feature, 3, 3)
    ) < 1e-12


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=RESULT_PATH)
    parser.add_argument("--structural-only", action="store_true")
    args = parser.parse_args()
    structural_self_test()
    if args.structural_only:
        print("[*] Phase 473 structural self-test OK")
        return
    report = build_report()
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "family_size": report["family_size"],
        "evaluations": [
            {
                "name": row["name"],
                "global_max_z": row["global_max_z"],
                "global_p": row["global_p_upper_plus_one"],
                "winning_cell": row["winning_cell"],
            }
            for row in report["evaluations"]
        ],
        "decision_gates": report["decision_gates"],
    }, indent=2))


if __name__ == "__main__":
    main()
