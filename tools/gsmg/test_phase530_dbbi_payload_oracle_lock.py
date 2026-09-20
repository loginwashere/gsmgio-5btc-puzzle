import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase530_dbbi_payload_oracle_lock as phase530


def fake_environment():
    return {
        "container_image": phase530.IMAGE,
        "container_image_id": phase530.EXPECTED_IMAGE_ID,
        "gpu_uuid": phase530.EXPECTED_GPU_UUID,
    }


def test_lock_payload_pins_five_bases_and_ninety_forms():
    payload = phase530.build_lock(fake_environment())
    assert payload["base_count"] == 5
    assert payload["expected_gpu_form_count"] == 90
    assert payload["options"] == ["--newline-variants"]


def test_lock_payload_pins_phase529_result_and_base_list():
    payload = phase530.build_lock(fake_environment())
    assert payload["phase529_result_sha256"] == phase530.EXPECTED_RESULT_SHA256
    assert payload["base_list_sha256"] == phase530.EXPECTED_BASE_SHA256


def test_wrong_environment_fails_closed():
    env = fake_environment()
    env["gpu_uuid"] = "wrong"
    try:
        phase530.build_lock(env)
    except AssertionError:
        pass
    else:
        raise AssertionError("wrong GPU environment was accepted")

