#!/usr/bin/env python3
"""GPU-scored width-19 bidirectional beam survival probe (development only)."""

from __future__ import annotations

import argparse
from collections import defaultdict
import itertools
import json
import time
from pathlib import Path

import numpy as np

import phase484a_raw_symbol_vic_solver as base
import phase484g_hard_negative_discriminator as learned
import phase484j_constructive_prefix_beam_probe as prefix
import phase484k_bidirectional_segment_assembly_probe as bidi
from phase484n_hybrid_prefix_scorer import GpuPrefixScorer, DEFAULT_BINARY

SCRIPT_DIR = Path(__file__).resolve().parent
WIDTH = 19
START_DEPTH = 4
STOP_DEPTH = 18
DEFAULT_BEAM = 16384
DEFAULT_INDEX = 23


def score_paths(binary: Path, blocks, pair, model, paths) -> np.ndarray:
    with GpuPrefixScorer(binary, blocks, pair, model) as scorer:
        return scorer.score(np.asarray(paths, dtype=np.uint8))


def select_diverse_arrays(paths, scores, width: int, beam_width: int):
    candidates = {
        tuple(int(value) for value in path): float(score)
        for path, score in zip(paths, scores)
    }
    return bidi.select_diverse(candidates, width, beam_width=beam_width)


def select_coverage_diverse(paths, scores, beam_width: int):
    ranked = sorted(
        ((float(score), tuple(int(value) for value in path))
         for path, score in zip(paths, scores)),
        key=lambda item: (-item[0], item[1]),
    )
    groups = defaultdict(list)
    for score, path in ranked:
        mask = sum(1 << value for value in path)
        groups[mask].append((score, path))
    quota = max(1, beam_width // max(1, len(groups)))
    selected = {}
    for mask in sorted(groups):
        for score, path in groups[mask][:quota]:
            if len(selected) == beam_width:
                break
            selected[path] = score
    for score, path in ranked:
        if len(selected) == beam_width:
            break
        selected.setdefault(path, score)
    return sorted(
        ((score, path) for path, score in selected.items()),
        key=lambda item: (-item[0], item[1]),
    )


def expand_bidirectional(beam, width: int) -> list[tuple[int, ...]]:
    candidates = set()
    for _, path in beam:
        used = set(path)
        for block in range(width):
            if block not in used:
                candidates.add((block,) + path)
                candidates.add(path + (block,))
    return sorted(candidates)


def search_survival(fixture: dict, models, binary: Path,
                    beam_width: int, diversity: str = "endpoint") -> dict:
    blocks = prefix.blocks_from_observed(fixture)
    pair = tuple(fixture["pair"])
    truth = prefix.order_to_sequence(fixture["order"])
    diagnostics = []
    began = time.monotonic()

    paths = list(itertools.permutations(range(WIDTH), START_DEPTH))
    score_began = time.monotonic()
    scores = score_paths(binary, blocks, pair, models[START_DEPTH], paths)
    score_seconds = time.monotonic() - score_began
    select_began = time.monotonic()
    selector = (
        (lambda p, s: select_coverage_diverse(p, s, beam_width))
        if diversity == "coverage"
        else (lambda p, s: select_diverse_arrays(p, s, WIDTH, beam_width))
    )
    beam = selector(paths, scores)
    select_seconds = time.monotonic() - select_began

    for depth in range(START_DEPTH, STOP_DEPTH + 1):
        genuine = bidi.true_windows(truth, depth)
        true_ranks = [
            rank for rank, (_, path) in enumerate(beam, start=1)
            if path in genuine
        ]
        diagnostics.append({
            "depth": depth,
            "beam_size": len(beam),
            "generated_candidate_count": len(paths),
            "gpu_score_seconds": score_seconds,
            "selection_seconds": select_seconds,
            "true_segment_count_retained": len(true_ranks),
            "best_true_segment_rank": min(true_ranks) if true_ranks else None,
        })
        if depth == STOP_DEPTH or not true_ranks:
            break
        generate_began = time.monotonic()
        paths = expand_bidirectional(beam, WIDTH)
        generate_seconds = time.monotonic() - generate_began
        score_began = time.monotonic()
        scores = score_paths(binary, blocks, pair, models[depth + 1], paths)
        score_seconds = time.monotonic() - score_began
        select_began = time.monotonic()
        beam = selector(paths, scores)
        select_seconds = time.monotonic() - select_began
        diagnostics[-1]["next_generation_seconds"] = generate_seconds

    return {
        "survived_to_depth_18": diagnostics[-1]["true_segment_count_retained"] > 0,
        "depth_diagnostics": diagnostics,
        "wall_seconds": time.monotonic() - began,
    }


def run(mode: str, fixture_index: int, beam_width: int,
        binary: Path, diversity: str = "endpoint") -> dict:
    trained_at = time.monotonic()
    models = prefix.train_models(WIDTH)
    training_seconds = time.monotonic() - trained_at
    fixture = base.make_fixture(
        WIDTH, learned.PAIR_INDEX, fixture_index, seed=learned.SEED,
        board_mode=mode, split="dev",
    )
    return {
        "phase": "484N",
        "status": "development_gpu_width19_beam_survival_not_frozen",
        "faed_scored": False,
        "holdout_consumed": False,
        "board_mode": mode,
        "fixture_split": "dev",
        "fixture_index": fixture_index,
        "width": WIDTH,
        "beam_width": beam_width,
        "diversity": diversity,
        "training_seconds": training_seconds,
        **search_survival(fixture, models, binary, beam_width, diversity),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--mode", choices=base.BOARD_MODES, default="vic_profile")
    parser.add_argument("--fixture-index", type=int, default=DEFAULT_INDEX)
    parser.add_argument("--beam", type=int, default=DEFAULT_BEAM)
    parser.add_argument("--diversity", choices=("endpoint", "coverage"),
                        default="endpoint")
    parser.add_argument("--binary", type=Path, default=DEFAULT_BINARY)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.run:
        parser.error("use --run for the development probe")
    result = run(args.mode, args.fixture_index, args.beam, args.binary,
                 args.diversity)
    output = args.output or SCRIPT_DIR / (
        f"phase484n_gpu_beam_{args.mode}_i{args.fixture_index}_"
        f"b{args.beam}_{args.diversity}.json"
    )
    output.write_text(json.dumps(result, indent=2) + "\n")
    print("survived", result["survived_to_depth_18"],
          "wall", round(result["wall_seconds"], 3))
    for record in result["depth_diagnostics"]:
        print(record["depth"], record["generated_candidate_count"],
              "score", round(record["gpu_score_seconds"], 3),
              "select", round(record["selection_seconds"], 3),
              "true", record["true_segment_count_retained"],
              "rank", record["best_true_segment_rank"])
    print("wrote", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
