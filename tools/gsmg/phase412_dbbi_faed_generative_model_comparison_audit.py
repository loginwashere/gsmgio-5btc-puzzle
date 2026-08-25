#!/usr/bin/env python3
"""Phase 412: preregistered DBBI/FAED generative-model comparison.

Implements, without widening, the protocol frozen in:

    doc/Brainstorms/2026-08-25 - DBBI FAED Generative Model Comparison
    Pre-Registration.md

Five models (uniform IID, shared/independent KT-smoothed IID, and
shared/independent KT-smoothed first-order Markov) are compared by fixed
contiguous five-fold predictive loss.  Two one-sided contrasts are calibrated
with independent 100,000-replicate parametric bootstraps.  Four fully numeric
synthetic controls must recover their planted topology/order before the real
DBBI/FAED result may be interpreted.

This script generates no candidate text and runs no password/key oracle.
"""

import argparse
import json
import math
from pathlib import Path

import numpy as np

from data import DBBI, FAED


ALPHABET = "abcdefghi"
K = len(ALPHABET)
KT_ALPHA = 0.5
MODEL_NAMES = ("U0", "S0", "I0", "S1", "I1")
MODEL_INDEX = {name: index for index, name in enumerate(MODEL_NAMES)}

DBBI_LENGTH = 91
FAED_LENGTH = 570
DBBI_FOLD_SIZES = (19, 18, 18, 18, 18)
FAED_FOLD_SIZES = (114, 114, 114, 114, 114)

BOOTSTRAP_TRIALS = 100_000
FAMILY_THRESHOLD = 0.005
BATCH_SIZE = 512

REAL_TOPOLOGY_SEED = 0x412A0
REAL_MEMORY_SEED = 0x412A1
FIXTURE_GENERATION_BASE_SEED = 0x412B0
FIXTURE_BOOTSTRAP_BASE_SEED = 0x412C0

SHARED_IID_PROBS = np.array(
    [.30, .20, .15, .10, .08, .06, .05, .04, .02], dtype=np.float64
)
INDEPENDENT_IID_DBBI_PROBS = np.array(
    [.03, .28, .08, .04, .22, .10, .10, .09, .06], dtype=np.float64
)
INDEPENDENT_IID_FAED_PROBS = np.array(
    [.09, .08, .09, .08, .12, .10, .19, .10, .15], dtype=np.float64
)


def cyclic_transition_matrix(direction):
    """Return the frozen forward (+1) or reverse (-1) fixture matrix."""
    if direction not in (-1, 1):
        raise ValueError("direction must be -1 or +1")
    matrix = np.full((K, K), 0.10 / 7.0, dtype=np.float64)
    for row in range(K):
        matrix[row, row] = 0.55
        matrix[row, (row + direction) % K] = 0.35
    return matrix


FORWARD_MARKOV = cyclic_transition_matrix(1)
REVERSE_MARKOV = cyclic_transition_matrix(-1)
UNIFORM_PROBS = np.full(K, 1.0 / K, dtype=np.float64)


def fold_bounds(sizes):
    starts = np.cumsum((0,) + tuple(sizes[:-1]))
    ends = np.cumsum(sizes)
    return tuple((int(start), int(end)) for start, end in zip(starts, ends))


DBBI_FOLDS = fold_bounds(DBBI_FOLD_SIZES)
FAED_FOLDS = fold_bounds(FAED_FOLD_SIZES)


def encode_stream(text):
    invalid = sorted(set(text) - set(ALPHABET))
    if invalid:
        raise ValueError(f"symbols outside a-i: {invalid}")
    return np.fromiter((ord(ch) - ord("a") for ch in text), dtype=np.int8)


def categorical_rows(rng, probabilities):
    """Draw one categorical value per row of a probability matrix."""
    probabilities = np.asarray(probabilities, dtype=np.float64)
    if probabilities.ndim != 2 or probabilities.shape[1] != K:
        raise ValueError("probabilities must have shape (batch, 9)")
    draws = rng.random(probabilities.shape[0])
    cumulative = np.cumsum(probabilities, axis=1)
    cumulative[:, -1] = 1.0
    return np.sum(draws[:, None] > cumulative, axis=1).astype(np.int8)


def generate_iid_batch(rng, probabilities, batch, length):
    return rng.choice(K, size=(batch, length), p=probabilities).astype(np.int8)


