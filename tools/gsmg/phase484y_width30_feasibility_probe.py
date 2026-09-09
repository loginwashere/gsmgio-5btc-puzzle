#!/usr/bin/env python3
"""Width-30 exact-profile shortlist feasibility probe (development only).

This deliberately stops at depth 8.  It tests whether the complementary
30-column orientation preserves genuine order fragments before any joint
checkerboard machinery is ported or FAED is examined at width 30.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import struct
import subprocess
import time
from pathlib import Path

import numpy as np

import phase484a_raw_symbol_vic_solver as base
import phase484j_constructive_prefix_beam_probe as prefix
import phase484k_bidirectional_segment_assembly_probe as bidi
import phase484n_hybrid_prefix_scorer as gpu19
import phase484x_exact_faed_profile_power_probe as exact

SCRIPT_DIR = Path(__file__).resolve().parent
WIDTH, ROWS = 30, 19
START_DEPTH, STOP_DEPTH = 4, 8
DEFAULT_KEEP = 262144
DEFAULT_FINAL_KEEP = 1048576
DEFAULT_DEPTH6_KEEP = 524288
DEFAULT_DEPTH7_KEEP = 1048576
SCORE_CHUNK = 16000000
DEFAULT_BINARY = SCRIPT_DIR.parents[1] / "_work/phase484y/prefix_server"
MAGIC = b"P484YG1\0"
SEED = 0x484A030
TRAIN_INDICES = tuple(range(3, 13))


def width30_fixture(fixture_index: int, split: str = "dev") -> dict:
    source = exact.make_fixture(fixture_index, split)
    fixture = dict(source)
    fixture["width"] = WIDTH
    rng = base.PCG32(base.derive_seed(SEED, fixture_index,
                                     0 if split == "dev" else 1))
    fixture["order"] = rng.permutation(WIDTH)
    fixture["observed"] = base.Geometry(base.RAW_LENGTH, WIDTH).encrypt(
        fixture["raw"], fixture["order"])
    fixture["raw_sha256"] = hashlib.sha256(
        fixture["raw"].encode("ascii")).hexdigest()
    base.verify_fixture(fixture)
    exact.verify_exact_profile(fixture)
    return fixture


def train_models(train_indices=TRAIN_INDICES):
    fixtures = [width30_fixture(index) for index in train_indices]
    models = {}
    for depth in range(START_DEPTH, STOP_DEPTH + 1):
        positives, negatives = [], []
        for fixture in fixtures:
            blocks = prefix.blocks_from_observed(fixture)
            truth = prefix.order_to_sequence(fixture["order"])
            true_paths = bidi.true_windows(truth, depth)
            positives.extend(prefix.prefix_features(
                blocks, path, exact.PAIR) for path in sorted(true_paths))
            rng = base.PCG32(base.derive_seed(
                SEED, depth, fixture["fixture_index"]))
            made = set()
            while len(made) < prefix.NEGATIVE_RATIO * len(true_paths):
                path = tuple(rng.permutation(WIDTH)[:depth])
                if path not in true_paths:
                    made.add(path)
            negatives.extend(prefix.prefix_features(
                blocks, path, exact.PAIR) for path in sorted(made))
        models[depth] = prefix.fit_centroid(positives, negatives)
    return models


def canonical_blocks(blocks, pair) -> bytes:
    remaining = [symbol for symbol in base.NINE_SYMBOLS if symbol not in pair]
    mapping = {symbol: index for index, symbol in enumerate(
        [pair[0], pair[1], *remaining])}
    if len(blocks) != WIDTH or any(len(block) != ROWS for block in blocks):
        raise ValueError("width-30 scorer requires 30 blocks of 19 rows")
    return bytes(mapping[symbol] for block in blocks for symbol in block)


class GpuWidth30Scorer:
    def __init__(self, binary: Path, blocks, pair, model):
        coefficient, intercept = gpu19.linear_coefficients(model)
        self.process = subprocess.Popen(
            [str(binary)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        self.process.stdin.write(MAGIC)
        self.process.stdin.write(canonical_blocks(blocks, pair))
        self.process.stdin.write(coefficient.tobytes())
        self.process.stdin.write(struct.pack("<d", intercept))
        self.process.stdin.flush()

    def score(self, paths) -> np.ndarray:
        paths = np.ascontiguousarray(paths, dtype=np.uint8)
        if paths.ndim != 2 or not START_DEPTH <= paths.shape[1] <= WIDTH:
            raise ValueError("paths must have depth 4..30")
        if not len(paths):
            return np.empty(0, dtype=np.float64)
        if np.any(paths >= WIDTH):
            raise ValueError("path column outside width 30")
        self.process.stdin.write(struct.pack("<II", len(paths), paths.shape[1]))
        self.process.stdin.write(paths.tobytes())
        self.process.stdin.flush()
        needed = len(paths) * 8
        data = gpu19.read_exact(self.process.stdout, needed)
        if len(data) != needed:
            error = self.process.stderr.read().decode("utf-8", "replace")
            raise RuntimeError(f"width-30 scorer stopped early: {error}")
        return np.frombuffer(data, dtype="<f8").copy()

    def close(self):
        if self.process.poll() is None:
            self.process.stdin.write(struct.pack("<II", 0, 0))
            self.process.stdin.flush()
            self.process.stdin.close()
            return_code = self.process.wait(timeout=10)
            if return_code:
                error = self.process.stderr.read().decode("utf-8", "replace")
                raise RuntimeError(
                    f"width-30 scorer exited {return_code}: {error}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.close()


def score_chunked(scorer, paths, chunk_size=SCORE_CHUNK):
    if chunk_size < 1:
        raise ValueError("score chunk size must be positive")
    return np.concatenate([
        scorer.score(paths[start:start + chunk_size])
        for start in range(0, len(paths), chunk_size)
    ]) if len(paths) else np.empty(0, dtype=np.float64)


def initial_paths(depth: int = START_DEPTH) -> np.ndarray:
    if depth not in (4, 5):
        raise ValueError("exhaustive start depth must be 4 or 5")
    count = math.prod(range(WIDTH - depth + 1, WIDTH + 1))
    values = np.fromiter(
        (value for path in itertools.permutations(range(WIDTH), depth)
         for value in path), dtype=np.uint8, count=count * depth)
    return values.reshape(count, depth)


def expand_bidirectional(paths: np.ndarray) -> np.ndarray:
    paths = np.asarray(paths, dtype=np.uint8)
    width, depth = WIDTH, paths.shape[1]
    total = sum(2 * int(np.count_nonzero(
        ~np.any(paths == column, axis=1))) for column in range(width))
    expanded = np.empty((total, depth + 1), dtype=np.uint8)
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
    if offset != total:
        raise AssertionError("expansion count mismatch")
    return expanded


def packed_keys(paths: np.ndarray) -> np.ndarray:
    if paths.shape[1] > 12:
        raise ValueError("5-bit uint64 path keys are collision-free only through depth 12")
    keys = np.zeros(len(paths), dtype=np.uint64)
    for column in paths.T:
        keys = (keys << np.uint64(5)) | column.astype(np.uint64)
    return keys


def unique_path_indices(paths: np.ndarray) -> np.ndarray:
    if paths.shape[1] <= 12:
        _, indices = np.unique(packed_keys(paths), return_index=True)
    else:
        _, indices = np.unique(paths, axis=0, return_index=True)
    return indices


def ranked_indices(paths: np.ndarray, scores: np.ndarray,
                   indices=None) -> np.ndarray:
    if indices is None:
        indices = np.arange(len(paths), dtype=np.int64)
    else:
        indices = np.asarray(indices, dtype=np.int64)
    selected = paths[indices]
    keys = tuple(selected[:, column]
                 for column in range(selected.shape[1] - 1, -1, -1))
    order = np.lexsort((*keys, -scores[indices]))
    return indices[order]


def true_path_mask(paths: np.ndarray, truth, depth: int) -> np.ndarray:
    mask = np.zeros(len(paths), dtype=bool)
    for target in bidi.true_windows(truth, depth):
        mask |= np.all(paths == np.asarray(target, dtype=np.uint8), axis=1)
    return mask


def select_diverse(paths: np.ndarray, scores: np.ndarray,
                   keep: int) -> tuple[np.ndarray, np.ndarray, int]:
    """Exact dedupe, half endpoint reservation, then global score fill."""
    unique_index = unique_path_indices(paths)
    paths = paths[unique_index]
    scores = scores[unique_index]
    unique_count = len(paths)
    keep = min(keep, unique_count)
    reserved_budget = keep // 2
    quota = max(1, reserved_budget // (WIDTH * (WIDTH - 1)))
    groups = paths[:, 0].astype(np.int16) * WIDTH + paths[:, -1]
    group_order = np.argsort(groups, kind="stable")
    sorted_groups = groups[group_order]
    boundaries = np.flatnonzero(np.r_[True, sorted_groups[1:] != sorted_groups[:-1], True])
    reserved = []
    for left, right in zip(boundaries[:-1], boundaries[1:]):
        members = group_order[left:right]
        take = min(quota, len(members))
        if take < len(members):
            chosen = members[np.argpartition(-scores[members], take - 1)[:take]]
        else:
            chosen = members
        reserved.extend(chosen.tolist())
    reserved = np.asarray(reserved, dtype=np.int64)
    if len(reserved) >= keep:
        selected = ranked_indices(paths, scores, reserved)[:keep]
        return paths[selected].copy(), scores[selected].copy(), unique_count
    chosen = np.zeros(unique_count, dtype=bool)
    chosen[reserved] = True
    fill_count = keep - int(np.count_nonzero(chosen))
    global_take = min(unique_count, keep + len(reserved))
    if global_take < unique_count:
        global_best = np.argpartition(-scores, global_take - 1)[:global_take]
    else:
        global_best = np.arange(unique_count)
    fill = ranked_indices(paths, scores, global_best)
    fill = fill[~chosen[fill]][:fill_count]
    selected = np.concatenate([reserved, fill])
    selected = ranked_indices(paths, scores, selected)
    return paths[selected].copy(), scores[selected].copy(), unique_count


def true_ranks(paths: np.ndarray, scores: np.ndarray, truth, depth: int):
    mask = true_path_mask(paths, truth, depth)
    order = ranked_indices(paths, scores)
    return (np.flatnonzero(mask[order]) + 1).tolist()


def generated_true_metrics(paths: np.ndarray, scores: np.ndarray,
                           truth, depth: int):
    unique_index = unique_path_indices(paths)
    unique_paths, unique_scores = paths[unique_index], scores[unique_index]
    mask = true_path_mask(unique_paths, truth, depth)
    if not np.any(mask):
        return 0, None
    order = ranked_indices(unique_paths, unique_scores)
    ranks = np.flatnonzero(mask[order]) + 1
    return int(np.count_nonzero(mask)), int(np.min(ranks))


def run_fixture(fixture_index: int, keep: int = DEFAULT_KEEP,
                final_keep: int = DEFAULT_FINAL_KEEP,
                binary: Path = DEFAULT_BINARY, models=None,
                start_depth: int = START_DEPTH,
                depth6_keep: int | None = None,
                depth7_keep: int | None = None) -> dict:
    fixture = width30_fixture(fixture_index)
    if models is None:
        models = train_models()
    blocks = prefix.blocks_from_observed(fixture)
    truth = prefix.order_to_sequence(fixture["order"])
    diagnostics = []
    began = time.monotonic()
    paths = initial_paths(start_depth)
    with GpuWidth30Scorer(binary, blocks, exact.PAIR,
                          models[start_depth]) as scorer:
        scores = score_chunked(scorer, paths)
    for depth in range(start_depth, STOP_DEPTH + 1):
        generated_true_count, generated_best_true_rank = generated_true_metrics(
            paths, scores, truth, depth)
        select_began = time.monotonic()
        depth_keep = (final_keep if depth == STOP_DEPTH else
                      depth7_keep if depth == 7 and depth7_keep is not None else
                      depth6_keep if depth == 6 and depth6_keep is not None else
                      keep)
        paths, scores, unique_count = select_diverse(paths, scores, depth_keep)
        selection_seconds = time.monotonic() - select_began
        ranks = true_ranks(paths, scores, truth, depth)
        record = {
            "depth": depth,
            "generated": unique_count,
            "retained": len(paths),
            "generated_true_segments": generated_true_count,
            "generated_best_true_rank": generated_best_true_rank,
            "true_segments_retained": len(ranks),
            "best_true_rank": min(ranks) if ranks else None,
            "selection_seconds": selection_seconds,
        }
        diagnostics.append(record)
        if depth == STOP_DEPTH or not ranks:
            break
        expand_began = time.monotonic()
        paths = expand_bidirectional(paths)
        record["expanded_with_duplicates"] = len(paths)
        record["expansion_seconds"] = time.monotonic() - expand_began
        score_began = time.monotonic()
        with GpuWidth30Scorer(binary, blocks, exact.PAIR,
                              models[depth + 1]) as scorer:
            scores = score_chunked(scorer, paths)
        record["gpu_score_seconds"] = time.monotonic() - score_began
    return {
        "phase": "484Y",
        "status": "development_width30_shortlist_feasibility_not_frozen",
        "faed_scored": False,
        "holdout_consumed": False,
        "width": WIDTH,
        "rows": ROWS,
        "fixture_index": fixture_index,
        "beam_keep": keep,
        "depth8_keep": final_keep,
        "depth6_keep": depth6_keep if depth6_keep is not None else keep,
        "depth7_keep": depth7_keep if depth7_keep is not None else keep,
        "exhaustive_start_depth": start_depth,
        "exact_profile_fixture": exact.fixture_summary(fixture),
        "survived_depth8": diagnostics[-1]["depth"] == STOP_DEPTH and
                           diagnostics[-1]["true_segments_retained"] > 0,
        "depth_diagnostics": diagnostics,
        "wall_seconds": time.monotonic() - began,
    }


def gpu_parity(binary=DEFAULT_BINARY):
    fixture = width30_fixture(13)
    models = train_models((3, 4))
    blocks = prefix.blocks_from_observed(fixture)
    paths = initial_paths()[:256]
    expected = np.asarray([prefix.score_prefix(
        models[START_DEPTH], blocks, exact.PAIR, path) for path in paths])
    with GpuWidth30Scorer(binary, blocks, exact.PAIR,
                          models[START_DEPTH]) as scorer:
        actual = scorer.score(paths)
    error = float(np.max(np.abs(expected - actual)))
    if error > 1e-10:
        raise AssertionError(f"CPU/GPU mismatch: {error}")
    return {"paths": len(paths), "max_abs_error": error}


def run_batch(indices, keep=DEFAULT_KEEP, final_keep=DEFAULT_FINAL_KEEP,
              binary=DEFAULT_BINARY, start_depth=START_DEPTH,
              depth6_keep=None, depth7_keep=None):
    models = train_models()
    began = time.monotonic()
    records = [run_fixture(index, keep, final_keep, binary, models, start_depth,
                           depth6_keep, depth7_keep)
               for index in indices]
    return {
        "phase": "484Y",
        "status": "development_width30_shortlist_batch_not_frozen",
        "faed_scored": False,
        "holdout_consumed": False,
        "indices": list(indices),
        "beam_keep": keep,
        "depth8_keep": final_keep,
        "depth6_keep": depth6_keep if depth6_keep is not None else keep,
        "depth7_keep": depth7_keep if depth7_keep is not None else keep,
        "exhaustive_start_depth": start_depth,
        "survived_count": sum(record["survived_depth8"] for record in records),
        "fixture_count": len(records),
        "records": records,
        "wall_seconds_excluding_shared_training": time.monotonic() - began,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--batch", nargs="+", type=int)
    parser.add_argument("--fixture-index", type=int, default=13)
    parser.add_argument("--keep", type=int, default=DEFAULT_KEEP)
    parser.add_argument("--final-keep", type=int, default=DEFAULT_FINAL_KEEP)
    parser.add_argument("--depth6-keep", type=int)
    parser.add_argument("--depth7-keep", type=int)
    parser.add_argument("--start-depth", type=int, choices=(4, 5),
                        default=START_DEPTH)
    parser.add_argument("--binary", type=Path, default=DEFAULT_BINARY)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(gpu_parity(args.binary), indent=2))
        return 0
    if args.batch:
        result = run_batch(args.batch, args.keep, args.final_keep, args.binary,
                           args.start_depth, args.depth6_keep,
                           args.depth7_keep)
        output = args.output or SCRIPT_DIR / "phase484y_width30_batch.json"
        output.write_text(json.dumps(result, indent=2) + "\n")
        print("survived", result["survived_count"], "/",
              result["fixture_count"], "wall",
              round(result["wall_seconds_excluding_shared_training"], 3))
        for record in result["records"]:
            print("fixture", record["fixture_index"],
                  "survived", record["survived_depth8"],
                  "depths", [(item["depth"],
                              item["true_segments_retained"])
                             for item in record["depth_diagnostics"]])
        print("wrote", output)
        return 0
    if not args.run:
        parser.error("use --self-test or --run")
    result = run_fixture(args.fixture_index, args.keep, args.final_keep,
                         args.binary, start_depth=args.start_depth,
                         depth6_keep=args.depth6_keep,
                         depth7_keep=args.depth7_keep)
    output = args.output or SCRIPT_DIR / (
        f"phase484y_width30_i{args.fixture_index}_k{args.keep}_"
        f"f{args.final_keep}.json")
    output.write_text(json.dumps(result, indent=2) + "\n")
    print("survived depth 8", result["survived_depth8"],
          "wall", round(result["wall_seconds"], 3))
    for record in result["depth_diagnostics"]:
        print(record)
    print("wrote", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
