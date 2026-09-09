#!/usr/bin/env python3

import json
import tempfile
import unittest
from pathlib import Path

import phase482a_verify_run as verifier


class Phase482AVerifierTests(unittest.TestCase):
    def test_real_artifacts_recompute(self):
        with tempfile.TemporaryDirectory() as directory:
            record = verifier.verify(
                verifier.SCRIPT_DIR / "phase482a_execution_lock.json",
                verifier.SCRIPT_DIR / "phase482a_result.json",
                Path(directory) / "verification.json",
                recompute=True,
            )
            self.assertTrue(record["consistent"])

    def test_tampered_result_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            result = json.loads((verifier.SCRIPT_DIR / "phase482a_result.json").read_text())
            result["total_windows"] += 1
            changed = Path(directory) / "result.json"
            changed.write_text(json.dumps(result), encoding="utf-8")
            record = verifier.verify(
                verifier.SCRIPT_DIR / "phase482a_execution_lock.json",
                changed,
                Path(directory) / "verification.json",
                recompute=False,
            )
            self.assertFalse(record["consistent"])


if __name__ == "__main__":
    unittest.main()
