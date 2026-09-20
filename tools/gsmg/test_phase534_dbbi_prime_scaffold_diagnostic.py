import random
import sys
import unittest
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase534_dbbi_prime_scaffold_diagnostic as p
import phase534_scaffold_rarity_addendum as rarity


class ScaffoldTests(unittest.TestCase):
    def test_independent_segmenter_cross_check(self):
        self.assertEqual(p.self_test()['status'], 'passed')

    def test_hosts_histogram_and_grammar_preserved(self):
        for tokens in p.enumerate_complete_parses(p.DBBI):
            rng = random.Random(731 + len(tokens))
            for _ in range(20):
                raw = p.shuffled_scaffold(tokens, rng)
                self.assertEqual(Counter(raw), Counter(p.DBBI))
                self.assertTrue(rarity.has_parse(raw))

    def test_invalid_pair_counts_as_failure(self):
        result = p.summarize_null(lambda: 'acdb', 3, p.metrics(p.DBBI))
        self.assertEqual(result['counts'].get('be_valid', 0), 0)
        self.assertEqual(result['be_unique_first_rate'], 0)

    def test_rarity_parser_positive_and_negative(self):
        self.assertTrue(rarity.has_parse('ab'))
        self.assertFalse(rarity.has_parse('aa'))
        self.assertTrue(rarity.has_parse(p.DBBI))


if __name__ == '__main__':
    unittest.main()
