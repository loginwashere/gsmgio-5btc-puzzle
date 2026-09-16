#!/usr/bin/env python3

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase515_ternary_decomposition_square_matrix_audit as audit


class Phase515TernaryDecompositionSquareMatrixTests(unittest.TestCase):
    def test_self_test_passes(self):
        audit.self_test()

    def test_expansion_lengths_are_exact_perfect_squares(self):
        self.assertEqual(len(audit.expand(audit.DBBI)), 169)
        self.assertEqual(len(audit.expand(audit.FAED)), 1225)
        self.assertEqual(13 * 13, 169)
        self.assertEqual(35 * 35, 1225)

    def test_sixteen_of_thirty_two_cells_valid(self):
        report = audit.audit(run_oracles=False)
        self.assertEqual(len(report["rows"]), 16)
        self.assertEqual(len(report["rejected_variants"]), 16)

    def test_printable_ratios_are_in_the_noise_range(self):
        report = audit.audit(run_oracles=False)
        for row in report["rows"]:
            self.assertLess(row["strict_printable_ratio"], 0.5)

    def test_full_oracle_sweep_zero_hits(self):
        report = audit.audit(run_oracles=True)
        self.assertEqual(report["unique_password_material_count"], 48)
        self.assertTrue(report["phase32_positive_control"])
        self.assertEqual(report["hits"], [])


if __name__ == "__main__":
    unittest.main()
