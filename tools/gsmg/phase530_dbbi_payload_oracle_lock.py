#!/usr/bin/env python3
"""Build and verify the Phase-530 DBBI payload oracle execution lock."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
PROTOCOL = REPO_ROOT / "doc/Brainstorms/2026-09-20 - Phase 530 DBBI Payload Oracle Protocol.md"
PREP_SCRIPT = SCRIPT_DIR / "phase529_dbbi_payload_material_overlap.py"
OVERLAP_RESULT = SCRIPT_DIR / "phase529_dbbi_payload_material_overlap_result.json"
BASES = REPO_ROOT / "_work/phase529/bases.txt"
BLOOM = REPO_ROOT / "db/addresses.hash160.bloom"
LOCK = SCRIPT_DIR / "phase530_execution_lock.json"

IMAGE = "gsmg-gpu-oracle:phase524-kt"
EXPECTED_IMAGE_ID = "sha256:cf2432d168e5dcb5018b57cc54a2a4d19df2f918e89388d1b78f7479850ab60a"
EXPECTED_GPU_UUID = "GPU-422f614f-fda3-a9fa-751f-f36612c276c0"
EXPECTED_RESULT_SHA256 = "2490cc9363d9af892066ff2eba2d41bca8282d76b2a2f3b306e1745faaeb6527"
EXPECTED_BASE_SHA256 = "2ac0d46de28a77d30cd670b8f35d7c67b2e22032830018d2c5fd3e820c919c3d"
EXPECTED_BLOOM_SHA256 = "376375ce1c63e5484cf941c422467d1d41b0b889c4b74fd4309e8cdb83882250"
EXPECTED_BASE_COUNT = 5
EXPECTED_FORM_COUNT = 90


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
    gpu_uuid = command_output(
        ["nvidia-smi", "--query-gpu=uuid", "--format=csv,noheader"]
    ).splitlines()[0]
    return {"container_image": IMAGE, "container_image_id": image_id, "gpu_uuid": gpu_uuid}


def build_lock(environment: dict | None = None) -> dict:
    env = current_environment() if environment is None else environment
    if env["container_image_id"] != EXPECTED_IMAGE_ID:
        raise AssertionError(f"container image drifted: {env['container_image_id']}")
    if env["gpu_uuid"] != EXPECTED_GPU_UUID:
        raise AssertionError(f"GPU UUID drifted: {env['gpu_uuid']}")
    hashes = {
        "protocol_sha256": sha256_file(PROTOCOL),
        "runner_sha256": sha256_file(Path(__file__)),
        "phase529_result_sha256": sha256_file(OVERLAP_RESULT),
        "base_list_sha256": sha256_file(BASES),
        "bloom_cache_sha256": sha256_file(BLOOM),
    }
    expected = {
        "phase529_result_sha256": EXPECTED_RESULT_SHA256,
        "base_list_sha256": EXPECTED_BASE_SHA256,
        "bloom_cache_sha256": EXPECTED_BLOOM_SHA256,
    }
    for name, value in expected.items():
        if hashes[name] != value:
            raise AssertionError(f"{name} drifted: {hashes[name]}")
    lines = BASES.read_text(encoding="utf-8").splitlines()
    if len(lines) != EXPECTED_BASE_COUNT or len(set(lines)) != EXPECTED_BASE_COUNT:
        raise AssertionError("Phase-530 base count/uniqueness drifted")
    if any(not line or line != line.strip() or not line.isalpha() for line in lines):
        raise AssertionError("unsafe Phase-530 base line")
    return {
        "phase": 530,
        "issued_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "five Phase-528 payload bases; fixed Phase-527 four-blob 60-variant oracle",
        **env,
        **hashes,
        "base_count": EXPECTED_BASE_COUNT,
        "expected_gpu_form_count": EXPECTED_FORM_COUNT,
        "options": ["--newline-variants"],
        "required_startup_markers": [
            "GPU kernel output matches the CPU reference oracle",
            "Bloom cache loaded",
            "folded in 8 known EC-derived target address(es)",
        ],
        "detectors": ["strong", "structural", "raw-key Bloom/API", "Phase-331 known-target"],
        "stop_rule": "one resumable run; zero decisive hits closes only the frozen five-base/90-form universe",
    }


def write_lock() -> dict:
    if LOCK.exists():
        raise FileExistsError(f"lock already exists: {LOCK}")
    payload = build_lock()
    LOCK.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def verify_lock() -> dict:
    actual = json.loads(LOCK.read_text(encoding="utf-8"))
    expected = build_lock()
    for key, value in expected.items():
        if key == "issued_utc":
            continue
        if actual.get(key) != value:
            raise AssertionError(f"lock mismatch for {key}")
    return {"consistent": True, "lock_sha256": sha256_file(LOCK)}


def self_test() -> None:
    fake = {
        "container_image": IMAGE,
        "container_image_id": EXPECTED_IMAGE_ID,
        "gpu_uuid": EXPECTED_GPU_UUID,
    }
    payload = build_lock(fake)
    assert payload["base_count"] == 5
    assert payload["expected_gpu_form_count"] == 90


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--write-lock", action="store_true")
    group.add_argument("--verify-lock", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("[*] Phase 530 lock self-test passed")
    elif args.write_lock:
        print(json.dumps(write_lock(), indent=2))
    else:
        print(json.dumps(verify_lock(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

