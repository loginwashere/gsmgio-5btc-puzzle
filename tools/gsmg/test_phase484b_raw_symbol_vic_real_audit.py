#!/usr/bin/env python3

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase484b_raw_symbol_vic_real_audit as audit


class Phase484BRealRunnerTests(unittest.TestCase):
    def test_pinned_faed_shape(self):
        self.assertEqual(len(audit.FAED), 570)
        self.assertEqual(
            audit.input_sha256(audit.FAED),
            "066191b4aafc114fbca7f0d168382f40129c4ff18490375b689741081d5ef3c2",
        )

    def test_small_synthetic_output_is_ranked_and_complete(self):
        fixture = audit.solver.make_fixture(2, 0, 47, board_mode="broad_random")
        result = audit.solve_observed_width(
            fixture["observed"], 2, joint_keep=4,
            board_restarts=1, board_iters=100, seed=9,
        )
        scores = [candidate["normalized_score"] for candidate in result["top"]]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertTrue(all(candidate["plaintext"] for candidate in result["top"]))


if __name__ == "__main__":
    unittest.main()
