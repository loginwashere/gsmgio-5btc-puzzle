#!/usr/bin/env python3

import unittest

import numpy as np

import phase483a_invariant_order_statistic_probe as p


class Phase483AProbeTests(unittest.TestCase):
    def test_self_test(self):
        self.assertTrue(p.self_test())

    def test_equality_code_is_substitution_invariant(self):
        source = np.array([0, 1, 0, 2, 3, 2, 4, 4], dtype=np.int64)
        renamed = np.array([8, 2, 8, 9, 1, 9, 6, 6], dtype=np.int64)
        for size in p.PATTERN_LENGTHS:
            np.testing.assert_array_equal(
                p.equality_codes(source, size), p.equality_codes(renamed, size))

    def test_geometry_round_trip_both_directions(self):
        for width in p.WIDTHS:
            for direction in p.DIRECTIONS:
                fixture = p.make_fixture("dev", width, direction, 2)
                recovered = p.reconstructed(fixture, fixture["order"])
                self.assertEqual(recovered.shape[0], p.LENGTH)
                self.assertEqual(len(set(fixture["order"])), width)

    def test_splits_are_disjoint_slices(self):
        splits = p.corpus_splits()
        self.assertGreater(min(map(len, splits.values())), p.LENGTH)
        self.assertNotEqual(splits["dev"][:p.LENGTH], splits["holdout"][:p.LENGTH])

    def test_reduced_budget_cannot_power_cell(self):
        result = p.run_probe("dev", fixtures=1, random_orders=3, corruptions=2)
        self.assertFalse(result["full_frozen_budget"])
        self.assertEqual(result["powered_cells"], [])

    def test_development_never_claims_power(self):
        result = p.run_probe("dev", fixtures=1, random_orders=1, corruptions=1)
        self.assertTrue(all(not cell["statistic_powered"] for cell in result["cells"]))

    def test_corruptions_remain_permutations(self):
        order = list(range(19))
        for severity in p.SEVERITIES:
            changed = p.corrupt_order(order, p.PCG32(100 + severity), severity)
            self.assertEqual(sorted(changed), order)


if __name__ == "__main__":
    unittest.main()
