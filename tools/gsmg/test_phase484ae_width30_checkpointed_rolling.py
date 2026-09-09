import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase484ae_width30_checkpointed_rolling as subject


class Phase484AECheckpointTests(unittest.TestCase):
    def test_load_checkpoint_round_trip(self):
        paths = np.asarray([[0, 1, 2, 3], [3, 2, 1, 0]], dtype=np.uint8)
        scores = np.asarray([1.0, 2.0])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "population.npz"
            np.savez(path, paths=paths, scores=scores)
            loaded_paths, loaded_scores, digest = subject.load_checkpoint(path)
            np.testing.assert_array_equal(loaded_paths, paths)
            np.testing.assert_array_equal(loaded_scores, scores)
            self.assertEqual(len(digest), 64)

    def test_repeated_column_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.npz"
            np.savez(path,
                     paths=np.asarray([[0, 1, 1, 3]], dtype=np.uint8),
                     scores=np.asarray([1.0]))
            with self.assertRaises(ValueError):
                subject.load_checkpoint(path)


if __name__ == "__main__":
    unittest.main()
