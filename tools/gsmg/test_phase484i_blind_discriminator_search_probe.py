#!/usr/bin/env python3

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase484i_blind_discriminator_search_probe as probe


class Phase484ITests(unittest.TestCase):
    def test_self_test(self):
        probe.self_test()

    def test_no_truth_seeded_start_class(self):
        source = Path(probe.__file__).read_text()
        self.assertNotIn('"controlled"', source)
        self.assertNotIn("controlled_start", source)

    def test_faed_is_prohibited(self):
        source = Path(probe.__file__).read_text()
        self.assertNotIn("from data import FAED", source)
        self.assertNotIn("data.FAED", source)


if __name__ == "__main__":
    unittest.main()
