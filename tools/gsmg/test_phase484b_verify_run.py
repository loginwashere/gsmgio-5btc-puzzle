#!/usr/bin/env python3

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase484b_verify_run as verify


class Phase484BVerifierTests(unittest.TestCase):
    def test_rejects_empty_result(self):
        self.assertTrue(verify.validate_result({}))


if __name__ == "__main__":
    unittest.main()
