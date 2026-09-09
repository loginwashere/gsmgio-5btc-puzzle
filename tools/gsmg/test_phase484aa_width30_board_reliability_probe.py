import sys
import unittest
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase484aa_width30_board_reliability_probe as subject


class Phase484AABoardReliabilityTests(unittest.TestCase):
    def test_identical_boards_have_unit_agreement(self):
        boards = np.tile(np.arange(25, dtype=np.uint8), (3, 1))
        self.assertEqual(subject.weighted_board_agreement(
            boards, np.asarray([0, 0, 4, 9])), 1.0)

    def test_agreement_is_weighted_by_observed_tokens(self):
        first = np.arange(25, dtype=np.uint8)
        second = first.copy()
        second[1] = 9
        boards = np.asarray([first, second])
        self.assertEqual(subject.weighted_board_agreement(
            boards, np.asarray([0, 0, 0, 1])), 0.75)

    def test_summary_ranks_higher_scores_first(self):
        scores = np.asarray([3.0, 1.0, 2.0, 0.0])
        true = np.asarray([True, False, True, False])
        summary = subject.summarize(scores, true)
        self.assertEqual(summary["best_true_rank"], 1)
        self.assertEqual(summary["worst_true_rank"], 2)
        self.assertEqual(summary["mean_beaten_by_background"], 0.0)

    def test_pool_hash_is_order_sensitive(self):
        paths = [(0, 1), (2, 3)]
        self.assertNotEqual(subject.pool_sha256(paths),
                            subject.pool_sha256(paths[::-1]))


if __name__ == "__main__":
    unittest.main()
