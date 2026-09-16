import json
import tempfile
import unittest
from pathlib import Path

import phase501_holdout0_depth11_repair as phase501


class Phase501Tests(unittest.TestCase):
    def test_self_test(self):
        result = phase501.self_test()
        self.assertEqual(result["changed_fields"],
                         ["coarse_iterations", "coarse_restarts"])
        self.assertFalse(result["holdout_gate_repaired"])

    def test_marker_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            phase501.ensure_marker(root)
            marker = root / "objective_marker.json"
            marker.write_text(json.dumps({"tampered": True}) + "\n")
            with self.assertRaises(RuntimeError):
                phase501.ensure_marker(root)


if __name__ == "__main__":
    unittest.main()
