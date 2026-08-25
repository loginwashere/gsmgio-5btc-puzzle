#!/usr/bin/env python3
"""Phase 413: localize and stress-test Phase 412's I0-vs-S0 signal.

Implements, without widening, the protocol frozen in:

    doc/Brainstorms/2026-08-25 - Phase 413 I0 vs S0 Signal Localization
    Pre-Registration.md

This is a diagnostic audit of an already-executed result (Phase 412's
topology contrast: I0 beats S0, macro_loss(S0)-macro_loss(I0)=0.0566564,
p_family=0.000599994), not a new cipher search. Five diagnostics:

  1. Letter/stream/fold decomposition of the observed contrast into
     macro-loss-unit cells, with a hard reconciliation invariant.
  2. Pooled-label permutation test (same-data corroboration, not
     independent confirmation).
  3. Nine leave-one-letter-out sensitivities under a true conditional
     K=8 refit, Bonferroni-corrected.
  4. b/e reported as ordinary rows of (3), not privileged.
  5. Per-fold direction check, descriptive except for its role as one
     of two frozen branch-decision gates.

This script generates no candidate text and runs no password/key oracle.
"""

import argparse
import json
import math
from pathlib import Path

import numpy as np

from data import DBBI, FAED
from phase412_dbbi_faed_generative_model_comparison_audit import (
    ALPHABET,
    K,
    KT_ALPHA,
    DBBI_LENGTH,
    FAED_LENGTH,
    DBBI_FOLDS,
    FAED_FOLDS,
    MODEL_INDEX,
    encode_stream,
    stream_fold_statistics,
    kt_unigram,
    score_models_batch,
    fit_full_generator,
    generate_from_fitted,
    generate_iid_batch,
)

BOOTSTRAP_TRIALS = 100_000
BATCH_SIZE = 512

PERMUTATION_THRESHOLD = 0.005
LOLO_FAMILY_THRESHOLD = 0.005
LOLO_BONFERRONI_FACTOR = 9

LOLO_DISTRIBUTED_MIN = 7
LOLO_LOCALIZED_MAX = 6
FOLD_DISTRIBUTED_MIN = 4
FOLD_LOCALIZED_MAX = 3

PERM_REAL_NULL_SEED = 0x413A0
PERM_POSITIVE_FIXTURE_GEN_SEED = 0x413A1
PERM_NEGATIVE_FIXTURE_GEN_SEED = 0x413A2
PERM_POSITIVE_NULL_SEED = 0x413A3
PERM_NEGATIVE_NULL_SEED = 0x413A4

LOLO_REAL_NULL_BASE_SEED = 0x413B0  # + L, L = 0..8
LOLO_FIXTURE_GEN_SEED = 0x413B9
LOLO_FIXTURE_NULL_BASE_SEED = 0x413C0  # + L, L = 0..8

LOLO_CONCENTRATION_DBBI_PROBS = np.array(
    [.50, .0625, .0625, .0625, .0625, .0625, .0625, .0625, .0625], dtype=np.float64
)
LOLO_CONCENTRATION_FAED_PROBS = np.full(K, 1.0 / K, dtype=np.float64)


# ---------------------------------------------------------------------------
# Diagnostic 1: letter / stream / fold decomposition
# ---------------------------------------------------------------------------

