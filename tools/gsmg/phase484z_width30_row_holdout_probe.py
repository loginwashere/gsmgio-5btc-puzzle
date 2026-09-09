#!/usr/bin/env python3
"""Development probe: row held-out cross-validated board fitting.

The depth-7 true-parent-inherited-board diagnostic
(phase484z_width30_i15_true_parent_inherited_board.json) showed a board
annealed and scored on the *same* 19 rows only ranks the two genuine depth-8
children 21st of 46 candidates: a short fragment can fit its own 25-letter
board to whatever tokens happen to land on those rows, so false fragments
overfit into pseudo-English on the very data used to score them.

This probe tests the fix proposed in that diagnostic's follow-up: fit the
board on a subset of rows and score it only on rows held out from that fit,
rotating which rows are held out and combining the held-out scores, so a
candidate can only score well by genuinely generalizing across independently
sampled rows -- something only a real order/board pairing has reason to do.

Development only: this module never imports FAED and never uses holdout
fixtures (fixture 15 here is the project's "dev" split, matching every other
484Y/Z development script).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from pathlib import Path

import numpy as np

import phase484a_raw_symbol_vic_solver as base
import phase484j_constructive_prefix_beam_probe as prefix
import phase484k_bidirectional_segment_assembly_probe as bidi
import phase484y_width30_feasibility_probe as width30

SCRIPT_DIR = Path(__file__).resolve().parent
ROWS = width30.ROWS
SWITCH_DEPTH = 8
DEFAULT_FOLDS = 3
DEFAULT_RESTARTS = 4
DEFAULT_ITERS = 3000
DEFAULT_T0 = 20.0
DEFAULT_T1 = 1.0
SEED = 0x484ACF01
INHERITED_BOARD_DIAGNOSTIC_PARENT = (24, 16, 20, 10, 28, 4, 19)
QUAD: np.ndarray | None = None


def path_seed(seed: int, path) -> int:
    """Order-independent candidate seed used by the established GPU solver."""
    value = base.derive_seed(seed, len(path), 0)
    for index, column in enumerate(path):
        value = base.derive_seed(value, int(column) + 1, index + 1)
    return value


def pool_sha256(paths) -> str:
    payload = json.dumps([list(map(int, path)) for path in paths],
                         separators=(",", ":")).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def make_folds(k: int = DEFAULT_FOLDS, rows: int = ROWS) -> list[list[int]]:
    """Deterministic round-robin row partition (no RNG needed)."""
    if not 2 <= k <= rows:
        raise ValueError("fold count must be between 2 and the row count")
    folds = [[] for _ in range(k)]
    for row in range(rows):
        folds[row % k].append(row)
    return folds


def row_token_indices(blocks, pair: tuple[str, str], path) -> list[np.ndarray]:
    """25-slot indices per row for the raw stream selected by `path`.

    Mirrors phase484o_joint_board_order_ceiling.cpu_board_score's
    per-row segmentation, generalized from width-19/ROWS-30 to
    width-30/ROWS-19 and from a full-width path to any path length.
    """
    codes = base.slot_codes(pair)
    code_to_slot = {code: index for index, code in enumerate(codes)}
    rows = []
    for row in range(ROWS):
        raw = "".join(blocks[column][row] for column in path)
        segmented = base.segment_raw(raw, pair)
        if segmented is None:
            # A trailing lone escape byte is an incomplete window at this
            # depth, not a decoding failure; score the complete prefix.
            segmented = base.segment_raw(raw[:-1], pair) or ()
        rows.append(np.asarray([code_to_slot[code] for code in segmented],
                                dtype=np.int64))
    return rows


def subset_score(board: np.ndarray, rows_indices: list[np.ndarray],
                  row_subset) -> tuple[float, int]:
    """Raw (unnormalized) summed quadgram log-probability and window count
    over only the given rows, never letting windows span a row boundary."""
    total, windows = 0.0, 0
    for row in row_subset:
        idx = rows_indices[row]
        if len(idx) >= 4:
            total += base.score_indices(board[idx], QUAD)
            windows += len(idx) - 3
    return total, windows


def anneal_board_subset(rows_indices: list[np.ndarray], row_subset,
                        rng: base.PCG32, iters: int, t0: float,
                        t1: float) -> tuple[np.ndarray, float]:
    """Simulated annealing restricted to `row_subset`'s windows only.
    Mirrors phase484a_raw_symbol_vic_solver.anneal_board's schedule and
    swap proposal; the difference is the multi-row, boundary-safe score."""
    n = len(base.LETTER_ALPHABET)
    key = np.array(rng.permutation(n), dtype=np.int64)

    def score(candidate: np.ndarray) -> float:
        total, _ = subset_score(candidate, rows_indices, row_subset)
        return total

    current = score(key)
    best, best_key = current, key.copy()
    cool = (t1 / t0) ** (1.0 / max(1, iters))
    temperature = t0
    for _ in range(iters):
        i, j = rng.below(n), rng.below(n)
        if i != j:
            key[i], key[j] = key[j], key[i]
            proposed = score(key)
            delta = proposed - current
            if delta >= 0 or rng.random() < math.exp(delta / temperature):
                current = proposed
                if proposed > best:
                    best, best_key = proposed, key.copy()
            else:
                key[i], key[j] = key[j], key[i]
        temperature *= cool
    return best_key, best


def fit_best(rows_indices: list[np.ndarray], row_subset, seed: int,
            restarts: int, iters: int, t0: float, t1: float) -> np.ndarray:
    best_total, best_key = -math.inf, None
    for restart in range(restarts):
        rng = base.PCG32(base.derive_seed(seed, restart))
        key, total = anneal_board_subset(rows_indices, row_subset, rng,
                                         iters, t0, t1)
        if total > best_total:
            best_total, best_key = total, key
    return best_key


def cv_score(rows_indices: list[np.ndarray], folds: list[list[int]],
            seed: int, restarts: int, iters: int, t0: float,
            t1: float) -> dict:
    held_total, held_windows = 0.0, 0
    for fold_index, held_out in enumerate(folds):
        train = [row for row in range(ROWS) if row not in held_out]
        fold_seed = base.derive_seed(seed, fold_index)
        board = fit_best(rows_indices, train, fold_seed, restarts, iters,
                         t0, t1)
        total, windows = subset_score(board, rows_indices, held_out)
        held_total += total
        held_windows += windows
    normalized = held_total / held_windows if held_windows else -1e9
    return {"normalized": normalized, "total": held_total,
            "windows": held_windows}


def baseline_score(rows_indices: list[np.ndarray], seed: int, restarts: int,
                   iters: int, t0: float, t1: float) -> dict:
    """Fit and score on every row -- the status-quo approach being tested
    against, using identically-sized SA budget for a fair comparison."""
    all_rows = list(range(ROWS))
    board = fit_best(rows_indices, all_rows, seed, restarts, iters, t0, t1)
    total, windows = subset_score(board, rows_indices, all_rows)
    normalized = total / windows if windows else -1e9
    return {"normalized": normalized, "total": total, "windows": windows}


def ranks_of(scores: np.ndarray) -> np.ndarray:
    """1-based rank (1 = highest score) of every entry."""
    order = np.argsort(-scores, kind="stable")
    ranks = np.empty(len(scores), dtype=np.int64)
    ranks[order] = np.arange(1, len(scores) + 1)
    return ranks


def rank_of(scores: np.ndarray, true_mask: np.ndarray) -> int | None:
    true_ranks = ranks_of(scores)[true_mask]
    return int(true_ranks.min()) if len(true_ranks) else None


def run(fixture_index: int = 15, folds: int = DEFAULT_FOLDS,
       restarts: int = DEFAULT_RESTARTS, iters: int = DEFAULT_ITERS,
       t0: float = DEFAULT_T0, t1: float = DEFAULT_T1,
       seed: int = SEED) -> dict:
    global QUAD
    fixture = width30.width30_fixture(fixture_index, "dev")
    blocks = prefix.blocks_from_observed(fixture)
    pair = tuple(fixture["pair"])
    truth = prefix.order_to_sequence(fixture["order"])
    QUAD, _ = base.load_language_model()

    parent_windows = bidi.true_windows(truth, SWITCH_DEPTH - 1)
    # Any true depth-7 window works equally well for this probe; use the
    # same one as the original inherited-board diagnostic
    # (phase484z_width30_i15_true_parent_inherited_board.json's
    # "parent_path") so its 21-of-46 baseline result is directly comparable.
    parent = INHERITED_BOARD_DIAGNOSTIC_PARENT
    if parent not in parent_windows:
        raise AssertionError(
            "fixture/truth mismatch: expected parent is not a true window "
            "of this fixture's order")

    fold_list = make_folds(folds)
    children = width30.expand_bidirectional(np.asarray([parent], dtype=np.uint8))
    true_mask = width30.true_path_mask(children, truth, SWITCH_DEPTH)

    began = time.monotonic()
    cv_scores = np.empty(len(children), dtype=np.float64)
    baseline_scores = np.empty(len(children), dtype=np.float64)
    per_candidate = []
    for index, path in enumerate(children):
        rows_indices = row_token_indices(blocks, pair, path.tolist())
        candidate_seed = path_seed(seed, path)
        cv = cv_score(rows_indices, fold_list, candidate_seed, restarts,
                     iters, t0, t1)
        baseline = baseline_score(rows_indices, candidate_seed, restarts,
                                  iters, t0, t1)
        cv_scores[index] = cv["normalized"]
        baseline_scores[index] = baseline["normalized"]
        per_candidate.append({
            "path": path.tolist(), "is_true": bool(true_mask[index]),
            "cv": cv, "baseline": baseline,
        })

    return {
        "phase": "484Z",
        "status": "development_row_holdout_probe_not_frozen",
        "faed_scored": False,
        "holdout_consumed": False,
        "fixture_index": fixture_index,
        "width": width30.WIDTH,
        "rows": ROWS,
        "switch_depth": SWITCH_DEPTH,
        "parent_path": list(parent),
        "candidate_count": len(children),
        "true_segments": int(true_mask.sum()),
        "folds": folds,
        "fold_sizes": [len(fold) for fold in fold_list],
        "restarts": restarts,
        "iterations": iters,
        "seed": seed,
        "candidate_seed_scheme": "path_seed_v1",
        "candidate_pool_sha256": pool_sha256(children),
        "cv_best_true_rank": rank_of(cv_scores, true_mask),
        "baseline_best_true_rank": rank_of(baseline_scores, true_mask),
        "per_candidate": per_candidate,
        "wall_seconds": time.monotonic() - began,
    }


def sample_background(count: int, exclude: set, seed: int) -> list[tuple[int, ...]]:
    """`count` distinct random depth-8 column combinations, none a true
    window and none a duplicate -- a background of structurally unrelated
    candidates, standing in for the millions of unrelated paths a real
    depth-8 board screen ranks a true fragment against (unlike the 46-item
    sibling pool, where every candidate shares the true fragment's first
    seven columns)."""
    rng = base.PCG32(seed)
    background = []
    seen = set(exclude)
    while len(background) < count:
        candidate = tuple(rng.permutation(width30.WIDTH)[:SWITCH_DEPTH])
        if candidate not in seen:
            seen.add(candidate)
            background.append(candidate)
    return background


def run_background(fixture_index: int = 15, background_count: int = 400,
                   folds: int = DEFAULT_FOLDS, restarts: int = 3,
                   iters: int = 2000, t0: float = DEFAULT_T0,
                   t1: float = DEFAULT_T1, seed: int = SEED,
                   cv_restarts: int | None = None,
                   cv_iters: int | None = None) -> dict:
    """Do many structurally unrelated false depth-8 candidates out-score a
    true one once each gets its own independently fitted board? This is the
    multiple-comparisons version of the overfitting concern (many candidates,
    each with 25! board freedom, competing on ~50-60 windows of data), as
    opposed to the sibling probe's same-data-refit version.

    `cv_restarts`/`cv_iters` default to `restarts`/`iters` (the baseline's
    budget) but can be raised independently: each CV fold fits on only
    12-13 of 19 rows, so it starts from noticeably fewer quadgram windows
    than the baseline's full-row fit and may need more search to converge
    as well, not just an equal budget.
    """
    global QUAD
    cv_restarts = restarts if cv_restarts is None else cv_restarts
    cv_iters = iters if cv_iters is None else cv_iters
    fixture = width30.width30_fixture(fixture_index, "dev")
    blocks = prefix.blocks_from_observed(fixture)
    pair = tuple(fixture["pair"])
    truth = prefix.order_to_sequence(fixture["order"])
    QUAD, _ = base.load_language_model()

    true_children = sorted(bidi.true_windows(truth, SWITCH_DEPTH))
    background = sample_background(
        background_count, set(true_children), base.derive_seed(seed, 0xB0))
    pool = true_children + background
    true_mask = np.array([True] * len(true_children)
                         + [False] * len(background))

    fold_list = make_folds(folds)
    began = time.monotonic()
    cv_scores = np.empty(len(pool), dtype=np.float64)
    baseline_scores = np.empty(len(pool), dtype=np.float64)
    for index, path in enumerate(pool):
        rows_indices = row_token_indices(blocks, pair, path)
        candidate_seed = path_seed(seed, path)
        cv_scores[index] = cv_score(
            rows_indices, fold_list, candidate_seed, cv_restarts, cv_iters,
            t0, t1)["normalized"]
        baseline_scores[index] = baseline_score(
            rows_indices, candidate_seed, restarts, iters, t0,
            t1)["normalized"]

    def summarize(scores: np.ndarray) -> dict:
        true_scores = scores[true_mask]
        background_scores = scores[~true_mask]
        true_ranks = ranks_of(scores)[true_mask]
        # For each true candidate, how many background candidates outrank it.
        beaten_by = [int(np.count_nonzero(background_scores > value))
                    for value in true_scores]
        return {
            "true_scores": true_scores.tolist(),
            "background_mean": float(background_scores.mean()),
            "background_std": float(background_scores.std()),
            "background_max": float(background_scores.max()),
            "best_true_rank": int(true_ranks.min()),
            "worst_true_rank": int(true_ranks.max()),
            "beaten_by_background_count": beaten_by,
        }

    per_candidate = [{
        "path": list(path), "is_true": bool(true_mask[index]),
        "baseline_score": float(baseline_scores[index]),
        "cv_score": float(cv_scores[index]),
    } for index, path in enumerate(pool)]

    return {
        "phase": "484Z",
        "status": "development_row_holdout_background_probe_not_frozen",
        "faed_scored": False,
        "holdout_consumed": False,
        "fixture_index": fixture_index,
        "width": width30.WIDTH,
        "rows": ROWS,
        "switch_depth": SWITCH_DEPTH,
        "true_child_count": len(true_children),
        "background_count": len(background),
        "pool_size": len(pool),
        "folds": folds,
        "fold_sizes": [len(fold) for fold in fold_list],
        "restarts": restarts,
        "iterations": iters,
        "cv_restarts": cv_restarts,
        "cv_iterations": cv_iters,
        "seed": seed,
        "candidate_seed_scheme": "path_seed_v1",
        "candidate_pool_sha256": pool_sha256(pool),
        "per_candidate": per_candidate,
        "baseline": summarize(baseline_scores),
        "cv": summarize(cv_scores),
        "wall_seconds": time.monotonic() - began,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--mode", choices=["siblings", "background"],
                        default="siblings")
    parser.add_argument("--fixture-index", type=int, default=15)
    parser.add_argument("--folds", type=int, default=DEFAULT_FOLDS)
    parser.add_argument("--restarts", type=int, default=DEFAULT_RESTARTS)
    parser.add_argument("--iterations", type=int, default=DEFAULT_ITERS)
    parser.add_argument("--background-count", type=int, default=400)
    parser.add_argument("--cv-restarts", type=int)
    parser.add_argument("--cv-iterations", type=int)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.run:
        parser.error("use --run")
    if args.mode == "siblings":
        result = run(args.fixture_index, args.folds, args.restarts,
                    args.iterations)
        output = args.output or SCRIPT_DIR / (
            f"phase484z_width30_row_holdout_i{args.fixture_index}_"
            f"k{args.folds}_r{args.restarts}_n{args.iterations}.json")
        output.write_text(json.dumps(result, indent=2) + "\n")
        print("true_segments", result["true_segments"], "of",
              result["candidate_count"])
        print("baseline best_true_rank", result["baseline_best_true_rank"])
        print("cv best_true_rank", result["cv_best_true_rank"])
    else:
        result = run_background(args.fixture_index, args.background_count,
                                args.folds, args.restarts, args.iterations,
                                cv_restarts=args.cv_restarts,
                                cv_iters=args.cv_iterations)
        cv_r, cv_n = result["cv_restarts"], result["cv_iterations"]
        output = args.output or SCRIPT_DIR / (
            f"phase484z_width30_row_holdout_background_i{args.fixture_index}_"
            f"b{args.background_count}_k{args.folds}_r{args.restarts}_"
            f"n{args.iterations}_cvr{cv_r}_cvn{cv_n}.json")
        output.write_text(json.dumps(result, indent=2) + "\n")
        print("pool_size", result["pool_size"], "true", result["true_child_count"])
        print("baseline best/worst true rank",
              result["baseline"]["best_true_rank"],
              result["baseline"]["worst_true_rank"],
              "background max", round(result["baseline"]["background_max"], 3))
        print("cv best/worst true rank",
              result["cv"]["best_true_rank"], result["cv"]["worst_true_rank"],
              "background max", round(result["cv"]["background_max"], 3))
    print("wall", round(result["wall_seconds"], 3))
    print("wrote", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
