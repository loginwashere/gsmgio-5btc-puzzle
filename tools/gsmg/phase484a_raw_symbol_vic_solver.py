#!/usr/bin/env python3
"""Phase 484A development infrastructure for raw-symbol VIC-order fixtures.

This module intentionally does not import or score FAED.  It supplies frozen-
shape geometry and exact-570 synthetic fixtures for solver development.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
CORPUS_FILE = REPO_ROOT / "wordlists/gsmg/cosmic_duality_book_full_text.txt"
QUADGRAM_FILE = SCRIPT_DIR / "data_files" / "english_quadgrams.txt"

RAW_LENGTH = 570
WIDTHS = tuple(range(2, 41))
EXACT_WIDTHS = tuple(w for w in WIDTHS if RAW_LENGTH % w == 0)
NINE_SYMBOLS = "abcdefghi"
LETTER_ALPHABET = "ABCDEFGHIKLMNOPQRSTUVWXYZ"
ESCAPE_PAIRS = tuple(itertools.combinations(NINE_SYMBOLS, 2))
SEED_DEV = 0x484A0DE
SEED_HOLDOUT = 0x484A401D
BOARD_MODES = ("vic_profile", "broad_random")
FIXTURE_SPLITS = ("dev", "holdout")
JOINT_TAIL_FIXTURES = (
    ("vic_profile", 6, 30),
    ("vic_profile", 6, 34),
    ("broad_random", 6, 28),
    ("broad_random", 6, 30),
)
M64 = (1 << 64) - 1
PCG_MULT = 6364136223846793005
NON_PROSE_PATTERNS = (
    r"^Table of Contents", r"INDEX", r"Acknowledgments", r"colophon",
    r"^Back matter", r"^End of transcription", r"^Front matter",
)


class PCG32:
    def __init__(self, initstate: int, initseq: int = 0x484A):
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

    def below(self, n: int) -> int:
        if n <= 0:
            raise ValueError("bound must be positive")
        return self.next_u32() % n

    def shuffle(self, values: list) -> None:
        for index in range(len(values) - 1, 0, -1):
            other = self.below(index + 1)
            values[index], values[other] = values[other], values[index]

    def permutation(self, n: int) -> list[int]:
        values = list(range(n))
        self.shuffle(values)
        return values

    def random(self) -> float:
        return self.next_u32() / 4294967296.0


def derive_seed(base: int, *parts: int) -> int:
    value = base & M64
    for part in parts:
        value = ((value ^ (part & M64)) * 0x9E3779B97F4A7C15) & M64
        value ^= value >> 29
    return value


def slot_codes(pair: tuple[str, str]) -> tuple[str, ...]:
    e1, e2 = pair
    if e1 == e2 or e1 not in NINE_SYMBOLS or e2 not in NINE_SYMBOLS:
        raise ValueError("escape pair must contain two distinct a-i symbols")
    singles = [symbol for symbol in NINE_SYMBOLS if symbol not in pair]
    return tuple(singles + [e1 + symbol for symbol in NINE_SYMBOLS]
                 + [e2 + symbol for symbol in NINE_SYMBOLS])


def relabel_symbol_map(pair_from: tuple[str, str], pair_to: tuple[str, str]) -> dict[str, str]:
    """Bijection on the 9-symbol a-i alphabet mapping pair_from's two escapes
    onto pair_to's two escapes (in order) while preserving the relative order
    of the remaining 7 symbols. Witnesses that a synthetic fixture family
    built on any escape pair is structurally identical (same segmentation
    shape, same solvability) to the family built on any other pair -- because
    the choice of which two of the nine symbols play "escape" is a pure
    labeling convention for synthetic fixtures, unlike for the real FAED
    stream, whose a-i symbol frequencies are fixed and not relabeled."""
    non_pair_from = [symbol for symbol in NINE_SYMBOLS if symbol not in pair_from]
    non_pair_to = [symbol for symbol in NINE_SYMBOLS if symbol not in pair_to]
    mapping = dict(zip(pair_from, pair_to))
    mapping.update(zip(non_pair_from, non_pair_to))
    return mapping


def relabel_string(text: str, mapping: dict[str, str]) -> str:
    return "".join(mapping[symbol] for symbol in text)


def segment_raw(raw: str, pair: tuple[str, str]) -> tuple[str, ...] | None:
    escapes = frozenset(pair)
    result = []
    index = 0
    while index < len(raw):
        if raw[index] in escapes:
            if index + 1 == len(raw):
                return None
            result.append(raw[index:index + 2])
            index += 2
        else:
            result.append(raw[index])
            index += 1
    return tuple(result)


@dataclass(frozen=True)
class Geometry:
    length: int
    width: int

    def __post_init__(self) -> None:
        if self.length <= 0 or self.width <= 0 or self.width > self.length:
            raise ValueError("geometry requires 0 < width <= length")

    @property
    def rows(self) -> int:
        return -(-self.length // self.width)

    @property
    def short_count(self) -> int:
        return self.width * self.rows - self.length

    @property
    def column_lengths(self) -> tuple[int, ...]:
        long_count = self.width - self.short_count
        return tuple(self.rows if column < long_count else self.rows - 1
                     for column in range(self.width))

    def validate_order(self, order) -> tuple[int, ...]:
        order = tuple(order)
        if len(order) != self.width or set(order) != set(range(self.width)):
            raise ValueError("order must be a permutation of range(width)")
        return order

    def encrypt(self, row_major: str, order) -> str:
        if len(row_major) != self.length:
            raise ValueError("row-major input has wrong length")
        order = self.validate_order(order)
        columns = [row_major[column::self.width] for column in range(self.width)]
        return "".join(columns[column] for column in order)

    def decrypt(self, column_read: str, order) -> str:
        if len(column_read) != self.length:
            raise ValueError("column-read input has wrong length")
        order = self.validate_order(order)
        columns = [""] * self.width
        offset = 0
        lengths = self.column_lengths
        for column in order:
            next_offset = offset + lengths[column]
            columns[column] = column_read[offset:next_offset]
            offset = next_offset
        if offset != self.length:
            raise AssertionError("column chunks did not consume input")
        indices = [0] * self.width
        restored = []
        for position in range(self.length):
            column = position % self.width
            restored.append(columns[column][indices[column]])
            indices[column] += 1
        return "".join(restored)


def corpus_words() -> tuple[str, ...]:
    keep = True
    chunks = []
    for line in CORPUS_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section = line[3:]
            keep = not any(re.search(pattern, section) for pattern in NON_PROSE_PATTERNS)
            continue
        if line.startswith("#") or not keep:
            continue
        chunks.append(line)
    return tuple(word.replace("J", "I")
                 for word in re.findall(r"[A-Z]+", "\n".join(chunks).upper()))


def corpus_split_words() -> dict[str, tuple[str, ...]]:
    words = corpus_words()
    midpoint = len(words) // 2
    third = midpoint + len(words) // 4
    gap_words = 100
    return {
        "train": words[:midpoint - gap_words],
        "dev": words[midpoint + gap_words:third - gap_words],
        "holdout": words[third + gap_words:],
    }


def corpus_splits() -> dict[str, str]:
    return {name: "".join(words) for name, words in corpus_split_words().items()}


def corpus_word_starts(split: str) -> tuple[int, ...]:
    words = corpus_split_words()[split]
    starts = []
    offset = 0
    for word in words:
        starts.append(offset)
        offset += len(word)
    return tuple(starts)


def corpus_letters() -> str:
    return "".join(corpus_words())


def encode_plaintext(plaintext: str, letter_to_code: dict[str, str]) -> str:
    try:
        return "".join(letter_to_code[letter] for letter in plaintext)
    except KeyError as error:
        raise ValueError(f"plaintext contains unsupported letter {error.args[0]!r}") from error


def decode_raw(raw: str, pair: tuple[str, str], code_to_letter: dict[str, str]) -> str | None:
    codes = segment_raw(raw, pair)
    if codes is None:
        return None
    try:
        return "".join(code_to_letter[code] for code in codes)
    except KeyError as error:
        raise ValueError(f"board has no assignment for code {error.args[0]!r}") from error


def exact_length_passage(source: str, start: int, letter_to_code: dict[str, str],
                         target: int = RAW_LENGTH) -> str | None:
    total = 0
    end = start
    while end < len(source) and total < target:
        total += len(letter_to_code[source[end]])
        end += 1
    return source[start:end] if total == target else None


def make_fixture(width: int, pair_index: int = 0, fixture_index: int = 0,
                 seed: int = SEED_DEV, max_attempts: int = 10000,
                 board_mode: str = "vic_profile", split: str = "dev") -> dict:
    if width not in WIDTHS:
        raise ValueError("development width must be in 2..40")
    if not 0 <= pair_index < len(ESCAPE_PAIRS):
        raise ValueError("pair index out of range")
    if board_mode not in BOARD_MODES:
        raise ValueError(f"unknown board mode: {board_mode}")
    if split not in FIXTURE_SPLITS:
        raise ValueError(f"unknown fixture split: {split}")
    mode_index = BOARD_MODES.index(board_mode)
    rng = PCG32(derive_seed(seed, width, pair_index, fixture_index, mode_index))
    pair = ESCAPE_PAIRS[pair_index]
    codes = slot_codes(pair)
    splits = corpus_splits()
    source = splits[split]
    if board_mode == "broad_random":
        letters = list(LETTER_ALPHABET)
        rng.shuffle(letters)
    else:
        training = splits["train"]
        frequencies = {letter: training.count(letter) for letter in LETTER_ALPHABET}
        common = sorted(LETTER_ALPHABET, key=lambda letter: (-frequencies[letter], letter))[:7]
        other = [letter for letter in LETTER_ALPHABET if letter not in common]
        rng.shuffle(common)
        rng.shuffle(other)
        letters = common + other
    letter_to_code = dict(zip(letters, codes))
    code_to_letter = {code: letter for letter, code in letter_to_code.items()}

    plaintext = None
    start = None
    eligible_starts = tuple(position for position in corpus_word_starts(split)
                            if position <= len(source) - RAW_LENGTH)
    for _ in range(max_attempts):
        candidate_start = eligible_starts[rng.below(len(eligible_starts))]
        candidate = exact_length_passage(source, candidate_start, letter_to_code)
        if candidate is not None:
            plaintext = candidate
            start = candidate_start
            break
    if plaintext is None or start is None:
        raise RuntimeError("could not construct exact-570 fixture")
    raw = encode_plaintext(plaintext, letter_to_code)
    order = rng.permutation(width)
    observed = Geometry(RAW_LENGTH, width).encrypt(raw, order)
    return {
        "width": width,
        "pair": list(pair),
        "fixture_index": fixture_index,
        "board_mode": board_mode,
        "split": split,
        "source_start": start,
        "plaintext": plaintext,
        "plaintext_length": len(plaintext),
        "letter_to_code": letter_to_code,
        "order": order,
        "raw": raw,
        "observed": observed,
        "raw_sha256": hashlib.sha256(raw.encode("ascii")).hexdigest(),
    }


def verify_fixture(fixture: dict) -> None:
    pair = tuple(fixture["pair"])
    geometry = Geometry(RAW_LENGTH, fixture["width"])
    restored = geometry.decrypt(fixture["observed"], fixture["order"])
    assert restored == fixture["raw"]
    assert len(restored) == RAW_LENGTH
    assert sorted(restored) == sorted(fixture["observed"])
    board = fixture["letter_to_code"]
    assert len(board) == 25 and len(set(board.values())) == 25
    assert set(board) == set(LETTER_ALPHABET)
    decoded = decode_raw(restored, pair, {code: letter for letter, code in board.items()})
    assert decoded == fixture["plaintext"]
    assert "J" not in decoded


def transition_matrix(tokens: tuple[str, ...], pair: tuple[str, str]) -> np.ndarray:
    code_to_index = {code: index for index, code in enumerate(slot_codes(pair))}
    matrix = np.zeros((25, 25), dtype=np.float64)
    for left, right in zip(tokens, tokens[1:]):
        matrix[code_to_index[left], code_to_index[right]] += 1.0
    total = float(matrix.sum())
    if total:
        matrix /= total
    return matrix


def spectral_features(matrix: np.ndarray) -> np.ndarray:
    """Permutation-invariant features of a directed transition graph."""
    symmetric = (matrix + matrix.T) / 2.0
    antisymmetric = (matrix - matrix.T) / 2.0
    parts = (
        np.linalg.svd(matrix, compute_uv=False),
        np.linalg.eigvalsh(symmetric),
        np.linalg.svd(antisymmetric, compute_uv=False),
        matrix.sum(axis=0),
        matrix.sum(axis=1),
    )
    normalized = []
    for part in parts:
        ordered = np.sort(part)[::-1]
        normalized.append(ordered / (np.linalg.norm(ordered) + 1e-12))
    return np.concatenate(normalized)


@dataclass(frozen=True)
class SpectralModel:
    target: np.ndarray

    @classmethod
    def from_training_corpus(cls) -> "SpectralModel":
        letter_to_index = {letter: index for index, letter in enumerate(LETTER_ALPHABET)}
        sequence = tuple(letter_to_index[letter] for letter in corpus_splits()["train"])
        matrix = np.zeros((25, 25), dtype=np.float64)
        for left, right in zip(sequence, sequence[1:]):
            matrix[left, right] += 1.0
        matrix /= matrix.sum()
        return cls(spectral_features(matrix))

    def score_restored_raw(self, raw: str, pair: tuple[str, str]) -> float | None:
        tokens = segment_raw(raw, pair)
        if tokens is None:
            return None
        difference = spectral_features(transition_matrix(tokens, pair)) - self.target
        return -float(np.dot(difference, difference))

    def score_order(self, observed: str, width: int, order,
                    pair: tuple[str, str]) -> float | None:
        raw = Geometry(len(observed), width).decrypt(observed, order)
        return self.score_restored_raw(raw, pair)


def enumerate_orders_by_spectral(observed: str, width: int,
                                 pair: tuple[str, str], model: SpectralModel,
                                 keep: int | None = None) -> dict:
    """Exact small-width order enumeration with deterministic tie-breaking."""
    if width > 9:
        raise ValueError("exact development enumerator is limited to width <= 9")
    if keep is not None and keep <= 0:
        raise ValueError("keep must be positive")
    ranked = []
    invalid = 0
    for order in itertools.permutations(range(width)):
        score = model.score_order(observed, width, order, pair)
        if score is None:
            invalid += 1
        else:
            ranked.append((score, order))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    selected = ranked if keep is None else ranked[:keep]
    return {
        "width": width,
        "pair": list(pair),
        "orders_total": math.factorial(width),
        "valid_orders": len(ranked),
        "invalid_segmentations": invalid,
        "shortlist": [
            {"score": score, "order": list(order)}
            for score, order in selected
        ],
    }


def random_order_rank(fixture: dict, model: SpectralModel, samples: int,
                      seed: int) -> dict:
    pair = tuple(fixture["pair"])
    planted = model.score_order(fixture["observed"], fixture["width"],
                                fixture["order"], pair)
    assert planted is not None
    rng = PCG32(seed)
    exceedances = 0
    invalid = 0
    for _ in range(samples):
        score = model.score_order(fixture["observed"], fixture["width"],
                                  rng.permutation(fixture["width"]), pair)
        if score is None:
            invalid += 1
        elif score >= planted:
            exceedances += 1
    return {
        "planted_score": planted,
        "samples": samples,
        "tie_inclusive_exceedances": exceedances,
        "invalid_segmentations": invalid,
    }


def enumerate_pair_orders_by_spectral(observed: str, width: int,
                                       model: SpectralModel,
                                       keep: int | None = None) -> dict:
    """Rank every escape-pair/order tuple without solving any board.

    This measures whether the cheap substitution-invariant statistic can
    retain the planted joint hypothesis before expensive board annealing.
    """
    if width > EXHAUSTIVE_MAX_WIDTH:
        raise ValueError(
            f"joint exact enumeration is limited to width <= {EXHAUSTIVE_MAX_WIDTH}"
        )
    if keep is not None and keep <= 0:
        raise ValueError("keep must be positive")
    ranked = []
    invalid = 0
    for pair_index, pair in enumerate(ESCAPE_PAIRS):
        result = enumerate_orders_by_spectral(observed, width, pair, model, keep=None)
        invalid += result["invalid_segmentations"]
        ranked.extend(
            (entry["score"], pair_index, tuple(entry["order"]))
            for entry in result["shortlist"]
        )
    ranked.sort(key=lambda item: (-item[0], item[1], item[2]))
    selected = ranked if keep is None else ranked[:keep]
    return {
        "width": width,
        "hypotheses_total": len(ESCAPE_PAIRS) * math.factorial(width),
        "valid_hypotheses": len(ranked),
        "invalid_segmentations": invalid,
        "shortlist": [
            {
                "score": score,
                "pair_index": pair_index,
                "pair": list(ESCAPE_PAIRS[pair_index]),
                "order": list(order),
            }
            for score, pair_index, order in selected
        ],
    }


def planted_joint_spectral_rank(fixture: dict, model: SpectralModel) -> dict:
    """Return the one-based rank of a fixture's planted pair/order tuple."""
    ranked = enumerate_pair_orders_by_spectral(
        fixture["observed"], fixture["width"], model, keep=None
    )
    planted_pair_index = ESCAPE_PAIRS.index(tuple(fixture["pair"]))
    planted_order = list(fixture["order"])
    for rank, entry in enumerate(ranked["shortlist"], start=1):
        if entry["pair_index"] == planted_pair_index and entry["order"] == planted_order:
            return {
                "rank": rank,
                "score": entry["score"],
                "valid_hypotheses": ranked["valid_hypotheses"],
                "hypotheses_total": ranked["hypotheses_total"],
                "invalid_segmentations": ranked["invalid_segmentations"],
            }
    raise AssertionError("planted pair/order was not a valid joint hypothesis")


