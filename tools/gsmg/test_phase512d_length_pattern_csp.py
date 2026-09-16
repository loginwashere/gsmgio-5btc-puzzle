#!/usr/bin/env python3
from __future__ import annotations

import unittest

import phase512d_length_pattern_csp as phase512d


class Phase512DTests(unittest.TestCase):
    def test_length_pattern_bounds(self):
        crib = phase512d.phase512a.CRIBS["creator_macro_message"]
        patterns = phase512d.length_patterns(crib)
        first = next(patterns)
        self.assertLessEqual(len(first), 7)
        self.assertLessEqual(len(set(crib)) - len(first), 18)

    def test_known_pattern_recovers_width15(self):
        result = phase512d.run_true_pattern("phase1_credential", 15, 1_000_000)
        self.assertTrue(result["truth_recovered"])
        self.assertFalse(result["node_limit_reached"])

    def test_pattern_family_contains_truth(self):
        fixture = phase512d.phase512a.make_fixture("phase1_credential", 15)
        truth = phase512d.true_single_letters(fixture)
        self.assertIn(truth, set(phase512d.length_patterns(fixture["crib"])))

    def test_solution_acceptor_filters_leaf_solutions(self):
        fixture = phase512d.phase512a.make_fixture("phase1_credential", 15)
        singles = phase512d.true_single_letters(fixture)
        rejected = phase512d.solve_length_pattern(
            fixture["observed"], 15, phase512d.phase512a.PAIR,
            fixture["crib"], fixture["planted_raw_offset"], singles,
            solution_acceptor=lambda _solution: False)
        self.assertEqual(rejected["solutions"], [])


if __name__ == "__main__":
    unittest.main()
