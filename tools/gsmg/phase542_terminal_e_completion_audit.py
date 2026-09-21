#!/usr/bin/env python3
"""Phase 542: place DBBI's terminal ``e`` by Selection A conservation.

Selection A keeps 23 picture events representing source bytes 1..23 exactly
once.  Its two omitted events are the ordinary duplicate for source byte 21
(FEFE is retained as byte 21's representative) and source byte 24's endpoint.
The complete 84-token DBBI parse has one unhosted terminal symbol, ``e``.

This audit performs the single completion that preserves the same invariant:
put that 24th object at source byte 24's omitted endpoint, then rerun Phase
535's already-fixed matrix and Architect consumers.  It calls no oracle and
does not search alternative placements or transforms.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from architect_choice_boundary_audit import edge_letters, film_scopes, screenplay_scopes
from phase525_dbbi_selection_a_reconstruction import picture_events
from phase535_selection_a_matrix_composition import run as phase535_run
from telegram_yellow_blue_fefe_sweep import row_sums_from_spiral
from telegram_yellow_blue_guide_audit import output_from_row_sums, token_value


RESULT_PATH = Path(__file__).with_name("phase542_terminal_e_completion_result.json")


def consume(row_sums: tuple[int, ...]) -> list[dict]:
    out = []
    for source, tokens in (
        ("film", film_scopes()["moment_to_choice"]),
        ("screenplay", screenplay_scopes()["moment_to_choice"]),
    ):
        selected = tuple(tokens[-index] for index in row_sums)
        out.append(
            {
                "source": source,
                "word_count": len(tokens),
                "backward_one_words": selected,
                "edges": edge_letters(selected),
            }
        )
    return out


def audit() -> dict:
    prior = phase535_run()
    selection_a = next(
        row for row in prior["rows"]
        if row["logical_length"] == 84
        and row["represents_source_bytes_1_through_23_once"]
    )
    if selection_a["omitted_event_ranks"] != [22, 25]:
        raise AssertionError("Selection A omissions changed")
    if selection_a["unplaced_tail"] != "e":
        raise AssertionError("84-token tail is no longer literal e")

    events = picture_events()
    omitted = {
        event["event_rank"]: event
        for event in events
        if event["event_rank"] in selection_a["omitted_event_ranks"]
    }
    if omitted[22]["source_byte"] != 21 or omitted[25]["source_byte"] != 24:
        raise AssertionError("omitted-event identities changed")

    represented_before = tuple(selection_a["source_bytes"])
    represented_after = tuple(sorted((*represented_before, omitted[25]["source_byte"])))
    if represented_after != tuple(range(1, 25)):
        raise AssertionError("completion does not represent source bytes 1..24 once")
    if tuple(sorted((*represented_before, omitted[22]["source_byte"]))) == tuple(range(1, 25)):
        raise AssertionError("duplicate-byte omission unexpectedly completes the invariant")

    variants = selection_a["variants"]
    if len({tuple(row["spiral_cells"]) for row in variants}) != 1:
        raise AssertionError("Selection A collision policies no longer agree")
    cells = list(variants[0]["spiral_cells"])
    destination = omitted[25]["spiral_0"]
    if cells[destination] != 0:
        raise AssertionError("byte-24 endpoint is already occupied")
    cells[destination] = token_value("e")
    if sum(bool(value) for value in cells) != 84:
        raise AssertionError("completed matrix does not contain 84 occupied cells")

    sums = tuple(row_sums_from_spiral(cells))
    output = output_from_row_sums(sums)
    consumers = consume(sums)
    return {
        "phase": 542,
        "scope": "unique source-byte-conserving placement of the 84-parse terminal e",
        "selection_a_omitted_event_ranks": selection_a["omitted_event_ranks"],
        "omitted_event_source_bytes": {
            str(rank): omitted[rank]["source_byte"] for rank in sorted(omitted)
        },
        "terminal_symbol": "e",
        "terminal_value": token_value("e"),
        "destination_event_rank": 25,
        "destination_source_byte": omitted[25]["source_byte"],
        "destination_spiral_zero_based": destination,
        "represented_source_bytes": represented_after,
        "occupied_cells": sum(bool(value) for value in cells),
        "row_sums": sums,
        "row_sum_output": output,
        "architect_consumers": consumers,
        "recognition": "none",
        "cross_source_consumer_agreement": (
            consumers[0]["backward_one_words"] == consumers[1]["backward_one_words"]
        ),
        "oracle_calls": 0,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }


def self_test() -> dict:
    report = audit()
    assert report["represented_source_bytes"] == tuple(range(1, 25))
    assert report["occupied_cells"] == 84
    assert report["row_sums"] == (34, 51, 37, 36, 30, 49, 62, 58, 32, 34, 41, 15, 56, 13)
    assert report["row_sum_output"] == "IZLKEXKGGIPPEN"
    assert not report["cross_source_consumer_agreement"]
    assert report["oracle_calls"] == 0
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    report = self_test() if args.self_test else audit()
    if args.write:
        RESULT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
