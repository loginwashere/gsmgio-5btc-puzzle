#!/usr/bin/env python3
"""Regression tests for the frozen Phase 454 acquisition audit."""

import json
import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase454_recipient_artifact_acquisition as module


class Phase454AcquisitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = module.load_manifest()

    def test_full_self_test(self):
        module.self_test(self.manifest)

    def test_no_primary_artifact_or_oracle(self):
        report = module.build_report(self.manifest)
        self.assertEqual(report["new_primary_artifact"], 0)
        self.assertEqual(report["new_recipient_copy_known_bytes"], 2)
        self.assertEqual(report["gap_closures"], 0)
        self.assertFalse(report["oracle_run"])
        self.assertEqual(report["password_materials_generated"], 0)
        self.assertFalse(report["external_outreach"])

    def test_attachment_ledger_is_complete_and_disjoint(self):
        ledger = json.loads(module.LEDGER_PATH.read_text(encoding="utf-8"))
        rows = ledger["attachments"]
        self.assertEqual(len(rows), 65)
        self.assertEqual(len({row["url"] for row in rows}), 65)
        self.assertEqual(
            sum(row["classification"] == "fabricated_or_spam" for row in rows),
            49,
        )
        self.assertEqual(
            sum(
                row["classification"] == "new_community_derivative"
                for row in rows
            ),
            15,
        )
        self.assertEqual(
            sum(row["classification"] == "access_limited" for row in rows),
            1,
        )

    def test_urlscan_hashes_match_local_icons(self):
        observed = tuple(
            module.sha256_path(module.ROOT / path) for path in module.ICON_PATHS
        )
        self.assertEqual(observed, module.EXPECTED_ICON_HASHES)

    def test_saved_result_contract_when_present(self):
        if not module.RESULT_PATH.exists():
            self.skipTest("Phase 454 result has not been generated")
        result = json.loads(module.RESULT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(result["manifest_sha256"], module.EXPECTED_MANIFEST_SHA256)
        self.assertEqual(result["new_primary_artifact"], 0)
        self.assertEqual(
            result["disposition"], "provenance_upgraded_no_new_clue_content"
        )


if __name__ == "__main__":
    unittest.main()
