#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase519_p391_material_all_blobs_audit as p519


class Phase519Tests(unittest.TestCase):
    def test_self_test_reproduces_391_and_widens_negative(self):
        result = p519.self_test()
        original = result["original"]
        widened = result["widened"]
        self.assertEqual(original["blobs"], ("P32TRAILING",))
        self.assertEqual(original["total_hits"], 0)
        self.assertEqual(set(widened["blobs"]), {"SALPH", "COSMIC", "P32TRAILING", "URLBLOB"})
        self.assertEqual(widened["material_count"], 69)
        self.assertEqual(widened["total_hits"], 0)
        self.assertEqual(widened["effective_decrypt_attempts"], original["effective_decrypt_attempts"] * 4)


if __name__ == "__main__":
    unittest.main()
