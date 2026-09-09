import sys
import unittest
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase484ac_width30_partition_constrained_board_probe as subject


class Phase484ACPartitionTests(unittest.TestCase):
    def test_groups_partition_all_letters(self):
        common, other = subject.letter_groups()
        self.assertEqual(len(common), 7)
        self.assertEqual(len(other), 18)
        self.assertEqual(set(common.tolist()) | set(other.tolist()), set(range(25)))
        self.assertFalse(set(common.tolist()) & set(other.tolist()))

    def test_initial_boards_respect_partition(self):
        for seed in range(5):
            board = subject.initial_board(subject.base.PCG32(seed))
            self.assertTrue(subject.respects_partition(board))
            self.assertEqual(sorted(board.tolist()), list(range(25)))

    def test_multistart_is_path_seeded(self):
        old = subject.anneal
        calls = []
        try:
            def fake(rows, quad, seed, iterations):
                calls.append(seed)
                return np.arange(25), float(seed & 255), 1
            subject.anneal = fake
            subject.multistart([], None, (1, 2, 3), restarts=2,
                               iterations=4, seed=9)
            first = calls.copy()
            calls.clear()
            subject.multistart([], None, (1, 2, 3), restarts=2,
                               iterations=4, seed=9)
            self.assertEqual(first, calls)
        finally:
            subject.anneal = old

    def test_gpu_wire_board_requires_wide_score_indices(self):
        # GPU boards arrive as uint8. Base-25 quadgram-key arithmetic wraps
        # in that dtype, so parity/recomputation must widen them first.
        board = np.arange(25, dtype=np.uint8)
        row = np.asarray([20, 21, 22, 23, 24], dtype=np.int64)
        quad = np.arange(25 ** 4, dtype=np.float64)
        narrow = subject.base.score_indices(board[row], quad)
        wide = subject.base.score_indices(board.astype(np.int64)[row], quad)
        self.assertNotEqual(narrow, wide)


if __name__ == "__main__":
    unittest.main()
