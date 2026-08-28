#!/usr/bin/env python3
"""Explain the Phase-430 quadgram gain with frozen mechanical controls."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import statistics
from collections import Counter
from pathlib import Path

import phase431_bifid16_equivalence_class_audit as phase431
import phase432_bifid16_candidate_reviewer as phase432
from phase387_btcseed_kmodest_checkpoint_audit import load_quadgrams, quadgram_mean
from phase426_btcseed_heldout_continuation_structure_audit import (
    lag1_mutual_information,
    longest_repeated_substring,
    raw_deflate_saving,
)


TARGET = "BTCSEED"
TRIALS = 1_000
RANK_SAMPLES = 10_000
SEED = 0x433
ENGLISH_PATH = Path(__file__).resolve().parents[2] / "doc/GSMG_PHASE425_BTCSEED_FAMILYWIDE_SIGNIFICANCE_AUDIT.md"
ENGLISH_SOURCE_SHA256 = "126ebd33bbd1454de610c9bbd24064e134c9fc50cd3f11507d56a19dec10d5b5"
CANDIDATES = (
    ("phase430_rank_zero", 0, "DBIFHCEGAKLMNOPQRSTUVWXYZ", None),
    ("phase429_exact_winner", 1_013_932_382, "DBIFHCEGAKNMRUOPLSTWXYVQZ", -3815.068),
    ("phase432_snapshot_leader", 6_734_809_711_440, "DBIFKCENAMUHOGPLRSTQVWXYZ", -3507.5981),
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def score(text: str, logs: dict[str, float], floor: float) -> float:
    return quadgram_mean(text, logs, floor)


def inclusive_p(observed: float, null: list[float]) -> float:
    return (1 + sum(value >= observed for value in null)) / (len(null) + 1)


def summarize(null: list[float], observed: float) -> dict:
    ordered = sorted(null)
    return {
        "trials": len(null),
        "min": ordered[0],
        "median": statistics.median(ordered),
        "mean": statistics.fmean(ordered),
        "max": ordered[-1],
        "observed_inclusive_upper_p": inclusive_p(observed, null),
        "observed_exceeds_all_controls": observed > ordered[-1],
    }


def entropy(text: str) -> float:
    n = len(text)
    return -sum((count / n) * math.log2(count / n) for count in Counter(text).values())


def index_of_coincidence(text: str) -> float:
    counts = Counter(text)
    n = len(text)
    return sum(count * (count - 1) for count in counts.values()) / (n * (n - 1))


def profile(text: str, logs: dict[str, float], floor: float) -> dict:
    grams = [text[i:i + 4] for i in range(len(text) - 3)]
    counts = Counter(grams)
    contributions = []
    total_excess = 0.0
    floor_windows = 0
    for gram, count in counts.items():
        value = logs.get(gram, floor)
        if value == floor:
            floor_windows += count
        excess = (value - floor) * count
        total_excess += excess
        contributions.append({"quadgram": gram, "count": count,
                              "log10_probability": value,
                              "excess_over_floor_total": excess})
    contributions.sort(key=lambda row: (-row["excess_over_floor_total"], row["quadgram"]))
    return {
        "length": len(text),
        "quadgram_mean": score(text, logs, floor),
        "quadgram_total": sum(logs.get(gram, floor) for gram in grams),
        "unseen_floor_windows": floor_windows,
        "unseen_floor_fraction": floor_windows / len(grams),
        "alphabet_size": len(set(text)),
        "character_entropy_bits": entropy(text),
        "vowel_fraction": sum(ch in "AEIOU" for ch in text) / len(text),
        "index_of_coincidence": index_of_coincidence(text),
        "lag1_mutual_information_bits": lag1_mutual_information(text),
        "raw_deflate_saving": raw_deflate_saving(text),
        "longest_repeated_substring": longest_repeated_substring(text),
        "distinct_ngrams": {str(n): len({text[i:i+n] for i in range(len(text)-n+1)})
                            for n in range(1, 5)},
        "top_excess_quadgrams": contributions[:10],
        "top10_fraction_of_above_floor_score": (
            sum(row["excess_over_floor_total"] for row in contributions[:10]) / total_excess
            if total_excess else 0.0
        ),
    }


def exact_shuffle_scores(tail: str, rng: random.Random, count: int,
                         logs: dict[str, float], floor: float) -> list[float]:
    letters = list(tail)
    result = []
    for _ in range(count):
        rng.shuffle(letters)
        result.append(score("".join(letters), logs, floor))
    return result


def digraph_shuffle_scores(tail: str, rng: random.Random, count: int,
                           logs: dict[str, float], floor: float) -> list[float]:
    singleton, digraphs = tail[0], [tail[i:i + 2] for i in range(1, len(tail), 2)]
    result = []
    for _ in range(count):
        rng.shuffle(digraphs)
        result.append(score(singleton + "".join(digraphs), logs, floor))
    return result


def conditional_square(square: str, rng: random.Random) -> str:
    g_position, h_position = square.index("G"), square.index("H")
    cells = [cell for cell in phase431.FREE_POSITIONS if cell not in {g_position, h_position}]
    symbols = list(phase431.OTHER_FREE_SYMBOLS)
    rng.shuffle(symbols)
    return phase431.square_for_placement(g_position, h_position, dict(zip(cells, symbols)))


def conditional_scores(square: str, rng: random.Random, count: int,
                       logs: dict[str, float], floor: float) -> list[float]:
    result = []
    for _ in range(count):
        decoded = phase431.decode_square(conditional_square(square, rng))
        assert decoded.startswith(TARGET)
        result.append(score(decoded[len(TARGET):], logs, floor))
    return result


def global_scores(rng: random.Random, count: int, logs: dict[str, float],
                  floor: float) -> list[float]:
    result = []
    for _ in range(count):
        rank = rng.randrange(phase431.TOTAL_RANKS)
        decoded = phase431.decode_square(phase432.square_for_rank(rank))
        assert decoded.startswith(TARGET)
        result.append(score(decoded[len(TARGET):], logs, floor))
    return result


def english_control() -> tuple[str, str]:
    raw = ENGLISH_PATH.read_bytes()
    if sha256(raw) != ENGLISH_SOURCE_SHA256:
        raise ValueError("pinned English source hash mismatch")
    normalized = "".join(chr(byte) for byte in raw.upper() if 65 <= byte <= 90).replace("J", "I")
    return normalized[:563], sha256(normalized[:563].encode("ascii"))


def audit(trials: int = TRIALS, rank_samples: int = RANK_SAMPLES) -> dict:
    if trials < 1 or rank_samples < 1:
        raise ValueError("control counts must be positive")
    logs, floor = load_quadgrams()
    english, english_hash = english_control()
    global_null = global_scores(random.Random(SEED ^ 0xA11), rank_samples, logs, floor)
    rows = []
    for index, (label, rank, square, frozen_gpu_total) in enumerate(CANDIDATES):
        decoded = phase431.decode_square(square)
        if not decoded.startswith(TARGET):
            raise ValueError(f"{label} does not preserve BTCSEED")
        tail = decoded[len(TARGET):]
        observed = score(tail, logs, floor)
        rng = random.Random(SEED + index)
        row = {
            "label": label,
            "rank": rank,
            "square": square,
            "decoded_sha256": sha256(decoded.encode("ascii")),
            "tail_prefix_72": tail[:72],
            "frozen_gpu_score_total": frozen_gpu_total,
            "profile": profile(tail, logs, floor),
            "controls": {
                "exact_multiset_shuffle": summarize(
                    exact_shuffle_scores(tail, rng, trials, logs, floor), observed),
                "intact_digraph_shuffle": summarize(
                    digraph_shuffle_scores(tail, rng, trials, logs, floor), observed),
                "conditional_same_g_h_placement": summarize(
                    conditional_scores(square, rng, rank_samples, logs, floor), observed),
                "uniform_global_rank": summarize(global_null, observed),
            },
        }
        rows.append(row)
    return {
        "phase": 433,
        "protocol": {"tail_start": 7, "shuffle_trials": trials,
                     "rank_samples": rank_samples, "seed": SEED,
                     "quadgram_floor": floor, "oracle_calls": 0},
        "english_control": {"source_path": str(ENGLISH_PATH),
                            "source_sha256": ENGLISH_SOURCE_SHA256,
                            "normalized_slice_sha256": english_hash,
                            "profile": profile(english, logs, floor)},
        "candidates": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=TRIALS)
    parser.add_argument("--rank-samples", type=int, default=RANK_SAMPLES)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.trials, args.rank_samples)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    args.output.write_text(rendered, encoding="utf-8")
    print(json.dumps({
        "english": result["english_control"]["profile"],
        "candidates": [{"label": row["label"], "profile": row["profile"],
                        "controls": row["controls"]} for row in result["candidates"]],
    }, indent=2))


if __name__ == "__main__":
    main()
