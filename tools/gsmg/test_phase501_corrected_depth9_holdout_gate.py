import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import phase501_corrected_depth9_holdout_gate as phase501


class Phase501Tests(unittest.TestCase):
    def test_holdout_variant_has_frozen_invariants(self):
        fixture = phase501.make_holdout_variant(2)
        self.assertEqual(fixture["split"], "holdout")
        self.assertEqual(fixture["partition_swap_count"], 3)
        self.assertEqual(len(fixture["partition_swaps"]), 3)
        self.assertEqual(len(fixture["raw"]), 570)

    def test_fixture_universe_fails_closed(self):
        with self.assertRaises(ValueError):
            phase501.make_holdout_variant(0)
        with self.assertRaises(ValueError):
            phase501.make_holdout_variant(1)

    def test_rejected_fixtures_fail_construction_gate(self):
        # Fixtures 1 and 4 were excluded from FIXTURE_INDICES because they
        # fail the frozen language-quality gate under this swap variant, not
        # for difficulty or solver-behavior reasons; confirm that holds.
        with mock.patch.object(phase501, "FIXTURE_INDICES", (1, 2, 3, 5)):
            with self.assertRaises(AssertionError):
                phase501.make_holdout_variant(1)

    def test_marker_fails_closed(self):
        payload = {"phase": 501, "fixture_index": 2}
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(phase501, "marker_payload",
                                  return_value=payload):
            root = Path(directory)
            phase501.ensure_marker(root, 2)
            marker = root / "objective_marker.json"
            marker.write_text(json.dumps({"tampered": True}) + "\n")
            with self.assertRaises(RuntimeError):
                phase501.ensure_marker(root, 2)

    def test_self_test(self):
        result = phase501.self_test()
        self.assertFalse(result["faed_scored"])
        self.assertEqual(result["fixtures"], [2, 3, 5])


if __name__ == "__main__":
    unittest.main()