def run_joint_rank_batch(widths: tuple[int, ...], fixtures_per_cell: int,
                         fixture_index_start: int, pair_index: int = 0,
                         board_modes: tuple[str, ...] = BOARD_MODES,
                         seed: int = SEED_DEV, split: str = "dev") -> dict:
    """Board-free development survey of planted joint spectral ranks."""
    if split != "dev":
        raise ValueError("joint rank scoping is development-only before lock")
    if fixtures_per_cell <= 0:
        raise ValueError("fixtures_per_cell must be positive")
    model = SpectralModel.from_training_corpus()
    cells = []
    for board_mode in board_modes:
        for width in widths:
            records = []
            for offset in range(fixtures_per_cell):
                fixture_index = fixture_index_start + offset
                fixture = make_fixture(
                    width, pair_index, fixture_index, seed=seed,
                    board_mode=board_mode, split=split,
                )
                rank = planted_joint_spectral_rank(fixture, model)
                records.append({
                    "fixture_index": fixture_index,
                    "rank": rank["rank"],
                    "valid_hypotheses": rank["valid_hypotheses"],
                    "invalid_segmentations": rank["invalid_segmentations"],
                })
            ranks = [record["rank"] for record in records]
            cells.append({
                "board_mode": board_mode,
                "width": width,
                "fixture_count": fixtures_per_cell,
                "minimum_rank": min(ranks),
                "median_rank": float(np.median(ranks)),
                "maximum_rank": max(ranks),
                "within_1536": sum(rank <= 1536 for rank in ranks),
                "records": records,
            })
    return {
        "phase": "484A",
        "status": "informal_joint_rank_dev_scoping_not_frozen",
        "faed_scored": False,
        "fixture_split": split,
        "pair_index": pair_index,
        "widths": list(widths),
        "board_modes": list(board_modes),
        "fixtures_per_cell": fixtures_per_cell,
        "fixture_index_start": fixture_index_start,
        "cells": cells,
    }


