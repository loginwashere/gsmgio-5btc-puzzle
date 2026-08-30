#!/usr/bin/env python3
"""Regression tests for the frozen Phase 456 transfer audit."""

import json
import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase456_seed1_unresolved_rule_transfer as module


class Phase456Seed1TransferTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = module.load_manifest()
        cls.report = module.build_report(cls.manifest)

    def test_full_self_test(self):
        module.self_test(self.manifest)

    def test_all_original_rules_replay(self):
        for rule in module.RULES:
            self.assertTrue(self.report["source_replays"][rule]["reproduced"])

    def test_zero_of_nine_transfer_cells_are_applicable(self):
        self.assertEqual(self.report["applicable_cells"], 0)
        self.assertEqual(self.report["total_cells"], 9)
        for rule in module.RULES:
            for boundary in module.BOUNDARIES:
                row = self.report["transfer_matrix"][rule][boundary]
                self.assertEqual(row["status"], "not_applicable")
                self.assertEqual(row["candidate_count"], 0)
                self.assertIsNone(row["rank"])

    def test_nonapplicability_does_not_reject_rules(self):
        self.assertEqual(
            set(self.report["rule_outcomes"].values()),
            {"insufficient_comparable_boundaries"},
        )
        self.assertFalse(self.report["seed1_support_added"])
        self.assertFalse(self.report["rules_rejected"])
        self.assertEqual(self.report["gap_closures"], 0)

    def test_no_password_or_oracle_activity(self):
        self.assertEqual(self.report["new_password_candidates"], 0)
        self.assertEqual(self.report["oracle_calls"], 0)
        self.assertEqual(self.report["decryptions_attempted"], 0)

    def test_saved_result_contract_when_present(self):
        if not module.RESULT_PATH.exists():
            self.skipTest("Phase 456 result has not been generated")
        saved = json.loads(module.RESULT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(saved["manifest_sha256"], module.EXPECTED_MANIFEST_SHA256)
        self.assertEqual(
            saved["overall_verdict"],
            "all_three_insufficient_comparable_boundaries",
        )


if __name__ == "__main__":
    unittest.main()
