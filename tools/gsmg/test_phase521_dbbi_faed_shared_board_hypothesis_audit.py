#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase521_dbbi_faed_shared_board_hypothesis_audit as p521


class Phase521Tests(unittest.TestCase):
    def test_self_test_passes(self):
        p521.self_test()

    def test_own_best_pairs_reproduced(self):
        from data import DBBI, FAED
        self.assertEqual("".join(p521.own_best_pair(DBBI)), "be")
        self.assertEqual("".join(p521.own_best_pair(FAED)), "gi")

    def test_cost_of_sharing_nonnegative_and_deterministic(self):
        from data import DBBI, FAED
        row1 = p521.cost_of_sharing(DBBI, FAED, (7, 7), 500, 1)
        row2 = p521.cost_of_sharing(DBBI, FAED, (7, 7), 500, 1)
        self.assertGreaterEqual(row1["cost_raw"], -1e-9)
        self.assertEqual(row1["cost_raw"], row2["cost_raw"])

    def test_null_population_small(self):
        values = p521.null_population("euler", 5, 12345)
        self.assertEqual(len(values), 5)
        self.assertTrue(all(v >= -1e-6 for v in values))


if __name__ == "__main__":
    unittest.main()
