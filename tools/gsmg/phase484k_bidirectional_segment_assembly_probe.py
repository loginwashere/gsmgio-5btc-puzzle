#!/usr/bin/env python3
"""Bidirectional internal-segment assembly for synthetic Phase 484 fixtures."""

from __future__ import annotations

import concurrent.futures
import itertools
import json
import time
from collections import defaultdict
from pathlib import Path

import phase484a_raw_symbol_vic_solver as base
import phase484g_hard_negative_discriminator as learned
import phase484h_discriminator_landscape_probe as full_model
import phase484j_constructive_prefix_beam_probe as prefix

SCRIPT_DIR = Path(__file__).resolve().parent
FAILED_SPECS = (
    ("vic_profile", 15),
    ("broad_random", 15),
    ("broad_random", 19),
)
BEAM_WIDTH = 4096
RESERVED_FRACTION = 0.5
EVAL_INDEX = prefix.EVAL_INDEX
FRESH_EVAL_INDEX = 23
DEV_BATCH_INDICES = tuple(range(23, 28))
DEV_BATCH_WIDTHS = (10, 15)
DEV_GATE_PER_CELL = 4
WORKERS = 6


def select_diverse(candidates: dict[tuple[int, ...], float], width: int,
                   beam_width: int = BEAM_WIDTH) -> list[tuple[float, tuple[int, ...]]]:
    ranked = sorted(
        ((score, path) for path, score in candidates.items()),
        key=lambda item: (-item[0], item[1]),
    )
    endpoint_groups = defaultdict(list)
    for score, path in ranked:
        endpoint_groups[(path[0], path[-1])].append((score, path))
    reserved_budget = int(beam_width * RESERVED_FRACTION)
    quota = max(1, reserved_budget // max(1, width * (width - 1)))
    selected = {}
    for key in sorted(endpoint_groups):
        for score, path in endpoint_groups[key][:quota]:
            selected[path] = score
    for score, path in ranked:
        if len(selected) >= beam_width:
            break
        selected.setdefault(path, score)
    return sorted(
        ((score, path) for path, score in selected.items()),
        key=lambda item: (-item[0], item[1]),
    )[:beam_width]


def true_windows(truth: list[int], depth: int) -> set[tuple[int, ...]]:
    return {
        tuple(truth[start:start + depth])
        for start in range(len(truth) - depth + 1)
    }


def terminal_score(fixture, sequence, classifier, spectral) -> float | None:
    order = prefix.sequence_to_order(sequence)
    return full_model.objective(classifier, spectral, fixture, order)


def search_fixture(fixture, models) -> dict:
    width = fixture["width"]
    blocks = prefix.blocks_from_observed(fixture)
    pair = tuple(fixture["pair"])
    truth = prefix.order_to_sequence(fixture["order"])
    classifier = full_model.load_model()
    spectral = base.SpectralModel.from_training_corpus()
    began = time.monotonic()
    candidates = {
        path: prefix.score_prefix(
            models[prefix.START_DEPTH], blocks, pair, path
        )
        for path in itertools.permutations(range(width), prefix.START_DEPTH)
    }
    beam = select_diverse(candidates, width)
    diagnostics = []
    for depth in range(prefix.START_DEPTH, width + 1):
        genuine = true_windows(truth, depth)
        true_ranks = [
            rank for rank, (_, path) in enumerate(beam, start=1)
            if path in genuine
        ]
        diagnostics.append({
            "depth": depth,
            "beam_size": len(beam),
            "true_segment_count_retained": len(true_ranks),
            "best_true_segment_rank": min(true_ranks) if true_ranks else None,
        })
        if depth == width:
            break
        extended = {}
        next_depth = depth + 1
        for _, path in beam:
            used = set(path)
            for block in range(width):
                if block in used:
                    continue
                for candidate in ((block,) + path, path + (block,)):
                    if candidate in extended:
                        continue
                    if next_depth == width:
                        score = terminal_score(
                            fixture, candidate, classifier, spectral
                        )
                    else:
                        score = prefix.score_prefix(
                            models[next_depth], blocks, pair, candidate
                        )
                    if score is not None:
                        extended[candidate] = score
        if not extended:
            raise RuntimeError("bidirectional beam has no valid extensions")
        beam = select_diverse(extended, width)

    best_score, best_sequence = beam[0]
    best_order = prefix.sequence_to_order(best_sequence)
    truth_rank = next(
        (rank for rank, (_, path) in enumerate(beam, start=1)
         if list(path) == truth),
        None,
    )
    return {
        "exact_recovery": best_order == fixture["order"],
        "best_tau": base.kendall_tau(fixture["order"], best_order),
        "best_score": best_score,
        "best_sequence": list(best_sequence),
        "best_order": best_order,
        "truth_rank_if_retained": truth_rank,
        "depth_diagnostics": diagnostics,
        "wall_seconds": time.monotonic() - began,
    }


def run_probe(specs=FAILED_SPECS) -> dict:
    cells = []
    began = time.monotonic()
    models_by_width = {}
    for mode, width in specs:
        if width not in models_by_width:
            models_by_width[width] = prefix.train_models(width)
        fixture = base.make_fixture(
            width, learned.PAIR_INDEX, EVAL_INDEX, seed=learned.SEED,
            board_mode=mode, split="dev",
        )
        cells.append({
            "board_mode": mode,
            "width": width,
            "fixture_index": EVAL_INDEX,
            **search_fixture(fixture, models_by_width[width]),
        })
    return {
        "phase": "484K",
        "status": "informal_bidirectional_segment_assembly_dev_not_frozen",
        "faed_scored": False,
        "fixture_split": "dev",
        "source_failed_cells": "phase484j_constructive_prefix_beam_result.json",
        "budgets": {
            "start_depth": prefix.START_DEPTH,
            "beam_width": BEAM_WIDTH,
            "reserved_fraction": RESERVED_FRACTION,
        },
        "exact_recovery_count": sum(c["exact_recovery"] for c in cells),
        "cell_count": len(cells),
        "cells": cells,
        "wall_seconds": time.monotonic() - began,
    }


def run_fresh_cell(spec):
    mode, width = spec
    models = prefix.train_models(width)
    fixture = base.make_fixture(
        width, learned.PAIR_INDEX, FRESH_EVAL_INDEX, seed=learned.SEED,
        board_mode=mode, split="dev",
    )
    return {
        "board_mode": mode,
        "width": width,
        "fixture_index": FRESH_EVAL_INDEX,
        **search_fixture(fixture, models),
    }


def run_fresh_smoke() -> dict:
    specs = [
        (mode, width)
        for mode in prefix.BOARD_MODES
        for width in prefix.WIDTHS
    ]
    began = time.monotonic()
    with concurrent.futures.ProcessPoolExecutor(max_workers=WORKERS) as pool:
        cells = list(pool.map(run_fresh_cell, specs))
    return {
        "phase": "484K",
        "status": "informal_fresh_all_cell_replication_dev_not_frozen",
        "faed_scored": False,
        "fixture_split": "dev",
        "fixture_index": FRESH_EVAL_INDEX,
        "budgets": {
            "start_depth": prefix.START_DEPTH,
            "beam_width": BEAM_WIDTH,
            "reserved_fraction": RESERVED_FRACTION,
            "workers": WORKERS,
        },
        "exact_recovery_count": sum(c["exact_recovery"] for c in cells),
        "cell_count": len(cells),
        "cells": cells,
        "wall_seconds": time.monotonic() - began,
    }


def run_dev_batch_cell(spec):
    mode, width, fixture_index = spec
    models = prefix.train_models(width)
    fixture = base.make_fixture(
        width, learned.PAIR_INDEX, fixture_index, seed=learned.SEED,
        board_mode=mode, split="dev",
    )
    return {
        "board_mode": mode,
        "width": width,
        "fixture_index": fixture_index,
        **search_fixture(fixture, models),
    }


def run_dev_batch() -> dict:
    specs = [
        (mode, width, index)
        for mode in prefix.BOARD_MODES
        for width in DEV_BATCH_WIDTHS
        for index in DEV_BATCH_INDICES
    ]
    began = time.monotonic()
    with concurrent.futures.ProcessPoolExecutor(max_workers=WORKERS) as pool:
        records = list(pool.map(run_dev_batch_cell, specs))
    cells = []
    for mode in prefix.BOARD_MODES:
        for width in DEV_BATCH_WIDTHS:
            selected = [
                record for record in records
                if record["board_mode"] == mode and record["width"] == width
            ]
            exact = sum(record["exact_recovery"] for record in selected)
            cells.append({
                "board_mode": mode,
                "width": width,
                "fixture_count": len(selected),
                "exact_recovery_count": exact,
                "gate_pass": exact >= DEV_GATE_PER_CELL,
                "records": selected,
            })
    return {
        "phase": "484K",
        "status": "informal_bidirectional_width10_15_dev_power_batch_not_frozen",
        "faed_scored": False,
        "fixture_split": "dev",
        "fixture_indices": list(DEV_BATCH_INDICES),
        "widths": list(DEV_BATCH_WIDTHS),
        "gate": {
            "minimum_exact_recoveries_per_five_fixture_cell": DEV_GATE_PER_CELL,
            "all_cells_must_pass": True,
        },
        "all_cells_pass": all(cell["gate_pass"] for cell in cells),
        "cells": cells,
        "wall_seconds": time.monotonic() - began,
    }


def self_test() -> None:
    candidates = {
        (0, 1, 2): 3.0,
        (0, 2, 1): 2.0,
        (1, 0, 2): 1.0,
        (2, 1, 0): 0.0,
    }
    selected = select_diverse(candidates, width=3, beam_width=3)
    assert len(selected) == 3
    assert len({path for _, path in selected}) == 3
    truth = list(range(8))
    assert (2, 3, 4, 5) in true_windows(truth, 4)
    assert true_windows(truth, 8) == {tuple(truth)}
    for path in itertools.permutations(range(5), 4):
        unused = next(block for block in range(5) if block not in path)
        assert len((unused,) + path) == 5
        assert len(path + (unused,)) == 5


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
        self_test()
        print("self-test: ok")
        raise SystemExit(0)
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "--fresh-smoke":
        result = run_fresh_smoke()
        path = SCRIPT_DIR / "phase484k_fresh_all_cell_result.json"
    elif mode == "--dev-batch":
        result = run_dev_batch()
        path = SCRIPT_DIR / "phase484k_width10_15_dev_batch_result.json"
    else:
        result = run_probe()
        path = SCRIPT_DIR / "phase484k_bidirectional_segment_assembly_result.json"
    path.write_text(json.dumps(result, indent=2))
    if "exact_recovery_count" in result:
        print("exact", result["exact_recovery_count"], "/", result["cell_count"])
    else:
        print("all_cells_pass", result["all_cells_pass"])
    for cell in result["cells"]:
        if "records" in cell:
            print(cell["board_mode"], cell["width"],
                  "exact", cell["exact_recovery_count"], "/",
                  cell["fixture_count"], "gate", cell["gate_pass"])
            continue
        lost = next(
            (d["depth"] for d in cell["depth_diagnostics"]
             if d["true_segment_count_retained"] == 0),
            None,
        )
        print(cell["board_mode"], cell["width"],
              "exact", cell["exact_recovery"],
              "tau", round(cell["best_tau"], 3),
              "all_true_segments_lost_at", lost)
    print("wrote", path)
