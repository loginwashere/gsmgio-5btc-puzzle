import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase484z_width30_row_holdout_probe as subject


class Phase484ZRowHoldoutTests(unittest.TestCase):
    def test_path_seed_is_pool_order_independent(self):
        path = (7, 3, 11, 2, 9, 1, 8, 4)
        self.assertEqual(subject.path_seed(123, path),
                         subject.path_seed(123, tuple(path)))
        self.assertNotEqual(subject.path_seed(123, path),
                            subject.path_seed(123, path[::-1]))

    def test_folds_partition_every_row_once(self):
        folds = subject.make_folds(3)
        self.assertEqual(sorted(row for fold in folds for row in fold),
                         list(range(subject.ROWS)))
        self.assertTrue(all(set(left).isdisjoint(right)
                            for i, left in enumerate(folds)
                            for right in folds[i + 1:]))

    def test_pool_hash_is_canonical_and_order_sensitive(self):
        paths = [(0, 1, 2), (3, 4, 5)]
        self.assertEqual(subject.pool_sha256(paths),
                         subject.pool_sha256([list(path) for path in paths]))
        self.assertNotEqual(subject.pool_sha256(paths),
                            subject.pool_sha256(paths[::-1]))


if __name__ == "__main__":
    unittest.main()
