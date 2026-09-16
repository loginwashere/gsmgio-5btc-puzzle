import unittest

import numpy as np

import phase495_depth10_objective_diagnostic as phase495


class Phase495Tests(unittest.TestCase):
    def test_self_test(self):
        result = phase495.self_test()
        self.assertFalse(result["faed_scored"])
        self.assertTrue(result["marker_verified"])

    def test_top_false_excludes_truth(self):
        scores = np.asarray([1.0, 9.0, 8.0, 7.0])
        truth = np.asarray([False, True, False, False])
        self.assertEqual(phase495.top_false(scores, truth, 2).tolist(), [2, 3])

    def test_panel_is_deduplicated_and_labeled(self):
        unrestricted = np.asarray([10.0, 9.0, 8.0, 7.0])
        constrained = np.asarray([7.0, 8.0, 9.0, 10.0])
        truth = np.asarray([True, False, False, False])
        old_top, old_random = phase495.TOP_FALSE, phase495.RANDOM_FALSE
        phase495.TOP_FALSE, phase495.RANDOM_FALSE = 2, 1
        try:
            indices, labels = phase495.make_panel(
                unrestricted, constrained, truth)
        finally:
            phase495.TOP_FALSE, phase495.RANDOM_FALSE = old_top, old_random
        self.assertEqual(len(indices), len(set(indices.tolist())))
        self.assertIn("true", labels[0])

    def test_partition_violations(self):
        common, uncommon = phase495.rawonly.training_groups()
        letters = phase495.base.LETTER_ALPHABET
        board = np.asarray([letters.index(x) for x in (*common, *uncommon)],
                           dtype=np.uint8)
        self.assertEqual(phase495.partition_violations(board), 0)
        board[0], board[7] = board[7], board[0]
        self.assertEqual(phase495.partition_violations(board), 1)


if __name__ == "__main__":
    unittest.main()
