#!/usr/bin/env python3
from __future__ import annotations

import unittest

import phase512j_rust_sweep_validation as phase512j


class Phase512JRustSweepValidationTests(unittest.TestCase):
    def test_self_test(self):
        result = phase512j.self_test()
        self.assertEqual(result["self_test"], "pass")
        self.assertGreater(result["cells_checked"], 0)

    def test_sweep_parity_matches_python_reference(self):
        parity = phase512j.run_sweep_parity()
        self.assertTrue(parity["match"])
        self.assertTrue(parity["cells_match"])
        self.assertEqual(parity["python_status"], parity["rust_status"])
        self.assertEqual(parity["python_hit_cells"], parity["rust_hit_cells"])


if __name__ == "__main__":
    unittest.main()
