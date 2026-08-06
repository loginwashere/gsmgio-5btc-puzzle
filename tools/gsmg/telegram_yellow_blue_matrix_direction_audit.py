#!/usr/bin/env python3
"""Close the literal row/column directions of the recovered Y/B guide matrix.

The historical Telegram guide explicitly places DBBI chunks in a 14x14 matrix
and sums rows.  Columns are the only equally direct untested list of matrix
sums.  This audit fixes the complete family before scoring:

* row sums, forward and reverse;
* column sums, forward and reverse.

The two main diagonal sums are also reported, but their two-letter output is
not language-scored.  The endpoint-assignment null is inherited from the
corrected guide audit: it preserves chunks, endpoints, placement, and the full
four-output family, while shuffling chunk-to-endpoint assignments.
"""

import argparse
import random

from first_piece_color_reconstruction import spiral_top_left_counterclockwise
from quadgram_solver import score as quadgram_score
from telegram_yellow_blue_fefe_sweep import (
    N,
    historical_inputs,
    place_chunks,
)
from telegram_yellow_blue_guide_audit import (
    EXPECTED_MATRIX,
    EXPECTED_OUTPUT,
    output_from_row_sums,
)

EXPECTED_OUTPUTS = {
    "rows_forward": "IZLKESEEDQPPEN",
    "rows_reverse": "NEPPQDEESEKLZI",
    "columns_forward": "GBCXQOGEDMHFEV",
    "columns_reverse": "VEFHMDEGOQXCBG",
}
EXPECTED_DIAGONALS = {
    "main_then_anti": "JF",
    "anti_then_main": "FJ",
}


def matrix_from_spiral(values):
    matrix = [[0] * N for _ in range(N)]
    for value, (row, column) in zip(values, spiral_top_left_counterclockwise()):
        matrix[row][column] = value
    return tuple(tuple(row) for row in matrix)


def directional_outputs(matrix):
    row_sums = tuple(sum(row) for row in matrix)
    column_sums = tuple(
        sum(matrix[row][column] for row in range(N))
        for column in range(N)
    )
    rows = output_from_row_sums(row_sums)
    columns = output_from_row_sums(column_sums)
    main_diagonal = sum(matrix[index][index] for index in range(N))
    anti_diagonal = sum(matrix[index][N - index - 1] for index in range(N))
    diagonals = output_from_row_sums((main_diagonal, anti_diagonal))
    return {
        "outputs": {
            "rows_forward": rows,
            "rows_reverse": rows[::-1],
            "columns_forward": columns,
            "columns_reverse": columns[::-1],
        },
        "diagonals": {
            "main_then_anti": diagonals,
            "anti_then_main": diagonals[::-1],
        },
        "row_sums": row_sums,
        "column_sums": column_sums,
        "diagonal_sums": (main_diagonal, anti_diagonal),
    }


def normalized_quadgram_score(text):
    return quadgram_score(text) / max(1, len(text) - 3)


def caesar_shift(text, shift):
    return "".join(
        chr((ord(character) - ord("A") + shift) % 26 + ord("A"))
        for character in text
    )


def expanded_outputs(outputs, include_caesar):
    if not include_caesar:
        return dict(outputs)
    return {
        f"{label}_caesar_{shift:02d}": caesar_shift(output, shift)
        for label, output in outputs.items()
        for shift in range(26)
    }


def best_family_score(outputs):
    scored = {
        label: normalized_quadgram_score(output)
        for label, output in outputs.items()
    }
    best_label = max(scored, key=lambda label: (scored[label], label))
    return best_label, scored


def historical_family():
    report = directional_outputs(EXPECTED_MATRIX)
    best_label, scores = best_family_score(report["outputs"])
    report["scores"] = scores
    report["best_label"] = best_label
    report["best_score"] = scores[best_label]
    return report


