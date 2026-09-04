#!/usr/bin/env python3

import unittest
from collections import Counter

import phase474_selected31_exact_cover_anagram_audit as audit


class Phase474Tests(unittest.TestCase):
    def test_structural_self_test(self):
        audit.structural_self_test()

    def test_independent_lexicon_is_pinned_and_clean(self):
        words = audit.load_independent_words()
        self.assertEqual(len(words), 2050)
        self.assertIn("safe", words)
        self.assertNotIn(audit.TARGET, words)

    def test_discovery_rule_is_mechanical(self):
        words = audit.load_discovery_words()
        self.assertIn("salvation", words)
        self.assertIn("ying", words)
        self.assertTrue(all(word in {"a", "i"} or 3 <= len(word) <= 12 for word in words if word not in audit.load_independent_words()))

    def test_historical_phrases_are_exact(self):
        for phrase in audit.MANUAL_ANAGRAMS:
            self.assertEqual(Counter(audit.normalize_letters(phrase)), Counter(audit.TARGET))


if __name__ == "__main__":
    unittest.main()
