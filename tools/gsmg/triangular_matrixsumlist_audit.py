#!/usr/bin/env python3
"""Audit the exact 91 + 104 + 1 = 14^2 DBBI/matrix-bit geometry.

DBBI has T13=91 raw characters.  The binary-ASCII spelling of
``matrixsumlist`` has 104 bits, one fewer than T14=105.  This audit inserts
the only literal binary zero (``a``) at every possible position, treats that
entire 105-way choice as one fitted family, and tests the two transpose-related
ways to place the 91- and 105-cell triangular halves of a 14x14 square.

No AES oracle is used.  The bounded structural consumers are:

* a paired bit chooses keep (0) versus mirror9 (1) for each DBBI character;
* all 196 cell values are summed by row modulo 26, matching the historical
  guide's output convention;
* paired bits are checked against the guide's eight within-chunk ``be`` merges
  versus the two literal ``be`` pairs split by prime-chunk boundaries.

Every reported tail probability calibrates the maximum over both orientations
and all 105 insertion positions against shuffled 104-bit controls with the
same bit counts.  This prevents selecting the nicest missing-zero position
after seeing the output.
"""

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from data import DBBI  # noqa: E402
from page_structure_audit import MATRIX_INSTRUCTION, binary_ascii  # noqa: E402
from salt_selector_permutation_audit import (  # noqa: E402
    load_quadgrams,
    quadgram_score,
)
from telegram_yellow_blue_guide_audit import (  # noqa: E402
    EXPECTED_CHUNKS,
    EXPECTED_OUTPUT,
)


SIDE = 14
ZERO = "a"
BITS = binary_ascii(MATRIX_INSTRUCTION)
ORIENTATIONS = ("dbbi_upper", "dbbi_lower")
DEFAULT_TRIALS = 2000
MARKERS = ("seed", "matrix", "list", "bitcoin", "choice", "salvation")


def triangular(value):
    return value * (value + 1) // 2


def mirror9(char):
    if char < "a" or char > "i":
        raise ValueError(f"mirror9 requires a-i, got {char!r}")
    return chr(ord("a") + ord("i") - ord(char))


def insertion_family(bits=BITS):
    return tuple(
        bits[:position] + ZERO + bits[position:]
        for position in range(len(bits) + 1)
    )


def geometry(orientation):
    coords = tuple((row, column) for row in range(SIDE) for column in range(SIDE))
    if orientation == "dbbi_upper":
        dbbi_coords = tuple(cell for cell in coords if cell[0] < cell[1])
        bit_coords = tuple(cell for cell in coords if cell[0] >= cell[1])
    elif orientation == "dbbi_lower":
        dbbi_coords = tuple(cell for cell in coords if cell[0] > cell[1])
        bit_coords = tuple(cell for cell in coords if cell[0] <= cell[1])
    else:
        raise ValueError(f"unknown orientation: {orientation}")
    bit_index = {cell: index for index, cell in enumerate(bit_coords)}
    paired_indices = tuple(bit_index[(column, row)] for row, column in dbbi_coords)
    diagonal_indices = tuple(bit_index[(index, index)] for index in range(SIDE))
    bit_rows = tuple(
        tuple(bit_index[cell] for cell in bit_coords if cell[0] == row)
        for row in range(SIDE)
    )
    dbbi_index = {cell: index for index, cell in enumerate(dbbi_coords)}
    dbbi_row_sums = tuple(
        sum(
            ord(DBBI[dbbi_index[cell]]) - ord("a") + 1
            for cell in dbbi_coords
            if cell[0] == row
        )
        for row in range(SIDE)
    )
    if len(dbbi_coords) != len(DBBI) or len(bit_coords) != len(BITS) + 1:
        raise AssertionError("triangle sizes do not match source lengths")
    return {
        "paired_indices": paired_indices,
        "diagonal_indices": diagonal_indices,
        "bit_rows": bit_rows,
        "dbbi_row_sums": dbbi_row_sums,
    }


GEOMETRIES = {name: geometry(name) for name in ORIENTATIONS}
LITERAL_BE_STARTS = tuple(
    index
    for index in range(len(DBBI) - 1)
    if DBBI[index:index + 2] == "be"
)


def historical_merge_starts(chunks=EXPECTED_CHUNKS):
    starts = []
    cursor = 0
    for chunk in chunks:
        local = 0
        while local < len(chunk):
            if chunk.startswith("be", local):
                starts.append(cursor + local)
                local += 2
            else:
                local += 1
        cursor += len(chunk)
    if cursor != len(DBBI) or "".join(chunks) != DBBI:
        raise AssertionError("historical chunks do not partition DBBI")
    return tuple(starts)


