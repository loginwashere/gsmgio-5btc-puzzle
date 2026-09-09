import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import phase484q_revised_dev_batch as subject


class Phase484QRevisedBatchTests(unittest.TestCase):
    def test_tuning_and_fresh_cases_do_not_overlap(self):
        self.assertFalse(set(subject.TUNING_CASES) & set(subject.FRESH_CASES))

    def test_fresh_batch_has_twenty_cells(self):
        self.assertEqual(len(subject.FRESH_CASES), 20)
        self.assertEqual({index for _, index in subject.FRESH_CASES}, set(range(50, 60)))

    def test_revised_budgets_cover_diagnosed_cutoffs(self):
        self.assertGreaterEqual(subject.SHORTLIST, 262144)
        self.assertGreaterEqual(subject.REFINE_KEEP, 8192)
        self.assertGreaterEqual(subject.EXTEND_SEEDS, 16)

    def test_summary_counts_each_stage(self):
        cells = [
            {"true_segments_retained": 1, "exact_order_in_terminals": True,
             "top1_exact_order": True},
            {"true_segments_retained": 0, "exact_order_in_terminals": False,
             "top1_exact_order": False},
        ]
        summary = subject.summarize(cells)
        self.assertEqual(summary["shortlist_retained"], 1)
        self.assertEqual(summary["exact_order_in_terminals"], 1)
        self.assertEqual(summary["exact_order_top1_rate"], 0.5)


if __name__ == "__main__":
    unittest.main()
