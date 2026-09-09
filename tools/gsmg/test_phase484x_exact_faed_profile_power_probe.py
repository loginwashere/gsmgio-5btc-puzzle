import collections
import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase484x_exact_faed_profile_power_probe as subject


class Phase484XExactProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = subject.make_fixture(0)

    def test_exact_raw_histogram(self):
        self.assertEqual(collections.Counter(self.fixture["raw"]),
                         collections.Counter(subject.TARGET_RAW_COUNTS))

    def test_exact_token_histogram(self):
        tokens = subject.base.segment_raw(self.fixture["raw"], subject.PAIR)
        self.assertEqual(collections.Counter(tokens),
                         collections.Counter(subject.TARGET_TOKEN_COUNTS))
        self.assertEqual(len(tokens), 436)

    def test_minimum_edit_count_matches_hamming_distance(self):
        distance = sum(left != right for left, right in zip(
            self.fixture["source_plaintext"], self.fixture["plaintext"]))
        self.assertEqual(distance, self.fixture["minimum_edit_count"])

    def test_fixture_is_deterministic(self):
        self.assertEqual(self.fixture, subject.make_fixture(0))


if __name__ == "__main__":
    unittest.main()
