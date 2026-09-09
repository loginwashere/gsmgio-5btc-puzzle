import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase484af_width30_fixed_schedule_dev as subject


class Phase484AFFixedScheduleTests(unittest.TestCase):
    def test_schedule_hash_is_stable(self):
        self.assertEqual(
            subject.schedule_sha256(),
            "8aba55be72a86f6ff2de838f0bb422562af318b0c2488ec48834c6bb9a091af0")

    def test_transfer_indices_exclude_training_and_tuning_fixture(self):
        self.assertNotIn(15, subject.TRANSFER_DEV_INDICES)
        self.assertFalse(set(subject.TRANSFER_DEV_INDICES) &
                         set(subject.early.width30.TRAIN_INDICES))
        self.assertEqual(len(set(subject.TRANSFER_DEV_INDICES)), 3)

    def test_require_file_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(RuntimeError):
                subject.require_file(Path(directory) / "missing.npz", "stage")

    def test_run_refuses_existing_result(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.json"
            path.write_text("existing")
            with self.assertRaises(FileExistsError):
                subject.run_fixture(19, Path(directory), path)

    def test_runner_disables_truth_gated_stops(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            calls = {}

            def fake_initial(**kwargs):
                calls["initial"] = kwargs
                (work / "depth10_selected.npz").touch()
                return {
                    "depth7": {"after_board_selection": {"true_segments": 0}},
                    "depth8": {
                        "strong_refine": {"after_selection": {"true_segments": 0}},
                        "rolling_probe": [{"after_selection": {"true_segments": 0}}],
                    },
                }

            def fake_bridge(**kwargs):
                calls["bridge"] = kwargs
                (work / "depth12_selected.npz").touch()
                return {
                    "depth11": {"after_reservation": {"true_segments": 0}},
                    "depth12": {"after_selection": {"true_segments": 0}},
                }

            def fake_roll(**kwargs):
                calls.setdefault("rolling", []).append(kwargs)
                depth = kwargs["max_depth"]
                (work / f"depth{depth}_selected.npz").touch()
                return {"depth_diagnostics": [
                    {"after_selection": {"true_segments": 0}}]}

            fake_final = {
                "exact_order_final_rank": None,
                "top1_exact_order": False,
                "top1_plaintext_accuracy": 0.0,
            }
            with mock.patch.object(subject.early, "run_fixture", fake_initial), \
                    mock.patch.object(subject.bridge, "run", fake_bridge), \
                    mock.patch.object(subject.rolling, "run", fake_roll), \
                    mock.patch.object(subject.rolling, "resolve_final",
                                      return_value=fake_final):
                result = subject.run_fixture(19, work)
            self.assertFalse(calls["initial"]["stop_on_truth_loss"])
            self.assertTrue(all(not call["stop_on_truth_loss"]
                                for call in calls["rolling"]))
            self.assertFalse(result["top1_exact_order"])


if __name__ == "__main__":
    unittest.main()
