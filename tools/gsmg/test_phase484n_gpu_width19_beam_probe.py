import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import phase484n_gpu_width19_beam_probe as subject


class Phase484NBeamTests(unittest.TestCase):
    def test_bidirectional_expansion_deduplicates(self):
        beam = [(1.0, (1, 2, 3)), (0.5, (0, 1, 2))]
        paths = subject.expand_bidirectional(beam, 4)
        self.assertEqual(len(paths), len(set(paths)))
        self.assertIn((0, 1, 2, 3), paths)

    def test_array_selection_matches_width(self):
        paths = [(0, 1, 2, 3), (1, 2, 3, 4), (2, 3, 4, 5)]
        beam = subject.select_diverse_arrays(paths, [1.0, 3.0, 2.0], 19, 2)
        self.assertEqual(len(beam), 2)
        self.assertEqual(beam[0], (3.0, (1, 2, 3, 4)))

    def test_coverage_selection_reserves_distinct_sets(self):
        paths = [
            (0, 1, 2, 3), (0, 1, 3, 2),
            (4, 5, 6, 7), (4, 5, 7, 6),
        ]
        beam = subject.select_coverage_diverse(paths, [4, 3, 2, 1], 2)
        masks = {sum(1 << value for value in path) for _, path in beam}
        self.assertEqual(len(masks), 2)


if __name__ == "__main__":
    unittest.main()
