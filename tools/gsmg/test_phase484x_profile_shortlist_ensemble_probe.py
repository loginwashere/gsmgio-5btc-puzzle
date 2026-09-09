import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase484x_profile_shortlist_ensemble_probe as subject


class Phase484XProfileShortlistEnsembleTests(unittest.TestCase):
    def test_self_test(self):
        result = subject.self_test()
        self.assertEqual(result["total_keep"], 262144)

    def test_digest_is_set_order_invariant(self):
        paths = [(2, 1), (1, 2), (0, 3)]
        self.assertEqual(subject.path_set_sha256(paths),
                         subject.path_set_sha256(reversed(paths)))


if __name__ == "__main__":
    unittest.main()
