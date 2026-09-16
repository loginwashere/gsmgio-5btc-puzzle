#!/usr/bin/env python3
"""Parallel, checkpointed development search for Phase-512 exact cribs.

The scheduler is deliberately raw-start-major.  Every selected escape-pair
branch at a start is completed and retained before the search advances or
stops, so process completion order cannot select the reported solution.
This module is synthetic-only and never imports or scores FAED.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import time

import phase512a_transposition_crib_feasibility as phase512a
import phase512d_length_pattern_csp as phase512d


SCHEMA = "phase512e-parallel-blind-crib-v1"
SEED = 0x512E001

_WORKER_FIXTURE = None
_WORKER_PATTERNS = None
_WORKER_NODE_LIMIT = None


def sha_ascii(value: str) -> str:
    return hashlib.sha256(value.encode("ascii")).hexdigest()


def patterns_sha256(patterns) -> str:
    canonical = ["".join(sorted(value)) for value in patterns]
    payload = json.dumps(canonical, separators=(",", ":")).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def make_absent_fixture(crib_id: str, width: int,
                        fixture_index: int = 0) -> dict:
    """Construct a deterministic filler-only fixture lacking the target pattern."""
    if crib_id not in phase512a.CRIBS or width not in phase512a.WIDTHS:
        raise ValueError("unknown crib or width")
    if fixture_index < 0:
        raise ValueError("fixture_index must be non-negative")
    crib = phase512a.CRIBS[crib_id]
    wanted = phase512a.pattern(crib)
    for attempt in range(1000):
        rng = phase512a.base.PCG32(phase512a.base.derive_seed(
            SEED, phase512a.WIDTHS.index(width),
            tuple(phase512a.CRIBS).index(crib_id), fixture_index, attempt))
        board = phase512a.random_board(rng)
        plaintext = phase512a.filler_for_raw_length(
            phase512a.base.RAW_LENGTH, board, rng)
        if any(phase512a.pattern(plaintext[start:start + len(crib)]) == wanted
               for start in range(len(plaintext) - len(crib) + 1)):
            continue
        raw = phase512a.base.encode_plaintext(plaintext, board)
        order = rng.permutation(width)
        observed = phase512a.base.Geometry(len(raw), width).encrypt(raw, order)
        if phase512a.crib_matches_for_order(
                observed, width, order, phase512a.PAIR, crib):
            raise AssertionError("absent fixture matched under its true order")
        return {
            "fixture_kind": "crib_absent",
            "crib_id": crib_id,
            "crib": crib,
            "fixture_index": fixture_index,
            "construction_attempt": attempt,
            "width": width,
            "pair": list(phase512a.PAIR),
            "board": board,
            "plaintext": plaintext,
            "raw": raw,
            "order": order,
            "observed": observed,
            "planted_raw_offset": None,
        }
    raise RuntimeError("could not construct a crib-absent fixture")


def _init_worker(fixture: dict, patterns, node_limit: int) -> None:
    global _WORKER_FIXTURE, _WORKER_PATTERNS, _WORKER_NODE_LIMIT
    _WORKER_FIXTURE = fixture
    _WORKER_PATTERNS = patterns
    _WORKER_NODE_LIMIT = node_limit


def _worker_cell(task: tuple[int, int]) -> dict:
    pair_index, raw_start = task
    pair = phase512a.base.ESCAPE_PAIRS[pair_index]
    result = phase512d.search_lengths_at_start(
        _WORKER_FIXTURE, raw_start, _WORKER_NODE_LIMIT,
        patterns=_WORKER_PATTERNS, pair=pair)
    return {
        "pair_index": pair_index,
        "pair": list(pair),
        "raw_start": raw_start,
        **result,
    }


def _worker_shard(task: tuple[int, int, int, int]) -> dict:
    pair_index, raw_start, pattern_begin, pattern_end = task
    pair = phase512a.base.ESCAPE_PAIRS[pair_index]
    result = phase512d.search_lengths_at_start(
        _WORKER_FIXTURE, raw_start, _WORKER_NODE_LIMIT,
        patterns=_WORKER_PATTERNS[pattern_begin:pattern_end], pair=pair)
    for hit in result["hits"]:
        hit["pattern_index"] += pattern_begin
    return {
        "pair_index": pair_index,
        "pair": list(pair),
        "raw_start": raw_start,
        "pattern_begin": pattern_begin,
        "pattern_end": pattern_end,
        **result,
    }


def pattern_ranges(length: int, shard_count: int) -> tuple[tuple[int, int], ...]:
    if length <= 0 or shard_count <= 0:
        raise ValueError("length and shard_count must be positive")
    count = min(length, shard_count)
    return tuple(
        (index * length // count, (index + 1) * length // count)
        for index in range(count)
    )


def merge_pair_shards(rows: list[dict], full_pattern_count: int) -> dict:
    if not rows:
        raise ValueError("cannot merge an empty shard family")
    rows = sorted(rows, key=lambda value: value["pattern_begin"])
    expected = 0
    all_hits = []
    for row in rows:
        if row["pattern_begin"] != expected:
            raise RuntimeError("pattern shards are not contiguous")
        expected = row["pattern_end"]
        all_hits.extend(row["hits"])
    if expected != full_pattern_count:
        raise RuntimeError("pattern shards do not cover the full family")
    all_hits.sort(key=lambda value: value["pattern_index"])
    first_hit = all_hits[:1]
    complete = bool(first_hit) or all(row["search_complete"] for row in rows)
    first = rows[0]
    return {
        "pair_index": first["pair_index"],
        "pair": first["pair"],
        "raw_start": first["raw_start"],
        "legal_length_pattern_count": full_pattern_count,
        "patterns_tested": sum(row["patterns_tested"] for row in rows),
        "total_nodes": sum(row["total_nodes"] for row in rows),
        "global_node_limit": first["global_node_limit"],
        "node_limit_reached": any(row["node_limit_reached"] for row in rows),
        "search_complete": complete,
        "hit_count": len(first_hit),
        "hits": first_hit,
        "first_hit_exact_truth": (first_hit[0]["exact_truth"]
                                  if first_hit else None),
        "pattern_shards": len(rows),
        "additional_shard_hit_count": max(0, len(all_hits) - 1),
    }


def stable_cell(cell: dict) -> dict:
    """Remove wall-clock noise for parity checks and persisted comparisons."""
    return {key: value for key, value in cell.items()
            if key != "elapsed_seconds"}


def _atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def scan_identity(fixture: dict, patterns, pair_indices: tuple[int, ...],
                  start_begin: int, start_count: int,
                  per_cell_node_limit: int) -> dict:
    return {
        "schema": SCHEMA,
        "fixture_kind": fixture.get("fixture_kind", "crib_present"),
        "crib_id": fixture["crib_id"],
        "fixture_index": fixture.get("fixture_index", 0),
        "crib_sha256": sha_ascii(fixture["crib"]),
        "observed_sha256": sha_ascii(fixture["observed"]),
        "width": fixture["width"],
        "patterns_sha256": patterns_sha256(patterns),
        "legal_length_pattern_count": len(patterns),
        "pair_indices": list(pair_indices),
        "start_begin": start_begin,
        "start_count": start_count,
        "per_cell_node_limit": per_cell_node_limit,
    }


def _new_checkpoint(identity: dict) -> dict:
    return {
        "identity": identity,
        "completed_starts": [],
        "status": "in_progress",
        "faed_imported_or_scored": False,
    }


def _validate_checkpoint(value: dict, identity: dict) -> None:
    if value.get("identity") != identity:
        raise RuntimeError("checkpoint identity does not match this search")
    rows = value.get("completed_starts")
    if not isinstance(rows, list):
        raise RuntimeError("checkpoint completed_starts is malformed")
    expected = identity["start_begin"]
    for row in rows:
        if row.get("raw_start") != expected:
            raise RuntimeError("checkpoint starts are not contiguous")
        pair_indices = [cell.get("pair_index") for cell in row.get("cells", [])]
        if pair_indices != identity["pair_indices"]:
            raise RuntimeError("checkpoint pair set/order is incomplete")
        expected += 1


def _summarize(checkpoint: dict) -> dict:
    rows = checkpoint["completed_starts"]
    hits = []
    incomplete = []
    for row in rows:
        for cell in row["cells"]:
            if cell["hit_count"]:
                hits.append({
                    "raw_start": row["raw_start"],
                    "pair_index": cell["pair_index"],
                    "pair": cell["pair"],
                    "hits": cell["hits"],
                })
            if not cell["search_complete"]:
                incomplete.append({
                    "raw_start": row["raw_start"],
                    "pair_index": cell["pair_index"],
                    "total_nodes": cell["total_nodes"],
                })
    checkpoint["hit_cells"] = hits
    checkpoint["incomplete_cells"] = incomplete
    checkpoint["starts_completed"] = len(rows)
    checkpoint["pair_start_cells_completed"] = sum(len(row["cells"]) for row in rows)
    if incomplete:
        checkpoint["status"] = "incomplete_node_limit"
    elif hits:
        checkpoint["status"] = "hit_at_earliest_completed_start"
    elif len(rows) == checkpoint["identity"]["start_count"]:
        checkpoint["status"] = "no_hit_in_complete_requested_family"
    else:
        checkpoint["status"] = "in_progress"
    return checkpoint


def scan_fixture(fixture: dict, *, workers: int | None = None,
                 per_cell_node_limit: int = 2_000_000,
                 pair_indices=None, start_begin: int = 0,
                 start_count: int | None = None,
                 checkpoint_path: Path | None = None,
                 pattern_shards: int = 1) -> dict:
    patterns = tuple(phase512d.length_patterns(fixture["crib"]))
    pair_indices = (tuple(range(len(phase512a.base.ESCAPE_PAIRS)))
                    if pair_indices is None else tuple(pair_indices))
    if not pair_indices or len(set(pair_indices)) != len(pair_indices):
        raise ValueError("pair_indices must be nonempty and unique")
    if any(index < 0 or index >= len(phase512a.base.ESCAPE_PAIRS)
           for index in pair_indices):
        raise ValueError("pair index out of range")
    maximum_start = len(fixture["observed"]) - len(fixture["crib"])
    if start_begin < 0 or start_begin > maximum_start:
        raise ValueError("start_begin out of range")
    available = maximum_start - start_begin + 1
    start_count = available if start_count is None else start_count
    if start_count <= 0 or start_count > available:
        raise ValueError("start_count out of range")
    if per_cell_node_limit <= 0:
        raise ValueError("per_cell_node_limit must be positive")
    workers = min(16, os.cpu_count() or 1) if workers is None else workers
    if workers <= 0:
        raise ValueError("workers must be positive")
    if pattern_shards <= 0:
        raise ValueError("pattern_shards must be positive")

    identity = scan_identity(fixture, patterns, pair_indices, start_begin,
                             start_count, per_cell_node_limit)
    if checkpoint_path is not None and checkpoint_path.exists():
        checkpoint = json.loads(checkpoint_path.read_text())
        _validate_checkpoint(checkpoint, identity)
        _summarize(checkpoint)
        if checkpoint["status"] != "in_progress":
            return checkpoint
    else:
        checkpoint = _new_checkpoint(identity)

    first_unfinished = start_begin + len(checkpoint["completed_starts"])
    stop = start_begin + start_count
    started = time.monotonic()

    def record_start(raw_start: int, cells: list[dict]) -> bool:
        stable = [stable_cell(cell) for cell in sorted(
            cells, key=lambda value: value["pair_index"])]
        checkpoint["completed_starts"].append({
            "raw_start": raw_start,
            "cells": stable,
        })
        _summarize(checkpoint)
        checkpoint["last_session_elapsed_seconds"] = time.monotonic() - started
        if checkpoint_path is not None:
            _atomic_json(checkpoint_path, checkpoint)
        return checkpoint["status"] != "in_progress"

    if workers == 1 and pattern_shards == 1:
        _init_worker(fixture, patterns, per_cell_node_limit)
        for raw_start in range(first_unfinished, stop):
            cells = [_worker_cell((pair_index, raw_start))
                     for pair_index in pair_indices]
            if record_start(raw_start, cells):
                break
    else:
        context = multiprocessing.get_context("fork")
        with concurrent.futures.ProcessPoolExecutor(
                max_workers=min(workers, len(pair_indices) * pattern_shards),
                mp_context=context, initializer=_init_worker,
                initargs=(fixture, patterns, per_cell_node_limit)) as pool:
            for raw_start in range(first_unfinished, stop):
                if pattern_shards == 1:
                    cells = list(pool.map(
                        _worker_cell,
                        ((pair_index, raw_start) for pair_index in pair_indices)))
                else:
                    ranges = pattern_ranges(len(patterns), pattern_shards)
                    shard_rows = list(pool.map(
                        _worker_shard,
                        ((pair_index, raw_start, begin, end)
                         for pair_index in pair_indices
                         for begin, end in ranges)))
                    by_pair = {pair_index: [] for pair_index in pair_indices}
                    for row in shard_rows:
                        by_pair[row["pair_index"]].append(row)
                    cells = [merge_pair_shards(by_pair[pair_index], len(patterns))
                             for pair_index in pair_indices]
                if record_start(raw_start, cells):
                    break
    _summarize(checkpoint)
    checkpoint["last_session_elapsed_seconds"] = time.monotonic() - started
    if checkpoint_path is not None:
        _atomic_json(checkpoint_path, checkpoint)
    return checkpoint


def parity_probe(workers: int = 2) -> dict:
    fixture = phase512a.make_fixture("phase1_credential", 15)
    true_pair_index = phase512a.base.ESCAPE_PAIRS.index(phase512a.PAIR)
    comparison_pair = 0 if true_pair_index != 0 else 1
    pair_indices = (comparison_pair, true_pair_index)
    singles = phase512d.true_single_letters(fixture)
    patterns = (singles,)
    # Use the worker primitive directly so this fast parity probe can freeze a
    # one-pattern ceiling without changing scan_fixture's full-pattern family.
    _init_worker(fixture, patterns, 100_000)
    serial = [stable_cell(_worker_cell((index, fixture["planted_raw_offset"])))
              for index in pair_indices]
    context = multiprocessing.get_context("fork")
    with concurrent.futures.ProcessPoolExecutor(
            max_workers=workers, mp_context=context, initializer=_init_worker,
            initargs=(fixture, patterns, 100_000)) as pool:
        parallel = [stable_cell(value) for value in pool.map(
            _worker_cell,
            ((index, fixture["planted_raw_offset"]) for index in pair_indices))]
    if serial != parallel:
        raise AssertionError("serial and parallel pair cells differ")
    return {
        "parity": "pass",
        "pair_indices": list(pair_indices),
        "true_pair_hit": parallel[1]["hit_count"] == 1,
        "cells": parallel,
    }


def self_test() -> dict:
    phase512a.self_test()
    absent = make_absent_fixture("phase1_credential", 15)
    if absent["fixture_kind"] != "crib_absent":
        raise AssertionError("negative fixture kind changed")
    parity = parity_probe()
    if not parity["true_pair_hit"]:
        raise AssertionError("parallel ceiling missed the planted pair")
    return {"self_test": "pass", "parallel_parity": "pass",
            "absent_fixture_true_order_match_count": 0}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--parity-probe", action="store_true")
    parser.add_argument("--crib", choices=tuple(phase512a.CRIBS))
    parser.add_argument("--width", type=int, choices=phase512a.WIDTHS)
    parser.add_argument("--fixture-index", type=int, default=0)
    parser.add_argument("--absent", action="store_true")
    parser.add_argument("--workers", type=int, default=min(16, os.cpu_count() or 1))
    parser.add_argument("--node-limit", type=int, default=2_000_000)
    parser.add_argument("--start-begin", type=int, default=0)
    parser.add_argument("--start-count", type=int)
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--pattern-shards", type=int, default=1)
    args = parser.parse_args()
    if args.self_test:
        value = self_test()
    elif args.parity_probe:
        value = parity_probe(args.workers)
    elif args.crib is not None and args.width is not None:
        fixture = (make_absent_fixture(args.crib, args.width, args.fixture_index)
                   if args.absent else
                   phase512a.make_fixture(args.crib, args.width,
                                          args.fixture_index))
        value = scan_fixture(
            fixture, workers=args.workers,
            per_cell_node_limit=args.node_limit,
            start_begin=args.start_begin, start_count=args.start_count,
            checkpoint_path=args.checkpoint, pattern_shards=args.pattern_shards)
    else:
        parser.error("use a probe or provide --crib and --width")
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
