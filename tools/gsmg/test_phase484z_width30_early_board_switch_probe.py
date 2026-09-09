import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase484z_width30_early_board_switch_probe as subject


class Phase484ZEarlyBoardSwitchTests(unittest.TestCase):
    def test_checkpoint_round_trip(self):
        paths = np.asarray([[1, 2, 3], [3, 2, 1]], dtype=np.uint8)
        scores = np.asarray([-1.5, -2.5], dtype=np.float64)
        with tempfile.TemporaryDirectory() as directory:
            saved = subject.save_checkpoint(directory, "stage", paths, scores)
            with np.load(saved) as payload:
                np.testing.assert_array_equal(payload["paths"], paths)
                np.testing.assert_array_equal(payload["scores"], scores)

    def test_recovery_record_can_include_best_true_path(self):
        truth = list(range(subject.width30.WIDTH))
        paths = np.asarray([truth[:4], truth[1:5]], dtype=np.uint8)
        scores = np.asarray([1.0, 2.0])
        record = subject.recovery_record(
            paths, scores, truth, 4, include_best=True)
        self.assertEqual(record["best_true_path"], truth[1:5])
        self.assertEqual(record["best_true_score"], 2.0)

    def test_recovery_record_uses_exact_true_windows(self):
        paths = np.asarray([
            [0, 1, 2, 3], [1, 2, 3, 4], [8, 9, 10, 11]],
            dtype=np.uint8)
        record = subject.recovery_record(
            paths, np.asarray([1.0, 3.0, 2.0]), [0, 1, 2, 3, 4], 4)
        self.assertEqual(record["true_segments"], 2)
        self.assertEqual(record["best_true_rank"], 1)

    def test_defaults_switch_at_depth7_with_widened_capacity(self):
        self.assertEqual(subject.SWITCH_DEPTH, 7)
        self.assertEqual(subject.DEFAULT_DEPTH6_KEEP, 524288)
        self.assertEqual(subject.DEFAULT_DEPTH7_KEEP, 1048576)

    def test_board_screen_chunks_without_changing_path_order(self):
        old = subject.joint.gpu_multistart_screen
        calls = []
        try:
            def fake(binary, blocks, pair, quad, paths, restarts, iterations):
                calls.append(paths.copy())
                scores = paths[:, 0].astype(float)
                n = len(paths)
                return scores, np.zeros(n), np.zeros((n, 25)), np.zeros(n)

            subject.joint.gpu_multistart_screen = fake
            paths = np.arange(15, dtype=np.uint8).reshape(5, 3)
            scores = subject.board_screen(
                paths, None, None, None, chunk_size=2)
            self.assertEqual([len(call) for call in calls], [2, 2, 1])
            np.testing.assert_array_equal(scores, paths[:, 0].astype(float))
        finally:
            subject.joint.gpu_multistart_screen = old


if __name__ == "__main__":
    unittest.main()
