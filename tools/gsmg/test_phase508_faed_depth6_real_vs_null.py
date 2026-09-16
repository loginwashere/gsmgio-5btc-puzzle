import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import phase508_faed_depth6_real_vs_null as phase508


class Phase508Tests(unittest.TestCase):
    def test_null_is_deterministic_exact_multiset(self):
        a = phase508.shuffled_faed(0)
        b = phase508.shuffled_faed(0)
        self.assertEqual(a, b)
        self.assertNotEqual(a, phase508.FAED)
        self.assertEqual(sorted(a), sorted(phase508.FAED))

    def test_null_indices_are_frozen(self):
        with self.assertRaises(ValueError):
            phase508.shuffled_faed(-1)
        with self.assertRaises(ValueError):
            phase508.shuffled_faed(phase508.TRIALS)

    def test_tie_counts_as_exceedance(self):
        records = [{"hypothesis_pair_index": index,
                    "hypothesis_pair": list(pair),
                    "null_observed_sha256": "null",
                    "observable": {"primary_selector": float(index)}}
                   for index, pair in enumerate(phase508.ceiling.ALL_PAIRS)]
        with mock.patch.object(phase508, "sha", return_value="lock"), \
                mock.patch.object(phase508, "real_maximum", return_value=35.0):
            result = phase508.summarize_trial(0, records)
        self.assertTrue(result["tie_inclusive_exceedance"])

    def test_run_refuses_without_lock_before_training(self):
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(phase508, "LOCK", Path(directory) / "none"), \
                mock.patch.object(phase508.deep, "train_pair_balanced_models",
                                  side_effect=AssertionError("trained")):
            with self.assertRaisesRegex(RuntimeError, "lock is absent"):
                phase508.run()

    def test_validate_rejects_wrong_null_identity(self):
        record = {"phase": 508, "status": "null_pair_cell_complete",
                  "faed_scored": False, "null_trial_index": 0,
                  "null_observed_sha256": "wrong",
                  "execution_lock_sha256": "lock", "model_sha256": "model",
                  "hypothesis_pair_index": 0,
                  "hypothesis_pair": list(phase508.ceiling.ALL_PAIRS[0]),
                  "observable": {"primary_selector": -4.0}}
        with mock.patch.object(phase508, "sha", return_value="lock"), \
                mock.patch.object(phase508.selector, "model_sha256",
                                  return_value="model"):
            with self.assertRaisesRegex(RuntimeError, "null_observed_sha256"):
                phase508.validate_cell(record, 0, 0, phase508.shuffled_faed(0), {})

    def test_completed_trial_is_recomputed_from_cells(self):
        observed = phase508.shuffled_faed(0)
        observed_hash = phase508.hashlib.sha256(observed.encode("ascii")).hexdigest()
        records = []
        for index, pair in enumerate(phase508.ceiling.ALL_PAIRS):
            records.append({
                "phase": 508,
                "status": "null_pair_cell_complete",
                "faed_scored": False,
                "null_trial_index": 0,
                "null_observed_sha256": observed_hash,
                "execution_lock_sha256": "lock",
                "model_sha256": "model",
                "hypothesis_pair_index": index,
                "hypothesis_pair": list(pair),
                "observable": {"primary_selector": float(index)},
            })
        expected = phase508.summarize_trial(
            0, records, real_score=35.0, lock_sha256="lock")
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(phase508, "WORK_DIR", Path(directory)), \
                mock.patch.object(phase508, "sha", return_value="lock"), \
                mock.patch.object(phase508, "real_maximum", return_value=35.0), \
                mock.patch.object(phase508.selector, "model_sha256",
                                  return_value="model"):
            for record in records:
                path = phase508.cell_path(0, record["hypothesis_pair_index"])
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(record))
            phase508.trial_path(0).write_text(json.dumps(expected))
            self.assertEqual(
                phase508.load_completed_trial(0, observed, {}), expected)
            tampered = dict(expected)
            tampered["family_maximum"] = -99.0
            phase508.trial_path(0).write_text(json.dumps(tampered))
            with self.assertRaisesRegex(RuntimeError, "does not match its cells"):
                phase508.load_completed_trial(0, observed, {})


if __name__ == "__main__":
    unittest.main()
