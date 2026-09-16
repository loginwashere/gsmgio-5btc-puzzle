#!/usr/bin/env python3
"""Phase 505D: post-hoc minimum-window diagnostic for shallow pair scores."""
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
import phase484q_blind_joint_width19_solver as joint
import phase490_width19_dual_lane_dev as front
import phase493_partial_unrestricted_board_diagnostic as variants
import phase505_escape_pair_identifiability as ceiling
import phase505c_shallow_escape_pair_screen as shallow


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
PROTOCOL = (REPO_ROOT / "doc" / "Brainstorms" /
            "2026-09-14 - Phase 505D Shallow Window-Gate Diagnostic.md")
LOCK_PATH = SCRIPT_DIR / "phase505d_diagnostic_lock.json"
DEFAULT_WORK_DIR = REPO_ROOT / "_work" / "phase505d"
MIN_WINDOWS = tuple(range(1, 31))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def expected_lock_payload() -> dict:
    dependencies = (base, prefix, joint, front, variants, ceiling, shallow)
    return {
        "phase": "505D", "status": "development_diagnostic_lock",
        "protocol_sha256": sha256_file(PROTOCOL),
        "script_sha256": sha256_file(Path(__file__)),
        "dependencies_sha256": {
            str(Path(module.__file__).relative_to(REPO_ROOT)):
                sha256_file(Path(module.__file__)) for module in dependencies
        },
        "phase505c_result_sha256": sha256_file(
            shallow.DEFAULT_WORK_DIR / "result.json"),
        "unrestricted_board_binary_sha256": sha256_file(
            variants.UNRESTRICTED_BINARY),
        "true_pair_indices": list(shallow.PILOT_TRUE_PAIR_INDICES),
        "hypothesis_pair_indices": list(range(len(ceiling.ALL_PAIRS))),
        "depth": shallow.DEPTH, "path_count": len(shallow.path_universe()),
        "minimum_window_grid": list(MIN_WINDOWS),
        "budgets": {"restarts": shallow.RESTARTS,
                    "iterations": shallow.ITERATIONS,
                    "seed": shallow.BOARD_SEED},
        "faed_scored": False, "holdout_consumed": False,
    }


def verify_lock() -> dict:
    if not LOCK_PATH.is_file():
        raise RuntimeError("Phase-505D execution lock is absent")
    actual = json.loads(LOCK_PATH.read_text())
    if actual != expected_lock_payload():
        raise RuntimeError("Phase-505D execution lock mismatch")
    return actual


def multistart_with_windows(paths, blocks, pair, quad):
    best = np.full(len(paths), -np.inf)
    windows = None
    for restart in range(shallow.RESTARTS):
        scores, current_windows, _ = joint.gpu_coarse_screen(
            variants.UNRESTRICTED_BINARY, blocks, pair, quad, paths,
            shallow.ITERATIONS,
            base.derive_seed(shallow.BOARD_SEED, restart))
        if windows is None:
            windows = current_windows.copy()
        elif not np.array_equal(windows, current_windows):
            raise AssertionError("window counts changed across restarts")
        best = np.maximum(best, scores)
    return best, windows


def true_mask(paths, fixture) -> np.ndarray:
    truth = prefix.order_to_sequence(fixture["order"])
    targets = {
        tuple(truth[start:start + shallow.DEPTH])
        for start in range(shallow.WIDTH - shallow.DEPTH + 1)
    }
    return np.asarray([tuple(path) in targets for path in paths], dtype=bool)


