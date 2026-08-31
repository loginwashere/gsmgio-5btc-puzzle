#!/usr/bin/env python3
"""Test the smallest column-sum extension after authenticated THEFLOWER.

The established frame/parity grammar cannot emit S.  Column sums are the
smallest matrix-native extension that introduces it.  This audit exhausts a
bounded no-reuse endpoint family and records why the tempting hand spelling
of BLOSSOMS is not a derived result.
"""

import itertools
from collections import Counter

from first_hint_hash_audit import PHASE1_PASSWORD
from prime_matrixsum_reconstruction import load_architect_words
from second_prime_matrixsumlist_audit import (
    EXPECTED_COMBINED_MATRIX,
    EXPECTED_MATRIX,
    audit as matrix_audit,
    selected_words,
)


FIRST_MATRIX = ((5, 7, 4), (0, 6, 1))
TARGET = "blossoms"
EXPECTED_AGGREGATE_INDICES = (
    (23, 16, 7, 5, 13, 5),
    (14, 5, 9, 3, 3, 8),
    (37, 21, 16, 8, 16, 13),
)
EXPECTED_AGGREGATE_WORDS = (
    ("both", "ultimately", "the", "last", "fundamental", "last"),
    ("flaw", "last", "of", "us", "us", "moment"),
    ("take", "revealed", "ultimately", "moment", "ultimately", "fundamental"),
)
EXPECTED_LABELED_VARIANTS = 69120
EXPECTED_UNIQUE_VALUES = 31264


def aggregate_indices(matrix):
    """Return total, two row sums, then three column sums."""
    return (
        sum(sum(row) for row in matrix),
        *(sum(row) for row in matrix),
        *(sum(row[column] for row in matrix) for column in range(3)),
    )


def endpoint_rails(words):
    return (
        "".join(word[0] for word in words),
        "".join(word[-1] for word in words),
    )


def ordered_mixed_nodes(first_total, second_rows, second_columns):
    """All natural block orders, row directions, and column permutations.

    Nodes remain labeled, including the two separate column-3 US occurrences.
    """
    blocks = ("total", "rows", "columns")
    for block_order in itertools.permutations(blocks):
        for row_order in (second_rows, second_rows[::-1]):
            for column_order in itertools.permutations(second_columns):
                values = {
                    "total": (first_total,),
                    "rows": row_order,
                    "columns": column_order,
                }
                yield tuple(
                    node for block in block_order for node in values[block]
                )


def mixed_endpoint_family(first_total, second_rows, second_columns):
    """Emit eight letters from six non-repeated words.

    Exactly two words contribute both endpoints (in either direction); the
    remaining four contribute one selected endpoint.  This is the complete
    minimal-length family under those rules.
    """
    counts = Counter()
    hits = []
    unique_values = set()
    for nodes in ordered_mixed_nodes(first_total, second_rows, second_columns):
        counts["node_orders"] += 1
        for double_positions in itertools.combinations(range(6), 2):
            double_positions = frozenset(double_positions)
            for double_directions in itertools.product((0, 1), repeat=2):
                double_direction = dict(
                    zip(sorted(double_positions), double_directions)
                )
                single_positions = tuple(
                    position for position in range(6)
                    if position not in double_positions
                )
                for single_endpoints in itertools.product((0, -1), repeat=4):
                    single_endpoint = dict(
                        zip(single_positions, single_endpoints)
                    )
                    pieces = []
                    for position, (_, word) in enumerate(nodes):
                        if position in double_positions:
                            pair = word[0] + word[-1]
                            if double_direction[position]:
                                pair = pair[::-1]
                            pieces.append(pair)
                        else:
                            pieces.append(word[single_endpoint[position]])
                    value = "".join(pieces)
                    counts["labeled_variants"] += 1
                    unique_values.add(value)
                    if value == TARGET:
                        hits.append(
                            {
                                "nodes": nodes,
                                "double_positions": tuple(sorted(double_positions)),
                                "double_directions": tuple(
                                    double_direction[position]
                                    for position in sorted(double_positions)
                                ),
                                "single_endpoints": tuple(
                                    single_endpoint[position]
                                    for position in single_positions
                                ),
                            }
                        )
    counts["unique_values"] = len(unique_values)
    counts["target_hits"] = len(hits)
    return counts, tuple(hits)