def run_joint_tail_batch(fixture_specs=JOINT_TAIL_FIXTURES,
                         joint_keep: int = 1536, board_restarts: int = 2,
                         board_iters: int = 6000, seed: int = SEED_DEV) -> dict:
    """End-to-end blind development solve of preselected rank-tail fixtures."""
    model = SpectralModel.from_training_corpus()
    quad, _ = load_language_model()
    records = []
    for board_mode, width, fixture_index in fixture_specs:
        fixture = make_fixture(
            width, 0, fixture_index, seed=seed,
            board_mode=board_mode, split="dev",
        )
        result = solve_fixture_joint_pairs(
            fixture, model, quad, joint_keep=joint_keep,
            board_restarts=board_restarts, board_iters=board_iters,
            seed=derive_seed(seed, width, fixture_index),
        )
        records.append({
            "board_mode": board_mode,
            "fixture_index": fixture_index,
            **result,
        })
    return {
        "phase": "484A",
        "status": "informal_joint_tail_dev_scoping_not_frozen",
        "faed_scored": False,
        "fixture_split": "dev",
        "budgets": {
            "joint_keep": joint_keep,
            "board_restarts": board_restarts,
            "board_iters": board_iters,
            "board_t0": 20.0,
            "board_t1": 1.0,
        },
        "joint_recovery_count": sum(record["joint_recovery"] for record in records),
        "fixture_count": len(records),
        "records": records,
    }


