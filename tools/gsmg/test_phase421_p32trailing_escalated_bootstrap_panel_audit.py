#!/usr/bin/env python3
"""Focused regression for Phase 421's escalated bootstrap adapter."""

import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase421_p32trailing_escalated_bootstrap_panel_audit as phase421


class Phase421RegressionTests(unittest.TestCase):
    def test_frozen_escalated_bootstrap_panel(self):
        report = phase421.self_test()
        self.assertEqual(report["launcher_length"], phase421.LAUNCHER_LENGTH)
        self.assertEqual(report["launcher_sha256"], phase421.LAUNCHER_SHA256)
        self.assertEqual(report["prompt_sha256"], phase421.phase420.PROMPT_SHA256)
        self.assertLessEqual(report["prompt_line_count"], 260)
        self.assertEqual(report["diagnostic_invocations_excluded"], 1)
        self.assertEqual(report["panel_invocations"], 0)


if __name__ == "__main__":
    unittest.main()
