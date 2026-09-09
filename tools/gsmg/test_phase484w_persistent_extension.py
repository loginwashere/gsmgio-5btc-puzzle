import sys
import unittest
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import phase484w_persistent_extension as subject


class Phase484WPersistentExtensionTests(unittest.TestCase):
    def test_board_validation(self):
        self.assertEqual(subject.validate_board(range(25)), bytes(range(25)))
        with self.assertRaisesRegex(ValueError, "permutation"):
            subject.validate_board([0] * 25)
        with self.assertRaisesRegex(ValueError, "permutation"):
            subject.validate_board(range(24))

    def test_path_validation(self):
        paths = subject.canonical_paths([[0, 1, 2, 3], [3, 2, 1, 0]])
        self.assertEqual(paths.dtype, np.uint8)
        self.assertTrue(paths.flags.c_contiguous)
        with self.assertRaisesRegex(ValueError, "depth"):
            subject.canonical_paths([[0, 1, 2]])
        with self.assertRaisesRegex(ValueError, "width 19"):
            subject.canonical_paths([[0, 1, 2, 19]])

    def test_merge_is_rank_ordered_and_deduplicated(self):
        records = [
            {"rank": 1, "shortlist_index": 10},
            {"rank": 2, "shortlist_index": 20},
        ]
        extended = [
            (2, [(2.0, (0, 1, 2, 3)), (1.0, (3, 2, 1, 0))], ["b"]),
            (1, [(3.0, (0, 1, 2, 3)), (0.0, (1, 0, 3, 2))], ["a"]),
        ]
        terminals, diagnostics = subject.merge_extended(records, extended, 2)
        self.assertEqual([r["extension_score"] for r in terminals],
                         [3.0, 1.0, 0.0])
        self.assertEqual([r["extension_rank"] for r in terminals], [1, 2, 3])
        self.assertEqual([d["refined_rank"] for d in diagnostics], [1, 2])

    def test_zero_seed_population(self):
        self.assertEqual(subject.extend_population(
            [], ("a", "b"), np.zeros(1), [], 0), ([], []))


if __name__ == "__main__":
    unittest.main()
