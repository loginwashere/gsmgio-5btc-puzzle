#!/usr/bin/env python3
"""Exact output-equivalence census for Phase 430's sealed 16! Bifid family.

This is a combinatorial audit, not a language or password search.  It groups
the 240 ordered placements of G and H by their canonical decoded-cell
templates, then counts injective assignments of the other fourteen symbols to
the free cells that are actually visible in each template.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from data import FAED


ALPHABET = "ABCDEFGHIKLMNOPQRSTUVWXYZ"
BASE_SQUARE = "DBIFHCEGAKLMNOPQRSTUVWXYZ"
FREE_SYMBOLS = "GHKLMNOPQRUVWXYZ"
OTHER_FREE_SYMBOLS = FREE_SYMBOLS[2:]
FREE_POSITIONS = (7, 4, 9, 10, 11, 12, 13, 14, 15, 16, 19, 20, 21, 22, 23, 24)
FAED_SHA256 = "585ee5d801486348f3396b3301bc87f14420204ed3242e67bc53d60cfed14664"
TOTAL_RANKS = math.factorial(16)


def normalized_faed() -> str:
    return "".join(ch for ch in FAED.upper() if ch.isalpha())


def source_positions(g_position: int, h_position: int) -> dict[str, int]:
    positions = {
        symbol: cell
        for cell, symbol in enumerate(BASE_SQUARE)
        if symbol not in "GH"
    }
    positions["G"] = g_position
    positions["H"] = h_position
    return positions


def decoded_cells(g_position: int, h_position: int) -> tuple[int, ...]:
    positions = source_positions(g_position, h_position)
    coordinates: list[int] = []
    for symbol in normalized_faed():
        row, column = divmod(positions[symbol], 5)
        coordinates.extend((row, column))
    length = len(coordinates) // 2
    return tuple(
        coordinates[index] * 5 + coordinates[length + index]
        for index in range(length)
    )


def canonical_template(
    g_position: int, h_position: int
) -> tuple[tuple[str, object], ...]:
    """Return literals and first-occurrence-numbered free-cell variables."""
    variable_ids: dict[int, int] = {}
    tokens: list[tuple[str, object]] = []
    for cell in decoded_cells(g_position, h_position):
        if cell == g_position:
            tokens.append(("literal", "G"))
        elif cell == h_position:
            tokens.append(("literal", "H"))
        elif cell in FREE_POSITIONS:
            variable_id = variable_ids.setdefault(cell, len(variable_ids))
            tokens.append(("variable", variable_id))
        else:
            tokens.append(("literal", BASE_SQUARE[cell]))
    return tuple(tokens)


def visible_free_cells(g_position: int, h_position: int) -> set[int]:
    other_cells = set(FREE_POSITIONS) - {g_position, h_position}
    return other_cells.intersection(decoded_cells(g_position, h_position))


def decode_square(square: str) -> str:
    positions = {symbol: cell for cell, symbol in enumerate(square)}
    coordinates: list[int] = []
    for symbol in normalized_faed():
        row, column = divmod(positions[symbol], 5)
        coordinates.extend((row, column))
    length = len(coordinates) // 2
    return "".join(
        square[coordinates[index] * 5 + coordinates[length + index]]
        for index in range(length)
    )


def square_for_placement(
    g_position: int,
    h_position: int,
    assignments: dict[int, str] | None = None,
) -> str:
    remaining_cells = [
        cell for cell in FREE_POSITIONS if cell not in {g_position, h_position}
    ]
    assignments = assignments or dict(zip(remaining_cells, OTHER_FREE_SYMBOLS))
    if set(assignments) != set(remaining_cells):
        raise ValueError("assignments must cover every non-G/H free cell")
    if sorted(assignments.values()) != sorted(OTHER_FREE_SYMBOLS):
        raise ValueError("assignments must be a permutation of the 14 other free symbols")
    square = list(BASE_SQUARE)
    square[g_position] = "G"
    square[h_position] = "H"
    for cell, symbol in assignments.items():
        square[cell] = symbol
    return "".join(square)


def placement_records() -> list[dict[str, object]]:
    records = []
    for g_position in FREE_POSITIONS:
        for h_position in FREE_POSITIONS:
            if g_position == h_position:
                continue
            template = canonical_template(g_position, h_position)
            visible = visible_free_cells(g_position, h_position)
            records.append(
                {
                    "g_position": g_position,
                    "h_position": h_position,
                    "visible_other_free_cells": len(visible),
                    "invisible_other_free_cells": 14 - len(visible),
                    "distinct_output_cells": len(set(decoded_cells(g_position, h_position))),
                    "template": template,
                }
            )
    return records


def audit() -> dict[str, object]:
    faed = normalized_faed()
    assert len(faed) == 570
    assert hashlib.sha256(faed.encode()).hexdigest() == FAED_SHA256
    assert len(set(BASE_SQUARE)) == 25
    assert set(BASE_SQUARE) == set(ALPHABET)

    records = placement_records()
    groups: dict[tuple[tuple[str, object], ...], list[dict[str, object]]] = defaultdict(list)
    for record in records:
        groups[record["template"]].append(record)

    placement_histogram = Counter(
        int(record["visible_other_free_cells"]) for record in records
    )
    template_histogram = Counter(
        (int(group[0]["visible_other_free_cells"]), len(group))
        for group in groups.values()
    )

    unique_outputs = 0
    outputs_by_rank_multiplicity: Counter[int] = Counter()
    for group in groups.values():
        visible = int(group[0]["visible_other_free_cells"])
        group_size = len(group)
        outputs = math.perm(14, visible)
        multiplicity = group_size * math.factorial(14 - visible)
        unique_outputs += outputs
        outputs_by_rank_multiplicity[multiplicity] += outputs

    reconstructed_ranks = sum(
        multiplicity * output_count
        for multiplicity, output_count in outputs_by_rank_multiplicity.items()
    )
    assert reconstructed_ranks == TOTAL_RANKS

    return {
        "phase": 431,
        "question": "exact decoded-output equivalence census for the sealed Phase-430 16! family",
        "inputs": {
            "base_square": BASE_SQUARE,
            "free_symbols": FREE_SYMBOLS,
            "free_positions": list(FREE_POSITIONS),
            "faed_length": len(faed),
            "faed_sha256": FAED_SHA256,
            "rank_count_16_factorial": TOTAL_RANKS,
        },
        "method": {
            "ordered_g_h_placements": len(records),
            "canonical_template_definition": (
                "decoded literals plus first-occurrence-numbered placeholders for "
                "visited non-G/H free cells"
            ),
            "outputs_per_template": "14! / (14-m)!, where m is the visible non-G/H free-cell count",
            "rank_multiplicity_per_output": (
                "canonical-template group size times (14-m)!"
            ),
        },
        "results": {
            "canonical_template_count": len(groups),
            "cross_placement_template_collisions": len(records) - len(groups),
            "placement_count_by_visible_other_free_cells": {
                str(key): value for key, value in sorted(placement_histogram.items())
            },
            "template_count_by_visible_cells_and_group_size": {
                f"m={visible},group={group_size}": count
                for (visible, group_size), count in sorted(template_histogram.items())
            },
            "unique_decoded_outputs": unique_outputs,
            "unique_fraction_of_16_factorial": unique_outputs / TOTAL_RANKS,
            "removable_duplicate_ranks": TOTAL_RANKS - unique_outputs,
            "removable_fraction": 1.0 - unique_outputs / TOTAL_RANKS,
            "raw_to_unique_ratio": TOTAL_RANKS / unique_outputs,
            "output_count_by_rank_multiplicity": {
                str(key): value for key, value in sorted(outputs_by_rank_multiplicity.items())
            },
            "rank_count_reconstructed_from_classes": reconstructed_ranks,
        },
        "interpretation": {
            "global": (
                "Exact quotienting removes 31.98% of Phase-430 ranks; most of the "
                "family remains genuinely output-distinct."
            ),
            "local": (
                "The 42 placements with only five visible other free cells have "
                "9! = 362880 rank representations per decoded output, explaining "
                "large duplicate clusters in retained block winners."
            ),
            "scope": (
                "This is output identity only. It neither evaluates readability nor "
                "changes the sealed Phase-430 exhaustive result."
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit()
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
