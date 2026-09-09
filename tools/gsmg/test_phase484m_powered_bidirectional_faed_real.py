#!/usr/bin/env python3

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase484m_powered_bidirectional_faed_real as real


class Phase484MTests(unittest.TestCase):
    def test_self_test(self):
        real.self_test()

    def test_exact_cell_family(self):
        self.assertEqual(real.WIDTHS, (10, 15))
        self.assertEqual(len(real.PAIRS), 36)
        self.assertEqual(len(real.WIDTHS) * len(real.PAIRS), 72)

    def test_lock_pins_holdout_evidence(self):
        names = real.pinned_files()
        for required in ("holdout_lock", "holdout_result", "holdout_verification"):
            self.assertIn(required, names)

    def test_no_cli_budget_override(self):
        source = Path(real.__file__).read_text()
        self.assertNotIn("--beam", source)
        self.assertNotIn("--width", source)
        self.assertNotIn("--pair", source)


if __name__ == "__main__":
    unittest.main()
