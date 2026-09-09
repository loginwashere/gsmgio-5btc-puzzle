#!/usr/bin/env python3

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import phase479_verify_run as verifier


class Phase479VerifierTests(unittest.TestCase):
    def test_real_artifacts_pass_without_recompute(self):
        with tempfile.TemporaryDirectory() as directory:
            record = verifier.verify(
                verifier.SCRIPT_DIR / "phase479_execution_lock.json",
                verifier.SCRIPT_DIR / "phase479_result.json",
                Path(directory) / "verification.json",
                recompute=False,
            )
            self.assertTrue(record["consistent"])

    def test_result_tamper_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            result = json.loads((verifier.SCRIPT_DIR / "phase479_result.json").read_text())
            result["decryptions"] -= 1
            changed = Path(directory) / "result.json"
            changed.write_text(json.dumps(result))
            record = verifier.verify(
                verifier.SCRIPT_DIR / "phase479_execution_lock.json",
                changed,
                Path(directory) / "verification.json",
                recompute=False,
            )
            self.assertFalse(record["consistent"])

    def test_locked_source_tamper_fails_before_import(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.dict(
            verifier.FILE_PATHS, {"audit_script": Path(directory) / "changed.py"}
        ):
            verifier.FILE_PATHS["audit_script"].write_text("raise AssertionError('must not import')\n")
            record = verifier.verify(
                verifier.SCRIPT_DIR / "phase479_execution_lock.json",
                verifier.SCRIPT_DIR / "phase479_result.json",
                Path(directory) / "verification.json",
                recompute=True,
            )
            self.assertFalse(record["consistent"])
            self.assertIn("hash mismatch: audit_script", record["errors"])


if __name__ == "__main__":
    unittest.main()