MERGE_STARTS = historical_merge_starts()
SPLIT_BE_STARTS = tuple(
    index for index in LITERAL_BE_STARTS if index not in MERGE_STARTS
)


def paired_bits(bits105, orientation):
    return "".join(bits105[index] for index in GEOMETRIES[orientation]["paired_indices"])


def diagonal_bits(bits105, orientation):
    return "".join(bits105[index] for index in GEOMETRIES[orientation]["diagonal_indices"])


def mirror_output(bits105, orientation):
    selectors = paired_bits(bits105, orientation)
    return "".join(
        char if selector == "a" else mirror9(char)
        for char, selector in zip(DBBI, selectors)
    )


def row_output(bits105, orientation):
    shape = GEOMETRIES[orientation]
    sums = tuple(
        base + sum(bits105[index] == "b" for index in bit_indices)
        for base, bit_indices in zip(shape["dbbi_row_sums"], shape["bit_rows"])
    )
    return "".join(chr(value % 26 + ord("A")) for value in sums), sums


def merge_gap(bits105, orientation):
    selectors = paired_bits(bits105, orientation)
    # The sharp historical distinction is among literal BE pairs: eight were
    # merged inside chunks and two were split by a prime-chunk boundary.
    merge = set(MERGE_STARTS)
    positive = [
        selectors[index] == "b"
        for index in LITERAL_BE_STARTS
        if index in merge
    ]
    negative = [
        selectors[index] == "b"
        for index in LITERAL_BE_STARTS
        if index not in merge
    ]
    return abs(sum(positive) / len(positive) - sum(negative) / len(negative))


def hamming_matches(left, right):
    if len(left) != len(right):
        raise ValueError("Hamming comparison requires equal lengths")
    return sum(a == b for a, b in zip(left, right))


def candidate_rows(bits104, model):
    rows = []
    for insertion, bits105 in enumerate(insertion_family(bits104)):
        for orientation in ORIENTATIONS:
            mirrored = mirror_output(bits105, orientation)
            row_text, row_sums = row_output(bits105, orientation)
            diagonal = diagonal_bits(bits105, orientation)
            rows.append({
                "insertion_zero_based": insertion,
                "orientation": orientation,
                "mirror_output": mirrored,
                "mirror_score": quadgram_score(mirrored.encode("ascii"), model),
                "row_output": row_text,
                "row_sums": row_sums,
                "row_score": quadgram_score(row_text.encode("ascii"), model),
                "guide_matches": hamming_matches(row_text, EXPECTED_OUTPUT),
                "merge_gap": merge_gap(bits105, orientation),
                "diagonal_bits": diagonal,
                "diagonal_integer": int(
                    diagonal.translate(str.maketrans("ab", "01")), 2
                ),
            })
    return rows


def maxima(rows):
    metrics = ("mirror_score", "row_score", "guide_matches", "merge_gap")
    return {
        metric: max(
            rows,
            key=lambda row: (
                row[metric],
                -row["insertion_zero_based"],
                row["orientation"],
            ),
        )
        for metric in metrics
    }


def familywise_null(model, trials, seed):
    rng = random.Random(seed)
    controls = {
        name: []
        for name in ("mirror_score", "row_score", "guide_matches", "merge_gap")
    }
    source = list(BITS)
    for _ in range(trials):
        rng.shuffle(source)
        best = maxima(candidate_rows("".join(source), model))
        for name in controls:
            controls[name].append(best[name][name])
    return controls


