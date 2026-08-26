#!/usr/bin/env python3
"""Focused regression for Phase 422's macro-clue panel implementation."""

import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase422_p32trailing_macro_clue_panel_audit as phase422


class Phase422RegressionTests(unittest.TestCase):
    def test_frozen_macro_clue_panel(self):
        report = phase422.self_test()
        self.assertEqual(report["packet_sha256"], phase422.EVIDENCE_PACKET_SHA256)
        self.assertEqual(report["prompt_sha256"], phase422.PROMPT_SHA256)
        self.assertEqual(report["launcher_sha256"], phase422.LAUNCHER_SHA256)
        self.assertLessEqual(report["prompt_line_count"], 320)
        self.assertEqual(report["comparator"]["union"]["count"], phase422.COMPARATOR_UNION_COUNT)
        self.assertEqual(report["solver_invocations"], 0)


if __name__ == "__main__":
    unittest.main()
