#!/usr/bin/env python3
"""Fail-closed verification of the completed Phase-511 calibration."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import phase510a_closed_vocabulary_manifest as phase510a
import phase511_closed_corpus_character_signal as phase511
from quadgram_solver import load_quadgrams


VERIFICATION = phase511.SCRIPT_DIR / "phase511_verification.json"


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(write: bool = False) -> dict:
    lock = phase511.verify_lock()
    if not phase511.RESULT.is_file():
        raise RuntimeError("Phase-511 result is absent")
    actual = json.loads(phase511.RESULT.read_text())
    regions = phase510a.literal_regions()
    quadgrams, floor = load_quadgrams(phase511.QUADGRAMS)
    fixtures = [phase511.evaluate_fixture(source, index, regions, quadgrams, floor)
                for index, source in enumerate(phase511.EVALUATION_SOURCES)]
    expected = {
        "phase": "511",
        "status": "heldout_character_signal_complete",
        "execution_lock_sha256": sha(phase511.LOCK),
        "faed_scored": False,
        "fixtures": fixtures,
        "gate_passed": all(row["fixture_gate_passed"] for row in fixtures),
        "verdict": ("licenses_separate_known_order_ceiling"
                    if all(row["fixture_gate_passed"] for row in fixtures)
                    else "closed_corpus_character_model_stops_before_faed"),
    }
    consistent = actual == expected
    record = {
        "phase": "511",
        "consistent": consistent,
        "execution_lock_sha256": sha(phase511.LOCK),
        "result_sha256": sha(phase511.RESULT),
        "protocol_sha256": lock["files_sha256"]["protocol"],
        "runner_sha256": lock["files_sha256"]["runner"],
        "fixture_count": len(fixtures),
        "null_trials_recomputed": len(fixtures) * phase511.NULL_TRIALS,
        "transfer_pass_count": sum(row["transfer_gate_passed"] for row in fixtures),
        "incremental_value_pass_count": sum(
            row["incremental_value_gate_passed"] for row in fixtures),
        "faed_scored": actual.get("faed_scored"),
    }
    if not consistent:
        raise RuntimeError("Phase-511 result does not reproduce exactly")
    if write:
        phase511.atomic_json(VERIFICATION, record)
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    print(json.dumps(verify(write=args.write), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