def generate_markov_batch(rng, initial, transition, batch, length):
    initial = np.asarray(initial, dtype=np.float64)
    transition = np.asarray(transition, dtype=np.float64)
    if initial.shape != (K,) or transition.shape != (K, K):
        raise ValueError("invalid Markov generator shape")
    output = np.empty((batch, length), dtype=np.int8)
    output[:, 0] = rng.choice(K, size=batch, p=initial)
    for position in range(1, length):
        rows = transition[output[:, position - 1]]
        output[:, position] = categorical_rows(rng, rows)
    return output


def _counts(values, categories):
    """Vectorized categorical counts for each batch row."""
    values = np.asarray(values)
    if values.ndim != 2:
        raise ValueError("values must have shape (batch, observations)")
    batch = values.shape[0]
    offsets = np.arange(batch, dtype=np.int64)[:, None] * categories
    flat = (values.astype(np.int64) + offsets).ravel()
    return np.bincount(flat, minlength=batch * categories).reshape(batch, categories)


def _transition_counts(values):
    if values.shape[1] < 2:
        return np.zeros((values.shape[0], K * K), dtype=np.int64)
    codes = values[:, :-1].astype(np.int64) * K + values[:, 1:].astype(np.int64)
    return _counts(codes, K * K)


def stream_fold_statistics(values, folds):
    """Return sufficient statistics without introducing gap transitions."""
    values = np.asarray(values, dtype=np.int8)
    if values.ndim == 1:
        values = values[None, :]
    batch, length = values.shape
    if folds[-1][1] != length:
        raise ValueError("folds do not partition the stream")

    full_chars = _counts(values, K)
    full_transitions = _transition_counts(values)
    rows = []
    batch_indices = np.arange(batch)

    for start, end in folds:
        held = values[:, start:end]
        held_chars = _counts(held, K)
        held_transitions = _transition_counts(held)
        train_chars = full_chars - held_chars
        train_transitions = full_transitions - held_transitions

        # Remove the two real transitions that touch the held-out block.
        # They belong to neither surviving training chunk.
        if start > 0:
            left_code = values[:, start - 1].astype(np.int64) * K + values[:, start]
            train_transitions[batch_indices, left_code] -= 1
        if end < length:
            right_code = values[:, end - 1].astype(np.int64) * K + values[:, end]
            train_transitions[batch_indices, right_code] -= 1

        if np.any(train_chars < 0) or np.any(train_transitions < 0):
            raise AssertionError("negative sufficient statistic")
        rows.append({
            "start": start,
            "end": end,
            "first": held[:, 0].astype(np.int64),
            "held_chars": held_chars,
            "held_transitions": held_transitions,
            "train_chars": train_chars,
            "train_transitions": train_transitions,
        })
    return rows


def kt_unigram(counts):
    counts = np.asarray(counts, dtype=np.float64)
    return (counts + KT_ALPHA) / (
        np.sum(counts, axis=1, keepdims=True) + K * KT_ALPHA
    )


def kt_markov(flat_counts):
    counts = np.asarray(flat_counts, dtype=np.float64).reshape(-1, K, K)
    return (counts + KT_ALPHA) / (
        np.sum(counts, axis=2, keepdims=True) + K * KT_ALPHA
    )


def held_iid_bits(held_counts, probabilities):
    return -np.sum(held_counts * np.log2(probabilities), axis=1)


def held_markov_bits(first, held_transition_counts, initial_probs, transition_probs):
    batch_indices = np.arange(len(first))
    first_bits = -np.log2(initial_probs[batch_indices, first])
    transition_counts = held_transition_counts.reshape(-1, K, K)
    transition_bits = -np.sum(transition_counts * np.log2(transition_probs), axis=(1, 2))
    return first_bits + transition_bits


