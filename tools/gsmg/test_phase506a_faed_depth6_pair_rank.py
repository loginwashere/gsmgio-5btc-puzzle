import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import phase506a_faed_depth6_pair_rank as phase506a


class Phase506ATests(unittest.TestCase):
    def test_run_refuses_before_training_without_lock(self):
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(phase506a, "LOCK", Path(directory) / "no"), \
                mock.patch.object(phase506a.deep, "train_pair_balanced_models",
                                  side_effect=AssertionError("trained")):
            with self.assertRaisesRegex(RuntimeError, "lock is absent"):
                phase506a.run()

    def test_ranking_excludes_gi_after_global_sort(self):
        gi = phase506a.ceiling.ALL_PAIRS.index(("g", "i"))
        records = []
        for i, pair in enumerate(phase506a.ceiling.ALL_PAIRS):
            score = 100.0 if i == gi else float(i)
            records.append({"hypothesis_pair_index": i,
                            "hypothesis_pair": list(pair),
                            "observable": {"primary_selector": score}})
        ranking, selected = phase506a.rank_records(records)
        self.assertEqual(ranking[0]["pair"], ["g", "i"])
        self.assertNotIn(["g", "i"], [row["pair"] for row in selected])
        self.assertEqual(len(selected), 5)

    def test_ties_break_by_pair_index(self):
        records = [{"hypothesis_pair_index": i,
                    "hypothesis_pair": list(pair),
                    "observable": {"primary_selector": 0.0}}
                   for i, pair in enumerate(phase506a.ceiling.ALL_PAIRS)]
        ranking, _ = phase506a.rank_records(records)
        self.assertEqual([row["pair_index"] for row in ranking], list(range(36)))

    def test_validate_rejects_wrong_pair(self):
        record = {"phase": "506A",
                  "status": "real_faed_depth6_pair_cell_complete",
                  "faed_scored": True, "holdout_consumed": False,
                  "execution_lock_sha256": "x",
                  "faed_ascii_sha256": phase506a.FAED_SHA256,
                  "model_sha256": "model",
                  "hypothesis_pair_index": 0,
                  "hypothesis_pair": ["a", "c"],
                  "observable": {"primary_selector": -4.0}}
        with mock.patch.object(phase506a, "sha", return_value="x"), \
                mock.patch.object(phase506a.selector, "model_sha256",
                                  return_value="model"):
            with self.assertRaisesRegex(RuntimeError, "hypothesis_pair"):
                phase506a.validate_cell(record, 0, {})


if __name__ == "__main__":
    unittest.main()
