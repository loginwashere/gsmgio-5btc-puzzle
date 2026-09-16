#!/usr/bin/env python3
"""Width-19 port foundation for the Phase-488 dual-lane solver.

This development module stops at the refined depth-7 population.  It uses
the existing exact-FAED-profile synthetic fixture family and never imports or
scores FAED.  The purpose of this first stage is to establish that the
width-30 solver's load-bearing early switch can be reproduced at width 19
before porting its two expensive continuation lanes.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import time
from pathlib import Path

import numpy as np

import phase484a_raw_symbol_vic_solver as base
import phase484j_constructive_prefix_beam_probe as prefix
import phase484k_bidirectional_segment_assembly_probe as bidi
import phase484n_hybrid_prefix_scorer as invariant
import phase484q_blind_joint_width19_solver as width19
import phase484x_exact_faed_profile_power_probe as exact
import phase484ac_width30_partition_constrained_board_probe as constrained_cpu
import phase484z_width30_row_holdout_probe as rowcv


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
WIDTH, ROWS = 19, 30
CONSTRAINED_BINARY = REPO_ROOT / "_work/phase490/constrained_board_server"
DEFAULT_WORK_DIR = REPO_ROOT / "_work/phase490/front_i13"
BOARD_CHUNK = 1 << 20
BOARD_SEED = 0x49019001

FRONT_SCHEDULE = {
    "switch_depth": 6,
    "keep_early": 262144,
    "keep_penultimate": 524288,
    "keep_preboard": 1048576,
    "keep_board": 524288,
    "depth7_coarse_keep": 1310720,
    "coarse_restarts": 3,
    "coarse_iterations": 2000,
    "depth7_refine_keep": 655360,
    "refine_restarts": 4,
    "refine_iterations": 10000,
}


def schedule_sha256() -> str:
    encoded = json.dumps(
        FRONT_SCHEDULE, sort_keys=True, separators=(",", ":")
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def initial_paths(width=WIDTH, depth=4) -> np.ndarray:
    if not 1 <= depth <= width:
        raise ValueError("initial depth must lie within the width")
    count = math.prod(range(width - depth + 1, width + 1))
    values = np.fromiter(
        (value for path in itertools.permutations(range(width), depth)
         for value in path),
        dtype=np.uint8,
        count=count * depth,
    )
    return values.reshape(count, depth)


def expand_bidirectional(paths, width=WIDTH) -> np.ndarray:
    paths = np.asarray(paths, dtype=np.uint8)
    if paths.ndim != 2 or paths.shape[1] >= width:
        raise ValueError("paths must be an N x depth array below full width")
    # Keep validation vectorized: apply_along_axis invokes Python once per
    # candidate and turned a million-row diagnostic into a long CPU stall.
    repeated = (np.any(np.diff(np.sort(paths, axis=1), axis=1) == 0)
                if len(paths) and paths.shape[1] > 1 else False)
    if len(paths) and (np.any(paths >= width) or repeated):
        raise ValueError("paths contain an invalid or repeated column")
    depth = paths.shape[1]
    expanded = np.empty((len(paths) * 2 * (width - depth), depth + 1),
                        dtype=np.uint8)
    offset = 0
    for column in range(width):
        parents = paths[~np.any(paths == column, axis=1)]
        count = len(parents)
        expanded[offset:offset + count, 0] = column
        expanded[offset:offset + count, 1:] = parents
        offset += count
        expanded[offset:offset + count, :-1] = parents
        expanded[offset:offset + count, -1] = column
        offset += count
    if offset != len(expanded):
        raise AssertionError("bidirectional expansion count mismatch")
    return expanded


def packed_keys(paths) -> np.ndarray:
    paths = np.asarray(paths, dtype=np.uint8)
    if paths.shape[1] > 12:
        raise ValueError("5-bit keys are collision-free only through depth 12")
    keys = np.zeros(len(paths), dtype=np.uint64)
    for column in paths.T:
        keys = (keys << np.uint64(5)) | column.astype(np.uint64)
    return keys


def unique_path_indices(paths) -> np.ndarray:
    paths = np.asarray(paths, dtype=np.uint8)
    if paths.shape[1] <= 12:
        _, indices = np.unique(packed_keys(paths), return_index=True)
    else:
        _, indices = np.unique(paths, axis=0, return_index=True)
    return indices


def ranked_indices(paths, scores, indices=None) -> np.ndarray:
    paths = np.asarray(paths, dtype=np.uint8)
    scores = np.asarray(scores, dtype=np.float64)
    if scores.shape != (len(paths),):
        raise ValueError("score count differs from path count")
    indices = (np.arange(len(paths), dtype=np.int64) if indices is None
               else np.asarray(indices, dtype=np.int64))
    selected = paths[indices]
    keys = tuple(selected[:, column]
                 for column in range(selected.shape[1] - 1, -1, -1))
    return indices[np.lexsort((*keys, -scores[indices]))]


def select_diverse(paths, scores, keep, width=WIDTH):
    """Exact dedupe, endpoint reservation, then global score fill."""
    paths = np.asarray(paths, dtype=np.uint8)
    scores = np.asarray(scores, dtype=np.float64)
    # Rank before deduplication so independently produced copies retain the
    # strongest score, rather than whichever copy happened to arrive first.
    ranked = ranked_indices(paths, scores)
    unique = ranked[unique_path_indices(paths[ranked])]
    paths, scores = paths[unique], scores[unique]
    unique_count = len(paths)
    keep = min(int(keep), unique_count)
    reserved_budget = keep // 2
    quota = max(1, reserved_budget // (width * (width - 1)))
    groups = paths[:, 0].astype(np.int32) * width + paths[:, -1]
    group_order = np.argsort(groups, kind="stable")
    sorted_groups = groups[group_order]
    boundaries = np.flatnonzero(
        np.r_[True, sorted_groups[1:] != sorted_groups[:-1], True])
    reserved = []
    for left, right in zip(boundaries[:-1], boundaries[1:]):
        members = group_order[left:right]
        take = min(quota, len(members))
        if take < len(members):
            members = members[np.argpartition(-scores[members], take - 1)[:take]]
        reserved.extend(members.tolist())
    reserved = np.asarray(reserved, dtype=np.int64)
    if len(reserved) >= keep:
        selected = ranked_indices(paths, scores, reserved)[:keep]
    else:
        chosen = np.zeros(unique_count, dtype=bool)
        chosen[reserved] = True
        fill = ranked_indices(paths, scores, np.flatnonzero(~chosen))[
            :keep - len(reserved)]
        selected = np.concatenate([reserved, fill])
        selected = ranked_indices(paths, scores, selected)
    return paths[selected].copy(), scores[selected].copy(), unique_count


def true_record(paths, scores, truth, depth) -> dict:
    """Cheap post-selection truth diagnostic; never used by solver logic.

    Computing a complete lexicographic ranking of millions of paths merely to
    locate a handful of planted windows dominated the first test run.  The
    score-only lower rank is sufficient to diagnose survival and is explicit
    about score ties.
    """
    paths = np.asarray(paths, dtype=np.uint8)
    scores = np.asarray(scores, dtype=np.float64)
    targets = bidi.true_windows(truth, depth)
    mask = np.zeros(len(paths), dtype=bool)
    for target in targets:
        mask |= np.all(paths == np.asarray(target, dtype=np.uint8), axis=1)
    indices = np.flatnonzero(mask)
    if len(indices):
        best_score = float(np.max(scores[indices]))
        better = int(np.count_nonzero(scores > best_score))
        tied = int(np.count_nonzero(scores == best_score))
    else:
        best_score, better, tied = None, 0, 0
    return {
        "candidate_count": len(paths),
        "true_segments": len(indices),
        "best_true_score": best_score,
        "best_true_rank": (better + 1 if len(indices) else None),
        "best_true_score_tie_count": tied,
        "rank_definition": "1 + candidates with strictly greater score",
    }


def score_invariant(paths, blocks, pair, model,
                    binary=invariant.DEFAULT_BINARY) -> np.ndarray:
    with invariant.GpuPrefixScorer(binary, blocks, pair, model) as scorer:
        return scorer.score(np.asarray(paths, dtype=np.uint8))


def constrained_multistart(paths, blocks, pair, quad, restarts, iterations,
                           binary=CONSTRAINED_BINARY, seed=BOARD_SEED):
    paths = np.asarray(paths, dtype=np.uint8)
    best = np.full(len(paths), -np.inf)
    for restart in range(restarts):
        restart_seed = base.derive_seed(seed, restart)
        parts = []
        for start in range(0, len(paths), BOARD_CHUNK):
            scores, _, _ = width19.gpu_coarse_screen(
                binary, blocks, pair, quad,
                paths[start:start + BOARD_CHUNK], iterations=iterations,
                seed=restart_seed)
            parts.append(scores)
        current = np.concatenate(parts) if parts else np.empty(0)
        best = np.maximum(best, current)
    return best


def canonical_token_rows(blocks, pair, path):
    """Reproduce the constrained kernel's pair-canonical slot convention."""
    remaining = [symbol for symbol in base.NINE_SYMBOLS if symbol not in pair]
    mapping = {symbol: index for index, symbol in enumerate(
        [pair[0], pair[1], *remaining])}
    rows = []
    for row in range(len(blocks[0])):
        raw = [mapping[blocks[int(column)][row]] for column in path]
        tokens = []
        index = 0
        while index < len(raw):
            symbol = raw[index]
            if symbol < 2:
                if index + 1 == len(raw):
                    break
                tokens.append(7 + symbol * 9 + raw[index + 1])
                index += 2
            else:
                tokens.append(symbol - 2)
                index += 1
        rows.append(np.asarray(tokens, dtype=np.int64))
    return rows