def score_models_batch(dbbi_values, faed_values, include_fold_details=False):
    """Run the exact five-fold scorer for one or more stream pairs."""
    dbbi_values = np.asarray(dbbi_values, dtype=np.int8)
    faed_values = np.asarray(faed_values, dtype=np.int8)
    if dbbi_values.ndim == 1:
        dbbi_values = dbbi_values[None, :]
    if faed_values.ndim == 1:
        faed_values = faed_values[None, :]
    if dbbi_values.shape[0] != faed_values.shape[0]:
        raise ValueError("DBBI/FAED batches differ")
    if dbbi_values.shape[1] != DBBI_LENGTH or faed_values.shape[1] != FAED_LENGTH:
        raise ValueError("source lengths differ from preregistration")

    batch = dbbi_values.shape[0]
    dbbi_stats = stream_fold_statistics(dbbi_values, DBBI_FOLDS)
    faed_stats = stream_fold_statistics(faed_values, FAED_FOLDS)
    total_bits = np.zeros((batch, len(MODEL_NAMES), 2), dtype=np.float64)
    fold_bits = []

    # U0 is fixed, so every character costs log2(9) bits.
    total_bits[:, MODEL_INDEX["U0"], 0] = DBBI_LENGTH * math.log2(K)
    total_bits[:, MODEL_INDEX["U0"], 1] = FAED_LENGTH * math.log2(K)

    for fold_index, (dbbi_fold, faed_fold) in enumerate(zip(dbbi_stats, faed_stats)):
        current = np.zeros((batch, len(MODEL_NAMES), 2), dtype=np.float64)
        current[:, MODEL_INDEX["U0"], 0] = (dbbi_fold["end"] - dbbi_fold["start"]) * math.log2(K)
        current[:, MODEL_INDEX["U0"], 1] = (faed_fold["end"] - faed_fold["start"]) * math.log2(K)

        # Shared and independent IID fits.
        shared_chars = dbbi_fold["train_chars"] + faed_fold["train_chars"]
        shared_unigram = kt_unigram(shared_chars)
        dbbi_unigram = kt_unigram(dbbi_fold["train_chars"])
        faed_unigram = kt_unigram(faed_fold["train_chars"])

        current[:, MODEL_INDEX["S0"], 0] = held_iid_bits(dbbi_fold["held_chars"], shared_unigram)
        current[:, MODEL_INDEX["S0"], 1] = held_iid_bits(faed_fold["held_chars"], shared_unigram)
        current[:, MODEL_INDEX["I0"], 0] = held_iid_bits(dbbi_fold["held_chars"], dbbi_unigram)
        current[:, MODEL_INDEX["I0"], 1] = held_iid_bits(faed_fold["held_chars"], faed_unigram)

        # Shared and independent first-order Markov fits.  The first held-out
        # symbol uses the corresponding IID topology's fitted unigram.
        shared_transitions = dbbi_fold["train_transitions"] + faed_fold["train_transitions"]
        shared_markov = kt_markov(shared_transitions)
        dbbi_markov = kt_markov(dbbi_fold["train_transitions"])
        faed_markov = kt_markov(faed_fold["train_transitions"])

        current[:, MODEL_INDEX["S1"], 0] = held_markov_bits(
            dbbi_fold["first"], dbbi_fold["held_transitions"], shared_unigram, shared_markov
        )
        current[:, MODEL_INDEX["S1"], 1] = held_markov_bits(
            faed_fold["first"], faed_fold["held_transitions"], shared_unigram, shared_markov
        )
        current[:, MODEL_INDEX["I1"], 0] = held_markov_bits(
            dbbi_fold["first"], dbbi_fold["held_transitions"], dbbi_unigram, dbbi_markov
        )
        current[:, MODEL_INDEX["I1"], 1] = held_markov_bits(
            faed_fold["first"], faed_fold["held_transitions"], faed_unigram, faed_markov
        )

        # U0 was already installed in total_bits; add only learned models.
        total_bits[:, 1:, :] += current[:, 1:, :]
        if include_fold_details:
            fold_bits.append(current)

    stream_bpc = total_bits / np.array([DBBI_LENGTH, FAED_LENGTH])[None, None, :]
    macro = 0.5 * np.sum(stream_bpc, axis=2)
    micro = np.sum(total_bits, axis=2) / (DBBI_LENGTH + FAED_LENGTH)
    result = {
        "total_bits": total_bits,
        "stream_bpc": stream_bpc,
        "macro_loss": macro,
        "micro_loss": micro,
    }
    if include_fold_details:
        result["fold_bits"] = np.stack(fold_bits, axis=1)
    return result


