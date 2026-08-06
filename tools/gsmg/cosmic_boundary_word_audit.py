#!/usr/bin/env python3
"""Test the 27 creator-clause words against Cosmic's 27 authored boundaries."""

import argparse
import base64
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cb_common import printable_z_score  # noqa: E402
from page_structure_audit import DEFAULT_HTML, TextareaParser  # noqa: E402

CREATOR_CLAUSE = (
    "yin yang we wont give away the password its in front of your eyes but "
    "youre not seeing it very last step is a true giveaway promised"
)


def load_cosmic_lines(path=DEFAULT_HTML):
    parser = TextareaParser()
    parser.feed(Path(path).read_text())
    if len(parser.textareas) != 2:
        raise ValueError(f"expected two textareas, found {len(parser.textareas)}")
    lines = parser.textareas[1].splitlines()
    if len(lines) != 28 or set(map(len, lines)) != {64}:
        raise AssertionError("Cosmic textarea is not 28 authored 64-character lines")
    return lines


def decode_base64_rail(rail):
    padding = "=" * (-len(rail) % 4)
    return base64.b64decode(rail + padding, validate=True)


def candidate_rails(lines, words):
    if len(words) != len(lines) - 1:
        raise ValueError("word count must equal the number of line boundaries")
    before = "".join(lines[index][-1] for index in range(len(words)))
    after = "".join(lines[index + 1][0] for index in range(len(words)))
    return {
        "odd_before": "".join(
            before[index] if len(word) % 2 else after[index]
            for index, word in enumerate(words)
        ),
        "even_before": "".join(
            before[index] if len(word) % 2 == 0 else after[index]
            for index, word in enumerate(words)
        ),
        "length_before": "".join(
            lines[index][-len(word)]
            for index, word in enumerate(words)
        ),
        "length_after": "".join(
            lines[index + 1][len(word) - 1]
            for index, word in enumerate(words)
        ),
    }


def score_rail(rail):
    decoded = decode_base64_rail(rail)
    return printable_z_score(decoded), decoded


def max_score(lines, words):
    return max(score_rail(rail)[0] for rail in candidate_rails(lines, words).values())


def self_test():
    assert len(CREATOR_CLAUSE.split()) == 27
    assert decode_base64_rail("SGVsbG8") == b"Hello"
    lines = ["A" * 64 for _ in range(28)]
    words = ["a"] * 27
    rails = candidate_rails(lines, words)
    assert set(rails) == {
        "odd_before",
        "even_before",
        "length_before",
        "length_after",
    }
    assert set(rails.values()) == {"A" * 27}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20260725)
    args = parser.parse_args()

    self_test()
    lines = load_cosmic_lines()
    words = CREATOR_CLAUSE.split()
    rails = candidate_rails(lines, words)
    scored = {
        label: score_rail(rail)
        for label, rail in rails.items()
    }
    real_max = max(score for score, _ in scored.values())

    rng = random.Random(args.seed)
    at_least_as_good = 0
    null_total = 0.0
    null_max = float("-inf")
    for _ in range(args.trials):
        shuffled = words.copy()
        rng.shuffle(shuffled)
        score = max_score(lines, shuffled)
        null_total += score
        null_max = max(null_max, score)
        at_least_as_good += score >= real_max
    empirical_p = (at_least_as_good + 1) / (args.trials + 1)

    print("words:", len(words))
    print("boundaries:", len(lines) - 1)
    for label, rail in rails.items():
        score, decoded = scored[label]
        print(
            label,
            f"rail={rail}",
            f"z={score:.4f}",
            f"decoded={decoded!r}",
        )
    print("real family max:", f"{real_max:.4f}")
    print("null mean:", f"{null_total / args.trials:.4f}")
    print("null max:", f"{null_max:.4f}")
    print("at least as good:", f"{at_least_as_good}/{args.trials}")
    print("empirical p:", f"{empirical_p:.6f}")


if __name__ == "__main__":
    main()
