#!/usr/bin/env python3

import json
import unittest
from pathlib import Path

import phase475_dbbi_p91_dependency_aware_audit as phase475


class Phase475AuditTests(unittest.TestCase):
    def test_primitives_and_dependency_aware_null(self):
        report = phase475.audit(trials=64, seed=phase475.DEFAULT_SEED, batch_size=16)
        self.assertEqual(report["observed"]["decoded_prefix"], "BTCSEED")
        self.assertTrue(report["observed"]["p91_matches_phase386_slice"])
        self.assertEqual(len(report["observed"]["family"]), 6)
        self.assertTrue(report["alphabet_subtraction_roundtrip"])
        self.assertTrue(report["coordinate_subtraction_roundtrip"])
        self.assertEqual(report["null"]["trials"], 64)
        self.assertEqual(sum(report["null"]["winning_operation_counts"].values()), 64)

    def test_vectorized_p91_matches_phase386(self):
        _keyword, lookup, positions = phase475.square_arrays()
        faed = phase475.alpha_indices(phase475.FAED)[None, :]
        vectorized = phase475.text_from_indices(
            phase475.decode_p91_batch(faed, lookup, positions)[0]
        )
        scalar = phase475.phase386_audit()["decoded"][7:98]
        self.assertEqual(vectorized, scalar)

    def test_frozen_result_if_present(self):
        path = Path(__file__).with_name("phase475_result.json")
        if not path.exists():
            self.skipTest("full frozen result not generated")
        report = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(report["phase"], 475)
        self.assertEqual(report["null"]["trials"], phase475.DEFAULT_TRIALS)
        self.assertEqual(report["null"]["seed"], phase475.DEFAULT_SEED)
        self.assertEqual(len(report["family_labels"]), 6)
        self.assertEqual(report["oracle_calls"], 0)
        self.assertEqual(report["bitcoin_endpoint_calls"], 0)


if __name__ == "__main__":
    unittest.main()
