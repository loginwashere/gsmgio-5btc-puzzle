import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import phase484s_unknown_pair_screen as subject


class Phase484SUnknownPairScreenTests(unittest.TestCase):
    def test_rank_pairs_is_descending_and_stable(self):
        cells = [
            {"hypothesis_pair_index": 2, "best_refined_normalized_score": -5.0,
             "hypothesis_is_true_pair": False},
            {"hypothesis_pair_index": 1, "best_refined_normalized_score": -4.0,
             "hypothesis_is_true_pair": True},
            {"hypothesis_pair_index": 0, "best_refined_normalized_score": -4.0,
             "hypothesis_is_true_pair": False},
        ]
        ranked = subject.rank_pairs(cells)
        self.assertEqual([c["hypothesis_pair_index"] for c in ranked], [0, 1, 2])
        self.assertEqual([c["pair_screen_rank"] for c in ranked], [1, 2, 3])

    def test_screen_does_not_extend_orders(self):
        self.assertEqual(subject.KEEP, 16384)
        self.assertEqual(subject.REFINE_KEEP, 64)


if __name__ == "__main__":
    unittest.main()
