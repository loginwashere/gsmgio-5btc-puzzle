import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import phase484t_pair_fair_capacity as subject


class Phase484TPairFairCapacityTests(unittest.TestCase):
    def test_fixed_capacity(self):
        self.assertEqual(subject.budgets(), {
            "shortlist": 262144,
            "refine_keep": 8192,
            "extension_seed_count": 256,
            "extension_workers": 8,
            "extension_beam": 4096,
            "terminals_per_seed": 8,
        })

    def test_resume_rejects_budget_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.json"
            artifact = subject.new_artifact("broad_random", 51)
            artifact["budgets"]["extension_seed_count"] = 255
            path.write_text(json.dumps(artifact))
            with self.assertRaisesRegex(ValueError, "budgets"):
                subject.load_or_create("broad_random", 51, path)

    def test_resume_rejects_duplicate_pair(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.json"
            artifact = subject.new_artifact("broad_random", 51)
            artifact["cells"] = [
                {"hypothesis_pair_index": 0},
                {"hypothesis_pair_index": 0},
            ]
            path.write_text(json.dumps(artifact))
            with self.assertRaisesRegex(ValueError, "pair indices"):
                subject.load_or_create("broad_random", 51, path)

    def test_nondefault_true_pair_is_pinned(self):
        artifact = subject.new_artifact("vic_profile", 62, 34)
        self.assertEqual(artifact["true_pair_index"], 34)
        self.assertEqual(artifact["true_pair"], ["g", "i"])

    def test_invalid_true_pair_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "true pair index"):
            subject.new_artifact("vic_profile", 62, 36)

    def test_progress_before_nondefault_true_pair(self):
        cells = [{"hypothesis_pair_index": 0,
                  "hypothesis_is_true_pair": False,
                  "top1_final_normalized_score": -5.0}]
        self.assertIsNone(subject.true_pair_rank(cells))


if __name__ == "__main__":
    unittest.main()
