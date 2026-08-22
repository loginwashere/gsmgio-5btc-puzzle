#!/usr/bin/env python3
"""Reconstruct `matrixsumlist` and bounded Architect-choice indexing."""

import itertools
import re
import subprocess
from pathlib import Path

from first_piece_color_reconstruction import DEFAULT_IMAGE, reconstruct

EXPECTED_PRIME = 574061
EXPECTED_SUM_LIST = (23, 16, 7)
NINE_SYMBOLS = "abcdefghi"
PDF_PATH = (
    Path(__file__).resolve().parents[2]
    / "wordlists"
    / "matrix"
    / "the-matrix-reloaded-2003.pdf"
)


def load_architect_words(path=PDF_PATH):
    completed = subprocess.run(
        ["pdftotext", "-layout", str(path), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    normalized = re.sub(r"\s+", " ", completed.stdout)
    start_match = re.search(r"Which brings us at last to the", normalized)
    if not start_match:
        raise ValueError("Architect speech start was not found")
    first_end_match = re.search(
        r"as both beginning and end\.",
        normalized[start_match.start():],
    )
    if not first_end_match:
        raise ValueError("Architect first dialogue block end was not found")
    first_end = start_match.start() + first_end_match.end()
    second_start_match = re.search(r"There are two doors,", normalized[first_end:])
    if not second_start_match:
        raise ValueError("Architect second dialogue block start was not found")
    second_start = first_end + second_start_match.start()
    end_match = re.search(
        r"As you adequately put, the problem is choice\.",
        normalized[second_start:],
    )
    if not end_match:
        raise ValueError("Architect choice marker was not found")
    end = second_start + end_match.end()
    first_block = normalized[start_match.start():first_end]
    second_block = normalized[second_start:end]
    tokens = words(first_block) + words(second_block)
    if not tokens or tokens[-1] != "choice":
        raise AssertionError("Architect extraction did not end at choice")
    continuation = normalized[end:end + 500]
    continuation_match = re.search(r"\bBut we already know\b", continuation)
    if not continuation_match:
        raise AssertionError("Architect continuation was not found after choice")
    return tokens[:-1], continuation_match.group(0).split()[0].lower()


def matrixsumlist(prime):
    digits = [int(character) for character in str(prime)]
    if len(digits) != 6:
        raise ValueError("expected a six-digit prime")
    matrix = [digits[:3], digits[3:]]
    row_sums = tuple(sum(row) for row in matrix)
    result = (sum(digits), *row_sums)
    if result != EXPECTED_SUM_LIST:
        raise AssertionError(f"matrix sum list mismatch: {result}")
    return matrix, result


def matching_matrix_orientations(prime, expected_rows):
    digits = [int(character) for character in str(prime)]
    matches = []
    for direction, sequence in (("forward", digits), ("reverse", digits[::-1])):
        for rows in (1, 2, 3, 6):
            columns = len(sequence) // rows
            matrix = [
                sequence[offset:offset + columns]
                for offset in range(0, len(sequence), columns)
            ]
            row_values = tuple(sum(row) for row in matrix)
            column_values = tuple(
                sum(matrix[row][column] for row in range(rows))
                for column in range(columns)
            )
            if row_values == expected_rows:
                matches.append(f"{direction}_{rows}x{columns}_rows")
            if column_values == expected_rows:
                matches.append(f"{direction}_{rows}x{columns}_columns")
    return matches


def words(text):
    return re.findall(r"[A-Za-z]+", text.lower())


def bounded_indexings(tokens, indices):
    if max(indices) >= len(tokens):
        raise ValueError("source is too short for zero-based indexing")
    return {
        "forward_one": tuple(tokens[index - 1] for index in indices),
        "forward_zero": tuple(tokens[index] for index in indices),
        "backward_one": tuple(tokens[-index] for index in indices),
        "backward_zero": tuple(tokens[-index - 1] for index in indices),
    }


def edge_letters(selected):
    return (
        "".join(token[0] for token in selected),
        "".join(token[-1] for token in selected),
    )


def add_shifts(text, shifts):
    if len(text) != len(shifts):
        raise ValueError("text and shift list must have the same length")
    return "".join(
        chr((ord(character) - ord("a") + shift) % 26 + ord("a"))
        for character, shift in zip(text, shifts)
    )


def order_payload_by_key(key, payload):
    if len(key) != len(payload):
        raise ValueError("key and payload must have the same length")
    order = sorted(range(len(key)), key=lambda index: (key[index], index))
    return "".join(payload[index] for index in order)


def mirror9(character):
    if character not in NINE_SYMBOLS:
        raise ValueError(f"not an a-i symbol: {character!r}")
    return NINE_SYMBOLS[-NINE_SYMBOLS.index(character) - 1]


def exact_chain_null(tokens, boundary_word, end_marker):
    counts = {
        "triples": 0,
        "boundary": 0,
        "end_marker": 0,
        "joint": 0,
    }
    joint_indices = []
    for indices in itertools.permutations(range(1, len(tokens) + 1), 3):
        selected = tuple(tokens[index - 1] for index in indices)
        first_edges, last_edges = edge_letters(selected)
        boundary_match = first_edges == boundary_word
        end_marker_match = add_shifts(last_edges, indices) == end_marker
        counts["triples"] += 1
        counts["boundary"] += boundary_match
        counts["end_marker"] += end_marker_match
        counts["joint"] += boundary_match and end_marker_match
        if boundary_match and end_marker_match:
            joint_indices.append(indices)
    return counts, joint_indices


def exact_rail_null(tokens, boundary_word, rail_word):
    counts = {
        "triples": 0,
        "boundary": 0,
        "rail_word": 0,
        "joint": 0,
    }
    joint_indices = []
    for indices in itertools.permutations(range(1, len(tokens) + 1), 3):
        selected = tuple(tokens[index - 1] for index in indices)
        first_edges, last_edges = edge_letters(selected)
        boundary_match = first_edges == boundary_word
        rail_match = order_payload_by_key(first_edges, last_edges) == rail_word
        counts["triples"] += 1
        counts["boundary"] += boundary_match
        counts["rail_word"] += rail_match
        counts["joint"] += boundary_match and rail_match
        if boundary_match and rail_match:
            joint_indices.append(indices)
    return counts, joint_indices


def audit():
    """Compute and hard-assert every claim this module makes; return a
    report dict so both `self_test()` and `main()` print from one
    computation instead of duplicating it (and drifting apart over time)."""
    color_result = reconstruct(DEFAULT_IMAGE)
    prime = color_result["prime_value"]
    if prime != EXPECTED_PRIME:
        raise AssertionError(f"unexpected first-piece prime: {prime}")
    matrix, sum_list = matrixsumlist(prime)
    orientation_matches = matching_matrix_orientations(prime, sum_list[1:])
    if orientation_matches != ["forward_2x3_rows"]:
        raise AssertionError(f"matrix orientation is not unique: {orientation_matches}")

    architect_words, first_word_after_choice = load_architect_words()
    results = bounded_indexings(architect_words, sum_list)
    boundary_matches = [
        label for label, selected in results.items()
        if edge_letters(selected)[0] == first_word_after_choice
    ]
    if boundary_matches != ["forward_one"]:
        raise AssertionError(f"choice-boundary rule is not unique: {boundary_matches}")

    selected = results["forward_one"]
    first_edges, last_edges = edge_letters(selected)
    if first_edges != first_word_after_choice:
        raise AssertionError(
            f"boundary validation mismatch: {first_edges} != {first_word_after_choice}"
        )
    ordered_end_rail = order_payload_by_key(first_edges, last_edges)
    if ordered_end_rail != "hey":
        raise AssertionError(f"beginning-keyed end rail mismatch: {ordered_end_rail}")

    first_9ary = "".join(character for character in first_edges if character in NINE_SYMBOLS)
    last_9ary = "".join(character for character in last_edges if character in NINE_SYMBOLS)
    if first_9ary != "b" or last_9ary != "he":
        raise AssertionError(
            f"unexpected a-i rail symbols: {first_9ary!r}/{last_9ary!r}"
        )
    if mirror9(first_9ary) != last_9ary[0] or mirror9(last_9ary[1]) != last_9ary[1]:
        raise AssertionError("B/H mirror pair with fixed E center was not recovered")

    rail_rebus = last_edges + first_edges
    if rail_rebus != "hyebut":
        raise AssertionError(f"unexpected rail rebus: {rail_rebus}")

    end_of_line = add_shifts(last_edges, sum_list)
    if end_of_line != "eol":
        raise AssertionError(f"end-of-line validation mismatch: {end_of_line}")

    null_counts, joint_indices = exact_chain_null(
        architect_words,
        first_word_after_choice,
        end_of_line,
    )
    if sum_list not in joint_indices:
        raise AssertionError("matrix sum list is absent from the joint null matches")

    rail_counts, rail_joint_indices = exact_rail_null(
        architect_words,
        first_word_after_choice,
        ordered_end_rail,
    )

    return {
        "prime": prime,
        "matrix": matrix,
        "sum_list": sum_list,
        "orientation": orientation_matches[0],
        "architect_word_count": len(architect_words),
        "results": results,
        "first_word_after_choice": first_word_after_choice,
        "first_edges": first_edges,
        "last_edges": last_edges,
        "ordered_end_rail": ordered_end_rail,
        "first_9ary": first_9ary,
        "last_9ary": last_9ary,
        "rail_rebus": rail_rebus,
        "end_of_line": end_of_line,
        "null_counts": null_counts,
        "joint_indices": joint_indices,
        "rail_counts": rail_counts,
        "rail_joint_indices": rail_joint_indices,
        "sum_list_in_rail_joint": sum_list in rail_joint_indices,
    }


def self_test():
    report = audit()
    assert report["null_counts"] == {"triples": 357840, "boundary": 160, "end_marker": 24, "joint": 4}
    assert report["rail_counts"]["boundary"] == 160
    assert report["rail_counts"]["rail_word"] == 114
    assert report["rail_counts"]["joint"] == 12
    assert report["sum_list_in_rail_joint"]
    print(
        "[*] self-test OK: prime 574061, unique forward_2x3_rows orientation, "
        "BUT/HYE/EOL chain, and exact 357,840-triple null counts (160/24/4, "
        "12 rail-joint) all reproduce"
    )
    return report


def main():
    report = self_test()
    print("prime:", report["prime"])
    print("matrix:")
    for row in report["matrix"]:
        print(" ", row)
    print("matrix sum list:", report["sum_list"])
    print("unique orientation:", report["orientation"])
    print("words before Architect choice:", report["architect_word_count"])
    for label, selected in report["results"].items():
        print(f"{label}: {' '.join(selected)}")
    print("forward_one first letters:", report["first_edges"])
    print("forward_one last letters:", report["last_edges"])
    print("first Architect word after choice:", report["first_word_after_choice"])
    print("last letters ordered by first letters:", report["ordered_end_rail"])
    print("a-i symbols in beginning/end rails:", report["first_9ary"], report["last_9ary"])
    print("end rail followed by beginning rail:", report["rail_rebus"], "(H | YE | BUT)")
    print("last letters + matrix sum list:", report["end_of_line"])
    print("exact ordered-triple null:")
    for label in ("triples", "boundary", "end_marker", "joint"):
        print(f"  {label}: {report['null_counts'][label]}")
    print("  joint indices:", report["joint_indices"])
    print("exact beginning-keyed-end-rail null:")
    for label in ("triples", "boundary", "rail_word", "joint"):
        print(f"  {label}: {report['rail_counts'][label]}")
    print("  derived indices among joint matches:", report["sum_list_in_rail_joint"])


if __name__ == "__main__":
    main()