def contrasts_from_macro(macro):
    macro = np.asarray(macro, dtype=np.float64)
    if macro.ndim == 1:
        macro = macro[None, :]
    topology = np.minimum(macro[:, MODEL_INDEX["S0"]], macro[:, MODEL_INDEX["S1"]]) - np.minimum(
        macro[:, MODEL_INDEX["I0"]], macro[:, MODEL_INDEX["I1"]]
    )
    memory = np.minimum(macro[:, MODEL_INDEX["S0"]], macro[:, MODEL_INDEX["I0"]]) - np.minimum(
        macro[:, MODEL_INDEX["S1"]], macro[:, MODEL_INDEX["I1"]]
    )
    return {"topology": topology, "memory": memory}


def full_char_counts(values):
    values = np.asarray(values, dtype=np.int8)
    return np.bincount(values, minlength=K).astype(np.float64)


def full_transition_counts(values):
    values = np.asarray(values, dtype=np.int8)
    codes = values[:-1].astype(np.int64) * K + values[1:].astype(np.int64)
    return np.bincount(codes, minlength=K * K).reshape(K, K).astype(np.float64)


def fit_full_generator(dbbi_values, faed_values, model):
    dbbi_chars = full_char_counts(dbbi_values)
    faed_chars = full_char_counts(faed_values)
    if model == "S0":
        probs = (dbbi_chars + faed_chars + KT_ALPHA) / (
            DBBI_LENGTH + FAED_LENGTH + K * KT_ALPHA
        )
        return {"model": model, "dbbi_initial": probs, "faed_initial": probs}
    if model == "I0":
        dbbi_probs = (dbbi_chars + KT_ALPHA) / (DBBI_LENGTH + K * KT_ALPHA)
        faed_probs = (faed_chars + KT_ALPHA) / (FAED_LENGTH + K * KT_ALPHA)
        return {"model": model, "dbbi_initial": dbbi_probs, "faed_initial": faed_probs}
    if model == "S1":
        # Pool within-stream transitions only; never add a DBBI->FAED edge.
        transitions = full_transition_counts(dbbi_values) + full_transition_counts(faed_values)
        transition = (transitions + KT_ALPHA) / (
            np.sum(transitions, axis=1, keepdims=True) + K * KT_ALPHA
        )
        initial = (dbbi_chars + faed_chars + KT_ALPHA) / (
            DBBI_LENGTH + FAED_LENGTH + K * KT_ALPHA
        )
        return {
            "model": model,
            "dbbi_initial": initial,
            "faed_initial": initial,
            "dbbi_transition": transition,
            "faed_transition": transition,
        }
    raise ValueError(f"model {model} is not an allowed bootstrap generator")


def generate_from_fitted(rng, fitted, batch):
    model = fitted["model"]
    if model in ("S0", "I0"):
        return (
            generate_iid_batch(rng, fitted["dbbi_initial"], batch, DBBI_LENGTH),
            generate_iid_batch(rng, fitted["faed_initial"], batch, FAED_LENGTH),
        )
    if model == "S1":
        return (
            generate_markov_batch(
                rng, fitted["dbbi_initial"], fitted["dbbi_transition"], batch, DBBI_LENGTH
            ),
            generate_markov_batch(
                rng, fitted["faed_initial"], fitted["faed_transition"], batch, FAED_LENGTH
            ),
        )
    raise ValueError(f"unsupported fitted generator: {model}")


def select_null_models(macro_row):
    macro_row = np.asarray(macro_row, dtype=np.float64)
    topology = "S0" if macro_row[MODEL_INDEX["S0"]] <= macro_row[MODEL_INDEX["S1"]] else "S1"
    memory = "S0" if macro_row[MODEL_INDEX["S0"]] <= macro_row[MODEL_INDEX["I0"]] else "I0"
    return {"topology": topology, "memory": memory}


