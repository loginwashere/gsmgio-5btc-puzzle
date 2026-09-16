import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

import phase505e_depth6_escape_pair_selector as phase505e


class Phase505ETests(unittest.TestCase):
    def test_timing_refuses_before_training_without_lock(self):
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(phase505e, "TIMING_LOCK",
                                   Path(directory) / "absent.json"), \
                    mock.patch.object(
                        phase505e.deep, "train_pair_balanced_models",
                        side_effect=AssertionError("training started")):
                with self.assertRaisesRegex(RuntimeError,
                                             "timing execution lock is absent"):
                    phase505e.run_timing(Path(directory) / "work")

    def test_pilot_cost_gate_rejects_expensive_projection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            timing = root / "timing_cell.json"
            timing.write_text(json.dumps({
                "projected_pilot_seconds":
                    phase505e.MAX_PILOT_PROJECTED_SECONDS + 1}) + "\n")
            with self.assertRaisesRegex(RuntimeError, "exceeds cost gate"):
                phase505e.expected_pilot_lock(root)

    def test_model_hash_is_canonical(self):
        class Model:
            mean = np.asarray([1.0])
            scale = np.asarray([2.0])
            weight = np.asarray([3.0])
            intercept = 4.0
        left = phase505e.model_sha256({5: Model(), 4: Model()})
        right = phase505e.model_sha256({4: Model(), 5: Model()})
        self.assertEqual(left, right)

    def test_rank_row_ignores_audit_fields(self):
        records = []
        for index in range(36):
            records.append({
                "hypothesis_pair_index": index,
                "observable": {"primary_selector": 1.0 if index == 8 else 0.0},
                "audit_only": {"fabricated": 1000 - index},
            })
        result = phase505e.rank_row(records, 8)
        self.assertEqual(result["true_pair_rank"], 1)
        self.assertEqual(result["ranked_pair_indices"][0], 8)

    def test_best_path_window_count(self):
        rows = [np.asarray([0, 1, 2, 3]), np.asarray([0, 1, 2]),
                np.asarray([0, 1, 2, 3, 4])]
        with mock.patch.object(phase505e.front, "canonical_token_rows",
                               return_value=rows):
            self.assertEqual(phase505e.best_path_window_count(
                [], ("a", "b"), [0, 1, 2, 3]), 3)

    def test_validate_cell_rejects_stale_model(self):
        fixture = {"observed": "a" * 570}
        with mock.patch.object(phase505e.ceiling, "make_fixture",
                               return_value=fixture), \
                mock.patch.object(phase505e, "model_sha256",
                                  side_effect=["new", "new"]):
            record = {
                "phase": "505E", "status": "development_depth6_cell_complete",
                "faed_scored": False, "holdout_consumed": False,
                "true_pair_index": 0,
                "true_pair": list(phase505e.ceiling.ALL_PAIRS[0]),
                "hypothesis_pair_index": 0,
                "hypothesis_pair": list(phase505e.ceiling.ALL_PAIRS[0]),
                "fixture_observed_sha256": __import__("hashlib").sha256(
                    fixture["observed"].encode()).hexdigest(),
                "model_sha256": "old",
                "observable": {"primary_selector": -4.0},
            }
            with self.assertRaisesRegex(RuntimeError, "model_sha256"):
                phase505e.validate_cell(record, 0, 0, {})


if __name__ == "__main__":
    unittest.main()