def run_cell(true_pair_index: int, hypothesis_pair_index: int,
             paths: np.ndarray) -> dict:
    fixture = ceiling.make_fixture(true_pair_index,
                                   shallow.EVAL_FIXTURE_INDEX)
    pair = ceiling.ALL_PAIRS[hypothesis_pair_index]
    blocks = prefix.blocks_from_observed(fixture)
    quad, _ = base.load_language_model()
    began = time.monotonic()
    scores, windows = multistart_with_windows(paths, blocks, pair, quad)
    planted = true_mask(paths, fixture)
    records = []
    for minimum in MIN_WINDOWS:
        eligible = windows >= minimum
        if np.any(eligible):
            eligible_indices = np.flatnonzero(eligible)
            best_index = int(eligible_indices[np.argmax(scores[eligible])])
            best_score = float(scores[best_index])
            best_path = paths[best_index].tolist()
        else:
            best_score, best_path = None, None
        true_eligible = eligible & planted
        if np.any(true_eligible):
            best_true = float(np.max(scores[true_eligible]))
            true_rank = 1 + int(np.count_nonzero(
                eligible & (scores > best_true)))
        else:
            best_true, true_rank = None, None
        records.append({
            "minimum_windows": minimum,
            "eligible_paths": int(np.count_nonzero(eligible)),
            "best_score": best_score, "best_path": best_path,
            "audit_true_eligible": int(np.count_nonzero(true_eligible)),
            "audit_best_true_score": best_true,
            "audit_best_true_rank": true_rank,
        })
    return {
        "phase": "505D", "status": "development_window_cell_complete",
        "faed_scored": False, "holdout_consumed": False,
        "true_pair_index": true_pair_index,
        "hypothesis_pair_index": hypothesis_pair_index,
        "pair": list(pair), "records": records,
        "wall_seconds": time.monotonic() - began,
    }


def summarize(cells: list[dict]) -> dict:
    curves = []
    for minimum in MIN_WINDOWS:
        rows = []
        for true_pair_index in shallow.PILOT_TRUE_PAIR_INDICES:
            row = [cell for cell in cells
                   if cell["true_pair_index"] == true_pair_index]
            scored = []
            for cell in row:
                record = cell["records"][minimum - 1]
                if record["best_score"] is not None:
                    scored.append((record["best_score"],
                                   cell["hypothesis_pair_index"]))
            scored.sort(key=lambda item: (-item[0], item[1]))
            rank = next((index for index, (_, pair_index)
                         in enumerate(scored, 1)
                         if pair_index == true_pair_index), None)
            rows.append({"true_pair_index": true_pair_index,
                         "true_pair_rank": rank,
                         "valid_pairs": len(scored)})
        curves.append({
            "minimum_windows": minimum,
            "top1": sum(row["true_pair_rank"] == 1 for row in rows),
            "top3": sum(row["true_pair_rank"] is not None and
                        row["true_pair_rank"] <= 3 for row in rows),
            "rows": rows,
        })
    return {
        "phase": "505D", "status": "development_window_diagnostic_complete",
        "faed_scored": False, "holdout_consumed": False,
        "execution_lock_sha256": sha256_file(LOCK_PATH),
        "best_top1": max(record["top1"] for record in curves),
        "best_top3": max(record["top3"] for record in curves),
        "any_threshold_top3_all_rows": any(
            record["top3"] == len(shallow.PILOT_TRUE_PAIR_INDICES)
            for record in curves),
        "curves": curves,
    }


def run(root: Path = DEFAULT_WORK_DIR) -> dict:
    verify_lock()
    root = Path(root)
    paths = shallow.path_universe()
    cells = []
    for true_pair_index in shallow.PILOT_TRUE_PAIR_INDICES:
        for hypothesis_pair_index in range(len(ceiling.ALL_PAIRS)):
            path = root / f"true_{true_pair_index:02d}" / (
                f"hypothesis_{hypothesis_pair_index:02d}.json")
            if path.exists():
                cell = json.loads(path.read_text())
                if (cell.get("true_pair_index") != true_pair_index or
                        cell.get("hypothesis_pair_index") !=
                        hypothesis_pair_index):
                    raise RuntimeError("Phase-505D checkpoint identity mismatch")
            else:
                cell = run_cell(true_pair_index, hypothesis_pair_index, paths)
                atomic_json(path, cell)
            cells.append(cell)
            atomic_json(root / "progress.json", {
                "phase": "505D", "status": "in_progress",
                "completed": len(cells), "total": 108,
                "execution_lock_sha256": sha256_file(LOCK_PATH),
            })
    result = summarize(cells)
    atomic_json(root / "result.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--verify-lock", action="store_true")
    group.add_argument("--run", action="store_true")
    parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK_DIR)
    args = parser.parse_args()
    result = verify_lock() if args.verify_lock else run(args.work_dir)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
