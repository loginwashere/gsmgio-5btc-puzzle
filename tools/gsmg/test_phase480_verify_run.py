#!/usr/bin/env python3

import json
import tempfile
import unittest
from pathlib import Path

import phase480_verify_run as verifier


class Phase480VerifierTests(unittest.TestCase):
    def test_real_artifacts_pass_with_recompute(self):
        with tempfile.TemporaryDirectory() as directory:
            record = verifier.verify(
                verifier.SCRIPT_DIR / "phase480_execution_lock.json",
                verifier.SCRIPT_DIR / "phase480_result.json",
                Path(directory) / "verification.json",
                recompute=True,
            )
            self.assertTrue(record["consistent"])

    def test_result_tamper_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            result = json.loads((verifier.SCRIPT_DIR / "phase480_result.json").read_text())
            result["decryptions"] = 7
            changed = Path(directory) / "result.json"
            changed.write_text(json.dumps(result), encoding="utf-8")
            record = verifier.verify(
                verifier.SCRIPT_DIR / "phase480_execution_lock.json",
                changed,
                Path(directory) / "verification.json",
                recompute=False,
            )
            self.assertFalse(record["consistent"])
            self.assertIn("result field mismatch: decryptions", record["errors"])


if __name__ == "__main__":
    unittest.main()
