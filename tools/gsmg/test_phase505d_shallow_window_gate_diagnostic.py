import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

import phase505d_shallow_window_gate_diagnostic as phase505d


class Phase505DTests(unittest.TestCase):
    def test_window_grid_covers_full_depth4_range(self):
        self.assertEqual(phase505d.MIN_WINDOWS, tuple(range(1, 31)))

    def test_refuses_without_lock_before_path_or_gpu_work(self):
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(phase505d, "LOCK_PATH",
                                   Path(directory) / "absent.json"), \
                    mock.patch.object(
                        phase505d.shallow, "path_universe",
                        side_effect=AssertionError("work started")):
                with self.assertRaisesRegex(RuntimeError, "lock is absent"):
                    phase505d.run(Path(directory) / "work")

    def test_true_mask_finds_contiguous_planted_windows(self):
        fixture = {"order": list(range(19))}
        truth = phase505d.prefix.order_to_sequence(fixture["order"])
        paths = np.asarray([truth[:4], truth[1:5], [0, 2, 4, 6]],
                           dtype=np.uint8)
        self.assertEqual(phase505d.true_mask(paths, fixture).tolist(),
                         [True, True, False])

    def test_summarize_ranks_each_threshold_independently(self):
        cells = []
        for true_index in phase505d.shallow.PILOT_TRUE_PAIR_INDICES:
            for hypothesis in range(36):
                records = []
                for minimum in phase505d.MIN_WINDOWS:
                    records.append({
                        "best_score": (1.0 if hypothesis == true_index else 0.0)
                    })
                cells.append({"true_pair_index": true_index,
                              "hypothesis_pair_index": hypothesis,
                              "records": records})
        with mock.patch.object(phase505d, "sha256_file", return_value="lock"):
            result = phase505d.summarize(cells)
        self.assertEqual(result["best_top1"], 3)
        self.assertEqual(result["best_top3"], 3)
        self.assertTrue(result["any_threshold_top3_all_rows"])

    def test_multistart_preserves_window_counts_and_best_score(self):
        calls = []

        def fake(_binary, _blocks, _pair, _quad, _paths, _iterations, seed):
            calls.append(seed)
            index = len(calls)
            return (np.asarray([-5.0 + index, -4.0]),
                    np.asarray([1, 7]), np.zeros((2, 25), dtype=np.uint8))

        with mock.patch.object(phase505d.joint, "gpu_coarse_screen",
                               side_effect=fake):
            scores, windows = phase505d.multistart_with_windows(
                np.zeros((2, 4), dtype=np.uint8), [], ("a", "b"), None)
        self.assertEqual(len(calls), phase505d.shallow.RESTARTS)
        self.assertEqual(windows.tolist(), [1, 7])
        self.assertEqual(scores.tolist(), [-2.0, -4.0])


if __name__ == "__main__":
    unittest.main()
