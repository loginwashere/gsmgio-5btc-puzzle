import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase484aj_width30_depth6_dev_screen as subject


class Phase484AJScreenTests(unittest.TestCase):
    def record(self, index, d6=1, coarse=1, refined=1):
        return {
            "phase": "484AI",
            "fixture_index": index,
            "schedule_sha256": subject.full.schedule_sha256(),
            "wall_seconds": 1.5,
            "switch_stage": {"after_board_selection": {"true_segments": d6}},
            "depth7": {
                "after_selection": {"true_segments": coarse},
                "refine": {"after_selection": {"true_segments": refined}},
            },
        }

    def test_summary_separates_search_from_posthoc_truth_metric(self):
        row = subject.summarize_initial(self.record(13, 0, 0, 0))
        self.assertFalse(row["survived_depth7_refined"])
        self.assertEqual(row["depth7_refined_true_segments"], 0)

    def test_schedule_drift_fails_closed(self):
        record = self.record(13)
        record["schedule_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            subject.summarize_initial(record)

    def test_partial_summary_requires_expected_prefix(self):
        with self.assertRaises(ValueError):
            subject.build_summary([self.record(14)], 0.0)

    def test_complete_summary_counts_survivors(self):
        records = [self.record(index, refined=(index % 2))
                   for index in subject.FIXTURE_INDICES]
        result = subject.build_summary(records, 0.0)
        self.assertEqual(result["status"],
                         "development_depth6_screen_complete_not_frozen")
        self.assertEqual(result["completed_count"], 10)
        self.assertEqual(result["survived_count"], 5)
        self.assertFalse(result["faed_scored"])
        self.assertFalse(result["holdout_consumed"])
        self.assertTrue(set(result["fixture_indices"]).isdisjoint(
                            result["training_indices"]))


if __name__ == "__main__":
    unittest.main()
