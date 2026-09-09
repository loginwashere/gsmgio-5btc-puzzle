import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase484x_corrected_faed_gi_rerun as subject


class Phase484XCorrectedFaedGiTests(unittest.TestCase):
    def test_self_test(self):
        result = subject.self_test()
        self.assertEqual(result["tokens"], 436)
        self.assertEqual(result["single_slots"], 302)


if __name__ == "__main__":
    unittest.main()
