#!/usr/bin/env python3
"""Checkpointed width-19 dual-lane development continuation.

This ports Phase 488's fixed width-30 continuation schedule to width 19 and
starts from Phase 490's refined depth-7 population.  Every expensive depth is
an independently committed NPZ + JSON stage.  A restart validates completed
stages and resumes at the first absent stage.  Synthetic truth is diagnostic
only; no selection or branch depends on it.  FAED is never imported here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np

import phase484a_raw_symbol_vic_solver as base
import phase484j_constructive_prefix_beam_probe as prefix
import phase484q_blind_joint_width19_solver as joint
import phase484x_exact_faed_profile_power_probe as exact
import phase490_width19_dual_lane_dev as front


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_WORK_DIR = REPO_ROOT / "_work/phase490/i14"
WIDTH = 19

SCHEDULE = {
    "front_schedule_sha256": front.schedule_sha256(),
    "lane_a_depth7_parent_keep": 32768,
    "lane_a_depth8_children_per_parent": 40,
    "lane_a_depth8_keep": 262144,
    "lane_a_bridge_parent_keep": 65536,
    "lane_a_bridge_children_per_parent": 8,
    "lane_b_descendants_per_root": 4,
    "lane_b_root_chunk": 16384,
    "lane_b_depth9_root_keep": 262144,
    "lane_b_depth10_root_keep": 65536,
    "merge_depth12_keep": 262144,
    "depth13_16_keep": 262144,
    "depth17_19_keep": 4096,
    "coarse_restarts": 3,
    "coarse_iterations": 2000,
    "refine_restarts": 4,
    "refine_iterations": 10000,
    "final_top": 8,
    "final_restarts": 4,
    "final_iterations": 10000,
    "board_seed": front.BOARD_SEED,
}


def canonical_hash(value) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def schedule_sha256() -> str:
    return canonical_hash(SCHEDULE)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_json(path: Path, value: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def atomic_population(path: Path, paths, scores, **extra) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp.npz")
    np.savez(temporary, paths=np.asarray(paths, dtype=np.uint8),
             scores=np.asarray(scores, dtype=np.float64), **extra)
    temporary.replace(path)
    return path


def load_population(path: Path, *, min_depth=4, max_depth=WIDTH,
                    require_roots=False):
    path = Path(path)
    with np.load(path) as payload:
        paths = np.asarray(payload["paths"], dtype=np.uint8)
        scores = np.asarray(payload["scores"], dtype=np.float64)
        roots = (np.asarray(payload["root_ids"], dtype=np.int64)
                 if "root_ids" in payload else None)
        original = (np.asarray(payload["original_root_ids"], dtype=np.int64)
                    if "original_root_ids" in payload else None)
    if paths.ndim != 2 or not min_depth <= paths.shape[1] <= max_depth:
        raise ValueError("checkpoint path depth is invalid")
    if scores.shape != (len(paths),) or not np.all(np.isfinite(scores)):
        raise ValueError("checkpoint scores are invalid")
    if len(paths) and (np.any(paths >= WIDTH) or
                       np.any(np.diff(np.sort(paths, axis=1), axis=1) == 0)):
        raise ValueError("checkpoint contains invalid or repeated columns")
    if require_roots:
        if roots is None or roots.shape != (len(paths),):
            raise ValueError("root-lineage checkpoint lacks valid root IDs")
        if len(roots) == 0 or np.any(roots < 0) or np.any(roots[1:] < roots[:-1]):
            raise ValueError("root IDs must be nonempty, nonnegative, and sorted")
    return paths, scores, roots, original


def fixture_context(fixture_index: int, split: str):
    fixture = exact.make_fixture(fixture_index, split)
    blocks = prefix.blocks_from_observed(fixture)
    truth = prefix.order_to_sequence(fixture["order"])
    quad, _ = base.load_language_model()
    return fixture, blocks, tuple(fixture["pair"]), truth, quad


def stage_paths(work_dir: Path, name: str):
    directory = Path(work_dir) / "continuation"
    return directory / f"{name}.npz", directory / f"{name}.json"


def completed_stage(work_dir: Path, name: str, fixture_index: int, split: str,
                    source: Path | None = None) -> Path | None:
    output, record_path = stage_paths(work_dir, name)
    if not output.exists() and not record_path.exists():
        return None
    # A stop can land after the atomic NPZ rename but before its JSON commit.
    # That orphan is not trusted or resumed; the stage is safely recomputed.
    if output.exists() and not record_path.exists():
        load_population(output)
        return None
    if not output.exists():
        raise RuntimeError(f"partial checkpoint exists for {name}")
    record = json.loads(record_path.read_text())
    expected = {
        "phase": "490",
        "stage": name,
        "fixture_index": fixture_index,
        "split": split,
        "schedule_sha256": schedule_sha256(),
        "output_sha256": sha256_file(output),
    }
    for key, value in expected.items():
        if record.get(key) != value:
            raise RuntimeError(f"checkpoint {name} has wrong {key}")
    if source is not None and record.get("source_sha256") != sha256_file(source):
        raise RuntimeError(f"checkpoint {name} source hash mismatch")
    load_population(output)
    return output


def commit_stage(work_dir: Path, name: str, fixture_index: int, split: str,
                 paths, scores, details: dict, source: Path | None = None,
                 **extra) -> Path:
    output, record_path = stage_paths(work_dir, name)
    atomic_population(output, paths, scores, **extra)
    record = {
        "phase": "490", "status": "development_checkpoint_complete",
        "faed_scored": False, "holdout_consumed": split == "holdout",
        "stage": name, "fixture_index": fixture_index, "split": split,
        "schedule_sha256": schedule_sha256(),
        "source": str(source) if source is not None else None,
        "source_sha256": sha256_file(source) if source is not None else None,
        "output": str(output), "output_sha256": sha256_file(output),
        **details,
    }
    atomic_json(record_path, record)
    return output


def recovery(paths, scores, truth, depth):
    return front.true_record(paths, scores, truth, depth)


def expand_with_parent_indices(paths):
    paths = np.asarray(paths, dtype=np.uint8)
    children = front.expand_bidirectional(paths)
    depth = paths.shape[1]
    parents = np.empty(len(children), dtype=np.int64)
    offset = 0
    all_indices = np.arange(len(paths), dtype=np.int64)
    for column in range(WIDTH):
        mask = ~np.any(paths == column, axis=1)
        count = int(np.count_nonzero(mask))
        parents[offset:offset + count] = all_indices[mask]
        offset += count
        parents[offset:offset + count] = all_indices[mask]
        offset += count
    if offset != len(children) or len(children) != 2 * len(paths) * (WIDTH-depth):
        raise AssertionError("parent-index expansion diverged")
    return children, parents


def reserve_local_children(paths, scores, parent_ids, keep):
    paths = np.asarray(paths, dtype=np.uint8)
    scores = np.asarray(scores, dtype=np.float64)
    parent_ids = np.asarray(parent_ids, dtype=np.int64)
    parent_count = int(parent_ids.max()) + 1
    group_size = len(paths) // parent_count
    if len(paths) != parent_count * group_size:
        raise ValueError("children are not balanced across parents")
    keys = tuple(paths[:, column]
                 for column in range(paths.shape[1] - 1, -1, -1))
    order = np.lexsort((*keys, -scores, parent_ids))
    grouped = order.reshape(parent_count, group_size)
    chosen = grouped[:, :min(keep, group_size)].reshape(-1)
    chosen_paths, chosen_scores = paths[chosen], scores[chosen]
    unique = front.unique_path_indices(chosen_paths)
    return chosen_paths[unique].copy(), chosen_scores[unique].copy()


def score_paths(paths, blocks, pair, quad, *, refined=False):
    return front.constrained_multistart(
        paths, blocks, pair, quad,
        SCHEDULE["refine_restarts" if refined else "coarse_restarts"],
        SCHEDULE["refine_iterations" if refined else "coarse_iterations"],
        seed=SCHEDULE["board_seed"])


def global_depth(source: Path, depth: int, keep: int, fixture_index: int,
                 split: str, work_dir: Path, name: str | None = None):
    name = name or f"depth{depth}_global"
    done = completed_stage(work_dir, name, fixture_index, split, source)
    if done:
        print("resume", name, flush=True)
        return done
    paths, _, _, _ = load_population(source, max_depth=depth-1)
    if paths.shape[1] != depth - 1:
        raise ValueError(f"{name} requires depth {depth-1} input")
    _, blocks, pair, truth, quad = fixture_context(fixture_index, split)
    began = time.monotonic()
    generated = front.expand_bidirectional(paths)
    scores = score_paths(generated, blocks, pair, quad)
    before = recovery(generated, scores, truth, depth)
    selected, selected_scores, unique = front.select_diverse(
        generated, scores, keep)
    after = recovery(selected, selected_scores, truth, depth)
    output = commit_stage(
        work_dir, name, fixture_index, split, selected, selected_scores,
        {"depth": depth, "keep": len(selected), "generated_unique": unique,
         "before_selection": before, "after_selection": after,
         "wall_seconds": time.monotonic() - began}, source)
    print("complete", name, "true", after["true_segments"], flush=True)
    return output


def lane_a_depth8(source: Path, fixture_index: int, split: str,
                  work_dir: Path):
    name = "lane_a_depth8"
    done = completed_stage(work_dir, name, fixture_index, split, source)
    if done:
        print("resume", name, flush=True)
        return done
    paths, scores, _, _ = load_population(source, min_depth=7, max_depth=7)
    ranked = front.ranked_indices(paths, scores)
    parents = paths[ranked[:SCHEDULE["lane_a_depth7_parent_keep"]]]
    _, blocks, pair, truth, quad = fixture_context(fixture_index, split)
    began = time.monotonic()
    children, parent_ids = expand_with_parent_indices(parents)
    coarse = score_paths(children, blocks, pair, quad)
    reserved, _ = reserve_local_children(
        children, coarse, parent_ids,
        SCHEDULE["lane_a_depth8_children_per_parent"])
    refined = score_paths(reserved, blocks, pair, quad, refined=True)
    selected, selected_scores, unique = front.select_diverse(
        reserved, refined, SCHEDULE["lane_a_depth8_keep"])
    before = recovery(reserved, refined, truth, 8)
    after = recovery(selected, selected_scores, truth, 8)
    return commit_stage(
        work_dir, name, fixture_index, split, selected, selected_scores,
        {"depth": 8, "parent_count": len(parents),
         "child_count": len(children), "reserved_count": len(reserved),
         "generated_unique": unique, "before_selection": before,
         "after_selection": after, "wall_seconds": time.monotonic()-began},
        source)


def bridge_depth(source: Path, depth: int, parent_keep: int,
                 children_per_parent: int, output_keep: int,
                 fixture_index: int, split: str, work_dir: Path, name: str):
    done = completed_stage(work_dir, name, fixture_index, split, source)
    if done:
        print("resume", name, flush=True)
        return done
    paths, scores, _, _ = load_population(source, min_depth=depth-1,
                                           max_depth=depth-1)
    ranked = front.ranked_indices(paths, scores)
    parents = paths[ranked[:min(parent_keep, len(paths))]]
    _, blocks, pair, truth, quad = fixture_context(fixture_index, split)
    began = time.monotonic()
    children, parent_ids = expand_with_parent_indices(parents)
    child_scores = score_paths(children, blocks, pair, quad)
    before = recovery(children, child_scores, truth, depth)
    reserved, reserved_scores = reserve_local_children(
        children, child_scores, parent_ids, children_per_parent)
    if len(reserved) > output_keep:
        reserved, reserved_scores, unique = front.select_diverse(
            reserved, reserved_scores, output_keep)
    else:
        unique = len(reserved)
    after = recovery(reserved, reserved_scores, truth, depth)
    return commit_stage(
        work_dir, name, fixture_index, split, reserved, reserved_scores,
        {"depth": depth, "parent_count": len(parents),
         "children_per_parent": children_per_parent,
         "generated_unique": unique, "before_selection": before,
         "after_selection": after, "wall_seconds": time.monotonic()-began},
        source)


def unique_root_path_indices(roots, paths, scores):
    roots = np.asarray(roots, dtype=np.int64)
    paths = np.ascontiguousarray(paths, dtype=np.uint8)
    scores = np.asarray(scores, dtype=np.float64)
    order = np.lexsort((-scores,) + tuple(
        paths[:, c] for c in range(paths.shape[1]-1, -1, -1)) + (roots,))
    ordered_roots, ordered_paths = roots[order], paths[order]
    first = np.r_[True, (ordered_roots[1:] != ordered_roots[:-1]) |
                  np.any(ordered_paths[1:] != ordered_paths[:-1], axis=1)]
    return order[first]


def select_per_root(paths, scores, roots, keep):
    unique = unique_root_path_indices(roots, paths, scores)
    paths, scores, roots = paths[unique], scores[unique], roots[unique]
    order = np.lexsort(tuple(paths[:, c] for c in range(
        paths.shape[1]-1, -1, -1)) + (-scores, roots))
    sorted_roots = roots[order]
    boundaries = np.flatnonzero(
        np.r_[True, sorted_roots[1:] != sorted_roots[:-1], True])
    chosen = np.concatenate([order[left:min(right, left+keep)]
                             for left, right in zip(boundaries[:-1],
                                                    boundaries[1:])])
    final = np.lexsort(tuple(paths[chosen, c] for c in range(
        paths.shape[1]-1, -1, -1)) + (-scores[chosen], roots[chosen]))
    chosen = chosen[final]
    return paths[chosen].copy(), scores[chosen].copy(), roots[chosen].copy()


def lineage_depth(source: Path, depth: int, fixture_index: int, split: str,
                  work_dir: Path, name: str):
    done = completed_stage(work_dir, name, fixture_index, split, source)
    if done:
        print("resume", name, flush=True)
        return done
    paths, _, roots, original = load_population(
        source, min_depth=depth-1, max_depth=depth-1, require_roots=True)
    root_values = np.unique(roots)
    if not np.array_equal(root_values, np.arange(root_values[-1]+1)):
        raise ValueError("root IDs are not dense")
    _, blocks, pair, truth, quad = fixture_context(fixture_index, split)
    began = time.monotonic()
    out_paths, out_scores, out_roots = [], [], []
    chunk = SCHEDULE["lane_b_root_chunk"]
    for root_start in range(0, len(root_values), chunk):
        root_stop = min(len(root_values), root_start + chunk)
        left = np.searchsorted(roots, root_start, side="left")
        right = np.searchsorted(roots, root_stop, side="left")
        children, parent_ids = expand_with_parent_indices(paths[left:right])
        child_roots = roots[left:right][parent_ids]
        child_scores = score_paths(children, blocks, pair, quad)
        selected = select_per_root(
            children, child_scores, child_roots,
            SCHEDULE["lane_b_descendants_per_root"])
        out_paths.append(selected[0]); out_scores.append(selected[1])
        out_roots.append(selected[2])
        print(name, "roots", root_start, root_stop, flush=True)
    selected_paths = np.concatenate(out_paths)
    selected_scores = np.concatenate(out_scores)
    selected_roots = np.concatenate(out_roots)
    after = recovery(selected_paths, selected_scores, truth, depth)
    return commit_stage(
        work_dir, name, fixture_index, split, selected_paths, selected_scores,
        {"depth": depth, "root_count": len(root_values),
         "retained_count": len(selected_paths), "after_selection": after,
         "wall_seconds": time.monotonic()-began}, source,
        root_ids=selected_roots,
        original_root_ids=(original if original is not None else
                           np.arange(len(root_values), dtype=np.int64)))


def initialize_roots(source: Path, fixture_index: int, split: str,
                     work_dir: Path):
    name = "lane_b_depth7_roots"
    done = completed_stage(work_dir, name, fixture_index, split, source)
    if done:
        print("resume", name, flush=True)
        return done
    paths, scores, _, _ = load_population(source, min_depth=7, max_depth=7)
    roots = np.arange(len(paths), dtype=np.int64)
    return commit_stage(
        work_dir, name, fixture_index, split, paths, scores,
        {"depth": 7, "root_count": len(paths), "wall_seconds": 0.0}, source,
        root_ids=roots, original_root_ids=roots)


def prune_roots(source: Path, keep_roots: int, fixture_index: int, split: str,
                work_dir: Path, name: str):
    done = completed_stage(work_dir, name, fixture_index, split, source)
    if done:
        print("resume", name, flush=True)
        return done
    paths, scores, roots, original = load_population(source, require_roots=True)
    root_count = int(roots.max()) + 1
    best = np.full(root_count, -np.inf)
    np.maximum.at(best, roots, scores)
    chosen = np.sort(np.lexsort((np.arange(root_count), -best))[
        :min(keep_roots, root_count)])
    mask = np.isin(roots, chosen)
    new_roots = np.searchsorted(chosen, roots[mask])
    return commit_stage(
        work_dir, name, fixture_index, split, paths[mask], scores[mask],
        {"depth": paths.shape[1], "root_count_before": root_count,
         "root_count_after": len(chosen), "wall_seconds": 0.0}, source,
        root_ids=new_roots,
        original_root_ids=(original[chosen] if original is not None else chosen))


def release_lineage(source: Path, depth: int, keep: int, fixture_index: int,
                    split: str, work_dir: Path, name: str):
    done = completed_stage(work_dir, name, fixture_index, split, source)
    if done:
        print("resume", name, flush=True)
        return done
    paths, _, _, _ = load_population(source, min_depth=depth-1,
                                      max_depth=depth-1, require_roots=True)
    _, blocks, pair, truth, quad = fixture_context(fixture_index, split)
    began = time.monotonic()
    generated = front.expand_bidirectional(paths)
    scores = score_paths(generated, blocks, pair, quad)
    before = recovery(generated, scores, truth, depth)
    selected, selected_scores, unique = front.select_diverse(
        generated, scores, keep)
    after = recovery(selected, selected_scores, truth, depth)
    return commit_stage(
        work_dir, name, fixture_index, split, selected, selected_scores,
        {"depth": depth, "generated_unique": unique,
         "before_selection": before, "after_selection": after,
         "wall_seconds": time.monotonic()-began}, source)


def merge_depth12(a: Path, b: Path, fixture_index: int, split: str,
                  work_dir: Path):
    name = "merged_depth12"
    done = completed_stage(work_dir, name, fixture_index, split)
    if done:
        record = json.loads(stage_paths(work_dir, name)[1].read_text())
        if record.get("source_hashes") != [sha256_file(a), sha256_file(b)]:
            raise RuntimeError("merged checkpoint source hashes mismatch")
        print("resume", name, flush=True)
        return done
    ap, ascore, _, _ = load_population(a, min_depth=12, max_depth=12)
    bp, bscore, _, _ = load_population(b, min_depth=12, max_depth=12)
    paths, scores = np.concatenate([ap, bp]), np.concatenate([ascore, bscore])
    ranked = front.ranked_indices(paths, scores)
    unique = ranked[front.unique_path_indices(paths[ranked])]
    paths, scores = paths[unique], scores[unique]
    selected, selected_scores, unique_count = front.select_diverse(
        paths, scores, SCHEDULE["merge_depth12_keep"])
    output = commit_stage(
        work_dir, name, fixture_index, split, selected, selected_scores,
        {"depth": 12, "source_hashes": [sha256_file(a), sha256_file(b)],
         "source_counts": [len(ap), len(bp)], "generated_unique": unique_count,
         "wall_seconds": 0.0})
    return output


def final_resolve(source: Path, fixture_index: int, split: str,
                  work_dir: Path):
    name = "final_resolve"
    _, record_path = stage_paths(work_dir, name)
    if record_path.exists():
        record = json.loads(record_path.read_text())
        if (record.get("schedule_sha256") != schedule_sha256() or
                record.get("source_sha256") != sha256_file(source)):
            raise RuntimeError("final result does not match schedule/source")
        print("resume", name, flush=True)
        return record
    paths, scores, _, _ = load_population(source, min_depth=WIDTH,
                                           max_depth=WIDTH)
    fixture, blocks, pair, truth, quad = fixture_context(fixture_index, split)
    ranked = front.ranked_indices(paths, scores)[:SCHEDULE["final_top"]]
    terminals = [{"extension_rank": rank, "extension_score": float(scores[i]),
                  "order": paths[i].tolist()}
                 for rank, i in enumerate(ranked, 1)]
    began = time.monotonic()
    final, skipped = joint.resolve_terminals(
        blocks, pair, quad, terminals, SCHEDULE["final_restarts"],
        SCHEDULE["final_iterations"])
    truth_tuple = tuple(truth)
    for record in final:
        record["is_exact_order"] = tuple(record["order"]) == truth_tuple
        record["plaintext_accuracy"] = (
            sum(a == b for a, b in zip(
                record["plaintext"], fixture["plaintext"])) /
            max(len(record["plaintext"]), len(fixture["plaintext"])))
    exact_record = next((r for r in final if r["is_exact_order"]), None)
    result = {
        "phase": "490", "status": "development_final_resolve_complete",
        "faed_scored": False, "holdout_consumed": split == "holdout",
        "stage": name, "fixture_index": fixture_index, "split": split,
        "schedule_sha256": schedule_sha256(), "source": str(source),
        "source_sha256": sha256_file(source), "terminal_count": len(terminals),
        "terminal_candidates": terminals,
        "skipped": len(skipped), "skipped_terminals": skipped,
        "exact_order_final_rank": (exact_record["final_rank"]
                                   if exact_record else None),
        "top1_exact_order": bool(final and final[0]["is_exact_order"]),
        "top1_plaintext_accuracy": (final[0]["plaintext_accuracy"]
                                    if final else None),
        "final_candidates": final, "wall_seconds": time.monotonic()-began,
    }
    atomic_json(record_path, result)
    return result


def run(fixture_index=14, split="dev", work_dir=DEFAULT_WORK_DIR):
    work_dir = Path(work_dir)
    front_source = work_dir / "depth7_refined.npz"
    front_result = work_dir / "result.json"
    if not front_source.is_file() or not front_result.is_file():
        raise RuntimeError("validated Phase 490 depth-7 front checkpoint is absent")
    front_record = json.loads(front_result.read_text())
    if (front_record.get("fixture_index") != fixture_index or
            front_record.get("split") != split or
            front_record.get("schedule_sha256") != front.schedule_sha256()):
        raise RuntimeError("front checkpoint metadata mismatch")
    if front_record.get("checkpoint") != str(front_source):
        # Relative paths are allowed, but they must resolve to this exact file.
        recorded = (SCRIPT_DIR / front_record.get("checkpoint", "")).resolve()
        if recorded != front_source.resolve():
            raise RuntimeError("front checkpoint path mismatch")

    lane_a8 = lane_a_depth8(front_source, fixture_index, split, work_dir)
    lane_a9 = global_depth(lane_a8, 9, SCHEDULE["lane_a_depth8_keep"],
                           fixture_index, split, work_dir, "lane_a_depth9")
    lane_a10 = global_depth(lane_a9, 10, SCHEDULE["lane_a_depth8_keep"],
                            fixture_index, split, work_dir, "lane_a_depth10")
    lane_a11 = bridge_depth(
        lane_a10, 11, SCHEDULE["lane_a_bridge_parent_keep"],
        SCHEDULE["lane_a_bridge_children_per_parent"],
        (SCHEDULE["lane_a_bridge_parent_keep"] *
         SCHEDULE["lane_a_bridge_children_per_parent"]),
        fixture_index, split, work_dir,
        "lane_a_depth11_bridge")
    lane_a12 = global_depth(
        lane_a11, 12, SCHEDULE["merge_depth12_keep"], fixture_index, split,
        work_dir, "lane_a_depth12")

    lane_b7 = initialize_roots(front_source, fixture_index, split, work_dir)
    lane_b8 = lineage_depth(lane_b7, 8, fixture_index, split, work_dir,
                            "lane_b_depth8")
    lane_b9 = lineage_depth(lane_b8, 9, fixture_index, split, work_dir,
                            "lane_b_depth9")
    lane_b9p = prune_roots(
        lane_b9, SCHEDULE["lane_b_depth9_root_keep"], fixture_index, split,
        work_dir, "lane_b_depth9_pruned")
    lane_b10 = lineage_depth(lane_b9p, 10, fixture_index, split, work_dir,
                             "lane_b_depth10")
    lane_b10p = prune_roots(
        lane_b10, SCHEDULE["lane_b_depth10_root_keep"], fixture_index, split,
        work_dir, "lane_b_depth10_pruned")
    lane_b11 = lineage_depth(lane_b10p, 11, fixture_index, split, work_dir,
                             "lane_b_depth11")
    lane_b12 = release_lineage(
        lane_b11, 12, SCHEDULE["merge_depth12_keep"], fixture_index, split,
        work_dir, "lane_b_depth12_release")

    current = merge_depth12(lane_a12, lane_b12, fixture_index, split, work_dir)
    for depth in range(13, WIDTH + 1):
        keep = (SCHEDULE["depth13_16_keep"] if depth <= 16
                else SCHEDULE["depth17_19_keep"])
        current = global_depth(current, depth, keep, fixture_index, split,
                               work_dir, f"merged_depth{depth}")
    result = final_resolve(current, fixture_index, split, work_dir)
    atomic_json(work_dir / "phase490_complete_result.json", result)
    return result


def self_test():
    if WIDTH != exact.WIDTH or WIDTH != front.WIDTH:
        raise AssertionError("width-19 modules disagree")
    parents = np.asarray([[0, 1], [1, 2]], dtype=np.uint8)
    children, parent_ids = expand_with_parent_indices(parents)
    expected = front.expand_bidirectional(parents)
    if not np.array_equal(children, expected) or parent_ids.shape != (len(children),):
        raise AssertionError("parent-index expansion changed")
    scores = np.arange(len(children), dtype=np.float64)
    kept, kept_scores = reserve_local_children(children, scores, parent_ids, 1)
    if len(kept) != 2 or len(kept_scores) != 2:
        raise AssertionError("local child reservation changed")
    roots = np.asarray([0, 0, 1, 1], dtype=np.int64)
    sample = np.asarray([[0, 1], [0, 2], [1, 2], [1, 3]], dtype=np.uint8)
    selected = select_per_root(sample, np.asarray([1., 2., 4., 3.]), roots, 1)
    if selected[0].tolist() != [[0, 2], [1, 2]]:
        raise AssertionError("root-local selection changed")
    return {"width": WIDTH, "schedule_sha256": schedule_sha256(),
            "checkpointed_per_depth": True, "faed_imported": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--run", action="store_true")
    parser.add_argument("--fixture-index", type=int, default=14)
    parser.add_argument("--split", choices=base.FIXTURE_SPLITS, default="dev")
    parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK_DIR)
    args = parser.parse_args()
    result = (self_test() if args.self_test else
              run(args.fixture_index, args.split, args.work_dir))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
