#!/usr/bin/env python3
"""Regression tests for Phases 426–428."""

import json
import unittest
from pathlib import Path

import phase426_btcseed_heldout_continuation_structure_audit as phase426
import phase427_btcseed_continuation_rail_attribution_audit as phase427
import phase428_btcseed_continuation_digraph_attribution_audit as phase428


SCRIPT_DIR = Path(__file__).resolve().parent


class Phase426To428Tests(unittest.TestCase):
    def load_result(self, phase):
        return json.loads((SCRIPT_DIR / f"phase{phase}_result.json").read_text(encoding="utf-8"))

    def test_primitives_and_controls(self):
        phase426.self_test()
        phase427.self_test()
        phase428.self_test()

    def test_lrs_matches_bruteforce_more_cases(self):
        for sample in ("ABRACADABRA", "ABCDEF", "XYZXYZX", "AABCAABDAAB"):
            self.assertEqual(phase426.longest_repeated_substring(sample), phase426.brute_force_lrs(sample))

    def test_frozen_outcomes(self):
        expected = {
            426: ("continuation_structure_positive", 3),
            427: ("residual_structure_positive", 41),
            428: ("digraph_mechanical_attribution", 5364),
        }
        for phase, (outcome, tail_count) in expected.items():
            result = self.load_result(phase)
            self.assertEqual(result["outcome"], outcome)
            self.assertEqual(result["calibration"]["family_tail_count_including_observed"], tail_count)
            self.assertEqual(result["protocol"]["trials"], 10_000)
            self.assertEqual(result["protocol"]["oracle_calls"], 0)

    def test_final_attribution_is_null_like(self):
        result = self.load_result(428)
        self.assertGreater(result["calibration"]["family_corrected_p"], 0.05)
        self.assertTrue(all(value > 0.05 for value in result["calibration"]["individual_p"].values()))
        self.assertEqual(result["protocol"]["globally_aligned_digraph_count"], 281)


if __name__ == "__main__":
    unittest.main()
