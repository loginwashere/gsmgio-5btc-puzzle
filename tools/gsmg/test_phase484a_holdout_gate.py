#!/usr/bin/env python3

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase484a_holdout_gate as gate


class Phase484AHoldoutGateTests(unittest.TestCase):
    def test_fixture_gate_is_conjunctive(self):
        good = {
            "joint_recovery": True,
            "plaintext_char_accuracy": 1.0,
            "board_accuracy": 0.8,
            "decoded_length": 400,
            "true_length": 400,
        }
        self.assertTrue(gate.fixture_passes(good))
        for field in ("joint_recovery", "plaintext_char_accuracy", "board_accuracy", "decoded_length"):
            bad = dict(good)
            bad[field] = False if field == "joint_recovery" else 0
            self.assertFalse(gate.fixture_passes(bad))

    def test_pair_schedule_spans_enumeration(self):
        self.assertEqual(len(gate.PAIR_INDICES), 10)
        self.assertEqual(gate.PAIR_INDICES[0], 0)
        self.assertEqual(gate.PAIR_INDICES[-1], 35)

    def test_frozen_budget_constants(self):
        self.assertEqual(gate.JOINT_KEEP, 1536)
        self.assertEqual((gate.BOARD_RESTARTS, gate.BOARD_ITERS), (2, 6000))
        self.assertEqual((gate.BOARD_T0, gate.BOARD_T1), (20.0, 1.0))
        self.assertEqual(gate.WORKERS, 8)


if __name__ == "__main__":
    unittest.main()
