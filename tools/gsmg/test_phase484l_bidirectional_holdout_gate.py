#!/usr/bin/env python3

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase484l_bidirectional_holdout_gate as gate


class Phase484LTests(unittest.TestCase):
    def test_self_test(self):
        gate.self_test()

    def test_scope_excludes_width_19(self):
        self.assertEqual(gate.WIDTHS, (10, 15))

    def test_lock_prohibits_faed(self):
        payload = gate.lock_payload()
        self.assertTrue(payload["prohibitions"]["faed_scoring"])
        self.assertFalse(payload["faed_scored"])

    def test_source_does_not_import_faed(self):
        source = Path(gate.__file__).read_text()
        self.assertNotIn("from data import FAED", source)
        self.assertNotIn("data.FAED", source)


if __name__ == "__main__":
    unittest.main()
