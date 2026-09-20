#!/usr/bin/env python3
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase541_round2_exec as e


class Phase541Tests(unittest.TestCase):
    def test_static_check(self):
        self.assertTrue(e.control_static())

    def test_sandbox_basic_and_limits(self):
        dp = e.WORK / "data.json"
        good = e.run_sandboxed(e.GOOD, dp)
        self.assertTrue(good["ok"])
        self.assertEqual(good["outputs"][1], "xxx")
        bad = e.run_sandboxed("def run(d):\n    return [1 // 0]\n", dp)
        self.assertFalse(bad["ok"])
        big = e.run_sandboxed("def run(d):\n    return [str(i) for i in range(4000)]\n", dp)
        self.assertEqual((len(big["outputs"]), big["returned"]), (e.MAX_RETURN, 4000))

    def test_sandbox_blocks_import_and_file_access(self):
        dp = e.WORK / "data.json"
        self.assertFalse(e.run_sandboxed("def run(d):\n    import os\n    return []\n", dp)["ok"])
        # bypass attempts are stopped statically
        for code in ("def run(d):\n    return [str(open)]\n", "def run(d):\n    return [str(().__class__)]\n"):
            self.assertFalse(e.static_check(code)[0])

    def test_keyshape_exactness(self):
        self.assertTrue(e.control_keyshape())

    def test_data_integrity(self):
        self.assertTrue(e.control_data())

    def test_no_oracle_or_decrypt_in_namespace(self):
        for name in ("aes_try_open", "aes_try_open_bytes", "passphrase_hits", "BLOBS"):
            self.assertNotIn(name, dir(e))

    def test_bounds_are_consistent(self):
        self.assertLessEqual(e.MAX_TRIED_PER_PROPOSAL * 10, e.MAX_TRIED_PER_AGENT * 2)
        self.assertGreaterEqual(e.MAX_RETURN, e.MAX_TRIED_PER_PROPOSAL)


if __name__ == "__main__":
    unittest.main()
