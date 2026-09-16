#!/usr/bin/env python3
from __future__ import annotations

import unittest

import phase511_closed_corpus_character_signal as phase511


class Phase511Tests(unittest.TestCase):
    def test_self_test(self):
        self.assertEqual(phase511.self_test()["self_test"], "pass")

    def test_no_cross_document_ngrams(self):
        contexts, grams = phase511.train_markov(["ab", "cd"], 2)
        self.assertNotIn("bc", grams)
        self.assertEqual(contexts, {"a": 1, "c": 1})

    def test_add_one_unseen_probability(self):
        model = phase511.train_markov(["aaaa"], 2)
        seen = phase511.markov_score("aa", 2, model)
        unseen = phase511.markov_score("ab", 2, model)
        self.assertGreater(seen, unseen)

    def test_family_standardization_is_symmetric(self):
        first = phase511.zscores([3.0, 1.0, 2.0])
        second = phase511.zscores([1.0, 2.0, 3.0])
        self.assertAlmostEqual(first[0], second[2])
        self.assertAlmostEqual(first[1], second[0])
        self.assertAlmostEqual(first[2], second[1])

    def test_lock_absence_fails_closed(self):
        original = phase511.LOCK
        try:
            phase511.LOCK = original.with_name("nonexistent_phase511_lock.json")
            with self.assertRaises(RuntimeError):
                phase511.verify_lock()
        finally:
            phase511.LOCK = original


if __name__ == "__main__":
    unittest.main()
