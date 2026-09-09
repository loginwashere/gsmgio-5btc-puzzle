import sys, unittest
from pathlib import Path
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import phase484o_joint_board_order_ceiling as subject

class Phase484OTests(unittest.TestCase):
    def test_planted_board_is_permutation(self):
        f = subject.base.make_fixture(19, 0, 23, seed=subject.learned.SEED,
            board_mode="vic_profile", split="dev")
        self.assertEqual(sorted(subject.planted_board(f)), list(range(25)))

    def test_disjoint_swaps_have_exact_accuracy(self):
        board = bytes(range(25))
        changed = subject.perturb_board(board, 4, 23)
        self.assertEqual(sum(a == b for a, b in zip(board, changed)), 17)
        self.assertEqual(sorted(changed), list(range(25)))

if __name__ == "__main__": unittest.main()
