import sys
import unittest
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import phase484n_fixed_window_overlap_beam as subject


class FakeScorer:
    def score(self, paths):
        return np.asarray(paths, dtype=np.float64).sum(axis=1)


class Phase484NOverlapTests(unittest.TestCase):
    def test_overlapping_windows_order(self):
        paths = np.asarray([[0, 1, 2, 3], [4, 5, 6, 7]], dtype=np.uint8)
        windows = subject.overlapping_windows(paths, 3)
        self.assertEqual(windows.tolist(), [
            [0, 1, 2], [4, 5, 6], [1, 2, 3], [5, 6, 7],
        ])

    def test_window_sums_restore_candidate_axis(self):
        paths = np.asarray([[0, 1, 2, 3], [4, 5, 6, 7]], dtype=np.uint8)
        scores = subject.score_window_sums(FakeScorer(), paths, 3, 10)
        self.assertEqual(scores.tolist(), [9.0, 33.0])


if __name__ == "__main__":
    unittest.main()
