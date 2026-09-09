#!/usr/bin/env python3

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase484f_modelb_spectral_annealing_probe as probe


class Phase484FTests(unittest.TestCase):
    def test_self_test(self):
        probe.self_test()

    def test_start_classes_and_budgets_are_distinct(self):
        self.assertEqual(probe.CONTROLLED_DEPTHS, (1, 2, 4))
        self.assertEqual(probe.SPECTRAL_STARTS, 4)
        self.assertEqual(probe.RANDOM_STARTS, 2)
        self.assertEqual(probe.WORKERS, 6)


if __name__ == "__main__":
    unittest.main()
