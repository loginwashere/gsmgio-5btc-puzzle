import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase535_selection_a_matrix_composition as p


class CompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = p.run()

    def test_five_mappings_and_two_collision_free(self):
        rows = self.result['rows']
        self.assertEqual(len(rows), 5)
        self.assertEqual(sum(r['variants'][0]['collisions'] == 0 for r in rows), 2)

    def test_selection_a_preserves_tail_and_policy_independence(self):
        row = next(r for r in self.result['rows'] if r['represents_source_bytes_1_through_23_once'])
        self.assertEqual(row['unplaced_tail'], 'e')
        self.assertEqual({v['output'] for v in row['variants']}, {'IZLKESKGGIPPEN'})
        self.assertTrue(all(v['occupied_cells'] == 83 for v in row['variants']))

    def test_zeroing_preserves_row_sums(self):
        row = next(r for r in self.result['rows'] if r['represents_source_bytes_1_through_23_once'])
        host, payload = self.result['selection_a_zeroing_comparison']
        self.assertEqual([a+b for a,b in zip(host['row_sums'], payload['row_sums'])], row['variants'][0]['row_sums'])


if __name__ == '__main__':
    unittest.main()
