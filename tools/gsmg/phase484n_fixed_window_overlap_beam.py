#!/usr/bin/env python3
"""Width-19 overlap beam using repeated fixed-depth local evidence."""

from __future__ import annotations

import argparse
import itertools
import json
import time
from pathlib import Path

import numpy as np

import phase484a_raw_symbol_vic_solver as base
import phase484g_hard_negative_discriminator as learned
import phase484j_constructive_prefix_beam_probe as prefix
import phase484k_bidirectional_segment_assembly_probe as bidi
import phase484n_gpu_width19_beam_probe as gpu_beam
from phase484n_hybrid_prefix_scorer import GpuPrefixScorer, DEFAULT_BINARY

SCRIPT_DIR = Path(__file__).resolve().parent
WIDTH = 19
LOCAL_DEPTH = 8
STOP_DEPTH = 19
DEFAULT_BEAM = 65536
DEFAULT_INDEX = 23
WINDOW_BATCH = 100000


def overlapping_windows(paths, local_depth: int = LOCAL_DEPTH):
    paths = np.asarray(paths, dtype=np.uint8)
    if paths.ndim != 2 or paths.shape[1] < local_depth:
        raise ValueError("paths shorter than local window")
    return np.concatenate([
        paths[:, start:start + local_depth]
        for start in range(paths.shape[1] - local_depth + 1)
    ], axis=0)


def score_window_sums(scorer: GpuPrefixScorer, paths,
                      local_depth: int = LOCAL_DEPTH,
                      candidate_batch: int = WINDOW_BATCH) -> np.ndarray:
    paths = np.asarray(paths, dtype=np.uint8)
    result = np.empty(len(paths), dtype=np.float64)
    window_count = paths.shape[1] - local_depth + 1
    for begin in range(0, len(paths), candidate_batch):
        chunk = paths[begin:begin + candidate_batch]
        windows = overlapping_windows(chunk, local_depth)
        scores = scorer.score(windows)
        # concatenate() groups by window offset, so restore offset x candidate.
        result[begin:begin + len(chunk)] = scores.reshape(
            window_count, len(chunk)
        ).sum(axis=0)
    return result


def search(fixture: dict, models, binary: Path, beam_width: int,
           local_depth: int = LOCAL_DEPTH) -> dict:
    blocks = prefix.blocks_from_observed(fixture)
    pair = tuple(fixture["pair"])
    truth = prefix.order_to_sequence(fixture["order"])
    diagnostics = []
    began = time.monotonic()
    beam = None

    for depth in range(prefix.START_DEPTH, local_depth + 1):
        if depth == prefix.START_DEPTH:
            paths = list(itertools.permutations(range(WIDTH), depth))
        else:
            paths = gpu_beam.expand_bidirectional(beam, WIDTH)
        score_began = time.monotonic()
        scores = gpu_beam.score_paths(binary, blocks, pair, models[depth], paths)
        score_seconds = time.monotonic() - score_began
        select_began = time.monotonic()
        beam = gpu_beam.select_diverse_arrays(paths, scores, WIDTH, beam_width)
        select_seconds = time.monotonic() - select_began
        diagnostics.append(_diagnostic(
            depth, beam, paths, truth, score_seconds, select_seconds,
            "depth_specific",
        ))

    with GpuPrefixScorer(binary, blocks, pair, models[local_depth]) as scorer:
        for depth in range(local_depth + 1, STOP_DEPTH + 1):
            generate_began = time.monotonic()
            paths = gpu_beam.expand_bidirectional(beam, WIDTH)
            generate_seconds = time.monotonic() - generate_began
            score_began = time.monotonic()
            scores = score_window_sums(scorer, paths, local_depth)
            score_seconds = time.monotonic() - score_began
            select_began = time.monotonic()
            beam = gpu_beam.select_diverse_arrays(paths, scores, WIDTH, beam_width)
            select_seconds = time.monotonic() - select_began
            record = _diagnostic(
                depth, beam, paths, truth, score_seconds, select_seconds,
                f"overlapping_depth{local_depth}_sum",
            )
            record["generation_seconds"] = generate_seconds
            diagnostics.append(record)
            if not record["true_segment_count_retained"]:
                break

    exact = False
    truth_rank = None
    if diagnostics[-1]["depth"] == WIDTH:
        truth_tuple = tuple(truth)
        truth_rank = next(
            (rank for rank, (_, path) in enumerate(beam, start=1)
             if path == truth_tuple), None,
        )
        exact = bool(beam and beam[0][1] == truth_tuple)
    return {
        "truth_survived_full_depth": truth_rank is not None,
        "exact_top1_recovery": exact,
        "truth_full_rank": truth_rank,
        "depth_diagnostics": diagnostics,
        "wall_seconds": time.monotonic() - began,
    }


def _diagnostic(depth, beam, paths, truth, score_seconds,
                select_seconds, statistic):
    genuine = bidi.true_windows(truth, depth)
    ranks = [
        rank for rank, (_, path) in enumerate(beam, start=1)
        if path in genuine
    ]
    return {
        "depth": depth,
        "statistic": statistic,
        "generated_candidate_count": len(paths),
        "beam_size": len(beam),
        "gpu_score_seconds": score_seconds,
        "selection_seconds": select_seconds,
        "true_segment_count_retained": len(ranks),
        "best_true_segment_rank": min(ranks) if ranks else None,
    }


def run(mode: str, fixture_index: int, beam_width: int,
        binary: Path, local_depth: int = LOCAL_DEPTH) -> dict:
    if not prefix.START_DEPTH <= local_depth < WIDTH:
        raise ValueError("local depth must be in 4..18")
    trained_at = time.monotonic()
    models = prefix.train_models(WIDTH)
    training_seconds = time.monotonic() - trained_at
    fixture = base.make_fixture(
        WIDTH, learned.PAIR_INDEX, fixture_index, seed=learned.SEED,
        board_mode=mode, split="dev",
    )
    return {
        "phase": "484N",
        "status": "development_fixed_window_overlap_beam_not_frozen",
        "faed_scored": False,
        "holdout_consumed": False,
        "board_mode": mode,
        "fixture_split": "dev",
        "fixture_index": fixture_index,
        "width": WIDTH,
        "local_depth": local_depth,
        "beam_width": beam_width,
        "training_seconds": training_seconds,
        **search(fixture, models, binary, beam_width, local_depth),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--mode", choices=base.BOARD_MODES, default="vic_profile")
    parser.add_argument("--fixture-index", type=int, default=DEFAULT_INDEX)
    parser.add_argument("--beam", type=int, default=DEFAULT_BEAM)
    parser.add_argument("--local-depth", type=int, default=LOCAL_DEPTH)
    parser.add_argument("--binary", type=Path, default=DEFAULT_BINARY)
    args = parser.parse_args()
    if not args.run:
        parser.error("use --run for the development probe")
    result = run(args.mode, args.fixture_index, args.beam, args.binary,
                 args.local_depth)
    output = SCRIPT_DIR / (
        f"phase484n_overlap_{args.mode}_i{args.fixture_index}_"
        f"d{args.local_depth}_b{args.beam}.json"
    )
    output.write_text(json.dumps(result, indent=2) + "\n")
    print("full_survival", result["truth_survived_full_depth"],
          "exact_top1", result["exact_top1_recovery"],
          "truth_rank", result["truth_full_rank"],
          "wall", round(result["wall_seconds"], 3))
    for record in result["depth_diagnostics"]:
        print(record["depth"], record["statistic"],
              "candidates", record["generated_candidate_count"],
              "true", record["true_segment_count_retained"],
              "rank", record["best_true_segment_rank"])
    print("wrote", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
