#!/usr/bin/env python3
"""Family-wise calibration of words in the exact 31-character selection.

Two controls address the post-hoc word-spotting problem:

1. A deliberately generous, declared vocabulary grouped into five
   puzzle-clue families. Exact dynamic programming counts uniformly weighted,
   order-preserving 31-of-91 subsets that hit at least as many distinct
   families as the real selection.
2. A broad common-English control using the repository's 7,887-word XKCD
   list. Monte Carlo measures how often a null string contains at least as
   many distinct 4-12-letter dictionary substrings as the real selection,
   under both uniform order-preserving subsets and fixed-mask/source shuffles.

This calibration occurs after ``yang``, ``leaf``, and ``nest`` were noticed.
It quantifies local multiple comparisons but cannot turn the observation into
a preregistered discovery.
"""

import argparse
import hashlib
import itertools
import json
import math
import random
import sys
from collections import Counter
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from denis_prime_extraction_audit import SOURCE, TARGET  # noqa: E402
from flo_prime_walk_provenance_audit import audit as prime_walk_audit  # noqa: E402


FAMILIES = {
    "plant": (
        "seed",
        "planted",
        "flower",
        "blossom",
        "blossoms",
        "rose",
        "leaf",
        "root",
        "stem",
    ),
    "rabbit": ("rabbit", "nest", "door", "hole", "burrow"),
    "polarity": (
        "yellow",
        "blue",
        "prime",
        "primes",
        "yin",
        "yang",
        "duality",
        "opposite",
        "opposites",
        "attract",
    ),
    "matrix": ("matrix", "sum", "list", "choice", "architect"),
    "lock": (
        "password",
        "key",
        "keys",
        "hash",
        "enter",
        "command",
        "answer",
        "eyes",
        "giveaway",
        "promised",
    ),
}
DEFAULT_WORDLIST = (
    Path(__file__).resolve().parents[2] / "wordlists" / "xkcd" / "words.txt"
)
DEFAULT_TRIALS = 1_000_000
DEFAULT_SEED = 20260729
MIN_WORD_LENGTH = 4
MAX_WORD_LENGTH = 12


def family_terms():
    terms = []
    for index, (family, words) in enumerate(FAMILIES.items()):
        for word in words:
            terms.append((word, family, 1 << index))
    return tuple(terms)


def family_automaton():
    terms = family_terms()
    prefixes = {""}
    for word, _, _ in terms:
        prefixes.update(word[:length] for length in range(1, len(word) + 1))

    def transition(state, character):
        combined = state + character
        found = 0
        for word, _, family_bit in terms:
            if combined.endswith(word):
                found |= family_bit
        suffixes = [prefix for prefix in prefixes if combined.endswith(prefix)]
        return max(suffixes, key=len), found

    return transition


def family_hits(text):
    return {
        family: tuple(word for word in words if word in text)
        for family, words in FAMILIES.items()
        if any(word in text for word in words)
    }


def exact_family_rate(source, subset_size, minimum_families):
    transition = family_automaton()

    @lru_cache(maxsize=None)
    def count(position, used, state, found):
        if used == subset_size:
            return int(found.bit_count() >= minimum_families)
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


def normalize_word(line):
    return "".join(character for character in line.strip().lower() if character.isalpha())


def load_common_words(path):
    raw = path.read_bytes()
    words = {
        normalized
        for line in raw.decode("utf-8", errors="ignore").splitlines()
        if MIN_WORD_LENGTH <= len(normalized := normalize_word(line)) <= MAX_WORD_LENGTH
    }
    return words, hashlib.sha256(raw).hexdigest()


def common_word_hits(text, words):
    return {
        text[start:end]
        for start in range(len(text))
        for end in range(
            start + MIN_WORD_LENGTH,
            min(len(text), start + MAX_WORD_LENGTH) + 1,
        )
        if text[start:end] in words
    }


def monte_carlo_controls(source, positions, words, real_score, trials, seed):
    subset_rng = random.Random(seed)
    shuffle_rng = random.Random(seed + 1)
    subset_exceedances = 0
    shuffle_exceedances = 0
    subset_histogram = Counter()
    shuffle_histogram = Counter()
    source_positions = range(len(source))
    zero_based_positions = tuple(position - 1 for position in positions)
    shuffled = list(source)

    for _ in range(trials):
        selected_indices = sorted(
            subset_rng.sample(source_positions, len(zero_based_positions))
        )
        subset_text = "".join(source[index] for index in selected_indices)
        subset_score = len(common_word_hits(subset_text, words))
        subset_histogram[subset_score] += 1
        subset_exceedances += int(subset_score >= real_score)

        shuffle_rng.shuffle(shuffled)
        shuffled_text = "".join(shuffled[index] for index in zero_based_positions)
        shuffle_score = len(common_word_hits(shuffled_text, words))
        shuffle_histogram[shuffle_score] += 1
        shuffle_exceedances += int(shuffle_score >= real_score)

    return {
        "trials": trials,
        "subset_seed": seed,
        "source_shuffle_seed": seed + 1,
        "uniform_subset": {
            "exceedances": subset_exceedances,
            "empirical_p": (subset_exceedances + 1) / (trials + 1),
            "histogram": dict(sorted(subset_histogram.items())),
        },
        "fixed_mask_source_shuffle": {
            "exceedances": shuffle_exceedances,
            "empirical_p": (shuffle_exceedances + 1) / (trials + 1),
            "histogram": dict(sorted(shuffle_histogram.items())),
        },
    }


