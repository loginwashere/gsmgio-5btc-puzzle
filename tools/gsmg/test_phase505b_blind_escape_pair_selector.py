import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

import phase505b_blind_escape_pair_selector as phase505b


class Phase505BTests(unittest.TestCase):
    def test_describe_has_complete_benchmark_and_matrix_universes(self):
        with mock.patch.object(phase505b.BENCHMARK_LOCK_PATH.__class__,
                               "is_file", return_value=False):
            record = phase505b.describe()
        self.assertEqual(record["benchmark_cells"], 108)
        self.assertEqual(record["full_development_cells"], 1296)
        self.assertFalse(record["faed_scored"])
        self.assertFalse(record["holdout_consumed"])

    def test_score_summary_is_finite_and_deterministic(self):
        record = phase505b.score_summary(np.asarray([-5.0, -4.0, -3.0]))
        self.assertEqual(record["count"], 3)
        self.assertEqual(record["finite"], 3)
        self.assertEqual(record["best"], -3.0)
        self.assertGreaterEqual(record["best_minus_q99"], 0.0)
        empty = phase505b.score_summary(np.asarray([-np.inf, np.nan]))
        self.assertEqual(empty["finite"], 0)
        self.assertIsNone(empty["best"])

    def test_rank_row_uses_only_primary_selector_and_canonical_ties(self):
        records = []
        for index in range(36):
            records.append({
                "hypothesis_pair_index": index,
                "observable": {"primary_selector": -10.0},
                "audit_only": {"fabricated_truth_score": 1000 - index},
                "wall_seconds": 1.0,
            })
        records[4]["observable"]["primary_selector"] = -3.0
        records[5]["observable"]["primary_selector"] = -3.0
        ranked = phase505b.rank_row(records, 5)
        self.assertEqual(ranked["true_pair_rank"], 2)
        self.assertEqual(ranked["ranked_pair_indices"][:2], [4, 5])
        self.assertEqual(ranked["true_minus_best_wrong"], 0.0)

    def test_benchmark_refuses_before_training_when_lock_absent(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "benchmark-lock.json"
            with mock.patch.object(phase505b, "BENCHMARK_LOCK_PATH", missing), \
                    mock.patch.object(
                        phase505b, "train_pair_balanced_models",
                        side_effect=AssertionError("training must not start")):
                with self.assertRaisesRegex(RuntimeError,
                                             "benchmark execution lock is absent"):
                    phase505b.run_benchmark(Path(directory) / "work")

    def test_matrix_refuses_before_training_when_lock_absent(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "benchmark-lock.json"
            with mock.patch.object(phase505b, "BENCHMARK_LOCK_PATH", missing), \
                    mock.patch.object(
                        phase505b, "train_pair_balanced_models",
                        side_effect=AssertionError("training must not start")):
                with self.assertRaisesRegex(RuntimeError,
                                             "benchmark execution lock is absent"):
                    phase505b.run_development_matrix(Path(directory) / "work")

    def test_validate_cell_rejects_stale_model_hash(self):
        fixture = {
            "observed": "a" * 570,
        }
        with mock.patch.object(phase505b.ceiling, "make_fixture",
                               return_value=fixture):
            record = phase505b.expected_cell_identity(0, 1, "old")
            record["observable"] = {"primary_selector": -4.0}
            with self.assertRaisesRegex(RuntimeError,
                                         "model_manifest_sha256"):
                phase505b.validate_cell(record, 0, 1, "new")

    def test_validate_cell_rejects_nonfinite_selector(self):
        fixture = {"observed": "a" * 570}
        with mock.patch.object(phase505b.ceiling, "make_fixture",
                               return_value=fixture):
            record = phase505b.expected_cell_identity(0, 1, "model")
            record["observable"] = {"primary_selector": float("nan")}
            with self.assertRaisesRegex(RuntimeError, "invalid primary"):
                phase505b.validate_cell(record, 0, 1, "model")

    def test_run_rows_writes_distinct_summary_and_resumable_cells(self):
        fake_models = {4: object()}
        fake_payload = {"model": "fixed"}

        def fake_cell(_root, true_index, hypothesis_index, _models,
                      _model_hash):
            return {
                "hypothesis_pair_index": hypothesis_index,
                "observable": {
                    "primary_selector": (1.0 if hypothesis_index == true_index
                                         else 0.0),
                },
                "wall_seconds": 0.25,
            }

        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(phase505b, "train_pair_balanced_models",
                                  return_value=fake_models), \
                mock.patch.object(phase505b, "model_payload",
                                  return_value=fake_payload), \
                mock.patch.object(phase505b, "run_or_resume_cell",
                                  side_effect=fake_cell):
            root = Path(directory)
            result = phase505b.run_rows((0,), root, "benchmark_summary.json")
            self.assertEqual(result["top1"], 1)
            self.assertEqual(result["cell_count"], 36)
            self.assertTrue((root / "benchmark_summary.json").is_file())
            self.assertFalse((root / "development_matrix_summary.json").exists())
            progress = json.loads((root / "progress.json").read_text())
            self.assertEqual(progress["total_cells"], 36)


if __name__ == "__main__":
    unittest.main()
