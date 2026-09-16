import tempfile
import unittest
from pathlib import Path

import phase491_current_model_front_screen as screen
import phase491_raw_histogram_fixture as rawonly


class Phase491FrontScreenTests(unittest.TestCase):
    def test_self_test(self):
        self.assertFalse(screen.self_test()["faed_scored"])

    def test_summary_gate(self):
        sample = {
            "depth7_refine": {"after_selection": {
                "true_segments": 1, "best_true_rank": 9}},
            "wall_seconds": 1.0,
        }
        result = screen.result_summary(0, sample)
        self.assertTrue(result["passed"])
        self.assertEqual(result["true_segments_retained"], 1)

    def test_empty_partial_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "result.json").write_text("{}")
            self.assertIsNone(screen.validate_completed(
                0, root, rawonly.make_fixture(0)))


if __name__ == "__main__":
    unittest.main()
