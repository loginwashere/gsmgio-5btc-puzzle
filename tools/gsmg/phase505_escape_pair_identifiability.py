#!/usr/bin/env python3
"""Phase 505A: synthetic known-order escape-pair identifiability ceiling.

The module deliberately never imports ``data`` or FAED.  ``--run-ceiling``
requires the existing unrestricted full-board GPU server; ``--self-test`` is
CPU-only and does not execute the expensive 72 x 36 matrix.
"""
from __future__ import annotations

import argparse
import ast
import collections
import hashlib
import json
import time
from functools import lru_cache
from pathlib import Path

import numpy as np

import phase484a_raw_symbol_vic_solver as base
import phase484q_blind_joint_width19_solver as joint
import phase491_raw_histogram_fixture as rawonly


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
PROTOCOL = (REPO_ROOT / "doc" / "Brainstorms" /
            "2026-09-14 - Phase 505 Escape-Pair Identifiability Protocol.md")
DEFAULT_OUTPUT = REPO_ROOT / "_work" / "phase505" / "ceiling_result.json"
DEFAULT_MANIFEST = SCRIPT_DIR / "phase505_fixture_manifest.json"
LOCK_PATH = SCRIPT_DIR / "phase505_execution_lock.json"

WIDTH, ROWS = 19, 30
ALL_PAIRS = tuple(base.ESCAPE_PAIRS)
FIXTURE_INDICES = (0, 1)
SPLIT = "dev"
PROFILE_SEED = 0x505A001
ORDER_SEED = 0x505A002
ANNEAL_SEED = 0x505A003
RESTARTS = 8
ITERATIONS = 20000
TOP1_REQUIRED = 65
TOP3_REQUIRED = 72
MAX_CONSTRUCTION_CANDIDATES = 200
MAX_EDIT_FRACTION = 0.21


class FixtureEligibilityError(ValueError):
    """A candidate failed a frozen, pre-solver construction gate."""


def canonical_raw_multiset() -> list[str]:
    values = [symbol for symbol in base.NINE_SYMBOLS
              for _ in range(rawonly.RAW_COUNTS[symbol])]
    if len(values) != WIDTH * ROWS:
        raise AssertionError("frozen raw histogram does not total 570")
    return values


@lru_cache(maxsize=None)
def sampled_token_profile(pair_index: int, fixture_index: int,
                          split: str = SPLIT) -> dict:
    if not 0 <= pair_index < len(ALL_PAIRS):
        raise ValueError("pair index out of range")
    if fixture_index < 0:
        raise ValueError("fixture index must be nonnegative")
    if split not in base.FIXTURE_SPLITS:
        raise ValueError("unknown corpus split")
    pair = ALL_PAIRS[pair_index]
    split_index = base.FIXTURE_SPLITS.index(split)
    rng = base.PCG32(base.derive_seed(
        PROFILE_SEED, split_index, pair_index, fixture_index))
    values = canonical_raw_multiset()
    for attempt in range(rawonly.MAX_SHUFFLES):
        rng.shuffle(values)
        raw = "".join(values)
        tokens = base.segment_raw(raw, pair)
        if tokens is None:
            continue
        counts = collections.Counter(tokens)
        ordered = {code: counts[code] for code in base.slot_codes(pair)}
        return {
            "pair_index": pair_index,
            "pair": list(pair),
            "shuffle_attempt": attempt,
            "tokens": tokens,
            "token_counts": ordered,
            "token_count": len(tokens),
            "single_count": sum(len(token) == 1 for token in tokens),
            "profile_sha256": hashlib.sha256(json.dumps(
                ordered, sort_keys=True, separators=(",", ":")
            ).encode("ascii")).hexdigest(),
        }
    raise RuntimeError("could not sample a valid latent token profile")


def unrestricted_board_for_passage(
        passage: str, pair: tuple[str, str],
        token_counts: dict[str, int]) -> dict[str, str]:
    passage_counts = collections.Counter(passage)
    ranked_letters = sorted(base.LETTER_ALPHABET,
                            key=lambda x: (-passage_counts[x], x))
    ranked_codes = sorted(base.slot_codes(pair),
                          key=lambda x: (-token_counts[x], x))
    return dict(zip(ranked_letters, ranked_codes))


