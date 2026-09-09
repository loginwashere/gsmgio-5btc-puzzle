#!/usr/bin/env python3

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase484c_width7_raw_symbol_vic_solver as audit


class Phase484CWidth7Tests(unittest.TestCase):
    def test_width7_geometry_and_family_size(self):
        self.assertEqual(audit.HYPOTHESES_TOTAL, 181440)
        geometry = audit.base.Geometry(audit.base.RAW_LENGTH, 7)
        self.assertEqual(geometry.column_lengths, (82, 82, 82, 81, 81, 81, 81))

    def test_rejects_wrong_observed_length(self):
        model = audit.base.SpectralModel.from_training_corpus()
        with self.assertRaises(ValueError):
            audit.enumerate_joint("a" * 569, model, keep=1)

    def test_self_test(self):
        audit.self_test()

    def test_worker_budget_is_explicit(self):
        self.assertEqual(audit.WORKERS, 8)

    def test_board_budget_is_explicit(self):
        self.assertEqual(audit.JOINT_KEEP, 1536)
        self.assertEqual((audit.BOARD_RESTARTS, audit.BOARD_ITERS), (2, 6000))
        self.assertEqual(
            audit.TAIL_FIXTURES,
            (("vic_profile", 57), ("broad_random", 56)),
        )
        self.assertEqual(audit.SEED_HOLDOUT, 0x484C401D)


if __name__ == "__main__":
    unittest.main()