def audit():
    tokens, _ = load_architect_words()
    matrices = (FIRST_MATRIX, EXPECTED_MATRIX, EXPECTED_COMBINED_MATRIX)
    indices = tuple(aggregate_indices(matrix) for matrix in matrices)
    words = tuple(selected_words(tokens, item) for item in indices)
    rails = tuple(endpoint_rails(item) for item in words)

    established = matrix_audit(run_null=False)
    frames = established["frames"]
    closed_values = set()
    for frame in frames:
        for value in (frame, frame[::-1], frame[0::2], frame[1::2]):
            closed_values.add(value)
            closed_values.add(value[::-1])
    closed_alphabet = "".join(sorted(set("".join(closed_values))))

    first_total = (("first_total", indices[0][0]), words[0][0])
    second_rows = tuple(
        ((f"second_row_{number}", index), word)
        for number, (index, word) in enumerate(
            zip(indices[1][1:3], words[1][1:3]), start=1
        )
    )
    second_columns = tuple(
        ((f"second_column_{number}", index), word)
        for number, (index, word) in enumerate(
            zip(indices[1][3:], words[1][3:]), start=1
        )
    )
    family_counts, family_hits = mixed_endpoint_family(
        first_total, second_rows, second_columns
    )

    posthoc_steps = (
        ("BOTH", "initial", "b"),
        ("LAST", "initial", "l"),
        ("OF", "initial", "o"),
        ("US", "ending", "s"),
        ("US", "ending", "s"),
        ("OF", "initial", "o"),
        ("MOMENT", "initial", "m"),
        ("US", "ending", "s"),
    )
    posthoc_value = "".join(step[2] for step in posthoc_steps)
    posthoc_reuse = Counter(step[0] for step in posthoc_steps)

    return {
        "indices": indices,
        "words": words,
        "rails": rails,
        "frames": frames,
        "closed_values": tuple(sorted(closed_values)),
        "closed_alphabet": closed_alphabet,
        "closed_has_s": "s" in closed_alphabet,
        "family_counts": family_counts,
        "family_hits": family_hits,
        "posthoc_steps": posthoc_steps,
        "posthoc_value": posthoc_value,
        "posthoc_reuse": posthoc_reuse,
        "authenticated_continuation": PHASE1_PASSWORD.decode(),
    }


def self_test():
    result = audit()
    assert result["indices"] == EXPECTED_AGGREGATE_INDICES
    assert result["words"] == EXPECTED_AGGREGATE_WORDS
    assert result["rails"] == (
        ("butlfl", "hyetlt"),
        ("flouum", "wtfsst"),
        ("trumuf", "edytyl"),
    )
    assert result["frames"] == ("buth", "flow", "true")
    assert not result["closed_has_s"]
    assert result["family_counts"]["node_orders"] == 72
    assert (
        result["family_counts"]["labeled_variants"]
        == EXPECTED_LABELED_VARIANTS
    )
    assert result["family_counts"]["unique_values"] == EXPECTED_UNIQUE_VALUES
    assert result["family_counts"]["target_hits"] == 0
    assert result["family_hits"] == ()
    assert result["posthoc_value"] == TARGET
    assert result["posthoc_reuse"] == Counter(
        BOTH=1, LAST=1, OF=2, US=3, MOMENT=1
    )
    assert result["authenticated_continuation"].startswith("theflowerblossoms")


def main():
    self_test()
    result = audit()
    print("aggregate indices:", result["indices"])
    for label, words, rails in zip(
        ("first", "second", "combined"), result["words"], result["rails"]
    ):
        print(f"{label}: {' / '.join(word.upper() for word in words)}")
        print(f"  initials={rails[0].upper()} endings={rails[1].upper()}")
    print(
        "closed frame/parity alphabet:",
        result["closed_alphabet"].upper(),
        "(S absent)",
    )
    counts = result["family_counts"]
    print(
        "bounded column extension:",
        f"{counts['target_hits']}/{counts['labeled_variants']} BLOSSOMS hits",
        f"({counts['unique_values']} unique values)",
    )
    print(
        "post-hoc witness:",
        " + ".join(f"{word}[{edge}]" for word, edge, _ in result["posthoc_steps"]),
        "=",
        result["posthoc_value"].upper(),
    )
    print("post-hoc reuse:", dict(result["posthoc_reuse"]))


if __name__ == "__main__":
    main()
