#!/usr/bin/env python3
"""Factoradic/Lehmer record-validity gate for DBBI and FAED.

Standard Lehmer codes are not self-delimiting: permutation size and record
boundary must be supplied.  This audit admits only two source-grounded sizes,
n=6 (the six FAED lanes) and n=9 (the alphabet/9x9 matrix), under the two
standard serializations: the mandatory final zero present or conventionally
omitted.

For each source/grammar it counts all valid sliding windows and the largest
valid-block count at any fixed phase.  Sixteen pre-registered statistics are
calibrated against independently shuffled streams preserving exact symbol
profiles.  No phase, permutation, or downstream reorder is selected from
readability, and no password oracle is used.
"""

import argparse
import json
import math
import random

from data import DBBI, FAED


SIZES = (6, 9)
TERMINAL_MODES = ("terminal_zero_present", "terminal_zero_omitted")


def spec_name(size, terminal_mode):
    suffix = "full" if terminal_mode == "terminal_zero_present" else "omit0"
    return f"n{size}_{suffix}"


METRIC_ALTERNATIVES = {
    metric: "high"
    for source in ("DBBI", "FAED")
    for size in SIZES
    for terminal_mode in TERMINAL_MODES
    for metric in (
        f"{source}_{spec_name(size, terminal_mode)}_sliding_valid_count",
        f"{source}_{spec_name(size, terminal_mode)}_best_phase_valid_count",
    )
}
FAMILY_SIZE = len(METRIC_ALTERNATIVES)


def digit_values(stream):
    values = tuple(ord(symbol) - ord("a") for symbol in stream)
    if any(not 0 <= value <= 8 for value in values):
        raise ValueError("stream contains symbols outside a-i")
    return values


def grammar(size, terminal_mode):
    if size < 2:
        raise ValueError("permutation size must be at least two")
    if terminal_mode == "terminal_zero_present":
        maxima = tuple(range(size - 1, -1, -1))
    elif terminal_mode == "terminal_zero_omitted":
        maxima = tuple(range(size - 1, 0, -1))
    else:
        raise ValueError(f"unknown terminal mode: {terminal_mode}")
    return maxima


def valid_record(record, maxima):
    return len(record) == len(maxima) and all(
        0 <= digit <= maximum for digit, maximum in zip(record, maxima)
    )


def complete_digits(record, terminal_mode):
    if terminal_mode == "terminal_zero_omitted":
        return tuple(record) + (0,)
    return tuple(record)


def lehmer_decode(record, size, terminal_mode):
    digits = complete_digits(record, terminal_mode)
    if not valid_record(digits, grammar(size, "terminal_zero_present")):
        raise ValueError("invalid Lehmer record")
    available = list(range(size))
    permutation = []
    for digit in digits:
        permutation.append(available.pop(digit))
    return tuple(permutation)


def factoradic_rank(record, size, terminal_mode):
    digits = complete_digits(record, terminal_mode)
    return sum(
        digit * math.factorial(size - 1 - index)
        for index, digit in enumerate(digits)
    )


def grammar_observation(values, size, terminal_mode):
    maxima = grammar(size, terminal_mode)
    width = len(maxima)
    valid_windows = []
    for start in range(0, len(values) - width + 1):
        record = values[start:start + width]
        if valid_record(record, maxima):
            valid_windows.append({
                "start_0": start,
                "digits": record,
                "rank": factoradic_rank(record, size, terminal_mode),
                "permutation": lehmer_decode(record, size, terminal_mode),
            })

    phase_rows = []
    for phase in range(width):
        starts = tuple(range(phase, len(values) - width + 1, width))
        valid_starts = tuple(
            start for start in starts
            if valid_record(values[start:start + width], maxima)
        )
        phase_rows.append({
            "phase_0": phase,
            "complete_blocks": len(starts),
            "valid_blocks": len(valid_starts),
            "valid_starts_0": valid_starts,
        })
    best_phase = max(
        phase_rows,
        key=lambda row: (row["valid_blocks"], -row["phase_0"]),
    )
    return {
        "size": size,
        "terminal_mode": terminal_mode,
        "record_width": width,
        "digit_maxima": maxima,
        "sliding_window_count": max(0, len(values) - width + 1),
        "sliding_valid_count": len(valid_windows),
        "valid_windows": tuple(valid_windows),
        "phase_rows": tuple(phase_rows),
        "best_phase_valid_count": best_phase["valid_blocks"],
        "best_phase": best_phase,
    }