def load_language_model(path: Path = QUADGRAM_FILE) -> tuple[np.ndarray, float]:
    """25-letter (J merged into I) quadgram log10-probability table, built by
    folding the standard 26-letter frozen quadgram counts down to this
    project's 25-slot alphabet."""
    n = len(LETTER_ALPHABET)
    letter_to_index = {letter: index for index, letter in enumerate(LETTER_ALPHABET)}
    accumulated = np.zeros(n ** 4, dtype=np.float64)
    total = 0
    with open(path) as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            quad, count = line.split()
            count = int(count)
            total += count
            mapped = quad.replace("J", "I")
            indices = [letter_to_index[letter] for letter in mapped]
            key = ((indices[0] * n + indices[1]) * n + indices[2]) * n + indices[3]
            accumulated[key] += count
    floor = math.log10(0.01 / total)
    table = np.full(n ** 4, floor, dtype=np.float64)
    nonzero = accumulated > 0
    table[nonzero] = np.log10(accumulated[nonzero] / total)
    return table, floor


def score_indices(idx: np.ndarray, quad: np.ndarray) -> float:
    """Sum of log10 quadgram probabilities over every sliding window of a
    25-letter index array (values 0..24)."""
    n = len(LETTER_ALPHABET)
    if idx.shape[0] < 4:
        return 0.0
    keys = ((idx[:-3] * n + idx[1:-2]) * n + idx[2:-1]) * n + idx[3:]
    return float(quad[keys].sum())