def gpu_parity(binary=CONSTRAINED_BINARY) -> dict:
    """Verify the two-line geometry port against the existing CPU oracle."""
    fixture = exact.make_fixture(0, "dev")
    blocks = prefix.blocks_from_observed(fixture)
    pair = tuple(fixture["pair"])
    truth = prefix.order_to_sequence(fixture["order"])
    paths = np.asarray(sorted(bidi.true_windows(truth, 7))[:8],
                       dtype=np.uint8)
    quad, _ = base.load_language_model()
    errors = []
    initial_scores, initial_windows, initial_boards = width19.gpu_coarse_screen(
        binary, blocks, pair, quad, paths, iterations=0, seed=BOARD_SEED)
    scores, windows, boards = width19.gpu_coarse_screen(
        binary, blocks, pair, quad, paths, iterations=37, seed=BOARD_SEED)
    for index, path in enumerate(paths):
        rows = canonical_token_rows(blocks, pair, path)
        seed = rowcv.path_seed(BOARD_SEED, path)
        initial_board, initial_score, cpu_windows = constrained_cpu.anneal(
            rows, quad, seed, iterations=0)
        if not np.array_equal(initial_board, initial_boards[index]):
            raise AssertionError("width-19 CPU/GPU initial board mismatch")
        errors.append(abs(initial_score - initial_scores[index]))
        returned = boards[index].astype(np.int64)
        if not constrained_cpu.respects_partition(returned):
            raise AssertionError("width-19 GPU board escaped the partition")
        total = sum(base.score_indices(returned[row], quad)
                    for row in rows if len(row) >= 4)
        recomputed = total / cpu_windows if cpu_windows else -1e9
        errors.append(abs(recomputed - scores[index]))
        if cpu_windows != initial_windows[index] or cpu_windows != windows[index]:
            raise AssertionError("width-19 CPU/GPU window-count mismatch")
    maximum = max(errors)
    if maximum > 1e-10:
        raise AssertionError(f"width-19 CUDA score mismatch: {maximum}")
    return {
        "paths": len(paths),
        "binary": str(binary),
        "binary_sha256": hashlib.sha256(Path(binary).read_bytes()).hexdigest(),
        "exact_initial_board_parity": True,
        "returned_boards_respect_partition": True,
        "max_abs_score_error": maximum,
    }