def bootstrap_contrast(
    dbbi_values,
    faed_values,
    observed_macro,
    contrast_name,
    trials,
    seed,
    batch_size=BATCH_SIZE,
):
    if contrast_name not in ("topology", "memory"):
        raise ValueError("unknown contrast")
    if trials < 1 or batch_size < 1:
        raise ValueError("trials and batch_size must be positive")

    null_models = select_null_models(observed_macro)
    selected = null_models[contrast_name]
    fitted = fit_full_generator(dbbi_values, faed_values, selected)
    observed = float(contrasts_from_macro(observed_macro)[contrast_name][0])
    rng = np.random.default_rng(seed)
    null_values = np.empty(trials, dtype=np.float64)

    offset = 0
    while offset < trials:
        batch = min(batch_size, trials - offset)
        synthetic_dbbi, synthetic_faed = generate_from_fitted(rng, fitted, batch)
        scores = score_models_batch(synthetic_dbbi, synthetic_faed)
        values = contrasts_from_macro(scores["macro_loss"])[contrast_name]
        null_values[offset : offset + batch] = values
        offset += batch

    as_large = int(np.count_nonzero(null_values >= observed))
    p_raw = (1 + as_large) / (trials + 1)
    p_family = min(1.0, 2.0 * p_raw)
    positive_direction = observed > 0
    family_significant = p_family <= FAMILY_THRESHOLD
    return {
        "contrast": contrast_name,
        "observed": observed,
        "null_model": selected,
        "trials": trials,
        "seed": seed,
        "as_large": as_large,
        "p_raw": p_raw,
        "p_family": p_family,
        "positive_direction": positive_direction,
        "family_significant": family_significant,
        "promoted": positive_direction and family_significant,
        "null_median": float(np.median(null_values)),
        "null_5th_percentile": float(np.quantile(null_values, 0.05)),
        "null_95th_percentile": float(np.quantile(null_values, 0.95)),
    }


def generate_fixture(index):
    rng = np.random.default_rng(FIXTURE_GENERATION_BASE_SEED + index)
    if index == 0:
        return (
            generate_iid_batch(rng, SHARED_IID_PROBS, 1, DBBI_LENGTH)[0],
            generate_iid_batch(rng, SHARED_IID_PROBS, 1, FAED_LENGTH)[0],
        )
    if index == 1:
        return (
            generate_iid_batch(rng, INDEPENDENT_IID_DBBI_PROBS, 1, DBBI_LENGTH)[0],
            generate_iid_batch(rng, INDEPENDENT_IID_FAED_PROBS, 1, FAED_LENGTH)[0],
        )
    if index == 2:
        return (
            generate_markov_batch(rng, UNIFORM_PROBS, FORWARD_MARKOV, 1, DBBI_LENGTH)[0],
            generate_markov_batch(rng, UNIFORM_PROBS, FORWARD_MARKOV, 1, FAED_LENGTH)[0],
        )
    if index == 3:
        return (
            generate_markov_batch(rng, UNIFORM_PROBS, FORWARD_MARKOV, 1, DBBI_LENGTH)[0],
            generate_markov_batch(rng, UNIFORM_PROBS, REVERSE_MARKOV, 1, FAED_LENGTH)[0],
        )
    raise ValueError("fixture index must be 0..3")


FIXTURE_NAMES = (
    "shared_iid",
    "independent_iid",
    "shared_markov",
    "independent_markov",
)


def summarize_scores(scores):
    macro = scores["macro_loss"][0]
    micro = scores["micro_loss"][0]
    total_bits = scores["total_bits"][0]
    stream_bpc = scores["stream_bpc"][0]
    result = {}
    for index, name in enumerate(MODEL_NAMES):
        result[name] = {
            "macro_loss": float(macro[index]),
            "micro_loss": float(micro[index]),
            "dbbi_total_bits": float(total_bits[index, 0]),
            "faed_total_bits": float(total_bits[index, 1]),
            "dbbi_bits_per_character": float(stream_bpc[index, 0]),
            "faed_bits_per_character": float(stream_bpc[index, 1]),
        }
    return result


def run_pair(dbbi_values, faed_values, topology_seed, memory_seed, trials, batch_size):
    scores = score_models_batch(dbbi_values, faed_values, include_fold_details=True)
    macro = scores["macro_loss"][0]
    contrasts = contrasts_from_macro(macro)
    topology = bootstrap_contrast(
        dbbi_values, faed_values, macro, "topology", trials, topology_seed, batch_size
    )
    memory = bootstrap_contrast(
        dbbi_values, faed_values, macro, "memory", trials, memory_seed, batch_size
    )
    fold_bits = scores["fold_bits"][0]
    return {
        "models": summarize_scores(scores),
        "fold_bits": {
            name: {
                "DBBI": [float(value) for value in fold_bits[:, index, 0]],
                "FAED": [float(value) for value in fold_bits[:, index, 1]],
            }
            for index, name in enumerate(MODEL_NAMES)
        },
        "contrasts": {
            "topology": topology,
            "memory": memory,
        },
        "selected_null_models": select_null_models(macro),
        "lowest_macro_model": MODEL_NAMES[int(np.argmin(macro))],
        "candidate_text_generated": False,
        "password_oracle_run": False,
    }


