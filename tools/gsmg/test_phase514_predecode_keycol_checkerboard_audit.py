#!/usr/bin/env python3

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase514_predecode_keycol_checkerboard_audit as audit


class Phase514PredecodeKeycolCheckerboardTests(unittest.TestCase):
    def test_self_test_passes(self):
        audit.self_test()

    def test_eight_streams_are_distinct_and_length_preserving(self):
        streams = []
        for target_name, (ciphertext, _) in audit.TARGETS.items():
            for label, stream in audit.stream_variants(target_name, ciphertext):
                self.assertEqual(len(stream), len(ciphertext))
                self.assertTrue(set(stream) <= set("abcdefghi"))
                streams.append(stream)
        self.assertEqual(len(streams), 8)
        self.assertEqual(len(set(streams)), 8)

    def test_full_pipeline_zero_aes_hits(self):
        report = audit.audit(shuffle_trials=20, run_aes=True)
        self.assertEqual(report["total_aes_hits"], 0)
        self.assertEqual(report["dbbi"]["checkerboard_candidate_count"], 88)
        self.assertEqual(report["faed"]["checkerboard_candidate_count"], 110)

    def test_shuffle_gate_shows_no_significant_signal(self):
        report = audit.audit(shuffle_trials=200, run_aes=False)
        for target_name in ("dbbi", "faed"):
            gate = report[target_name]["shuffle_gate"]
            # Well above any conventional significance threshold -- real best
            # score is unremarkable against the null distribution.
            self.assertGreater(gate["p_value"], 0.1)
            self.assertGreaterEqual(gate["null_max"], gate["real_best_score"])


if __name__ == "__main__":
    unittest.main()
