#!/usr/bin/env python3
"""Development CSP using enumerated crib-letter code lengths and MRV columns."""
from __future__ import annotations

import argparse
import itertools
import json
import time

import phase512a_transposition_crib_feasibility as phase512a
import phase512b_crib_csp_ceiling as phase512b


def true_single_letters(fixture: dict) -> frozenset[str]:
    return frozenset(letter for letter in set(fixture["crib"])
                     if len(fixture["board"][letter]) == 1)


def length_patterns(crib: str):
    letters = tuple(sorted(set(crib)))
    minimum_singles = max(0, len(letters) - 18)
    maximum_singles = min(7, len(letters))
    expected = len(letters) * 7 / 25
    counts = sorted(range(minimum_singles, maximum_singles + 1),
                    key=lambda value: (abs(value - expected), value))
    for count in counts:
        for values in itertools.combinations(letters, count):
            yield frozenset(values)


def build_constraints(crib: str, raw_start: int, width: int,
                      single_letters: frozenset[str], raw_length: int = 570):
    by_column: dict[int, list[tuple[int, tuple[str, int], str]]] = {}
    position = raw_start
    for letter in crib:
        components = ((letter, 0, "non_escape"),) if letter in single_letters else (
            (letter, 0, "escape"), (letter, 1, "any"))
        for variable_letter, component, category in components:
            if position >= raw_length:
                return None
            column, row = position % width, position // width
            by_column.setdefault(column, []).append(
                (row, (variable_letter, component), category))
            position += 1
    return by_column, position


def completed_codes(assignments: dict[tuple[str, int], str], crib: str,
                    single_letters: frozenset[str]):
    values = {}
    for letter in set(crib):
        if letter in single_letters:
            if (letter, 0) in assignments:
                values[letter] = assignments[(letter, 0)]
        elif (letter, 0) in assignments and (letter, 1) in assignments:
            values[letter] = assignments[(letter, 0)] + assignments[(letter, 1)]
    return values


def compatible_assignment(constraints, block: str, pair: tuple[str, str],
                          assignments: dict[tuple[str, int], str], crib: str,
                          single_letters: frozenset[str]):
    updates = {}
    escapes = frozenset(pair)
    for row, variable, category in constraints:
        symbol = block[row]
        if category == "escape" and symbol not in escapes:
            return None
        if category == "non_escape" and symbol in escapes:
            return None
        existing = assignments.get(variable, updates.get(variable))
        if existing is not None and existing != symbol:
            return None
        updates[variable] = symbol
    merged = dict(assignments)
    merged.update(updates)
    codes = completed_codes(merged, crib, single_letters)
    if len(set(codes.values())) != len(codes):
        return None
    return updates


def solve_length_pattern(observed: str, width: int, pair: tuple[str, str],
                         crib: str, raw_start: int,
                         single_letters: frozenset[str],
                         node_limit: int = 1_000_000,
                         solution_limit: int = 32,
                         solution_acceptor=None) -> dict:
    blocks = phase512b.observed_blocks(observed, width)
    built = build_constraints(crib, raw_start, width, single_letters, len(observed))
    if built is None:
        return {"nodes": 0, "node_limit_reached": False, "solutions": [],
                "raw_end": None}
    by_column, raw_end = built
    constrained_columns = tuple(sorted(by_column))
    column_to_chunk = [-1] * width
    used = [False] * width
    assignments: dict[tuple[str, int], str] = {}
    solutions = []
    nodes = 0
    limit_reached = False

    def candidates(column: int):
        output = []
        for chunk, block in enumerate(blocks):
            if used[chunk]:
                continue
            updates = compatible_assignment(
                by_column[column], block, pair, assignments, crib, single_letters)
            if updates is not None:
                output.append((chunk, updates))
        return output

    def visit(remaining: tuple[int, ...]) -> None:
        nonlocal nodes, limit_reached
        if len(solutions) >= solution_limit or limit_reached:
            return
        nodes += 1
        if nodes > node_limit:
            limit_reached = True
            return
        if not remaining:
            if len(set(completed_codes(assignments, crib, single_letters).values())) != len(set(crib)):
                return
            solution = tuple(column_to_chunk)
            if solution_acceptor is None or solution_acceptor(solution):
                solutions.append(solution)
            return
        choices = []
        for column in remaining:
            options = candidates(column)
            if not options:
                return
            choices.append((len(options), -len(by_column[column]), column, options))
        _, _, column, options = min(choices, key=lambda row: row[:3])
        next_remaining = tuple(value for value in remaining if value != column)
        for chunk, updates in options:
            added = [variable for variable in updates if variable not in assignments]
            assignments.update(updates)
            used[chunk] = True
            column_to_chunk[column] = chunk
            visit(next_remaining)
            column_to_chunk[column] = -1
            used[chunk] = False
            for variable in added:
                del assignments[variable]

    started = time.monotonic()
    visit(constrained_columns)
    return {
        "nodes": nodes, "node_limit": node_limit,
        "node_limit_reached": limit_reached,
        "solutions": [list(value) for value in solutions],
        "solution_count_capped": len(solutions),
        "constrained_column_count": len(constrained_columns),
        "raw_end": raw_end, "elapsed_seconds": time.monotonic() - started,
    }