def kendall_tau(perm_a, perm_b) -> float:
    width = len(perm_a)
    rank_a = np.empty(width, dtype=np.int64)
    rank_b = np.empty(width, dtype=np.int64)
    rank_a[np.asarray(perm_a)] = np.arange(width)
    rank_b[np.asarray(perm_b)] = np.arange(width)
    concordant = 0
    for i in range(width):
        for j in range(i + 1, width):
            concordant += 1 if (rank_a[i] - rank_a[j]) * (rank_b[i] - rank_b[j]) > 0 else -1
    denominator = width * (width - 1) / 2
    return concordant / denominator if denominator else 1.0


def anneal_board(token_slots: np.ndarray, quad: np.ndarray, rng: PCG32, iters: int,
                 t0: float, t1: float, key0: np.ndarray | None = None) -> tuple[np.ndarray, float]:
    """Simulated annealing over 25-slot board swaps, geometric cooling from
    t0 to t1 over exactly `iters` proposals. Mirrors Phase 477A's anneal_key."""
    n = len(LETTER_ALPHABET)
    key = key0.copy() if key0 is not None else np.array(rng.permutation(n), dtype=np.int64)

    def score(candidate: np.ndarray) -> float:
        return score_indices(candidate[token_slots], quad)

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


MIN_DECODED_LENGTH = math.ceil(RAW_LENGTH / 2)
EXHAUSTIVE_MAX_WIDTH = 6


def normalized_quadgram_score(quadgram_total: float, decoded_length: int) -> float:
    """Per-quadgram-window average, so candidate orders that happen to decode
    to fewer tokens (and therefore sum fewer, less-negative log-probability
    windows) are not favoured purely for being shorter."""
    return quadgram_total / max(1, decoded_length - 3)


