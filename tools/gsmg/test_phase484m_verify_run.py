#!/usr/bin/env python3

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase484m_verify_run as verifier


class Phase484MVerifierTests(unittest.TestCase):
    def test_verifier_has_no_runtime_options(self):
        source = Path(verifier.__file__).read_text()
        self.assertNotIn("argparse", source)


if __name__ == "__main__":
    unittest.main()
