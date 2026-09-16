import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

import phase505c_shallow_escape_pair_screen as phase505c


class Phase505CTests(unittest.TestCase):
    def test_exact_depth4_path_universe(self):
        paths = phase505c.path_universe()
        self.assertEqual(paths.shape, (93024, 4))
        self.assertEqual(len(np.unique(paths, axis=0)), len(paths))
        self.assertTrue(np.all(np.diff(np.sort(paths, axis=1), axis=1) > 0))

    def test_score_summary_rejects_nonfinite(self):
        with self.assertRaisesRegex(ValueError, "finite"):
            phase505c.score_summary(np.asarray([-4.0, np.nan]))

    def test_score_summary_reports_primary_maximum(self):
        record = phase505c.score_summary(np.asarray([-5.0, -4.0, -3.0]))
        self.assertEqual(record["best"], -3.0)
        self.assertEqual(record["count"], 3)
        self.assertGreaterEqual(record["best_minus_q99"], 0.0)

    def test_pilot_refuses_before_any_gpu_work_without_lock(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "absent.json"
            with mock.patch.object(phase505c, "LOCK_PATH", missing), \
                    mock.patch.object(
                        phase505c, "path_universe",
                        side_effect=AssertionError("path construction started")):
                with self.assertRaisesRegex(RuntimeError,
                                             "execution lock is absent"):
                    phase505c.run_pilot(Path(directory) / "work")

    def test_rank_row_ignores_audit_truth_and_breaks_ties_canonically(self):
        records = []
        for index in range(36):
            records.append({
                "hypothesis_pair_index": index,
                "observable": {"primary_selector": -9.0},
                "audit_only": {"true_fragment_recovery": {
                    "best_true_rank": 36 - index}},
                "wall_seconds": 0.1,
            })
        records[2]["observable"]["primary_selector"] = -3.0
        records[3]["observable"]["primary_selector"] = -3.0
        result = phase505c.rank_row(records, 3)
        self.assertEqual(result["true_pair_rank"], 2)
        self.assertEqual(result["ranked_pair_indices"][:2], [2, 3])
        self.assertEqual(result["true_minus_best_wrong"], 0.0)

    def test_validate_cell_rejects_wrong_pair_identity(self):
        fixture = {"observed": "a" * 570}
        with mock.patch.object(phase505c.ceiling, "make_fixture",
                               return_value=fixture):
            record = phase505c.expected_identity(0, 0)
            record["observable"] = {"primary_selector": -4.0}
            record["hypothesis_pair_index"] = 1
            with self.assertRaisesRegex(RuntimeError,
                                         "hypothesis_pair_index"):
                phase505c.validate_cell(record, 0, 0)

    def test_run_cell_scores_every_supplied_path_without_truth_feedback(self):
        paths = np.asarray([[0, 1, 2, 3], [3, 2, 1, 0]], dtype=np.uint8)
        fixture = {
            "pair": ["a", "b"], "order": list(range(19)),
            "observed": "a" * 570,
        }
        seen = {}

        def fake_score(given, _blocks, pair, _quad, restarts, iterations,
                       binary, seed):
            seen.update(pair=pair, restarts=restarts, iterations=iterations,
                        binary=binary, seed=seed)
            self.assertTrue(np.array_equal(given, paths))
            return np.asarray([-5.0, -4.0])

        with mock.patch.object(phase505c.ceiling, "make_fixture",
                               return_value=fixture), \
                mock.patch.object(phase505c.prefix, "blocks_from_observed",
                                  return_value=["a" * 30] * 19), \
                mock.patch.object(phase505c.base, "load_language_model",
                                  return_value=(np.zeros(25**4), None)), \
                mock.patch.object(phase505c.front, "constrained_multistart",
                                  side_effect=fake_score):
            result = phase505c.run_cell(0, 1, paths)
        self.assertEqual(result["observable"]["primary_selector"], -4.0)
        self.assertEqual(seen["pair"], phase505c.ceiling.ALL_PAIRS[1])
        self.assertEqual(seen["restarts"], phase505c.RESTARTS)
        self.assertEqual(seen["iterations"], phase505c.ITERATIONS)
        self.assertFalse(result["audit_only"]["true_pair"])


if __name__ == "__main__":
    unittest.main()
