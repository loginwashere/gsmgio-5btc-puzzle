import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase536_prime_scaffold_numeric_text as p


class NumericGeneratorTests(unittest.TestCase):
    def test_numeric_roundtrip_and_known_vectors(self):
        self.assertEqual(p.encode('A', 'D10'), '65')
        self.assertEqual(p.encode('A', 'R9'), '72')
        self.assertEqual(p.encode('A', 'B9'), '072')
        for text in ('ABCDEFGHIJKLMNOPQRST', 'a'.join('bcdefghijklmnopqrstu')):
            for model in p.MODELS:
                self.assertEqual(p.decode(p.encode(text, model), model), text.encode())

    def test_pattern_and_mapping_agree(self):
        for left, right in [('0012','aabc'), ('0012','abbc'), ('0012','aabb'), ('0120','abca')]:
            self.assertEqual(p.pattern(left) == p.pattern(right), p.matching_map(left, right) is not None)

    def test_tail_is_mandatory_and_raw_roundtrips(self):
        for target in p.target_records():
            self.assertEqual(p.insert_hosts(target['residue'], target['tokens']), p.DBBI)
            with self.assertRaises(ValueError):
                p.insert_hosts(target['residue'][:-1], target['tokens'])

    def test_length_bound_pruning_is_sound(self):
        for model in p.MODELS:
            for case in p.CASES:
                letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' if case == 'upper' else 'abcdefghijklmnopqrstuvwxyz'
                for n in range(p.MIN_WINDOW, p.MAX_WINDOW+1):
                    for text in (letters[0]*n, letters[-1]*n, (letters*2)[:n]):
                        length = len(p.encode(text, model))
                        if length in p.LENGTHS:
                            self.assertIn(n, p.eligible_lengths(model, case, length))

    def test_all_eligible_planted_cells_recover(self):
        rows = p.planted_gate()
        self.assertEqual(len(rows), 12)
        self.assertTrue(all(r['status'] in ('exactly_recovered','structurally_ineligible') for r in rows))
        self.assertTrue(any(r['status'] == 'exactly_recovered' for r in rows))


if __name__ == '__main__':
    unittest.main()