def final_board_for_passage(passage: str, pair: tuple[str, str],
                            token_counts: dict[str, int]):
    board = unrestricted_board_for_passage(passage, pair, token_counts)
    target = {letter: token_counts[code] for letter, code in board.items()}
    passage_counts = collections.Counter(passage)
    edits = sum(abs(passage_counts[letter] - target[letter])
                for letter in base.LETTER_ALPHABET) // 2
    common, _ = rawonly.training_groups()
    singles = {letter for letter, code in board.items() if len(code) == 1}
    partition_distance = len(set(common) - singles)
    return board, target, edits, partition_distance


def select_passage(pair_index: int, fixture_index: int, split: str,
                   token_counts: dict[str, int]):
    pair = ALL_PAIRS[pair_index]
    source = base.corpus_splits()[split]
    length = sum(token_counts.values())
    left, right = rawonly.source_region(split, fixture_index)
    candidates = []
    for start in base.corpus_word_starts(split):
        if start < left or start + length > right:
            continue
        passage = source[start:start + length]
        board, target, edits, partition_distance = final_board_for_passage(
            passage, pair, token_counts)
        candidates.append((edits, start, passage, board, target,
                           partition_distance))
    if not candidates:
        raise RuntimeError("source region contains no complete passage")
    return min(candidates, key=lambda record: (record[0], record[1]))


def build_candidate(pair_index: int, candidate_index: int,
                    split: str = SPLIT) -> dict:
    profile = sampled_token_profile(pair_index, candidate_index, split)
    pair = ALL_PAIRS[pair_index]
    edits, start, source, board, target, partition_distance = select_passage(
        pair_index, candidate_index, split, profile["token_counts"])
    # Reject on the exact L1 edit count before performing the much more
    # expensive score-aware substitution placement.
    edit_fraction = edits / len(source)
    if edit_fraction > MAX_EDIT_FRACTION:
        raise FixtureEligibilityError(f"edit_fraction:{edit_fraction:.12f}")
    quad, _ = base.load_language_model()
    plaintext, actual_edits = rawonly.minimum_edit_plaintext(source, target, quad)
    if actual_edits != edits:
        raise AssertionError("minimum edit count changed during application")
    raw = base.encode_plaintext(plaintext, board)
    split_index = base.FIXTURE_SPLITS.index(split)
    order = base.PCG32(base.derive_seed(
        ORDER_SEED, split_index, pair_index, candidate_index)).permutation(WIDTH)
    observed = base.Geometry(len(raw), WIDTH).encrypt(raw, order)
    indices = np.asarray([base.LETTER_ALPHABET.index(x) for x in plaintext],
                         dtype=np.int64)
    normalized = base.score_indices(indices, quad) / max(1, len(indices) - 3)
    fixture = {
        "phase": "505A",
        "fixture_index": None,
        "construction_candidate_index": candidate_index,
        "true_pair_index": pair_index,
        "pair": list(pair),
        "split": split,
        "width": WIDTH,
        "board_mode": "raw_histogram_unrestricted_min_l1",
        "partition_distance": partition_distance,
        "source_region": list(rawonly.source_region(split, candidate_index)),
        "source_start": start,
        "source_plaintext": source,
        "plaintext": plaintext,
        "plaintext_length": len(plaintext),
        "minimum_edit_count": actual_edits,
        "edit_fraction": actual_edits / len(plaintext),
        "normalized_quadgram": normalized,
        "letter_to_code": board,
        "order": order,
        "raw": raw,
        "observed": observed,
        "raw_sha256": hashlib.sha256(raw.encode("ascii")).hexdigest(),
        "latent_profile_sha256": profile["profile_sha256"],
        "latent_token_count": profile["token_count"],
        "latent_single_count": profile["single_count"],
    }
    if fixture["normalized_quadgram"] < rawonly.MIN_NORMALIZED_QUADGRAM:
        raise FixtureEligibilityError(
            f"normalized_quadgram:{fixture['normalized_quadgram']:.12f}")
    return fixture


@lru_cache(maxsize=None)
def eligible_candidates(pair_index: int, split: str = SPLIT):
    accepted, rejected, used_regions = [], [], set()
    for candidate_index in range(MAX_CONSTRUCTION_CANDIDATES):
        try:
            fixture = build_candidate(pair_index, candidate_index, split)
        except FixtureEligibilityError as error:
            rejected.append({"construction_candidate_index": candidate_index,
                             "reason": str(error)})
            continue
        region = tuple(fixture["source_region"])
        if region in used_regions:
            rejected.append({"construction_candidate_index": candidate_index,
                             "reason": "source_region_reused"})
            continue
        fixture["fixture_index"] = len(accepted)
        verify_fixture(fixture)
        accepted.append(fixture)
        used_regions.add(region)
        if len(accepted) == len(FIXTURE_INDICES):
            return tuple(accepted), tuple(rejected)
    raise RuntimeError(
        f"pair {pair_index} lacks two eligible construction candidates")


