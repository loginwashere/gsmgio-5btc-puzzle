import unittest

import numpy as np

import phase490_width19_dual_lane_dev as port


class Width19PortTests(unittest.TestCase):
    def test_self_test(self):
        self.assertFalse(port.self_test()["faed_imported"])

    def test_expansion_rejects_repeated_columns(self):
        with self.assertRaises(ValueError):
            port.expand_bidirectional(np.asarray([[0, 0]], dtype=np.uint8), 4)

    def test_select_diverse_keeps_best_duplicate(self):
        paths = np.asarray([[0, 1], [0, 1], [1, 0]], dtype=np.uint8)
        scores = np.asarray([1.0, 3.0, 2.0])
        selected, selected_scores, unique = port.select_diverse(
            paths, scores, 2, width=2)
        self.assertEqual(unique, 2)
        self.assertIn(3.0, selected_scores)
        self.assertEqual({tuple(row) for row in selected}, {(0, 1), (1, 0)})

    def test_canonical_rows_match_kernel_convention(self):
        blocks = ["g", "a", "i", "b"]
        rows = port.canonical_token_rows(blocks, ("g", "i"), (0, 1, 2, 3))
        self.assertEqual(rows[0].tolist(), [7 + 0 * 9 + 2, 7 + 1 * 9 + 3])

    def test_true_record_uses_tie_explicit_score_rank(self):
        paths = np.asarray([[0, 1], [1, 2], [2, 3], [3, 0]], dtype=np.uint8)
        scores = np.asarray([2.0, 5.0, 5.0, 1.0])
        # A four-column circular truth has all four adjacent directed windows.
        record = port.true_record(paths, scores, [0, 1, 2, 3], 2)
        self.assertEqual(record["true_segments"], 3)
        self.assertEqual(record["best_true_rank"], 1)
        self.assertEqual(record["best_true_score_tie_count"], 2)

    def test_vectorized_repeat_validation(self):
        valid = np.tile(np.asarray([[0, 1, 2]], dtype=np.uint8), (1000, 1))
        self.assertEqual(port.expand_bidirectional(valid, 4).shape, (2000, 4))


if __name__ == "__main__":
    unittest.main()