def decompose_topology(dbbi_values, faed_values):
    """Cell-level macro-loss decomposition of the S0-vs-I0 gap.

    Returns an array of shape (2, 5, K): [stream, fold, letter], each entry
    already weighted into macro-loss units (0.5/91 for DBBI, 0.5/570 for
    FAED), not raw bits.
    """
    dbbi_values = np.asarray(dbbi_values, dtype=np.int8)
    faed_values = np.asarray(faed_values, dtype=np.int8)
    dbbi_stats = stream_fold_statistics(dbbi_values[None, :], DBBI_FOLDS)
    faed_stats = stream_fold_statistics(faed_values[None, :], FAED_FOLDS)

    weight_dbbi = 0.5 / DBBI_LENGTH
    weight_faed = 0.5 / FAED_LENGTH
    cells = np.zeros((2, 5, K), dtype=np.float64)

    for fold_index, (dbbi_fold, faed_fold) in enumerate(zip(dbbi_stats, faed_stats)):
        shared_chars = dbbi_fold["train_chars"] + faed_fold["train_chars"]
        shared_unigram = kt_unigram(shared_chars)[0]
        dbbi_unigram = kt_unigram(dbbi_fold["train_chars"])[0]
        faed_unigram = kt_unigram(faed_fold["train_chars"])[0]

        dbbi_held = dbbi_fold["held_chars"][0]
        faed_held = faed_fold["held_chars"][0]

        cells[0, fold_index, :] = weight_dbbi * dbbi_held * np.log2(dbbi_unigram / shared_unigram)
        cells[1, fold_index, :] = weight_faed * faed_held * np.log2(faed_unigram / shared_unigram)

    return cells


def reconciliation_check(dbbi_values, faed_values, cells):
    """Hard assertion: cells must sum to exactly macro_loss(S0)-macro_loss(I0)."""
    scores = score_models_batch(dbbi_values[None, :], faed_values[None, :])
    macro = scores["macro_loss"][0]
    if not (macro[MODEL_INDEX["S0"]] <= macro[MODEL_INDEX["S1"]]):
        raise AssertionError("decomposition precondition violated: S0 does not win the shared pair")
    if not (macro[MODEL_INDEX["I0"]] <= macro[MODEL_INDEX["I1"]]):
        raise AssertionError("decomposition precondition violated: I0 does not win the independent pair")
    reference = float(macro[MODEL_INDEX["S0"]] - macro[MODEL_INDEX["I0"]])
    total = float(np.sum(cells))
    if not math.isclose(total, reference, rel_tol=0.0, abs_tol=1e-9):
        raise AssertionError(f"Diagnostic 1 reconciliation failed: {total} != {reference}")
    return reference


def concentration_ratio(values):
    positive = np.clip(np.asarray(values, dtype=np.float64), 0, None)
    total_positive = float(positive.sum())
    if total_positive <= 0:
        return {"ratio": 0.0, "top_index": None, "total_positive": 0.0}
    top_index = int(np.argmax(positive))
    return {
        "ratio": float(positive[top_index] / total_positive),
        "top_index": top_index,
        "total_positive": total_positive,
    }


def diagnostic1(dbbi_values, faed_values):
    cells = decompose_topology(dbbi_values, faed_values)
    reference = reconciliation_check(dbbi_values, faed_values, cells)

    letter_totals = cells.sum(axis=(0, 1))
    stream_totals = cells.sum(axis=(1, 2))
    fold_totals = cells.sum(axis=(0, 2))

    letter_concentration = concentration_ratio(letter_totals)
    if letter_concentration["top_index"] is not None:
        letter_concentration["top_letter"] = ALPHABET[letter_concentration["top_index"]]
    fold_concentration = concentration_ratio(fold_totals)

    return {
        "reconciliation_reference": reference,
        "letter_totals": {ALPHABET[i]: float(letter_totals[i]) for i in range(K)},
        "stream_totals": {"DBBI": float(stream_totals[0]), "FAED": float(stream_totals[1])},
        "fold_totals": [float(value) for value in fold_totals],
        "letter_concentration": letter_concentration,
        "fold_concentration": fold_concentration,
    }


# ---------------------------------------------------------------------------
# Diagnostic 2: pooled-label permutation test (same-data corroboration)
# ---------------------------------------------------------------------------

def unigram_bits(counts):
    counts = np.asarray(counts, dtype=np.float64)
    total = counts.sum()
    probs = (counts + KT_ALPHA) / (total + K * KT_ALPHA)
    return -float(np.sum(counts * np.log2(probs)))


def split_bits(pooled_codes, idx_a):
    mask = np.ones(len(pooled_codes), dtype=bool)
    mask[idx_a] = False
    counts_a = np.bincount(pooled_codes[idx_a], minlength=K).astype(np.float64)
    counts_b = np.bincount(pooled_codes[mask], minlength=K).astype(np.float64)
    return unigram_bits(counts_a) + unigram_bits(counts_b)