def solve_fixture(fixture: dict, model: SpectralModel, quad: np.ndarray,
                  shortlist_keep: int = 16, exhaustive: bool = False,
                  board_restarts: int = 2, board_iters: int = 6000,
                  board_t0: float = 20.0, board_t1: float = 1.0, seed: int = 0) -> dict:
    """Escape pair is taken from the fixture (not searched). Order candidates
    come from the exact spectral shortlist, or (if ``exhaustive``) from every
    valid order at this width; the board is annealed independently per
    candidate order, and the candidate with the highest length-normalized
    quadgram score wins, subject to ``MIN_DECODED_LENGTH``. This does not
    implement blind escape-pair recovery (Phase 484A step 6)."""
    width = fixture["width"]
    if exhaustive:
        if width > EXHAUSTIVE_MAX_WIDTH:
            raise ValueError(
                f"exhaustive mode is only budget-approved for width <= {EXHAUSTIVE_MAX_WIDTH}"
            )
        shortlist_keep = math.factorial(width)
    pair = tuple(fixture["pair"])
    geometry = Geometry(RAW_LENGTH, width)
    codes = slot_codes(pair)
    code_to_slot = {code: index for index, code in enumerate(codes)}
    shortlist = enumerate_orders_by_spectral(fixture["observed"], width, pair, model, shortlist_keep)

    candidates = []
    for rank, entry in enumerate(shortlist["shortlist"]):
        order = entry["order"]
        raw = geometry.decrypt(fixture["observed"], order)
        segmented = segment_raw(raw, pair)
        if segmented is None:
            continue
        decoded_length = len(segmented)
        token_slots = np.array([code_to_slot[code] for code in segmented], dtype=np.int64)
        best_key, best_score = None, -math.inf
        for restart in range(board_restarts):
            # Key randomness to the permutation, not its mutable shortlist rank.
            rng = PCG32(derive_seed(seed, width, *order, restart))
            key, score = anneal_board(token_slots, quad, rng, board_iters, board_t0, board_t1)
            if score > best_score:
                best_key, best_score = key, score
        normalizer = max(1, len(token_slots) - 3)
        candidates.append({
            "rank": rank,
            "spectral_score": entry["score"],
            "order": order,
            "decoded_length": decoded_length,
            "quadgram_score": best_score,
            "normalized_score": normalized_quadgram_score(best_score, decoded_length),
            "key": best_key,
        })

    if not candidates:
        return {
            "width": width,
            "pair": list(pair),
            "shortlist_size": len(shortlist["shortlist"]),
            "valid_candidates": 0,
            "solved": False,
        }

    eligible = [c for c in candidates if c["decoded_length"] >= MIN_DECODED_LENGTH]
    if not eligible:
        return {
            "width": width,
            "pair": list(pair),
            "shortlist_size": len(shortlist["shortlist"]),
            "valid_candidates": len(candidates),
            "solved": False,
            "rejected_reason": "no_candidate_met_min_decoded_length",
        }

    winner = max(eligible, key=lambda candidate: candidate["normalized_score"])
    winner_raw = geometry.decrypt(fixture["observed"], winner["order"])
    winner_code_to_letter = {
        codes[slot]: LETTER_ALPHABET[int(winner["key"][slot])] for slot in range(25)
    }
    decoded = decode_raw(winner_raw, pair, winner_code_to_letter)
    truth_plaintext = fixture["plaintext"]
    true_code_to_letter = {code: letter for letter, code in fixture["letter_to_code"].items()}

    overlap = min(len(decoded), len(truth_plaintext)) if decoded is not None else 0
    matches = sum(decoded[i] == truth_plaintext[i] for i in range(overlap)) if overlap else 0

    return {
        "width": width,
        "pair": list(pair),
        "shortlist_size": len(shortlist["shortlist"]),
        "valid_candidates": len(candidates),
        "eligible_candidates": len(eligible),
        "solved": True,
        "exact_order_recovery": list(winner["order"]) == list(fixture["order"]),
        "kendall_tau": kendall_tau(fixture["order"], winner["order"]),
        "board_accuracy": sum(
            winner_code_to_letter[code] == true_code_to_letter[code] for code in codes
        ) / 25,
        "decoded_length": len(decoded) if decoded is not None else None,
        "true_length": len(truth_plaintext),
        "decoded_length_error": (
            len(decoded) - len(truth_plaintext) if decoded is not None else None
        ),
        "plaintext_char_accuracy": matches / len(truth_plaintext) if decoded is not None else 0.0,
        "winner_rank_in_shortlist": winner["rank"],
        "winner_quadgram_score": winner["quadgram_score"],
        "winner_normalized_score": winner["normalized_score"],
    }


