#!/usr/bin/env python3
"""Focused regression for Phase 423's macro-clue panel implementation."""

import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase423_p32trailing_macro_clue_panel_audit as phase423


class Phase423RegressionTests(unittest.TestCase):
    def test_frozen_macro_clue_panel(self):
        report = phase423.self_test()
        self.assertEqual(report["packet_sha256"], phase423.EVIDENCE_PACKET_SHA256)
        self.assertEqual(report["prompt_sha256"], phase423.PROMPT_SHA256)
        self.assertEqual(report["launcher_sha256"], phase423.LAUNCHER_SHA256)
        self.assertLessEqual(report["prompt_line_count"], 320)
        self.assertEqual(report["comparator"]["union"]["count"], phase423.COMPARATOR_UNION_COUNT)
        self.assertEqual(report["solver_invocations"], 0)

    def test_disclosed_residues_are_allowed_but_hidden_residues_are_not(self):
        prompt = phase423.PROMPT_PATH.read_text(encoding="utf-8")
        self.assertEqual(phase423.disclosed_response_residues(prompt),
                         phase423.DISCLOSED_RESPONSE_RESIDUES)
        self.assertEqual(phase423.response_blinding_violations("SalPhaseIon yinyang"), [])
        self.assertIn("DBBI", phase423.response_blinding_violations("SalPhaseIon DBBI"))


if __name__ == "__main__":
    unittest.main()