def permutation_test(pooled_codes, size_a, trials, seed):
    n = len(pooled_codes)
    counts_pooled = np.bincount(pooled_codes, minlength=K).astype(np.float64)
    bits_pooled = unigram_bits(counts_pooled)

    observed_idx = np.arange(size_a)
    observed_stat = bits_pooled - split_bits(pooled_codes, observed_idx)

    rng = np.random.default_rng(seed)
    null_values = np.empty(trials, dtype=np.float64)
    for trial in range(trials):
        idx_a = rng.choice(n, size=size_a, replace=False)
        null_values[trial] = bits_pooled - split_bits(pooled_codes, idx_a)

    as_large = int(np.count_nonzero(null_values >= observed_stat))
    p_raw = (1 + as_large) / (trials + 1)
    return {
        "observed": observed_stat,
        "as_large": as_large,
        "trials": trials,
        "seed": seed,
        "p_raw": p_raw,
        "p_family": p_raw,
        "significant": p_raw <= PERMUTATION_THRESHOLD,
        "null_median": float(np.median(null_values)),
    }


def make_pooled_fixture(dbbi_probs, faed_probs, seed):
    rng = np.random.default_rng(seed)
    dbbi = generate_iid_batch(rng, dbbi_probs, 1, DBBI_LENGTH)[0]
    faed = generate_iid_batch(rng, faed_probs, 1, FAED_LENGTH)[0]
    return np.concatenate([dbbi, faed])


# ---------------------------------------------------------------------------
# Diagnostic 3: nine leave-one-letter-out sensitivities, conditional K=8
# ---------------------------------------------------------------------------

def lolo_fold_bits(train_chars, held_chars, drop_letter):
    """K=8 conditional KT fit/score for one model's per-fold counts, batched."""
    keep = [c for c in range(K) if c != drop_letter]
    train8 = train_chars[:, keep]
    held8 = held_chars[:, keep]
    total = train8.sum(axis=1, keepdims=True)
    probs8 = (train8 + KT_ALPHA) / (total + (K - 1) * KT_ALPHA)
    return -np.sum(held8 * np.log2(probs8), axis=1)


def lolo_contrast_batch(dbbi_values, faed_values, drop_letter):
    dbbi_stats = stream_fold_statistics(dbbi_values, DBBI_FOLDS)
    faed_stats = stream_fold_statistics(faed_values, FAED_FOLDS)
    batch = dbbi_values.shape[0]

    dbbi_bits_s0 = np.zeros(batch, dtype=np.float64)
    dbbi_bits_i0 = np.zeros(batch, dtype=np.float64)
    faed_bits_s0 = np.zeros(batch, dtype=np.float64)
    faed_bits_i0 = np.zeros(batch, dtype=np.float64)

    for dbbi_fold, faed_fold in zip(dbbi_stats, faed_stats):
        pooled_train = dbbi_fold["train_chars"] + faed_fold["train_chars"]

        dbbi_bits_s0 += lolo_fold_bits(pooled_train, dbbi_fold["held_chars"], drop_letter)
        faed_bits_s0 += lolo_fold_bits(pooled_train, faed_fold["held_chars"], drop_letter)
        dbbi_bits_i0 += lolo_fold_bits(dbbi_fold["train_chars"], dbbi_fold["held_chars"], drop_letter)
        faed_bits_i0 += lolo_fold_bits(faed_fold["train_chars"], faed_fold["held_chars"], drop_letter)

    dbbi_length_l = DBBI_LENGTH - np.sum(dbbi_values == drop_letter, axis=1)
    faed_length_l = FAED_LENGTH - np.sum(faed_values == drop_letter, axis=1)
    if np.any(dbbi_length_l <= 0) or np.any(faed_length_l <= 0):
        raise AssertionError("LOLO removal emptied a stream; masking assumption violated")

    macro_s0 = 0.5 * (dbbi_bits_s0 / dbbi_length_l + faed_bits_s0 / faed_length_l)
    macro_i0 = 0.5 * (dbbi_bits_i0 / dbbi_length_l + faed_bits_i0 / faed_length_l)
    return macro_s0 - macro_i0