def run_true_pattern(crib_id: str, width: int, node_limit: int) -> dict:
    fixture = phase512a.make_fixture(crib_id, width)
    singles = true_single_letters(fixture)
    result = solve_length_pattern(
        fixture["observed"], width, phase512a.PAIR, fixture["crib"],
        fixture["planted_raw_offset"], singles, node_limit=node_limit)
    truth = (list(phase512b.truth_column_to_chunk(fixture["order"]))
             if "order" in fixture else None)
    result.update({
        "crib_id": crib_id, "width": width,
        "single_letter_count": len(singles),
        "single_letters": "".join(sorted(singles)),
        "truth_recovered": truth in result["solutions"],
        "truth_column_to_chunk": truth,
    })
    return result


def run_blind_lengths(crib_id: str, width: int,
                      global_node_limit: int = 2_000_000) -> dict:
    fixture = phase512a.make_fixture(crib_id, width)
    result = search_lengths_at_start(
        fixture, fixture["planted_raw_offset"], global_node_limit)
    result.update({
        "crib_id": crib_id, "width": width,
        "known_pair": list(phase512a.PAIR),
        "known_raw_start": fixture["planted_raw_offset"],
    })
    return result


def search_lengths_at_start(fixture: dict, raw_start: int,
                            global_node_limit: int,
                            patterns=None,
                            pair: tuple[str, str] = phase512a.PAIR) -> dict:
    width = fixture["width"]
    truth = (list(phase512b.truth_column_to_chunk(fixture["order"]))
             if "order" in fixture else None)
    patterns = tuple(length_patterns(fixture["crib"])) if patterns is None else patterns
    patterns_tested = 0
    total_nodes = 0
    hits = []
    node_limit_reached = False
    started = time.monotonic()

    def accepts_token_boundary(column_to_chunk) -> bool:
        order = [0] * width
        for column, chunk in enumerate(column_to_chunk):
            order[chunk] = column
        raw = phase512a.base.Geometry(
            len(fixture["observed"]), width).decrypt(fixture["observed"], order)
        return (
            phase512a.base.segment_raw(raw[:raw_start], pair) is not None
            and phase512a.base.segment_raw(raw, pair) is not None
        )

    for pattern_index, singles in enumerate(patterns):
        remaining = global_node_limit - total_nodes
        if remaining <= 0:
            node_limit_reached = True
            break
        result = solve_length_pattern(
            fixture["observed"], width, pair, fixture["crib"],
            raw_start, singles,
            node_limit=remaining, solution_limit=1,
            solution_acceptor=accepts_token_boundary)
        patterns_tested += 1
        total_nodes += result["nodes"]
        if result["solutions"]:
            solution = result["solutions"][0]
            hits.append({
                "pattern_index": pattern_index,
                "single_letters": "".join(sorted(singles)),
                "column_to_chunk": solution,
                "exact_truth": (solution == truth if truth is not None else None),
                "nodes_for_pattern": result["nodes"],
            })
            break
        if result["node_limit_reached"]:
            node_limit_reached = True
            break
    return {
        "raw_start": raw_start,
        "pair": list(pair),
        "legal_length_pattern_count": len(patterns),
        "patterns_tested": patterns_tested,
        "total_nodes": total_nodes,
        "global_node_limit": global_node_limit,
        "node_limit_reached": node_limit_reached,
        "search_complete": bool(hits) or patterns_tested == len(patterns),
        "hit_count": len(hits), "hits": hits,
        "first_hit_exact_truth": (bool(hits[0]["exact_truth"])
                                  if hits and truth is not None else None),
        "elapsed_seconds": time.monotonic() - started,
    }


