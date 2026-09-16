#!/usr/bin/env python3
"""Diagnose the Phase-494 unrestricted-board collapse at depth 10."""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np

import phase484a_raw_symbol_vic_solver as base
import phase484j_constructive_prefix_beam_probe as prefix
import phase484k_bidirectional_segment_assembly_probe as bidi
import phase484q_blind_joint_width19_solver as joint
import phase490_width19_dual_lane_dev as front
import phase490_width19_checkpointed_dual_lane as continuation
import phase491_raw_histogram_fixture as rawonly
import phase493_partial_unrestricted_board_diagnostic as variants
import phase494_unrestricted_board_full_pipeline as phase494


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
PROTOCOL = (REPO_ROOT / "doc" / "Brainstorms" /
            "2026-09-13 - Phase 495 Depth10 Objective Root-Cause Diagnostic.md")
DEFAULT_SOURCE = (REPO_ROOT / "_work" / "phase494" / "i3_s3" /
                  "continuation" / "lane_a_depth9.npz")
DEFAULT_MARKER = (REPO_ROOT / "_work" / "phase494" / "i3_s3" /
                  "objective_marker.json")
DEFAULT_OUTPUT = (REPO_ROOT / "_work" / "phase495" /
                  "depth10_objective_diagnostic.json")
SEED = 0x495D10
TOP_FALSE = 512
RANDOM_FALSE = 512
BUDGET_ARMS = (
    ("baseline", 3, 2000),
    ("iterations", 3, 10000),
    ("restarts", 12, 2000),
    ("combined", 8, 20000),
)
HYBRID_ALPHAS = (0.0, 0.25, 0.5, 0.75, 1.0)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def verify_phase494_marker(path: Path = DEFAULT_MARKER) -> dict:
    actual = json.loads(Path(path).read_text())
    expected = phase494.marker_payload()
    if actual != expected:
        raise RuntimeError("Phase-494 marker or a pinned dependency changed")
    return actual


def true_mask(paths: np.ndarray, truth: tuple[int, ...], depth: int) -> np.ndarray:
    targets = np.asarray(sorted(bidi.true_windows(truth, depth)), dtype=np.uint8)
    target_keys = front.packed_keys(targets)
    return np.isin(front.packed_keys(paths), target_keys)


def score_rank(scores: np.ndarray, mask: np.ndarray) -> dict:
    selected = np.flatnonzero(mask)
    if not len(selected):
        return {"true_count": 0, "best_true_score": None,
                "best_true_rank": None}
    values = scores[selected]
    best = float(np.max(values))
    return {"true_count": int(len(selected)), "best_true_score": best,
            "best_true_rank": 1 + int(np.count_nonzero(scores > best))}


def top_false(scores: np.ndarray, is_true: np.ndarray, count: int) -> np.ndarray:
    false = np.flatnonzero(~is_true)
    count = min(count, len(false))
    if count == 0:
        return false
    chosen = false[np.argpartition(scores[false], -count)[-count:]]
    return chosen[np.argsort(-scores[chosen], kind="stable")]


def sampled_false(is_true: np.ndarray, count: int, seed: int = SEED) -> np.ndarray:
    rng = base.PCG32(seed)
    selected: set[int] = set()
    while len(selected) < min(count, int(np.count_nonzero(~is_true))):
        index = rng.below(len(is_true))
        if not is_true[index]:
            selected.add(index)
    return np.asarray(sorted(selected), dtype=np.int64)


def make_panel(unrestricted: np.ndarray, constrained: np.ndarray,
               is_true: np.ndarray) -> tuple[np.ndarray, dict[int, list[str]]]:
    groups = {
        "true": np.flatnonzero(is_true),
        "unrestricted_top": top_false(unrestricted, is_true, TOP_FALSE),
        "constrained_top": top_false(constrained, is_true, TOP_FALSE),
        "random": sampled_false(is_true, RANDOM_FALSE),
    }
    labels: dict[int, list[str]] = {}
    for label, indices in groups.items():
        for index in indices:
            labels.setdefault(int(index), []).append(label)
    return np.asarray(sorted(labels), dtype=np.int64), labels


