#!/usr/bin/env python3
from __future__ import annotations

import unittest

import phase512c_crib_prefix_search as phase512c


class Phase512CPrefixTests(unittest.TestCase):
    def test_self_test(self):
        self.assertEqual(phase512c.self_test()["self_test"], "pass")

    def test_truth_satisfies_complete_crib(self):
        fixture = phase512c.phase512a.make_fixture("creator_macro_message", 19)
        score = phase512c.consistent_prefix_length(
            fixture["observed"], 19, fixture["order"],
            phase512c.phase512a.PAIR, fixture["crib"],
            fixture["planted_raw_offset"])
        self.assertEqual(score, len(fixture["crib"]))


if __name__ == "__main__":
    unittest.main()
