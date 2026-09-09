#!/usr/bin/env python3
"""Blind width-30 joint solver: invariant shortlist plus GPU board screen.

Development only: this module never imports FAED and never uses holdout data.

Ported from phase484q_blind_joint_width19_solver.py for the complementary
30-column orientation whose planted-board ceiling was validated in Phase
484Y (doc/Brainstorms/2026-09-07 - Phase 484O Joint Board-Order Ceiling.md).
Unlike the width-19 solver, the escape pair is not blindly searched: it is
fixed to the frequency-established real pair `exact.PAIR` ({g,i}), matching
phase484y_width30_feasibility_probe.py's convention, since the pair is a
property of the raw a-i stream independent of the transposition orientation
used to describe column order.

Depths 1..8 reuse phase484y_width30_feasibility_probe.py's own invariant
GPU scorer and selection/expansion routines (already validated for width 30)
instead of phase484n_gpu_width19_beam_probe.py's width-19-flavored ones.

Depths 9..30 default to a *rolling board re-anneal* extension
(extend_seed_reanneal, backend="reanneal"): at every depth it re-anneals an
independent board per surviving candidate via gpu_multistart_screen (the
same coarse-anneal kernel used at depth 8), instead of freezing one board
from the depth-8 refine stage for the whole walk to depth 30. This is
484O's own anticipated fallback ("a population of estimated boards
alternated with the same GPU order step"). It replaced a frozen-board
design (extend_seed, backend="frozen", using
phase484y_width30_extend_board_server.cu) after dev testing on fixture 16
showed the frozen board's quadgram signal for the true continuation
collapses around depths 14-17 regardless of beam width (widening 4,096 ->
131,072 only delayed the loss by one depth) -- the width-19 pipeline's
9-19 walk is short enough for a single frozen board to survive, but
width-30's longer 9-30 walk is not. The frozen-board kernel and backend are
kept for comparison, not because either is known to be more expensive or
cheaper in general.

Path identity at depths 13..30 must use collision-free row keys.  The first
port reused a 5-bit-per-column uint64 key that is valid only through depth
12; overflow silently merged distinct longer paths.  The shared width-30
selector now rejects packed keys above depth 12 and switches to exact NumPy
row identity.  All extension conclusions predating that correction are
superseded by the collision-fixed traces and recovery artifacts.

Whichever extension backend is used, only the independent final full-stream
re-anneal (phase484q_full_board_server.cu, reused as-is -- it is already
geometry agnostic) needs the true absolute-alphabet slot convention, which
it gets from this module's own complete_token_slots() rather than from any
GPU board layout. See the Phase 484Y write-up for why mixing conventions
would be wrong: phase484y_width30_board_score_server.cu (the ceiling-map
oracle kernel) uses the corrected convention on purpose, because it scores
a fixed board built the true (absolute-alphabet) way; nothing in this
module should be pointed at that kernel.

A `board_accuracy` diagnostic against the true planted board (as
phase484q_blind_joint_width19_solver.screen_fixture computes) is
deliberately not reported here: the coarse/refine boards this pipeline
carries are in the internal canonical-slot convention, and comparing them
directly against ceiling.planted_board()'s absolute-alphabet convention
would silently be wrong whenever pair != {a,b}, which is always true here.
Recovery is judged by order/plaintext identity instead, which does not
depend on board labeling.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import functools
import hashlib
import itertools
import json
import struct
import subprocess
import time
from pathlib import Path

import numpy as np

import phase484a_raw_symbol_vic_solver as base
import phase484j_constructive_prefix_beam_probe as prefix
import phase484k_bidirectional_segment_assembly_probe as bidi
import phase484p_partial_board_recovery_probe as partial
import phase484q_blind_joint_width19_solver as solver19
import phase484y_width30_feasibility_probe as width30
from phase484n_hybrid_prefix_scorer import read_exact

SCRIPT_DIR = Path(__file__).resolve().parent
COARSE_BINARY = SCRIPT_DIR.parents[1] / "_work/phase484y/coarse_board_server"
EXTEND_BINARY = SCRIPT_DIR.parents[1] / "_work/phase484y/extend_board_server"
FULL_BINARY = SCRIPT_DIR.parents[1] / "_work/phase484q/full_board_server"
COARSE_MAGIC = b"P484YQ1\0"
EXTEND_MAGIC = b"P484YE1\0"

WIDTH, ROWS, DEPTH = width30.WIDTH, width30.ROWS, width30.STOP_DEPTH
SHORTLIST, FINAL_SHORTLIST_KEEP = width30.DEFAULT_KEEP, width30.DEFAULT_FINAL_KEEP
ITERATIONS, RESTARTS = 2000, 8
REFINE_KEEP, REFINE_RESTARTS, REFINE_ITERATIONS = 64, 4, 10000
EXTEND_SEEDS, EXTEND_BEAM, TERMINALS_PER_SEED = 8, 4096, 8
REANNEAL_RESTARTS, REANNEAL_ITERATIONS = 4, 10000
FINAL_RESTARTS, FINAL_ITERATIONS = 4, 10000
T0, T1, SEED = partial.T0, partial.T1, partial.SEED

fragment_seed = solver19.fragment_seed
initial_board = solver19.initial_board
gpu_full_screen = solver19.gpu_full_screen
gpu_full_multistart = solver19.gpu_full_multistart


def records_reanneal_budget(backend):
    return backend in ("reanneal", "pooled_reanneal")


def shortlist_capacity(depth, keep, final_keep=None):
    return final_keep if final_keep is not None and depth == DEPTH else keep


def build_depth8_shortlist(fixture, keep=SHORTLIST, final_keep=FINAL_SHORTLIST_KEEP, models=None,
                           binary=width30.DEFAULT_BINARY, start_depth=width30.START_DEPTH):
    if models is None:
        models = width30.train_models()
    blocks = prefix.blocks_from_observed(fixture)
    pair = tuple(fixture["pair"])
    paths = width30.initial_paths(start_depth)
    with width30.GpuWidth30Scorer(binary, blocks, pair, models[start_depth]) as scorer:
        scores = scorer.score(paths)
    for depth in range(start_depth, DEPTH + 1):
        paths, scores, _ = width30.select_diverse(paths, scores, shortlist_capacity(depth, keep, final_keep))
        if depth == DEPTH:
            break
        paths = width30.expand_bidirectional(paths)
        with width30.GpuWidth30Scorer(binary, blocks, pair, models[depth + 1]) as scorer:
            scores = scorer.score(paths)
    return paths, scores


def gpu_coarse_screen(binary, blocks, pair, quad, paths, iterations=ITERATIONS, seed=SEED, t0=T0, t1=T1):
    paths = np.asarray(paths, dtype=np.uint8)
    if paths.ndim != 2 or not 4 <= paths.shape[1] <= WIDTH:
        raise ValueError("paths must be an N x depth array")
    if len(paths) == 0 or np.any(paths >= WIDTH):
        raise ValueError("paths must be nonempty and within width 30")
    process = subprocess.Popen([str(binary)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    payload = b"".join([
        COARSE_MAGIC, width30.canonical_blocks(blocks, pair),
        np.asarray(quad, dtype="<f8").tobytes(),
        struct.pack("<IIIQdd", len(paths), paths.shape[1], iterations, seed, t0, t1),
        np.ascontiguousarray(paths).tobytes(),
    ])
    stdout, stderr = process.communicate(payload)
    if process.returncode:
        raise RuntimeError(f"coarse GPU server exited {process.returncode}: {stderr.decode('utf-8', 'replace')}")
    sb, wb = len(paths) * 8, len(paths) * 4
    expected = sb + wb + len(paths) * 25
    if len(stdout) != expected:
        raise RuntimeError(f"coarse GPU server returned {len(stdout)} bytes, expected {expected}")
    scores = np.frombuffer(stdout[:sb], dtype="<f8").copy()
    windows = np.frombuffer(stdout[sb:sb + wb], dtype="<i4").copy()
    boards = np.frombuffer(stdout[sb + wb:], dtype=np.uint8).copy().reshape(len(paths), 25)
    return scores, windows, boards


def gpu_multistart_screen(binary, blocks, pair, quad, paths, restarts=RESTARTS, iterations=ITERATIONS):
    best_scores = np.full(len(paths), -np.inf)
    best_windows = None
    best_boards = None
    best_restarts = np.zeros(len(paths), dtype=np.int64)
    for restart in range(restarts):
        restart_seed = base.derive_seed(SEED, restart)
        scores, windows, boards = gpu_coarse_screen(binary, blocks, pair, quad, paths, iterations, seed=restart_seed)
        if best_windows is None:
            best_windows = windows.copy()
            best_boards = boards.copy()
        elif not np.array_equal(windows, best_windows):
            raise AssertionError("window counts changed across restarts")
        improved = scores > best_scores
        best_scores[improved] = scores[improved]
        best_boards[improved] = boards[improved]
        best_restarts[improved] = restart
    return best_scores, best_windows, best_boards, best_restarts


def canonical_token_rows(blocks, pair, path):
    """Reproduce phase484y_width30_coarse_board_server.cu's own token-index
    convention (7+symbol*9+next, using canonical_blocks's pair-relabeled
    symbol values with no escape-pair correction) directly in Python.  This
    is deliberately NOT partial.token_rows/base.slot_codes, which use the
    true absolute-alphabet convention: the two only coincide for pair
    {a,b}, and this pipeline always uses {g,i} (see the module docstring)."""
    remaining = [symbol for symbol in base.NINE_SYMBOLS if symbol not in pair]
    mapping = {symbol: index for index, symbol in enumerate([pair[0], pair[1], *remaining])}
    rows = []
    for row in range(len(blocks[0])):
        raw = [mapping[blocks[column][row]] for column in path]
        tokens = []
        j = 0
        while j < len(raw):
            symbol = raw[j]
            if symbol < 2:
                if j + 1 == len(raw):
                    break
                tokens.append(7 + symbol * 9 + raw[j + 1])
                j += 2
            else:
                tokens.append(symbol - 2)
                j += 1
        rows.append(np.asarray(tokens, dtype=np.int64))
    return rows


def cpu_recompute(blocks, pair, quad, path, board):
    rows = canonical_token_rows(blocks, pair, path)
    windows = sum(max(0, len(row) - 3) for row in rows)
    board = np.asarray(board, dtype=np.int64)
    total = sum(base.score_indices(board[row], quad) for row in rows if len(row) >= 4)
    return (total / windows if windows else -1e9), windows


def complete_token_slots(blocks, pair, order, strict=True):
    raw = "".join(blocks[column][row] for row in range(ROWS) for column in order)
    segmented = base.segment_raw(raw, pair)
    if segmented is None:
        if strict:
            raise ValueError("complete order did not segment")
        return None
    code_to_slot = {code: i for i, code in enumerate(base.slot_codes(pair))}
    return np.asarray([code_to_slot[code] for code in segmented], dtype=np.int64)


def resolve_terminals(blocks, pair, quad, terminals, restarts=FINAL_RESTARTS, iterations=FINAL_ITERATIONS,
                      full_binary=FULL_BINARY):
    valid, skipped = [], []
    for record in terminals:
        rows = complete_token_slots(blocks, pair, record["order"], strict=False)
        if rows is None:
            skipped.append(record)
        else:
            valid.append((record, rows))
    if not valid:
        return [], skipped
    terminals_valid = [r for r, _ in valid]
    token_rows_list = [rows for _, rows in valid]
    scores, boards, best_restarts = gpu_full_multistart(full_binary, token_rows_list, quad, restarts, iterations)
    order = np.lexsort((np.arange(len(scores)), -scores))
    ranked = []
    for rank, i in enumerate(order, 1):
        slots = token_rows_list[i]
        plaintext = "".join(base.LETTER_ALPHABET[value] for value in boards[i][slots])
        ranked.append({
            "final_rank": rank, "extension_rank": terminals_valid[i]["extension_rank"],
            "normalized_score": float(scores[i]), "decoded_length": len(plaintext),
            "plaintext": plaintext, "order": terminals_valid[i]["order"],
            "board": boards[i].tolist(), "best_restart": int(best_restarts[i]),
            "quadgram_windows": len(slots) - 3,
        })
    return ranked, skipped


class BoardScorer:
    def __init__(self, binary, blocks, pair, board, quad):
        self.process = subprocess.Popen(
            [str(binary)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.process.stdin.write(EXTEND_MAGIC)
        self.process.stdin.write(width30.canonical_blocks(blocks, pair))
        self.process.stdin.write(bytes(board))
        self.process.stdin.write(np.asarray(quad, dtype="<f8").tobytes())
        self.process.stdin.flush()

    def score(self, paths):
        paths = np.ascontiguousarray(paths, dtype=np.uint8)
        self.process.stdin.write(struct.pack("<II", len(paths), paths.shape[1]))
        self.process.stdin.write(paths.tobytes())
        self.process.stdin.flush()
        data = read_exact(self.process.stdout, len(paths) * 8)
        if len(data) != len(paths) * 8:
            raise RuntimeError(self.process.stderr.read().decode("utf-8", "replace"))
        return np.frombuffer(data, dtype="<f8").copy()

    def close(self):
        if self.process.poll() is None:
            self.process.stdin.write(struct.pack("<II", 0, 0))
            self.process.stdin.flush()
            self.process.stdin.close()
            if self.process.wait(timeout=10):
                raise RuntimeError(self.process.stderr.read().decode("utf-8", "replace"))

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def extend_seed(blocks, pair, quad, record, board_binary=EXTEND_BINARY, beam_width=EXTEND_BEAM):
    paths = np.asarray([record["path"]], dtype=np.uint8)
    scores = np.asarray([record["normalized_score"]], dtype=np.float64)
    diagnostics = []
    with BoardScorer(board_binary, blocks, pair, bytes(record["board"]), quad) as scorer:
        for depth in range(DEPTH + 1, WIDTH + 1):
            paths = width30.expand_bidirectional(paths)
            scores = scorer.score(paths)
            paths, scores, unique_count = width30.select_diverse(paths, scores, beam_width)
            diagnostics.append({"depth": depth, "generated": int(unique_count), "retained": len(paths)})
    beam = sorted(
        ((float(score), tuple(int(value) for value in path)) for path, score in zip(paths, scores)),
        key=lambda item: -item[0])
    return beam, diagnostics


def extend_seed_reanneal(blocks, pair, quad, record, coarse_binary=COARSE_BINARY, beam_width=EXTEND_BEAM,
                         restarts=REANNEAL_RESTARTS, iterations=REANNEAL_ITERATIONS):
    """Extension that re-anneals a fresh board per surviving candidate at
    every depth via gpu_multistart_screen, instead of freezing one board
    from the depth-8 refine stage.  See the module docstring for why."""
    paths = np.asarray([record["path"]], dtype=np.uint8)
    scores = np.asarray([record["normalized_score"]], dtype=np.float64)
    diagnostics = []
    for depth in range(DEPTH + 1, WIDTH + 1):
        paths = width30.expand_bidirectional(paths)
        path_tuples = [tuple(int(value) for value in path) for path in paths]
        scores, windows, boards, best_restarts = gpu_multistart_screen(
            coarse_binary, blocks, pair, quad, path_tuples, restarts=restarts, iterations=iterations)
        paths, scores, unique_count = width30.select_diverse(paths, scores, beam_width)
        diagnostics.append({"depth": depth, "generated": int(unique_count), "retained": len(paths)})
    beam = sorted(
        ((float(score), tuple(int(value) for value in path)) for path, score in zip(paths, scores)),
        key=lambda item: -item[0])
    return beam, diagnostics


def extend_pooled_reanneal(blocks, pair, quad, refined,
                           seed_count=256, beam_width=EXTEND_BEAM,
                           terminals_per_seed=TERMINALS_PER_SEED,
                           coarse_binary=COARSE_BINARY,
                           restarts=REANNEAL_RESTARTS,
                           iterations=REANNEAL_ITERATIONS):
    """Merge many refined seeds into one bounded rolling-anneal beam."""
    selected = refined[:seed_count]
    if not selected:
        return [], []
    paths = np.asarray([record["path"] for record in selected], dtype=np.uint8)
    scores = np.asarray([record["normalized_score"] for record in selected],
                        dtype=np.float64)
    diagnostics = []
    for depth in range(DEPTH + 1, WIDTH + 1):
        paths = width30.expand_bidirectional(paths)
        path_tuples = [tuple(int(value) for value in path) for path in paths]
        scores, _, _, _ = gpu_multistart_screen(
            coarse_binary, blocks, pair, quad, path_tuples,
            restarts=restarts, iterations=iterations)
        paths, scores, unique_count = width30.select_diverse(
            paths, scores, beam_width)
        diagnostics.append({"depth": depth, "generated": int(unique_count),
                            "retained": len(paths)})
    beam = sorted(
        ((float(score), tuple(int(value) for value in path))
         for path, score in zip(paths, scores)),
        key=lambda item: (-item[0], item[1]))
    terminals = []
    for rank, (score, path) in enumerate(beam[:terminals_per_seed], 1):
        terminals.append({
            "extension_rank": rank, "extension_score": score,
            "order": list(path), "source_refined_rank": None,
            "source_shortlist_index": None,
            "pooled_source_ranks": [record["rank"] for record in selected],
        })
    seed_diagnostics = [{
        "backend": "pooled_reanneal",
        "pooled_seed_count": len(selected),
        "pooled_source_ranks": [record["rank"] for record in selected],
        "depths": diagnostics,
    }]
    return terminals, seed_diagnostics


def _extend_chunk(args):
    extend_fn, blocks, pair, quad, records, binary, beam_width = args
    return [(record["rank"], *extend_fn(blocks, pair, quad, record, binary, beam_width))
            for record in records]


def extend_population(extend_fn, blocks, pair, quad, refined, binary, seed_count=EXTEND_SEEDS,
                      beam_width=EXTEND_BEAM, terminals_per_seed=TERMINALS_PER_SEED, workers=1):
    selected = refined[:seed_count]
    if workers < 1:
        raise ValueError("extension workers must be positive")
    if workers == 1 or len(selected) < 2:
        extended = _extend_chunk((extend_fn, blocks, pair, quad, selected, binary, beam_width))
    else:
        worker_count = min(workers, len(selected))
        chunks = [selected[i::worker_count] for i in range(worker_count)]
        tasks = [(extend_fn, blocks, pair, quad, chunk, binary, beam_width) for chunk in chunks]
        with concurrent.futures.ProcessPoolExecutor(max_workers=worker_count) as pool:
            extended = [item for chunk in pool.map(_extend_chunk, tasks) for item in chunk]
        extended.sort(key=lambda item: item[0])
    terminal = {}
    seed_diagnostics = []
    records_by_rank = {record["rank"]: record for record in selected}
    for rank, beam, diagnostics in extended:
        record = records_by_rank[rank]
        seed_diagnostics.append({
            "refined_rank": record["rank"], "shortlist_index": record["shortlist_index"], "depths": diagnostics})
        for score, path in beam[:terminals_per_seed]:
            old = terminal.get(path)
            candidate = {
                "extension_score": float(score), "order": list(path),
                "source_refined_rank": record["rank"], "source_shortlist_index": record["shortlist_index"],
            }
            if old is None or score > old["extension_score"]:
                terminal[path] = candidate
    ranked = sorted(terminal.values(), key=lambda r: (-r["extension_score"], r["order"]))
    for rank, record in enumerate(ranked, 1):
        record["extension_rank"] = rank
    return ranked, seed_diagnostics


def run_extension_backend(blocks, pair, quad, refined, seed_count=EXTEND_SEEDS, beam_width=EXTEND_BEAM,
                          terminals_per_seed=TERMINALS_PER_SEED, workers=1, backend="reanneal",
                          board_binary=EXTEND_BINARY, coarse_binary=COARSE_BINARY,
                          reanneal_restarts=REANNEAL_RESTARTS, reanneal_iterations=REANNEAL_ITERATIONS):
    if backend == "pooled_reanneal":
        return extend_pooled_reanneal(
            blocks, pair, quad, refined, seed_count=seed_count,
            beam_width=beam_width, terminals_per_seed=terminals_per_seed,
            coarse_binary=coarse_binary, restarts=reanneal_restarts,
            iterations=reanneal_iterations)
    if backend == "frozen":
        extend_fn, binary = extend_seed, board_binary
    elif backend == "reanneal":
        extend_fn = functools.partial(
            extend_seed_reanneal, restarts=reanneal_restarts, iterations=reanneal_iterations)
        binary = coarse_binary
    else:
        raise ValueError(f"unknown extension backend: {backend}")
    return extend_population(extend_fn, blocks, pair, quad, refined, binary, seed_count=seed_count,
                             beam_width=beam_width, terminals_per_seed=terminals_per_seed, workers=workers)


def screen_observed(observed, keep=SHORTLIST, iterations=ITERATIONS, restarts=RESTARTS,
                    refine_keep=REFINE_KEEP, refine_restarts=REFINE_RESTARTS,
                    refine_iterations=REFINE_ITERATIONS, coarse_binary=COARSE_BINARY,
                    extend_seed_count=EXTEND_SEEDS, extend_beam=EXTEND_BEAM,
                    terminals_per_seed=TERMINALS_PER_SEED, final_restarts=FINAL_RESTARTS,
                    final_iterations=FINAL_ITERATIONS, extend_workers=1, extend_binary=EXTEND_BINARY,
                    extension_backend="reanneal", reanneal_restarts=REANNEAL_RESTARTS,
                    reanneal_iterations=REANNEAL_ITERATIONS,
                    full_binary=FULL_BINARY, shortlist_models=None,
                    shortlist_final_keep=FINAL_SHORTLIST_KEEP, pair=None):
    if len(observed) != base.RAW_LENGTH:
        raise ValueError("observed width-30 stream must contain 570 symbols")
    if set(observed) - set(base.NINE_SYMBOLS):
        raise ValueError("observed stream contains symbols outside a-i")
    if pair is None:
        pair = width30.exact.PAIR
    pair = tuple(pair)
    fixture = {"observed": observed, "width": WIDTH, "pair": list(pair)}
    blocks = prefix.blocks_from_observed(fixture)
    quad, _ = base.load_language_model()
    began = time.monotonic()
    paths, _ = build_depth8_shortlist(fixture, keep, final_keep=shortlist_final_keep, models=shortlist_models)
    paths_list = [tuple(int(value) for value in path) for path in paths]
    shortlist_seconds = time.monotonic() - began
    began = time.monotonic()
    scores, windows, boards, best_restarts = gpu_multistart_screen(
        coarse_binary, blocks, pair, quad, paths_list, restarts, iterations)
    screen_seconds = time.monotonic() - began
    order = np.lexsort((np.arange(len(scores)), -scores))
    refine_indices = order[:min(refine_keep, len(order))]
    refine_paths = [paths_list[i] for i in refine_indices]
    began = time.monotonic()
    rs, rw, rb, rr = gpu_multistart_screen(
        coarse_binary, blocks, pair, quad, refine_paths, refine_restarts, refine_iterations)
    refine_seconds = time.monotonic() - began
    refine_order = np.lexsort((np.arange(len(rs)), -rs))
    ranks = np.empty(len(scores), dtype=np.int64)
    ranks[order] = np.arange(1, len(scores) + 1)
    refined = []
    for rank, j in enumerate(refine_order, 1):
        original = int(refine_indices[j])
        refined.append({
            "rank": rank, "coarse_rank": int(ranks[original]), "shortlist_index": original,
            "normalized_score": float(rs[j]), "best_restart": int(rr[j]),
            "path": list(paths_list[original]), "board": rb[j].tolist(), "quadgram_windows": int(rw[j]),
        })
    began = time.monotonic()
    terminals, extension_diagnostics = run_extension_backend(
        blocks, pair, quad, refined, seed_count=extend_seed_count, beam_width=extend_beam,
        terminals_per_seed=terminals_per_seed, workers=extend_workers, backend=extension_backend,
        board_binary=extend_binary, coarse_binary=coarse_binary, reanneal_restarts=reanneal_restarts,
        reanneal_iterations=reanneal_iterations)
    extension_seconds = time.monotonic() - began
    began = time.monotonic()
    final, skipped = resolve_terminals(
        blocks, pair, quad, terminals, restarts=final_restarts, iterations=final_iterations,
        full_binary=full_binary)
    final_seconds = time.monotonic() - began
    return {
        "phase": "484Y", "status": "exploratory_real_cell_complete", "faed_scored": True,
        "holdout_consumed": False, "pair": list(pair),
        "shortlist_size": len(paths_list), "restarts_per_fragment": restarts,
        "iterations_per_restart": iterations, "refine_keep": len(refine_paths),
        "shortlist_final_keep": shortlist_final_keep,
        "refine_restarts": refine_restarts, "refine_iterations": refine_iterations,
        "extension_seed_count": min(extend_seed_count, len(refined)), "extension_workers": extend_workers,
        "extension_beam": extend_beam, "terminals_per_seed": terminals_per_seed,
        "extension_backend": extension_backend,
        "reanneal_restarts": reanneal_restarts if records_reanneal_budget(extension_backend) else None,
        "reanneal_iterations": reanneal_iterations if records_reanneal_budget(extension_backend) else None,
        "final_restarts": final_restarts, "final_iterations": final_iterations,
        "shortlist_seconds": shortlist_seconds, "gpu_screen_seconds": screen_seconds,
        "gpu_refine_seconds": refine_seconds, "extension_seconds": extension_seconds,
        "final_seconds": final_seconds,
        "best_refined_normalized_score": float(rs[refine_order[0]]) if len(refine_order) else None,
        "top1_final_normalized_score": final[0]["normalized_score"] if final else None,
        "terminals_total": len(terminals), "terminals_valid": len(terminals) - len(skipped),
        "terminals_skipped_invalid_segmentation": len(skipped), "final_candidates": final,
        "refined_population": refined, "terminal_orders": terminals, "skipped_terminals": skipped,
        "extension_diagnostics": extension_diagnostics,
    }


def screen_fixture(fixture_index=13, split="dev", keep=SHORTLIST, iterations=ITERATIONS, restarts=RESTARTS,
                   refine_keep=REFINE_KEEP, refine_restarts=REFINE_RESTARTS,
                   refine_iterations=REFINE_ITERATIONS, coarse_binary=COARSE_BINARY,
                   extend_seed_count=EXTEND_SEEDS, extend_beam=EXTEND_BEAM,
                   terminals_per_seed=TERMINALS_PER_SEED, final_restarts=FINAL_RESTARTS,
                   final_iterations=FINAL_ITERATIONS, extend_workers=1, extend_binary=EXTEND_BINARY,
                   extension_backend="reanneal", reanneal_restarts=REANNEAL_RESTARTS,
                   reanneal_iterations=REANNEAL_ITERATIONS,
                   full_binary=FULL_BINARY, shortlist_models=None,
                   shortlist_final_keep=FINAL_SHORTLIST_KEEP):
    fixture = width30.width30_fixture(fixture_index, split)
    pair = tuple(fixture["pair"])
    blocks = prefix.blocks_from_observed(fixture)
    truth = prefix.order_to_sequence(fixture["order"])
    truth_windows = bidi.true_windows(truth, DEPTH)
    quad, _ = base.load_language_model()
    began = time.monotonic()
    paths, _ = build_depth8_shortlist(fixture, keep, final_keep=shortlist_final_keep, models=shortlist_models)
    paths_list = [tuple(int(value) for value in path) for path in paths]
    shortlist_seconds = time.monotonic() - began
    truth_indices = [i for i, path in enumerate(paths_list) if path in truth_windows]
    began = time.monotonic()
    scores, windows, boards, best_restarts = gpu_multistart_screen(
        coarse_binary, blocks, pair, quad, paths_list, restarts, iterations)
    screen_seconds = time.monotonic() - began
    order = np.lexsort((np.arange(len(scores)), -scores))
    ranks = np.empty(len(scores), dtype=np.int64)
    ranks[order] = np.arange(1, len(scores) + 1)
    true_records = [{
        "shortlist_index": i, "coarse_rank": int(ranks[i]), "normalized_score": float(scores[i]),
        "best_restart": int(best_restarts[i]), "path": list(paths_list[i]),
    } for i in truth_indices]
    refine_indices = order[:min(refine_keep, len(order))]
    refine_paths = [paths_list[i] for i in refine_indices]
    began = time.monotonic()
    rs, rw, rb, rr = gpu_multistart_screen(
        coarse_binary, blocks, pair, quad, refine_paths, refine_restarts, refine_iterations)
    refine_seconds = time.monotonic() - began
    refine_order = np.lexsort((np.arange(len(rs)), -rs))
    refined = []
    for rank, j in enumerate(refine_order, 1):
        original = int(refine_indices[j])
        refined.append({
            "rank": rank, "coarse_rank": int(ranks[original]), "shortlist_index": original,
            "is_true_segment": paths_list[original] in truth_windows,
            "normalized_score": float(rs[j]), "best_restart": int(rr[j]),
            "path": list(paths_list[original]), "board": rb[j].tolist(), "quadgram_windows": int(rw[j]),
        })
    began = time.monotonic()
    terminals, extension_diagnostics = run_extension_backend(
        blocks, pair, quad, refined, seed_count=extend_seed_count, beam_width=extend_beam,
        terminals_per_seed=terminals_per_seed, workers=extend_workers, backend=extension_backend,
        board_binary=extend_binary, coarse_binary=coarse_binary, reanneal_restarts=reanneal_restarts,
        reanneal_iterations=reanneal_iterations)
    extension_seconds = time.monotonic() - began
    truth_tuple = tuple(truth)
    truth_terminal = next((r for r in terminals if tuple(r["order"]) == truth_tuple), None)
    began = time.monotonic()
    final, skipped_terminals = resolve_terminals(
        blocks, pair, quad, terminals, restarts=final_restarts, iterations=final_iterations,
        full_binary=full_binary)
    final_seconds = time.monotonic() - began
    exact_final = next((r for r in final if tuple(r["order"]) == truth_tuple), None)
    truth_plaintext = fixture["plaintext"]
    for record in final:
        record["is_exact_order"] = tuple(record["order"]) == truth_tuple
        record["plaintext_accuracy"] = sum(
            a == b for a, b in zip(record["plaintext"], truth_plaintext)) / max(
            len(record["plaintext"]), len(truth_plaintext))
    return {
        "phase": "484Y", "status": "development_blind_joint_width30_complete_not_frozen",
        "faed_scored": False, "holdout_consumed": split == "holdout", "fixture_index": fixture_index,
        "split": split, "pair": list(pair),
        "shortlist_size": len(paths_list), "restarts_per_fragment": restarts,
        "iterations_per_restart": iterations, "refine_keep": len(refine_paths),
        "shortlist_final_keep": shortlist_final_keep,
        "refine_restarts": refine_restarts, "refine_iterations": refine_iterations,
        "extension_seed_count": min(extend_seed_count, len(refined)), "extension_workers": extend_workers,
        "extension_beam": extend_beam, "terminals_per_seed": terminals_per_seed,
        "extension_backend": extension_backend,
        "reanneal_restarts": reanneal_restarts if records_reanneal_budget(extension_backend) else None,
        "reanneal_iterations": reanneal_iterations if records_reanneal_budget(extension_backend) else None,
        "final_restarts": final_restarts, "final_iterations": final_iterations,
        "shortlist_seconds": shortlist_seconds, "gpu_screen_seconds": screen_seconds,
        "gpu_refine_seconds": refine_seconds, "extension_seconds": extension_seconds,
        "final_seconds": final_seconds,
        "best_refined_normalized_score": float(rs[refine_order[0]]) if len(refine_order) else None,
        "top1_final_normalized_score": final[0]["normalized_score"] if final else None,
        "true_segments_retained": len(true_records),
        "best_true_coarse_rank": min((r["coarse_rank"] for r in true_records), default=None),
        "best_true_refined_rank": min(
            (r["rank"] for r in refined if r["is_true_segment"]), default=None),
        "exact_order_in_terminals": truth_terminal is not None,
        "exact_order_extension_rank": truth_terminal["extension_rank"] if truth_terminal else None,
        "exact_order_final_rank": exact_final["final_rank"] if exact_final else None,
        "top1_exact_order": bool(final and final[0]["is_exact_order"]),
        "top1_plaintext_accuracy": final[0]["plaintext_accuracy"] if final else None,
        "terminals_total": len(terminals), "terminals_valid": len(terminals) - len(skipped_terminals),
        "terminals_skipped_invalid_segmentation": len(skipped_terminals),
        "true_records": true_records, "refined_population": refined, "terminal_orders": terminals,
        "final_candidates": final, "skipped_terminals": skipped_terminals,
        "extension_diagnostics": extension_diagnostics,
    }


def load_true_refined_seed(path):
    source = json.loads(Path(path).read_text())
    if source.get("fixture_index") is None:
        raise ValueError("trace source has no fixture_index")
    true_records = [record for record in source.get("refined_population", [])
                    if record.get("is_true_segment")]
    if not true_records:
        raise ValueError("trace source has no true refined segment")
    true_records.sort(key=lambda record: record["rank"])
    return source, true_records[0]


def trace_true_extension(source_path, restarts=REANNEAL_RESTARTS,
                         iterations=REANNEAL_ITERATIONS,
                         beam_width=EXTEND_BEAM,
                         coarse_binary=COARSE_BINARY):
    """Replay one known-true dev seed and persist pre/post-selection survival."""
    source_path = Path(source_path)
    source, record = load_true_refined_seed(source_path)
    fixture_index = int(source["fixture_index"])
    fixture = width30.width30_fixture(fixture_index, "dev")
    pair = tuple(fixture["pair"])
    blocks = prefix.blocks_from_observed(fixture)
    truth = prefix.order_to_sequence(fixture["order"])
    if tuple(record["path"]) not in bidi.true_windows(truth, DEPTH):
        raise ValueError("selected source record is not a true depth-8 segment")
    quad, _ = base.load_language_model()
    paths = np.asarray([record["path"]], dtype=np.uint8)
    diagnostics = []
    began = time.monotonic()
    for depth in range(DEPTH + 1, WIDTH + 1):
        paths = width30.expand_bidirectional(paths)
        path_tuples = [tuple(int(value) for value in path) for path in paths]
        scores, _, _, _ = gpu_multistart_screen(
            coarse_binary, blocks, pair, quad, path_tuples,
            restarts=restarts, iterations=iterations)
        pre_count, pre_rank = width30.generated_true_metrics(
            paths, scores, truth, depth)
        paths, scores, unique_count = width30.select_diverse(
            paths, scores, beam_width)
        post_ranks = width30.true_ranks(paths, scores, truth, depth)
        diagnostics.append({
            "depth": depth,
            "generated_unique": int(unique_count),
            "true_pre": int(pre_count),
            "best_true_pre_rank": pre_rank,
            "retained": len(paths),
            "true_post": len(post_ranks),
            "best_true_post_rank": min(post_ranks) if post_ranks else None,
        })
        if not post_ranks:
            break
    source_sha256 = hashlib.sha256(source_path.read_bytes()).hexdigest()
    return {
        "phase": "484Y",
        "status": "development_true_extension_trace_not_frozen",
        "faed_scored": False,
        "holdout_consumed": False,
        "fixture_index": fixture_index,
        "source_artifact": str(source_path),
        "source_artifact_sha256": source_sha256,
        "source_refined_rank": record["rank"],
        "source_path": record["path"],
        "extension_backend": "reanneal",
        "reanneal_restarts": restarts,
        "reanneal_iterations": iterations,
        "extension_beam": beam_width,
        "survived_to_depth": diagnostics[-1]["depth"] if diagnostics else DEPTH,
        "completed_depth30": bool(diagnostics and diagnostics[-1]["depth"] == WIDTH
                                  and diagnostics[-1]["true_post"]),
        "depth_diagnostics": diagnostics,
        "wall_seconds": time.monotonic() - began,
    }


def self_test(binary=COARSE_BINARY):
    fixture = width30.width30_fixture(13)
    pair = tuple(fixture["pair"])
    blocks = prefix.blocks_from_observed(fixture)
    quad, _ = base.load_language_model()
    paths = np.asarray(
        list(itertools.islice(itertools.permutations(range(WIDTH), DEPTH), 16)), dtype=np.uint8)
    _, _, boards0 = gpu_coarse_screen(binary, blocks, pair, quad, paths, iterations=0)
    for i, (path, b) in enumerate(zip(paths, boards0)):
        if not np.array_equal(b, initial_board(SEED, path)):
            raise AssertionError(f"initial board mismatch at {i}")
    reversed_paths = paths[::-1].copy()
    _, _, reversed_boards = gpu_coarse_screen(binary, blocks, pair, quad, reversed_paths, iterations=0)
    board_by_path = {tuple(path): board for path, board in zip(paths, boards0)}
    for path, board in zip(reversed_paths, reversed_boards):
        if not np.array_equal(board, board_by_path[tuple(path)]):
            raise AssertionError("fragment seed changed after reordering")
    scores, windows, boards = gpu_coarse_screen(binary, blocks, pair, quad, paths, iterations=37)
    errors = []
    for i, (path, board) in enumerate(zip(paths, boards)):
        expected, ew = cpu_recompute(blocks, pair, quad, path, board)
        errors.append(abs(expected - scores[i]))
        if ew != windows[i]:
            raise AssertionError((ew, windows[i]))
        if sorted(board.tolist()) != list(range(25)):
            raise AssertionError("board is not a permutation")
    truth = prefix.order_to_sequence(fixture["order"])
    slots = complete_token_slots(blocks, pair, truth)
    fs, fb = gpu_full_screen(FULL_BINARY, [slots], quad, 37, SEED)
    expected = base.score_indices(fb[0][slots].astype(np.int64), quad) / max(1, len(slots) - 3)
    errors.append(abs(expected - fs[0]))
    if errors[-1] > 1e-10:
        raise AssertionError(f"full-stream score mismatch: {errors[-1]}")
    return {
        "paths": len(paths), "initial_rng_parity": True, "path_reordering_invariant": True,
        "score_recomputation_max_abs_error": max(errors),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--trace-source", type=Path)
    parser.add_argument("--fixture-index", type=int, default=13)
    parser.add_argument("--split", choices=("dev", "holdout"), default="dev")
    parser.add_argument("--keep", type=int, default=SHORTLIST)
    parser.add_argument("--shortlist-final-keep", type=int, default=FINAL_SHORTLIST_KEEP)
    parser.add_argument("--iterations", type=int, default=ITERATIONS)
    parser.add_argument("--restarts", type=int, default=RESTARTS)
    parser.add_argument("--refine-keep", type=int, default=REFINE_KEEP)
    parser.add_argument("--refine-restarts", type=int, default=REFINE_RESTARTS)
    parser.add_argument("--refine-iterations", type=int, default=REFINE_ITERATIONS)
    parser.add_argument("--extend-seeds", type=int, default=EXTEND_SEEDS)
    parser.add_argument("--extend-workers", type=int, default=1)
    parser.add_argument("--extend-beam", type=int, default=EXTEND_BEAM)
    parser.add_argument("--extension-backend",
                        choices=("reanneal", "pooled_reanneal", "frozen"),
                        default="reanneal")
    parser.add_argument("--reanneal-restarts", type=int, default=REANNEAL_RESTARTS)
    parser.add_argument("--reanneal-iterations", type=int, default=REANNEAL_ITERATIONS)
    parser.add_argument("--terminals-per-seed", type=int, default=TERMINALS_PER_SEED)
    parser.add_argument("--final-restarts", type=int, default=FINAL_RESTARTS)
    parser.add_argument("--final-iterations", type=int, default=FINAL_ITERATIONS)
    parser.add_argument("--coarse-binary", type=Path, default=COARSE_BINARY)
    parser.add_argument("--extend-binary", type=Path, default=EXTEND_BINARY)
    parser.add_argument("--full-binary", type=Path, default=FULL_BINARY)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(args.coarse_binary), indent=2))
        return 0
    if args.trace_source:
        if args.split == "holdout":
            parser.error("holdout fixtures are prohibited before a frozen development gate")
        result = trace_true_extension(
            args.trace_source, args.reanneal_restarts,
            args.reanneal_iterations, args.extend_beam, args.coarse_binary)
        output = args.output or SCRIPT_DIR / (
            f"phase484y_width30_trace_i{result['fixture_index']}_"
            f"reanneal_rr{args.reanneal_restarts}_ri{args.reanneal_iterations}_"
            f"b{args.extend_beam}.json")
        output.write_text(json.dumps(result, indent=2) + "\n")
        print("survived to", result["survived_to_depth"],
              "completed", result["completed_depth30"],
              "wall", round(result["wall_seconds"], 3))
        print("wrote", output)
        return 0
    if not args.run:
        parser.error("use --self-test or --run")
    if args.split == "holdout":
        parser.error("holdout fixtures are prohibited before a frozen development gate")
    result = screen_fixture(
        fixture_index=args.fixture_index, split=args.split, keep=args.keep,
        iterations=args.iterations, restarts=args.restarts, refine_keep=args.refine_keep,
        refine_restarts=args.refine_restarts, refine_iterations=args.refine_iterations,
        coarse_binary=args.coarse_binary, extend_seed_count=args.extend_seeds,
        extend_beam=args.extend_beam, extension_backend=args.extension_backend,
        reanneal_restarts=args.reanneal_restarts, reanneal_iterations=args.reanneal_iterations,
        terminals_per_seed=args.terminals_per_seed,
        final_restarts=args.final_restarts, final_iterations=args.final_iterations,
        extend_workers=args.extend_workers, extend_binary=args.extend_binary,
        full_binary=args.full_binary, shortlist_final_keep=args.shortlist_final_keep)
    output = args.output or SCRIPT_DIR / (
        f"phase484y_width30_blind_{args.split}_i{args.fixture_index}_k{args.keep}_"
        f"f{args.shortlist_final_keep}_r{args.restarts}_n{args.iterations}_"
        f"e{args.extension_backend}_rr{args.reanneal_restarts}_"
        f"ri{args.reanneal_iterations}.json")
    output.write_text(json.dumps(result, indent=2) + "\n")
    print("true", result["true_segments_retained"], "coarse rank", result["best_true_coarse_rank"],
          "refined rank", result["best_true_refined_rank"], "exact final rank",
          result["exact_order_final_rank"], "top1 exact", result["top1_exact_order"],
          "gpu seconds", round(result["gpu_screen_seconds"] + result["gpu_refine_seconds"], 3))
    print("wrote", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
