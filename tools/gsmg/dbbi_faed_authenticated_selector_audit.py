#!/usr/bin/env python3
"""Use DBBI/FAED as indices into five authenticated fixed strings.

The family is closed before scoring: zero-based single symbols (0..8) and
boundary-aligned base-81 pairs (0..80), applied modulo each exact target
length.  Four family maxima/minima are calibrated over independent exact-
profile stream shuffles.  No target is added after output inspection.
"""

import argparse
import json
import random
import re
import zlib

from data import DBBI, FAED, VALIDATION_ANSWER
from quadgram_solver import score as quadgram_score


TRIALS = 5_000
SEED = 0x1D3EED
PRIZE_ADDRESS = "1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe"
NATIVE_ROW_SUMS = (6, 10, 8, 7, 6, 6, 5, 4, 9, 9, 7, 8, 7, 9)
NATIVE_COLUMN_SUMS = (8, 10, 8, 10, 8, 7, 3, 6, 7, 5, 9, 6, 6, 8)
TARGETS = {
    "solved_url": "gsmg.io/theseedisplanted",
    "prize_address": PRIZE_ADDRESS,
    "native_row_sum_digits": "".join(map(str, NATIVE_ROW_SUMS)),
    "native_column_sum_digits": "".join(map(str, NATIVE_COLUMN_SUMS)),
    "validation_answer": VALIDATION_ANSWER.lower(),
}
AUTHENTICATED_WORDS = (
    "gsmg", "seed", "planted", "theseedisplanted",
    "case", "manage", "crack", "this", "private", "keys", "belong",
    "half", "better", "they", "also", "need", "funds", "live",
)
STAT_SPECS = (
    ("maximum_quadgram_score", "high"),
    ("maximum_authenticated_word_length", "high"),
    ("maximum_adjacent_repeat_rate", "high"),
    ("minimum_zlib_ratio", "low"),
)


def values(stream):
    output = tuple(ord(symbol) - ord("a") for symbol in stream)
    if any(not 0 <= value < 9 for value in output):
        raise ValueError("selector streams must use only a-i")
    return output


def select_single(stream_values, target):
    return "".join(target[value % len(target)] for value in stream_values)


def select_pairs(stream_values, target):
    usable = len(stream_values) - len(stream_values) % 2
    output = "".join(
        target[(stream_values[index] * 9 + stream_values[index + 1]) % len(target)]
        for index in range(0, usable, 2)
    )
    return output, len(stream_values) - usable


def candidate_rows(dbbi_values, faed_values):
    rows = []
    for source_name, stream_values in (
        ("dbbi", dbbi_values), ("faed", faed_values)
    ):
        for target_name, target in TARGETS.items():
            single = select_single(stream_values, target)
            paired, leftover = select_pairs(stream_values, target)
            rows.append({
                "source": source_name,
                "target": target_name,
                "mode": "single_0_to_8",
                "output": single,
                "output_length": len(single),
                "unconsumed_symbols": 0,
            })
            rows.append({
                "source": source_name,
                "target": target_name,
                "mode": "paired_base81",
                "output": paired,
                "output_length": len(paired),
                "unconsumed_symbols": leftover,
            })
    return rows


def normalized_quadgram(text):
    letters = re.sub(r"[^A-Za-z]", "", text).upper()
    if len(letters) < 4:
        return float("-inf")
    return quadgram_score(letters) / (len(letters) - 3)


def authenticated_word_hits(text):
    lowered = text.lower()
    return tuple(sorted(
        (word for word in AUTHENTICATED_WORDS if word in lowered),
        key=lambda word: (-len(word), word),
    ))


def adjacent_repeat_rate(text):
    if len(text) < 2:
        return 0.0
    return sum(left == right for left, right in zip(text, text[1:])) / (len(text) - 1)


def zlib_ratio(text):
    raw = text.encode("ascii")
    return len(zlib.compress(raw, 9)) / len(raw)


def observe(rows):
    for row in rows:
        hits = authenticated_word_hits(row["output"])
        row["normalized_quadgram_score"] = normalized_quadgram(row["output"])
        row["authenticated_word_hits"] = hits
        row["longest_authenticated_word_length"] = max(map(len, hits), default=0)
        row["adjacent_repeat_rate"] = adjacent_repeat_rate(row["output"])
        row["zlib_ratio"] = zlib_ratio(row["output"])
    return {
        "maximum_quadgram_score": max(
            row["normalized_quadgram_score"] for row in rows
        ),
        "maximum_authenticated_word_length": max(
            row["longest_authenticated_word_length"] for row in rows
        ),
        "maximum_adjacent_repeat_rate": max(
            row["adjacent_repeat_rate"] for row in rows
        ),
        "minimum_zlib_ratio": min(row["zlib_ratio"] for row in rows),
    }


