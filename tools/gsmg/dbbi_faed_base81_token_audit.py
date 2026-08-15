#!/usr/bin/env python3
"""Natural base-81 non-overlapping digraph-token audit for DBBI/FAED.

Pairs of a-i values become exact tokens 0..80.  FAED yields 285 tokens;
DBBI yields 45 and preserves one unpaired symbol.  High-first versus low-first
is proven to be a bijective token relabelling for the declared statistics.

Six structural measures per source are calibrated against independent raw-
symbol shuffles preserving the exact source profiles.  No ASCII offset,
homophonic substitution, crib placement, token lookup, or password oracle is
used unless this twelve-test gate survives family correction.
"""

import argparse
import json
import math
import random
from collections import Counter

from data import DBBI, FAED


ALPHABET = "abcdefghi"
METRIC_ALTERNATIVES = {
    "DBBI_pair_mutual_information": "high",
    "DBBI_token_index_of_coincidence": "high",
    "DBBI_max_token_multiplicity": "high",
    "DBBI_adjacent_token_repeats": "high",
    "DBBI_token_transition_mutual_information": "high",
    "DBBI_max_lag_repeat_rate": "high",
    "FAED_pair_mutual_information": "high",
    "FAED_token_index_of_coincidence": "high",
    "FAED_max_token_multiplicity": "high",
    "FAED_adjacent_token_repeats": "high",
    "FAED_token_transition_mutual_information": "high",
    "FAED_max_lag_repeat_rate": "high",
}
FAMILY_SIZE = len(METRIC_ALTERNATIVES)


def tokenize(stream, high_first=True):
    values = tuple(ord(symbol) - ord("a") for symbol in stream)
    usable = len(values) - len(values) % 2
    tokens = []
    pairs = []
    for index in range(0, usable, 2):
        first, second = values[index:index + 2]
        pairs.append((first, second))
        tokens.append(first * 9 + second if high_first else second * 9 + first)
    leftover = stream[usable:]
    return tuple(tokens), tuple(pairs), leftover


def mutual_information(pairs):
    if not pairs:
        return 0.0
    joint = Counter(pairs)
    first = Counter(left for left, _ in pairs)
    second = Counter(right for _, right in pairs)
    total = len(pairs)
    return sum(
        (count / total) * math.log2(
            (count / total)
            / ((first[left] / total) * (second[right] / total))
        )
        for (left, right), count in joint.items()
    )


def index_of_coincidence(values):
    length = len(values)
    if length < 2:
        return 0.0
    counts = Counter(values)
    return sum(count * (count - 1) for count in counts.values()) / (
        length * (length - 1)
    )


def transition_mutual_information(values):
    return mutual_information(tuple(zip(values, values[1:])))


def max_lag_repeat_rate(values, maximum_lag=40):
    if len(values) < 2:
        return {"rate": 0.0, "lag": None, "matches": 0, "opportunities": 0}
    maximum_lag = min(maximum_lag, len(values) // 2)
    rows = []
    for lag in range(1, maximum_lag + 1):
        opportunities = len(values) - lag
        matches = sum(
            values[index] == values[index + lag]
            for index in range(opportunities)
        )
        rows.append((matches / opportunities, lag, matches, opportunities))
    rate, lag, matches, opportunities = max(rows)
    return {
        "rate": rate,
        "lag": lag,
        "matches": matches,
        "opportunities": opportunities,
    }


def source_observation(stream, high_first=True):
    tokens, pairs, leftover = tokenize(stream, high_first)
    counts = Counter(tokens)
    lag = max_lag_repeat_rate(tokens)
    return {
        "tokens": tokens,
        "pairs": pairs,
        "leftover_symbol": leftover,
        "token_count": len(tokens),
        "distinct_token_count": len(counts),
        "top_tokens": tuple(sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:10]),
        "pair_mutual_information": mutual_information(pairs),
        "token_index_of_coincidence": index_of_coincidence(tokens),
        "max_token_multiplicity": max(counts.values(), default=0),
        "adjacent_token_repeats": sum(
            left == right for left, right in zip(tokens, tokens[1:])
        ),
        "token_transition_mutual_information": transition_mutual_information(tokens),
        "max_lag_repeat_rate": lag["rate"],
        "max_lag_detail": lag,
    }


def observation(dbbi, faed):
    sources = {
        "DBBI": source_observation(dbbi),
        "FAED": source_observation(faed),
    }
    metric_names = (
        "pair_mutual_information",
        "token_index_of_coincidence",
        "max_token_multiplicity",
        "adjacent_token_repeats",
        "token_transition_mutual_information",
        "max_lag_repeat_rate",
    )
    metrics = {
        f"{source}_{name}": row[name]
        for source, row in sources.items()
        for name in metric_names
    }
    if tuple(metrics) != tuple(METRIC_ALTERNATIVES):
        raise AssertionError("base-81 metric registry/order drifted")
    return {"sources": sources, "metrics": metrics}


def empirical_upper_p(observed, null_values):
    return (1 + sum(value >= observed for value in null_values)) / (
        len(null_values) + 1
    )