def multistart_panel(binary: Path, paths: np.ndarray, blocks, pair, quad,
                     restarts: int, iterations: int, seed: int = SEED):
    all_scores = []
    best = np.full(len(paths), -np.inf)
    best_boards = None
    best_restart = np.zeros(len(paths), dtype=np.int64)
    for restart in range(restarts):
        current, _, boards = joint.gpu_coarse_screen(
            binary, blocks, pair, quad, paths, iterations,
            base.derive_seed(seed, restart))
        all_scores.append(current)
        improved = current > best
        if best_boards is None:
            best_boards = boards.copy()
        best[improved] = current[improved]
        best_boards[improved] = boards[improved]
        best_restart[improved] = restart
    return np.asarray(all_scores), best, best_boards, best_restart


def partition_violations(board: np.ndarray) -> int:
    common, _ = rawonly.training_groups()
    allowed = {base.LETTER_ALPHABET.index(letter) for letter in common}
    return sum(int(value) not in allowed for value in board[:7])


def planted_scores(paths, blocks, pair, board, quad) -> np.ndarray:
    return variants.score_planted(paths, blocks, pair, board, quad)


def panel_summary(scores_by_restart, best, boards, planted, planted_board,
                  labels, global_indices, best_restart) -> dict:
    accuracy = np.mean(boards == planted_board, axis=1)
    records = []
    for local, global_index in enumerate(global_indices):
        series = scores_by_restart[:, local]
        records.append({
            "global_index": int(global_index),
            "labels": labels[int(global_index)],
            "best_score": float(best[local]),
            "planted_board_score": float(planted[local]),
            "gap_from_planted": float(best[local] - planted[local]),
            "best_board_accuracy": float(accuracy[local]),
            "best_board_partition_violations": partition_violations(boards[local]),
            "best_restart": int(best_restart[local]),
            "restart_mean": float(np.mean(series)),
            "restart_std": float(np.std(series)),
            "restart_range": float(np.ptp(series)),
        })
    return {"records": records}


