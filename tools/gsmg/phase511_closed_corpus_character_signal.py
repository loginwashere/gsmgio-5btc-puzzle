#!/usr/bin/env python3
"""Phase 511: held-out closed-corpus character-model transfer diagnostic."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import os
from pathlib import Path

import phase510a_closed_vocabulary_manifest as phase510a
import phase510b_heldout_vocabulary_signal as phase510b
from quadgram_solver import load_quadgrams


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
PROTOCOL = (REPO_ROOT / "doc" / "Brainstorms" /
            "2026-09-15 - Phase 511 Closed-Corpus Character Model Protocol.md")
LOCK = SCRIPT_DIR / "phase511_execution_lock.json"
RESULT = SCRIPT_DIR / "phase511_result.json"
QUADGRAMS = SCRIPT_DIR / "data_files" / "english_quadgrams.txt"
EVALUATION_SOURCES = phase510b.EVALUATION_SOURCES
ORDERS = (2, 3)
ALPHA = 1.0
NULL_TRIALS = 200
NULL_SEED = 0x511C0DE


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normalized(value: bytes) -> str:
    return phase510b.normalized(value)


def training_documents(regions: dict[str, bytes], heldout: str) -> list[str]:
    return [normalized(regions[source]) for source in sorted(regions)
            if source != heldout]


def observed_coverage(training: list[str], test: str, order: int) -> float:
    seen = {text[index:index + order]
            for text in training
            for index in range(len(text) - order + 1)}
    windows = max(0, len(test) - order + 1)
    return (sum(test[index:index + order] in seen for index in range(windows)) /
            windows if windows else 0.0)


def train_markov(documents: list[str], order: int) -> tuple[dict[str, int], dict[str, int]]:
    if order < 2:
        raise ValueError("order must be at least two")
    contexts: collections.Counter[str] = collections.Counter()
    grams: collections.Counter[str] = collections.Counter()
    for text in documents:
        for index in range(len(text) - order + 1):
            gram = text[index:index + order]
            grams[gram] += 1
            contexts[gram[:-1]] += 1
    return dict(contexts), dict(grams)


def markov_score(text: str, order: int, model: tuple[dict[str, int], dict[str, int]]) -> float:
    contexts, grams = model
    windows = len(text) - order + 1
    if windows <= 0:
        raise ValueError("text too short for model order")
    total = 0.0
    for index in range(windows):
        gram = text[index:index + order]
        numerator = grams.get(gram, 0) + ALPHA
        denominator = contexts.get(gram[:-1], 0) + ALPHA * 26
        total += math.log10(numerator / denominator)
    return total / windows


def generic_quadgram_score(text: str, table: dict[str, float], floor: float) -> float:
    windows = len(text) - 3
    if windows <= 0:
        raise ValueError("text too short for quadgram model")
    return sum(table.get(text[index:index + 4].upper(), floor)
               for index in range(windows)) / windows


def zscores(values: list[float]) -> list[float]:
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    standard_deviation = math.sqrt(variance)
    if standard_deviation == 0.0:
        return [0.0] * len(values)
    return [(value - mean) / standard_deviation for value in values]


def shuffled_ensemble(text: str, fixture_index: int) -> list[str]:
    values = [text]
    for trial_index in range(NULL_TRIALS):
        chars = list(text)
        seed = phase510b.derive_seed(NULL_SEED, fixture_index, trial_index)
        phase510b.PCG32(seed).shuffle(chars)
        values.append("".join(chars))
    return values


def evaluate_fixture(source_id: str, fixture_index: int,
                     regions: dict[str, bytes], quadgrams: dict[str, float],
                     floor: float) -> dict:
    text = normalized(regions[source_id])
    training = training_documents(regions, source_id)
    sequences = shuffled_ensemble(text, fixture_index)
    order_rows = {}
    order_z = {}
    for order in ORDERS:
        model = train_markov(training, order)
        scores = [markov_score(sequence, order, model) for sequence in sequences]
        standardized = zscores(scores)
        order_z[order] = standardized
        order_rows[str(order)] = {
            "observed_heldout_coverage": observed_coverage(training, text, order),
            "real_mean_log10_probability": scores[0],
            "real_z": standardized[0],
        }
    family = [max(order_z[order][index] for order in ORDERS)
              for index in range(len(sequences))]
    generic_scores = [generic_quadgram_score(sequence, quadgrams, floor)
                      for sequence in sequences]
    generic_z = zscores(generic_scores)
    exceedances = sum(value >= family[0] for value in family[1:])
    transfer = exceedances == 0
    incremental = family[0] > generic_z[0]
    return {
        "source_id": source_id,
        "normalized_length": len(text),
        "training_document_lengths": [len(value) for value in training],
        "orders": order_rows,
        "real_family_z": family[0],
        "null_family_maxima": family[1:],
        "tie_inclusive_exceedances": exceedances,
        "add_one_p": (exceedances + 1) / (NULL_TRIALS + 1),
        "real_generic_quadgram_z": generic_z[0],
        "transfer_gate_passed": transfer,
        "incremental_value_gate_passed": incremental,
        "fixture_gate_passed": transfer and incremental,
    }


def lock_payload() -> dict:
    manifest = phase510a.validate_manifest()
    regions = phase510a.literal_regions()
    return {
        "phase": "511",
        "status": "locked_before_heldout_character_scoring",
        "files_sha256": {
            "protocol": sha(PROTOCOL),
            "runner": sha(Path(__file__)),
            "phase510a_builder": sha(Path(phase510a.__file__)),
            "phase510a_manifest": sha(phase510a.MANIFEST),
            "phase510b_runner": sha(Path(phase510b.__file__)),
            "generic_quadgrams": sha(QUADGRAMS),
        },
        "evaluation_sources": list(EVALUATION_SOURCES),
        "evaluation_region_sha256": {
            source: hashlib.sha256(regions[source]).hexdigest()
            for source in EVALUATION_SOURCES},
        "closed_corpus_source_count": manifest["source_count"],
        "normalization": "lowercase ASCII letters, each source kept separate",
        "orders": list(ORDERS),
        "model": "order-(n-1) Markov; add-one smoothing; 26 next letters; mean log10 probability",
        "family_statistic": "max order-2/order-3 symmetric ensemble z-score",
        "generic_comparator": "symmetric ensemble z-score of frozen English quadgram mean",
        "null": "200 exact-letter-multiset PCG32 Fisher-Yates shuffles per fixture",
        "null_trials": NULL_TRIALS,
        "null_seed": NULL_SEED,
        "ties_are_exceedances": True,
        "gate": "all fixtures: 0/200 family exceedances and real family z > real generic z",
        "faed_scored": False,
    }


def verify_lock() -> dict:
    if not LOCK.is_file():
        raise RuntimeError("Phase-511 execution lock is absent")
    actual = json.loads(LOCK.read_text())
    if actual != lock_payload():
        raise RuntimeError("Phase-511 execution lock mismatch")
    return actual


def atomic_json(path: Path, value: dict) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite {path}")
    temporary = path.with_suffix(path.suffix + ".tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def run() -> dict:
    verify_lock()
    if RESULT.exists():
        raise FileExistsError("refusing to repeat Phase 511")
    regions = phase510a.literal_regions()
    quadgrams, floor = load_quadgrams(QUADGRAMS)
    fixtures = [evaluate_fixture(source, index, regions, quadgrams, floor)
                for index, source in enumerate(EVALUATION_SOURCES)]
    passed = all(row["fixture_gate_passed"] for row in fixtures)
    result = {
        "phase": "511",
        "status": "heldout_character_signal_complete",
        "execution_lock_sha256": sha(LOCK),
        "faed_scored": False,
        "fixtures": fixtures,
        "gate_passed": passed,
        "verdict": ("licenses_separate_known_order_ceiling" if passed else
                    "closed_corpus_character_model_stops_before_faed"),
    }
    atomic_json(RESULT, result)
    return result


def self_test() -> dict:
    model = train_markov(["abababab"], 2)
    if markov_score("abab", 2, model) <= markov_score("aabb", 2, model):
        raise AssertionError("Markov scorer does not prefer the planted transitions")
    values = zscores([1.0, 2.0, 3.0])
    if abs(sum(values)) > 1e-12 or abs(sum(value * value for value in values) / 3 - 1) > 1e-12:
        raise AssertionError("z-score normalization failed")
    chars = shuffled_ensemble("aaabbbcccdddeee", 0)
    if len(chars) != 201 or any(sorted(value) != sorted(chars[0]) for value in chars):
        raise AssertionError("shuffle ensemble changed the letter multiset")
    regions = phase510a.literal_regions()
    expected = {
        "phase2_solved_plaintext": {2: 0.9111617312072893, 3: 0.4292237442922374},
        "phase3_literal_plaintext": {2: 0.8986866791744841, 3: 0.43609022556390975},
        "phase32_literal_plaintext": {2: 0.8656387665198237, 3: 0.41280353200883},
    }
    for source, by_order in expected.items():
        training = training_documents(regions, source)
        text = normalized(regions[source])
        for order, wanted in by_order.items():
            actual = observed_coverage(training, text, order)
            if abs(actual - wanted) > 1e-15:
                raise AssertionError(f"coverage changed for {source} order {order}: {actual}")
    return {"self_test": "pass", "orders": list(ORDERS),
            "fixtures": 3, "nulls_per_fixture": NULL_TRIALS}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--print-lock", action="store_true")
    group.add_argument("--verify-lock", action="store_true")
    group.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        value = self_test()
    elif args.print_lock:
        value = lock_payload()
    elif args.verify_lock:
        value = verify_lock()
    else:
        value = run()
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
