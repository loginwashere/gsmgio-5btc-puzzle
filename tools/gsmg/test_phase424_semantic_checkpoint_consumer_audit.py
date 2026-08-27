#!/usr/bin/env python3
"""Focused regression for the Phase 424 semantic checkpoint audit."""

import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase424_semantic_checkpoint_consumer_audit as phase424


class Phase424RegressionTests(unittest.TestCase):
    def test_recognition_does_not_promote_a_consumer(self):
        report = phase424.self_test()
        self.assertEqual(report["outcome"], "recognition_only_no_forward_edge")
        self.assertEqual(report["oracle_calls"], 0)
        self.assertEqual(report["strongest_recognition_family"], "farewell")
        self.assertEqual(report["most_local_live_role"], "faed_plaintext_is_password")

    def test_phase423_partition_is_exact(self):
        _result, promoted = phase424.phase423_state()
        declared = {
            member
            for members in phase424.FAMILY_MEMBERS.values()
            for member in members
        }
        self.assertEqual(set(promoted), declared)
        self.assertEqual(len(promoted), 12)


if __name__ == "__main__":
    unittest.main()