def make_fixture(pair_index: int, fixture_index: int,
                 split: str = SPLIT) -> dict:
    if fixture_index not in FIXTURE_INDICES:
        raise ValueError("fixture index is outside the planned logical set")
    accepted, _ = eligible_candidates(pair_index, split)
    return dict(accepted[fixture_index])


def verify_fixture(fixture: dict) -> None:
    base.verify_fixture(fixture)
    pair = tuple(fixture["pair"])
    if pair != ALL_PAIRS[fixture["true_pair_index"]]:
        raise AssertionError("pair index metadata mismatch")
    if collections.Counter(fixture["raw"]) != collections.Counter(
            rawonly.RAW_COUNTS):
        raise AssertionError("fixture missed frozen raw histogram")
    if fixture["edit_fraction"] > MAX_EDIT_FRACTION:
        raise AssertionError("fixture exceeds edit-fraction gate")
    if fixture["normalized_quadgram"] < rawonly.MIN_NORMALIZED_QUADGRAM:
        raise AssertionError("fixture falls below language-quality gate")
    tokens = base.segment_raw(fixture["raw"], pair)
    if tokens is None or len(tokens) != fixture["plaintext_length"]:
        raise AssertionError("true-pair segmentation mismatch")
    common, _ = rawonly.training_groups()
    singles = {letter for letter, code in fixture["letter_to_code"].items()
               if len(code) == 1}
    if len(set(common) - singles) != fixture["partition_distance"]:
        raise AssertionError("partition-distance metadata mismatch")


def token_slots(raw: str, pair: tuple[str, str]) -> np.ndarray | None:
    tokens = base.segment_raw(raw, pair)
    if tokens is None:
        return None
    code_to_slot = {code: index for index, code in enumerate(
        base.slot_codes(pair))}
    return np.asarray([code_to_slot[token] for token in tokens],
                      dtype=np.int64)


def canonical_planted_board(fixture: dict) -> np.ndarray:
    pair = tuple(fixture["pair"])
    inverse = {code: letter for letter, code in
               fixture["letter_to_code"].items()}
    return np.asarray([
        base.LETTER_ALPHABET.index(inverse[code])
        for code in base.slot_codes(pair)
    ], dtype=np.uint8)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def expected_lock_payload() -> dict:
    dependencies = (base, joint, rawonly)
    return {
        "phase": "505A",
        "status": "execution_lock",
        "protocol_sha256": sha256_file(PROTOCOL),
        "script_sha256": sha256_file(Path(__file__)),
        "fixture_manifest_sha256": sha256_file(DEFAULT_MANIFEST),
        "dependencies_sha256": {
            str(Path(module.__file__).relative_to(REPO_ROOT)):
                sha256_file(Path(module.__file__))
            for module in dependencies
        },
        "full_board_binary_sha256": sha256_file(joint.FULL_BINARY),
        "pair_count": len(ALL_PAIRS),
        "fixture_indices": list(FIXTURE_INDICES),
        "split": SPLIT,
        "budgets": {"restarts": RESTARTS, "iterations": ITERATIONS,
                    "seed": ANNEAL_SEED},
        "gate": {"top1_required": TOP1_REQUIRED,
                 "top3_required": TOP3_REQUIRED,
                 "positive_median_gap_required": True},
    }


def verify_lock() -> dict:
    if not LOCK_PATH.is_file():
        raise RuntimeError("Phase-505A execution lock is absent")
    actual = json.loads(LOCK_PATH.read_text())
    expected = expected_lock_payload()
    if actual != expected:
        raise RuntimeError("Phase-505A execution lock mismatch")
    return actual


def rank_true_pair(records: list[dict], true_pair_index: int) -> dict:
    valid = [record for record in records if record["valid"]]
    ranked = sorted(valid, key=lambda record: (
        -record["normalized_score"], record["hypothesis_pair_index"]))
    for rank, record in enumerate(ranked, 1):
        record["rank"] = rank
    true = next(record for record in ranked
                if record["hypothesis_pair_index"] == true_pair_index)
    wrong = [record for record in ranked
             if record["hypothesis_pair_index"] != true_pair_index]
    return {
        "true_pair_rank": true["rank"],
        "true_pair_score": true["normalized_score"],
        "best_wrong_pair_score": wrong[0]["normalized_score"],
        "true_minus_best_wrong": (true["normalized_score"] -
                                  wrong[0]["normalized_score"]),
        "ranked_pair_indices": [record["hypothesis_pair_index"]
                                for record in ranked],
    }


