#!/usr/bin/env python3
"""Move-to-front structural gate for DBBI/FAED, before any BWT scan.

The a-i symbols are interpreted as ranks 0-8.  MTF decoding uses the canonical
ascending alphabet; every other initial ordering is a global relabelling and
therefore leaves the equality/run/information/compression statistics unchanged.

Five pre-registered measures per stream are calibrated against independently
shuffled rank streams preserving the exact input profiles.  The ten-test family
is Bonferroni-corrected.  Burrows-Wheeler primary-index scanning is explicitly
unauthorized unless this gate reaches corrected p < 0.01.
"""

import argparse
import json
import math
import random
import zlib
from collections import Counter

from data import DBBI, FAED


ALPHABET = "abcdefghi"
METRIC_ALTERNATIVES = {
    "DBBI_adjacent_repeats": "high",
    "DBBI_longest_run": "high",
    "DBBI_index_of_coincidence": "high",
    "DBBI_transition_mutual_information": "high",
    "DBBI_zlib_length": "low",
    "FAED_adjacent_repeats": "high",
    "FAED_longest_run": "high",
    "FAED_index_of_coincidence": "high",
    "FAED_transition_mutual_information": "high",
    "FAED_zlib_length": "low",
}
FAMILY_SIZE = len(METRIC_ALTERNATIVES)


def mtf_decode(rank_stream, initial_alphabet=ALPHABET):
    if len(initial_alphabet) != len(set(initial_alphabet)):
        raise ValueError("MTF alphabet must contain unique symbols")
    state = list(initial_alphabet)
    output = []
    for symbol in rank_stream:
        rank = ord(symbol) - ord("a")
        if not 0 <= rank < len(state):
            raise ValueError(f"rank symbol outside a-i: {symbol!r}")
        selected = state.pop(rank)
        output.append(selected)
        state.insert(0, selected)
    return "".join(output)


def mtf_encode(text, initial_alphabet=ALPHABET):
    state = list(initial_alphabet)
    output = []
    for symbol in text:
        rank = state.index(symbol)
        output.append(chr(ord("a") + rank))
        state.pop(rank)
        state.insert(0, symbol)
    return "".join(output)


def longest_run(text):
    best = current = 0
    previous = None
    for symbol in text:
        if symbol == previous:
            current += 1
        else:
            current = 1
            previous = symbol
        best = max(best, current)
    return best


def index_of_coincidence(text):
    length = len(text)
    if length < 2:
        return 0.0
    counts = Counter(text)
    return sum(count * (count - 1) for count in counts.values()) / (
        length * (length - 1)
    )


def transition_mutual_information(text):
    if len(text) < 2:
        return 0.0
    pairs = Counter(zip(text, text[1:]))
    left = Counter(text[:-1])
    right = Counter(text[1:])
    total = len(text) - 1
    information = 0.0
    for (first, second), count in pairs.items():
        joint = count / total
        information += joint * math.log2(
            joint / ((left[first] / total) * (right[second] / total))
        )
    return information


def structural_metrics(decoded):
    return {
        "adjacent_repeats": sum(
            left == right for left, right in zip(decoded, decoded[1:])
        ),
        "longest_run": longest_run(decoded),
        "index_of_coincidence": index_of_coincidence(decoded),
        "transition_mutual_information": transition_mutual_information(decoded),
        "zlib_length": len(zlib.compress(decoded.encode("ascii"), level=9)),
    }


def observation(dbbi, faed):
    decoded = {
        "DBBI": mtf_decode(dbbi),
        "FAED": mtf_decode(faed),
    }
    per_source = {
        source: structural_metrics(text) for source, text in decoded.items()
    }
    metrics = {
        f"{source}_{name}": value
        for source, rows in per_source.items()
        for name, value in rows.items()
    }
    if tuple(metrics) != tuple(METRIC_ALTERNATIVES):
        raise AssertionError("MTF metric registry/order drifted")
    return {
        "decoded": decoded,
        "per_source": per_source,
        "metrics": metrics,
    }


