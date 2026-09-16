import tempfile
import unittest
from pathlib import Path

import phase494_unrestricted_board_full_pipeline as phase494


class Phase494Tests(unittest.TestCase):
    def test_self_test(self):
        self.assertFalse(phase494.self_test()["faed_scored"])

    def test_marker_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            phase494.ensure_marker(root)
            path = root / "objective_marker.json"
            path.write_text("{}\n")
            with self.assertRaises(RuntimeError):
                phase494.ensure_marker(root)


if __name__ == "__main__":
    unittest.main()
