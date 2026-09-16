#!/usr/bin/env python3

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase513_giant_decimal_escape_digit_audit as audit


class Phase513GiantDecimalEscapeDigitTests(unittest.TestCase):
    def test_self_test_passes(self):
        audit.self_test()

    def test_a1i9_reproduces_phase273_exactly(self):
        report = audit.audit(run_oracles=False)
        self.assertEqual(report["a1i9_reused_from_phase273"], {"DBBI": True, "FAED": True})
        by_label = {row["label"]: row for row in report["rows"]}
        self.assertEqual(
            by_label["DBBI/a1i9"]["sha256"],
            "7270ed152fa64b85f144f99b49352ecabeb01c0f0b624fb71cb648f91d1d8b80",
        )
        self.assertEqual(
            by_label["FAED/a1i9"]["sha256"],
            "7f14db2d90301b8e1d16ff014ad3e84ba75350ef828ad9b8a8a26b1e69302de9",
        )

    def test_a0i8_is_new_and_distinct(self):
        report = audit.audit(run_oracles=False)
        by_label = {row["label"]: row for row in report["rows"]}
        for source in ("DBBI", "FAED"):
            self.assertNotEqual(
                by_label[f"{source}/a0i8"]["sha256"],
                by_label[f"{source}/a1i9"]["sha256"],
            )
        self.assertEqual(
            by_label["DBBI/a0i8"]["sha256"],
            "38f51afc69242ea4a9a6ab7e9f05166956f66b24820e91c835abed48e138b920",
        )
        self.assertEqual(
            by_label["FAED/a0i8"]["sha256"],
            "4eb87c8314f06db20cc88ced00895535c2d3a59ccce81b1520d570a0965a4c6b",
        )

    def test_printable_ratios_match_reported_table(self):
        report = audit.audit(run_oracles=False)
        by_label = {row["label"]: row for row in report["rows"]}
        self.assertAlmostEqual(by_label["DBBI/a1i9"]["strict_printable_ratio"], 0.421, places=3)
        self.assertAlmostEqual(by_label["DBBI/a0i8"]["strict_printable_ratio"], 0.395, places=3)
        self.assertAlmostEqual(by_label["FAED/a1i9"]["strict_printable_ratio"], 0.329, places=3)
        self.assertAlmostEqual(by_label["FAED/a0i8"]["strict_printable_ratio"], 0.295, places=3)

    def test_no_odd_hex_rejections(self):
        report = audit.audit(run_oracles=False)
        self.assertEqual(report["rejected_variants"], ())

    def test_full_oracle_sweep_zero_hits(self):
        report = audit.audit(run_oracles=True)
        self.assertEqual(report["unique_password_material_count"], 12)
        self.assertTrue(report["phase32_positive_control"])
        self.assertEqual(report["hits"], [])


if __name__ == "__main__":
    unittest.main()