def null_calibration(observed, trials, seed):
    rng = random.Random(seed)
    shuffled_dbbi = list(DBBI)
    shuffled_faed = list(FAED)
    nulls = {name: [] for name in METRIC_ALTERNATIVES}
    for _ in range(trials):
        rng.shuffle(shuffled_dbbi)
        rng.shuffle(shuffled_faed)
        row = observation("".join(shuffled_dbbi), "".join(shuffled_faed))["metrics"]
        for name in nulls:
            nulls[name].append(row[name])
    rows = {}
    for name in METRIC_ALTERNATIVES:
        values = sorted(nulls[name])
        raw_p = empirical_upper_p(observed["metrics"][name], values)
        rows[name] = {
            "observed": observed["metrics"][name],
            "null_median": values[len(values) // 2],
            "null_95th_percentile": values[(95 * len(values)) // 100],
            "empirical_p": raw_p,
            "family_bonferroni_p": min(1.0, raw_p * FAMILY_SIZE),
        }
    return rows


def compact_source(row):
    return {
        key: value for key, value in row.items()
        if key not in ("tokens", "pairs")
    }


def audit(trials=20_000, seed=20260814):
    if trials < 1:
        raise ValueError("trials must be positive")
    observed = observation(DBBI, FAED)
    calibration = null_calibration(observed, trials, seed)
    family_p = min(row["family_bonferroni_p"] for row in calibration.values())
    threshold = 0.01

    orientation_invariant = {}
    for source, stream in (("DBBI", DBBI), ("FAED", FAED)):
        high = source_observation(stream, True)
        low = source_observation(stream, False)
        orientation_invariant[source] = all(
            high[name] == low[name]
            for name in (
                "pair_mutual_information",
                "token_index_of_coincidence",
                "max_token_multiplicity",
                "adjacent_token_repeats",
                "token_transition_mutual_information",
                "max_lag_repeat_rate",
            )
        )
    promoted = family_p < threshold
    return {
        "prior_repository_coverage": {
            "raw_base81_token_audits_before_this": 0,
            "checkerboard_digraphic_work_is_distinct": True,
        },
        "mapping": "token = 9*first + second, a=0..i=8",
        "orientation_structural_relabel_invariant": orientation_invariant,
        "sources": {
            source: compact_source(row)
            for source, row in observed["sources"].items()
        },
        "calibration": {
            "trials": trials,
            "seed": seed,
            "null_model": "independent raw-symbol shuffles preserving exact DBBI/FAED profiles before non-overlapping pairing",
            "metric_count": FAMILY_SIZE,
            "rows": calibration,
            "family_bonferroni_p_bound": family_p,
            "promotion_threshold": threshold,
            "promoted": promoted,
        },
        "homophonic_or_lookup_stage": {
            "authorized": promoted,
            "operations_run": 0,
            "reason": (
                "token gate passed; define a separately bounded consumer"
                if promoted else
                "token gate failed; no source-selected lookup or crib model is authorized"
            ),
        },
        "candidate_text_generated": False,
        "password_oracle_run": False,
    }


def self_test():
    tokens, pairs, leftover = tokenize("abice")
    assert tokens == (1, 74)
    assert pairs == ((0, 1), (8, 2))
    assert leftover == "e"
    high = source_observation(DBBI, True)
    low = source_observation(DBBI, False)
    assert high["token_count"] == low["token_count"] == 45
    assert high["leftover_symbol"] == low["leftover_symbol"] == DBBI[-1]
    assert high["token_index_of_coincidence"] == low["token_index_of_coincidence"]
    dependent = tuple((index, index) for index in range(9) for _ in range(3))
    independent = tuple((left, right) for left in range(9) for right in range(9))
    assert mutual_information(dependent) > mutual_information(independent)
    report = audit(trials=10)
    assert report["sources"]["DBBI"]["token_count"] == 45
    assert report["sources"]["FAED"]["token_count"] == 285
    assert report["calibration"]["metric_count"] == 12
    assert report["homophonic_or_lookup_stage"]["operations_run"] == 0
    assert not report["password_oracle_run"]
    print("[*] self-test OK: exact base-81 tokens, leftover, orientation invariance, and gate verified")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=20_000)
    parser.add_argument("--seed", type=int, default=20260814)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = self_test() if args.self_test else audit(args.trials, args.seed)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    for source, row in report["sources"].items():
        print(
            f"[*] {source}: tokens={row['token_count']} distinct={row['distinct_token_count']} "
            f"leftover={row['leftover_symbol']!r} top={row['top_tokens']}"
        )
    for name, row in report["calibration"]["rows"].items():
        print(
            f"    {name}: observed={row['observed']:.9g} "
            f"null_median={row['null_median']:.9g} "
            f"raw_p={row['empirical_p']:.6g} "
            f"corrected_p={row['family_bonferroni_p']:.6g}"
        )
    print(
        "[*] family p-bound:",
        f"{report['calibration']['family_bonferroni_p_bound']:.6g}",
        "promoted=" + str(report["calibration"]["promoted"]),
    )
    print("[*] consumer stage:", report["homophonic_or_lookup_stage"])
    print("[*] no candidate text or password oracle was used")


if __name__ == "__main__":
    main()

