import sys, unittest
from pathlib import Path
import numpy as np
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import phase484p_partial_board_recovery_probe as subject

class Phase484PTests(unittest.TestCase):
    def test_row_score_counts_only_within_rows(self):
        quad = np.ones(25 ** 4)
        rows = [np.arange(5), np.arange(3)]
        self.assertEqual(subject.row_windows(rows), 2)
        self.assertEqual(subject.row_score(np.arange(25), rows, quad), 2)

if __name__ == "__main__": unittest.main()
