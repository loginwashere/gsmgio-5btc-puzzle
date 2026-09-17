#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase517_closed_system_untried_theory_batch as p517


class Phase517Tests(unittest.TestCase):
    def test_self_test_passes(self):
        result = p517.self_test()
        self.assertTrue(result["ok"])

    def test_1a_negative(self):
        r = p517.test_1a()
        self.assertEqual(r["total_faed_sumlist_cells"], 112)
        self.assertFalse(r["any_consistent"])

    def test_1b_1c_negative(self):
        r = p517.test_1b_1c()
        self.assertFalse(r["any_consistent"])

    def test_6_negative(self):
        r = p517.test_6()
        self.assertFalse(r["any_hit"])

    def test_4_primary_negative(self):
        r = p517.test_4_primary()
        self.assertFalse(r["any_header_hit"])

    def test_10b_negative_and_pinned(self):
        r = p517.test_10b()
        self.assertEqual(r["dbbi_vs_validation_answer"], 59)
        self.assertEqual(r["dbbi_vs_phase32_plaintext_best"], 49)
        self.assertEqual(r["faed_vs_architect_full_best"], 449)
        self.assertFalse(r["any_consistent"])

    def test_8_negative(self):
        r = p517.test_8()
        self.assertEqual(r["total_hits"], 0)
        self.assertEqual(set(r["blobs"]), {"SALPH", "COSMIC", "URLBLOB"})

    def test_9_structural_elimination_and_negative(self):
        r = p517.test_9()
        b64 = r["base64_text_position_reading"]
        self.assertEqual(b64["variants_parsed_as_valid_blob"], 0)
        byte = r["ciphertext_byte_position_reading"]
        self.assertEqual(byte["variants_block_aligned"], 12)
        self.assertEqual(byte["hits"], [])

    def test_7_negative(self):
        r = p517.test_7()
        self.assertEqual(r["bodies_built"], 11)
        self.assertEqual(r["header_hits"], [])
        self.assertEqual(len(r["oracle_hits"]), 0)


if __name__ == "__main__":
    unittest.main()