def empirical_p(observed, null_values, alternative):
    if alternative == "high":
        count = sum(value >= observed for value in null_values)
    elif alternative == "low":
        count = sum(value <= observed for value in null_values)
    else:
        raise ValueError(f"unknown alternative: {alternative}")
    return (1 + count) / (len(null_values) + 1)


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
    for name, alternative in METRIC_ALTERNATIVES.items():
        values = sorted(nulls[name])
        raw_p = empirical_p(observed["metrics"][name], values, alternative)
        rows[name] = {
            "observed": observed["metrics"][name],
            "alternative": alternative,
            "null_median": values[len(values) // 2],
            "null_5th_percentile": values[(5 * len(values)) // 100],
            "null_95th_percentile": values[(95 * len(values)) // 100],
            "empirical_p": raw_p,
            "family_bonferroni_p": min(1.0, raw_p * FAMILY_SIZE),
        }
    return rows


def inverse_bwt(last_column, primary_index):
    """Invert a BWT under the conventional zero-based sorted-row index."""
    length = len(last_column)
    if not 0 <= primary_index < length:
        raise ValueError("primary index outside BWT row range")
    occurrence = Counter()
    last_tags = []
    for symbol in last_column:
        last_tags.append((symbol, occurrence[symbol]))
        occurrence[symbol] += 1
    occurrence.clear()
    first_tags = []
    for symbol in sorted(last_column):
        first_tags.append((symbol, occurrence[symbol]))
        occurrence[symbol] += 1
    first_positions = {tag: index for index, tag in enumerate(first_tags)}
    lf = tuple(first_positions[tag] for tag in last_tags)
    row = primary_index
    output = []
    for _ in range(length):
        output.append(last_column[row])
        row = lf[row]
    return "".join(reversed(output))


def bwt_transform(text):
    """Small positive-control transform returning (last column, row index)."""
    rotations = sorted(text[index:] + text[:index] for index in range(len(text)))
    return "".join(row[-1] for row in rotations), rotations.index(text)


def audit(trials=20_000, seed=20260814):
    if trials < 1:
        raise ValueError("trials must be positive")
    observed = observation(DBBI, FAED)
    calibration = null_calibration(observed, trials, seed)
    family_p = min(row["family_bonferroni_p"] for row in calibration.values())
    threshold = 0.01
    authorized = family_p < threshold

    ascending = observed["decoded"]
    descending = {
        "DBBI": mtf_decode(DBBI, ALPHABET[::-1]),
        "FAED": mtf_decode(FAED, ALPHABET[::-1]),
    }
    relabel_invariant = all(
        structural_metrics(ascending[source]) == structural_metrics(descending[source])
        for source in ascending
    )
    return {
        "prior_repository_coverage": {
            "implemented_mtf_or_bwt_audits_before_this": 0,
            "basis": "repository keyword audit excluding this brainstorm and implementation",
        },
        "source_lengths": {"DBBI": len(DBBI), "FAED": len(FAED)},
        "rank_mapping": "a=0 through i=8",
        "initial_alphabets_checked": (ALPHABET, ALPHABET[::-1]),
        "initial_alphabet_structural_relabel_invariant": relabel_invariant,
        "decoded": {
            source: {
                "text": text,
                "prefix": text[:120],
                **observed["per_source"][source],
            }
            for source, text in ascending.items()
        },
        "calibration": {
            "trials": trials,
            "seed": seed,
            "null_model": "independent shuffles preserving exact MTF-rank profiles",
            "metric_count": FAMILY_SIZE,
            "rows": calibration,
            "family_bonferroni_p_bound": family_p,
            "promotion_threshold": threshold,
            "promoted": authorized,
        },
        "bwt": {
            "authorized": authorized,
            "primary_indices_scanned": 0,
            "reason": (
                "MTF structural gate passed; implement a separately calibrated scan"
                if authorized else
                "MTF structural gate failed; stop rule prohibits primary-index scanning"
            ),
        },
        "candidate_text_generated": False,
        "password_oracle_run": False,
    }


def self_test():
    plaintext = "abacabad"
    encoded = mtf_encode(plaintext)
    assert mtf_decode(encoded) == plaintext
    assert structural_metrics(mtf_decode(encoded, ALPHABET)) == structural_metrics(
        mtf_decode(encoded, ALPHABET[::-1])
    )
    bwt, index = bwt_transform("banana$")
    assert inverse_bwt(bwt, index) == "banana$"
    report = audit(trials=10)
    assert report["initial_alphabet_structural_relabel_invariant"]
    assert report["calibration"]["metric_count"] == 10
    assert report["bwt"]["primary_indices_scanned"] == 0
    assert not report["candidate_text_generated"]
    assert not report["password_oracle_run"]
    print("[*] self-test OK: MTF round-trip, relabel invariance, BWT inverse, and gate verified")
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
    for source, row in report["decoded"].items():
        print(f"[*] {source} MTF prefix: {row['prefix']!r}")
    for name, row in report["calibration"]["rows"].items():
        print(
            f"    {name}: observed={row['observed']:.9g} "
            f"null_median={row['null_median']:.9g} "
            f"raw_p={row['empirical_p']:.6g} "
            f"corrected_p={row['family_bonferroni_p']:.6g}"
        )
    print(
        "[*] MTF gate family p-bound:",
        f"{report['calibration']['family_bonferroni_p_bound']:.6g}",
        "promoted=" + str(report["calibration"]["promoted"]),
    )
    print("[*] BWT:", report["bwt"])
    print("[*] no candidate text or password oracle was used")


if __name__ == "__main__":
    main()
