#!/usr/bin/env python3
"""Three-trit/base-27 language audit for DBBI and FAED.

This closes a specific gap in dual_ternary_sweep.py: that audit packed five
trits as base-243 bytes and whole trit streams as base-3 integers, but never
grouped three trits into a natural 27-character alphabet.

The declared family is exactly eight 3x3 square symmetries, two within-symbol
trit orders, and two conventional alphabets (space+A-Z and A-Z+space).  Groups
start at the authored stream boundary.  FAED consumes all 1140 trits; DBBI
consumes 180 and reports, but never pads, its final two trits.  Exact duplicate
outputs are collapsed before scoring.

The maximum normalized English quadgram score across both streams and the
entire declared family is calibrated against independently shuffled streams
that preserve their exact symbol profiles.  No fragments are selected and no
password oracle is used.
"""

import argparse
import inspect
import json
import random

from data import DBBI, FAED
from dual_ternary_sweep import coordinate_map, decode_stream
from quadgram_solver import score as quadgram_score


SYMMETRIES = (
    "identity",
    "rot90",
    "rot180",
    "rot270",
    "mirror_vertical",
    "mirror_horizontal",
    "mirror_diagonal",
    "mirror_antidiagonal",
)
TRIT_ORDERS = ("first_second", "second_first")
ALPHABETS = {
    "space_then_AZ": " ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "AZ_then_space": "ABCDEFGHIJKLMNOPQRSTUVWXYZ ",
}
DECLARATION_COUNT = len(SYMMETRIES) * len(TRIT_ORDERS) * len(ALPHABETS)


def prior_coverage():
    source = inspect.getsource(decode_stream)
    return {
        "base243_present": "base243" in source,
        "whole_base3_present": "whole_base3" in source,
        "binary_masks_present": "pack_bits" in source,
        "base27_present": "base27" in source,
        "three_trit_grouping_present": "range(0, len(usable) - 2, 3)" in source,
    }


def trit_stream(stream, symmetry, trit_order):
    mapping = coordinate_map(symmetry)
    output = []
    for symbol in stream:
        first, second = mapping[symbol]
        pair = (first, second) if trit_order == "first_second" else (second, first)
        output.extend(pair)
    return tuple(output)


def decode_base27(trits, alphabet):
    usable_length = len(trits) - len(trits) % 3
    text = "".join(
        alphabet[trits[index] * 9 + trits[index + 1] * 3 + trits[index + 2]]
        for index in range(0, usable_length, 3)
    )
    return text, tuple(trits[usable_length:])


def normalized_language_score(text):
    compact = text.replace(" ", "")
    if len(compact) < 4:
        return float("-inf")
    return quadgram_score(compact) / (len(compact) - 3)


def candidate_rows(source_name, stream):
    registry = {}
    declarations = []
    for symmetry in SYMMETRIES:
        for trit_order in TRIT_ORDERS:
            trits = trit_stream(stream, symmetry, trit_order)
            for alphabet_name, alphabet in ALPHABETS.items():
                text, leftover = decode_base27(trits, alphabet)
                label = f"{symmetry}/{trit_order}/{alphabet_name}"
                declarations.append({
                    "label": label,
                    "text": text,
                    "leftover_trits": leftover,
                })
                entry = registry.setdefault((text, leftover), {
                    "source": source_name,
                    "text": text,
                    "leftover_trits": leftover,
                    "labels": [],
                })
                entry["labels"].append(label)
    rows = []
    for entry in registry.values():
        text = entry["text"]
        rows.append({
            **entry,
            "labels": tuple(entry["labels"]),
            "output_length": len(text),
            "space_count": text.count(" "),
            "compact_length": len(text.replace(" ", "")),
            "normalized_quadgram_score": normalized_language_score(text),
        })
    rows.sort(key=lambda row: row["normalized_quadgram_score"], reverse=True)
    return {
        "declaration_count": len(declarations),
        "unique_output_count": len(rows),
        "rows": tuple(rows),
    }


def family_observation(dbbi, faed):
    sources = {
        "DBBI": candidate_rows("DBBI", dbbi),
        "FAED": candidate_rows("FAED", faed),
    }
    source_best = {
        name: report["rows"][0]["normalized_quadgram_score"]
        for name, report in sources.items()
    }
    return {
        "sources": sources,
        "source_best_scores": source_best,
        "family_best_score": max(source_best.values()),
        "family_winner": max(source_best, key=source_best.get),
    }


def empirical_upper_p(observed, null_values):
    return (1 + sum(value >= observed for value in null_values)) / (
        len(null_values) + 1
    )