def run(source: Path = DEFAULT_SOURCE, marker: Path = DEFAULT_MARKER,
        output: Path = DEFAULT_OUTPUT) -> dict:
    source, marker, output = Path(source), Path(marker), Path(output)
    if output.exists():
        raise FileExistsError("refusing to overwrite diagnostic result")
    began = time.monotonic()
    marker_data = verify_phase494_marker(marker)
    population = np.load(source)
    parents = np.asarray(population["paths"], dtype=np.uint8)
    if parents.shape != (262144, 9):
        raise RuntimeError("unexpected Phase-494 depth-9 population")
    children = front.expand_bidirectional(parents)

    fixture = variants.make_variant(phase494.FIXTURE_INDEX,
                                    phase494.SWAP_COUNT)
    blocks = prefix.blocks_from_observed(fixture)
    pair = tuple(fixture["pair"])
    truth = prefix.order_to_sequence(fixture["order"])
    quad, _ = base.load_language_model()
    is_true = true_mask(children, truth, 10)
    if int(np.count_nonzero(is_true)) != 2:
        raise AssertionError("expected exactly two true depth-10 children")

    production = continuation.SCHEDULE
    unrestricted = front.constrained_multistart(
        children, blocks, pair, quad, production["coarse_restarts"],
        production["coarse_iterations"], binary=variants.UNRESTRICTED_BINARY,
        seed=production["board_seed"])
    constrained = front.constrained_multistart(
        children, blocks, pair, quad, production["coarse_restarts"],
        production["coarse_iterations"], binary=variants.CONSTRAINED_BINARY,
        seed=production["board_seed"])

    panel_indices, labels = make_panel(unrestricted, constrained, is_true)
    panel = children[panel_indices]
    planted_board = variants.canonical_board(fixture["letter_to_code"])
    planted = planted_scores(panel, blocks, pair, planted_board, quad)

    arms = {}
    for name, restarts, iterations in BUDGET_ARMS:
        series, best, boards, which = multistart_panel(
            variants.UNRESTRICTED_BINARY, panel, blocks, pair, quad,
            restarts, iterations, seed=production["board_seed"])
        arms[name] = {
            "restarts": restarts, "iterations": iterations,
            **panel_summary(series, best, boards, planted, planted_board,
                            labels, panel_indices, which),
        }

    cseries, cbest, cboards, cwhich = multistart_panel(
        variants.CONSTRAINED_BINARY, panel, blocks, pair, quad,
        production["coarse_restarts"], production["coarse_iterations"],
        seed=production["board_seed"])
    constrained_panel = panel_summary(
        cseries, cbest, cboards, planted, planted_board, labels,
        panel_indices, cwhich)

    hybrids = []
    for alpha in HYBRID_ALPHAS:
        scores = alpha * unrestricted + (1.0 - alpha) * constrained
        hybrids.append({"unrestricted_weight": alpha,
                        **score_rank(scores, is_true)})

    result = {
        "phase": 495,
        "status": "development_root_cause_diagnostic_complete",
        "faed_scored": False,
        "holdout_consumed": False,
        "fixture_index": phase494.FIXTURE_INDEX,
        "swap_count": phase494.SWAP_COUNT,
        "normalized_quadgram": fixture["normalized_quadgram"],
        "phase494_marker_sha256": sha256_file(marker),
        "phase494_source_sha256": sha256_file(source),
        "protocol_sha256": sha256_file(PROTOCOL),
        "binaries_sha256": {
            "unrestricted": sha256_file(variants.UNRESTRICTED_BINARY),
            "constrained": sha256_file(variants.CONSTRAINED_BINARY),
        },
        "marker": marker_data,
        "population": {"parents": len(parents), "children": len(children),
                       "true_children": int(np.count_nonzero(is_true))},
        "production_budget": {
            "restarts": production["coarse_restarts"],
            "iterations": production["coarse_iterations"],
        },
        "full_population": {
            "unrestricted": score_rank(unrestricted, is_true),
            "constrained": score_rank(constrained, is_true),
            "hybrids": hybrids,
        },
        "panel": {
            "size": len(panel),
            "selection_counts": {
                name: sum(name in value for value in labels.values())
                for name in ("true", "unrestricted_top", "constrained_top",
                             "random")
            },
            "paths": [{"global_index": int(index),
                       "path": panel[local].tolist(),
                       "labels": labels[int(index)]}
                      for local, index in enumerate(panel_indices)],
            "planted_partition_violations": partition_violations(planted_board),
            "unrestricted_arms": arms,
            "constrained_baseline": constrained_panel,
        },
        "wall_seconds": time.monotonic() - began,
    }
    atomic_json(output, result)
    return result


def self_test() -> dict:
    verify_phase494_marker()
    paths = np.asarray([[0, 1, 2, 3], [0, 1, 3, 2], [1, 0, 2, 3]],
                       dtype=np.uint8)
    truth = (0, 1, 2, 3)
    mask = true_mask(paths, truth, 4)
    if mask.tolist() != [True, False, False]:
        raise AssertionError("true-mask mismatch")
    scores = np.asarray([1.0, 3.0, 2.0])
    if score_rank(scores, mask)["best_true_rank"] != 3:
        raise AssertionError("score-rank mismatch")
    return {"faed_scored": False, "marker_verified": True,
            "budget_arms": [list(arm) for arm in BUDGET_ARMS]}


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--run", action="store_true")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--marker", type=Path, default=DEFAULT_MARKER)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = (self_test() if args.self_test else
              run(args.source, args.marker, args.output))
    print(json.dumps(result if args.self_test else {
        "phase": result["phase"], "status": result["status"],
        "full_population": result["full_population"],
        "panel_size": result["panel"]["size"],
        "wall_seconds": result["wall_seconds"],
        "output": str(args.output),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
