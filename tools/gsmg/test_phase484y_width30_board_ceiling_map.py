import sys
import unittest
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase484y_width30_board_ceiling_map as subject


class Phase484YBoardCeilingTests(unittest.TestCase):
    def test_random_paths_are_deterministic_and_exclude_truth(self):
        fixture = subject.width30.width30_fixture(13)
        truth = subject.prefix.order_to_sequence(fixture["order"])
        forbidden = subject.bidi.true_windows(truth, 8)
        first = subject.random_paths(8, 50, forbidden, 123)
        second = subject.random_paths(8, 50, forbidden, 123)
        np.testing.assert_array_equal(first, second)
        self.assertFalse(any(tuple(path) in forbidden for path in first))

    def test_one_column_corruptions_are_unique_and_one_change_away(self):
        originals = {(0, 1, 2, 3)}
        corruptions = subject.one_column_corruptions(originals, 4)
        self.assertEqual(len(corruptions), 4 * (30 - 4))
        self.assertTrue(all(sum(a != b for a, b in zip(path, (0, 1, 2, 3))) == 1
                            for path in corruptions))

    def test_summary_rank(self):
        result = subject.summarize(np.asarray([2.0, 3.0]),
                                   np.asarray([1.0, 4.0, 2.5]))
        self.assertEqual(result["best_true_rank_pooled"], 2)
        self.assertEqual(result["controls_at_or_above_best_true"], 1)


if __name__ == "__main__":
    unittest.main()
