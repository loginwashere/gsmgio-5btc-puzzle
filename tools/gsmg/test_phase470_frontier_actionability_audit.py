#!/usr/bin/env python3

import unittest

import phase470_frontier_actionability_audit as audit


class Phase470Test(unittest.TestCase):
    def setUp(self):
        self.report = audit.build_report()

    def test_four_selectors_and_zero_executable_tests(self):
        self.assertEqual(self.report["selector_count"], 4)
        self.assertEqual(self.report["executable_current_internal_tests"], [])
        self.assertEqual(self.report["executable_current_internal_test_count"], 0)

    def test_architect_leverage_is_conditional_not_executable(self):
        self.assertEqual(self.report["highest_conditional_leverage"], "architect_edge_mirror_relation")
        self.assertEqual(self.report["highest_conditional_leverage_downstream_count"], 2)
        self.assertIsNone(self.report["highest_executable_leverage"])
        self.assertEqual(self.report["stale_registry_action"]["classification"], "duplicate_of_phase456")

    def test_lane_a_same_data_is_not_blind(self):
        lane = self.report["lane_a_blind_followup"]
        self.assertEqual(lane["same_ff67_endpoint"], "selection_biased_reuse")
        self.assertFalse(lane["available_now"])

    def test_zero_expansive_activity(self):
        for field in (
            "password_materials_generated", "hash_candidates_generated",
            "decryptions_attempted", "oracle_calls", "rescans_performed",
        ):
            self.assertEqual(self.report[field], 0)


if __name__ == "__main__":
    unittest.main()
