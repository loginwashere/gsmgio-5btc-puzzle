#!/usr/bin/env python3
"""Prepare and verify the Phase-527 Selection-A coordinate oracle lock.

This script never invokes Docker and never decrypts a blob.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
PROTOCOL = REPO_ROOT / "doc/Brainstorms/2026-09-19 - Phase 527 Selection A Coordinate Oracle Protocol.md"
PREP_SCRIPT = SCRIPT_DIR / "phase526_selection_a_slot_overlap.py"
P525_RESULT = SCRIPT_DIR / "phase525_selection_a_result.json"
OVERLAP_REPORT = REPO_ROOT / "_work/phase526/report.json"
BASES = REPO_ROOT / "_work/phase526/bases.txt"
BLOOM = REPO_ROOT / "db/addresses.hash160.bloom"
LOCK = SCRIPT_DIR / "phase527_execution_lock.json"

IMAGE = "gsmg-gpu-oracle:phase524-kt"
EXPECTED_IMAGE_ID = "sha256:cf2432d168e5dcb5018b57cc54a2a4d19df2f918e89388d1b78f7479850ab60a"
EXPECTED_GPU_UUID = "GPU-422f614f-fda3-a9fa-751f-f36612c276c0"
EXPECTED_BASE_COUNT = 112_624
EXPECTED_FORM_COUNT = 5_137_056
EXPECTED_BASE_SHA256 = "800e7a181a015416725d399059e8369c556a4f9e4e2fffe9e71f18f9fcd7ea36"
EXPECTED_P525_SHA256 = "82a46dc6c4077ee5626d0578d465ebaf64e141d6627e94848ef34483d02e9253"
EXPECTED_REPORT_SHA256 = "e05f22a887326af7cc76f123b86d03bd5ab19fd1df2402f81e184041ba6bf7b6"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def command_output(args: list[str]) -> str:
    return subprocess.run(args, check=True, text=True, capture_output=True).stdout.strip()


def current_environment() -> dict:
    image_id = command_output(["docker", "image", "inspect", IMAGE, "--format", "{{.Id}}"])
    gpu_uuid = command_output(["nvidia-smi", "--query-gpu=uuid", "--format=csv,noheader"]).splitlines()[0]
    return {"container_image": IMAGE, "container_image_id": image_id, "gpu_uuid": gpu_uuid}


def build_lock() -> dict:
    env = current_environment()
    if env["container_image_id"] != EXPECTED_IMAGE_ID:
        raise AssertionError(f"container image drifted: {env['container_image_id']}")
    if env["gpu_uuid"] != EXPECTED_GPU_UUID:
        raise AssertionError(f"GPU UUID drifted: {env['gpu_uuid']}")
    hashes = {
        "protocol_sha256": sha256_file(PROTOCOL),
        "prep_script_sha256": sha256_file(PREP_SCRIPT),
        "phase525_result_sha256": sha256_file(P525_RESULT),
        "overlap_report_sha256": sha256_file(OVERLAP_REPORT),
        "base_list_sha256": sha256_file(BASES),
        "bloom_cache_sha256": sha256_file(BLOOM),
    }
    if hashes["phase525_result_sha256"] != EXPECTED_P525_SHA256:
        raise AssertionError("Phase 525 result drifted")
    if hashes["overlap_report_sha256"] != EXPECTED_REPORT_SHA256:
        raise AssertionError("Phase 526 report drifted")
    if hashes["base_list_sha256"] != EXPECTED_BASE_SHA256:
        raise AssertionError("Phase 526 base list drifted")
    lines = BASES.read_text(encoding="utf-8").splitlines()
    if len(lines) != EXPECTED_BASE_COUNT or len(set(lines)) != EXPECTED_BASE_COUNT:
        raise AssertionError("base count or uniqueness drifted")
    if any(not line or line != line.strip() or line.startswith("#") for line in lines):
        raise AssertionError("unsafe base line")
    return {
        "phase": 527,
        "issued_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Selection-A 16-value matrixsumlist extension; SALPH primary, fixed four-blob GPU superset",
        **env,
        **hashes,
        "base_count": EXPECTED_BASE_COUNT,
        "expected_gpu_form_count": EXPECTED_FORM_COUNT,
        "options": ["--newline-variants"],
        "required_startup_markers": [
            "Bloom cache loaded",
            "folded in 8 known EC-derived target address(es)",
        ],
        "detectors": ["strong", "structural", "raw-key Bloom/API", "Phase-331 known-target"],
        "stop_rule": "one resumable run; zero exact/strong/structural/funded/known-target hits closes only this frozen universe",
    }


def write_lock() -> dict:
    if LOCK.exists():
        raise FileExistsError(f"lock already exists: {LOCK}")
    payload = build_lock()
    LOCK.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def verify_lock() -> dict:
    payload = json.loads(LOCK.read_text(encoding="utf-8"))
    expected = build_lock()
    ignored = {"issued_utc"}
    for key, value in expected.items():
        if key in ignored:
            continue
        if payload.get(key) != value:
            raise AssertionError(f"lock mismatch for {key}: {payload.get(key)!r} != {value!r}")
    return {"consistent": True, "lock_sha256": sha256_file(LOCK), "base_count": payload["base_count"]}


def self_test() -> dict:
    if EXPECTED_FORM_COUNT != 5_136_688 + 368:
        raise AssertionError("GPU form accounting drifted")
    if len(EXPECTED_BASE_SHA256) != 64 or len(EXPECTED_REPORT_SHA256) != 64:
        raise AssertionError("digest constant malformed")
    return {"ok": True, "checks": 2}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--write-lock", action="store_true")
    group.add_argument("--verify-lock", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), indent=2))
    elif args.write_lock:
        print(json.dumps(write_lock(), indent=2))
    else:
        print(json.dumps(verify_lock(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
