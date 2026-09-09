import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import phase484s_unknown_pair_full as subject


class Phase484SUnknownPairFullTests(unittest.TestCase):
    def test_missing_scores_rank_last(self):
        cells = [
            {"hypothesis_pair_index": 2, "top1_final_normalized_score": None},
            {"hypothesis_pair_index": 1, "top1_final_normalized_score": -5.0},
            {"hypothesis_pair_index": 0, "top1_final_normalized_score": -4.0},
        ]
        ranked = subject.rank_pairs(cells)
        self.assertEqual([c["hypothesis_pair_index"] for c in ranked], [0, 1, 2])

    def test_fixed_development_budget(self):
        self.assertEqual((subject.KEEP, subject.REFINE_KEEP,
                          subject.EXTEND_SEEDS), (16384, 64, 8))


if __name__ == "__main__":
    unittest.main()
