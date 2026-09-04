#!/usr/bin/env python3

import json
import unittest
from pathlib import Path

import numpy as np

import phase476_p91_second_bifid_key_audit as phase476


class Phase476AuditTests(unittest.TestCase):
    def test_small_complete_audit(self):
        report = phase476.audit(trials=48, seed=phase476.DEFAULT_SEED,
                                fixed_key_seed=phase476.FIXED_KEY_SEED, batch_size=16)
        observed = report["observed"]
        self.assertEqual(observed["first_pass_prefix"], "BTCSEED")
        self.assertEqual(len(observed["p91"]), 91)
        self.assertEqual(len(observed["second_pass"]), 472)
        self.assertTrue(observed["vectorized_matches_scalar"])
        self.assertTrue(observed["roundtrip_matches_q472"])
        self.assertTrue(report["planted_positive"]["roundtrip"])

    def test_dynamic_square_matches_build_grid(self):
        first = phase476.phase386_audit()["decoded"]
        p91 = first[7:98]
        vector = phase476.dynamic_squares_from_p91(
            phase476.alpha_indices(p91)[None, :]
        )[0]
        scalar_keyword, _grid, _pos = phase476.build_grid(p91)
        self.assertEqual(phase476.text_from_indices(vector), scalar_keyword)

    def test_dynamic_batch_is_row_local(self):
        first = phase476.phase386_audit()["decoded"]
        rows = np.stack((phase476.alpha_indices(first[7:98]),
                         phase476.alpha_indices(first[7:98])[::-1]))
        squares = phase476.dynamic_squares_from_p91(rows)
        self.assertFalse(np.array_equal(squares[0], squares[1]))

    def test_frozen_result_if_present(self):
        path = Path(__file__).with_name("phase476_result.json")
        if not path.exists():
            self.skipTest("full frozen result not generated")
        report = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(report["phase"], 476)
        self.assertEqual(report["primary_upstream_null"]["trials"], 100_000)
        self.assertEqual(report["secondary_fixed_p91_key_null"]["trials"], 100_000)
        self.assertEqual(report["oracle_calls"], 0)
        self.assertEqual(report["bitcoin_endpoint_calls"], 0)


if __name__ == "__main__":
    unittest.main()