def solve_fixture_joint_pairs(fixture: dict, model: SpectralModel, quad: np.ndarray,
                              joint_keep: int, board_restarts: int = 2,
                              board_iters: int = 6000, board_t0: float = 20.0,
                              board_t1: float = 1.0, seed: int = 0) -> dict:
    """Solve a synthetic fixture without being given its escape pair.

    The substitution-invariant statistic ranks all 36-pair/order hypotheses;
    the expensive board solver runs only on the first ``joint_keep`` valid
    hypotheses. This is development machinery, not yet a frozen gate.
    """
    width = fixture["width"]
    ranked = enumerate_pair_orders_by_spectral(
        fixture["observed"], width, model, keep=joint_keep
    )
    geometry = Geometry(RAW_LENGTH, width)
    candidates = []
    for rank, entry in enumerate(ranked["shortlist"]):
        pair_index = entry["pair_index"]
        pair = ESCAPE_PAIRS[pair_index]
        codes = slot_codes(pair)
        code_to_slot = {code: index for index, code in enumerate(codes)}
        raw = geometry.decrypt(fixture["observed"], entry["order"])
        segmented = segment_raw(raw, pair)
        if segmented is None:
            continue
        decoded_length = len(segmented)
        token_slots = np.array([code_to_slot[code] for code in segmented], dtype=np.int64)
        best_key, best_score = None, -math.inf
        for restart in range(board_restarts):
            rng = PCG32(derive_seed(seed, width, pair_index, *entry["order"], restart))
            key, score = anneal_board(
                token_slots, quad, rng, board_iters, board_t0, board_t1
            )
            if score > best_score:
                best_key, best_score = key, score
        candidates.append({
            "rank": rank,
            "pair_index": pair_index,
            "pair": pair,
            "order": entry["order"],
            "decoded_length": decoded_length,
            "quadgram_score": best_score,
            "normalized_score": normalized_quadgram_score(best_score, decoded_length),
            "key": best_key,
        })
    eligible = [c for c in candidates if c["decoded_length"] >= MIN_DECODED_LENGTH]
    if not eligible:
        return {"solved": False, "rejected_reason": "no_candidate_met_min_decoded_length"}
    winner = max(eligible, key=lambda candidate: candidate["normalized_score"])
    codes = slot_codes(winner["pair"])
    code_to_letter = {
        codes[slot]: LETTER_ALPHABET[int(winner["key"][slot])] for slot in range(25)
    }
    raw = geometry.decrypt(fixture["observed"], winner["order"])
    decoded = decode_raw(raw, winner["pair"], code_to_letter)
    truth = fixture["plaintext"]
    overlap = min(len(decoded), len(truth)) if decoded is not None else 0
    matches = sum(decoded[i] == truth[i] for i in range(overlap)) if overlap else 0
    true_pair = tuple(fixture["pair"])
    pair_recovered = winner["pair"] == true_pair
    board_accuracy = 0.0
    if pair_recovered:
        true_code_to_letter = {
            code: letter for letter, code in fixture["letter_to_code"].items()
        }
        board_accuracy = sum(
            code_to_letter[code] == true_code_to_letter[code] for code in codes
        ) / 25
    planted_pair_index = ESCAPE_PAIRS.index(true_pair)
    planted_in_shortlist = any(
        entry["pair_index"] == planted_pair_index
        and entry["order"] == list(fixture["order"])
        for entry in ranked["shortlist"]
    )
    return {
        "solved": True,
        "width": width,
        "joint_keep": joint_keep,
        "valid_hypotheses": ranked["valid_hypotheses"],
        "planted_in_shortlist": planted_in_shortlist,
        "escape_pair_recovery": pair_recovered,
        "exact_order_recovery": winner["order"] == list(fixture["order"]),
        "joint_recovery": pair_recovered and winner["order"] == list(fixture["order"]),
        "winner_pair": list(winner["pair"]),
        "winner_order": winner["order"],
        "winner_rank": winner["rank"],
        "kendall_tau": kendall_tau(fixture["order"], winner["order"]),
        "board_accuracy": board_accuracy,
        "plaintext_char_accuracy": matches / len(truth) if decoded is not None else 0.0,
        "decoded_length": len(decoded) if decoded is not None else None,
        "true_length": len(truth),
        "winner_normalized_score": winner["normalized_score"],
    }


def run_dev_batch(widths: tuple[int, ...], fixtures_per_width: int = 10,
                  fixture_index_start: int = 0, shortlist_keep: int = 16,
                  exhaustive: bool = False, board_restarts: int = 2,
                  board_iters: int = 6000, board_t0: float = 20.0,
                  board_t1: float = 1.0, pair_index: int = 0,
                  board_modes: tuple[str, ...] = ("vic_profile",),
                  seed: int = SEED_DEV, split: str = "dev") -> dict:
    """Informal scoping run over development fixtures only. Not a frozen gate:
    Phase 484A's protocol freezes no solver family, budget, or threshold yet.
    ``exhaustive`` is the only way to get every-valid-order board-solving (no
    silent shortlist fallback); it is recorded in the output so a result file
    is self-describing about which mode produced it."""
    if exhaustive and any(width > EXHAUSTIVE_MAX_WIDTH for width in widths):
        raise ValueError(
            f"exhaustive mode is only budget-approved for width <= {EXHAUSTIVE_MAX_WIDTH}"
        )
    if split not in FIXTURE_SPLITS:
        raise ValueError(f"unknown fixture split: {split}")
    model = SpectralModel.from_training_corpus()
    quad, _ = load_language_model()
    cells = []
    for board_mode in board_modes:
        for width in widths:
            records = []
            for offset in range(fixtures_per_width):
                fixture_index = fixture_index_start + offset
                fixture = make_fixture(width=width, pair_index=pair_index,
                                       fixture_index=fixture_index, seed=seed,
                                       board_mode=board_mode, split=split)
                result = solve_fixture(fixture, model, quad, shortlist_keep=shortlist_keep,
                                       exhaustive=exhaustive, board_restarts=board_restarts,
                                       board_iters=board_iters, board_t0=board_t0,
                                       board_t1=board_t1,
                                       seed=derive_seed(seed, width, fixture_index))
                records.append(result)
            solved = [r for r in records if r["solved"]]
            cells.append({
                "board_mode": board_mode,
                "width": width,
                "fixture_count": fixtures_per_width,
                "fixture_index_start": fixture_index_start,
                "exact_order_recovery": sum(r["exact_order_recovery"] for r in solved),
                "mean_kendall_tau": sum(r["kendall_tau"] for r in solved) / len(solved) if solved else None,
                "mean_board_accuracy": sum(r["board_accuracy"] for r in solved) / len(solved) if solved else None,
                "mean_plaintext_char_accuracy": (
                    sum(r["plaintext_char_accuracy"] for r in solved) / len(solved) if solved else None
                ),
                "records": records,
            })
    return {
        "phase": "484A",
        "status": "informal_dev_scoping_not_frozen",
        "faed_scored": False,
        "fixture_split": split,
        "board_modes": list(board_modes),
        "pair_index": pair_index,
        "shortlist_mode": "exhaustive" if exhaustive else "shortlist",
        "budgets": {
            "fixtures_per_width": fixtures_per_width,
            "fixture_index_start": fixture_index_start,
            "shortlist_keep": None if exhaustive else shortlist_keep,
            "board_restarts": board_restarts,
            "board_iters": board_iters,
            "board_t0": board_t0,
            "board_t1": board_t1,
        },
        "cells": cells,
    }