def audit(trials=DEFAULT_TRIALS, seed=177):
    if trials < 1:
        raise ValueError("trials must be positive")
    model = load_quadgrams()
    rows = candidate_rows(BITS, model)
    best = maxima(rows)
    controls = familywise_null(model, trials, seed)
    calibration = {}
    for name, row in best.items():
        value = row[name]
        calibration[name] = {
            "value": value,
            "familywise_upper_tail_p": (
                1 + sum(control >= value for control in controls[name])
            ) / (trials + 1),
            "best_candidate": row,
        }
    exact_hits = []
    for row in rows:
        for output_name in ("mirror_output", "row_output"):
            lowered = row[output_name].lower()
            for marker in MARKERS:
                if marker in lowered:
                    exact_hits.append({
                        "insertion_zero_based": row["insertion_zero_based"],
                        "orientation": row["orientation"],
                        "output": output_name,
                        "marker": marker,
                    })
    diagonal_sequences = sorted({row["diagonal_bits"] for row in rows})
    return {
        "identity": {
            "dbbi_length": len(DBBI),
            "t13": triangular(13),
            "instruction": MATRIX_INSTRUCTION,
            "instruction_bit_length": len(BITS),
            "t14": triangular(14),
            "missing_cells": triangular(14) - len(BITS),
            "combined_square_cells": len(DBBI) + len(BITS) + 1,
            "side_squared": SIDE * SIDE,
        },
        "bit_counts_before_insertion": {
            "a": BITS.count("a"),
            "b": BITS.count("b"),
        },
        "inserted_symbol": ZERO,
        "insertion_positions": len(BITS) + 1,
        "orientations": ORIENTATIONS,
        "candidate_count": len(rows),
        "merge_starts_zero_based": MERGE_STARTS,
        "merge_start_count": len(MERGE_STARTS),
        "split_be_starts_zero_based": SPLIT_BE_STARTS,
        "historical_guide_output": EXPECTED_OUTPUT,
        "null_trials": trials,
        "null_seed": seed,
        "calibration": calibration,
        "four_metric_bonferroni_min_p": min(
            1.0,
            min(item["familywise_upper_tail_p"] for item in calibration.values())
            * len(calibration),
        ),
        "exact_marker_hits": exact_hits,
        "unique_diagonal_sequence_count": len(diagonal_sequences),
        "diagonal_sequence_sha256": hashlib.sha256(
            "\n".join(diagonal_sequences).encode("ascii")
        ).hexdigest(),
    }


def self_test():
    assert len(DBBI) == triangular(13) == 91
    assert len(BITS) == 104
    assert len(insertion_family()) == 105
    assert all(len(value) == triangular(14) for value in insertion_family())
    assert BITS.count("a") == 48 and BITS.count("b") == 56
    assert len(MERGE_STARTS) == 8
    assert len(LITERAL_BE_STARTS) == 10 and len(SPLIT_BE_STARTS) == 2
    for orientation in ORIENTATIONS:
        assert len(paired_bits(insertion_family()[0], orientation)) == len(DBBI)
        assert len(diagonal_bits(insertion_family()[0], orientation)) == SIDE
        assert len(row_output(insertion_family()[0], orientation)[0]) == SIDE
    print(
        "[*] self-test OK: 91 + 104 + one zero = 14^2; "
        "two triangular orientations; eight merged and two split be pairs"
    )


def print_report(report):
    identity = report["identity"]
    print(
        "[*] identity: "
        f"DBBI={identity['dbbi_length']}=T13; bits={identity['instruction_bit_length']}; "
        f"bits+zero={identity['t14']}=T14; total={identity['combined_square_cells']}=14^2"
    )
    print(
        f"[*] family: {report['insertion_positions']} zero positions x "
        f"{len(report['orientations'])} orientations = "
        f"{report['candidate_count']} candidates"
    )
    print(
        f"[*] historical be merge starts ({report['merge_start_count']}): "
        f"{report['merge_starts_zero_based']}"
    )
    print(
        "[*] literal be pairs split at chunk boundaries: "
        f"{report['split_be_starts_zero_based']}"
    )
    for name, item in report["calibration"].items():
        row = item["best_candidate"]
        print(
            f"[*] {name}: value={item['value']:.6f} "
            f"familywise_p={item['familywise_upper_tail_p']:.6f} "
            f"at insert={row['insertion_zero_based']} orientation={row['orientation']} "
            f"mirror={row['mirror_output']} row={row['row_output']} "
            f"guide_matches={row['guide_matches']} merge_gap={row['merge_gap']:.6f} "
            f"diagonal={row['diagonal_bits']}"
        )
    print(
        "[*] four-metric Bonferroni minimum p: "
        f"{report['four_metric_bonferroni_min_p']:.6f}"
    )
    print(f"[*] exact marker hits: {len(report['exact_marker_hits'])}")
    print(
        "[*] diagonal family: "
        f"{report['unique_diagonal_sequence_count']} unique sequences, "
        f"sha256={report['diagonal_sequence_sha256']}"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=DEFAULT_TRIALS)
    parser.add_argument("--seed", type=int, default=177)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    self_test()
    if args.self_test:
        return
    report = audit(trials=args.trials, seed=args.seed)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)


if __name__ == "__main__":
    main()
