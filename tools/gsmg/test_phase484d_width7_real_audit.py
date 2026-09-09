#!/usr/bin/env python3

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase484d_width7_real_audit as audit


class Phase484DWidth7RealTests(unittest.TestCase):
    def test_pinned_input_and_family(self):
        audit.self_test()
        self.assertEqual(audit.TOP_COUNT, 10)
        self.assertEqual(audit.HOLDOUT_SCORE_FLOOR, -4.507065492983351)


if __name__ == "__main__":
    unittest.main()