def self_test() -> None:
    assert EXACT_WIDTHS == (2, 3, 5, 6, 10, 15, 19, 30, 38)
    sample = (NINE_SYMBOLS * 64)[:RAW_LENGTH]
    for width in WIDTHS:
        geometry = Geometry(RAW_LENGTH, width)
        order = list(reversed(range(width)))
        encrypted = geometry.encrypt(sample, order)
        assert geometry.decrypt(encrypted, order) == sample
        assert sorted(encrypted) == sorted(sample)
    for pair in ESCAPE_PAIRS:
        codes = slot_codes(pair)
        assert len(codes) == 25 and len(set(codes)) == 25
        assert segment_raw("".join(codes), pair) == codes
        assert segment_raw(pair[0], pair) is None
    for index in (0, 7, 21, 35):
        fixture = make_fixture(width=(7, 15, 19, 38)[index // 10], pair_index=index)
        verify_fixture(fixture)


if __name__ == "__main__":
    import sys

    self_test()
    print("self-test: ok")
    if len(sys.argv) > 1 and sys.argv[1] == "dev-batch":
        exhaustive = "--exhaustive" in sys.argv
        both_pools = "--both-pools" in sys.argv
        board_modes = BOARD_MODES if both_pools else ("vic_profile",)
        fixture_index_start = 0
        for arg in sys.argv:
            if arg.startswith("--start="):
                fixture_index_start = int(arg.split("=", 1)[1])
        if not exhaustive:
            raise SystemExit(
                "dev-batch requires an explicit mode flag; pass --exhaustive "
                "(the only mode currently budget-approved for widths 2,3,5,6)"
            )
        result = run_dev_batch(widths=(2, 3, 5, 6), exhaustive=exhaustive,
                               board_modes=board_modes,
                               fixture_index_start=fixture_index_start)
        out_path = SCRIPT_DIR / "phase484a_dev_batch_result.json"
        out_path.write_text(json.dumps(result, indent=2))
        for cell in result["cells"]:
            print(f"board_mode={cell['board_mode']} width={cell['width']} "
                  f"exact_order={cell['exact_order_recovery']}/{cell['fixture_count']} "
                  f"mean_board_acc={cell['mean_board_accuracy']} "
                  f"mean_plaintext_acc={cell['mean_plaintext_char_accuracy']}")
        print(f"wrote {out_path}")
    elif len(sys.argv) > 1 and sys.argv[1] == "joint-rank-dev":
        fixture_index_start = 25
        fixtures_per_cell = 20
        for arg in sys.argv:
            if arg.startswith("--start="):
                fixture_index_start = int(arg.split("=", 1)[1])
            elif arg.startswith("--count="):
                fixtures_per_cell = int(arg.split("=", 1)[1])
        result = run_joint_rank_batch(
            widths=(6,), fixtures_per_cell=fixtures_per_cell,
            fixture_index_start=fixture_index_start,
        )
        out_path = SCRIPT_DIR / "phase484a_joint_rank_batch_result.json"
        out_path.write_text(json.dumps(result, indent=2))
        for cell in result["cells"]:
            print(f"board_mode={cell['board_mode']} width={cell['width']} "
                  f"median_rank={cell['median_rank']} max_rank={cell['maximum_rank']} "
                  f"within_1536={cell['within_1536']}/{cell['fixture_count']}")
        print(f"wrote {out_path}")
    elif len(sys.argv) > 1 and sys.argv[1] == "joint-tail-dev":
        result = run_joint_tail_batch()
        out_path = SCRIPT_DIR / "phase484a_joint_tail_batch_result.json"
        out_path.write_text(json.dumps(result, indent=2))
        for record in result["records"]:
            print(f"board_mode={record['board_mode']} "
                  f"fixture={record['fixture_index']} "
                  f"joint_recovery={record['joint_recovery']} "
                  f"winner_rank={record['winner_rank']}", flush=True)
        print(f"wrote {out_path}")