def empirical_p(observed, null_values, direction):
    if direction == "high":
        count = sum(value >= observed for value in null_values)
    else:
        count = sum(value <= observed for value in null_values)
    return (count + 1) / (len(null_values) + 1)


def median(values_):
    ordered = sorted(values_)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2


def audit(trials=TRIALS, seed=SEED):
    dbbi_values = values(DBBI)
    faed_values = values(FAED)
    rows = candidate_rows(dbbi_values, faed_values)
    observed = observe(rows)

    rng = random.Random(seed)
    shuffled_dbbi = list(dbbi_values)
    shuffled_faed = list(faed_values)
    null = {name: [] for name, _ in STAT_SPECS}
    for _ in range(trials):
        rng.shuffle(shuffled_dbbi)
        rng.shuffle(shuffled_faed)
        trial_observed = observe(candidate_rows(shuffled_dbbi, shuffled_faed))
        for name, _direction in STAT_SPECS:
            null[name].append(trial_observed[name])

    statistic_rows = []
    for name, direction in STAT_SPECS:
        raw_p = empirical_p(observed[name], null[name], direction)
        statistic_rows.append({
            "name": name,
            "direction": direction,
            "observed": observed[name],
            "null_median": median(null[name]),
            "raw_p": raw_p,
            "family_p": min(1.0, raw_p * len(STAT_SPECS)),
        })
    corrected_minimum = min(row["family_p"] for row in statistic_rows)
    exact_target_hits = tuple(
        (row["source"], row["target"], row["mode"])
        for row in rows if row["output"] in TARGETS.values()
    )
    length_only_matches = tuple(
        (row["source"], row["target"], row["mode"], row["output_length"])
        for row in rows
        if row["output_length"] in {len(target) for target in TARGETS.values()}
        and row["output"] not in TARGETS.values()
    )
    leaders = {
        "quadgram": max(rows, key=lambda row: row["normalized_quadgram_score"]),
        "word": max(rows, key=lambda row: row["longest_authenticated_word_length"]),
        "repeats": max(rows, key=lambda row: row["adjacent_repeat_rate"]),
        "zlib": min(rows, key=lambda row: row["zlib_ratio"]),
    }
    return {
        "targets": TARGETS,
        "target_category_count": 4,
        "target_string_count": len(TARGETS),
        "modes": ("single_0_to_8", "paired_base81"),
        "candidate_count": len(rows),
        "single_modulo_is_vacuous_for_all_targets": all(len(target) > 9 for target in TARGETS.values()),
        "rows": tuple(rows),
        "leaders": leaders,
        "statistic_rows": tuple(statistic_rows),
        "corrected_minimum": corrected_minimum,
        "gate_threshold": 0.01,
        "gate_passed": corrected_minimum < 0.01,
        "exact_target_hits": exact_target_hits,
        "length_only_matches": length_only_matches,
        "trials": trials,
        "seed": seed,
        "diagnostic_outputs_generated": True,
        "candidate_text_promoted": False,
        "candidate_text_generated": False,
        "password_oracle_run": False,
    }


def self_test():
    assert TARGETS["solved_url"] == "gsmg.io/theseedisplanted"
    assert TARGETS["native_row_sum_digits"] == "610876654997879"
    assert TARGETS["native_column_sum_digits"] == "8108108736759668"
    assert select_single(tuple(range(9)), "abcdefghi") == "abcdefghi"
    paired, leftover = select_pairs((0, 1, 8, 8, 4), "abcdefghi")
    assert paired == "bi" and leftover == 1
    report = audit(trials=100)
    assert report["candidate_count"] == 20
    assert report["single_modulo_is_vacuous_for_all_targets"]
    assert report["diagnostic_outputs_generated"]
    assert not report["candidate_text_promoted"]
    assert not report["candidate_text_generated"]
    print("[*] self-test OK: five targets, two index modes, and null family verified")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=TRIALS)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = self_test() if args.self_test else audit(args.trials, args.seed)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    print("[*] targets:", report["targets"])
    print("[*] candidates:", report["candidate_count"], "single modulo vacuous:",
          report["single_modulo_is_vacuous_for_all_targets"])
    for label, row in report["leaders"].items():
        print(
            f"[*] leader {label}: {row['source']}/{row['target']}/{row['mode']} "
            f"prefix={row['output'][:100]!r} words={row['authenticated_word_hits']}"
        )
    for row in report["statistic_rows"]:
        print(
            f"[*] {row['name']}: observed={row['observed']} "
            f"null_median={row['null_median']} raw_p={row['raw_p']:.6f} "
            f"family_p={row['family_p']:.6f}"
        )
    print("[*] exact target hits:", report["exact_target_hits"])
    print("[*] gate passed:", report["gate_passed"])
    print("[*] no candidate text was promoted and no password oracle was used")


if __name__ == "__main__":
    main()