def score_fixture(fixture: dict) -> dict:
    began = time.monotonic()
    rows, valid_indices = [], []
    for pair_index, pair in enumerate(ALL_PAIRS):
        slots = token_slots(fixture["raw"], pair)
        if slots is not None:
            rows.append(slots)
            valid_indices.append(pair_index)
    quad, _ = base.load_language_model()
    scores, boards, restarts = joint.gpu_full_multistart(
        joint.FULL_BINARY, rows, quad, RESTARTS, ITERATIONS, ANNEAL_SEED)
    records = [{
        "hypothesis_pair_index": pair_index,
        "hypothesis_pair": list(ALL_PAIRS[pair_index]),
        "valid": False,
        "decoded_length": None,
        "normalized_score": None,
        "best_restart": None,
        "true_board_accuracy": None,
    } for pair_index in range(len(ALL_PAIRS))]
    planted = canonical_planted_board(fixture)
    for row_index, pair_index in enumerate(valid_indices):
        is_true = pair_index == fixture["true_pair_index"]
        records[pair_index].update({
            "valid": True,
            "decoded_length": len(rows[row_index]),
            "normalized_score": float(scores[row_index]),
            "best_restart": int(restarts[row_index]),
            "true_board_accuracy": (float(np.mean(boards[row_index] == planted))
                                    if is_true else None),
        })
    ranked = rank_true_pair(records, fixture["true_pair_index"])
    return {
        "true_pair_index": fixture["true_pair_index"],
        "true_pair": fixture["pair"],
        "fixture_index": fixture["fixture_index"],
        "fixture_raw_sha256": fixture["raw_sha256"],
        "plaintext_length": fixture["plaintext_length"],
        "edit_fraction": fixture["edit_fraction"],
        "normalized_quadgram": fixture["normalized_quadgram"],
        "wall_seconds": time.monotonic() - began,
        **ranked,
        "pairs": records,
    }


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def planned_fixtures() -> list[dict]:
    return [make_fixture(pair_index, fixture_index, SPLIT)
            for pair_index in range(len(ALL_PAIRS))
            for fixture_index in FIXTURE_INDICES]


def validate_progress(progress: dict, fixtures: list[dict],
                      lock_sha256: str, manifest_sha256: str) -> list[dict]:
    expected_header = {
        "phase": "505A", "status": "in_progress", "total": len(fixtures),
        "execution_lock_sha256": lock_sha256,
        "fixture_manifest_sha256": manifest_sha256,
    }
    for key, value in expected_header.items():
        if progress.get(key) != value:
            raise RuntimeError(f"Phase-505A progress mismatch: {key}")
    records = progress.get("records")
    if not isinstance(records, list) or progress.get("completed") != len(records):
        raise RuntimeError("Phase-505A progress record count mismatch")
    if len(records) > len(fixtures):
        raise RuntimeError("Phase-505A progress exceeds fixture universe")
    for record, fixture in zip(records, fixtures):
        expected = {
            "true_pair_index": fixture["true_pair_index"],
            "true_pair": fixture["pair"],
            "fixture_index": fixture["fixture_index"],
            "fixture_raw_sha256": fixture["raw_sha256"],
        }
        if any(record.get(key) != value for key, value in expected.items()):
            raise RuntimeError("Phase-505A progress fixture sequence mismatch")
    return records


def progress_payload(records: list[dict], total: int,
                     lock_sha256: str, manifest_sha256: str) -> dict:
    return {
        "phase": "505A", "status": "in_progress",
        "execution_lock_sha256": lock_sha256,
        "fixture_manifest_sha256": manifest_sha256,
        "completed": len(records), "total": total,
        "first_fixture_projected_total_seconds":
            records[0]["wall_seconds"] * total if records else None,
        "records": records,
    }


