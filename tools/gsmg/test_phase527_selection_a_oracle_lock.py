import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase527_selection_a_oracle_lock as p527


def test_frozen_counts():
    assert p527.EXPECTED_BASE_COUNT == 112_624
    assert p527.EXPECTED_FORM_COUNT == 5_137_056


def test_form_count_includes_digit_only_gpu_forms():
    assert p527.EXPECTED_FORM_COUNT == 5_136_688 + 368


def test_lock_builder_has_no_oracle_function():
    assert not any(name.startswith("aes_try_open") for name in vars(p527))


def test_self_test():
    assert p527.self_test() == {"ok": True, "checks": 2}
