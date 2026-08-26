#!/usr/bin/env python3
"""Focused regression for the frozen Phase 418 implementation."""

import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase418_p32trailing_solution_complete_blinded_reconstruction_audit as phase418


class Phase418RegressionTests(unittest.TestCase):
    def test_frozen_solution_complete_panel(self):
        report = phase418.self_test()
        self.assertEqual(report["packet_length"], phase418.SEALED_EVIDENCE_PACKET_LENGTH)
        self.assertEqual(report["packet_sha256"], phase418.SEALED_EVIDENCE_PACKET_SHA256)
        self.assertEqual(report["prompt_length"], phase418.SOLVER_PROMPT_LENGTH)
        self.assertEqual(report["prompt_sha256"], phase418.SOLVER_PROMPT_SHA256)
        self.assertEqual(report["phase270_base_candidates"], 25)
        self.assertEqual(report["phase270_materials"], 50)
        self.assertEqual(report["solver_invocations"], 0)


if __name__ == "__main__":
    unittest.main()
