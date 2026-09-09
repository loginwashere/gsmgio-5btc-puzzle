#!/usr/bin/env python3

import unittest

import phase482a_faed_frequency_signature_audit as audit


class Phase482ATests(unittest.TestCase):
    def test_self_test(self):
        self.assertTrue(audit.self_test())

    def test_signature_is_label_and_order_invariant(self):
        self.assertEqual(audit.signature("AAABBC"), audit.signature("XXXYYZ"))
        self.assertEqual(audit.signature("AAABBC"), audit.signature("CBABAA"))

    def test_rolling_matches_brute_force(self):
        text = ("ABCDE" * 100)[:450]
        for start, current in audit.iter_window_signatures(text):
            self.assertEqual(current, audit.signature(text[start:start + audit.WINDOW]))


if __name__ == "__main__":
    unittest.main()
