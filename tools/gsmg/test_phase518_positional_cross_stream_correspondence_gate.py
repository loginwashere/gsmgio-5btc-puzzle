#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase518_positional_cross_stream_correspondence_gate as p518


class Phase518Tests(unittest.TestCase):
    def test_self_test_passes(self):
        p518.self_test()

    def test_block_partition_tiles_exactly(self):
        for length in (91, 570):
            for k in p518.GRANULARITIES:
                total = sum(len(block) for block in p518.blocks("x" * length, k))
                self.assertEqual(total, length)

    def test_mode_symbol_tiebreak_is_alphabetical(self):
        self.assertEqual(p518.mode_symbol("cab"), "a")
        self.assertEqual(p518.mode_symbol("aabbcc"), "a")

    def test_k91_reduces_to_raw_dbbi_symbol(self):
        from data import DBBI
        self.assertEqual(p518.block_mode_sequence(DBBI, 91), tuple(DBBI))

    def test_controls_pass(self):
        results = p518.run_controls(2000, 51820260917 + 500000)
        self.assertEqual(
            results["independent_fixture"]["phase_level_decision"],
            "no_calibrated_correspondence",
        )
        self.assertEqual(
            results["planted_fixture"]["phase_level_decision"],
            "robust_correspondence",
        )

    def test_phase_level_decision_uses_k91_only(self):
        self.assertEqual(
            p518.phase_level_decision({91: "robust_correspondence", 13: "no_calibrated_correspondence"}),
            "robust_correspondence",
        )
        self.assertEqual(
            p518.phase_level_decision({91: "no_calibrated_correspondence", 13: "robust_correspondence"}),
            "no_calibrated_correspondence",
        )

    def test_real_result_is_negative(self):
        result = p518.run(trials=2000)
        self.assertEqual(result["phase_level_decision"], "no_calibrated_correspondence")
        self.assertEqual(result["by_k"]["91"]["decision"], "no_calibrated_correspondence")


if __name__ == "__main__":
    unittest.main()
