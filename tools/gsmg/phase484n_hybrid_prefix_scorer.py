#!/usr/bin/env python3
"""Persistent GPU adapter for the exact Phase 484J prefix statistic."""

from __future__ import annotations

import argparse
import itertools
import struct
import subprocess
from pathlib import Path

import numpy as np

import phase484a_raw_symbol_vic_solver as base
import phase484g_hard_negative_discriminator as learned
import phase484j_constructive_prefix_beam_probe as prefix

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_BINARY = SCRIPT_DIR.parents[1] / "_work/phase484n/prefix_server"
MAGIC = b"P484NG1\0"


def read_exact(stream, size: int) -> bytes:
    chunks = []
    remaining = size
    while remaining:
        chunk = stream.read(remaining)
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def canonical_blocks(blocks: list[str], pair: tuple[str, str]) -> bytes:
    remaining = [symbol for symbol in base.NINE_SYMBOLS if symbol not in pair]
    symbols = [pair[0], pair[1], *remaining]
    mapping = {symbol: index for index, symbol in enumerate(symbols)}
    if len(blocks) != 19 or any(len(block) != 30 for block in blocks):
        raise ValueError("GPU scorer currently requires 19 blocks of 30 rows")
    return bytes(mapping[symbol] for block in blocks for symbol in block)


def linear_coefficients(model) -> tuple[np.ndarray, float]:
    coefficient = np.asarray(model.weight / model.scale, dtype="<f8")
    intercept = float(model.intercept - np.dot(model.mean, coefficient))
    if coefficient.shape != (20,) or not np.all(np.isfinite(coefficient)):
        raise ValueError("expected a finite 20-feature linear model")
    return coefficient, intercept


class GpuPrefixScorer:
    def __init__(self, binary: Path, blocks: list[str], pair: tuple[str, str], model):
        coefficient, intercept = linear_coefficients(model)
        self.process = subprocess.Popen(
            [str(binary)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.process.stdin.write(MAGIC)
        self.process.stdin.write(canonical_blocks(blocks, pair))
        self.process.stdin.write(coefficient.tobytes())
        self.process.stdin.write(struct.pack("<d", intercept))
        self.process.stdin.flush()

    def score(self, paths) -> np.ndarray:
        paths = np.asarray(paths, dtype=np.uint8)
        if paths.ndim != 2 or not 4 <= paths.shape[1] <= 19:
            raise ValueError("paths must be an N x depth array, depth 4..19")
        if len(paths) == 0:
            return np.empty(0, dtype=np.float64)
        if np.any(paths >= 19):
            raise ValueError("path column outside width 19")
        self.process.stdin.write(struct.pack("<II", len(paths), paths.shape[1]))
        self.process.stdin.write(np.ascontiguousarray(paths).tobytes())
        self.process.stdin.flush()
        needed = len(paths) * 8
        data = read_exact(self.process.stdout, needed)
        if len(data) != needed:
            error = self.process.stderr.read().decode("utf-8", "replace")
            raise RuntimeError(f"GPU scorer stopped early: {error}")
        return np.frombuffer(data, dtype="<f8").copy()

    def close(self):
        if self.process.poll() is None:
            self.process.stdin.write(struct.pack("<II", 0, 0))
            self.process.stdin.flush()
            self.process.stdin.close()
            return_code = self.process.wait(timeout=10)
            if return_code:
                error = self.process.stderr.read().decode("utf-8", "replace")
                raise RuntimeError(f"GPU scorer exited {return_code}: {error}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.close()


def self_test(binary: Path) -> dict:
    width, fixture_index, depth = 19, 28, 8
    models = prefix.train_models(width)
    fixture = base.make_fixture(
        width, learned.PAIR_INDEX, fixture_index, seed=learned.SEED,
        board_mode="vic_profile", split="dev",
    )
    blocks = prefix.blocks_from_observed(fixture)
    paths = np.asarray(
        list(itertools.islice(itertools.permutations(range(width), depth), 256)),
        dtype=np.uint8,
    )
    expected = np.asarray([
        prefix.score_prefix(models[depth], blocks, tuple(fixture["pair"]), path)
        for path in paths
    ])
    with GpuPrefixScorer(binary, blocks, tuple(fixture["pair"]), models[depth]) as scorer:
        actual = scorer.score(paths)
    maximum_error = float(np.max(np.abs(expected - actual)))
    if maximum_error > 1e-10:
        raise AssertionError(f"CPU/GPU score mismatch: {maximum_error}")
    return {"paths": len(paths), "depth": depth, "max_abs_error": maximum_error}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, default=DEFAULT_BINARY)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if not args.self_test:
        parser.error("only --self-test is exposed; this module is solver infrastructure")
    print(self_test(args.binary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
