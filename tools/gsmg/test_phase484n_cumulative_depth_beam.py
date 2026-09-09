import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import phase484n_cumulative_depth_beam as subject


class Phase484NCumulativeTests(unittest.TestCase):
    def test_duplicate_child_keeps_best_parent(self):
        beam = [(2.0, (0, 1, 2)), (1.0, (1, 2, 3))]
        paths, scores = subject.expand_with_parent_scores(beam, 4)
        values = dict(zip(paths, scores))
        self.assertEqual(values[(0, 1, 2, 3)], 2.0)


if __name__ == "__main__":
    unittest.main()
