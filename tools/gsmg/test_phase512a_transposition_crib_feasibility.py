#!/usr/bin/env python3
from __future__ import annotations

import unittest

import phase512a_transposition_crib_feasibility as phase512


class Phase512Tests(unittest.TestCase):
    def test_self_test(self):
        self.assertEqual(phase512.self_test()["self_test"], "pass")

    def test_all_cribs_are_exact_and_representable(self):
        phase512.validate_cribs()
        self.assertEqual({key: len(value) for key, value in phase512.CRIBS.items()}, {
            "phase1_credential": 53,
            "phase322_validation_answer": 91,
            "creator_macro_message": 161,
        })

    def test_wrong_order_rejected_on_toy_fixture(self):
        fixture = phase512.make_fixture("phase322_validation_answer", 15)
        wrong = list(fixture["order"])
        wrong[0], wrong[1] = wrong[1], wrong[0]
        matches = phase512.crib_matches_for_order(
            fixture["observed"], 15, wrong, phase512.PAIR, fixture["crib"])
        self.assertNotIn(fixture["planted_token_offset"], matches)

    def test_geometry_round_trip(self):
        fixture = phase512.make_fixture("creator_macro_message", 38)
        restored = phase512.base.Geometry(570, 38).decrypt(
            fixture["observed"], fixture["order"])
        self.assertEqual(restored, fixture["raw"])


if __name__ == "__main__":
    unittest.main()
