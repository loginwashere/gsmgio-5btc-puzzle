#!/usr/bin/env python3
"""Parity and timing harness for the isolated persistent extension server."""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import phase484a_raw_symbol_vic_solver as base
import phase484g_hard_negative_discriminator as learned
import phase484j_constructive_prefix_beam_probe as prefix
import phase484q_blind_joint_width19_solver as solver
import phase484w_persistent_extension as persistent

SCRIPT_DIR = Path(__file__).resolve().parent
REFERENCE = SCRIPT_DIR / "phase484q_capacity_broad_random_i51_e256.json"
OUTPUT = SCRIPT_DIR / "phase484w_persistent_extension_benchmark.json"
REFERENCE_SHA256 = "506937a48e325a77486b1fe6023bc9495e8892d2c406555959276d5f1097438d"
WORKERS = 8
SEEDS = 256


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def self_test():
    if sha256_file(REFERENCE) != REFERENCE_SHA256:
        raise AssertionError("reference artifact hash mismatch")
    artifact = json.loads(REFERENCE.read_text())
    if artifact["extension_seed_count"] != SEEDS:
        raise AssertionError("reference seed count mismatch")
    if len(artifact["refined_population"]) < SEEDS:
        raise AssertionError("reference population is too short")
    if not persistent.DEFAULT_BINARY.exists():
        raise AssertionError("persistent CUDA binary is missing")


def run(output):
    self_test()
    artifact = json.loads(REFERENCE.read_text())
    fixture = base.make_fixture(
        solver.WIDTH, learned.PAIR_INDEX, 51, seed=learned.SEED,
        board_mode="broad_random", split="dev")
    blocks = prefix.blocks_from_observed(fixture)
    pair = tuple(fixture["pair"])
    quad, _ = base.load_language_model()
    began = time.monotonic()
    terminals, diagnostics = persistent.extend_population(
        blocks, pair, quad, artifact["refined_population"], SEEDS,
        workers=WORKERS)
    seconds = time.monotonic() - began
    if terminals != artifact["terminal_orders"]:
        raise AssertionError("persistent terminals differ from reference")
    if diagnostics != artifact["extension_diagnostics"]:
        raise AssertionError("persistent diagnostics differ from reference")
    result = {
        "phase": "484W",
        "status": "development_persistent_extension_parity_complete",
        "faed_scored": False,
        "reference_sha256": REFERENCE_SHA256,
        "persistent_source_sha256": sha256_file(Path(persistent.__file__)),
        "persistent_cuda_sha256": sha256_file(
            SCRIPT_DIR / "phase484w_persistent_board_score_server.cu"),
        "persistent_binary_sha256": sha256_file(
            persistent.DEFAULT_BINARY),
        "workers": WORKERS,
        "seeds": SEEDS,
        "terminals": len(terminals),
        "exact_terminal_parity": True,
        "exact_diagnostic_parity": True,
        "reference_serial_seconds": artifact["extension_seconds"],
        "persistent_seconds": seconds,
        "speedup_over_serial": artifact["extension_seconds"] / seconds,
    }
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(json.dumps(result, indent=2) + "\n")
    temporary.replace(output)
    return result


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--run", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("self-test: ok")
        return 0
    print(json.dumps(run(args.output), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