def run_ceiling(output: Path = DEFAULT_OUTPUT) -> dict:
    verify_lock()
    output = Path(output)
    if output.exists():
        raise FileExistsError("refusing to overwrite Phase-505A result")
    progress_path = output.with_name("ceiling_progress.json")
    fixtures = planned_fixtures()
    lock_sha256 = sha256_file(LOCK_PATH)
    manifest_sha256 = sha256_file(DEFAULT_MANIFEST)
    records = []
    if progress_path.exists():
        records = validate_progress(json.loads(progress_path.read_text()),
                                    fixtures, lock_sha256, manifest_sha256)
    for fixture in fixtures[len(records):]:
        records.append(score_fixture(fixture))
        atomic_json(progress_path, progress_payload(
            records, len(fixtures), lock_sha256, manifest_sha256))
    top1 = sum(record["true_pair_rank"] == 1 for record in records)
    top3 = sum(record["true_pair_rank"] <= 3 for record in records)
    gaps = sorted(record["true_minus_best_wrong"] for record in records)
    median_gap = (gaps[35] + gaps[36]) / 2
    result = {
        "phase": "505A",
        "status": "known_order_pair_ceiling_complete",
        "faed_scored": False,
        "holdout_consumed": False,
        "execution_lock_sha256": lock_sha256,
        "fixture_manifest_sha256": manifest_sha256,
        "pair_count": len(ALL_PAIRS),
        "fixture_indices": list(FIXTURE_INDICES),
        "fixture_count": len(records),
        "budgets": {"restarts": RESTARTS, "iterations": ITERATIONS,
                    "seed": ANNEAL_SEED},
        "gate": {"top1_required": TOP1_REQUIRED,
                 "top3_required": TOP3_REQUIRED,
                 "positive_median_gap_required": True},
        "top1": top1,
        "top3": top3,
        "median_true_minus_best_wrong": median_gap,
        "gate_passed": (top1 >= TOP1_REQUIRED and
                        top3 >= TOP3_REQUIRED and median_gap > 0),
        "records": records,
    }
    atomic_json(output, result)
    return result


def fixture_manifest() -> dict:
    records = []
    rejections = []
    for pair_index in range(len(ALL_PAIRS)):
        _, rejected = eligible_candidates(pair_index, SPLIT)
        rejections.append({"true_pair_index": pair_index,
                           "pair": list(ALL_PAIRS[pair_index]),
                           "rejected": list(rejected)})
        for fixture_index in FIXTURE_INDICES:
            fixture = make_fixture(pair_index, fixture_index, SPLIT)
            records.append({key: fixture[key] for key in (
                "true_pair_index", "pair", "fixture_index",
                "construction_candidate_index", "split",
                "source_region",
                "raw_sha256", "latent_profile_sha256", "plaintext_length",
                "minimum_edit_count", "edit_fraction", "normalized_quadgram",
                "latent_token_count", "latent_single_count",
                "partition_distance")})
    return {"phase": "505A", "status": "fixture_manifest",
            "faed_scored": False,
            "max_construction_candidates": MAX_CONSTRUCTION_CANDIDATES,
            "selection_rule":
                "first_two_eligible_distinct_source_regions_per_pair",
            "records": records, "construction_rejections": rejections}


def self_test() -> dict:
    if len(ALL_PAIRS) != 36 or len(set(ALL_PAIRS)) != 36:
        raise AssertionError("escape-pair universe changed")
    for pair_index in (0, len(ALL_PAIRS) - 1):
        profile = sampled_token_profile(pair_index, 0)
        contribution = collections.Counter()
        for token, count in profile["token_counts"].items():
            for symbol in token:
                contribution[symbol] += count
        if contribution != collections.Counter(rawonly.RAW_COUNTS):
            raise AssertionError("profile does not reconstruct raw histogram")
    tree = ast.parse(Path(__file__).read_text())
    imports = {
        alias.name for node in ast.walk(tree) if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    if "data" in imports:
        raise AssertionError("Phase 505A imports puzzle data")
    return {
        "pair_count": len(ALL_PAIRS),
        "fixture_count_planned": len(ALL_PAIRS) * len(FIXTURE_INDICES),
        "raw_length": sum(rawonly.RAW_COUNTS.values()),
        "faed_scored": False,
        "execution_lock_issued": False,
        "protocol_sha256": hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--build-fixture-manifest", action="store_true")
    group.add_argument("--verify-lock", action="store_true")
    group.add_argument("--run-ceiling", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.self_test:
        result = self_test()
    elif args.build_fixture_manifest:
        result = fixture_manifest()
        atomic_json(args.output or DEFAULT_MANIFEST, result)
    elif args.verify_lock:
        result = verify_lock()
    else:
        result = run_ceiling(args.output or DEFAULT_OUTPUT)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
