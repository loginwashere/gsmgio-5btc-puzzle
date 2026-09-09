#!/usr/bin/env python3
"""End-to-end parity check for the Phase 484W persistent CUDA backend."""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import phase484q_blind_joint_width19_solver as solver

SCRIPT_DIR = Path(__file__).resolve().parent
REFERENCE = SCRIPT_DIR / "phase484q_capacity_broad_random_i51_e256.json"
REFERENCE_SHA256 = "506937a48e325a77486b1fe6023bc9495e8892d2c406555959276d5f1097438d"
OUTPUT = SCRIPT_DIR / "phase484w_full_pipeline_parity.json"
LARGE_FIELDS = (
    "true_records",
    "refined_population",
    "terminal_orders",
    "final_candidates",
    "skipped_terminals",
    "extension_diagnostics",
)
SCALAR_FIELDS = (
    "true_segments_retained",
    "best_true_coarse_rank",
    "best_true_board_accuracy",
    "best_true_refined_rank",
    "best_true_refined_board_accuracy",
    "exact_order_in_terminals",
    "exact_order_extension_rank",
    "exact_order_final_rank",
    "top1_exact_order",
    "top1_plaintext_accuracy",
    "top1_final_normalized_score",
    "terminals_total",
    "terminals_valid",
    "terminals_skipped_invalid_segmentation",
)


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def compare(reference, candidate):
    scalar_equal = {
        field: reference[field] == candidate[field] for field in SCALAR_FIELDS
    }
    field_hashes = {}
    for field in LARGE_FIELDS:
        expected = canonical_sha256(reference[field])
        observed = canonical_sha256(candidate[field])
        field_hashes[field] = {
            "reference": expected,
            "persistent": observed,
            "equal": expected == observed,
        }
    return {
        "scalar_equal": scalar_equal,
        "large_field_hashes": field_hashes,
        "exact_parity": all(scalar_equal.values()) and all(
            record["equal"] for record in field_hashes.values()
        ),
    }


def self_test(reference=REFERENCE, binary=solver.PERSISTENT_BINARY):
    if file_sha256(reference) != REFERENCE_SHA256:
        raise AssertionError("saved Phase 484Q reference hash changed")
    if not Path(binary).is_file():
        raise AssertionError("persistent CUDA binary is missing")
    sample = {field: index for index, field in enumerate(SCALAR_FIELDS)}
    sample.update({field: [field] for field in LARGE_FIELDS})
    if not compare(sample, sample)["exact_parity"]:
        raise AssertionError("identity comparison failed")
    changed = dict(sample)
    changed["terminal_orders"] = ["changed"]
    if compare(sample, changed)["exact_parity"]:
        raise AssertionError("changed field was not detected")
    return {
        "reference_sha256": REFERENCE_SHA256,
        "persistent_binary_sha256": file_sha256(binary),
        "comparison_self_test": True,
    }


def run(reference=REFERENCE, binary=solver.PERSISTENT_BINARY):
    checks = self_test(reference, binary)
    saved = json.loads(Path(reference).read_text())
    began = time.monotonic()
    candidate = solver.screen_fixture(
        mode="broad_random",
        fixture_index=51,
        keep=262144,
        refine_keep=8192,
        extend_seed_count=256,
        extend_workers=8,
        extension_backend="persistent",
        persistent_binary=binary,
    )
    wall_seconds = time.monotonic() - began
    comparison = compare(saved, candidate)
    result = {
        "phase": "484W",
        "status": "full_pipeline_parity_complete",
        "reference": str(Path(reference).relative_to(SCRIPT_DIR.parents[1])),
        **checks,
        "fixture": {"board_mode": "broad_random", "index": 51},
        "capacity": {
            "shortlist": 262144,
            "refine_keep": 8192,
            "extend_seeds": 256,
            "extend_workers": 8,
        },
        "persistent_timings": {
            "shortlist_seconds": candidate["shortlist_seconds"],
            "gpu_screen_seconds": candidate["gpu_screen_seconds"],
            "gpu_refine_seconds": candidate["gpu_refine_seconds"],
            "extension_seconds": candidate["extension_seconds"],
            "final_seconds": candidate["final_seconds"],
            "wall_seconds": wall_seconds,
        },
        "reference_extension_seconds": saved["extension_seconds"],
        "extension_speedup_vs_serial_reference": (
            saved["extension_seconds"] / candidate["extension_seconds"]
        ),
        **comparison,
    }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--reference", type=Path, default=REFERENCE)
    parser.add_argument("--binary", type=Path, default=solver.PERSISTENT_BINARY)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(args.reference, args.binary), indent=2))
        return 0
    if not args.run:
        parser.error("use --self-test or --run")
    result = run(args.reference, args.binary)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["exact_parity"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
