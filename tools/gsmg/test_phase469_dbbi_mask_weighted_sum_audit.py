#!/usr/bin/env python3

import unittest

import phase469_dbbi_mask_weighted_sum_audit as audit


class Phase469StructuralTest(unittest.TestCase):
    def test_helpers(self):
        audit.structural_self_test()

    def test_live_invariants(self):
        report = audit.build_report()
        self.assertEqual(report["source_lengths"], {"dbbi": 91, "aligned_plaintext": 91})
        self.assertEqual(report["selected_position_count"], 31)
        self.assertEqual(set(report["selected_dbbi_symbols"]), {"b", "e"})
        self.assertEqual(report["selected_dbbi_symbols"].count("b"), 23)
        self.assertEqual(report["selected_dbbi_symbols"].count("e"), 8)
        for shape in report["shapes"].values():
            counts = shape["selected_escape_counts"]
            self.assertEqual(counts["b"]["total"], 23)
            self.assertEqual(counts["e"]["total"], 8)
            for partition in ("selected", "complement"):
                for values in shape["partitions"][partition].values():
                    self.assertFalse(values["rows_clue_hits"])
                    self.assertFalse(values["columns_clue_hits"])
                    self.assertFalse(values["rows_known_list_matches"])
                    self.assertFalse(values["columns_known_list_matches"])
        self.assertEqual(report["password_materials_generated"], 0)
        self.assertEqual(report["decryptions_attempted"], 0)
        self.assertEqual(report["oracle_calls"], 0)


if __name__ == "__main__":
    unittest.main()
