#!/usr/bin/env python3
"""Calibrate the Stage-0 shadow/macro length nesting and FAED width 38.

This is a measurement audit, not a decoder.  It first extends the exact
pairwise-sum methodology of ``small_number_coincidence_calibration.py`` while
keeping the shadow measurements' algebraic dependencies explicit.  It then
tests every divisor of FAED's raw 570-symbol length as a grid width under four
predeclared row/column heterogeneity statistics and three controls:

* raw-symbol multiset shuffles;
* {g,i}-token-preserving shuffles;
* all 570 cyclic origins, preserving the circular symbol/digram sequence.

No plaintext, password, cipher, blob, or address oracle is used.
"""

import argparse
import itertools
import math
import random
import sys
from collections import Counter
from functools import lru_cache
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from data import DBBI, FAED  # noqa: E402
from small_number_coincidence_calibration import (  # noqa: E402
    ESTABLISHED_NUMBERS,
    pairwise_sum_hits,
)

ALPHABET = "abcdefghi"
ESCAPES = "gi"
DEFAULT_TRIALS = 2000
DEFAULT_SEED = 240

TOKENS = (
    ("matrixsumlist", 13),
    ("enter", 5),
    ("lastwordsbeforearchichoice", 26),
    ("thispassword", 12),
)
SHADOW_MEASUREMENTS = {
    38: "collapsed hex color #383838 -> 38",
    56: "the same channel byte 0x38 in decimal",
    25: "upper #383838 row sum",
    18: "lower #383838 row sum",
    43: "total #383838 pixel count (=25+18)",
}
EXTENDED_VALUES = {
    5: "len(enter)",
    12: "len(thispassword)",
    18: "len(matrixsumlist+enter); lower shadow row sum",
    25: "upper shadow row sum",
    26: "len(lastwordsbeforearchichoice)",
    38: "len(lastwordsbeforearchichoice+thispassword); collapsed #38",
    43: "len(enter+lastwordsbeforearchichoice+thispassword); shadow total",
    56: "full four-token length; 0x38 decimal",
}

METRICS = (
    "column_symbol_chi2",
    "row_symbol_chi2",
    "column_escape_chi2",
    "row_escape_chi2",
)


def contiguous_spans(values):
    return tuple(
        (start, end, sum(values[start:end]))
        for start in range(len(values))
        for end in range(start + 1, len(values) + 1)
    )