def shuffle_gate(trials, seed, include_caesar=False):
    chunks, endpoints = historical_inputs()
    real = historical_family()
    real_scored_outputs = expanded_outputs(real["outputs"], include_caesar)
    real_best_label, real_scores = best_family_score(real_scored_outputs)
    real = dict(real)
    real["scored_outputs"] = real_scored_outputs
    real["scores"] = real_scores
    real["best_label"] = real_best_label
    real["best_score"] = real_scores[real_best_label]
    rng = random.Random(seed)
    indices = list(range(len(chunks)))
    at_least_as_good = 0
    null_scores = []
    for _ in range(trials):
        rng.shuffle(indices)
        shuffled = tuple(chunks[index] for index in indices)
        values, _ = place_chunks(shuffled, endpoints, "later_wins")
        outputs = expanded_outputs(
            directional_outputs(matrix_from_spiral(values))["outputs"],
            include_caesar,
        )
        _, scores = best_family_score(outputs)
        trial_best = max(scores.values())
        null_scores.append(trial_best)
        at_least_as_good += trial_best >= real["best_score"]
    return {
        "real": real,
        "trials": trials,
        "seed": seed,
        "include_caesar": include_caesar,
        "at_least_as_good": at_least_as_good,
        "empirical_p": (at_least_as_good + 1) / (trials + 1),
        "null_mean": sum(null_scores) / len(null_scores),
        "null_max": max(null_scores),
    }


def self_test():
    synthetic = tuple(
        tuple(row * N + column for column in range(N))
        for row in range(N)
    )
    assert matrix_from_spiral(
        tuple(
            synthetic[row][column]
            for row, column in spiral_top_left_counterclockwise()
        )
    ) == synthetic

    report = historical_family()
    assert report["outputs"] == EXPECTED_OUTPUTS
    assert report["diagonals"] == EXPECTED_DIAGONALS
    assert report["row_sums"] == (
        34, 51, 37, 36, 30, 44, 56, 56, 55, 42, 41, 15, 56, 13,
    )
    assert report["column_sums"] == (
        6, 27, 28, 23, 16, 66, 32, 56, 29, 64, 59, 57, 56, 47,
    )
    assert report["diagonal_sums"] == (35, 83)
    assert report["outputs"]["rows_forward"] == EXPECTED_OUTPUT
    assert caesar_shift("XYZ", 3) == "ABC"
    expanded = expanded_outputs({"rows": "ABC"}, True)
    assert len(expanded) == 26
    assert expanded["rows_caesar_04"] == "EFG"
    print(
        "[*] self-test OK: historical matrix row/column directions and "
        "main-diagonal sums reproduced"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=5_000)
    parser.add_argument("--seed", type=int, default=20260729)
    parser.add_argument(
        "--caesar",
        action="store_true",
        help="include all 26 Caesar shifts of every row/column direction",
    )
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    self_test()
    if args.self_test:
        return

    result = shuffle_gate(args.trials, args.seed, args.caesar)
    real = result["real"]
    for label, output in real["outputs"].items():
        print(
            f"[*] {label}: {output} "
            f"score={normalized_quadgram_score(output):.6f}"
        )
    print(
        f"[*] main diagonals: {real['diagonals']} "
        f"sums={real['diagonal_sums']} (reported, not language-scored)"
    )
    if args.caesar:
        print(
            f"[*] best Caesar-family member: {real['best_label']} -> "
            f"{real['scored_outputs'][real['best_label']]}"
        )
    print(
        f"[*] family-wise endpoint-assignment null: trials={result['trials']} "
        f"seed={result['seed']} real_best={real['best_label']} "
        f"{real['best_score']:.6f} null_mean={result['null_mean']:.6f} "
        f"null_max={result['null_max']:.6f} "
        f"at_least={result['at_least_as_good']}/{result['trials']} "
        f"p={result['empirical_p']:.6f}"
    )
    print(
        "[*] verdict: promote a direction or Caesar shift only if the complete "
        "declared family is exceptional under the same family-wise null; "
        "otherwise close that extension of the historical guide."
    )


if __name__ == "__main__":
    main()
