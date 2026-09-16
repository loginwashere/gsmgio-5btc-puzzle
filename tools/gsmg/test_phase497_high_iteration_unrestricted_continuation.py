import json
import tempfile
import unittest
from pathlib import Path

import phase497_high_iteration_unrestricted_continuation as phase497


class Phase497Tests(unittest.TestCase):
    def test_self_test(self):
        result = phase497.self_test()
        self.assertFalse(result["faed_scored"])
        self.assertTrue(result["inputs_verified"])

    def test_marker_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            phase497.ensure_marker(root)
            marker = root / "objective_marker.json"
            marker.write_text(json.dumps({"tampered": True}) + "\n")
            with self.assertRaises(RuntimeError):
                phase497.ensure_marker(root)


if __name__ == "__main__":
    unittest.main()
