#!/usr/bin/env python3
"""Development fast lane for Phase-512 exact-crib CSP searches.

Unlike the frozen Phase-512D solver, this version does not compute an exact
MRV candidate list for every remaining column at every node.  It chooses the
remaining column with the most crib constraints, evaluates only that column,
and forward-checks the next column after descending.  The search remains
exhaustive; only branch ordering changes.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import multiprocessing
import os
import time

import phase512a_transposition_crib_feasibility as phase512a
import phase512b_crib_csp_ceiling as phase512b
import phase512d_length_pattern_csp as phase512d
import phase512e_parallel_blind_crib as phase512e


_FIXTURE = None
_PATTERNS = None
_RAW_START = None
_NODE_LIMIT = None


def solve_length_pattern_fast(observed: str, width: int,
                              pair: tuple[str, str], crib: str,
                              raw_start: int,
                              single_letters: frozenset[str],
                              node_limit: int = 2_000_000,
                              solution_limit: int = 1,
                              solution_acceptor=None,
                              blocks=None) -> dict:
    blocks = (phase512b.observed_blocks(observed, width)
              if blocks is None else blocks)
    built = phase512d.build_constraints(
        crib, raw_start, width, single_letters, len(observed))
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
            updates = phase512d.compatible_assignment(
                by_column[column], block, pair, assignments, crib,
                single_letters)
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
            codes = phase512d.completed_codes(assignments, crib, single_letters)
            if len(set(codes.values())) != len(set(crib)):
                return
            solution = tuple(column_to_chunk)
            if solution_acceptor is None or solution_acceptor(solution):
                solutions.append(solution)
            return
        # Static most-constrained-first avoids constructing candidate lists for
        # every column when the first strong column already rejects the pattern.
        column = min(remaining, key=lambda value: (-len(by_column[value]), value))
        options = candidates(column)
        if not options:
            return
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

    visit(constrained_columns)
    return {
        "nodes": nodes,
        "node_limit": node_limit,
        "node_limit_reached": limit_reached,
        "solutions": [list(value) for value in solutions],
        "raw_end": raw_end,
    }


def search_lengths_fast(fixture: dict, raw_start: int,
                        global_node_limit: int, patterns=None,
                        pair: tuple[str, str] = phase512a.PAIR) -> dict:
    width = fixture["width"]
    patterns = (tuple(phase512d.length_patterns(fixture["crib"]))
                if patterns is None else patterns)
    blocks = phase512b.observed_blocks(fixture["observed"], width)
    truth = (list(phase512b.truth_column_to_chunk(fixture["order"]))
             if "order" in fixture else None)
    patterns_tested = 0
    total_nodes = 0
    hit = None
    node_limit_reached = False

    def accepts_boundary(column_to_chunk) -> bool:
        order = [0] * width
        for column, chunk in enumerate(column_to_chunk):
            order[chunk] = column
        raw = phase512a.base.Geometry(
            len(fixture["observed"]), width).decrypt(fixture["observed"], order)
        return (phase512a.base.segment_raw(raw[:raw_start], pair) is not None
                and phase512a.base.segment_raw(raw, pair) is not None)

    started = time.monotonic()
    for pattern_index, singles in enumerate(patterns):
        remaining = global_node_limit - total_nodes
        if remaining <= 0:
            node_limit_reached = True
            break
        result = solve_length_pattern_fast(
            fixture["observed"], width, pair, fixture["crib"], raw_start,
            singles, node_limit=remaining, solution_acceptor=accepts_boundary,
            blocks=blocks)
        patterns_tested += 1
        total_nodes += result["nodes"]
        if result["solutions"]:
            solution = result["solutions"][0]
            hit = {
                "pattern_index": pattern_index,
                "single_letters": "".join(sorted(singles)),
                "column_to_chunk": solution,
                "exact_truth": (solution == truth if truth is not None else None),
                "nodes_for_pattern": result["nodes"],
            }
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
        "node_limit_reached": node_limit_reached,
        "search_complete": hit is not None or patterns_tested == len(patterns),
        "hit_count": int(hit is not None),
        "hits": [hit] if hit else [],
        "elapsed_seconds": time.monotonic() - started,
    }


def _init_worker(fixture, patterns, raw_start, node_limit):
    global _FIXTURE, _PATTERNS, _RAW_START, _NODE_LIMIT
    _FIXTURE = fixture
    _PATTERNS = patterns
    _RAW_START = raw_start
    _NODE_LIMIT = node_limit


def _pair_worker(pair_index: int) -> dict:
    pair = phase512a.base.ESCAPE_PAIRS[pair_index]
    return {"pair_index": pair_index, **search_lengths_fast(
        _FIXTURE, _RAW_START, _NODE_LIMIT, _PATTERNS, pair)}


def benchmark_start(fixture: dict, raw_start: int, workers: int = 16,
                    node_limit: int = 2_000_000) -> dict:
    patterns = tuple(phase512d.length_patterns(fixture["crib"]))
    context = multiprocessing.get_context("fork")
    started = time.monotonic()
    with concurrent.futures.ProcessPoolExecutor(
            max_workers=min(workers, 36), mp_context=context,
            initializer=_init_worker,
            initargs=(fixture, patterns, raw_start, node_limit)) as pool:
        cells = list(pool.map(_pair_worker, range(36)))
    return {
        "raw_start": raw_start,
        "cells": cells,
        "hit_count": sum(cell["hit_count"] for cell in cells),
        "incomplete_count": sum(not cell["search_complete"] for cell in cells),
        "elapsed_seconds": time.monotonic() - started,
    }


def self_test() -> dict:
    fixture = phase512a.make_fixture("phase1_credential", 15)
    singles = phase512d.true_single_letters(fixture)
    result = search_lengths_fast(
        fixture, fixture["planted_raw_offset"], 100_000,
        patterns=(singles,), pair=phase512a.PAIR)
    if result["hit_count"] != 1 or not result["hits"][0]["exact_truth"]:
        raise AssertionError("fast CSP missed known exact solution")
    return {"self_test": "pass", "nodes": result["total_nodes"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--crib", choices=tuple(phase512a.CRIBS))
    parser.add_argument("--width", type=int, choices=phase512a.WIDTHS)
    parser.add_argument("--fixture-index", type=int, default=0)
    parser.add_argument("--absent", action="store_true")
    parser.add_argument("--raw-start", type=int, default=0)
    parser.add_argument("--workers", type=int, default=min(16, os.cpu_count() or 1))
    args = parser.parse_args()
    if args.self_test:
        value = self_test()
    elif args.crib and args.width:
        fixture = (phase512e.make_absent_fixture(
            args.crib, args.width, args.fixture_index) if args.absent else
            phase512a.make_fixture(args.crib, args.width, args.fixture_index))
        value = benchmark_start(fixture, args.raw_start, args.workers)
    else:
        parser.error("use --self-test or specify --crib and --width")
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