def numeric_calibration():
    lengths = tuple(length for _name, length in TOKENS)
    spans = contiguous_spans(lengths)
    span_values = tuple(value for _start, _end, value in spans)
    measurement_values = set(SHADOW_MEASUREMENTS)
    observed_hits = tuple(sorted(measurement_values & set(span_values)))

    permutation_rows = []
    exact_unlabeled_nested = []
    for permutation in itertools.permutations(lengths):
        values = {value for _start, _end, value in contiguous_spans(permutation)}
        hit_count = len(values & measurement_values)
        permutation_rows.append((permutation, hit_count))
        if (
            sum(permutation[:2]) == 18
            and sum(permutation[-2:]) == 38
            and sum(permutation[-3:]) == 43
            and sum(permutation) == 56
        ):
            exact_unlabeled_nested.append(permutation)

    extended_pool = dict(ESTABLISHED_NUMBERS)
    extended_pool.update(EXTENDED_VALUES)
    extended_hits = pairwise_sum_hits(extended_pool)
    total_pairs = math.comb(len(extended_pool), 2)

    factor_pairs_91 = tuple(
        (left, len(DBBI) // left)
        for left in range(1, math.isqrt(len(DBBI)) + 1)
        if len(DBBI) % left == 0
    )
    factor_pairs_570 = tuple(
        (left, len(FAED) // left)
        for left in range(1, math.isqrt(len(FAED)) + 1)
        if len(FAED) % left == 0
    )
    token_divisors = tuple(
        (name, length, len(FAED) // length)
        for name, length in TOKENS
        if len(FAED) % length == 0
    )
    return {
        "token_lengths": lengths,
        "contiguous_spans": spans,
        "span_values": span_values,
        "all_span_values_distinct": len(set(span_values)) == len(span_values),
        "shadow_measurement_span_hits": observed_hits,
        "shadow_measurement_span_hit_count": len(observed_hits),
        "permutation_hit_count_distribution": dict(Counter(
            hit_count for _permutation, hit_count in permutation_rows
        )),
        "permutations_with_at_least_four_hits": sum(
            hit_count >= 4 for _permutation, hit_count in permutation_rows
        ),
        "exact_unlabeled_nested_permutations": tuple(exact_unlabeled_nested),
        "exact_unlabeled_nested_rate": len(exact_unlabeled_nested) / math.factorial(4),
        "base_pool": {
            "size": len(ESTABLISHED_NUMBERS),
            "pairs": math.comb(len(ESTABLISHED_NUMBERS), 2),
            "hits": len(pairwise_sum_hits(ESTABLISHED_NUMBERS)),
        },
        "extended_pool": {
            "size": len(extended_pool),
            "pairs": total_pairs,
            "hits": len(extended_hits),
            "hit_rate": len(extended_hits) / total_pairs,
            "rows": extended_hits,
        },
        "factor_pairs_91": factor_pairs_91,
        "factor_pairs_570": factor_pairs_570,
        "faed_token_divisors": token_divisors,
        "dependencies": (
            "38 and 56 are two representations of one color byte",
            "43 is forced by 25+18",
            "56 is the sum of the four token lengths",
            "91=7x13 predates this comparison",
        ),
    }


def segment_gi_tokens(text):
    tokens = []
    index = 0
    while index < len(text):
        width = 2 if text[index] in ESCAPES else 1
        token = text[index:index + width]
        if len(token) != width:
            raise ValueError("dangling FAED escape")
        tokens.append(token)
        index += width
    return tuple(tokens)


def encoded(text):
    lookup = {character: index for index, character in enumerate(ALPHABET)}
    return tuple(lookup[character] for character in text)


def symbol_chi2(groups, global_counts):
    total = 0.0
    for group in groups:
        for symbol in range(len(ALPHABET)):
            expected = global_counts[symbol] / len(groups)
            total += (group[symbol] - expected) ** 2 / expected
    return total


def subset_chi2(groups, global_counts, selected_symbols):
    expected = sum(global_counts[symbol] for symbol in selected_symbols) / len(groups)
    return sum(
        (sum(group[symbol] for symbol in selected_symbols) - expected) ** 2 / expected
        for group in groups
    )


def grid_metrics(symbols, width, global_counts):
    row_count = len(symbols) // width
    columns = [[0] * len(ALPHABET) for _ in range(width)]
    rows = [[0] * len(ALPHABET) for _ in range(row_count)]
    for index, symbol in enumerate(symbols):
        columns[index % width][symbol] += 1
        rows[index // width][symbol] += 1
    escape_symbols = tuple(ALPHABET.index(character) for character in ESCAPES)
    return (
        symbol_chi2(columns, global_counts),
        symbol_chi2(rows, global_counts),
        subset_chi2(columns, global_counts, escape_symbols),
        subset_chi2(rows, global_counts, escape_symbols),
    )


def null_exceedances(real, widths, trials, seed, kind):
    rng = random.Random(seed)
    source = list(encoded(FAED))
    global_counts = Counter(source)
    token_source = list(segment_gi_tokens(FAED))
    encoded_tokens = [encoded(token) for token in token_source]
    exceedances = {(width, metric): 0 for width in widths for metric in range(len(METRICS))}

    for _trial in range(trials):
        if kind == "raw":
            rng.shuffle(source)
            sample = tuple(source)
        elif kind == "gi_token":
            rng.shuffle(encoded_tokens)
            sample = tuple(symbol for token in encoded_tokens for symbol in token)
        else:
            raise ValueError(kind)
        for width in widths:
            measured = grid_metrics(sample, width, global_counts)
            for metric, value in enumerate(measured):
                if value >= real[width][metric] - 1e-12:
                    exceedances[width, metric] += 1

    rows = {}
    family_size = len(widths) * len(METRICS)
    for width in widths:
        p_values = tuple(
            (exceedances[width, metric] + 1) / (trials + 1)
            for metric in range(len(METRICS))
        )
        rows[width] = {
            "p_values": dict(zip(METRICS, p_values)),
            "minimum_p": min(p_values),
            "minimum_bonferroni_p": min(1.0, min(p_values) * family_size),
        }
    return rows


def cyclic_origin_control(real, widths):
    source = encoded(FAED)
    global_counts = Counter(source)
    exceedances = {(width, metric): 0 for width in widths for metric in range(len(METRICS))}
    for offset in range(len(source)):
        sample = source[offset:] + source[:offset]
        for width in widths:
            measured = grid_metrics(sample, width, global_counts)
            for metric, value in enumerate(measured):
                if value >= real[width][metric] - 1e-12:
                    exceedances[width, metric] += 1
    family_size = len(widths) * len(METRICS)
    rows = {}
    for width in widths:
        p_values = tuple(
            exceedances[width, metric] / len(source)
            for metric in range(len(METRICS))
        )
        rows[width] = {
            "p_values": dict(zip(METRICS, p_values)),
            "minimum_p": min(p_values),
            "minimum_bonferroni_p": min(1.0, min(p_values) * family_size),
        }
    return rows


@lru_cache(maxsize=4)
def geometry_calibration(trials=DEFAULT_TRIALS, seed=DEFAULT_SEED):
    widths = tuple(divisor for divisor in range(1, len(FAED) + 1) if len(FAED) % divisor == 0)
    source = encoded(FAED)
    global_counts = Counter(source)
    real = {width: grid_metrics(source, width, global_counts) for width in widths}
    raw = null_exceedances(real, widths, trials, seed, "raw")
    token = null_exceedances(real, widths, trials, seed, "gi_token")
    cyclic = cyclic_origin_control(real, widths)
    rows = {}
    for width in widths:
        rows[width] = {
            "shape": (len(FAED) // width, width),
            "metrics": dict(zip(METRICS, real[width])),
            "raw_shuffle": raw[width],
            "gi_token_shuffle": token[width],
            "cyclic_origin": cyclic[width],
        }
    family_best = {}
    for control in ("raw_shuffle", "gi_token_shuffle", "cyclic_origin"):
        candidates = (
            (rows[width][control]["p_values"][metric], width, metric)
            for width in widths
            for metric in METRICS
        )
        p_value, width, metric = min(candidates)
        family_best[control] = {
            "width": width,
            "metric": metric,
            "uncorrected_p": p_value,
            "bonferroni_p": min(1.0, p_value * len(widths) * len(METRICS)),
        }
    return {
        "widths": widths,
        "factor_pair_count": len(widths) // 2,
        "orientation_count": len(widths),
        "metrics": METRICS,
        "family_size_per_null": len(widths) * len(METRICS),
        "trials": trials,
        "seed": seed,
        "gi_token_count": len(segment_gi_tokens(FAED)),
        "rows": rows,
        "family_best": family_best,
        "width_38_exceptional": all(
            rows[38][control]["minimum_bonferroni_p"] < 0.05
            for control in ("raw_shuffle", "gi_token_shuffle", "cyclic_origin")
        ),
        "any_family_corrected_hit": any(
            row[control]["minimum_bonferroni_p"] < 0.05
            for row in rows.values()
            for control in ("raw_shuffle", "gi_token_shuffle", "cyclic_origin")
        ),
    }


def audit(trials=DEFAULT_TRIALS, seed=DEFAULT_SEED):
    numeric = numeric_calibration()
    geometry = geometry_calibration(trials, seed)
    return {
        "numeric": numeric,
        "geometry": geometry,
        "gates": {
            "nested_length_identity_reproduced": numeric["shadow_measurement_span_hit_count"] == 4,
            "small_number_base_rate_low": False,
            "dbbi_13_factor_unique_nontrivial": numeric["factor_pairs_91"] == ((1, 91), (7, 13)),
            "faed_38_selected_by_length_alone": False,
            "faed_width_38_exceptional_under_controls": geometry["width_38_exceptional"],
            "decode_or_oracle_authorized": False,
        },
        "promoted": False,
    }


def self_test(trials=DEFAULT_TRIALS, seed=DEFAULT_SEED):
    report = audit(trials, seed)
    numeric = report["numeric"]
    assert numeric["token_lengths"] == (13, 5, 26, 12)
    assert numeric["span_values"] == (13, 18, 44, 56, 5, 31, 43, 26, 38, 12)
    assert numeric["all_span_values_distinct"]
    assert numeric["shadow_measurement_span_hits"] == (18, 38, 43, 56)
    assert numeric["permutation_hit_count_distribution"] == {4: 8, 2: 8, 3: 8}
    assert numeric["permutations_with_at_least_four_hits"] == 8
    assert numeric["exact_unlabeled_nested_permutations"] == (
        (13, 5, 26, 12), (13, 5, 12, 26),
    )
    assert numeric["extended_pool"]["size"] == 26
    assert numeric["extended_pool"]["pairs"] == 325
    assert numeric["extended_pool"]["hits"] == 44
    assert numeric["factor_pairs_570"] == (
        (1, 570), (2, 285), (3, 190), (5, 114),
        (6, 95), (10, 57), (15, 38), (19, 30),
    )
    assert numeric["faed_token_divisors"] == (
        ("enter", 5, 114),
    )
    geometry = report["geometry"]
    assert geometry["widths"] == (1, 2, 3, 5, 6, 10, 15, 19, 30, 38, 57, 95, 114, 190, 285, 570)
    assert geometry["gi_token_count"] == 436
    assert geometry["family_size_per_null"] == 64
    assert not geometry["width_38_exceptional"]
    assert not geometry["any_family_corrected_hit"]
    assert 0.03 < geometry["rows"][38]["raw_shuffle"]["minimum_p"] < 0.05
    assert 0.03 < geometry["rows"][38]["gi_token_shuffle"]["minimum_p"] < 0.05
    assert geometry["rows"][38]["cyclic_origin"]["minimum_p"] > 0.2
    assert geometry["rows"][5]["raw_shuffle"]["minimum_p"] < 0.05
    assert all(
        row["bonferroni_p"] >= 0.05
        for row in geometry["family_best"].values()
    )
    assert not report["gates"]["decode_or_oracle_authorized"]
    assert not report["promoted"]
    print(
        "[*] self-test OK: nested-length calibration and all-factor FAED "
        f"geometry reproduce ({trials} trials/null)"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=DEFAULT_TRIALS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.trials < 1:
        parser.error("--trials must be positive")
    report = audit(args.trials, args.seed)
    if args.self_test:
        self_test(args.trials, args.seed)
        return
    numeric = report["numeric"]
    geometry = report["geometry"]
    print(
        f"[*] extended small-number pool: {numeric['extended_pool']['hits']}/"
        f"{numeric['extended_pool']['pairs']} hits "
        f"({numeric['extended_pool']['hit_rate']:.1%})"
    )
    print(
        "[*] nested token-order control: "
        f"{numeric['permutations_with_at_least_four_hits']}/24 permutations "
        "retain >=4 measurement/span hits; "
        f"{len(numeric['exact_unlabeled_nested_permutations'])}/24 retain the exact nesting"
    )
    print(f"[*] FAED token divisors: {numeric['faed_token_divisors']}")
    print(f"[*] family-best corrected controls: {geometry['family_best']}")
    for width in (5, 38):
        row = geometry["rows"][width]
        print(f"[*] width {width}, shape {row['shape']}, metrics={row['metrics']}")
        for control in ("raw_shuffle", "gi_token_shuffle", "cyclic_origin"):
            print(f"    {control}: {row[control]}")
    print(
        "[*] verdict: nested identity retained as a recognition curiosity; "
        "width 38 is not geometrically exceptional; no decode/oracle authorized"
    )


if __name__ == "__main__":
    main()