def audit(wordlist=DEFAULT_WORDLIST, trials=DEFAULT_TRIALS, seed=DEFAULT_SEED):
    clue_hits = family_hits(TARGET)
    real_family_score = len(clue_hits)
    favorable, total, family_rate = exact_family_rate(
        SOURCE,
        len(TARGET),
        real_family_score,
    )
    common_words, wordlist_sha256 = load_common_words(wordlist)
    real_common_hits = tuple(sorted(common_word_hits(TARGET, common_words)))
    prime_walk = prime_walk_audit()
    controls = monte_carlo_controls(
        SOURCE,
        prime_walk["flo_positions"],
        common_words,
        len(real_common_hits),
        trials,
        seed,
    )
    return {
        "selected": TARGET,
        "declared_families": FAMILIES,
        "real_family_hits": clue_hits,
        "real_family_score": real_family_score,
        "exact_uniform_subset_family_control": {
            "threshold": f">={real_family_score} distinct clue families",
            "favorable": favorable,
            "total": total,
            "rate": family_rate,
            "one_in": total / favorable,
        },
        "common_word_control": {
            "wordlist": str(wordlist),
            "wordlist_sha256": wordlist_sha256,
            "loaded_words": len(common_words),
            "length_range": [MIN_WORD_LENGTH, MAX_WORD_LENGTH],
            "real_hits": real_common_hits,
            "real_score": len(real_common_hits),
            **controls,
        },
        "verdict": (
            "The declared creator-family control is rare, but it was defined "
            "after the observed words. The broader common-English uniform-"
            "subset control is the safer multiple-comparisons check. If that "
            "control does not clear the project's p<0.005 bar, the thematic "
            "cluster is ordinary under the load-bearing model and becomes a "
            "preserve-only observation. It must not change the chain or "
            "launch downstream sweeps."
        ),
    }


def brute_family_rate(source, subset_size, minimum_families):
    favorable = 0
    total = 0
    for positions in itertools.combinations(range(len(source)), subset_size):
        selected = "".join(source[position] for position in positions)
        total += 1
        favorable += int(len(family_hits(selected)) >= minimum_families)
    return favorable, total


def self_test():
    original = FAMILIES.copy()
    try:
        FAMILIES.clear()
        FAMILIES.update(
            {
                "one": ("ab",),
                "two": ("bc",),
                "three": ("ca",),
            }
        )
        for source, subset_size, threshold in (
            ("abcabc", 4, 2),
            ("aabbcc", 3, 1),
            ("abcdef", 3, 2),
        ):
            expected = brute_family_rate(source, subset_size, threshold)
            actual = exact_family_rate(source, subset_size, threshold)[:2]
            if actual != expected:
                raise AssertionError(
                    f"family DP mismatch for {source!r}: {actual} != {expected}"
                )
    finally:
        FAMILIES.clear()
        FAMILIES.update(original)

    report = audit(trials=100, seed=7)
    if report["real_family_score"] != 3:
        raise AssertionError("real clue-family score changed")
    if report["common_word_control"]["real_hits"] != (
        "gale",
        "leaf",
        "nest",
        "yang",
    ):
        raise AssertionError("real broad-English hits changed")
    print("[*] self-test OK")


def print_report(report):
    print(f"[*] selected: {report['selected']}")
    print(
        f"[*] clue families: score={report['real_family_score']} "
        f"hits={report['real_family_hits']}"
    )
    family = report["exact_uniform_subset_family_control"]
    print(
        f"[*] exact family-wise uniform-subset control: "
        f"{family['favorable']}/{family['total']} = {family['rate']:.12g} "
        f"(1 in {family['one_in']:.3f})"
    )
    common = report["common_word_control"]
    print(
        f"[*] broad common-English hits ({common['loaded_words']} words, "
        f"length {common['length_range'][0]}-{common['length_range'][1]}): "
        f"{common['real_hits']} score={common['real_score']}"
    )
    print(
        f"[*] uniform-subset Monte Carlo: "
        f"{common['uniform_subset']['exceedances']}/{common['trials']} "
        f"p={common['uniform_subset']['empirical_p']:.9f}"
    )
    print(
        f"[*] fixed-mask/source-shuffle Monte Carlo: "
        f"{common['fixed_mask_source_shuffle']['exceedances']}/"
        f"{common['trials']} "
        f"p={common['fixed_mask_source_shuffle']['empirical_p']:.9f}"
    )
    print(f"[*] verdict: {report['verdict']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wordlist", type=Path, default=DEFAULT_WORDLIST)
    parser.add_argument("--trials", type=int, default=DEFAULT_TRIALS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.trials <= 0:
        parser.error("--trials must be positive")
    if args.self_test:
        self_test()
        return
    report = audit(args.wordlist, args.trials, args.seed)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)


if __name__ == "__main__":
    main()