def null_calibration(observed, trials, seed):
    rng = random.Random(seed)
    shuffled_dbbi = list(DBBI)
    shuffled_faed = list(FAED)
    source_nulls = {"DBBI": [], "FAED": []}
    family_nulls = []
    for _ in range(trials):
        rng.shuffle(shuffled_dbbi)
        rng.shuffle(shuffled_faed)
        row = family_observation("".join(shuffled_dbbi), "".join(shuffled_faed))
        for source in source_nulls:
            source_nulls[source].append(row["source_best_scores"][source])
        family_nulls.append(row["family_best_score"])

    source_rows = {}
    for source, values in source_nulls.items():
        values.sort()
        source_rows[source] = {
            "observed_best_score": observed["source_best_scores"][source],
            "null_median_best_score": values[len(values) // 2],
            "null_95th_percentile_best_score": values[(95 * len(values)) // 100],
            "empirical_p": empirical_upper_p(
                observed["source_best_scores"][source], values
            ),
        }
    family_nulls.sort()
    family_p = empirical_upper_p(observed["family_best_score"], family_nulls)
    return {
        "trials": trials,
        "seed": seed,
        "null_model": "independent DBBI/FAED shuffles preserving exact symbol profiles; full-family maximum retained per trial",
        "source_rows": source_rows,
        "family": {
            "observed_best_score": observed["family_best_score"],
            "observed_winner": observed["family_winner"],
            "null_median_best_score": family_nulls[len(family_nulls) // 2],
            "null_95th_percentile_best_score": family_nulls[(95 * len(family_nulls)) // 100],
            "empirical_p": family_p,
            "promotion_threshold": 0.01,
            "promoted": family_p < 0.01,
        },
    }


def compact_top_rows(observation, limit=5):
    return {
        source: tuple({
            **row,
            "text_preview": row["text"][:120],
        } for row in report["rows"][:limit])
        for source, report in observation["sources"].items()
    }


def audit(trials=5_000, seed=20260814):
    if trials < 1:
        raise ValueError("trials must be positive")
    coverage = prior_coverage()
    if coverage["base27_present"] or coverage["three_trit_grouping_present"]:
        raise AssertionError("prior dual-ternary code now covers base-27; re-audit scope")
    observed = family_observation(DBBI, FAED)
    calibration = null_calibration(observed, trials, seed)
    return {
        "prior_coverage": coverage,
        "family": {
            "symmetries": SYMMETRIES,
            "trit_orders": TRIT_ORDERS,
            "alphabets": ALPHABETS,
            "declarations_per_source": DECLARATION_COUNT,
            "unique_outputs": {
                source: report["unique_output_count"]
                for source, report in observed["sources"].items()
            },
        },
        "source_geometry": {
            "DBBI": {
                "symbols": len(DBBI), "trits": len(DBBI) * 2,
                "output_characters": (len(DBBI) * 2) // 3,
                "leftover_trits": (len(DBBI) * 2) % 3,
            },
            "FAED": {
                "symbols": len(FAED), "trits": len(FAED) * 2,
                "output_characters": (len(FAED) * 2) // 3,
                "leftover_trits": (len(FAED) * 2) % 3,
            },
        },
        "top_rows": compact_top_rows(observed),
        "calibration": calibration,
        "candidate_promoted": calibration["family"]["promoted"],
        "password_oracle_run": False,
    }


def self_test():
    coverage = prior_coverage()
    assert coverage == {
        "base243_present": True,
        "whole_base3_present": True,
        "binary_masks_present": True,
        "base27_present": False,
        "three_trit_grouping_present": False,
    }
    text, leftover = decode_base27((0, 0, 0, 0, 0, 1, 2, 2, 2), ALPHABETS["AZ_then_space"])
    assert text == "AB "
    assert leftover == ()
    text, leftover = decode_base27((0, 0, 0, 1, 2), ALPHABETS["AZ_then_space"])
    assert text == "A"
    assert leftover == (1, 2)
    report = audit(trials=5)
    assert report["family"]["declarations_per_source"] == 32
    assert report["source_geometry"]["DBBI"]["leftover_trits"] == 2
    assert report["source_geometry"]["FAED"]["leftover_trits"] == 0
    assert not report["password_oracle_run"]
    print("[*] self-test OK: prior gap, exact base-27 grouping, leftovers, and family null verified")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=5_000)
    parser.add_argument("--seed", type=int, default=20260814)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = self_test() if args.self_test else audit(args.trials, args.seed)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    print("[*] prior dual-ternary coverage:", report["prior_coverage"])
    print("[*] family declarations/source:", report["family"]["declarations_per_source"],
          "unique:", report["family"]["unique_outputs"])
    for source, rows in report["top_rows"].items():
        top = rows[0]
        print(
            f"[*] {source} best: score={top['normalized_quadgram_score']:.6f} "
            f"labels={top['labels']} preview={top['text_preview']!r}"
        )
    for source, row in report["calibration"]["source_rows"].items():
        print(
            f"    {source}: real={row['observed_best_score']:.6f} "
            f"null_median={row['null_median_best_score']:.6f} "
            f"p={row['empirical_p']:.6g}"
        )
    family = report["calibration"]["family"]
    print(
        f"[*] family: real={family['observed_best_score']:.6f} "
        f"null_median={family['null_median_best_score']:.6f} "
        f"p={family['empirical_p']:.6g} promoted={family['promoted']}"
    )
    print("[*] no password oracle was used")


if __name__ == "__main__":
    main()

