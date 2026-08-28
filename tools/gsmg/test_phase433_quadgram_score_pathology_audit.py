#!/usr/bin/env python3

import random
import unittest

import phase431_bifid16_equivalence_class_audit as phase431
import phase433_quadgram_score_pathology_audit as audit
from phase387_btcseed_kmodest_checkpoint_audit import load_quadgrams


class Phase433Tests(unittest.TestCase):
    def test_pinned_english_beats_its_sorted_letters(self):
        logs, floor = load_quadgrams()
        english, digest = audit.english_control()
        self.assertEqual(len(english), 563)
        self.assertEqual(len(digest), 64)
        self.assertGreater(audit.score(english, logs, floor),
                           audit.score("".join(sorted(english)), logs, floor))

    def test_conditional_square_preserves_g_h_and_crib(self):
        original = audit.CANDIDATES[2][2]
        candidate = audit.conditional_square(original, random.Random(123))
        self.assertEqual(candidate.index("G"), original.index("G"))
        self.assertEqual(candidate.index("H"), original.index("H"))
        self.assertTrue(phase431.decode_square(candidate).startswith(audit.TARGET))

    def test_small_audit_has_all_frozen_controls(self):
        result = audit.audit(trials=3, rank_samples=5)
        self.assertEqual(len(result["candidates"]), 3)
        expected = {"exact_multiset_shuffle", "intact_digraph_shuffle",
                    "conditional_same_g_h_placement", "uniform_global_rank"}
        for row in result["candidates"]:
            self.assertEqual(set(row["controls"]), expected)
            self.assertEqual(row["profile"]["length"], 563)
            self.assertEqual(row["profile"]["distinct_ngrams"].keys(), {"1", "2", "3", "4"})


if __name__ == "__main__":
    unittest.main()
