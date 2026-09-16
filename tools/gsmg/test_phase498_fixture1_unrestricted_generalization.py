import json
import tempfile
import unittest
from pathlib import Path

import phase498_fixture1_unrestricted_generalization as phase498


class Phase498Tests(unittest.TestCase):
    def test_self_test(self):
        result = phase498.self_test()
        self.assertFalse(result["faed_scored"])
        self.assertEqual(result["fixture_index"], 1)

    def test_marker_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            phase498.ensure_marker(root)
            marker = root / "objective_marker.json"
            marker.write_text(json.dumps({"tampered": True}) + "\n")
            with self.assertRaises(RuntimeError):
                phase498.ensure_marker(root)


if __name__ == "__main__":
    unittest.main()