def run_blind_pair_and_lengths(crib_id: str, width: int,
                               global_node_limit: int = 20_000_000) -> dict:
    fixture = phase512a.make_fixture(crib_id, width)
    patterns = tuple(length_patterns(fixture["crib"]))
    total_nodes = 0
    pairs_tested = 0
    first_hit = None
    started = time.monotonic()
    for pair_index, pair in enumerate(phase512a.base.ESCAPE_PAIRS):
        remaining = global_node_limit - total_nodes
        if remaining <= 0:
            break
        result = search_lengths_at_start(
            fixture, fixture["planted_raw_offset"], remaining,
            patterns=patterns, pair=pair)
        pairs_tested += 1
        total_nodes += result["total_nodes"]
        if result["hit_count"]:
            first_hit = {
                "pair_index": pair_index, "pair": list(pair),
                "is_planted_pair": pair == phase512a.PAIR,
                **result["hits"][0],
            }
            break
    return {
        "crib_id": crib_id, "width": width,
        "known_raw_start": fixture["planted_raw_offset"],
        "pair_family_size": len(phase512a.base.ESCAPE_PAIRS),
        "pairs_tested": pairs_tested,
        "legal_length_pattern_count_per_pair": len(patterns),
        "total_nodes": total_nodes, "global_node_limit": global_node_limit,
        "first_hit": first_hit,
        "first_hit_is_exact_truth": bool(
            first_hit and first_hit["is_planted_pair"]
            and first_hit["exact_truth"]),
        "elapsed_seconds": time.monotonic() - started,
    }


def run_blind_start_and_lengths(crib_id: str, width: int,
                                global_node_limit: int = 20_000_000,
                                max_starts: int | None = None) -> dict:
    fixture = phase512a.make_fixture(crib_id, width)
    patterns = tuple(length_patterns(fixture["crib"]))
    maximum_start = len(fixture["observed"]) - len(fixture["crib"])
    total_nodes = 0
    starts_tested = 0
    started = time.monotonic()
    first_hit = None
    start_family = range(maximum_start + 1)
    if max_starts is not None:
        start_family = range(min(maximum_start + 1, max_starts))
    for raw_start in start_family:
        remaining = global_node_limit - total_nodes
        if remaining <= 0:
            break
        result = search_lengths_at_start(
            fixture, raw_start, remaining, patterns=patterns)
        starts_tested += 1
        total_nodes += result["total_nodes"]
        if result["hit_count"]:
            first_hit = {
                "raw_start": raw_start,
                "is_planted_raw_start": raw_start == fixture["planted_raw_offset"],
                **result["hits"][0],
            }
            break
    return {
        "crib_id": crib_id, "width": width,
        "known_pair": list(phase512a.PAIR),
        "planted_raw_start": fixture["planted_raw_offset"],
        "raw_starts_in_family": maximum_start + 1,
        "max_starts_requested": max_starts,
        "starts_tested": starts_tested,
        "legal_length_pattern_count_per_start": len(patterns),
        "total_nodes": total_nodes,
        "global_node_limit": global_node_limit,
        "first_hit": first_hit,
        "first_hit_is_exact_truth": bool(
            first_hit and first_hit["is_planted_raw_start"]
            and first_hit["exact_truth"]),
        "elapsed_seconds": time.monotonic() - started,
    }


