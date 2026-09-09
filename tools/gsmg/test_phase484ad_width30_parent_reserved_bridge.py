import sys
import unittest
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase484ad_width30_parent_reserved_bridge as subject


class Phase484ADBridgeTests(unittest.TestCase):
    def test_expand_parent_indices_matches_reference(self):
        paths = np.asarray([[0, 1, 2], [3, 4, 5]], dtype=np.uint8)
        expanded, parents = subject.expand_with_parent_indices(paths)
        expected = subject.width30.expand_bidirectional(paths)
        np.testing.assert_array_equal(expanded, expected)
        for path, parent_index in zip(expanded, parents):
            parent = paths[parent_index]
            self.assertTrue(np.array_equal(path[1:], parent) or
                            np.array_equal(path[:-1], parent))

    def test_local_reservation_keeps_best_per_parent(self):
        paths = np.asarray([
            [0, 1], [0, 2], [0, 3],
            [4, 1], [4, 2], [4, 3],
        ], dtype=np.uint8)
        scores = np.asarray([1.0, 3.0, 2.0, 6.0, 4.0, 5.0])
        parents = np.asarray([0, 0, 0, 1, 1, 1])
        kept, kept_scores = subject.reserve_local_children(
            paths, scores, parents, children_per_parent=2)
        observed = {tuple(path): score
                    for path, score in zip(kept, kept_scores)}
        self.assertEqual(observed, {
            (0, 2): 3.0, (0, 3): 2.0,
            (4, 1): 6.0, (4, 3): 5.0,
        })


if __name__ == "__main__":
    unittest.main()
