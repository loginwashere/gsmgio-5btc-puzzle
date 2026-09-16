#!/usr/bin/env python3
from __future__ import annotations

import unittest

import phase512a_transposition_crib_feasibility as phase512a
import phase512b_crib_csp_ceiling as phase512b
import phase512g_locked_faed_width15_credential as phase512g


class Phase512GLockedFAEDTests(unittest.TestCase):
    def test_dimensions_and_family(self):
        self.assertEqual(len(phase512g.FAED), 570)
        self.assertEqual(phase512g.WIDTH, 15)
        self.assertEqual(phase512g.START_COUNT, 518)
        self.assertEqual(len(phase512a.base.ESCAPE_PAIRS), 36)

    def test_order_mapping_round_trip(self):
        fixture = phase512a.make_fixture(phase512g.CRIB_ID, phase512g.WIDTH)
        mapping = phase512b.truth_column_to_chunk(fixture["order"])
        self.assertEqual(phase512g.order_from_column_to_chunk(mapping),
                         fixture["order"])

    def test_truth_agnostic_self_test(self):
        self.assertEqual(phase512g.self_test()["self_test"], "pass")


if __name__ == "__main__":
    unittest.main()