def run_blind_pair_start_lengths(crib_id: str, width: int,
                                 global_node_limit: int = 20_000_000,
                                 max_starts: int | None = None) -> dict:
    fixture = phase512a.make_fixture(crib_id, width)
    patterns = tuple(length_patterns(fixture["crib"]))
    maximum_start = len(fixture["observed"]) - len(fixture["crib"])
    start_family = range(maximum_start + 1)
    if max_starts is not None:
        start_family = range(min(maximum_start + 1, max_starts))
    total_nodes = 0
    cells_tested = 0
    starts_tested = 0
    first_hit = None
    started = time.monotonic()
    exhausted = False
    for raw_start in start_family:
        starts_tested += 1
        for pair_index, pair in enumerate(phase512a.base.ESCAPE_PAIRS):
            remaining = global_node_limit - total_nodes
            if remaining <= 0:
                exhausted = True
                break
            result = search_lengths_at_start(
                fixture, raw_start, remaining, patterns=patterns, pair=pair)
            cells_tested += 1
            total_nodes += result["total_nodes"]
            if result["hit_count"]:
                first_hit = {
                    "raw_start": raw_start,
                    "is_planted_raw_start": raw_start == fixture["planted_raw_offset"],
                    "pair_index": pair_index, "pair": list(pair),
                    "is_planted_pair": pair == phase512a.PAIR,
                    **result["hits"][0],
                }
                break
        if first_hit or exhausted:
            break
    return {
        "crib_id": crib_id, "width": width,
        "planted_raw_start": fixture["planted_raw_offset"],
        "raw_starts_in_family": maximum_start + 1,
        "max_starts_requested": max_starts,
        "pair_family_size": len(phase512a.base.ESCAPE_PAIRS),
        "legal_length_pattern_count_per_cell": len(patterns),
        "starts_tested": starts_tested, "pair_start_cells_tested": cells_tested,
        "total_nodes": total_nodes, "global_node_limit": global_node_limit,
        "first_hit": first_hit,
        "first_hit_is_exact_truth": bool(
            first_hit and first_hit["is_planted_raw_start"]
            and first_hit["is_planted_pair"] and first_hit["exact_truth"]),
        "elapsed_seconds": time.monotonic() - started,
    }


def self_test() -> dict:
    fixture = phase512a.make_fixture("phase1_credential", 15)
    singles = true_single_letters(fixture)
    built = build_constraints(fixture["crib"], fixture["planted_raw_offset"],
                              15, singles)
    if built is None or built[1] - fixture["planted_raw_offset"] != fixture["crib_raw_length"]:
        raise AssertionError("length pattern did not reproduce crib raw span")
    result = run_true_pattern("phase1_credential", 15, 1_000_000)
    if not result["truth_recovered"]:
        raise AssertionError("MRV CSP failed known-length-pattern ceiling")
    return {"self_test": "pass", "nodes": result["nodes"],
            "solutions": result["solution_count_capped"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--crib", choices=tuple(phase512a.CRIBS))
    parser.add_argument("--width", type=int, choices=phase512a.WIDTHS)
    parser.add_argument("--node-limit", type=int, default=1_000_000)
    parser.add_argument("--blind-lengths", action="store_true")
    parser.add_argument("--blind-start", action="store_true")
    parser.add_argument("--blind-pair", action="store_true")
    parser.add_argument("--fully-blind", action="store_true")
    parser.add_argument("--max-starts", type=int)
    args = parser.parse_args()
    if args.self_test:
        value = self_test()
    elif args.crib is not None and args.width is not None:
        value = (run_blind_pair_start_lengths(
                    args.crib, args.width, args.node_limit, args.max_starts)
                 if args.fully_blind else
                 run_blind_pair_and_lengths(args.crib, args.width, args.node_limit)
                 if args.blind_pair else
                 run_blind_start_and_lengths(
                    args.crib, args.width, args.node_limit, args.max_starts)
                 if args.blind_start else
                 run_blind_lengths(args.crib, args.width, args.node_limit)
                 if args.blind_lengths else
                 run_true_pattern(args.crib, args.width, args.node_limit))
    else:
        parser.error("use --self-test or provide --crib and --width")
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