def lolo_bootstrap(dbbi_values, faed_values, drop_letter, observed, trials, seed, batch_size=BATCH_SIZE):
    # dbbi_values/faed_values always arrive here as a single-row batch
    # (shape (1, length)); fit_full_generator wants the plain 1-D stream.
    fitted = fit_full_generator(dbbi_values[0], faed_values[0], "S0")
    rng = np.random.default_rng(seed)
    null_values = np.empty(trials, dtype=np.float64)

    offset = 0
    while offset < trials:
        batch = min(batch_size, trials - offset)
        synthetic_dbbi, synthetic_faed = generate_from_fitted(rng, fitted, batch)
        null_values[offset:offset + batch] = lolo_contrast_batch(synthetic_dbbi, synthetic_faed, drop_letter)
        offset += batch

    as_large = int(np.count_nonzero(null_values >= observed))
    p_raw = (1 + as_large) / (trials + 1)
    p_family = min(1.0, LOLO_BONFERRONI_FACTOR * p_raw)
    positive_direction = observed > 0
    family_significant = p_family <= LOLO_FAMILY_THRESHOLD
    return {
        "letter": ALPHABET[drop_letter],
        "observed": float(observed),
        "as_large": as_large,
        "trials": trials,
        "seed": seed,
        "p_raw": p_raw,
        "p_family": p_family,
        "positive_direction": positive_direction,
        "family_significant": family_significant,
        "promoted": positive_direction and family_significant,
        "null_median": float(np.median(null_values)),
    }


def diagnostic3(dbbi_values, faed_values, trials, batch_size=BATCH_SIZE):
    dbbi_batch = dbbi_values[None, :]
    faed_batch = faed_values[None, :]
    rows = {}
    for drop_letter in range(K):
        observed = float(lolo_contrast_batch(dbbi_batch, faed_batch, drop_letter)[0])
        row = lolo_bootstrap(
            dbbi_batch, faed_batch, drop_letter, observed,
            trials, LOLO_REAL_NULL_BASE_SEED + drop_letter, batch_size,
        )
        rows[ALPHABET[drop_letter]] = row
    # Diagnostic 3's frozen promotion threshold is p_family_L <= 0.005 alone
    # (no separate direction gate, unlike Phase 412's two contrasts); "promoted"
    # additionally requires positive_direction as an informative field on each
    # row, but the preregistered significant_count uses family_significant.
    significant_count = sum(1 for row in rows.values() if row["family_significant"])
    return {"rows": rows, "significant_count": significant_count}


def lolo_fixture_check(trials, batch_size=BATCH_SIZE):
    rng = np.random.default_rng(LOLO_FIXTURE_GEN_SEED)
    dbbi = generate_iid_batch(rng, LOLO_CONCENTRATION_DBBI_PROBS, 1, DBBI_LENGTH)
    faed = generate_iid_batch(rng, LOLO_CONCENTRATION_FAED_PROBS, 1, FAED_LENGTH)
    rows = {}
    for drop_letter in range(K):
        observed = float(lolo_contrast_batch(dbbi, faed, drop_letter)[0])
        row = lolo_bootstrap(
            dbbi, faed, drop_letter, observed,
            trials, LOLO_FIXTURE_NULL_BASE_SEED + drop_letter, batch_size,
        )
        rows[ALPHABET[drop_letter]] = row
    a_row = rows[ALPHABET[0]]
    a_collapses = not a_row["family_significant"]
    others_significant = any(rows[ALPHABET[i]]["promoted"] for i in range(1, K))
    passes = a_collapses and others_significant
    return {"rows": rows, "a_collapses": a_collapses, "others_significant": others_significant, "passes_frozen_requirement": passes}


# ---------------------------------------------------------------------------
# Controls (three synthetic fixtures + Diagnostic 1's reconciliation invariant)
# ---------------------------------------------------------------------------

