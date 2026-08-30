#!/usr/bin/env python3
"""Regression tests for the frozen Phase 455 typed semantic checksum."""

import json
import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase455_thispassword_typed_semantic_checksum as module


class Phase455TypedSemanticChecksumTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = module.load_manifest()
        cls.report = module.build_report(cls.manifest)

    def test_full_self_test(self):
        module.self_test(self.manifest)

    def test_all_roles_survive_without_scoring(self):
        self.assertEqual(self.report["verdict"], "all_roles_survive")
        self.assertEqual(self.report["surviving_roles"], list(module.ROLES))
        self.assertIsNone(self.report["role_selected"])
        self.assertFalse(self.report["typed_discriminant_found"])
        self.assertEqual(
            self.report["contradiction_counts"],
            {role: 0 for role in module.ROLES},
        )
        self.assertEqual(self.report["weighted_scores_computed"], 0)

    def test_enter_and_sha_are_scoped(self):
        facts = self.report["facts"]
        self.assertTrue(facts["enter_is_between_salph_halves"])
        self.assertEqual(facts["enter_split_offsets"], [64, 64])
        self.assertEqual(
            facts["decoded_local_terms"]["sha256"],
            "sha256 our first hint is your last command",
        )
        self.assertFalse(facts["explicit_attachment_marker_present"])

    def test_every_role_has_exactly_seven_typed_axes(self):
        for role in module.ROLES:
            self.assertEqual(tuple(self.report["matrix"][role]), module.AXES)
            self.assertTrue(
                all(
                    row["state"] in module.CELL_STATES
                    for row in self.report["matrix"][role].values()
                )
            )

    def test_no_password_or_oracle_activity(self):
        self.assertEqual(self.report["oracle_calls"], 0)
        self.assertEqual(self.report["password_materials_generated"], 0)
        self.assertEqual(self.report["decryptions_attempted"], 0)
        self.assertEqual(self.report["gap_closures"], 0)

    def test_saved_result_contract_when_present(self):
        if not module.RESULT_PATH.exists():
            self.skipTest("Phase 455 result has not been generated")
        saved = json.loads(module.RESULT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(saved["manifest_sha256"], module.EXPECTED_MANIFEST_SHA256)
        self.assertEqual(saved["verdict"], "all_roles_survive")
        self.assertEqual(
            saved["disposition"], "typed_constraints_confirm_underdetermination"
        )


if __name__ == "__main__":
    unittest.main()
