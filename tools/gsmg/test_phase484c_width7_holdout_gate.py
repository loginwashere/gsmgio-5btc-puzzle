#!/usr/bin/env python3

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase484c_width7_holdout_gate as gate


class Phase484CWidth7HoldoutTests(unittest.TestCase):
    def test_gate_is_conjunctive(self):
        record = {
            "joint_recovery": True,
            "plaintext_char_accuracy": 0.95,
            "board_accuracy": 0.80,
            "decoded_length": 400,
            "true_length": 400,
        }
        self.assertTrue(gate.fixture_passes(record))
        record["joint_recovery"] = False
        self.assertFalse(gate.fixture_passes(record))

    def test_pair_schedule_spans_family(self):
        self.assertEqual(len(gate.PAIR_INDICES), 10)
        self.assertEqual((gate.PAIR_INDICES[0], gate.PAIR_INDICES[-1]), (0, 35))


if __name__ == "__main__":
    unittest.main()
