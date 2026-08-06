#!/usr/bin/env python3
"""Audit literal thematic words in the exact 31-character prime-walk output.

The selected text was originally checked against a narrow fixed vocabulary
that found only ``yang``. A later direct reading also notices ``a leaf`` and
``a nest``. This script verifies those substrings, maps them onto the exact
prime-walk event boundaries, and computes exact uniform order-preserving
31-of-91 subset rates for each word and for all three jointly.

The rates are descriptive calibration, not discovery p-values: ``leaf`` and
``nest`` were noticed after inspecting the output, and no broader thematic
word family was pre-registered. Phase 48 mechanically reconstructs TARGET
from Flo's literal highlighted DBBI mask and the corrected FEFE-inserted
prime walk; it does not establish that the community discovered that rule
blindly or that the creator intended the resulting words.
"""

import argparse
import itertools
import math
import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from denis_prime_extraction_audit import (  # noqa: E402
    SOURCE,
    TARGET,
    exact_subset_rate,
)
from flo_prime_walk_provenance_audit import audit as prime_walk_audit  # noqa: E402


PATTERNS = ("yang", "leaf", "nest")
SUBSET_SIZE = 31


def automaton(patterns):
    prefixes = {""}
    for pattern in patterns:
        prefixes.update(pattern[:length] for length in range(1, len(pattern) + 1))

    def transition(state, character):
        combined = state + character
        found = 0
        for index, pattern in enumerate(patterns):
            if combined.endswith(pattern):
                found |= 1 << index
        suffixes = [prefix for prefix in prefixes if combined.endswith(prefix)]
        return max(suffixes, key=len), found

    return transition


def exact_joint_rate(source, subset_size, patterns):
    transition = automaton(patterns)
    all_found = (1 << len(patterns)) - 1

    @lru_cache(maxsize=None)
    def count(position, used, state, found):
        if used == subset_size:
            return int(found == all_found)
        if position == len(source) or len(source) - position < subset_size - used:
            return 0
        skipped = count(position + 1, used, state, found)
        next_state, newly_found = transition(state, source[position])
        selected = count(
            position + 1,
            used + 1,
            next_state,
            found | newly_found,
        )
        return skipped + selected

    favorable = count(0, 0, "", 0)
    total = math.comb(len(source), subset_size)
    return favorable, total, favorable / total


def event_map():
    report = prime_walk_audit()
    mapping = []
    output_position = 0
    for record in report["fitted_spatial_walk"]:
        width = len(record["required"])
        for local_index in range(width):
            mapping.append(
                {
                    "output_index": output_position,
                    "event": record["ordinal"],
                    "color": record["color"],
                    "prime": record["prime"],
                    "raw_position": record["raw_position"] + local_index,
                }
            )
            output_position += 1
    if len(mapping) != len(TARGET):
        raise AssertionError("event map no longer covers the selected text")
    return mapping


def substring_report(word, mapping):
    starts = [
        index
        for index in range(len(TARGET))
        if TARGET.startswith(word, index)
    ]
    if len(starts) != 1:
        raise AssertionError(f"expected one literal {word!r}, found {starts}")
    start = starts[0]
    end = start + len(word)
    cells = mapping[start:end]
    return {
        "word": word,
        "start_zero_based": start,
        "end_exclusive": end,
        "events": tuple(dict.fromkeys(cell["event"] for cell in cells)),
        "colors": tuple(dict.fromkeys(cell["color"] for cell in cells)),
        "characters": tuple(
            {
                "character": TARGET[index],
                **mapping[index],
            }
            for index in range(start, end)
        ),
    }


def audit():
    mapping = event_map()
    words = {
        word: substring_report(word, mapping)
        for word in PATTERNS
    }
    phrases = {
        "a leaf": TARGET.find("aleaf"),
        "a nest": TARGET.find("anest"),
    }
    if any(position < 0 for position in phrases.values()):
        raise AssertionError("thematic phrase disappeared")

    nest_e = words["nest"]["characters"][1]
    if (
        nest_e["character"] != "e"
        or nest_e["event"] != 21
        or nest_e["color"] != "F"
    ):
        raise AssertionError("FEFE no longer supplies the e in nest")

    singles = {}
    for word in PATTERNS:
        favorable, total, rate = exact_subset_rate(SOURCE, SUBSET_SIZE, word)
        singles[word] = {
            "favorable": favorable,
            "total": total,
            "rate": rate,
        }
    favorable, total, rate = exact_joint_rate(SOURCE, SUBSET_SIZE, PATTERNS)
    return {
        "source_length": len(SOURCE),
        "subset_size": SUBSET_SIZE,
        "selected": TARGET,
        "rendering": "ncs YANG cahiriasog A LEAF ay A NEST ve",
        "phrases_zero_based": phrases,
        "words": words,
        "single_rates": singles,
        "joint": {
            "patterns": PATTERNS,
            "favorable": favorable,
            "total": total,
            "rate": rate,
            "one_in": total / favorable,
        },
        "verdict": (
            "The literal cluster and its Phase-48 mechanical reconstruction "
            "are real, and FEFE specifically supplies the e in nest. The "
            "uniform-subset joint rate does not model post-hoc vocabulary "
            "selection, possible community search, or creator intent. Phase "
            "132's broad pre-existing-dictionary control supersedes any "
            "significance reading and classifies the cluster as preserve-only, "
            "not a password, recognition checkpoint, or basis for downstream "
            "sweeps."
        ),
    }


def brute_joint(source, subset_size, patterns):
    favorable = 0
    total = 0
    for positions in itertools.combinations(range(len(source)), subset_size):
        selected = "".join(source[position] for position in positions)
        total += 1
        favorable += int(all(pattern in selected for pattern in patterns))
    return favorable, total


def self_test():
    cases = (
        ("xyangzleafqnest", 12, ("yang", "leaf", "nest")),
        ("abababa", 4, ("aba", "bab")),
        ("abcdef", 3, ("ab", "ef")),
    )
    for source, subset_size, patterns in cases:
        expected = brute_joint(source, subset_size, patterns)
        actual = exact_joint_rate(source, subset_size, patterns)[:2]
        if actual != expected:
            raise AssertionError(
                f"joint DP mismatch for {source!r}: {actual} != {expected}"
            )
    report = audit()
    if report["joint"]["favorable"] != 4_004_246_800_477_440:
        raise AssertionError("real joint favorable count changed")
    print("[*] self-test OK")


def print_report(report):
    print(f"[*] selected: {report['selected']}")
    print(f"[*] rendering: {report['rendering']}")
    for word, details in report["words"].items():
        print(
            f"[*] {word}: output[{details['start_zero_based']}:"
            f"{details['end_exclusive']}], events={details['events']}, "
            f"colors={details['colors']}, "
            f"uniform-subset rate={report['single_rates'][word]['rate']:.12g}"
        )
    joint = report["joint"]
    print(
        f"[*] joint {joint['patterns']}: {joint['favorable']}/"
        f"{joint['total']} = {joint['rate']:.12g} "
        f"(1 in {joint['one_in']:.3f})"
    )
    print(f"[*] verdict: {report['verdict']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    print_report(audit())


if __name__ == "__main__":
    main()
