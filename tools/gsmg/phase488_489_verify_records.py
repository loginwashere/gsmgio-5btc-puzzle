#!/usr/bin/env python3
"""Verify the compact, committed Phase 488/489 result records.

The large checkpoint trees remain reproducible scratch data under ``_work``.
These records preserve the small terminal results on which the findings rest.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from data import FAED
import phase484a_raw_symbol_vic_solver as base
import phase484j_constructive_prefix_beam_probe as prefix
import phase484an_width30_dual_lane_dev as dual
import phase484ao_locked_faed_width30_gi_dual_lane as locked
import phase484y_width30_blind_joint_solver as joint


SCRIPT_DIR = Path(__file__).resolve().parent
PHASE488 = SCRIPT_DIR / "phase488_results"
PHASE489 = SCRIPT_DIR / "phase489_faed_width30_gi_result.json"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def verify_phase488() -> dict:
    expected = {
        "dev": tuple(range(13, 23)),
        "holdout": tuple(range(12)),
    }
    counts = {}
    hashes = {}
    for split, indices in expected.items():
        summary_path = PHASE488 / split / "summary.json"
        summary = read_json(summary_path)
        if set(summary) != {str(index) for index in indices}:
            raise AssertionError(f"Phase 488 {split} summary index set changed")
        exact = 0
        hashes[split] = {"summary.json": sha256_file(summary_path)}
        for index in indices:
            path = PHASE488 / split / f"i{index}.json"
            record = read_json(path)
            hashes[split][path.name] = sha256_file(path)
            if record["fixture_index"] != index:
                raise AssertionError("Phase 488 fixture index mismatch")
            if record["schedule_sha256"] != dual.schedule_sha256():
                raise AssertionError("Phase 488 schedule hash mismatch")
            if record["faed_scored"]:
                raise AssertionError("Phase 488 record claims FAED was scored")
            if split == "holdout":
                if record.get("split") != "holdout" or not record["holdout_consumed"]:
                    raise AssertionError("Phase 488 holdout provenance mismatch")
            elif record["holdout_consumed"]:
                raise AssertionError("Phase 488 dev record consumed holdout")
            selected = {
                key: record[key]
                for key in summary[str(index)]
                if key not in ("status",)
            }
            summarized = {
                key: value
                for key, value in summary[str(index)].items()
                if key not in ("status",)
            }
            if selected != summarized:
                raise AssertionError(f"Phase 488 {split} summary differs at {index}")
            exact += int(record["top1_exact_order"])
        counts[split] = {"fixtures": len(indices), "exact_top1": exact}
    if counts != {
        "dev": {"fixtures": 10, "exact_top1": 10},
        "holdout": {"fixtures": 12, "exact_top1": 11},
    }:
        raise AssertionError(f"Phase 488 headline counts changed: {counts}")
    return {"counts": counts, "sha256": hashes}


def verify_phase489() -> dict:
    locked.verify_lock()
    result = read_json(PHASE489)
    lock_hash = sha256_file(locked.LOCK)
    if result["execution_lock_sha256"] != lock_hash:
        raise AssertionError("Phase 489 result is not linked to the live lock")
    if result["arm"] != "real" or result["run_index"] != 0:
        raise AssertionError("Phase 489 preserved the wrong run")
    if result["raw_sha256"] != locked.FAED_SHA256:
        raise AssertionError("Phase 489 raw-input hash mismatch")
    if result["schedule_sha256"] != dual.schedule_sha256():
        raise AssertionError("Phase 489 schedule hash mismatch")
    fixture = {"width": locked.WIDTH, "observed": FAED}
    blocks = prefix.blocks_from_observed(fixture)
    quad, _ = base.load_language_model()
    previous_score = float("inf")
    max_score_error = 0.0
    for rank, candidate in enumerate(result["final_candidates"], 1):
        if candidate["final_rank"] != rank:
            raise AssertionError("Phase 489 final ranks are not contiguous")
        if sorted(candidate["order"]) != list(range(locked.WIDTH)):
            raise AssertionError("Phase 489 candidate order is not a permutation")
        if sorted(candidate["board"]) != list(range(len(base.LETTER_ALPHABET))):
            raise AssertionError("Phase 489 candidate board is not a permutation")
        slots = joint.complete_token_slots(blocks, locked.PAIR, candidate["order"])
        board = np.asarray(candidate["board"], dtype=np.int64)
        plaintext = "".join(base.LETTER_ALPHABET[value] for value in board[slots])
        score = base.score_indices(board[slots], quad) / max(1, len(slots) - 3)
        max_score_error = max(max_score_error, abs(score - candidate["normalized_score"]))
        if plaintext != candidate["plaintext"] or len(plaintext) != candidate["decoded_length"]:
            raise AssertionError("Phase 489 candidate plaintext does not recompute")
        raw = "".join(
            blocks[column][row]
            for row in range(locked.ROWS)
            for column in candidate["order"]
        )
        encryption_order = prefix.sequence_to_order(candidate["order"])
        if base.Geometry(len(FAED), locked.WIDTH).encrypt(raw, encryption_order) != FAED:
            raise AssertionError("Phase 489 candidate does not round-trip to FAED")
        if candidate["normalized_score"] > previous_score:
            raise AssertionError("Phase 489 candidates are not score-ranked")
        previous_score = candidate["normalized_score"]
    top = result["final_candidates"][0]
    if result["top1_plaintext"] != top["plaintext"]:
        raise AssertionError("Phase 489 top plaintext mismatch")
    if result["top1_normalized_score"] != top["normalized_score"]:
        raise AssertionError("Phase 489 top score mismatch")
    if max_score_error > 1e-10:
        raise AssertionError(f"Phase 489 score error too large: {max_score_error}")
    return {
        "result_sha256": sha256_file(PHASE489),
        "lock_sha256": lock_hash,
        "candidate_count": len(result["final_candidates"]),
        "top1_normalized_score": result["top1_normalized_score"],
        "top1_decoded_length": len(result["top1_plaintext"]),
        "max_score_recomputation_error": max_score_error,
        "all_candidates_round_trip": True,
    }


def main() -> int:
    print(json.dumps({
        "phase488": verify_phase488(),
        "phase489": verify_phase489(),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
