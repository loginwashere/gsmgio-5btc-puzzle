#!/usr/bin/env python3
"""Regression tests for the frozen Phase 453 symbolic calibration."""

import json
import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase453_false_discovery_calibration as module


class Phase453CalibrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = module.load_manifest()

    def test_controls(self):
        module.self_test(self.manifest)

    def test_manifest_contract(self):
        self.assertEqual(tuple(self.manifest["cases"]), module.CASE_IDS)
        self.assertEqual(
            self.manifest["phase_level_disposition"],
            "calibration_only_no_gap_closure",
        )
        self.assertEqual(self.manifest["trials_per_monte_carlo_null"], 100000)

    def test_real_scores_reproduce_canonical_audits(self):
        report = module.score_real_cases(self.manifest)
        self.assertEqual({case: row["score"] for case, row in report.items()}, {
            "S-KIT": 1,
            "S-FF67": 2,
            "S-GGN": 2,
            "S-ROMAN": 2,
        })
        self.assertIn("kit", report["S-KIT"]["hits"])
        self.assertIn((255, 103), report["S-FF67"]["hits"])
        self.assertIn("ggn", report["S-GGN"]["hits"])
        self.assertEqual(report["S-ROMAN"]["fefe_under_winning_rule"], 100)

    def test_short_nulls_are_deterministic(self):
        for case_id in module.CASE_IDS:
            runner = module.NULL_RUNNERS[case_id]
            first = runner(self.manifest, 50, "primary")
            second = runner(self.manifest, 50, "primary")
            self.assertEqual(first, second)

    def test_saved_result_contract_when_present(self):
        if not module.RESULT_PATH.exists():
            self.skipTest("Phase 453 real run has not been executed")
        report = json.loads(module.RESULT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(report["manifest_sha256"], module.EXPECTED_MANIFEST_SHA256)
        self.assertTrue(report["nulls_completed_before_real_scoring"])
        self.assertFalse(report["oracle_run"])
        self.assertEqual(report["password_materials_generated"], 0)
        self.assertEqual(set(report["decisions"]), set(module.CASE_IDS))
        self.assertEqual(
            {case: row["state"] for case, row in report["decisions"].items()},
            {
                "S-KIT": "sensitive_to_null_design",
                "S-FF67": "unusual_but_unselected",
                "S-GGN": "common_under_matched_null",
                "S-ROMAN": "common_under_matched_null",
            },
        )


if __name__ == "__main__":
    unittest.main()
