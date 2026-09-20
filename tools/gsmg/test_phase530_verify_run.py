import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase530_verify_run as verify


def make_checkpoint(path, count=90):
    header = {"header": True, "version": 1, "candidate_count": count}
    path.write_text(
        json.dumps(header) + "\n" + "".join(f"{index}\n" for index in range(count)),
        encoding="utf-8",
    )


def test_checkpoint_accepts_exact_contiguous_family(tmp_path):
    path = tmp_path / "checkpoint"
    make_checkpoint(path)
    result = verify.verify_checkpoint(path)
    assert result["completed_forms"] == 90
    assert result["line_count"] == 91


def test_checkpoint_rejects_wrong_count(tmp_path):
    path = tmp_path / "checkpoint"
    make_checkpoint(path, count=89)
    try:
        verify.verify_checkpoint(path)
    except AssertionError:
        pass
    else:
        raise AssertionError("wrong candidate count was accepted")


def test_checkpoint_rejects_discontinuity(tmp_path):
    path = tmp_path / "checkpoint"
    make_checkpoint(path)
    lines = path.read_text().splitlines()
    lines[10] = "999"
    path.write_text("\n".join(lines) + "\n")
    try:
        verify.verify_checkpoint(path)
    except AssertionError:
        pass
    else:
        raise AssertionError("checkpoint discontinuity was accepted")

