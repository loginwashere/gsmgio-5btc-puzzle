#!/usr/bin/env python3
"""Isolated persistent-CUDA extension client for Phase 484W development."""
from __future__ import annotations

import concurrent.futures
import struct
import subprocess
from pathlib import Path

import numpy as np

import phase484q_blind_joint_width19_solver as solver
from phase484n_hybrid_prefix_scorer import canonical_blocks, read_exact

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_BINARY = SCRIPT_DIR.parents[1] / "_work/phase484w/persistent_board_server"


def validate_board(board):
    values = bytes(board)
    if len(values) != 25 or sorted(values) != list(range(25)):
        raise ValueError("board must be a permutation of 0..24")
    return values


def canonical_paths(paths):
    values = np.asarray(paths, dtype=np.uint8)
    if values.ndim != 2 or not 4 <= values.shape[1] <= solver.WIDTH:
        raise ValueError("paths must be an N x depth array, depth 4..19")
    if len(values) == 0 or np.any(values >= solver.WIDTH):
        raise ValueError("paths must be nonempty and within width 19")
    return np.ascontiguousarray(values)


class PersistentBoardScorer:
    def __init__(self, binary, blocks, pair, quad):
        self.process = subprocess.Popen(
            [str(binary)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.process.stdin.write(b"P484WG1\0")
        self.process.stdin.write(canonical_blocks(blocks, pair))
        self.process.stdin.write(np.asarray(quad, dtype="<f8").tobytes())
        self.process.stdin.flush()
        self.board_loaded = False

    def set_board(self, board):
        values = validate_board(board)
        self.process.stdin.write(struct.pack("<I", 1))
        self.process.stdin.write(values)
        self.process.stdin.flush()
        self.board_loaded = True

    def score(self, paths):
        if not self.board_loaded:
            raise RuntimeError("set_board must be called before score")
        values = canonical_paths(paths)
        self.process.stdin.write(struct.pack(
            "<III", 2, len(values), values.shape[1]))
        self.process.stdin.write(values.tobytes())
        self.process.stdin.flush()
        data = read_exact(self.process.stdout, len(values) * 8)
        if len(data) != len(values) * 8:
            raise RuntimeError(self.process.stderr.read().decode(
                "utf-8", "replace"))
        return np.frombuffer(data, dtype="<f8").copy()

    def close(self):
        if self.process.poll() is None:
            self.process.stdin.write(struct.pack("<I", 0))
            self.process.stdin.flush()
            self.process.stdin.close()
            if self.process.wait(timeout=10):
                raise RuntimeError(self.process.stderr.read().decode(
                    "utf-8", "replace"))

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def extend_records(blocks, pair, quad, records, binary=DEFAULT_BINARY,
                   beam_width=solver.EXTEND_BEAM):
    results = []
    with PersistentBoardScorer(binary, blocks, pair, quad) as scorer:
        for record in records:
            scorer.set_board(record["board"])
            beam = [(record["normalized_score"], tuple(record["path"]))]
            diagnostics = []
            for depth in range(solver.DEPTH + 1, solver.WIDTH + 1):
                paths = solver.gpu_beam.expand_bidirectional(
                    beam, solver.WIDTH)
                scores = scorer.score(paths)
                beam = solver.gpu_beam.select_diverse_arrays(
                    paths, scores, solver.WIDTH, beam_width)
                diagnostics.append({"depth": depth, "generated": len(paths),
                                    "retained": len(beam)})
            results.append((record["rank"], beam, diagnostics))
    return results


def merge_extended(records, extended,
                   terminals_per_seed=solver.TERMINALS_PER_SEED):
    records_by_rank = {record["rank"]: record for record in records}
    terminal = {}
    diagnostics = []
    for rank, beam, depth_diagnostics in sorted(extended):
        record = records_by_rank[rank]
        diagnostics.append({"refined_rank": record["rank"],
                            "shortlist_index": record["shortlist_index"],
                            "depths": depth_diagnostics})
        for score, path in beam[:terminals_per_seed]:
            candidate = {
                "extension_score": float(score),
                "order": list(path),
                "source_refined_rank": record["rank"],
                "source_shortlist_index": record["shortlist_index"],
            }
            previous = terminal.get(path)
            if previous is None or score > previous["extension_score"]:
                terminal[path] = candidate
    ranked = sorted(terminal.values(),
                    key=lambda record: (-record["extension_score"],
                                        record["order"]))
    for rank, record in enumerate(ranked, 1):
        record["extension_rank"] = rank
    return ranked, diagnostics


def _persistent_chunk(args):
    return extend_records(*args)


def extend_population(blocks, pair, quad, refined, seed_count,
                      workers=8, binary=DEFAULT_BINARY,
                      beam_width=solver.EXTEND_BEAM,
                      terminals_per_seed=solver.TERMINALS_PER_SEED):
    selected = refined[:seed_count]
    if workers < 1:
        raise ValueError("workers must be positive")
    worker_count = min(workers, len(selected))
    if not worker_count:
        return [], []
    chunks = [selected[index::worker_count]
              for index in range(worker_count)]
    tasks = [(blocks, pair, quad, chunk, binary, beam_width)
             for chunk in chunks]
    if worker_count == 1:
        extended = _persistent_chunk(tasks[0])
    else:
        with concurrent.futures.ProcessPoolExecutor(
                max_workers=worker_count) as pool:
            extended = [item for chunk in pool.map(_persistent_chunk, tasks)
                        for item in chunk]
    return merge_extended(selected, extended, terminals_per_seed)
