#!/usr/bin/env python3
"""Audit the literal color-prime list sums at the DBBI/matrixsumlist boundary.

The authenticated macro order says ``yellowblueprimes -> matrixsumlist``.
The established spatial walk supplies 23 sequential-prime events that fit
inside DBBI: 14 blue, 8 yellow, and the distinct FEFE event.  This audit:

* sums the blue and yellow prime lists without transforming their values;
* computes the exact color-count-preserving base rate of their near-balance;
* reports the load-bearing alternatives (fold FEFE into blue; include the two
  events that already cross into ``matrixsumlist``);
* applies the resulting values only to the next literal clue source: words
  before the Architect's ``choice``.

The recovered historical Telegram guide already selects a different operation:
place DBBI token chunks in a 14x14 matrix and sum its rows.  The color-list
sums below are therefore an alternative literal observation, not the leading
interpretation of that guide.  This audit does not treat HTTP status codes,
digit sums, modular reductions, or cipher keys as selected operations.
"""

import argparse
import itertools
import re
from fractions import Fraction
from math import comb

from flo_prime_walk_provenance_audit import audit as prime_walk_audit
from matrix_dialogue_count_audit import extract_scene
from prime_matrixsum_reconstruction import load_architect_words

CHOICE_MARKER = "As you adequately put, the problem is choice."
EXPECTED_FITTED_SUMS = {"B": 401, "Y": 400, "F": 73}
EXPECTED_ALL_SUMS = {"B": 490, "Y": 497, "F": 73}


def group_primes(records):
    groups = {"B": [], "Y": [], "F": []}
    for record in records:
        groups[record["color"]].append(record["prime"])
    return {color: tuple(values) for color, values in groups.items()}


def group_sums(groups):
    return {color: sum(values) for color, values in groups.items()}


def exact_partition_rate(non_fefe_primes, yellow_count, max_difference=1):
    """Return the exact rate over all fixed-size yellow/blue assignments."""
    total_sum = sum(non_fefe_primes)
    successes = sum(
        abs(total_sum - 2 * sum(yellow)) <= max_difference
        for yellow in itertools.combinations(non_fefe_primes, yellow_count)
    )
    total = comb(len(non_fefe_primes), yellow_count)
    return Fraction(successes, total)


def words_through_choice():
    scene = re.sub(r"\s+", " ", extract_scene())
    marker_end = scene.find(CHOICE_MARKER)
    if marker_end < 0:
        raise AssertionError("Architect choice marker was not found")
    through_choice = scene[:marker_end + len(CHOICE_MARKER)]
    tokens = re.findall(r"[A-Za-z]+", through_choice.lower())
    if not tokens or tokens[-1] != "choice":
        raise AssertionError("scene extraction did not end at choice")
    return tokens


def index_report(tokens, values):
    report = {}
    for label, value in values.items():
        report[label] = {
            "value": value,
            "forward_one": tokens[value - 1] if value <= len(tokens) else None,
            "backward_one": tokens[-value] if value <= len(tokens) else None,
        }
    return report


def audit():
    walk = prime_walk_audit()
    fitted_groups = group_primes(walk["fitted_spatial_walk"])
    all_groups = group_primes(walk["spatial_walk"])
    fitted_sums = group_sums(fitted_groups)
    all_sums = group_sums(all_groups)
    non_fefe = fitted_groups["B"] + fitted_groups["Y"]
    balance_rate = exact_partition_rate(non_fefe, len(fitted_groups["Y"]))
    scene_words = words_through_choice()
    architect_words, _ = load_architect_words()

    return {
        "fitted_groups": fitted_groups,
        "fitted_sums": fitted_sums,
        "all_groups": all_groups,
        "all_sums": all_sums,
        "blue_yellow_difference": abs(fitted_sums["B"] - fitted_sums["Y"]),
        "fefe_folded_blue_difference": abs(
            fitted_sums["B"] + fitted_sums["F"] - fitted_sums["Y"]
        ),
        "all_event_blue_yellow_difference": abs(
            all_sums["B"] - all_sums["Y"]
        ),
        "balance_rate": balance_rate,
        "scene_word_count": len(scene_words),
        "scene_indices": index_report(scene_words, fitted_sums),
        "architect_word_count": len(architect_words),
        "architect_source_supports_indices": (
            max(fitted_sums.values()) <= len(architect_words)
        ),
    }


def self_test():
    for values in ((1, 2, 3, 4), (2, 3, 5, 7, 11)):
        for selected_count in range(len(values) + 1):
            expected = sum(
                abs(sum(values) - 2 * sum(selected)) <= 1
                for selected in itertools.combinations(values, selected_count)
            )
            actual = exact_partition_rate(values, selected_count)
            assert actual == Fraction(expected, comb(len(values), selected_count))

    report = audit()
    assert report["fitted_sums"] == EXPECTED_FITTED_SUMS
    assert report["all_sums"] == EXPECTED_ALL_SUMS
    assert report["blue_yellow_difference"] == 1
    assert report["fefe_folded_blue_difference"] == 74
    assert report["all_event_blue_yellow_difference"] == 7
    assert report["balance_rate"] == Fraction(813, 319_770)
    assert report["scene_word_count"] == 1326
    assert report["scene_indices"]["B"]["backward_one"] == "it"
    assert report["scene_indices"]["Y"]["backward_one"] == "int"
    assert report["scene_indices"]["F"]["backward_one"] == "truth"
    assert report["architect_word_count"] == 72
    assert report["architect_source_supports_indices"] is False
    print(
        "[*] self-test OK: color-prime sums, exact partition rate, boundary "
        "alternatives, and bounded Architect-choice indexing verified"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    report = audit()

    for color in ("Y", "B", "F"):
        print(
            f"[*] {color}: primes={report['fitted_groups'][color]} "
            f"sum={report['fitted_sums'][color]}"
        )
    rate = report["balance_rate"]
    print(
        f"[*] exact fixed-profile rate for |blue_sum-yellow_sum| <= 1: "
        f"{rate.numerator}/{rate.denominator} = {float(rate):.9f}"
    )
    print(
        f"[*] sensitivity: FEFE folded into blue -> difference "
        f"{report['fefe_folded_blue_difference']}; all 25 events -> difference "
        f"{report['all_event_blue_yellow_difference']}"
    )
    print(
        f"[*] full scene through Architect choice: "
        f"{report['scene_word_count']} words"
    )
    for color in ("B", "Y", "F"):
        item = report["scene_indices"][color]
        print(
            f"    {color}={item['value']}: forward[1]={item['forward_one']!r}; "
            f"backward[1]={item['backward_one']!r}"
        )
    print(
        f"[*] Architect-spoken source has only "
        f"{report['architect_word_count']} words before choice; "
        "400/401 cannot index it"
    )
    print(
        "[*] verdict: the literal blue/yellow prime-list sums form a notable "
        "401/400 near-balance under the mechanically fixed DBBI boundary, but "
        "the recovered historical guide explicitly selects 14x14 matrix row "
        "sums instead. The result also depends on keeping FEFE distinct. The "
        "next-clue indexing family yields no instruction, so retain 401/400 "
        "as a secondary observation only, not a password or cipher escalation."
    )
    if args.self_test:
        self_test()


if __name__ == "__main__":
    main()
