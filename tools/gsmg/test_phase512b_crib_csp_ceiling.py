#!/usr/bin/env python3
from __future__ import annotations

import unittest

import phase512b_crib_csp_ceiling as phase512b


class Phase512BCspTests(unittest.TestCase):
    def test_helpers(self):
        self.assertEqual(phase512b.observed_blocks("aabbcc", 3),
                         ("aa", "bb", "cc"))
        self.assertEqual(phase512b.truth_column_to_chunk([2, 0, 1]),
                         (1, 2, 0))

    def test_truth_first_canary(self):
        fixture = phase512b.phase512a.make_fixture("creator_macro_message", 15)
        truth = phase512b.truth_column_to_chunk(fixture["order"])
        result = phase512b.solve_known_start(
            fixture["observed"], 15, phase512b.phase512a.PAIR,
            fixture["crib"], fixture["planted_raw_offset"],
            node_limit=200_000, solution_limit=1,
            preferred_column_to_chunk=truth)
        self.assertIn(list(truth), result["solutions"])
        self.assertFalse(result["node_limit_reached"])


if __name__ == "__main__":
    unittest.main()
