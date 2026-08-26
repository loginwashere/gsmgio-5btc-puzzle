#!/usr/bin/env python3
"""Focused regression for Phase 420's one-file bootstrap adapter."""

import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase420_p32trailing_one_file_bootstrap_panel_audit as phase420


class Phase420RegressionTests(unittest.TestCase):
    def test_frozen_one_file_bootstrap_panel(self):
        report = phase420.self_test()
        self.assertEqual(report["prompt_length"], phase420.PROMPT_LENGTH)
        self.assertEqual(report["prompt_sha256"], phase420.PROMPT_SHA256)
        self.assertLessEqual(report["prompt_line_count"], 260)
        self.assertEqual(report["launcher_length"], phase420.LAUNCHER_LENGTH)
        self.assertEqual(report["launcher_sha256"], phase420.LAUNCHER_SHA256)
        self.assertEqual(report["phase270_base_candidates"], 25)
        self.assertEqual(report["phase270_materials"], 50)
        self.assertEqual(report["solver_invocations"], 0)


if __name__ == "__main__":
    unittest.main()
