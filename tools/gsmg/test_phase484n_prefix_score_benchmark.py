import unittest
from pathlib import Path


class Phase484NSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = (Path(__file__).with_name(
            "phase484n_prefix_score_benchmark.cu").read_text())

    def test_exact_feature_count(self):
        self.assertIn("constexpr int FEATURES = 20;", self.text)

    def test_all_eight_lags(self):
        self.assertIn("for (int lag = 1; lag <= 8; ++lag)", self.text)

    def test_parity_is_fail_closed(self):
        self.assertIn("return max_error <= 1e-10 ? 0 : 1;", self.text)

    def test_no_faed_dependency(self):
        self.assertNotIn("FAED", self.text)


if __name__ == "__main__":
    unittest.main()
