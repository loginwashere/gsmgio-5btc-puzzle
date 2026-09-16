#!/usr/bin/env python3
from __future__ import annotations

import unittest

import phase512i_rust_parity as phase512i


class Phase512IRustParityTests(unittest.TestCase):
    def test_self_test(self):
        result = phase512i.self_test()
        self.assertEqual(result["self_test"], "pass")

    def test_battery_all_match(self):
        result = phase512i.run_battery()
        self.assertTrue(result["all_cells_match"])
        self.assertEqual(result["mismatches"], [])
        self.assertFalse(result["faed_imported_or_scored"])
        self.assertEqual(len(result["cells"]), 10)


if __name__ == "__main__":
    unittest.main()
