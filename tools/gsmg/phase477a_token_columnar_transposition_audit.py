#!/usr/bin/env python3
"""Phase 477A: pre-board ragged columnar transposition of the {g,i} FAED tokens.

Model A only:

    plaintext letters -> columnar transposition (unknown width w, unknown order)
                      -> 25-slot straddling checkerboard, escapes {g,i} -> FAED

The 436 `{g,i}` code tokens of FAED are treated as a column-permuted sequence
of plaintext letters under one global 25-slot board.

Search families (frozen):

* ``untranspose`` (observed tokens are the column-read output): every one of
  the ``w!`` column orders is enumerated for ``w <= ENUM_MAX_WIDTH``; orders
  are ranked by a substitution-invariant digraph/trigraph coincidence
  statistic of the reconstructed token sequence, and the top ``TOP_ORDERS``
  receive a full quadgram board anneal.  Widths above ``ENUM_MAX_WIDTH`` are
  not enumerable and are reported as ``not_enumerable``; development evidence
  shows the score landscape over orders is flat beyond one column swap, so no
  local search is used there.
* ``transpose`` (observed tokens are the row-major grid): each column is a
  contiguous plaintext chunk, so the board is annealed on within-column
  quadgrams first; the column order is then solved by Held-Karp on junction
  gains (``w <= 16``) or greedily, followed by full-score polish.

Every random choice comes from an explicit PCG32; every budget is a fixed
count.  No password material, oracle calls, address derivations, or Bitcoin
endpoint checks are performed.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import re
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
REPO_ROOT = SCRIPT_DIR.parent.parent

from cb_common import NINE_SYMS  # noqa: E402
from checkerboard_code_ic_oracle import segment_codes  # noqa: E402
from data import FAED  # noqa: E402

# --------------------------------------------------------------------------
# Frozen geometry and constants
# --------------------------------------------------------------------------

E1 = E2 = None
SINGLES = SLOT_CODES = CODE_TO_SLOT = None
N_SLOTS = 25
L = None
PAIR_LABEL = None


def configure_pair(e1: str, e2: str) -> None:
    """Select the escape pair (primary {g,i}; secondary {h,e}).  The token
    length L is the segmented FAED length under that pair."""
    global E1, E2, SINGLES, SLOT_CODES, CODE_TO_SLOT, L, PAIR_LABEL
    E1, E2 = e1, e2
    SINGLES = [c for c in NINE_SYMS if c not in (e1, e2)]
    SLOT_CODES = SINGLES + [e1 + c for c in NINE_SYMS] + [e2 + c for c in NINE_SYMS]
    CODE_TO_SLOT = {code: i for i, code in enumerate(SLOT_CODES)}
    codes = segment_codes(FAED, e1, e2)
    if codes is None:
        raise ValueError(f"pair {e1}{e2} does not segment FAED")
    L = len(codes)
    PAIR_LABEL = e1 + e2
    _ELIGIBLE.clear()


def pair_seed(base: int) -> int:
    """Primary-pair seeds are the protocol constants; the secondary pair
    derives its own disjoint seeds from them."""
    if PAIR_LABEL == "gi":
        return base
    return derive_seed(base, ord(E1), ord(E2))


WIDTHS = tuple(range(2, 41))
DIRECTIONS = ("untranspose", "transpose")
HK_MAX_WIDTH = 16
PATH_IMPROVE_PASSES = 200
ENUM_MAX_WIDTH = 11
TRIVIAL_WIDTHS = (2, 3, 4)
TOP_ORDERS = 16
TRIGRAM_WEIGHT = 3.0

QUADGRAM_FILE = SCRIPT_DIR / "data_files" / "english_quadgrams.txt"
CORPUS_FILE = REPO_ROOT / "wordlists" / "gsmg" / "cosmic_duality_book_full_text.txt"
NON_PROSE_SECTION_PATTERNS = (
    r"^Table of Contents", r"INDEX", r"Acknowledgments", r"colophon",
    r"^Back matter", r"^End of transcription", r"^Front matter",
)
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
HARD_TOP7_SHARE = 0.62
HARD_MIN_START_SEPARATION = 50

SEED_DEV = 0x477A0DE
SEED_HOLD = 0x477A401D
SEED_NULL = 0x477A0000
SEED_REAL = 0x477A4EA1
SEED_EQUIV = 0x477AE0

HARD_POWER_FRACTION = 0.80
NULL_TRIALS = 200
PROMOTION_P = 0.005

BUDGET = {
    # untranspose: exhaustive order enumeration, then board anneal on top orders
    "top_orders": TOP_ORDERS,
    "enum_board_restarts": 2,
    "enum_board_iters": 30000,
    "enum_board_t0": 20.0,
    "enum_board_t1": 1.0,
    # transpose: within-column board anneal, junction order solve, polish
    "restarts": 16,
    "top_k": 4,
    "rounds": 3,
    "board_init_iters": 10000,
    "board_init_t0": 20.0,
    "board_init_t1": 1.0,
    "board_refine_iters": 4000,
    "board_refine_t0": 5.0,
    "board_refine_t1": 0.5,
    "polish_moves": 3000,
}


_ELIGIBLE = {}


# --------------------------------------------------------------------------
# Deterministic randomness (PCG32, XSH-RR output)
# --------------------------------------------------------------------------

M64 = (1 << 64) - 1
PCG_MULT = 6364136223846793005


class PCG32:
    def __init__(self, initstate: int, initseq: int = 0x477A):
        self.state = 0
        self.inc = ((initseq << 1) | 1) & M64
        self.next_u32()
        self.state = (self.state + (initstate & M64)) & M64
        self.next_u32()

    def next_u32(self) -> int:
        old = self.state
        self.state = (old * PCG_MULT + self.inc) & M64
        xorshifted = (((old >> 18) ^ old) >> 27) & 0xFFFFFFFF
        rot = old >> 59
        return ((xorshifted >> rot) | (xorshifted << ((-rot) & 31))) & 0xFFFFFFFF

    def random(self) -> float:
        return self.next_u32() / 4294967296.0

    def below(self, n: int) -> int:
        """Bounded integer in [0, n): u32 modulo n (frozen convention)."""
        return self.next_u32() % n

    def shuffle(self, items: list) -> None:
        for i in range(len(items) - 1, 0, -1):
            j = self.below(i + 1)
            items[i], items[j] = items[j], items[i]

    def permutation(self, n: int) -> list:
        items = list(range(n))
        self.shuffle(items)
        return items


def derive_seed(base: int, *parts: int) -> int:
    h = base & M64
    for part in parts:
        h = ((h ^ (part & M64)) * 0x9E3779B97F4A7C15) & M64
        h ^= h >> 29
    return h


configure_pair("g", "i")


# --------------------------------------------------------------------------
# Language model
# --------------------------------------------------------------------------


def load_language_model(path=QUADGRAM_FILE):
    counts = {}
    total = 0
    with open(path) as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            quad, count = line.split()
            counts[quad] = int(count)
            total += int(count)
    floor = math.log10(0.01 / total)
    quad = np.full(26 ** 4, floor, dtype=np.float64)
    for q, c in counts.items():
        a, b, cc, d = (ord(ch) - 65 for ch in q)
        quad[((a * 26 + b) * 26 + cc) * 26 + d] = math.log10(c / total)
    return quad, floor


QUAD, FLOOR = load_language_model()


def score_indices(idx: np.ndarray) -> float:
    """Sum of log10 quadgram probabilities over all sliding windows of a letter
    index array (values 0..25)."""
    if idx.shape[0] < 4:
        return 0.0
    keys = ((idx[:-3] * 26 + idx[1:-2]) * 26 + idx[2:-1]) * 26 + idx[3:]
    return float(QUAD[keys].sum())


def text_of(idx: np.ndarray) -> str:
    return "".join(ALPHABET[i] for i in idx)


# --------------------------------------------------------------------------
# Token stream and board
# --------------------------------------------------------------------------


def stream_to_slots(stream: str) -> np.ndarray:
    codes = segment_codes(stream, E1, E2)
    if codes is None:
        raise ValueError("dangling escape")
    return np.array([CODE_TO_SLOT[c] for c in codes], dtype=np.int64)


def slots_to_stream(slots: np.ndarray) -> str:
    return "".join(SLOT_CODES[int(s)] for s in slots)


def random_key(rng: PCG32) -> np.ndarray:
    """26-entry key: key[slot] for slot<25 is the letter index; key[25] is the
    unused letter (quadgram_solver convention)."""
    return np.array(rng.permutation(26), dtype=np.int64)


# --------------------------------------------------------------------------
# Ragged columnar geometry
# --------------------------------------------------------------------------


class Geometry:
    """Frozen ragged convention: rows = ceil(L / w); the final w*rows - L
    columns by original index are one short; nothing is padded."""

    def __init__(self, length: int, width: int):
        self.L = length
        self.w = width
        self.rows = -(-length // width)
        self.short = width * self.rows - length
        self.lengths = np.array(
            [self.rows - 1 if c >= width - self.short else self.rows for c in range(width)],
            dtype=np.int64,
        )
        self.n_long = width - self.short
        p = np.arange(length)
        self.row_of = p // width
        self.col_of = p % width
        self.is_exact = self.short == 0

    def offsets_for(self, perm) -> np.ndarray:
        """Start offset in the column-read stream of every original column."""
        perm = np.asarray(perm)
        starts = np.concatenate(([0], np.cumsum(self.lengths[perm])[:-1]))
        off = np.empty(self.w, dtype=np.int64)
        off[perm] = starts
        return off

    def sigma(self, perm, direction: str) -> np.ndarray:
        """Position map: plaintext[p] = observed[sigma[p]]."""
        off = self.offsets_for(perm)
        sig_u = off[self.col_of] + self.row_of
        if direction == "untranspose":
            return sig_u
        inv = np.empty(self.L, dtype=np.int64)
        inv[sig_u] = np.arange(self.L)
        return inv

    def sigma_batch(self, perms: np.ndarray) -> np.ndarray:
        """Untranspose position maps for a (B, w) array of perms, where
        perms[b, k] is the original column read at position k."""
        read_lengths = self.lengths[perms]
        starts = np.zeros_like(read_lengths)
        starts[:, 1:] = np.cumsum(read_lengths, axis=1)[:, :-1]
        off = np.empty_like(starts)
        np.put_along_axis(off, perms, starts, axis=1)
        return off[:, self.col_of] + self.row_of[None, :]

    def perm_from_untranspose_sigma(self, sigma: np.ndarray):
        """Return the column-read perm if `sigma` is a member of this width's
        untranspose family, else None."""
        if sigma.shape[0] != self.L:
            return None
        if self.L > self.w and not np.all(sigma[self.w:] == sigma[:-self.w] + 1):
            return None
        starts = sigma[: self.w]
        perm = list(np.argsort(starts, kind="stable"))
        if not np.array_equal(self.sigma(perm, "untranspose"), sigma):
            return None
        return perm


def direction_equivalence(width: int, samples: int = 200, seed: int = SEED_EQUIV) -> dict:
    """Mechanically test whether the transpose family's position permutations
    all belong to the untranspose family.  Exhaustive for w <= 7, sampled
    otherwise."""
    geo = Geometry(L, width)
    if width <= 7:
        perms = list(itertools.permutations(range(width)))
        mode = "exhaustive"
    else:
        rng = PCG32(derive_seed(seed, width))
        perms = [rng.permutation(width) for _ in range(samples)]
        mode = "sampled"
    members = 0
    for perm in perms:
        sig_t = geo.sigma(list(perm), "transpose")
        if geo.perm_from_untranspose_sigma(sig_t) is not None:
            members += 1
    return {
        "width": width,
        "rows": int(geo.rows),
        "short_columns": int(geo.short),
        "mode": mode,
        "tested": len(perms),
        "transpose_in_untranspose_family": members,
        "identical": members == len(perms),
        "retained_directions": 1 if members == len(perms) else 2,
    }


# --------------------------------------------------------------------------
# Substitution-invariant order statistic and exhaustive enumeration
# --------------------------------------------------------------------------


def _pair_count_rows(codes: np.ndarray) -> np.ndarray:
    """Number of coincident pairs sum_n C(n, 2) per row of an integer array."""
    s = np.sort(codes.astype(np.int32), axis=1)
    n = s.shape[1]
    idx = np.arange(1, n, dtype=np.int32)[None, :]
    eq = s[:, 1:] == s[:, :-1]
    reset = np.where(eq, np.int32(0), idx)
    last_reset = np.maximum.accumulate(reset, axis=1)
    run_pos = np.where(eq, idx - last_reset, np.int32(0))
    return run_pos.sum(axis=1, dtype=np.int64)


def invariant_batch(obs: np.ndarray, geo: Geometry, perms: np.ndarray) -> np.ndarray:
    """digraph pairs + TRIGRAM_WEIGHT * trigraph pairs for each perm row."""
    seq = obs[geo.sigma_batch(perms)]
    c2 = seq[:, :-1] * 25 + seq[:, 1:]
    c3 = c2[:, :-1] * 25 + seq[:, 2:]
    return _pair_count_rows(c2) + TRIGRAM_WEIGHT * _pair_count_rows(c3)


def invariant_single(obs: np.ndarray, geo: Geometry, perm) -> float:
    return float(invariant_batch(obs, geo, np.asarray([perm], dtype=np.int64))[0])


def enumerate_top_orders(obs: np.ndarray, width: int, top: int, batch: int = 256):
    """Rank all w! column orders by the invariant statistic; return the top
    `top` as (statistic, perm) with deterministic tie-breaking (lexicographic
    perm order)."""
    geo = Geometry(obs.shape[0], width)
    best = []  # list of (stat, perm tuple), kept sorted descending
    threshold = -np.inf
    total = 0
    it = itertools.permutations(range(width))
    while True:
        chunk = list(itertools.islice(it, batch))
        if not chunk:
            break
        perms = np.array(chunk, dtype=np.int64)
        stats = invariant_batch(obs, geo, perms)
        total += perms.shape[0]
        keep = np.flatnonzero(stats >= threshold) if len(best) >= top else np.arange(perms.shape[0])
        for k in keep:
            best.append((float(stats[k]), tuple(int(x) for x in perms[k])))
        if len(best) > top:
            best.sort(key=lambda e: (-e[0], e[1]))
            best = best[:top]
            threshold = best[-1][0]
    best.sort(key=lambda e: (-e[0], e[1]))
    return best[:top], total


# --------------------------------------------------------------------------
# Held-Karp exact open-path solver (transpose direction)
# --------------------------------------------------------------------------

_POPCOUNT_CACHE = {}


def _masks_by_popcount(n: int):
    if n not in _POPCOUNT_CACHE:
        masks = np.arange(1 << n, dtype=np.int64)
        pop = np.zeros(1 << n, dtype=np.int64)
        for b in range(n):
            pop += (masks >> b) & 1
        _POPCOUNT_CACHE[n] = [masks[pop == k] for k in range(n + 1)]
    return _POPCOUNT_CACHE[n]


def held_karp_path(gain: np.ndarray) -> list:
    """Maximise sum of gain[i, j] over consecutive pairs of an open path that
    visits every node once."""
    n = gain.shape[0]
    full = (1 << n) - 1
    dp = np.full((1 << n, n), -np.inf, dtype=np.float64)
    parent = np.full((1 << n, n), -1, dtype=np.int8)
    for j in range(n):
        dp[1 << j, j] = 0.0
    layers = _masks_by_popcount(n)
    for k in range(2, n + 1):
        masks = layers[k]
        for j in range(n):
            has = ((masks >> j) & 1) == 1
            m = masks[has]
            prev = m ^ (1 << j)
            cand = dp[prev] + gain[:, j][None, :]
            best_i = cand.argmax(axis=1)
            dp[m, j] = cand[np.arange(m.shape[0]), best_i]
            parent[m, j] = best_i
    last = int(dp[full].argmax())
    path = [last]
    mask = full
    while parent[mask, path[-1]] >= 0:
        prev_node = int(parent[mask, path[-1]])
        mask ^= 1 << path[-1]
        path.append(prev_node)
    path.reverse()
    return path


def brute_force_path(gain: np.ndarray) -> list:
    n = gain.shape[0]
    best, best_path = -np.inf, None
    for perm in itertools.permutations(range(n)):
        total = sum(gain[perm[t], perm[t + 1]] for t in range(n - 1))
        if total > best:
            best, best_path = total, list(perm)
    return best_path


def path_gain(gain: np.ndarray, path) -> float:
    return float(sum(gain[path[t], path[t + 1]] for t in range(len(path) - 1)))


def improve_path(gain: np.ndarray, path: list, passes: int = PATH_IMPROVE_PASSES) -> list:
    """Deterministic first-improvement or-opt (block lengths 1-3) and 2-opt
    reversal on an open path, repeated for at most `passes` sweeps."""
    n = len(path)
    best = path_gain(gain, path)
    for _ in range(passes):
        improved = False
        for length in (1, 2, 3):
            for i in range(n - length + 1):
                block = path[i:i + length]
                rest = path[:i] + path[i + length:]
                for j in range(len(rest) + 1):
                    if j == i:
                        continue
                    cand = rest[:j] + block + rest[j:]
                    g = path_gain(gain, cand)
                    if g > best + 1e-12:
                        path, best, improved = cand, g, True
                        break
                if improved:
                    break
            if improved:
                break
        if not improved:
            for i in range(n - 1):
                for j in range(i + 1, n):
                    cand = path[:i] + path[i:j + 1][::-1] + path[j + 1:]
                    g = path_gain(gain, cand)
                    if g > best + 1e-12:
                        path, best, improved = cand, g, True
                        break
                if improved:
                    break
        if not improved:
            break
    return path


def greedy_path(gain: np.ndarray) -> list:
    """Deterministic nearest-neighbour construction used above HK_MAX_WIDTH."""
    n = gain.shape[0]
    unvisited = set(range(n))
    start = max(range(n), key=lambda j: (float(np.max(gain[j])), -j))
    path = [start]
    unvisited.remove(start)
    while unvisited:
        nxt = max(unvisited, key=lambda j: (float(gain[path[-1], j]), -j))
        path.append(nxt)
        unvisited.remove(nxt)
    return path


# --------------------------------------------------------------------------
# Board annealing and order moves
# --------------------------------------------------------------------------


def anneal_key(score_fn, key: np.ndarray, rng: PCG32, iters: int, t0: float, t1: float):
    """Simulated annealing over 26-key swaps (including the unused letter),
    geometric cooling from t0 to t1 over exactly `iters` proposals."""
    key = key.copy()
    cur = score_fn(key)
    best, best_key = cur, key.copy()
    cool = (t1 / t0) ** (1.0 / max(1, iters))
    temp = t0
    for _ in range(iters):
        i, j = rng.below(26), rng.below(26)
        if i != j:
            key[i], key[j] = key[j], key[i]
            s = score_fn(key)
            delta = s - cur
            if delta >= 0 or rng.random() < math.exp(delta / temp):
                cur = s
                if s > best:
                    best, best_key = s, key.copy()
            else:
                key[i], key[j] = key[j], key[i]
        temp *= cool
    return best_key, best


def perm_move(perm, rng: PCG32):
    """One of three local order moves: swap, or-opt block move (1-3), reversal."""
    w = len(perm)
    cand = list(perm)
    kind = rng.below(3)
    if kind == 0:
        i, j = rng.below(w), rng.below(w)
        if i == j:
            return None
        cand[i], cand[j] = cand[j], cand[i]
    elif kind == 1:
        length = 1 + rng.below(3)
        if length >= w:
            return None
        i = rng.below(w - length + 1)
        block = cand[i:i + length]
        del cand[i:i + length]
        j = rng.below(len(cand) + 1)
        cand[j:j] = block
    else:
        i, j = rng.below(w), rng.below(w)
        if i > j:
            i, j = j, i
        if j == i:
            return None
        cand[i:j + 1] = cand[i:j + 1][::-1]
    if cand == list(perm):
        return None
    return cand


# --------------------------------------------------------------------------
# Cell solver
# --------------------------------------------------------------------------


class CellSolver:
    def __init__(self, observed: np.ndarray, width: int, direction: str, budget=BUDGET):
        self.obs = observed
        self.geo = Geometry(observed.shape[0], width)
        self.direction = direction
        self.budget = budget
        self.w = width
        self.rows = self.geo.rows
        if direction == "transpose":
            self.columns = [observed[c::width] for c in range(width)]
            natural = np.concatenate(self.columns)
            bounds = np.cumsum([0] + [len(c) for c in self.columns])
            starts = np.arange(natural.shape[0] - 3)
            inside = np.searchsorted(bounds, starts, side="right") == np.searchsorted(bounds, starts + 3, side="right")
            self.within_slots = natural
            self.within_starts = starts[inside]

    # -- evaluation -------------------------------------------------------
    def plain_slots(self, perm) -> np.ndarray:
        return self.obs[self.geo.sigma(perm, self.direction)]

    def evaluate(self, perm, key: np.ndarray) -> float:
        return score_indices(key[self.plain_slots(perm)])

    def within_score(self, key: np.ndarray) -> float:
        idx = key[self.within_slots]
        s = self.within_starts
        keys = ((idx[s] * 26 + idx[s + 1]) * 26 + idx[s + 2]) * 26 + idx[s + 3]
        return float(QUAD[keys].sum())

    # -- transpose order step ---------------------------------------------
    def junction_order(self, key: np.ndarray):
        letters = [key[col] for col in self.columns]
        tails = np.stack([c[-3:] for c in letters])
        heads = np.stack([c[:3] for c in letters])
        t0, t1, t2 = tails[:, 0], tails[:, 1], tails[:, 2]
        h0, h1, h2 = heads[:, 0], heads[:, 1], heads[:, 2]
        k1 = ((t0 * 26 + t1) * 26 + t2)[:, None] * 26 + h0[None, :]
        k2 = ((t1 * 26 + t2)[:, None] * 26 + h0[None, :]) * 26 + h1[None, :]
        k3 = ((t2[:, None] * 26 + h0[None, :]) * 26 + h1[None, :]) * 26 + h2[None, :]
        gain = QUAD[k1] + QUAD[k2] + QUAD[k3]
        if self.w <= HK_MAX_WIDTH:
            return list(held_karp_path(gain))
        return improve_path(gain, list(greedy_path(gain)))

    def polish(self, perm, key: np.ndarray, rng: PCG32, moves: int):
        cur = list(perm)
        cur_score = self.evaluate(cur, key)
        for _ in range(moves):
            cand = perm_move(cur, rng)
            if cand is None:
                continue
            s = self.evaluate(cand, key)
            if s >= cur_score:
                cur, cur_score = cand, s
        return cur, cur_score

    def board_refine(self, perm, key, rng):
        b = self.budget
        plain = self.plain_slots(perm)
        return anneal_key(lambda k: score_indices(k[plain]), key, rng,
                          b["board_refine_iters"], b["board_refine_t0"], b["board_refine_t1"])

    def _finish(self, best, extra=None):
        score, perm, key = best
        plain = key[self.plain_slots(perm)]
        out = {
            "width": self.w,
            "direction": self.direction,
            "score": score,
            "normalised": score / self.geo.L,
            "perm": [int(p) for p in perm],
            "key": [int(k) for k in key],
            "text": text_of(plain),
        }
        if extra:
            out.update(extra)
        return out

    def solve(self, seed: int):
        if self.direction == "transpose":
            return self._solve_transpose(seed)
        return self._solve_untranspose(seed)

    def _solve_untranspose(self, seed: int):
        b = self.budget
        if self.w > ENUM_MAX_WIDTH:
            return {"width": self.w, "direction": self.direction, "status": "not_enumerable"}
        top, total = enumerate_top_orders(self.obs, self.w, b["top_orders"])
        best = None
        ranked = []
        for rank, (stat, perm) in enumerate(top):
            plain = self.plain_slots(perm)
            cell_best = None
            for r in range(b["enum_board_restarts"]):
                rng = PCG32(derive_seed(seed, self.w, 0, rank, r))
                key, s = anneal_key(lambda k: score_indices(k[plain]), random_key(rng), rng,
                                    b["enum_board_iters"], b["enum_board_t0"], b["enum_board_t1"])
                if cell_best is None or s > cell_best[0]:
                    cell_best = (s, list(perm), key)
            ranked.append({"rank": rank, "invariant": stat, "score": cell_best[0]})
            if best is None or cell_best[0] > best[0]:
                best = cell_best
        return self._finish(best, {"status": "enumerated", "orders_enumerated": total,
                                   "top_orders": ranked})

    def _solve_transpose(self, seed: int):
        b = self.budget
        boards = []
        for r in range(b["restarts"]):
            rng = PCG32(derive_seed(seed, self.w, 1, r))
            key, s = anneal_key(self.within_score, random_key(rng), rng,
                                b["board_init_iters"], b["board_init_t0"], b["board_init_t1"])
            boards.append((s, key, rng))
        boards.sort(key=lambda item: -item[0])
        best = None
        for s, key, rng in boards[: b["top_k"]]:
            perm = self.junction_order(key)
            perm, _ = self.polish(perm, key, rng, b["polish_moves"])
            cand = (self.evaluate(perm, key), list(perm), key.copy())
            for _ in range(b["rounds"]):
                key, s = self.board_refine(perm, key, rng)
                perm = self.junction_order(key)
                perm, s = self.polish(perm, key, rng, b["polish_moves"])
                if s > cand[0]:
                    cand = (s, list(perm), key.copy())
            if best is None or cand[0] > best[0]:
                best = cand
        return self._finish(best, {"status": "searched"})


# --------------------------------------------------------------------------
# Synthetic fixtures
# --------------------------------------------------------------------------

_CORPUS = None


def corpus_letters() -> str:
    """Prose sections of the Cosmic Duality transcription, letters only,
    J -> I.  Front matter, table of contents, index, acknowledgments,
    colophon and back matter are excluded."""
    global _CORPUS
    if _CORPUS is None:
        keep = True
        chunks = []
        for line in CORPUS_FILE.read_text().splitlines():
            if line.startswith("## "):
                name = line[3:]
                keep = not any(re.search(p, name) for p in NON_PROSE_SECTION_PATTERNS)
                continue
            if line.startswith("#") or not keep:
                continue
            chunks.append(line)
        text = "\n".join(chunks).upper()
        _CORPUS = "".join(ch for ch in text if "A" <= ch <= "Z").replace("J", "I")
    return _CORPUS


def top7_share(passage: str) -> float:
    counts = np.bincount(np.frombuffer(passage.encode(), dtype=np.uint8) - 65, minlength=26)
    return float(np.sort(counts)[-7:].sum()) / len(passage)


def window_top7_shares() -> np.ndarray:
    letters = corpus_letters()
    arr = np.frombuffer(letters.encode(), dtype=np.uint8) - 65
    counts = np.bincount(arr[:L], minlength=26).astype(np.int64)
    shares = np.empty(len(arr) - L + 1)
    for start in range(len(arr) - L + 1):
        if start > 0:
            counts[arr[start - 1]] -= 1
            counts[arr[start + L - 1]] += 1
        shares[start] = np.sort(counts)[-7:].sum() / L
    return shares


def eligible_hard_starts(threshold=HARD_TOP7_SHARE, separation=HARD_MIN_START_SEPARATION):
    key = (threshold, separation)
    if key not in _ELIGIBLE:
        shares = window_top7_shares()
        candidates = np.flatnonzero(shares >= threshold)
        chosen = []
        for c in candidates:
            if not chosen or c - chosen[-1] >= separation:
                chosen.append(int(c))
        _ELIGIBLE[key] = (chosen, int(candidates.shape[0]), float(shares.max()))
    return _ELIGIBLE[key]


def make_fixture(width: int, direction: str, pool: str, seed: int) -> dict:
    rng = PCG32(seed)
    letters = corpus_letters()
    if pool == "hard":
        starts, _, _ = eligible_hard_starts()
        start = starts[rng.below(len(starts))]
    else:
        start = rng.below(len(letters) - L + 1)
    passage = letters[start:start + L]
    idx = np.frombuffer(passage.encode(), dtype=np.uint8).astype(np.int64) - 65
    available = [i for i in range(26) if i != 9]  # J unused
    if pool == "hard":
        counts = np.bincount(idx, minlength=26)
        top = sorted(range(26), key=lambda i: (-counts[i], i))[:7]
        rest = [i for i in available if i not in top]
        rng.shuffle(top)
        rng.shuffle(rest)
        key = np.array(top + rest + [9], dtype=np.int64)
    else:
        rng.shuffle(available)
        key = np.array(available + [9], dtype=np.int64)
    inverse = np.full(26, -1, dtype=np.int64)
    inverse[key[:25]] = np.arange(25)
    plain_slots = inverse[idx]
    assert np.all(plain_slots >= 0)
    perm = rng.permutation(width)
    geo = Geometry(L, width)
    observed = np.empty(L, dtype=np.int64)
    observed[geo.sigma(perm, direction)] = plain_slots
    return {
        "width": width,
        "direction": direction,
        "pool": pool,
        "seed": seed,
        "start": int(start),
        "passage": passage,
        "top7_share": top7_share(passage),
        "key": [int(k) for k in key],
        "perm": [int(p) for p in perm],
        "stream": slots_to_stream(observed),
    }


def kendall_tau(perm_a, perm_b) -> float:
    w = len(perm_a)
    rank_a = np.empty(w, dtype=np.int64)
    rank_b = np.empty(w, dtype=np.int64)
    rank_a[np.asarray(perm_a)] = np.arange(w)
    rank_b[np.asarray(perm_b)] = np.arange(w)
    concordant = 0
    for i in range(w):
        for j in range(i + 1, w):
            concordant += 1 if (rank_a[i] - rank_a[j]) * (rank_b[i] - rank_b[j]) > 0 else -1
    return concordant / (w * (w - 1) / 2)


def planted_score(fixture: dict) -> float:
    key = np.array(fixture["key"])
    obs = stream_to_slots(fixture["stream"])
    sigma = Geometry(L, fixture["width"]).sigma(fixture["perm"], fixture["direction"])
    return score_indices(key[obs[sigma]])


def evaluate_fixture(fixture: dict, result: dict) -> dict:
    truth = planted_score(fixture) / L
    if result.get("status") == "not_enumerable":
        return {"reach": False, "success": False, "truth_normalised": truth, "found_normalised": None,
                "tau": None, "accuracy": None, "exact_perm": False, "board_accuracy": None}
    tau = kendall_tau(fixture["perm"], result["perm"])
    accuracy = sum(a == b for a, b in zip(fixture["passage"], result["text"])) / L
    board_acc = sum(a == b for a, b in zip(fixture["key"][:25], result["key"][:25])) / 25
    reach = result["normalised"] >= truth - 1e-9
    return {
        "tau": tau,
        "accuracy": accuracy,
        "exact_perm": list(fixture["perm"]) == list(result["perm"]),
        "board_accuracy": board_acc,
        "truth_normalised": truth,
        "found_normalised": result["normalised"],
        "reach": reach,
        "success": reach,
    }


# --------------------------------------------------------------------------
# Family runs (multiprocessing over cells)
# --------------------------------------------------------------------------


def _solve_task(task):
    stream, width, direction, seed, budget = task
    obs = stream_to_slots(stream)
    t = time.perf_counter()
    result = CellSolver(obs, width, direction, budget).solve(seed)
    result["seconds"] = time.perf_counter() - t
    return result


def _fixture_task(task):
    width, direction, pool, fixture_seed, solve_seed, budget = task
    fixture = make_fixture(width, direction, pool, fixture_seed)
    result = _solve_task((fixture["stream"], width, direction, solve_seed, budget))
    metrics = evaluate_fixture(fixture, result)
    return {
        "width": width, "direction": direction, "pool": pool,
        "fixture_seed": fixture_seed, "solve_seed": solve_seed,
        "start": fixture["start"], "top7_share": fixture["top7_share"],
        "status": result.get("status"), "seconds": result["seconds"], **metrics,
    }


def run_pool(tasks, worker, workers: int):
    if workers <= 1:
        return [worker(t) for t in tasks]
    with Pool(workers) as pool:
        return list(pool.imap(worker, tasks, chunksize=1))


def power_tasks(widths, directions, n_hard: int, n_broad: int, seed_base: int, budget):
    tasks = []
    for w in widths:
        for d in directions:
            di = DIRECTIONS.index(d)
            for i in range(n_hard):
                fs = derive_seed(seed_base, 1, w, di, i)
                tasks.append((w, d, "hard", fs, derive_seed(fs, 77), budget))
            for i in range(n_broad):
                fs = derive_seed(seed_base, 2, w, di, i)
                tasks.append((w, d, "broad", fs, derive_seed(fs, 77), budget))
    return tasks


def summarise_power(records):
    cells = {}
    for r in records:
        cells.setdefault((r["width"], r["direction"]), []).append(r)
    summary = []
    for (w, d), rs in sorted(cells.items()):
        hard = [r for r in rs if r["pool"] == "hard"]
        broad = [r for r in rs if r["pool"] == "broad"]
        hard_ok = sum(r["success"] for r in hard)
        if d == "untranspose" and w > ENUM_MAX_WIDTH:
            status = "not_enumerable"
        elif hard and hard_ok >= HARD_POWER_FRACTION * len(hard):
            status = "trivially_powered" if w in TRIVIAL_WIDTHS else "powered"
        else:
            status = "underpowered"
        summary.append({
            "width": w, "direction": d, "status": status,
            "hard_success": hard_ok, "hard_n": len(hard),
            "broad_success": sum(r["success"] for r in broad), "broad_n": len(broad),
            "hard_exact_perm": sum(bool(r["exact_perm"]) for r in hard),
            "mean_hard_accuracy": float(np.mean([r["accuracy"] for r in hard if r["accuracy"] is not None])) if hard and status != "not_enumerable" else None,
            "mean_hard_tau": float(np.mean([r["tau"] for r in hard if r["tau"] is not None])) if hard and status != "not_enumerable" else None,
            "mean_seconds": float(np.mean([r["seconds"] for r in rs])),
        })
    return summary


def family_cells(widths, directions):
    return [(w, d) for w in widths for d in directions
            if not (d == "untranspose" and w > ENUM_MAX_WIDTH)]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --------------------------------------------------------------------------
# Self test
# --------------------------------------------------------------------------


def self_test(verbose=True) -> dict:
    report = {}
    obs = stream_to_slots(FAED)
    assert obs.shape[0] == L and len(set(obs.tolist())) == 25
    for w in WIDTHS:
        for d in DIRECTIONS:
            fx = make_fixture(w, d, "broad", derive_seed(5, w, DIRECTIONS.index(d)))
            back = stream_to_slots(fx["stream"])
            key = np.array(fx["key"])
            plain = text_of(key[back[Geometry(L, w).sigma(fx["perm"], d)]])
            assert plain == fx["passage"], (w, d)
    report["round_trip"] = "ok"
    for n in range(2, 9):
        for trial in range(3):
            r = PCG32(derive_seed(9, n, trial))
            gain = np.array([[r.random() * 10 - 5 for _ in range(n)] for _ in range(n)])
            assert held_karp_path(gain) == brute_force_path(gain), ("hk", n)
    report["held_karp_vs_brute_force"] = "ok"
    # batched invariant equals the scalar definition
    geo = Geometry(L, 7)
    r = PCG32(3)
    perms = np.array([r.permutation(7) for _ in range(5)])
    for k in range(5):
        seq = obs[geo.sigma(perms[k], "untranspose")]
        c2 = np.bincount(seq[:-1] * 25 + seq[1:])
        c3 = np.bincount((seq[:-2] * 25 + seq[1:-1]) * 25 + seq[2:])
        ref = (c2 * (c2 - 1)).sum() / 2 + TRIGRAM_WEIGHT * (c3 * (c3 - 1)).sum() / 2
        assert abs(invariant_batch(obs, geo, perms)[k] - ref) < 1e-9
    report["invariant_batch"] = "ok"
    report["direction_equivalence"] = [direction_equivalence(w) for w in WIDTHS]
    starts, raw, max_share = eligible_hard_starts()
    report["pair"] = PAIR_LABEL
    report["length"] = L
    report["hard_pool"] = {"threshold": HARD_TOP7_SHARE, "raw_windows": raw,
                           "separated_starts": len(starts), "corpus_max_top7_share": max_share,
                           "corpus_letters": len(corpus_letters())}
    if verbose:
        print(json.dumps({k: v for k, v in report.items() if k != "direction_equivalence"}, indent=2))
        print("directions retained per width:",
              {r["width"]: r["retained_directions"] for r in report["direction_equivalence"]})
    return report


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def parse_widths(spec: str):
    out = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-")
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


def budget_from_args(args):
    b = dict(BUDGET)
    if args.budget:
        b.update(json.loads(args.budget))
    return b


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("selftest")
    for name in ("power", "real", "null"):
        p = sub.add_parser(name)
        p.add_argument("--pair", choices=["gi", "he"], default="gi")
        p.add_argument("--widths", default="2-40")
        p.add_argument("--directions", default="untranspose,transpose")
        p.add_argument("--workers", type=int, default=16)
        p.add_argument("--budget", default=None)
        p.add_argument("--out", required=True)
        if name == "power":
            p.add_argument("--pool", choices=["dev", "hold"], default="dev")
            p.add_argument("--n-hard", type=int, default=10)
            p.add_argument("--n-broad", type=int, default=5)
        if name == "null":
            p.add_argument("--trials", type=int, default=NULL_TRIALS)
            p.add_argument("--first", type=int, default=0)
    args = parser.parse_args()

    if args.cmd == "selftest":
        self_test()
        return
    configure_pair(args.pair[0], args.pair[1])
    budget = budget_from_args(args)
    widths = parse_widths(args.widths)
    directions = args.directions.split(",")
    cells = family_cells(widths, directions)
    if args.cmd == "power":
        seed_base = pair_seed(SEED_DEV if args.pool == "dev" else SEED_HOLD)
        tasks = [t for t in power_tasks(widths, directions, args.n_hard, args.n_broad, seed_base, budget)
                 if (t[0], t[1]) in cells]
        t = time.perf_counter()
        records = run_pool(tasks, _fixture_task, args.workers)
        payload = {"pair": PAIR_LABEL, "length": L, "pool": args.pool, "seed_base": seed_base, "budget": budget,
                   "n_hard": args.n_hard, "n_broad": args.n_broad,
                   "wall_seconds": time.perf_counter() - t,
                   "summary": summarise_power(records), "records": records}
    elif args.cmd == "real":
        tasks = [(FAED, w, d, pair_seed(SEED_REAL), budget) for w, d in cells]
        t = time.perf_counter()
        results = run_pool(tasks, _solve_task, args.workers)
        payload = {"pair": PAIR_LABEL, "length": L, "seed": pair_seed(SEED_REAL), "budget": budget, "cells_run": cells,
                   "wall_seconds": time.perf_counter() - t,
                   "family_max": max(r["normalised"] for r in results), "cells": results}
    else:
        real = stream_to_slots(FAED)
        histogram = np.bincount(real, minlength=25).tolist()
        tasks = []
        for k in range(args.first, args.first + args.trials):
            rng = PCG32(derive_seed(pair_seed(SEED_NULL), k))
            shuffled = real.copy().tolist()
            rng.shuffle(shuffled)
            shuffled = np.array(shuffled)
            assert np.bincount(shuffled, minlength=25).tolist() == histogram
            stream = slots_to_stream(shuffled)
            for w, d in cells:
                tasks.append((stream, w, d, derive_seed(pair_seed(SEED_NULL), k, 1), budget))
        t = time.perf_counter()
        results = run_pool(tasks, _solve_task, args.workers)
        trials = []
        per = len(cells)
        for n, k in enumerate(range(args.first, args.first + args.trials)):
            rs = results[n * per:(n + 1) * per]
            trials.append({"trial": k, "family_max": max(r["normalised"] for r in rs),
                           "cells": [{"width": r["width"], "direction": r["direction"],
                                      "normalised": r["normalised"]} for r in rs]})
        payload = {"pair": PAIR_LABEL, "length": L, "seed_base": pair_seed(SEED_NULL), "budget": budget, "cells_run": cells,
                   "wall_seconds": time.perf_counter() - t, "trials": trials}
    Path(args.out).write_text(json.dumps(payload, indent=2) + "\n")
    print("wrote", args.out)


if __name__ == "__main__":
    main()
