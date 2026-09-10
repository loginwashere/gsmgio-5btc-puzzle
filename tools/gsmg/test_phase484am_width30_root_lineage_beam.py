import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase484am_width30_root_lineage_beam as subject


class Phase484AMTests(unittest.TestCase):
    def test_unique_root_path_keeps_best_duplicate(self):
        roots = np.asarray([0, 0, 0, 1], dtype=np.int64)
        paths = np.asarray([[1, 2], [1, 2], [2, 1], [1, 2]], dtype=np.uint8)
        scores = np.asarray([1.0, 3.0, 2.0, 4.0])
        indices = subject.unique_root_path_indices(roots, paths, scores)
        got = {(int(roots[i]), tuple(paths[i]), float(scores[i])) for i in indices}
        self.assertEqual(got, {(0, (1, 2), 3.0), (0, (2, 1), 2.0),
                               (1, (1, 2), 4.0)})

    def test_select_per_root_keeps_ranked_quota(self):
        roots = np.asarray([0, 0, 0, 1, 1], dtype=np.int64)
        paths = np.asarray([[0, 1], [0, 2], [0, 3], [1, 2], [1, 3]],
                           dtype=np.uint8)
        scores = np.asarray([1.0, 3.0, 2.0, 5.0, 4.0])
        p, s, r = subject.select_per_root(paths, scores, roots, keep=2)
        self.assertEqual(r.tolist(), [0, 0, 1, 1])
        self.assertEqual(s.tolist(), [3.0, 2.0, 5.0, 4.0])
        self.assertEqual(p.tolist(), [[0, 2], [0, 3], [1, 2], [1, 3]])

    def test_load_state_accepts_depth7_root_population(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "depth7.npz"
            np.savez(path, paths=np.asarray([np.arange(7)], dtype=np.uint8),
                     scores=np.ones(1), root_ids=np.asarray([0]))
            paths, scores, roots, digest = subject.load_state(path)
            self.assertEqual(paths.shape, (1, 7))
            self.assertEqual(scores.tolist(), [1.0])
            self.assertEqual(roots.tolist(), [0])
            self.assertEqual(len(digest), 64)

    def test_load_state_rejects_unsorted_roots(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.npz"
            np.savez(path, paths=np.tile(np.arange(8, dtype=np.uint8), (2, 1)),
                     scores=np.ones(2), root_ids=np.asarray([1, 0]))
            with self.assertRaises(ValueError):
                subject.load_state(path)


if __name__ == "__main__":
    unittest.main()
