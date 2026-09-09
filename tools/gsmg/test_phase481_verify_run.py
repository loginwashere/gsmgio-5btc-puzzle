#!/usr/bin/env python3

import json
import tempfile
import unittest
from pathlib import Path

import phase481_verify_run as verifier


class Phase481VerifierTests(unittest.TestCase):
    def test_real_artifacts_pass_with_recompute(self):
        with tempfile.TemporaryDirectory() as directory:
            record = verifier.verify(
                verifier.SCRIPT_DIR / "phase481_execution_lock.json",
                verifier.SCRIPT_DIR / "phase481_result.json",
                Path(directory) / "verification.json",
                recompute=True,
            )
            self.assertTrue(record["consistent"], record["errors"])

    def test_result_tamper_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            result = json.loads((verifier.SCRIPT_DIR / "phase481_result.json").read_text())
            result["attempted"] = result["attempted"] - 1
            changed = Path(directory) / "result.json"
            changed.write_text(json.dumps(result), encoding="utf-8")
            record = verifier.verify(
                verifier.SCRIPT_DIR / "phase481_execution_lock.json",
                changed,
                Path(directory) / "verification.json",
                recompute=False,
            )
            self.assertFalse(record["consistent"])
            self.assertIn("result field mismatch: attempted", record["errors"])

    def test_promoted_count_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            result = json.loads((verifier.SCRIPT_DIR / "phase481_result.json").read_text())
            result["promoted_count"] = result["promoted_count"] + 1
            changed = Path(directory) / "result.json"
            changed.write_text(json.dumps(result), encoding="utf-8")
            record = verifier.verify(
                verifier.SCRIPT_DIR / "phase481_execution_lock.json",
                changed,
                Path(directory) / "verification.json",
                recompute=False,
            )
            self.assertFalse(record["consistent"])
            self.assertIn(
                "promoted count is not the sum of its two tiers", record["errors"]
            )


if __name__ == "__main__":
    unittest.main()
