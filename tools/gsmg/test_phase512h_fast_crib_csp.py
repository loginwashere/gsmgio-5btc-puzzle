#!/usr/bin/env python3
from __future__ import annotations

import unittest

import phase512a_transposition_crib_feasibility as phase512a
import phase512d_length_pattern_csp as phase512d
import phase512h_fast_crib_csp as phase512h


class Phase512HFastCribCSPTests(unittest.TestCase):
    def test_known_solution_matches_truth(self):
        fixture = phase512a.make_fixture("phase1_credential", 15)
        singles = phase512d.true_single_letters(fixture)
        result = phase512h.search_lengths_fast(
            fixture, fixture["planted_raw_offset"], 100_000,
            patterns=(singles,), pair=phase512a.PAIR)
        self.assertEqual(result["hit_count"], 1)
        self.assertTrue(result["hits"][0]["exact_truth"])

    def test_first_pattern_prefix_matches_reference(self):
        fixture = phase512a.make_fixture("phase1_credential", 15)
        patterns = tuple(phase512d.length_patterns(fixture["crib"]))[:64]
        fast = phase512h.search_lengths_fast(fixture, 0, 1_000_000, patterns)
        reference = phase512d.search_lengths_at_start(
            fixture, 0, 1_000_000, patterns)
        self.assertEqual(fast["hit_count"], reference["hit_count"])
        self.assertEqual(fast["patterns_tested"], reference["patterns_tested"])
        self.assertEqual(fast["search_complete"], reference["search_complete"])

    def test_self_test(self):
        self.assertEqual(phase512h.self_test()["self_test"], "pass")


if __name__ == "__main__":
    unittest.main()
