#!/usr/bin/env python3
"""Width-19 beam accumulating successive depth-specific model scores."""

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
from phase484n_hybrid_prefix_scorer import DEFAULT_BINARY

SCRIPT_DIR = Path(__file__).resolve().parent
WIDTH = 19
DEFAULT_BEAM = 65536
DEFAULT_DECAY = 0.5


def expand_with_parent_scores(beam, width: int):
    candidates = {}
    for score, path in beam:
        used = set(path)
        for block in range(width):
            if block in used:
                continue
            for candidate in ((block,) + path, path + (block,)):
                candidates[candidate] = max(score, candidates.get(candidate, -np.inf))
    paths = sorted(candidates)
    return paths, np.asarray([candidates[path] for path in paths])


def search(fixture, models, binary: Path, beam_width: int, decay: float):
    blocks = prefix.blocks_from_observed(fixture)
    pair = tuple(fixture["pair"])
    truth = prefix.order_to_sequence(fixture["order"])
    paths = list(itertools.permutations(range(WIDTH), prefix.START_DEPTH))
    scores = gpu_beam.score_paths(
        binary, blocks, pair, models[prefix.START_DEPTH], paths
    )
    beam = gpu_beam.select_diverse_arrays(paths, scores, WIDTH, beam_width)
    diagnostics = []
    began = time.monotonic()
    for depth in range(prefix.START_DEPTH, WIDTH):
        genuine = bidi.true_windows(truth, depth)
        ranks = [
            rank for rank, (_, path) in enumerate(beam, start=1)
            if path in genuine
        ]
        diagnostics.append({
            "depth": depth,
            "true_segment_count_retained": len(ranks),
            "best_true_segment_rank": min(ranks) if ranks else None,
            "beam_size": len(beam),
        })
        if not ranks or depth == WIDTH - 1:
            break
        paths, parent_scores = expand_with_parent_scores(beam, WIDTH)
        current_scores = gpu_beam.score_paths(
            binary, blocks, pair, models[depth + 1], paths
        )
        combined = current_scores + decay * parent_scores
        beam = gpu_beam.select_diverse_arrays(
            paths, combined, WIDTH, beam_width
        )
    return {
        "survived_to_depth_18": diagnostics[-1]["depth"] == 18 and
        diagnostics[-1]["true_segment_count_retained"] > 0,
        "depth_diagnostics": diagnostics,
        "wall_seconds": time.monotonic() - began,
    }


def run(mode, fixture_index, beam_width, decay, binary):
    models = prefix.train_models(WIDTH)
    fixture = base.make_fixture(
        WIDTH, learned.PAIR_INDEX, fixture_index, seed=learned.SEED,
        board_mode=mode, split="dev",
    )
    return {
        "phase": "484N",
        "status": "development_cumulative_depth_beam_not_frozen",
        "faed_scored": False,
        "holdout_consumed": False,
        "board_mode": mode,
        "fixture_index": fixture_index,
        "beam_width": beam_width,
        "accumulation_decay": decay,
        **search(fixture, models, binary, beam_width, decay),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--mode", choices=base.BOARD_MODES, default="vic_profile")
    parser.add_argument("--fixture-index", type=int, default=23)
    parser.add_argument("--beam", type=int, default=DEFAULT_BEAM)
    parser.add_argument("--decay", type=float, default=DEFAULT_DECAY)
    parser.add_argument("--binary", type=Path, default=DEFAULT_BINARY)
    args = parser.parse_args()
    if not args.run or not 0 <= args.decay <= 1:
        parser.error("use --run and a decay in [0,1]")
    result = run(args.mode, args.fixture_index, args.beam, args.decay, args.binary)
    output = SCRIPT_DIR / (
        f"phase484n_cumulative_{args.mode}_i{args.fixture_index}_"
        f"b{args.beam}_d{args.decay:g}.json"
    )
    output.write_text(json.dumps(result, indent=2) + "\n")
    print("survived", result["survived_to_depth_18"],
          "wall", round(result["wall_seconds"], 3))
    for record in result["depth_diagnostics"]:
        print(record["depth"], record["true_segment_count_retained"],
              record["best_true_segment_rank"])
    print("wrote", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
