#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase520_dbbi_faed_joint_splice_hypothesis_audit as p520


class Phase520Tests(unittest.TestCase):
    def test_self_test_passes(self):
        p520.self_test()

    def test_structural_check_661_is_prime(self):
        result = p520.structural_check()
        self.assertEqual(result["spliced_length"], 661)
        self.assertTrue(result["is_prime"])
        self.assertEqual(result["nontrivial_factor_pairs"], [])

    def test_standing_best_pairs_reproduced(self):
        fit = p520.joint_fit_observed()
        self.assertIn("be", fit["dbbi_alone"]["best_pairs"])
        self.assertIn("gi", fit["faed_alone"]["best_pairs"])

    def test_joint_fit_worse_than_either_alone(self):
        fit = p520.joint_fit_observed()
        self.assertGreater(fit["spliced_dbbi_then_faed"]["loss"], fit["dbbi_alone"]["loss"])
        self.assertGreater(fit["spliced_dbbi_then_faed"]["loss"], fit["faed_alone"]["loss"])

    def test_null_population_small(self):
        values = p520.null_population("euler", 20, 12345)
        self.assertEqual(len(values), 20)
        self.assertTrue(all(0.0 <= v <= p520.INVALID_LOSS for v in values))


if __name__ == "__main__":
    unittest.main()
