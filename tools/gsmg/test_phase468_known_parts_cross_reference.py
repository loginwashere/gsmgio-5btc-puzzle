#!/usr/bin/env python3
"""External regression test for Phase 468.

Outcome-dependent assertions live here, not inside the audited script
(phase468_known_parts_cross_reference.py) -- editing the script after its
digest was pinned in phase468_execution_lock.json would invalidate the
lock. This test recomputes live and compares against the pinned
phase468_result.json by value, and separately confirms the audited
script's digest is still the one pinned in the execution lock.
"""

import hashlib
import json
import unittest
from pathlib import Path

import phase468_known_parts_cross_reference as audit

SCRIPT_DIR = Path(__file__).resolve().parent


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Phase468ResultRegressionTest(unittest.TestCase):
    def setUp(self):
        self.lock = json.loads((SCRIPT_DIR / "phase468_execution_lock.json").read_text())
        self.pinned_result = json.loads((SCRIPT_DIR / "phase468_result.json").read_text())
        self.result_record = json.loads((SCRIPT_DIR / "phase468_result_record.json").read_text())

    def test_execution_lock_unchanged_since_freeze(self):
        script_path = SCRIPT_DIR / self.lock["audit_script"]["path"].split("/")[-1]
        self.assertEqual(sha256_path(script_path), self.lock["audit_script"]["sha256"])
        catalog_path = SCRIPT_DIR / self.lock["catalog"]["path"].split("/")[-1]
        self.assertEqual(sha256_path(catalog_path), self.lock["catalog"]["sha256"])

    def test_result_record_matches_pinned_files(self):
        result_path = SCRIPT_DIR / "phase468_result.json"
        self.assertEqual(sha256_path(result_path), self.result_record["result_sha256"])
        lock_path = SCRIPT_DIR / "phase468_execution_lock.json"
        self.assertEqual(sha256_path(lock_path), self.result_record["execution_lock_sha256"])

    def test_live_recomputation_matches_pinned_result(self):
        manifest = audit.load_manifest()
        live_report = audit.build_report(manifest)
        self.assertEqual(live_report, self.pinned_result)

    def test_output_2_arithmetic(self):
        arithmetic = self.pinned_result["output_2_arithmetic_31"]
        self.assertTrue(arithmetic["is_prime"])
        self.assertEqual(arithmetic["nondegenerate_rectangular_factorizations"], [])

    def test_lane_a_reports_two_hypotheses_only(self):
        for population in self.pinned_result["output_3_lane_a"]["populations"].values():
            self.assertEqual(set(population["holm_p"]), {"g_i_primary", "union_e_g_h_i"})

    def test_lane_b_target_set_pinned_to_ten(self):
        self.assertEqual(self.pinned_result["output_3_lane_b"]["target_set_size"], 10)
        self.assertEqual(
            self.pinned_result["output_3_lane_b"]["target_set_source"],
            "raw_key_chunk_audit.known_targets()",
        )

    def test_zero_password_or_oracle_activity(self):
        self.assertEqual(self.pinned_result["password_materials_generated"], 0)
        self.assertEqual(self.pinned_result["oracle_calls"], 0)
        self.assertEqual(self.pinned_result["decryptions_attempted"], 0)


if __name__ == "__main__":
    unittest.main()
