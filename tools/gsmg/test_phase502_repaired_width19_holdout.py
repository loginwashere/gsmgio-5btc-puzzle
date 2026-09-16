import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import phase502_repaired_width19_holdout as phase502


class Phase502Tests(unittest.TestCase):
    def test_fixture_invariants(self):
        fixture = phase502.make_variant(3)
        self.assertEqual(fixture["split"], "holdout")
        self.assertEqual(fixture["partition_swap_count"], 3)
        self.assertEqual(len(fixture["raw"]), 570)

    def test_fixture_universe_fails_closed(self):
        with self.assertRaises(ValueError):
            phase502.make_variant(2)

    def test_marker_fails_closed(self):
        payload = {"phase": 502, "fixture_index": 3}
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(phase502, "marker_payload", return_value=payload):
            root = Path(directory)
            phase502.ensure_marker(root, 3)
            (root/"objective_marker.json").write_text("{}\n")
            with self.assertRaises(RuntimeError):
                phase502.ensure_marker(root, 3)

    def test_self_test(self):
        result = phase502.self_test()
        self.assertEqual(result["fixtures"], [3, 4])
        self.assertFalse(result["faed_scored"])


if __name__ == "__main__":
    unittest.main()
