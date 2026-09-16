import unittest

import phase488_489_verify_records as verify


class VerifyRecordsTests(unittest.TestCase):
    def test_phase488_headlines(self):
        result = verify.verify_phase488()
        self.assertEqual(result["counts"]["dev"]["exact_top1"], 10)
        self.assertEqual(result["counts"]["holdout"]["exact_top1"], 11)

    def test_phase489_roundtrip(self):
        result = verify.verify_phase489()
        self.assertTrue(result["all_candidates_round_trip"])
        self.assertLess(result["max_score_recomputation_error"], 1e-10)


if __name__ == "__main__":
    unittest.main()
