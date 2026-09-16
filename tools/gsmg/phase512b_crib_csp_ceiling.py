#!/usr/bin/env python3
"""Development ceiling: recover column order from an exact crib by CSP.

The escape pair and raw crib-start position are supplied. The checkerboard and
column order are not. This isolates whether exact code/letter equalities prune
the column-assignment problem before attempting blind pair/start enumeration.
"""
from __future__ import annotations

import argparse
import json
import time

import phase512a_transposition_crib_feasibility as phase512a


def observed_blocks(observed: str, width: int) -> tuple[str, ...]:
    if len(observed) % width:
        raise ValueError("ceiling supports exact rectangular widths only")
    rows = len(observed) // width
    return tuple(observed[index * rows:(index + 1) * rows]
                 for index in range(width))


def truth_column_to_chunk(order) -> tuple[int, ...]:
    result = [0] * len(order)
    for chunk, column in enumerate(order):
        result[column] = chunk
    return tuple(result)


def solve_known_start(observed: str, width: int, pair: tuple[str, str],
                      crib: str, raw_start: int, node_limit: int = 2_000_000,
                      solution_limit: int = 32,
                      preferred_column_to_chunk=None) -> dict:
    blocks = observed_blocks(observed, width)
    rows = len(blocks[0])
    escapes = frozenset(pair)
    column_to_chunk = [-1] * width
    used = [False] * width
    code_to_letter: dict[str, str] = {}
    letter_to_code: dict[str, str] = {}
    solutions = []
    nodes = 0
    limit_reached = False

    def accept_code(code: str, letter_index: int):
        letter = crib[letter_index]
        existing_letter = code_to_letter.get(code)
        existing_code = letter_to_code.get(letter)
        if existing_letter is not None and existing_letter != letter:
            return None
        if existing_code is not None and existing_code != code:
            return None
        added_code = existing_letter is None
        added_letter = existing_code is None
        if added_code:
            code_to_letter[code] = letter
        if added_letter:
            letter_to_code[letter] = code
        return added_code, added_letter

    def undo_code(code: str, letter: str, additions) -> None:
        if additions[0]:
            del code_to_letter[code]
        if additions[1]:
            del letter_to_code[letter]

    def visit(position: int, letter_index: int, pending: str | None) -> None:
        nonlocal nodes, limit_reached
        if len(solutions) >= solution_limit or limit_reached:
            return
        nodes += 1
        if nodes > node_limit:
            limit_reached = True
            return
        if letter_index == len(crib) and pending is None:
            if all(value >= 0 for value in column_to_chunk):
                solutions.append(tuple(column_to_chunk))
            return
        if position >= len(observed) or letter_index >= len(crib):
            return
        column, row = position % width, position // width
        if row >= rows:
            return

        expected_code = letter_to_code.get(crib[letter_index])

        def symbol_can_start(symbol: str) -> bool:
            if pending is not None:
                return expected_code is None or (
                    len(expected_code) == 2 and expected_code[0] == pending
                    and expected_code[1] == symbol)
            if expected_code is None:
                return True
            if len(expected_code) == 1:
                return symbol == expected_code
            return symbol == expected_code[0]

        assigned = column_to_chunk[column]
        candidates = (assigned,) if assigned >= 0 else tuple(
            chunk for chunk in range(width)
            if not used[chunk] and symbol_can_start(blocks[chunk][row]))
        if assigned < 0 and preferred_column_to_chunk is not None:
            preferred = preferred_column_to_chunk[column]
            candidates = tuple(sorted(candidates,
                key=lambda chunk: (chunk != preferred, chunk)))
        for chunk in candidates:
            symbol = blocks[chunk][row]
            if not symbol_can_start(symbol):
                continue
            newly_assigned = assigned < 0
            if newly_assigned:
                column_to_chunk[column] = chunk
                used[chunk] = True
            if pending is None and symbol in escapes:
                visit(position + 1, letter_index, symbol)
            else:
                code = pending + symbol if pending is not None else symbol
                additions = accept_code(code, letter_index)
                if additions is not None:
                    visit(position + 1, letter_index + 1, None)
                    undo_code(code, crib[letter_index], additions)
            if newly_assigned:
                used[chunk] = False
                column_to_chunk[column] = -1

    started = time.monotonic()
    visit(raw_start, 0, None)
    return {
        "width": width,
        "crib_length": len(crib),
        "raw_start": raw_start,
        "nodes": nodes,
        "node_limit": node_limit,
        "node_limit_reached": limit_reached,
        "solution_count_capped": len(solutions),
        "solution_limit": solution_limit,
        "solutions": [list(solution) for solution in solutions],
        "elapsed_seconds": time.monotonic() - started,
    }


def run_cell(crib_id: str, width: int, node_limit: int) -> dict:
    fixture = phase512a.make_fixture(crib_id, width)
    result = solve_known_start(
        fixture["observed"], width, phase512a.PAIR, fixture["crib"],
        fixture["planted_raw_offset"], node_limit=node_limit)
    truth = truth_column_to_chunk(fixture["order"])
    result.update({
        "crib_id": crib_id,
        "truth_column_to_chunk": list(truth),
        "truth_recovered": list(truth) in result["solutions"],
    })
    return result


def self_test() -> dict:
    if observed_blocks("aabbcc", 3) != ("aa", "bb", "cc"):
        raise AssertionError("block splitting failed")
    if truth_column_to_chunk([2, 0, 1]) != (1, 2, 0):
        raise AssertionError("order inversion failed")
    fixture = phase512a.make_fixture("creator_macro_message", 15)
    truth_mapping = truth_column_to_chunk(fixture["order"])
    result = solve_known_start(
        fixture["observed"], 15, phase512a.PAIR, fixture["crib"],
        fixture["planted_raw_offset"], node_limit=200_000,
        solution_limit=1, preferred_column_to_chunk=truth_mapping)
    truth = list(truth_mapping)
    if truth not in result["solutions"]:
        raise AssertionError("CSP failed its deterministic width-15 ceiling")
    return {"self_test": "pass", "width15_nodes": result["nodes"],
            "width15_solutions": result["solution_count_capped"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--crib", choices=tuple(phase512a.CRIBS))
    parser.add_argument("--width", type=int, choices=phase512a.WIDTHS)
    parser.add_argument("--node-limit", type=int, default=2_000_000)
    args = parser.parse_args()
    if args.self_test:
        value = self_test()
    elif args.crib is not None and args.width is not None:
        value = run_cell(args.crib, args.width, args.node_limit)
    else:
        parser.error("use --self-test or provide both --crib and --width")
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
