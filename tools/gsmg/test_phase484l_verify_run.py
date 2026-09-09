#!/usr/bin/env python3

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase484l_verify_run as verifier


class Phase484LVerifierTests(unittest.TestCase):
    def test_verifier_has_no_budget_overrides(self):
        source = Path(verifier.__file__).read_text()
        self.assertNotIn("--minimum", source)
        self.assertNotIn("--fixtures", source)
        self.assertNotIn("--width", source)


if __name__ == "__main__":
    unittest.main()