def fixture_passes(index, result):
    topology = result["contrasts"]["topology"]
    memory = result["contrasts"]["memory"]
    topology_independent = topology["promoted"]
    topology_shared_compatible = topology["observed"] <= 0 and not topology["family_significant"]
    memory_markov = memory["promoted"]
    if index == 0:
        return topology_shared_compatible
    if index == 1:
        return topology_independent
    if index == 2:
        return topology_shared_compatible and memory_markov
    if index == 3:
        return topology_independent and memory_markov
    raise ValueError("fixture index must be 0..3")


def validate_constants():
    probability_vectors = (
        SHARED_IID_PROBS,
        INDEPENDENT_IID_DBBI_PROBS,
        INDEPENDENT_IID_FAED_PROBS,
        UNIFORM_PROBS,
    )
    for vector in probability_vectors:
        if not np.isclose(np.sum(vector), 1.0, atol=1e-15):
            raise AssertionError(f"probability vector does not sum to one: {vector}")
    for matrix in (FORWARD_MARKOV, REVERSE_MARKOV):
        if not np.allclose(np.sum(matrix, axis=1), 1.0, atol=1e-15):
            raise AssertionError("transition row does not sum to one")
    if sum(DBBI_FOLD_SIZES) != DBBI_LENGTH or sum(FAED_FOLD_SIZES) != FAED_LENGTH:
        raise AssertionError("folds do not cover frozen lengths")
    if DBBI_FOLDS != ((0, 19), (19, 37), (37, 55), (55, 73), (73, 91)):
        raise AssertionError("DBBI fold boundaries drifted")
    if FAED_FOLDS != ((0, 114), (114, 228), (228, 342), (342, 456), (456, 570)):
        raise AssertionError("FAED fold boundaries drifted")


def unit_test():
    """Cheap implementation tests; does not replace frozen 100k controls."""
    validate_constants()
    # Exercise the scorer without touching the real streams.  The audit()
    # driver deliberately evaluates DBBI/FAED only after all four frozen
    # controls have passed.
    dbbi = (np.arange(DBBI_LENGTH, dtype=np.int64) % K).astype(np.int8)
    faed = ((2 * np.arange(FAED_LENGTH, dtype=np.int64) + 1) % K).astype(np.int8)
    scores = score_models_batch(dbbi, faed, include_fold_details=True)
    if scores["macro_loss"].shape != (1, 5):
        raise AssertionError("model score shape drifted")
    if scores["fold_bits"].shape != (1, 5, 5, 2):
        raise AssertionError("fold score shape drifted")
    expected_uniform = math.log2(K)
    if not np.allclose(scores["macro_loss"][0, MODEL_INDEX["U0"]], expected_uniform):
        raise AssertionError("uniform score drifted")

    # A no-gap transition-count identity on a small artificial stream.
    small = np.arange(DBBI_LENGTH, dtype=np.int64) % K
    stats = stream_fold_statistics(small.astype(np.int8), DBBI_FOLDS)
    for row in stats:
        expected_train_transitions = DBBI_LENGTH - 1
        expected_train_transitions -= (row["end"] - row["start"] - 1)
        expected_train_transitions -= int(row["start"] > 0)
        expected_train_transitions -= int(row["end"] < DBBI_LENGTH)
        if int(np.sum(row["train_transitions"])) != expected_train_transitions:
            raise AssertionError("gap transition leaked into training")
    return {
        "models": MODEL_NAMES,
        "dbbi_folds": DBBI_FOLDS,
        "faed_folds": FAED_FOLDS,
        "uniform_bits_per_character": expected_uniform,
    }


def controls(trials=BOOTSTRAP_TRIALS, batch_size=BATCH_SIZE):
    validate_constants()
    rows = {}
    for index, name in enumerate(FIXTURE_NAMES):
        dbbi, faed = generate_fixture(index)
        result = run_pair(
            dbbi,
            faed,
            FIXTURE_BOOTSTRAP_BASE_SEED + 2 * index,
            FIXTURE_BOOTSTRAP_BASE_SEED + 2 * index + 1,
            trials,
            batch_size,
        )
        result["passes_frozen_requirement"] = fixture_passes(index, result)
        rows[name] = result
        if not result["passes_frozen_requirement"]:
            raise AssertionError(
                f"frozen fixture {index} ({name}) failed; protocol stops without tuning"
            )
    return rows