def observation(dbbi, faed):
    sources = {}
    metrics = {}
    for source, stream in (("DBBI", dbbi), ("FAED", faed)):
        values = digit_values(stream)
        rows = {}
        for size in SIZES:
            for terminal_mode in TERMINAL_MODES:
                name = spec_name(size, terminal_mode)
                row = grammar_observation(values, size, terminal_mode)
                rows[name] = row
                metrics[f"{source}_{name}_sliding_valid_count"] = row[
                    "sliding_valid_count"
                ]
                metrics[f"{source}_{name}_best_phase_valid_count"] = row[
                    "best_phase_valid_count"
                ]
        sources[source] = rows
    if tuple(metrics) != tuple(METRIC_ALTERNATIVES):
        raise AssertionError("factoradic metric registry/order drifted")
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


def compact_sources(sources):
    return {
        source: {
            name: {
                key: value for key, value in row.items()
                if key != "phase_rows"
            }
            for name, row in rows.items()
        }
        for source, rows in sources.items()
    }


def audit(trials=20_000, seed=20260814):
    if trials < 1:
        raise ValueError("trials must be positive")
    observed = observation(DBBI, FAED)
    calibration = null_calibration(observed, trials, seed)
    family_p = min(row["family_bonferroni_p"] for row in calibration.values())
    threshold = 0.01
    promoted = family_p < threshold
    return {
        "prior_repository_coverage": {
            "factoradic_or_lehmer_audits_before_this": 0,
        },
        "specification_correction": {
            "standard_lehmer_is_self_delimiting": False,
            "externally_fixed_sizes": SIZES,
            "reason": "n=6 FAED lanes; n=9 alphabet/9x9 matrix",
        },
        "terminal_modes": TERMINAL_MODES,
        "sources": compact_sources(observed["sources"]),
        "calibration": {
            "trials": trials,
            "seed": seed,
            "null_model": "independent shuffles preserving exact DBBI/FAED symbol profiles",
            "metric_count": FAMILY_SIZE,
            "rows": calibration,
            "family_bonferroni_p_bound": family_p,
            "promotion_threshold": threshold,
            "promoted": promoted,
        },
        "permutation_consumer": {
            "authorized": promoted,
            "operations_run": 0,
            "reason": (
                "record gate passed; define a source-selected consumer"
                if promoted else
                "record gate failed; no row/lane/alphabet reorder is authorized"
            ),
        },
        "candidate_text_generated": False,
        "password_oracle_run": False,
    }


def self_test():
    record = (2, 0, 1)  # n=4 with terminal zero omitted
    assert grammar(4, "terminal_zero_omitted") == (3, 2, 1)
    assert valid_record(record, grammar(4, "terminal_zero_omitted"))
    assert lehmer_decode(record, 4, "terminal_zero_omitted") == (2, 0, 3, 1)
    assert factoradic_rank(record, 4, "terminal_zero_omitted") == 13
    assert not valid_record((4, 0, 1), grammar(4, "terminal_zero_omitted"))
    report = audit(trials=10)
    assert report["specification_correction"]["standard_lehmer_is_self_delimiting"] is False
    assert report["calibration"]["metric_count"] == 16
    assert report["permutation_consumer"]["operations_run"] == 0
    assert not report["candidate_text_generated"]
    assert not report["password_oracle_run"]
    print("[*] self-test OK: Lehmer grammar/decode/rank, fixed sizes, and null gate verified")
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
    print("[*] standard Lehmer self-delimiting:",
          report["specification_correction"]["standard_lehmer_is_self_delimiting"])
    for source, rows in report["sources"].items():
        for name, row in rows.items():
            print(
                f"[*] {source}/{name}: sliding={row['sliding_valid_count']} "
                f"best_phase={row['best_phase_valid_count']} "
                f"valid_starts={[item['start_0'] for item in row['valid_windows'][:10]]}"
            )
    for name, row in report["calibration"]["rows"].items():
        print(
            f"    {name}: observed={row['observed']} "
            f"null_median={row['null_median']} "
            f"raw_p={row['empirical_p']:.6g} "
            f"corrected_p={row['family_bonferroni_p']:.6g}"
        )
    print(
        "[*] family p-bound:",
        f"{report['calibration']['family_bonferroni_p_bound']:.6g}",
        "promoted=" + str(report["calibration"]["promoted"]),
    )
    print("[*] consumer:", report["permutation_consumer"])
    print("[*] no candidate text or password oracle was used")


if __name__ == "__main__":
    main()

