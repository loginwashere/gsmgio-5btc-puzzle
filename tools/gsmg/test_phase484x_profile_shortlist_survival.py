import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase484x_profile_shortlist_survival as subject


class Phase484XProfileShortlistSurvivalTests(unittest.TestCase):
    def test_self_test(self):
        self.assertEqual(subject.self_test(), {"start_depth": 4,
                                               "stop_depth": 8})


if __name__ == "__main__":
    unittest.main()
