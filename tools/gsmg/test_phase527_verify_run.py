import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase527_verify_run as verify


def test_checkpoint_is_complete_and_contiguous():
    result = verify.verify_checkpoint()
    assert result["completed_forms"] == 5_137_056
    assert result["line_count"] == 5_137_057


def test_completed_run_verifies_negative():
    result = verify.verify()
    assert result["consistent"]
    assert result["strong_hits"] == 0
    assert result["structural_hits"] == 0
    assert result["confirmed_funded"] == 0
    assert result["known_target_matches"] == 0
    assert result["weak_rows"] == 159


def test_saved_verification_matches_fresh_result():
    saved = json.loads(verify.VERIFICATION.read_text(encoding="utf-8"))
    assert saved == verify.verify()
