import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import phase499_unrestricted_width19_holdout as phase499


class Phase499Tests(unittest.TestCase):
    def test_holdout_variant_has_frozen_invariants(self):
        fixture = phase499.make_holdout_variant(0)
        self.assertEqual(fixture["split"], "holdout")
        self.assertEqual(fixture["partition_swap_count"], 3)
        self.assertEqual(len(fixture["partition_swaps"]), 3)
        self.assertEqual(len(fixture["raw"]), 570)

    def test_fixture_universe_fails_closed(self):
        with self.assertRaises(ValueError):
            phase499.make_holdout_variant(3)

    def test_marker_fails_closed(self):
        payload = {"phase": 499, "fixture_index": 0}
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(phase499, "marker_payload",
                                  return_value=payload):
            root = Path(directory)
            phase499.ensure_marker(root, 0)
            marker = root / "objective_marker.json"
            marker.write_text(json.dumps({"tampered": True}) + "\n")
            with self.assertRaises(RuntimeError):
                phase499.ensure_marker(root, 0)

    def test_self_test(self):
        result = phase499.self_test()
        self.assertFalse(result["faed_scored"])
        self.assertEqual(result["fixtures"], [0, 1, 2])


if __name__ == "__main__":
    unittest.main()