def controls(trials=BOOTSTRAP_TRIALS, batch_size=BATCH_SIZE):
    positive_pooled = make_pooled_fixture(
        np.array([.03, .28, .08, .04, .22, .10, .10, .09, .06]),
        np.array([.09, .08, .09, .08, .12, .10, .19, .10, .15]),
        PERM_POSITIVE_FIXTURE_GEN_SEED,
    )
    negative_pooled = make_pooled_fixture(
        np.array([.30, .20, .15, .10, .08, .06, .05, .04, .02]),
        np.array([.30, .20, .15, .10, .08, .06, .05, .04, .02]),
        PERM_NEGATIVE_FIXTURE_GEN_SEED,
    )
    positive_result = permutation_test(positive_pooled, DBBI_LENGTH, trials, PERM_POSITIVE_NULL_SEED)
    negative_result = permutation_test(negative_pooled, DBBI_LENGTH, trials, PERM_NEGATIVE_NULL_SEED)
    positive_result["passes_frozen_requirement"] = positive_result["significant"]
    negative_result["passes_frozen_requirement"] = not negative_result["significant"]

    lolo_fixture = lolo_fixture_check(trials, batch_size)

    for name, row in (("permutation_positive", positive_result), ("permutation_negative", negative_result), ("lolo_concentration", lolo_fixture)):
        if not row["passes_frozen_requirement"]:
            raise AssertionError(f"frozen fixture {name} failed; protocol stops without tuning")

    return {
        "permutation_positive": positive_result,
        "permutation_negative": negative_result,
        "lolo_concentration": lolo_fixture,
    }


def self_test(trials=BOOTSTRAP_TRIALS, batch_size=BATCH_SIZE):
    dbbi = encode_stream(DBBI)
    faed = encode_stream(FAED)
    reconciliation_reference = reconciliation_check(dbbi, faed, decompose_topology(dbbi, faed))
    planted = controls(trials=trials, batch_size=batch_size)
    print(
        "[*] self-test OK: reconciliation invariant holds "
        f"({reconciliation_reference:.6f}) and all three frozen fixtures passed "
        f"at {trials:,} bootstrap trials"
    )
    return {"reconciliation_reference": reconciliation_reference, "controls": planted}


# ---------------------------------------------------------------------------
# Audit driver
# ---------------------------------------------------------------------------

def classify_branch(lolo_significant_count, fold_agree_count):
    if lolo_significant_count >= LOLO_DISTRIBUTED_MIN and fold_agree_count >= FOLD_DISTRIBUTED_MIN:
        return "distributed"
    if lolo_significant_count <= LOLO_LOCALIZED_MAX and fold_agree_count <= FOLD_LOCALIZED_MAX:
        return "localized"
    return "mixed_inconclusive"


def audit(trials=BOOTSTRAP_TRIALS, batch_size=BATCH_SIZE):
    planted = controls(trials=trials, batch_size=batch_size)

    dbbi = encode_stream(DBBI)
    faed = encode_stream(FAED)

    diag1 = diagnostic1(dbbi, faed)

    pooled_real = np.concatenate([dbbi, faed])
    diag2 = permutation_test(pooled_real, DBBI_LENGTH, trials, PERM_REAL_NULL_SEED)

    diag3 = diagnostic3(dbbi, faed, trials, batch_size)

    overall_sign = 1 if diag1["reconciliation_reference"] > 0 else -1
    fold_agree_count = sum(1 for value in diag1["fold_totals"] if (value > 0) == (overall_sign > 0))
    diag5 = {"fold_signs": [value > 0 for value in diag1["fold_totals"]], "fold_agree_count": fold_agree_count}

    branch = classify_branch(diag3["significant_count"], fold_agree_count)

    if trials == BOOTSTRAP_TRIALS and batch_size == BATCH_SIZE:
        validate_authoritative_result(planted, diag1, diag2, diag3, diag5, branch)

    report = {
        "protocol": {
            "alphabet": ALPHABET,
            "kt_alpha": KT_ALPHA,
            "bootstrap_trials": trials,
            "lolo_bonferroni_factor": LOLO_BONFERRONI_FACTOR,
            "lolo_family_threshold": LOLO_FAMILY_THRESHOLD,
            "permutation_threshold": PERMUTATION_THRESHOLD,
            "lolo_distributed_min": LOLO_DISTRIBUTED_MIN,
            "lolo_localized_max": LOLO_LOCALIZED_MAX,
            "fold_distributed_min": FOLD_DISTRIBUTED_MIN,
            "fold_localized_max": FOLD_LOCALIZED_MAX,
        },
        "controls": planted,
        "diagnostic1": diag1,
        "diagnostic2": diag2,
        "diagnostic3": diag3,
        "diagnostic5": diag5,
        "branch": branch,
        "candidate_text_generated": False,
        "password_oracle_run": False,
    }
    return report