def self_test(trials=BOOTSTRAP_TRIALS, batch_size=BATCH_SIZE):
    implementation = unit_test()
    planted = controls(trials=trials, batch_size=batch_size)
    print(
        "[*] self-test OK: five-model scorer and all four frozen synthetic "
        f"fixtures passed at {trials:,} bootstrap trials per contrast"
    )
    return {"implementation": implementation, "controls": planted}


def audit(trials=BOOTSTRAP_TRIALS, batch_size=BATCH_SIZE):
    implementation = unit_test()
    planted = controls(trials=trials, batch_size=batch_size)
    dbbi = encode_stream(DBBI)
    faed = encode_stream(FAED)
    real = run_pair(
        dbbi,
        faed,
        REAL_TOPOLOGY_SEED,
        REAL_MEMORY_SEED,
        trials,
        batch_size,
    )
    topology_promoted = real["contrasts"]["topology"]["promoted"]
    memory_promoted = real["contrasts"]["memory"]["promoted"]
    if topology_promoted and not memory_promoted:
        result_branch = "independent_iid_narrow_support_no_predictive_sequential_language"
    elif topology_promoted and memory_promoted:
        result_branch = "distinct_sequential_generators_followup_licensed"
    elif memory_promoted:
        result_branch = "predictive_memory_without_independent_topology"
    else:
        result_branch = "neither_contrast_promoted"

    report = {
        "protocol": {
            "alphabet": ALPHABET,
            "kt_alpha": KT_ALPHA,
            "models": MODEL_NAMES,
            "dbbi_length": DBBI_LENGTH,
            "faed_length": FAED_LENGTH,
            "dbbi_folds": DBBI_FOLDS,
            "faed_folds": FAED_FOLDS,
            "bootstrap_trials_per_contrast": trials,
            "family_threshold": FAMILY_THRESHOLD,
            "family_correction": "Bonferroni x2 across topology and memory",
            "computationally_held_out_not_historically_blind": True,
        },
        "implementation": implementation,
        "controls": planted,
        "real": real,
        "result_branch": result_branch,
        "candidate_text_generated": False,
        "password_oracle_run": False,
    }
    if trials == BOOTSTRAP_TRIALS and batch_size == BATCH_SIZE:
        validate_authoritative_result(report)
    return report


def validate_authoritative_result(report):
    """Pin the frozen-seed 100k result used by Phase 412's finding."""
    expected_control_counts = {
        "shared_iid": (94_794, 14_091),
        "independent_iid": (0, 85_602),
        "shared_markov": (95_251, 0),
        "independent_markov": (0, 0),
    }
    for name, (topology_count, memory_count) in expected_control_counts.items():
        row = report["controls"][name]
        if not row["passes_frozen_requirement"]:
            raise AssertionError(f"authoritative fixture failed: {name}")
        if row["contrasts"]["topology"]["as_large"] != topology_count:
            raise AssertionError(f"topology bootstrap drift: {name}")
        if row["contrasts"]["memory"]["as_large"] != memory_count:
            raise AssertionError(f"memory bootstrap drift: {name}")

    real = report["real"]
    expected_macro = {
        "U0": 3.169925001442312,
        "S0": 3.150640715979967,
        "I0": 3.093984303179739,
        "S1": 3.1840554681567736,
        "I1": 3.1004668791334957,
    }
    for name, expected in expected_macro.items():
        actual = real["models"][name]["macro_loss"]
        if not math.isclose(actual, expected, rel_tol=0.0, abs_tol=1e-12):
            raise AssertionError(f"real macro loss drift: {name}: {actual}")

    topology = real["contrasts"]["topology"]
    memory = real["contrasts"]["memory"]
    if topology["as_large"] != 29 or not topology["promoted"]:
        raise AssertionError("authoritative topology result drifted")
    if memory["as_large"] != 482 or memory["promoted"]:
        raise AssertionError("authoritative memory result drifted")
    if report["result_branch"] != "independent_iid_narrow_support_no_predictive_sequential_language":
        raise AssertionError("authoritative interpretation branch drifted")


def json_default(value):
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(f"cannot JSON-encode {type(value).__name__}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--unit-test", action="store_true")
    parser.add_argument("--trials", type=int, default=BOOTSTRAP_TRIALS)
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.unit_test:
        report = unit_test()
    elif args.self_test:
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