def save_population(path, paths, scores) -> str:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(path, paths=np.asarray(paths, dtype=np.uint8),
             scores=np.asarray(scores, dtype=np.float64))
    return str(path)


def run_front(fixture_index=13, split="dev", work_dir=DEFAULT_WORK_DIR,
              prefix_binary=invariant.DEFAULT_BINARY,
              board_binary=CONSTRAINED_BINARY) -> dict:
    if split not in base.FIXTURE_SPLITS:
        raise ValueError("unknown fixture split")
    fixture = exact.make_fixture(fixture_index, split)
    models = exact.train_profile_models()
    blocks = prefix.blocks_from_observed(fixture)
    pair = tuple(fixture["pair"])
    truth = prefix.order_to_sequence(fixture["order"])
    quad, _ = base.load_language_model()
    work_dir = Path(work_dir)
    began = time.monotonic()
    diagnostics = []

    paths = initial_paths()
    scores = score_invariant(
        paths, blocks, pair, models[4], binary=prefix_binary)
    for depth in range(4, FRONT_SCHEDULE["switch_depth"] + 1):
        capacity = (FRONT_SCHEDULE["keep_preboard"]
                    if depth == FRONT_SCHEDULE["switch_depth"]
                    else FRONT_SCHEDULE["keep_penultimate"]
                    if depth == FRONT_SCHEDULE["switch_depth"] - 1
                    else FRONT_SCHEDULE["keep_early"])
        before = true_record(paths, scores, truth, depth)
        paths, scores, unique = select_diverse(paths, scores, capacity)
        after = true_record(paths, scores, truth, depth)
        diagnostics.append({"depth": depth, "generated_unique": unique,
                            "before_selection": before,
                            "after_selection": after})
        if depth < FRONT_SCHEDULE["switch_depth"]:
            paths = expand_bidirectional(paths)
            scores = score_invariant(
                paths, blocks, pair, models[depth + 1], binary=prefix_binary)

    board6 = constrained_multistart(
        paths, blocks, pair, quad, FRONT_SCHEDULE["coarse_restarts"],
        FRONT_SCHEDULE["coarse_iterations"], binary=board_binary)
    board6_before = true_record(paths, board6, truth, 6)
    paths, board6, unique6 = select_diverse(
        paths, board6, FRONT_SCHEDULE["keep_board"])
    board6_after = true_record(paths, board6, truth, 6)

    paths7 = expand_bidirectional(paths)
    scores7 = constrained_multistart(
        paths7, blocks, pair, quad, FRONT_SCHEDULE["coarse_restarts"],
        FRONT_SCHEDULE["coarse_iterations"], binary=board_binary)
    coarse7_before = true_record(paths7, scores7, truth, 7)
    paths7, scores7, unique7 = select_diverse(
        paths7, scores7, FRONT_SCHEDULE["depth7_coarse_keep"])
    coarse7_after = true_record(paths7, scores7, truth, 7)

    refined7 = constrained_multistart(
        paths7, blocks, pair, quad, FRONT_SCHEDULE["refine_restarts"],
        FRONT_SCHEDULE["refine_iterations"], binary=board_binary)
    refine7_before = true_record(paths7, refined7, truth, 7)
    paths7, refined7, refine_unique = select_diverse(
        paths7, refined7, FRONT_SCHEDULE["depth7_refine_keep"])
    refine7_after = true_record(paths7, refined7, truth, 7)
    checkpoint = save_population(
        work_dir / "depth7_refined.npz", paths7, refined7)
    result = {
        "phase": "490",
        "status": "development_width19_front_port_not_frozen",
        "faed_scored": False,
        "holdout_consumed": split == "holdout",
        "fixture_index": fixture_index,
        "split": split,
        "width": WIDTH,
        "pair": list(pair),
        "schedule": FRONT_SCHEDULE,
        "schedule_sha256": schedule_sha256(),
        "invariant_diagnostics": diagnostics,
        "depth6_board": {
            "generated_unique": unique6,
            "before_selection": board6_before,
            "after_selection": board6_after,
        },
        "depth7_coarse": {
            "generated_unique": unique7,
            "before_selection": coarse7_before,
            "after_selection": coarse7_after,
        },
        "depth7_refine": {
            "generated_unique": refine_unique,
            "before_selection": refine7_before,
            "after_selection": refine7_after,
        },
        "checkpoint": checkpoint,
        "wall_seconds": time.monotonic() - began,
    }
    work_dir.mkdir(parents=True, exist_ok=True)
    (work_dir / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def self_test() -> dict:
    sample = initial_paths(width=5, depth=3)
    if sample.shape != (60, 3) or len({tuple(row) for row in sample}) != 60:
        raise AssertionError("initial path enumeration changed")
    parents = np.asarray([[0, 1], [1, 2]], dtype=np.uint8)
    children = expand_bidirectional(parents, width=4)
    expected = {
        (2, 0, 1), (0, 1, 2), (3, 0, 1), (0, 1, 3),
        (0, 1, 2), (1, 2, 0), (3, 1, 2), (1, 2, 3),
    }
    if {tuple(row) for row in children} != expected:
        raise AssertionError("bidirectional expansion changed")
    if exact.make_fixture(0)["width"] != WIDTH:
        raise AssertionError("exact-profile fixture is not width 19")
    if len(prefix.blocks_from_observed(exact.make_fixture(0))) != WIDTH:
        raise AssertionError("width-19 block geometry changed")
    source = (SCRIPT_DIR / "phase490_width19_constrained_board_server.cu").read_text()
    if "constexpr int WIDTH = 19, ROWS = 30, SLOTS = 25;" not in source:
        raise AssertionError("width-19 constrained CUDA geometry changed")
    if 'std::memcmp(magic,"P484QG1\\0",8)' not in source:
        raise AssertionError("width-19 constrained CUDA wire magic changed")
    return {
        "width": WIDTH,
        "rows": ROWS,
        "schedule_sha256": schedule_sha256(),
        "faed_imported": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--gpu-parity", action="store_true")
    group.add_argument("--run-front", action="store_true")
    parser.add_argument("--fixture-index", type=int, default=13)
    parser.add_argument("--split", choices=base.FIXTURE_SPLITS, default="dev")
    parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK_DIR)
    parser.add_argument("--prefix-binary", type=Path,
                        default=invariant.DEFAULT_BINARY)
    parser.add_argument("--board-binary", type=Path,
                        default=CONSTRAINED_BINARY)
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), indent=2))
    elif args.gpu_parity:
        print(json.dumps(gpu_parity(args.board_binary), indent=2))
    else:
        print(json.dumps(run_front(
            args.fixture_index, args.split, args.work_dir,
            args.prefix_binary, args.board_binary), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
