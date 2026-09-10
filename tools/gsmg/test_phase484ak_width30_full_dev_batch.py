import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase484ak_width30_full_dev_batch as subject


class Phase484AKBatchTests(unittest.TestCase):
    def record(self, index, top1=False):
        return {
            "phase": "484AK",
            "fixture_index": index,
            "schedule_sha256": subject.full.schedule_sha256(),
            "faed_scored": False,
            "holdout_consumed": False,
            "top1_exact_order": top1,
        }

    def test_load_screen_fails_closed_on_schedule_drift(self):
        payload = {
            "status": "development_depth6_screen_complete_not_frozen",
            "faed_scored": False,
            "holdout_consumed": False,
            "schedule_sha256": "0" * 64,
            "fixture_indices": list(range(13, 23)),
            "records": [],
            "survivor_indices": [],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.json"
            path.write_text(json.dumps(payload))
            with self.assertRaises(ValueError):
                subject.load_screen(path)

    def test_completed_record_rejects_holdout_or_faed(self):
        record = self.record(13)
        record["faed_scored"] = True
        with self.assertRaises(ValueError):
            subject.validate_completed(record, 13)

    def test_summary_requires_survivor_order_and_counts_top1(self):
        survivors = [13, 14]
        records = [self.record(13, True), self.record(14, False)]
        result = subject.build_summary(records, survivors, Path("screen.json"),
                                       "a" * 64, 0.0)
        self.assertEqual(result["status"],
                         "development_full_batch_complete_not_frozen")
        self.assertEqual(result["exact_top1_count"], 1)
        self.assertIn("compute shortcut", result["selection_policy"])

    def test_partial_summary_rejects_nonprefix(self):
        with self.assertRaises(ValueError):
            subject.build_summary([self.record(14)], [13, 14],
                                  Path("screen.json"), "a" * 64, 0.0)


if __name__ == "__main__":
    unittest.main()