def validate_authoritative_result(planted, diag1, diag2, diag3, diag5, branch):
    """Pin the frozen-seed 100k result used by Phase 413's finding."""
    expected_control_as_large = {
        "permutation_positive": 0,
        "permutation_negative": 2303,
    }
    for name, expected in expected_control_as_large.items():
        row = planted[name]
        if not row["passes_frozen_requirement"]:
            raise AssertionError(f"authoritative control failed: {name}")
        if row["as_large"] != expected:
            raise AssertionError(f"control bootstrap drift: {name}")

    lolo_fixture = planted["lolo_concentration"]
    if not lolo_fixture["passes_frozen_requirement"]:
        raise AssertionError("authoritative LOLO concentration fixture failed")
    if lolo_fixture["rows"]["a"]["as_large"] != 99998:
        raise AssertionError("LOLO fixture letter-a bootstrap drift")

    if not math.isclose(diag1["reconciliation_reference"], 0.05665641280022804, rel_tol=0.0, abs_tol=1e-12):
        raise AssertionError("reconciliation reference drifted")
    expected_letter_totals = {
        "a": -0.016634774802114085,
        "b": 0.1517254685791458,
        "c": -0.01410947849402278,
        "d": -0.017846881750179733,
        "e": 0.04356888023831744,
        "f": -0.004471752359194301,
        "g": -0.03863298315204879,
        "h": -0.017915590002638117,
        "i": -0.029026475457037314,
    }
    for letter, expected in expected_letter_totals.items():
        if not math.isclose(diag1["letter_totals"][letter], expected, rel_tol=0.0, abs_tol=1e-12):
            raise AssertionError(f"letter total drift: {letter}")

    if diag2["as_large"] != 1:
        raise AssertionError("Diagnostic 2 permutation bootstrap drift")
    if not diag2["significant"]:
        raise AssertionError("Diagnostic 2 significance drifted")

    if diag3["significant_count"] != 5:
        raise AssertionError("Diagnostic 3 significant-letter count drifted")
    expected_lolo_as_large = {
        "a": 115, "b": 26208, "c": 1, "d": 41, "e": 35, "f": 9, "g": 59, "h": 8, "i": 91,
    }
    expected_lolo_promoted = {
        "a": False, "b": False, "c": True, "d": True, "e": True,
        "f": True, "g": False, "h": True, "i": False,
    }
    for letter, expected in expected_lolo_as_large.items():
        if diag3["rows"][letter]["as_large"] != expected:
            raise AssertionError(f"Diagnostic 3 bootstrap drift: {letter}")
        if diag3["rows"][letter]["promoted"] != expected_lolo_promoted[letter]:
            raise AssertionError(f"Diagnostic 3 promotion drift: {letter}")

    if diag5["fold_agree_count"] != 4:
        raise AssertionError("Diagnostic 5 fold-agreement count drifted")
    if diag5["fold_signs"] != [True, True, False, True, True]:
        raise AssertionError("Diagnostic 5 fold signs drifted")

    if branch != "mixed_inconclusive":
        raise AssertionError("authoritative branch classification drifted")


def json_default(value):
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    raise TypeError(f"cannot JSON-encode {type(value).__name__}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--trials", type=int, default=BOOTSTRAP_TRIALS)
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.self_test:
        report = self_test(args.trials, args.batch_size)
    else:
        report = audit(args.trials, args.batch_size)

    rendered = json.dumps(report, indent=2, sort_keys=True, default=json_default)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
        print(f"[*] wrote {args.output}")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
